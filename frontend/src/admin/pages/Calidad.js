import React, { useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Pagination from '../components/Pagination';
import ReviewDetail from '../components/ReviewDetail';
import useAdminList from '../hooks/useAdminList';
import { listReviewQueue, markReviewed } from '../../services/adminService';
import { fieldClasses, focusRing } from '../format';

const PAGE_SIZE = 20;
const TIME_ZONE = 'America/Mexico_City';


const REASONS = [
    { value: 'negative', label: 'Mal calificada' },
    { value: 'error', label: 'Con error' },
    { value: 'uncited', label: 'Sin citas' },
];
const REASON_LABEL = Object.fromEntries(REASONS.map(({ value, label }) => [value, label]));

const dateFormat = new Intl.DateTimeFormat('es-MX', {
    timeZone: TIME_ZONE,
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
});

const tabClasses = (active) =>
    `tw-min-h-[44px] tw-border-b-2 tw-px-4 tw-py-2 ${
        active ? 'tw-border-magenta tw-font-semibold tw-text-magenta' : 'tw-border-transparent tw-text-ink-soft'
    } ${focusRing}`;

const Calidad = () => {
    const [reviewed, setReviewed] = useState(false);
    const [reason, setReason] = useState('');
    const [page, setPage] = useState(1);
    const [selectedId, setSelectedId] = useState(null);
    const [detailOpen, setDetailOpen] = useState(false);
    const [removed, setRemoved] = useState([]);

    const params = { reason: reason || undefined, reviewed, page, pageSize: PAGE_SIZE };
    const { data, loading, error, reload } = useAdminList(listReviewQueue, params);

    const items = (data?.items || []).filter((it) => !removed.includes(it.messageId));
    const total = Math.max((data?.total || 0) - (data ? data.items.length - items.length : 0), 0);
    const selected = items.find((it) => it.messageId === selectedId) || items[0] || null;

    // Si la página quedó fuera de rango, vuelve a la última real.
    useEffect(() => {
        if (data && data.items.length === 0 && data.total > 0 && page > 1) {
            setPage(Math.ceil(data.total / PAGE_SIZE));
        }
    }, [data, page]);

    const changeView = (apply) => {
        apply();
        setPage(1);
        setRemoved([]);
        setSelectedId(null);
        setDetailOpen(false);
    };

    const handleMarkReviewed = async (note) => {
        const current = selected;
        await markReviewed(current.messageId, note);
        const index = items.findIndex((it) => it.messageId === current.messageId);
        const next = items[index + 1] || items[index - 1] || null;
        setRemoved((prev) => [...prev, current.messageId]);
        setSelectedId(next ? next.messageId : null);
        setDetailOpen(false);
        reload();
    };

    let content;
    if (error) {
        content = <ErrorState message={error} onRetry={reload} />;
    } else if (!data) {
        content = <Skeleton lines={6} />;
    } else if (items.length === 0 && total > 0) {
        content = <p className="tw-text-ink-soft">Cargando la siguiente página…</p>;
    } else if (items.length === 0) {
        content = reason ? (
            <EmptyState
                title="No hay respuestas con este motivo"
                hint="Prueba con otro motivo o quita el filtro."
                action={
                    <button
                        type="button"
                        onClick={() => changeView(() => setReason(''))}
                        className={`tw-rounded tw-bg-magenta tw-px-4 tw-py-2 tw-text-white ${focusRing}`}
                    >
                        Quitar filtro
                    </button>
                }
            />
        ) : reviewed ? (
            <EmptyState title="Todavía no hay respuestas revisadas" hint="Las que marques como revisadas aparecerán aquí." />
        ) : (
            <EmptyState
                title="No hay respuestas por revisar"
                hint="Aquí llegan las respuestas mal calificadas, con error o sin citas."
            />
        );
    } else {
        content = (
            <div className="md:tw-grid md:tw-grid-cols-[minmax(280px,380px)_1fr] md:tw-items-start md:tw-gap-6">
                <div className={detailOpen ? 'tw-hidden md:tw-block' : undefined}>
                    <ul
                        aria-label="Respuestas"
                        aria-busy={loading}
                        className={`tw-m-0 tw-list-none tw-space-y-2 tw-p-0 ${loading ? 'tw-opacity-60' : ''}`}
                    >
                        {items.map((it) => {
                            const active = selected && it.messageId === selected.messageId;
                            return (
                                <li key={it.messageId}>
                                    <button
                                        type="button"
                                        aria-current={active ? 'true' : undefined}
                                        onClick={() => {
                                            setSelectedId(it.messageId);
                                            setDetailOpen(true);
                                        }}
                                        className={`tw-block tw-w-full tw-rounded-lg tw-border tw-p-3 tw-text-left ${
                                            active ? 'tw-border-magenta tw-bg-white' : 'tw-border-rule tw-bg-paper-raised'
                                        } ${focusRing}`}
                                    >
                                        <span className="tw-flex tw-flex-wrap tw-items-center tw-gap-2 tw-text-sm tw-text-ink-soft">
                                            <time dateTime={it.askedAt}>{dateFormat.format(new Date(it.askedAt))}</time>
                                            {it.reasons.map((r) => (
                                                <span key={r} className="tw-rounded tw-bg-gris tw-px-2 tw-py-0.5 tw-text-ink">
                                                    {REASON_LABEL[r] || r}
                                                </span>
                                            ))}
                                        </span>
                                        <span className="tw-mt-1 tw-line-clamp-2 tw-block tw-break-words tw-text-ink">
                                            {it.question}
                                        </span>
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                    <div className="tw-mt-4">
                        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
                    </div>
                </div>
                <div className={detailOpen ? undefined : 'tw-hidden md:tw-block'}>
                    {selected && (
                        <ReviewDetail
                            key={selected.messageId}
                            item={selected}
                            onMarkReviewed={handleMarkReviewed}
                            onBack={() => setDetailOpen(false)}
                        />
                    )}
                </div>
            </div>
        );
    }

    return (
        <>
            <PageHeader
                title="Calidad"
                description="Respuestas que conviene revisar. No incluyen el nombre ni el correo de quien preguntó."
            />
            <div className="tw-mb-6 tw-flex tw-flex-wrap tw-items-end tw-justify-between tw-gap-4">
                <div role="tablist" aria-label="Estado de revisión" className="tw-flex tw-gap-2">
                    <button
                        type="button"
                        role="tab"
                        aria-selected={!reviewed}
                        className={tabClasses(!reviewed)}
                        onClick={() => changeView(() => setReviewed(false))}
                    >
                        Por revisar
                    </button>
                    <button
                        type="button"
                        role="tab"
                        aria-selected={reviewed}
                        className={tabClasses(reviewed)}
                        onClick={() => changeView(() => setReviewed(true))}
                    >
                        Revisadas
                    </button>
                </div>
                <label className="tw-block tw-w-full sm:tw-w-auto sm:tw-min-w-[200px]">
                    <span className="tw-text-sm tw-text-ink-soft">Motivo</span>
                    <select
                        value={reason}
                        onChange={(e) => changeView(() => setReason(e.target.value))}
                        className={`${fieldClasses} tw-w-full`}
                    >
                        <option value="">Todos</option>
                        {REASONS.map(({ value, label }) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            {content}
        </>
    );
};

export default Calidad;
