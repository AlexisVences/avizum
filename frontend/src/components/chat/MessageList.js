import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import ToolIndicator from './ToolIndicator';

export default function MessageList({ messages, tool, loading, onVote }) {
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
