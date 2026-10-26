import React from 'react';

// Three dots that bounce one after the other while the answer is being prepared. With "reduce motion" they stay still.
export default function TypingDots() {
  return (
    <span role="status" aria-label="Escribiendo" className="tw-inline-flex tw-items-center tw-gap-1.5 tw-py-2">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          data-dot
          aria-hidden="true"
          className="tw-inline-block tw-h-2 tw-w-2 tw-animate-dot-bounce tw-rounded-full tw-bg-ink-soft motion-reduce:tw-animate-none"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}
