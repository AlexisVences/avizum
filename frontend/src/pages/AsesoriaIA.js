import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { FaBars } from 'react-icons/fa';
import NavBar2 from '../components/NavBar2';
import Composer from '../components/chat/Composer';
import ConversationSidebar from '../components/chat/ConversationSidebar';
import MessageList from '../components/chat/MessageList';
import useChat from '../hooks/useChat';

const ErrorBanner = ({ error, onDismiss, onNewChat }) => {
  if (!error) return null;
  const sessionExpired = error.status === 401;
  return (
    <div role="alert" className="tw-flex tw-shrink-0 tw-flex-wrap tw-items-center tw-gap-3 tw-border-b tw-border-danger/30 tw-bg-danger/5 tw-px-4 tw-py-2 tw-text-sm tw-text-danger">
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

  return (
    <>
      <NavBar2 />
      <div className="tw-flex tw-h-screen tw-flex-col tw-overflow-hidden tw-bg-paper tw-pt-16">
        <div className="tw-flex tw-shrink-0 tw-items-center tw-gap-3 tw-border-b tw-border-rule tw-px-4 tw-py-3 sm:tw-px-6">
          <button
            type="button"
            aria-label="Abrir historial"
            onClick={() => setDrawerOpen(true)}
            className="tw-flex tw-h-9 tw-w-9 tw-items-center tw-justify-center tw-rounded tw-border tw-border-ink/15 tw-text-ink md:tw-hidden"
          >
            <FaBars size={14} />
          </button>
          <h1 className="tw-m-0 tw-font-display tw-text-base tw-font-semibold tw-text-ink">Asistente de tránsito CDMX</h1>
        </div>

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
          <main className="tw-flex tw-min-w-0 tw-flex-1 tw-flex-col">
            <MessageList
              messages={chat.messages}
              tool={chat.tool}
              loading={chat.phase === 'loading'}
              onVote={chat.vote}
              onSuggest={chat.send}
            />
            <Composer onSend={chat.send} canSend={chat.canSend} draft={chat.draft} />
          </main>
        </div>
      </div>
    </>
  );
};

export default AsesoriaIA;
