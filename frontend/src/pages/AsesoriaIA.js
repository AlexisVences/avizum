import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { FaBars } from 'react-icons/fa';
import Composer from '../components/chat/Composer';
import ConversationSidebar from '../components/chat/ConversationSidebar';
import EmptyState from '../components/chat/EmptyState';
import MessageList from '../components/chat/MessageList';
import useChat from '../hooks/useChat';
import '../styles/AsesoriaIA.css';

const ErrorBanner = ({ error, onDismiss, onNewChat }) => {
  if (!error) return null;
  const sessionExpired = error.status === 401;
  return (
    <div role="alert" className="tw-flex tw-shrink-0 tw-flex-wrap tw-items-center tw-gap-3 tw-bg-danger/5 tw-px-4 tw-py-2 tw-text-sm tw-text-danger">
      <span className="tw-flex-1">{sessionExpired ? 'Tu sesión expiró. Inicia sesión de nuevo para continuar.' : error.message}</span>
      {sessionExpired && <a href="/Login" className="tw-font-semibold tw-underline">Iniciar sesión</a>}
      {error.code === 'conversacion_llena' && (
        <button type="button" onClick={onNewChat} className="tw-border-0 tw-bg-transparent tw-font-semibold tw-underline">Nueva conversación</button>
      )}
      <button type="button" onClick={onDismiss} aria-label="Cerrar aviso" className="tw-border-0 tw-bg-transparent tw-font-semibold">Cerrar</button>
    </div>
  );
};

const AsesoriaIA = () => {
  const location = useLocation();
  const chat = useChat();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location]);

  const busy = chat.phase === 'sending' || chat.phase === 'streaming';

  const empty = chat.phase !== 'loading' && chat.messages.length === 0;

  return (
    <div className="tw-flex tw-h-screen tw-flex-col tw-overflow-hidden tw-bg-paper">
      <ErrorBanner error={chat.error} onDismiss={chat.dismissError} onNewChat={() => { chat.startNew(); }} />

      <div className="tw-flex tw-min-h-0 tw-flex-1">
        <ConversationSidebar
          conversations={chat.conversations}
          activeId={chat.activeId}
          busy={busy}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          onSelect={chat.selectConversation}
          onNew={chat.startNew}
          onRename={chat.renameConversation}
          onDelete={chat.removeConversation}
        />
        <main className="tw-relative tw-flex tw-min-w-0 tw-flex-1 tw-flex-col">
          <button
            type="button"
            aria-label="Abrir historial"
            onClick={() => setDrawerOpen(true)}
            className="tw-absolute tw-left-3 tw-top-3 tw-z-10 tw-flex tw-h-11 tw-w-11 tw-items-center tw-justify-center tw-rounded-full tw-border-0 tw-bg-ink/[.06] tw-text-ink md:tw-hidden"
          >
            <FaBars size={15} />
          </button>
          {empty ? (
            <EmptyState onSend={chat.send} canSend={chat.canSend} draft={chat.draft} />
          ) : (
            <>
              <MessageList messages={chat.messages} tool={chat.tool} loading={chat.phase === 'loading'} onVote={chat.vote} />
              <Composer onSend={chat.send} canSend={chat.canSend} draft={chat.draft} />
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default AsesoriaIA;
