import React, { useEffect, useRef, useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';

// `canSend` is false while an answer is generating or loading: the button is disabled, but the person can keep
// typing their next question. The server enforces the same rule (409), this only makes it visible.
export default function Composer({ onSend, canSend, draft = '', maxChars = 2000 }) {
  const [text, setText] = useState('');
  const areaRef = useRef(null);

  useEffect(() => {
    if (draft) setText(draft); // a refused message comes back so nothing typed is lost
  }, [draft]);

  const trimmed = text.trim();
  const tooLong = text.length > maxChars;
  const ready = canSend && trimmed.length > 0 && !tooLong;

  const submit = () => {
    if (!ready) return;
    onSend(trimmed);
    setText('');
    areaRef.current?.focus();
  };

  return (
    <form
      className="tw-shrink-0 tw-border-t tw-border-rule tw-bg-paper tw-px-4 tw-py-3 sm:tw-px-6"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <div className="tw-mx-auto tw-flex tw-max-w-3xl tw-items-end tw-gap-2">
        <div className="tw-relative tw-flex-1">
          <textarea
            ref={areaRef}
            value={text}
            rows={2}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent?.isComposing) {
                event.preventDefault();
                submit();
              }
            }}
            placeholder="Escribe tu pregunta de tránsito…"
            aria-label="Tu pregunta"
            className="tw-w-full tw-resize-none tw-rounded-xl tw-border tw-border-rule tw-bg-paper-raised tw-px-4 tw-py-3 tw-pb-6 tw-text-ink focus:tw-border-azul focus:tw-outline-none"
          />
          <span
            className={`tw-pointer-events-none tw-absolute tw-bottom-1.5 tw-right-3 tw-text-xs ${tooLong ? 'tw-text-danger' : 'tw-text-ink-soft'}`}
            aria-live="polite"
          >
            {text.length}/{maxChars}
          </span>
        </div>
        <button
          type="submit"
          disabled={!ready}
          aria-label="Enviar pregunta"
          className="tw-flex tw-h-12 tw-w-12 tw-shrink-0 tw-items-center tw-justify-center tw-rounded-xl tw-bg-magenta tw-text-white tw-transition-opacity disabled:tw-cursor-not-allowed disabled:tw-opacity-40"
        >
          <FaPaperPlane aria-hidden="true" />
        </button>
      </div>
      <p className="tw-mx-auto tw-mt-2 tw-max-w-3xl tw-text-center tw-text-xs tw-text-ink-soft">
        Información orientativa; no sustituye asesoría legal.
      </p>
    </form>
  );
}
