// All the state transitions of the chat screen, as a pure function: easy to test and to reason about.
// phase: 'idle' (can send) | 'loading' (fetching a conversation's messages) | 'sending' (question out, nothing back
// yet) | 'streaming' (the answer is arriving). The send button is enabled only in 'idle'.

export const initialChatState = {
  conversations: [],
  activeId: null,
  messages: [],
  phase: 'idle',
  tool: null, // { name, args } while the agent runs a tool: drives "Buscando en la legislación…"
  error: null, // { message, code, status }
  draft: '', // text handed back to the composer after a rejected send
};

export const normalizeMessage = (message) => ({
  key: `m-${message.id}`,
  id: message.id,
  role: message.role,
  content: message.content,
  status: message.status,
  citations: message.citations || [],
  feedback: message.feedback ?? null,
  createdAt: message.created_at,
});

const isUserPending = (message) => message.key.startsWith('tmp-user-');
const isAssistantPending = (message) => message.key.startsWith('tmp-assistant-');

const updatePending = (messages, change) =>
  messages.map((message) => (isAssistantPending(message) ? { ...message, ...change(message) } : message));

const hasPending = (messages) => messages.some(isAssistantPending);

const handleStreamEvent = (state, { event, data }) => {
  if (!hasPending(state.messages)) return state; // an event with no turn in flight

  switch (event) {
    case 'message_start':
      return {
        ...state,
        phase: 'streaming',
        messages: state.messages.map((message) =>
          isUserPending(message)
            ? { ...message, id: data.user_message_id, key: `m-${data.user_message_id}`, status: 'complete' }
            : message,
        ),
      };
    case 'tool_start':
      return { ...state, tool: { name: data.name, args: data.args } };
    case 'tool_end':
      return { ...state, tool: null };
    case 'token':
      return { ...state, messages: updatePending(state.messages, (m) => ({ content: m.content + data.text })) };
    case 'citations':
      return { ...state, messages: updatePending(state.messages, () => ({ citations: Array.isArray(data) ? data : [] })) };
    case 'done':
      // `done.text` is canonical: it has the invalid citation markers removed, unlike the streamed tokens.
      return {
        ...state,
        phase: 'idle',
        tool: null,
        messages: updatePending(state.messages, () => ({
          id: data.assistant_message_id, key: `m-${data.assistant_message_id}`, content: data.text, status: 'complete',
        })),
      };
    case 'error':
      return {
        ...state,
        phase: 'idle',
        tool: null,
        error: { message: data.message, code: data.code || null, status: 0 },
        messages: updatePending(state.messages, () => ({
          id: data.assistant_message_id ?? null,
          key: data.assistant_message_id ? `m-${data.assistant_message_id}` : 'error-assistant',
          content: data.message,
          status: 'error',
        })),
      };
    default:
      return state;
  }
};

export const chatReducer = (state, action) => {
  switch (action.type) {
    case 'CONVERSATIONS_LOADED':
      return { ...state, conversations: action.conversations };

    case 'CONVERSATION_SELECTED':
      return { ...state, activeId: action.id, messages: [], phase: 'loading', tool: null, error: null, draft: '' };

    case 'NEW_CHAT':
      // No server call: the conversation is created with the first question, so empty ones never pile up.
      return { ...state, activeId: null, messages: [], phase: 'idle', tool: null, error: null, draft: '' };

    case 'LOAD_FAILED':
      return { ...state, phase: 'idle', error: action.error };

    case 'MESSAGES_LOADED':
      if (action.conversationId !== state.activeId) return state; // the user already moved on
      return { ...state, messages: action.messages.map(normalizeMessage), phase: 'idle' };

    case 'CONVERSATION_CREATED':
      return {
        ...state,
        conversations: [action.conversation, ...state.conversations.filter((c) => c.id !== action.conversation.id)],
        activeId: action.conversation.id,
        messages: [],
        phase: 'idle',
        error: null,
      };

    case 'CONVERSATION_RENAMED':
      return {
        ...state,
        conversations: state.conversations.map((c) => (c.id === action.conversation.id ? action.conversation : c)),
      };

    case 'CONVERSATION_DELETED': {
      const wasOpen = state.activeId === action.id;
      return {
        ...state,
        conversations: state.conversations.filter((c) => c.id !== action.id),
        ...(wasOpen ? { activeId: null, messages: [], phase: 'idle', tool: null } : {}),
      };
    }

    case 'SEND_STARTED':
      return {
        ...state,
        phase: 'sending',
        error: null,
        draft: '',
        tool: null,
        messages: [
          ...state.messages,
          { key: `tmp-user-${action.nonce}`, id: null, role: 'user', content: action.content, status: 'sending', citations: [], feedback: null, createdAt: null },
          { key: `tmp-assistant-${action.nonce}`, id: null, role: 'assistant', content: '', status: 'streaming', citations: [], feedback: null, createdAt: null },
        ],
      };

    case 'STREAM_EVENT':
      return handleStreamEvent(state, action);

    case 'SEND_REJECTED':
      // Nothing was stored server-side: take the optimistic messages back and return the text to the composer.
      return {
        ...state,
        phase: 'idle',
        tool: null,
        draft: action.content,
        error: action.error,
        messages: state.messages.filter((m) => !isUserPending(m) && !isAssistantPending(m)),
      };

    case 'STREAM_FAILED':
      return {
        ...state,
        phase: 'idle',
        tool: null,
        error: action.error,
        messages: updatePending(state.messages, () => ({ status: 'error' })),
      };

    case 'VOTE_CHANGED':
      return {
        ...state,
        messages: state.messages.map((m) => (m.id === action.messageId ? { ...m, feedback: action.value } : m)),
      };

    case 'ERROR_DISMISSED':
      return { ...state, error: null, draft: '' };

    default:
      return state;
  }
};
