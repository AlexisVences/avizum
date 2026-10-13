import { TextDecoder, TextEncoder } from 'util';
import {
  ChatError,
  SSEParser,
  clearFeedback,
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  readSSE,
  renameConversation,
  setFeedback,
  streamMessage,
} from '../chatService';

// CRA's jest environment has fetch but not TextDecoder/TextEncoder/ReadableStream (browsers have all three).
global.TextDecoder = TextDecoder;
const encoder = new TextEncoder();

const sse = (event, data) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;

// A reader like ReadableStreamDefaultReader: hands the given byte chunks out one by one.
const readerOf = (chunks, { failAfter } = {}) => {
  let i = 0;
  return {
    read: async () => {
      if (failAfter !== undefined && i >= failAfter) throw new TypeError('network error');
      if (i >= chunks.length) return { done: true, value: undefined };
      return { done: false, value: chunks[i++] };
    },
    cancel: jest.fn(),
  };
};

const streamResponse = (chunks, opts) => ({ ok: true, status: 200, body: { getReader: () => readerOf(chunks, opts) } });
const jsonResponse = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });

beforeEach(() => {
  localStorage.setItem('token', 'tok-123');
  global.fetch = jest.fn();
});
afterEach(() => localStorage.clear());

describe('SSEParser', () => {
  test('returns the complete events and keeps the unfinished one for the next chunk', () => {
    const parser = new SSEParser();
    const full = sse('token', { text: 'Hola ' }) + sse('token', { text: 'mundo' });
    const cut = full.length - 9; // inside the second event
    expect(parser.feed(full.slice(0, cut))).toEqual([{ event: 'token', data: { text: 'Hola ' } }]);
    expect(parser.feed(full.slice(cut))).toEqual([{ event: 'token', data: { text: 'mundo' } }]);
  });

  test('an event split in the middle of a line is rebuilt', () => {
    const parser = new SSEParser();
    const text = sse('citations', [{ n: 1, article: '33' }]);
    const cut = 18;
    expect(parser.feed(text.slice(0, cut))).toEqual([]);
    expect(parser.feed(text.slice(cut))).toEqual([{ event: 'citations', data: [{ n: 1, article: '33' }] }]);
  });

  test('handles CRLF, comments used as keep-alives and multi-line data', () => {
    const parser = new SSEParser();
    const events = parser.feed(': keep-alive\r\n\r\nevent: token\r\ndata: {"text":\r\ndata: "hola"}\r\n\r\n');
    expect(events).toEqual([{ event: 'token', data: { text: 'hola' } }]);
  });

  test('a data line that is not JSON is delivered as text instead of breaking the stream', () => {
    const events = new SSEParser().feed('event: info\ndata: texto plano\n\n');
    expect(events).toEqual([{ event: 'info', data: 'texto plano' }]);
  });

  test('an event without a name is reported as "message", per the SSE spec', () => {
    expect(new SSEParser().feed('data: {"a":1}\n\n')).toEqual([{ event: 'message', data: { a: 1 } }]);
  });
});

describe('readSSE', () => {
  test('a multi-byte character split between two network chunks is not corrupted', async () => {
    const bytes = encoder.encode(sse('token', { text: 'Artículo 33 ¿ñandú? 🔧' }));
    const accent = bytes.indexOf(0xc3); // first byte of "í": cut right in the middle of it
    const received = [];
    await readSSE(readerOf([bytes.slice(0, accent + 1), bytes.slice(accent + 1)]), (event, data) => received.push([event, data]));
    expect(received).toEqual([['token', { text: 'Artículo 33 ¿ñandú? 🔧' }]]);
  });

  test('delivers events as they arrive, not at the end', async () => {
    const order = [];
    const reader = {
      read: jest
        .fn()
        .mockImplementationOnce(async () => { order.push('read 1'); return { done: false, value: encoder.encode(sse('token', { text: 'a' })) }; })
        .mockImplementationOnce(async () => { order.push('read 2'); return { done: false, value: encoder.encode(sse('token', { text: 'b' })) }; })
        .mockImplementationOnce(async () => ({ done: true })),
    };
    await readSSE(reader, (event, data) => order.push(`event ${data.text}`));
    expect(order).toEqual(['read 1', 'event a', 'read 2', 'event b']);
  });
});

describe('streamMessage', () => {
  test('posts with the stream Accept header and the token, and forwards every event in order', async () => {
    const body = [
      sse('message_start', { user_message_id: 7 }),
      sse('tool_start', { name: 'buscar_legislacion', args: { consulta: 'x' } }),
      sse('tool_end', { name: 'buscar_legislacion', ok: true }),
      sse('token', { text: 'Sí ' }),
      sse('citations', []),
      sse('done', { assistant_message_id: 8, text: 'Sí', usage: { input_tokens: 1, output_tokens: 1 } }),
    ].map((chunk) => encoder.encode(chunk));
    global.fetch.mockResolvedValue(streamResponse(body));
    const events = [];

    await streamMessage({ conversationId: 5, content: 'hola', onEvent: (event, data) => events.push(event) });

    expect(events).toEqual(['message_start', 'tool_start', 'tool_end', 'token', 'citations', 'done']);
    const [url, options] = global.fetch.mock.calls[0];
    expect(url).toMatch(/\/conversations\/5\/messages$/);
    expect(options.method).toBe('POST');
    expect(options.headers.Accept).toBe('text/event-stream');
    expect(options.headers.Authorization).toBe('Bearer tok-123');
    expect(JSON.parse(options.body)).toEqual({ content: 'hola' });
  });

  test('a limit error arrives as a ChatError with status, code and the server message', async () => {
    global.fetch.mockResolvedValue(
      jsonResponse({ detail: { code: 'respuesta_en_curso', message: 'Espera a que termine la respuesta en curso.' } }, 409),
    );
    await expect(streamMessage({ conversationId: 5, content: 'otra', onEvent: () => {} })).rejects.toMatchObject({
      name: 'ChatError', status: 409, code: 'respuesta_en_curso', message: 'Espera a que termine la respuesta en curso.',
    });
  });

  test('an unreadable error body still produces a usable message', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error('not json'); } });
    await expect(streamMessage({ conversationId: 1, content: 'x', onEvent: () => {} })).rejects.toBeInstanceOf(ChatError);
  });

  test('the connection dropping mid-stream rejects so the screen can show the error', async () => {
    const body = [encoder.encode(sse('token', { text: 'Una resp' }))];
    global.fetch.mockResolvedValue(streamResponse(body, { failAfter: 1 }));
    const tokens = [];
    await expect(streamMessage({ conversationId: 1, content: 'x', onEvent: (e, d) => tokens.push(d) })).rejects.toThrow('network error');
    expect(tokens).toEqual([{ text: 'Una resp' }]); // what arrived before the drop was delivered
  });

  test('passes the abort signal to fetch so the interface can stop a generation', async () => {
    global.fetch.mockResolvedValue(streamResponse([]));
    const controller = new AbortController();
    await streamMessage({ conversationId: 1, content: 'x', onEvent: () => {}, signal: controller.signal });
    expect(global.fetch.mock.calls[0][1].signal).toBe(controller.signal);
  });
});

describe('REST helpers', () => {
  test('list, create, rename and delete conversations', async () => {
    global.fetch
      .mockResolvedValueOnce(jsonResponse([{ id: 1, title: 'Placas' }]))
      .mockResolvedValueOnce(jsonResponse({ id: 2, title: null }, 201))
      .mockResolvedValueOnce(jsonResponse({ id: 2, title: 'Nuevo' }))
      .mockResolvedValueOnce({ ok: true, status: 204 });

    expect(await listConversations()).toEqual([{ id: 1, title: 'Placas' }]);
    expect(await createConversation()).toEqual({ id: 2, title: null });
    expect(await renameConversation(2, 'Nuevo')).toEqual({ id: 2, title: 'Nuevo' });
    expect(await deleteConversation(2)).toBeNull();

    const calls = global.fetch.mock.calls.map(([url, options]) => [options?.method || 'GET', url.replace(/^.*\/api\/v1|^http:\/\/localhost:8000\/api\/v1/, '')]);
    expect(calls).toEqual([['GET', '/conversations?limit=100'], ['POST', '/conversations'], ['PATCH', '/conversations/2'], ['DELETE', '/conversations/2']]);
    expect(JSON.parse(global.fetch.mock.calls[2][1].body)).toEqual({ title: 'Nuevo' });
  });

  test('messages, and the vote can be set and cleared', async () => {
    global.fetch
      .mockResolvedValueOnce(jsonResponse([{ id: 1, role: 'user' }]))
      .mockResolvedValueOnce({ ok: true, status: 204 })
      .mockResolvedValueOnce({ ok: true, status: 204 });

    expect(await listMessages(9)).toEqual([{ id: 1, role: 'user' }]);
    await setFeedback(4, -1);
    await clearFeedback(4);

    expect(global.fetch.mock.calls[1][1].method).toBe('PUT');
    expect(JSON.parse(global.fetch.mock.calls[1][1].body)).toEqual({ value: -1 });
    expect(global.fetch.mock.calls[2][1].method).toBe('DELETE');
  });

  test('a 404 or 401 becomes a ChatError the screen can react to', async () => {
    global.fetch.mockResolvedValue(jsonResponse({ detail: 'No encontrado' }, 404));
    await expect(listMessages(99)).rejects.toMatchObject({ status: 404, message: 'No encontrado' });
    global.fetch.mockResolvedValue(jsonResponse({ detail: 'Authentication required' }, 401));
    await expect(listConversations()).rejects.toMatchObject({ status: 401 });
  });
});
