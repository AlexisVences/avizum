import { useCallback, useEffect, useReducer, useRef } from 'react';
import * as chat from '../services/chatService';
import { chatReducer, initialChatState } from './chatReducer';

const CONNECTION_LOST = 'Se perdió la conexión con el asistente. Revisa la conversación: la respuesta pudo haberse guardado.';

const toError = (error) => ({
  message: error?.message || 'No se pudo completar la solicitud.',
  code: error?.code || null,
  status: error?.status || 0,
});

// Connects the reducer to the chat API. The screen reads state and calls these functions; it never touches fetch.
export default function useChat() {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);
  const stateRef = useRef(state);
  stateRef.current = state;
  const abortRef = useRef(null);
  const nonceRef = useRef(0);

  const refreshConversations = useCallback(async () => {
    try {
      dispatch({ type: 'CONVERSATIONS_LOADED', conversations: await chat.listConversations() });
    } catch (error) {
      dispatch({ type: 'LOAD_FAILED', error: toError(error) });
    }
  }, []);

  useEffect(() => {
    refreshConversations();
    return () => abortRef.current?.abort(); // leaving the page: the server keeps the partial answer as "cancelled"
  }, [refreshConversations]);

  const selectConversation = useCallback(async (id) => {
    if (id === stateRef.current.activeId || stateRef.current.phase === 'sending' || stateRef.current.phase === 'streaming') return;
    dispatch({ type: 'CONVERSATION_SELECTED', id });
    try {
      dispatch({ type: 'MESSAGES_LOADED', conversationId: id, messages: await chat.listMessages(id) });
    } catch (error) {
      dispatch({ type: 'LOAD_FAILED', error: toError(error) });
    }
  }, []);

  const startNew = useCallback(() => {
    if (stateRef.current.phase === 'sending' || stateRef.current.phase === 'streaming') return;
    dispatch({ type: 'NEW_CHAT' });
  }, []);

  const send = useCallback(async (rawContent) => {
    const content = rawContent.trim();
    if (!content || stateRef.current.phase !== 'idle') return; // the same rule the server enforces with a 409

    let conversationId = stateRef.current.activeId;
    if (conversationId == null) {
      try {
        const conversation = await chat.createConversation();
        dispatch({ type: 'CONVERSATION_CREATED', conversation });
        conversationId = conversation.id;
      } catch (error) {
        dispatch({ type: 'SEND_REJECTED', content, error: toError(error) });
        return;
      }
    }

    nonceRef.current += 1;
    dispatch({ type: 'SEND_STARTED', content, nonce: nonceRef.current });
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await chat.streamMessage({
        conversationId,
        content,
        signal: controller.signal,
        onEvent: (event, data) => dispatch({ type: 'STREAM_EVENT', event, data }),
      });
    } catch (error) {
      if (controller.signal.aborted) return;
      if (error?.status) {
        dispatch({ type: 'SEND_REJECTED', content, error: toError(error) }); // refused before anything was stored
      } else {
        dispatch({ type: 'STREAM_FAILED', error: { message: CONNECTION_LOST, code: 'conexion', status: 0 } });
        try {
          // The server may have stored the turn: show its truth instead of the interrupted screen.
          dispatch({ type: 'MESSAGES_LOADED', conversationId, messages: await chat.listMessages(conversationId) });
        } catch {
          /* keep the interrupted view; the error banner already explains it */
        }
      }
      return;
    } finally {
      if (abortRef.current === controller) abortRef.current = null;
    }
    refreshConversations(); // the server set the title and moved the conversation to the top
  }, [refreshConversations]);

  const vote = useCallback(async (messageId, value) => {
    const message = stateRef.current.messages.find((m) => m.id === messageId);
    if (!message) return;
    const previous = message.feedback;
    const next = previous === value ? null : value; // pressing the same thumb again removes the vote
    dispatch({ type: 'VOTE_CHANGED', messageId, value: next });
    try {
      if (next === null) await chat.clearFeedback(messageId);
      else await chat.setFeedback(messageId, next);
    } catch (error) {
      dispatch({ type: 'VOTE_CHANGED', messageId, value: previous });
      dispatch({ type: 'LOAD_FAILED', error: toError(error) });
    }
  }, []);

  const renameConversation = useCallback(async (id, title) => {
    try {
      dispatch({ type: 'CONVERSATION_RENAMED', conversation: await chat.renameConversation(id, title) });
    } catch (error) {
      dispatch({ type: 'LOAD_FAILED', error: toError(error) });
    }
  }, []);

  const removeConversation = useCallback(async (id) => {
    try {
      await chat.deleteConversation(id);
      dispatch({ type: 'CONVERSATION_DELETED', id });
    } catch (error) {
      dispatch({ type: 'LOAD_FAILED', error: toError(error) });
    }
  }, []);

  const dismissError = useCallback(() => dispatch({ type: 'ERROR_DISMISSED' }), []);

  return {
    ...state,
    canSend: state.phase === 'idle',
    send,
    selectConversation,
    startNew,
    vote,
    renameConversation,
    removeConversation,
    dismissError,
  };
}
