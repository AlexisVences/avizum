import { API_URL, authHeaders, extractErrorMessage } from './api';

// The chat API: conversations, messages (with citations) and votes, plus the streamed answer.

export class ChatError extends Error {
  constructor(message, { status = 0, code = null } = {}) {
    super(message);
    this.name = 'ChatError';
    this.status = status; // HTTP status: 401 login again, 404 not yours / gone, 409 busy or full, 422, 429 daily limit
    this.code = code; // machine-readable: 'respuesta_en_curso', 'limite_diario', 'conversacion_llena', ...
  }
}

const FALLBACK = 'No se pudo completar la solicitud. Intenta de nuevo.';

// Chat errors carry `detail: { code, message }`; other routes carry a string or a validation list.
const errorFrom = async (response) => {
  let detail;
  try {
    ({ detail } = await response.json());
  } catch {
    detail = undefined;
  }
  const isCoded = detail && typeof detail === 'object' && !Array.isArray(detail);
  return new ChatError(extractErrorMessage({ detail }, FALLBACK), {
    status: response.status,
    code: isCoded ? detail.code || null : null,
  });
};

const request = async (path, { method = 'GET', body, signal } = {}) => {
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...authHeaders() },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });
  if (!response.ok) throw await errorFrom(response);
  return response.status === 204 ? null : response.json();
};

export const listConversations = (limit = 100) => request(`/conversations?limit=${limit}`);
export const createConversation = () => request('/conversations', { method: 'POST' });
export const renameConversation = (id, title) => request(`/conversations/${id}`, { method: 'PATCH', body: { title } });
export const deleteConversation = (id) => request(`/conversations/${id}`, { method: 'DELETE' });
export const listMessages = (conversationId) => request(`/conversations/${conversationId}/messages`);
export const setFeedback = (messageId, value) => request(`/messages/${messageId}/feedback`, { method: 'PUT', body: { value } });
export const clearFeedback = (messageId) => request(`/messages/${messageId}/feedback`, { method: 'DELETE' });

// ---- Server-Sent Events -------------------------------------------------------------------------------------
// EventSource cannot POST nor send an Authorization header, so the stream is read from a fetch() response body.

const parseBlock = (block) => {
  let event = 'message';
  const dataLines = [];
  for (const line of block.split('\n')) {
    if (line.startsWith(':')) continue; // comment, used as keep-alive
    const colon = line.indexOf(':');
    const field = colon === -1 ? line : line.slice(0, colon);
    const value = colon === -1 ? '' : line.slice(colon + 1).replace(/^ /, '');
    if (field === 'event') event = value;
    else if (field === 'data') dataLines.push(value);
  }
  if (dataLines.length === 0) return null;
  const raw = dataLines.join('\n');
  try {
    return { event, data: JSON.parse(raw) };
  } catch {
    return { event, data: raw };
  }
};

// Incremental: feed it decoded text in whatever pieces the network delivered; it returns the events completed so far.
export class SSEParser {
  constructor() {
    this.buffer = '';
    this.carry = ''; // a trailing "\r" waits for the next piece: it may be the first half of "\r\n"
  }

  feed(text) {
    const incoming = this.carry + text;
    this.carry = incoming.endsWith('\r') ? '\r' : '';
    this.buffer += (this.carry ? incoming.slice(0, -1) : incoming).replace(/\r\n?/g, '\n');
    const events = [];
    let boundary = this.buffer.indexOf('\n\n');
    while (boundary !== -1) {
      const parsed = parseBlock(this.buffer.slice(0, boundary));
      this.buffer = this.buffer.slice(boundary + 2);
      if (parsed) events.push(parsed);
      boundary = this.buffer.indexOf('\n\n');
    }
    return events;
  }
}

// `reader` is a ReadableStreamDefaultReader. The decoder keeps state between calls (`stream: true`), so a character
// split across two network chunks is rebuilt instead of corrupted.
export const readSSE = async (reader, onEvent, decoder = new TextDecoder('utf-8')) => {
  const parser = new SSEParser();
  const deliver = (text) => parser.feed(text).forEach(({ event, data }) => onEvent(event, data));
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    deliver(decoder.decode(value, { stream: true }));
  }
  deliver(decoder.decode());
};

// Sends the question and calls onEvent(name, data) for message_start, tool_start, tool_end, token, citations, done
// and error as they arrive. Limit and ownership errors reject with a ChatError before any event. `signal` lets the
// screen abort the request (the server then saves what was generated as "cancelled").
export const streamMessage = async ({ conversationId, content, onEvent, signal }) => {
  const response = await fetch(`${API_URL}/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream', ...authHeaders() },
    body: JSON.stringify({ content }),
    signal,
  });
  if (!response.ok) throw await errorFrom(response);
  await readSSE(response.body.getReader(), onEvent);
};
