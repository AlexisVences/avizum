import { act, renderHook, waitFor } from '@testing-library/react';
import useChat from '../useChat';
import * as chat from '../../services/chatService';

jest.mock('../../services/chatService', () => ({
  ...jest.requireActual('../../services/chatService'),
  listConversations: jest.fn(),
  createConversation: jest.fn(),
  renameConversation: jest.fn(),
  deleteConversation: jest.fn(),
  listMessages: jest.fn(),
  setFeedback: jest.fn(),
  clearFeedback: jest.fn(),
  streamMessage: jest.fn(),
}));

const { ChatError } = jest.requireActual('../../services/chatService');
const conversation = (id, title = null) => ({ id, title, created_at: 'x', updated_at: 'y' });
const serverMessage = (overrides) => ({ id: 1, role: 'assistant', content: 'r', status: 'complete', citations: null, created_at: 'x', feedback: null, ...overrides });

const happyStream = async ({ onEvent }) => {
  onEvent('message_start', { user_message_id: 10 });
  onEvent('tool_start', { name: 'buscar_legislacion', args: {} });
  onEvent('tool_end', { name: 'buscar_legislacion', ok: true });
  onEvent('token', { text: 'Sí ' });
  onEvent('token', { text: '[1] y [99].' });
  onEvent('citations', [{ n: 1, orden: 1, article: '44', url: 'https://x#page=56' }]);
  onEvent('done', { assistant_message_id: 11, text: 'Sí [1].', usage: {} });
};

const mounted = async () => {
  const hook = renderHook(() => useChat());
  await waitFor(() => expect(chat.listConversations).toHaveBeenCalled());
  return hook;
};

beforeEach(() => {
  jest.resetAllMocks();
  chat.listConversations.mockResolvedValue([conversation(1, 'Placas')]);
  chat.listMessages.mockResolvedValue([]);
});

test('loads the conversation list on mount', async () => {
  const { result } = await mounted();
  await waitFor(() => expect(result.current.conversations).toEqual([conversation(1, 'Placas')]));
  expect(result.current.canSend).toBe(true);
});

test('selecting a conversation loads and shows its messages', async () => {
  chat.listMessages.mockResolvedValue([serverMessage({ id: 5, role: 'user', content: 'hola' }), serverMessage({ id: 6, content: 'respuesta [1]', citations: [{ n: 1 }], feedback: 1 })]);
  const { result } = await mounted();
  await act(async () => { await result.current.selectConversation(1); });
  expect(result.current.activeId).toBe(1);
  expect(result.current.messages.map((m) => [m.role, m.feedback])).toEqual([['user', null], ['assistant', 1]]);
});

test('the first question creates the conversation, streams the answer and refreshes the list', async () => {
  chat.createConversation.mockResolvedValue(conversation(2));
  chat.streamMessage.mockImplementation(happyStream);
  chat.listConversations.mockResolvedValueOnce([]).mockResolvedValue([conversation(2, '¿placas?')]);
  const { result } = await mounted();

  await act(async () => { await result.current.send('  ¿placas?  '); });

  expect(chat.createConversation).toHaveBeenCalledTimes(1);
  expect(chat.streamMessage.mock.calls[0][0]).toMatchObject({ conversationId: 2, content: '¿placas?' });
  expect(result.current.phase).toBe('idle');
  expect(result.current.messages.map((m) => m.content)).toEqual(['¿placas?', 'Sí [1].']); // canonical text, not the raw tokens
  expect(result.current.messages[1].citations[0].article).toBe('44');
  await waitFor(() => expect(result.current.conversations[0].title).toBe('¿placas?'));
});

test('while an answer is being generated a second send is ignored', async () => {
  chat.createConversation.mockResolvedValue(conversation(2));
  let finish;
  chat.streamMessage.mockImplementation(({ onEvent }) => new Promise((resolve) => {
    onEvent('message_start', { user_message_id: 10 });
    finish = resolve;
  }));
  const { result } = await mounted();

  act(() => { result.current.send('primera'); });
  await waitFor(() => expect(result.current.phase).toBe('streaming'));
  expect(result.current.canSend).toBe(false);

  await act(async () => { await result.current.send('segunda'); });
  expect(chat.streamMessage).toHaveBeenCalledTimes(1);

  await act(async () => { finish(); });
});

test('a refusal such as the daily limit gives the text back and explains why', async () => {
  chat.createConversation.mockResolvedValue(conversation(2));
  chat.streamMessage.mockRejectedValue(new ChatError('Llegaste al límite de 40 mensajes por día.', { status: 429, code: 'limite_diario' }));
  const { result } = await mounted();

  await act(async () => { await result.current.send('otra pregunta'); });

  expect(result.current.messages).toEqual([]);
  expect(result.current.draft).toBe('otra pregunta');
  expect(result.current.error).toMatchObject({ status: 429, code: 'limite_diario', message: 'Llegaste al límite de 40 mensajes por día.' });
  expect(result.current.canSend).toBe(true);
});

test('losing the connection mid-stream reloads the conversation from the server', async () => {
  chat.createConversation.mockResolvedValue(conversation(2));
  chat.streamMessage.mockImplementation(async ({ onEvent }) => {
    onEvent('message_start', { user_message_id: 10 });
    onEvent('token', { text: 'Parcial' });
    throw new TypeError('network error');
  });
  chat.listMessages.mockResolvedValue([serverMessage({ id: 10, role: 'user', content: 'hola' }), serverMessage({ id: 11, content: 'La respuesta completa se guardó' })]);
  const { result } = await mounted();

  await act(async () => { await result.current.send('hola'); });

  expect(result.current.error.code).toBe('conexion');
  expect(result.current.messages.map((m) => m.content)).toEqual(['hola', 'La respuesta completa se guardó']);
});

test('a thumb toggles, pressing it again removes the vote, and a server failure reverts it', async () => {
  chat.listMessages.mockResolvedValue([serverMessage({ id: 6 })]);
  chat.setFeedback.mockResolvedValue(null);
  chat.clearFeedback.mockResolvedValue(null);
  const { result } = await mounted();
  await act(async () => { await result.current.selectConversation(1); });

  await act(async () => { await result.current.vote(6, 1); });
  expect(result.current.messages[0].feedback).toBe(1);
  expect(chat.setFeedback).toHaveBeenCalledWith(6, 1);

  await act(async () => { await result.current.vote(6, 1); });
  expect(result.current.messages[0].feedback).toBeNull();
  expect(chat.clearFeedback).toHaveBeenCalledWith(6);

  chat.setFeedback.mockRejectedValue(new ChatError('Error', { status: 500 }));
  await act(async () => { await result.current.vote(6, -1); });
  expect(result.current.messages[0].feedback).toBeNull(); // reverted
  expect(result.current.error.status).toBe(500);
});

test('a new chat creates nothing on the server until a question is sent', async () => {
  const { result } = await mounted();
  await act(async () => { await result.current.selectConversation(1); });
  act(() => { result.current.startNew(); });
  expect(result.current.activeId).toBeNull();
  expect(chat.createConversation).not.toHaveBeenCalled();
});

test('leaving the page aborts the request in flight', async () => {
  chat.createConversation.mockResolvedValue(conversation(2));
  let signal;
  chat.streamMessage.mockImplementation(({ signal: s }) => { signal = s; return new Promise(() => {}); });
  const { result, unmount } = await mounted();
  act(() => { result.current.send('hola'); });
  await waitFor(() => expect(signal).toBeDefined());

  unmount();
  expect(signal.aborted).toBe(true);
});

test('renaming and deleting update the list', async () => {
  chat.renameConversation.mockResolvedValue(conversation(1, 'Nuevo nombre'));
  chat.deleteConversation.mockResolvedValue(null);
  const { result } = await mounted();
  await waitFor(() => expect(result.current.conversations).toHaveLength(1));

  await act(async () => { await result.current.renameConversation(1, 'Nuevo nombre'); });
  expect(result.current.conversations[0].title).toBe('Nuevo nombre');
  await act(async () => { await result.current.removeConversation(1); });
  expect(result.current.conversations).toEqual([]);
});
