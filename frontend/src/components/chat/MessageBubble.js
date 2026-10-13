import React from 'react';
import { FaThumbsDown, FaThumbsUp } from 'react-icons/fa';
import CitationChips from './CitationChips';
import MessageContent from './MessageContent';

const Vote = ({ active, label, onClick, children }) => (
  <button
    type="button"
    onClick={onClick}
    aria-label={label}
    aria-pressed={active}
    className={`tw-rounded tw-border-0 tw-p-1.5 tw-text-sm tw-transition-colors ${active ? 'tw-bg-azul/10 tw-text-azul' : 'tw-bg-transparent tw-text-ink-soft hover:tw-text-ink'}`}
  >
    {children}
  </button>
);

export default function MessageBubble({ message, onVote }) {
  const isUser = message.role === 'user';
  const streaming = message.status === 'streaming';

  if (isUser) {
    return (
      <div className="tw-flex tw-justify-end">
        <p className="tw-max-w-[85%] tw-whitespace-pre-wrap tw-rounded-2xl tw-bg-azul tw-px-4 tw-py-2.5 tw-text-white">
          {message.content}
        </p>
      </div>
    );
  }

  const failed = message.status === 'error';
  const canVote = message.status === 'complete' && message.id != null && onVote;

  return (
    <div className="tw-flex tw-justify-start">
      <article
        className={`tw-max-w-[92%] tw-rounded-2xl tw-border tw-px-4 tw-py-3 ${
          failed ? 'tw-border-danger/40 tw-bg-danger/5 tw-text-danger' : 'tw-border-rule tw-bg-paper-raised tw-text-ink'
        }`}
        aria-busy={streaming}
      >
        {streaming && !message.content ? (
          <span className="tw-text-ink-soft" aria-label="Escribiendo">…</span>
        ) : (
          <MessageContent content={message.content} citations={message.citations} streaming={streaming} />
        )}
        {!streaming && !failed && <CitationChips citations={message.citations} />}
        {canVote && (
          <div className="tw-mt-2 tw-flex tw-gap-1">
            <Vote active={message.feedback === 1} label="Respuesta útil" onClick={() => onVote(message.id, 1)}><FaThumbsUp /></Vote>
            <Vote active={message.feedback === -1} label="Respuesta no útil" onClick={() => onVote(message.id, -1)}><FaThumbsDown /></Vote>
          </div>
        )}
      </article>
    </div>
  );
}
