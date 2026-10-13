import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import ToolIndicator from './ToolIndicator';

const SUGGESTIONS = [
  '¿Qué puedo hacer si me ponen un inmovilizador en el coche?',
  '¿Cómo verifico si un agente de tránsito está autorizado para multarme?',
  '¿Cuánto tiempo tengo para impugnar una multa y ante quién?',
];

export default function MessageList({ messages, tool, loading, onVote, onSuggest }) {
  const containerRef = useRef(null);
  const last = messages[messages.length - 1];

  useEffect(() => {
    // Scroll only this container, never the page.
    const container = containerRef.current;
    if (container && typeof container.scrollTo === 'function') {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages.length, last?.content, last?.citations?.length, last?.status, tool]);

  if (loading) {
    return <div className="tw-flex-1 tw-p-8 tw-text-center tw-text-ink-soft" role="status">Cargando conversación…</div>;
  }

  if (messages.length === 0) {
    return (
      <div className="tw-flex tw-flex-1 tw-flex-col tw-items-center tw-justify-center tw-gap-6 tw-overflow-y-auto tw-px-4 tw-py-8">
        <div className="tw-text-center">
          <h2 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink">¿En qué te ayudo?</h2>
          <p className="tw-mt-2 tw-max-w-md tw-text-ink-soft">
            Respondo con base en la legislación vigente de la Ciudad de México y te indico en qué artículo y página se apoya.
          </p>
        </div>
        <ul className="tw-m-0 tw-flex tw-w-full tw-max-w-xl tw-list-none tw-flex-col tw-gap-2 tw-p-0">
          {SUGGESTIONS.map((question) => (
            <li key={question}>
              <button
                type="button"
                onClick={() => onSuggest(question)}
                className="tw-w-full tw-rounded-xl tw-border tw-border-rule tw-bg-paper-raised tw-px-4 tw-py-3 tw-text-left tw-text-ink hover:tw-border-azul"
              >
                {question}
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="tw-flex-1 tw-overflow-y-auto tw-px-4 tw-py-4 sm:tw-px-6" aria-live="polite">
      <div className="tw-mx-auto tw-flex tw-max-w-3xl tw-flex-col tw-gap-4">
        {messages.map((message) => (
          <MessageBubble key={message.key} message={message} onVote={onVote} />
        ))}
        <ToolIndicator tool={tool} />
      </div>
    </div>
  );
}
