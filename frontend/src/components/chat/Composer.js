import React, { useEffect, useRef, useState } from 'react';
import { FaArrowUp } from 'react-icons/fa';

// `canSend` is false while an answer is generating or loading: the button is disabled, but the person can keep
// typing their next question. The server enforces the same rule (409), this only makes it visible.
// `variant="hero"` is the big pill of the empty state; `"dock"` is the same pill, smaller, pinned under a conversation.
export default function Composer({ onSend, canSend, draft = '', maxChars = 2000, variant = 'dock' }) {
  const hero = variant === 'hero';
  const [text, setText] = useState('');
  const areaRef = useRef(null);

  useEffect(() => {
    if (draft) setText(draft); // a refused message comes back so nothing typed is lost
  }, [draft]);

  const trimmed = text.trim();
  const tooLong = text.length > maxChars;
  const showCounter = text.length >= maxChars * 0.8; // quiet until it matters
  const ready = canSend && trimmed.length > 0 && !tooLong;

  const submit = () => {
    if (!ready) return;
    onSend(trimmed);
    setText('');
    areaRef.current?.focus();
  };

  return (
    <form
      className={hero ? 'tw-w-full' : 'tw-shrink-0 tw-px-4 tw-pb-3 tw-pt-2 sm:tw-px-6'}
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <div
        className={`tw-mx-auto tw-flex tw-w-full tw-items-center tw-gap-3 tw-bg-ink/[.06] tw-transition-colors focus-within:tw-bg-ink/[.09] ${
          hero ? 'tw-min-h-[76px] tw-max-w-[740px] tw-rounded-[38px] tw-py-3 tw-pl-8 tw-pr-3' : 'tw-min-h-[60px] tw-max-w-3xl tw-rounded-[30px] tw-py-2 tw-pl-6 tw-pr-2'
        }`}
      >
        <textarea
          ref={areaRef}
          value={text}
          rows={1}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent?.isComposing) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder={hero ? 'Escribe tu pregunta de tránsito' : 'Escribe tu pregunta de tránsito…'}
          aria-label="Tu pregunta"
          className={`tw-max-h-32 tw-min-w-0 tw-flex-1 tw-resize-none tw-border-0 tw-bg-transparent tw-p-0 tw-text-ink placeholder:tw-text-ink-soft focus:tw-outline-none ${
            hero ? 'tw-text-base sm:tw-text-lg' : 'tw-text-base'
          }`}
          style={{ fieldSizing: 'content' }}
        />
        {showCounter && (
          <span className={`tw-shrink-0 tw-text-xs ${tooLong ? 'tw-text-danger' : 'tw-text-ink-soft'}`} aria-live="polite">
            {text.length}/{maxChars}
          </span>
        )}
        <button
          type="submit"
          disabled={!ready}
          aria-label="Enviar pregunta"
          className={`tw-flex tw-shrink-0 tw-items-center tw-justify-center tw-rounded-full tw-border-0 tw-bg-magenta tw-text-white tw-transition-colors disabled:tw-cursor-not-allowed disabled:tw-bg-ink/[.1] disabled:tw-text-ink-soft ${
            hero ? 'tw-h-[52px] tw-w-[52px]' : 'tw-h-11 tw-w-11'
          }`}
        >
          <FaArrowUp aria-hidden="true" size={hero ? 18 : 15} />
        </button>
      </div>
      <p
        data-testid="chat-disclaimer"
        className="tw-mx-auto tw-mb-0 tw-mt-2 tw-max-w-3xl tw-text-center tw-text-xs tw-text-ink-soft"
      >
        Avizum ofrece información general sobre el reglamento de tránsito y no sustituye a un abogado. Verifica siempre con la
        fuente oficial citada.
      </p>
    </form>
  );
}
