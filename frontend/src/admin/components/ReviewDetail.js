import React, { useState } from 'react';
import MessageContent from '../../components/chat/MessageContent';
import CitationChips from '../../components/chat/CitationChips';
import { getEvalCase } from '../../services/adminService';

export const NOTE_LIMIT = 500;

const focusRing =
    'focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';
const primaryButton = `tw-min-h-[44px] tw-rounded tw-bg-magenta tw-px-4 tw-py-2 tw-text-white disabled:tw-opacity-50 ${focusRing}`;
const secondaryButton = `tw-min-h-[44px] tw-rounded tw-border tw-border-rule tw-bg-paper-raised tw-px-4 tw-py-2 tw-text-ink disabled:tw-opacity-50 ${focusRing}`;

// The queue sends camelCase citations without the chat's markers. The chat components want snake_case keys, `n`
// (the "[n]" written in the text) and `orden` (position of use). The agent stores citations in order of first
// appearance, so the k-th distinct marker in the text belongs to the k-th citation.
export const toChatCitations = (answer, citations) => {
    const markers = [];
    for (const match of String(answer || '').matchAll(/\[(\d{1,3})\]/g)) {
        const n = Number(match[1]);
        if (!markers.includes(n)) markers.push(n);
    }
    return (citations || []).map((c, index) => ({
        n: markers[index] ?? index + 1,
        orden: index + 1,
        source_slug: c.sourceSlug,
        source_title: c.sourceTitle,
        article: c.article,
        fraction: c.fraction,
        page: c.page,
        url: c.url,
    }));
};

// `onMarkReviewed(note)` must reject with an Error whose message is shown to the person.
const ReviewDetail = ({ item, onMarkReviewed, onBack }) => {
    const [note, setNote] = useState(item.note || '');
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [copy, setCopy] = useState({ status: 'idle', line: '', message: null });

    const citations = toChatCitations(item.answer, item.citations);

    const save = async () => {
        setSaving(true);
        setSaveError(null);
        try {
            await onMarkReviewed(note.trim() ? note.trim() : null);
        } catch (err) {
            setSaveError(err?.message || 'No pudimos marcar la respuesta como revisada. Intenta de nuevo.');
            setSaving(false);
        }
    };

    const copyCase = async () => {
        setCopy({ status: 'working', line: '', message: null });
        let line;
        try {
            line = JSON.stringify(await getEvalCase(item.messageId));
        } catch (err) {
            setCopy({ status: 'error', line: '', message: err?.message || 'No pudimos preparar el caso de evaluación.' });
            return;
        }
        try {
            if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable');
            await navigator.clipboard.writeText(line);
            setCopy({ status: 'copied', line, message: null });
        } catch (err) {
            setCopy({
                status: 'error',
                line,
                message: 'No pudimos copiar al portapapeles. Copia la línea de abajo a mano.',
            });
        }
    };

    return (
        <section aria-label="Detalle de la respuesta" className="tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-5">
            <button type="button" onClick={onBack} className={`tw-mb-4 tw-text-azul md:tw-hidden ${focusRing}`}>
                Volver a la lista
            </button>

            <h2 className="tw-text-sm tw-font-semibold tw-text-ink-soft">Pregunta</h2>
            <p className="tw-mt-1 tw-whitespace-pre-wrap tw-break-words tw-text-lg tw-text-ink">{item.question}</p>

            <h2 className="tw-mt-6 tw-text-sm tw-font-semibold tw-text-ink-soft">Respuesta</h2>
            <div className="tw-mt-1 tw-break-words tw-text-ink">
                {item.answer ? (
                    <MessageContent content={item.answer} citations={citations} />
                ) : (
                    <p className="tw-text-ink-soft">Esta pregunta no recibió respuesta.</p>
                )}
                <CitationChips citations={citations} />
                {item.answer && citations.length === 0 && (
                    <p className="tw-mt-3 tw-text-sm tw-text-ink-soft">La respuesta no cita ninguna fuente.</p>
                )}
            </div>

            <h2 className="tw-mt-6 tw-text-sm tw-font-semibold tw-text-ink-soft">Herramientas consultadas</h2>
            {item.tools.length > 0 ? (
                <ul className="tw-mt-1 tw-flex tw-list-none tw-flex-wrap tw-gap-2 tw-p-0">
                    {item.tools.map((tool) => (
                        <li key={tool} className="tw-rounded tw-bg-gris tw-px-2 tw-py-0.5 tw-font-mono tw-text-sm">
                            {tool}
                        </li>
                    ))}
                </ul>
            ) : (
                <p className="tw-mt-1 tw-text-ink-soft">No consultó ninguna herramienta.</p>
            )}

            {item.reviewed ? (
                <div className="tw-mt-6">
                    <h2 className="tw-text-sm tw-font-semibold tw-text-ink-soft">Nota</h2>
                    <p className="tw-mt-1 tw-whitespace-pre-wrap tw-break-words">{item.note || 'Sin nota.'}</p>
                    <p className="tw-mt-2 tw-text-verde">Esta respuesta ya está revisada.</p>
                </div>
            ) : (
                <div className="tw-mt-6">
                    <label htmlFor={`nota-${item.messageId}`} className="tw-text-sm tw-font-semibold tw-text-ink-soft">
                        Nota
                    </label>
                    <textarea
                        id={`nota-${item.messageId}`}
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        rows={3}
                        className={`tw-mt-1 tw-block tw-w-full tw-rounded tw-border tw-border-rule tw-bg-white tw-px-3 tw-py-2 ${focusRing}`}
                    />
                    <p className={`tw-mt-1 tw-text-sm ${note.length > NOTE_LIMIT ? 'tw-text-danger' : 'tw-text-ink-soft'}`}>
                        {`${note.length} / ${NOTE_LIMIT}`}
                    </p>
                </div>
            )}

            {saveError && (
                <p role="alert" className="tw-mt-3 tw-text-danger">
                    {saveError}
                </p>
            )}

            <div className="tw-mt-4 tw-flex tw-flex-wrap tw-gap-3">
                {!item.reviewed && (
                    <button type="button" onClick={save} disabled={saving} className={primaryButton}>
                        Marcar como revisada
                    </button>
                )}
                <button type="button" onClick={copyCase} disabled={copy.status === 'working'} className={secondaryButton}>
                    Copiar como caso de evaluación
                </button>
                {copy.status === 'copied' && (
                    <span role="status" className="tw-self-center tw-text-verde">
                        Copiado
                    </span>
                )}
            </div>

            {copy.status === 'error' && (
                <div className="tw-mt-3">
                    <p role="alert" className="tw-text-danger">
                        {copy.message}
                    </p>
                    {copy.line && (
                        <>
                            <label htmlFor="caso-evaluacion" className="tw-mt-2 tw-block tw-text-sm tw-text-ink-soft">
                                Caso de evaluación
                            </label>
                            <textarea
                                id="caso-evaluacion"
                                readOnly
                                value={copy.line}
                                rows={3}
                                onFocus={(e) => e.target.select()}
                                className={`tw-mt-1 tw-block tw-w-full tw-rounded tw-border tw-border-rule tw-bg-white tw-px-3 tw-py-2 tw-font-mono tw-text-sm ${focusRing}`}
                            />
                        </>
                    )}
                </div>
            )}
        </section>
    );
};

export default ReviewDetail;
