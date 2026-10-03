import React from 'react';
import { Link } from 'react-router-dom';
import Revelar from './Revelar';

const BASE =
    'tw-group tw-relative tw-flex tw-h-full tw-w-full tw-flex-col tw-overflow-hidden tw-rounded-2xl tw-border tw-border-rule tw-bg-paper-raised tw-p-6 tw-text-left tw-no-underline tw-text-inherit tw-cursor-pointer tw-transition-all tw-duration-300 hover:-tw-translate-y-1 hover:tw-border-magenta/40 hover:tw-shadow-[0_14px_32px_rgba(22,24,29,0.10)] focus-visible:tw-outline-none focus-visible:tw-ring-2 focus-visible:tw-ring-azul/40';

// Moves a soft magenta glow under the cursor (see the overlay's CSS vars).
const seguirCursor = (evento) => {
    const caja = evento.currentTarget.getBoundingClientRect();
    evento.currentTarget.style.setProperty('--x', `${evento.clientX - caja.left}px`);
    evento.currentTarget.style.setProperty('--y', `${evento.clientY - caja.top}px`);
};

const AccionCard = ({ folio, titulo, descripcion, cta, to, onClick, retraso = 0 }) => {
    const contenido = (
        <>
            <span
                aria-hidden="true"
                className="tw-pointer-events-none tw-absolute tw-inset-0 tw-opacity-0 tw-transition-opacity tw-duration-300 group-hover:tw-opacity-100"
                style={{
                    background:
                        'radial-gradient(260px circle at var(--x, 50%) var(--y, 50%), rgba(196,0,95,0.10), transparent 70%)',
                }}
            />
            <span className="tw-relative tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-widest tw-text-magenta tw-mb-3">
                {folio}
            </span>
            <span className="tw-relative tw-block tw-font-sans tw-text-lg tw-font-bold tw-text-ink tw-mb-2">
                {titulo}
            </span>
            {descripcion && (
                <p className="tw-relative tw-text-ink-soft tw-text-sm tw-leading-relaxed tw-m-0 tw-mb-4">
                    {descripcion}
                </p>
            )}
            <span className="tw-relative tw-mt-auto tw-pt-4 tw-inline-flex tw-items-center tw-gap-1.5 tw-text-sm tw-font-semibold tw-text-azul">
                {cta}
                <span className="tw-transition-transform tw-duration-300 group-hover:tw-translate-x-1">→</span>
            </span>
        </>
    );

    return (
        <Revelar retraso={retraso} className="tw-h-full">
            {to ? (
                <Link to={to} className={BASE} onMouseMove={seguirCursor}>
                    {contenido}
                </Link>
            ) : (
                <button type="button" onClick={onClick} className={BASE} onMouseMove={seguirCursor}>
                    {contenido}
                </button>
            )}
        </Revelar>
    );
};

export default AccionCard;
