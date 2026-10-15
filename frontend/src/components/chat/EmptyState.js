import React from 'react';
import Composer from './Composer';

// Chips show a short label; the full question is what gets asked.
const SUGGESTIONS = [
  { label: 'Me pusieron un inmovilizador', question: '¿Qué puedo hacer si me ponen un inmovilizador en el coche?' },
  { label: 'Verificar a un agente', question: '¿Cómo verifico si un agente de tránsito está autorizado para multarme?' },
  { label: 'Plazo para impugnar una multa', question: '¿Cuánto tiempo tengo para impugnar una multa y ante quién?' },
];

// One focus: the question box. The glow (styles/AsesoriaIA.css) sits behind it.
export default function EmptyState({ onSend, canSend, draft }) {
  return (
    <div className="asesoria-glow tw-flex tw-min-h-0 tw-flex-1 tw-flex-col tw-items-center tw-overflow-y-auto">
      <div className="tw-flex tw-w-full tw-flex-1 tw-flex-col tw-items-center tw-justify-center tw-gap-9 tw-px-4 tw-pb-[72px] tw-pt-16 sm:tw-px-6">
        <h1 className="tw-m-0 tw-text-center tw-font-display tw-text-[40px] tw-font-normal tw-leading-[1.05] tw-tracking-[-0.02em] tw-text-ink sm:tw-text-[56px]">
          ¿En qué te <em className="tw-italic">ayudo</em>?
        </h1>
        <p className="tw-m-0 tw-max-w-[500px] tw-text-center tw-text-base tw-leading-relaxed tw-text-ink-soft">
          Respondo con base en la legislación vigente de la Ciudad de México y te indico en qué artículo y página me apoyo.
        </p>
        <Composer variant="hero" onSend={onSend} canSend={canSend} draft={draft} />
        <ul className="tw-m-0 tw-flex tw-max-w-[740px] tw-list-none tw-flex-wrap tw-justify-center tw-gap-3 tw-p-0">
          {SUGGESTIONS.map(({ label, question }) => (
            <li key={label}>
              <button
                type="button"
                onClick={() => onSend(question)}
                className="tw-h-11 tw-rounded-full tw-border-0 tw-bg-ink/[.06] tw-px-5 tw-text-sm tw-text-ink tw-transition-colors hover:tw-bg-ink/[.1]"
              >
                {label}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <p className="tw-m-0 tw-shrink-0 tw-px-4 tw-pb-5 tw-text-center tw-text-xs tw-text-ink-soft">
        Información orientativa; no sustituye asesoría legal.
      </p>
    </div>
  );
}
