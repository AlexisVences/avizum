import { chatReducer, initialChatState, normalizeMessage } from '../chatReducer';

const run = (...actions) => actions.reduce(chatReducer, initialChatState);

const serverMessage = (overrides = {}) => ({
  id: 1, role: 'user', content: 'hola', status: 'complete', citations: null, created_at: '2026-10-12T10:00:00Z', feedback: null,
  ...overrides,
});

const activeWith = (...messages) =>
  run(
    { type: 'CONVERSATIONS_LOADED', conversations: [{ id: 5, title: 'Placas', updated_at: 'x' }] },
    { type: 'CONVERSATION_SELECTED', id: 5 },
    { type: 'MESSAGES_LOADED', conversationId: 5, messages },
  );

describe('loading', () => {
  test('selecting a conversation clears the screen and loads its messages', () => {
    const state = run({ type: 'CONVERSATION_SELECTED', id: 5 });
    expect(state).toMatchObject({ activeId: 5, messages: [], phase: 'loading' });
    const loaded = chatReducer(state, { type: 'MESSAGES_LOADED', conversationId: 5, messages: [serverMessage()] });
    expect(loaded.phase).toBe('idle');
    expect(loaded.messages[0]).toMatchObject({ key: 'm-1', role: 'user', citations: [], feedback: null });
  });

  test('messages that arrive for a conversation the user already left are ignored', () => {
    const state = run({ type: 'CONVERSATION_SELECTED', id: 5 }, { type: 'CONVERSATION_SELECTED', id: 6 });
    const after = chatReducer(state, { type: 'MESSAGES_LOADED', conversationId: 5, messages: [serverMessage()] });
    expect(after.messages).toEqual([]);
    expect(after.phase).toBe('loading'); // still waiting for conversation 6
  });

  test('normalizing keeps what the interface needs and tolerates null citations', () => {
    expect(normalizeMessage(serverMessage({ id: 9, role: 'assistant', citations: [{ n: 1 }], feedback: -1 }))).toEqual({
      key: 'm-9', id: 9, role: 'assistant', content: 'hola', status: 'complete', citations: [{ n: 1 }], feedback: -1,
      createdAt: '2026-10-12T10:00:00Z',
    });
  });
});

describe('a streamed turn', () => {
  const started = () => chatReducer(activeWith(), { type: 'SEND_STARTED', content: '¿placas?', nonce: 1 });

  test('shows the question and an empty answer at once and blocks sending', () => {
    const state = started();
    expect(state.phase).toBe('sending');
    expect(state.messages.map((m) => [m.role, m.content, m.status])).toEqual([
      ['user', '¿placas?', 'sending'],
      ['assistant', '', 'streaming'],
    ]);
  });

  test('follows the events: ids, tool in use, tokens, citations and the canonical final text', () => {
    let state = started();
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'message_start', data: { user_message_id: 40 } });
    expect(state.phase).toBe('streaming');
    expect(state.messages[0]).toMatchObject({ id: 40, key: 'm-40', status: 'complete' });

    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'tool_start', data: { name: 'buscar_legislacion', args: { consulta: 'x' } } });
    expect(state.tool).toEqual({ name: 'buscar_legislacion', args: { consulta: 'x' } });
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'tool_end', data: { name: 'buscar_legislacion', ok: true } });
    expect(state.tool).toBeNull();

    for (const text of ['Sí ', 'es ', 'cierto [1] y [99].']) {
      state = chatReducer(state, { type: 'STREAM_EVENT', event: 'token', data: { text } });
    }
    expect(state.messages[1].content).toBe('Sí es cierto [1] y [99].');

    const citations = [{ n: 1, orden: 1, article: '44', page: 56, url: 'https://x/r.pdf#page=56' }];
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'citations', data: citations });
    expect(state.messages[1].citations).toEqual(citations);

    state = chatReducer(state, {
      type: 'STREAM_EVENT', event: 'done',
      data: { assistant_message_id: 41, text: 'Sí es cierto [1].', usage: { input_tokens: 1, output_tokens: 1 } },
    });
    expect(state.phase).toBe('idle');
    expect(state.messages[1]).toMatchObject({ id: 41, key: 'm-41', content: 'Sí es cierto [1].', status: 'complete', citations });
  });

  test('an error event turns the pending answer into a visible error and frees the screen', () => {
    let state = started();
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'token', data: { text: 'Una resp' } });
    state = chatReducer(state, {
      type: 'STREAM_EVENT', event: 'error',
      data: { code: 'generacion_fallida', message: 'No pude generar la respuesta.', assistant_message_id: 42 },
    });
    expect(state.phase).toBe('idle');
    expect(state.messages[1]).toMatchObject({ id: 42, status: 'error', content: 'No pude generar la respuesta.' });
  });

  test('a rejected send (409, 429, 422...) removes the optimistic messages and gives the text back', () => {
    const state = chatReducer(started(), {
      type: 'SEND_REJECTED', content: '¿placas?', error: { message: 'Llegaste al límite', code: 'limite_diario', status: 429 },
    });
    expect(state.messages).toEqual([]);
    expect(state.phase).toBe('idle');
    expect(state.draft).toBe('¿placas?');
    expect(state.error).toMatchObject({ code: 'limite_diario', status: 429 });
  });

  test('losing the connection mid-stream keeps the partial text and asks to reload', () => {
    let state = started();
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'message_start', data: { user_message_id: 40 } });
    state = chatReducer(state, { type: 'STREAM_EVENT', event: 'token', data: { text: 'Parcial' } });
    state = chatReducer(state, { type: 'STREAM_FAILED', error: { message: 'Se perdió la conexión.' } });
    expect(state.phase).toBe('idle');
    expect(state.messages[1]).toMatchObject({ status: 'error', content: 'Parcial' });
    expect(state.error.message).toBe('Se perdió la conexión.');
  });

  test('events that arrive with no turn in flight are ignored', () => {
    const state = chatReducer(activeWith(serverMessage()), { type: 'STREAM_EVENT', event: 'token', data: { text: 'x' } });
    expect(state.messages).toHaveLength(1);
  });
});

describe('conversations list', () => {
  const base = run({
    type: 'CONVERSATIONS_LOADED',
    conversations: [{ id: 1, title: 'A', updated_at: 'a' }, { id: 2, title: null, updated_at: 'b' }],
  });

  test('creating prepends and selects; renaming and deleting update the list', () => {
    let state = chatReducer(base, { type: 'CONVERSATION_CREATED', conversation: { id: 3, title: null, updated_at: 'c' } });
    expect(state.conversations.map((c) => c.id)).toEqual([3, 1, 2]);
    expect(state.activeId).toBe(3);
    expect(state.phase).toBe('idle'); // a new conversation has nothing to load

    state = chatReducer(state, { type: 'CONVERSATION_RENAMED', conversation: { id: 1, title: 'Nuevo', updated_at: 'd' } });
    expect(state.conversations.find((c) => c.id === 1).title).toBe('Nuevo');

    state = chatReducer(state, { type: 'CONVERSATION_DELETED', id: 3 });
    expect(state.conversations.map((c) => c.id)).toEqual([1, 2]);
    expect(state).toMatchObject({ activeId: null, messages: [] });
  });

  test('deleting another conversation leaves the open one alone', () => {
    const open = chatReducer(base, { type: 'CONVERSATION_SELECTED', id: 1 });
    const state = chatReducer(open, { type: 'CONVERSATION_DELETED', id: 2 });
    expect(state.activeId).toBe(1);
  });
});

describe('votes', () => {
  const withAnswer = () => activeWith(serverMessage({ id: 7, role: 'assistant', content: 'r' }));

  test('a vote shows immediately and can be reverted if the server refuses it', () => {
    let state = chatReducer(withAnswer(), { type: 'VOTE_CHANGED', messageId: 7, value: 1 });
    expect(state.messages[0].feedback).toBe(1);
    state = chatReducer(state, { type: 'VOTE_CHANGED', messageId: 7, value: -1 });
    expect(state.messages[0].feedback).toBe(-1);
    state = chatReducer(state, { type: 'VOTE_CHANGED', messageId: 7, value: null });
    expect(state.messages[0].feedback).toBeNull();
  });
});

describe('new chat and load failures', () => {
  test('a new chat is just an empty screen: nothing is created until the first question', () => {
    const state = run(
      { type: 'CONVERSATIONS_LOADED', conversations: [{ id: 1, title: 'A', updated_at: 'a' }] },
      { type: 'CONVERSATION_SELECTED', id: 1 },
      { type: 'MESSAGES_LOADED', conversationId: 1, messages: [serverMessage()] },
      { type: 'NEW_CHAT' },
    );
    expect(state).toMatchObject({ activeId: null, messages: [], phase: 'idle' });
    expect(state.conversations).toHaveLength(1);
  });

  test('failing to load a conversation frees the screen and reports why', () => {
    const state = run({ type: 'CONVERSATION_SELECTED', id: 3 }, { type: 'LOAD_FAILED', error: { message: 'No encontrado', status: 404 } });
    expect(state).toMatchObject({ phase: 'idle', error: { status: 404 } });
  });
});

describe('errors', () => {
  test('dismissing clears the error and the draft', () => {
    const state = run({ type: 'SEND_REJECTED', content: 'texto', error: { message: 'x', code: null, status: 422 } }, { type: 'ERROR_DISMISSED' });
    expect(state.error).toBeNull();
    expect(state.draft).toBe('');
  });
});
