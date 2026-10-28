import React, { useState } from 'react';
import PageHeader from '../components/PageHeader';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import StatusBadge from '../components/StatusBadge';
import useAdminList from '../hooks/useAdminList';
import { listSources } from '../../services/adminService';

const TIME_ZONE = 'America/Mexico_City';
const NO_PARAMS = {};

const KIND_TITLES = {
    ley: 'Leyes',
    reglamento: 'Reglamentos',
    codigo: 'Códigos',
    protocolo: 'Protocolos',
    acuerdo: 'Acuerdos',
    decreto: 'Decretos',
    programa: 'Programas',
    tarifas: 'Tarifas oficiales',
    ficha: 'Fichas oficiales (páginas web transcritas)',
};

const kindTitle = (kind) => {
    if (KIND_TITLES[kind]) return KIND_TITLES[kind];
    const raw = String(kind ?? 'sin tipo');
    return raw.charAt(0).toUpperCase() + raw.slice(1);
};

const focusRing =
    'focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';

const dayFormat = { day: 'numeric', month: 'short', year: 'numeric' };
// Las fechas «yyyy-mm-dd» son de calendario: se leen como UTC para que no se corran de día.
const calendarFormat = new Intl.DateTimeFormat('es-MX', { ...dayFormat, timeZone: 'UTC' });
const instantFormat = new Intl.DateTimeFormat('es-MX', { ...dayFormat, timeZone: TIME_ZONE });

const formatCalendarDate = (value) => {
    const date = new Date(`${value}T00:00:00Z`);
    return Number.isNaN(date.getTime()) ? null : calendarFormat.format(date);
};

const formatInstant = (value) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : instantFormat.format(date);
};

const dateLine = (source) => {
    const reform = source.lastReformDate ? formatCalendarDate(source.lastReformDate) : null;
    if (reform) return `Reforma: ${reform}`;
    const retrieved = formatInstant(source.retrievedAt);
    return retrieved ? `Consultada/descargada: ${retrieved}` : 'Sin fecha registrada';
};

const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

const groupByKind = (sources) => {
    const groups = new Map();
    sources.forEach((source) => {
        if (!groups.has(source.kind)) groups.set(source.kind, []);
        groups.get(source.kind).push(source);
    });
    return [...groups.entries()];
};

const SourceRow = ({ source }) => {
    const since = source.reviewDueSince ? formatCalendarDate(source.reviewDueSince) : null;
    return (
        <li className="tw-flex tw-flex-col tw-gap-2 tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-4 md:tw-flex-row md:tw-items-center md:tw-gap-6 md:tw-rounded-none md:tw-border-0 md:tw-border-b md:tw-bg-transparent md:tw-px-3 md:tw-py-3">
            <div className="tw-min-w-0 md:tw-flex-1">
                <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`tw-break-words tw-font-semibold tw-text-azul tw-underline ${focusRing}`}
                >
                    {source.title}
                </a>
                <p className="tw-text-sm tw-text-ink-soft">{dateLine(source)}</p>
            </div>
            <p className="tw-text-sm tw-text-ink-soft md:tw-whitespace-nowrap">
                <span>{plural(source.chunkCount, 'fragmento', 'fragmentos')}</span>
                {' · '}
                <span>{plural(source.versions, 'versión', 'versiones')}</span>
            </p>
            <div className="md:tw-w-60 md:tw-text-right">
                {source.reviewDue ? (
                    <StatusBadge tone="warn">
                        {since ? `Por revisar desde ${since}` : 'Por revisar'}
                    </StatusBadge>
                ) : (
                    <StatusBadge tone="ok">Al día</StatusBadge>
                )}
            </div>
        </li>
    );
};

const Fuentes = () => {
    const [onlyDue, setOnlyDue] = useState(false);
    const { data, error, reload } = useAdminList(listSources, NO_PARAMS);

    let body;
    if (error) {
        body = <ErrorState message={error} onRetry={reload} />;
    } else if (!data) {
        body = <Skeleton lines={8} />;
    } else {
        const all = data.sources || [];
        const visible = onlyDue ? all.filter((s) => s.reviewDue) : all;
        const pending = data.pendingSanctions || 0;
        let list;
        if (visible.length === 0) {
            list = onlyDue ? (
                <EmptyState title="No hay fuentes por revisar" hint="Todas las fuentes están al día." />
            ) : (
                <EmptyState
                    title="Todavía no hay fuentes registradas"
                    hint="Se registran con los scripts de la base de conocimiento."
                />
            );
        } else {
            list = groupByKind(visible).map(([kind, items]) => (
                <section key={kind} className="tw-mb-8">
                    <h2 className="tw-mb-2 tw-font-display tw-text-xl tw-font-semibold tw-text-ink">
                        {kindTitle(kind)}
                    </h2>
                    <ul className="tw-m-0 tw-list-none tw-space-y-3 tw-p-0 md:tw-space-y-0 md:tw-border-t md:tw-border-rule">
                        {items.map((source) => (
                            <SourceRow key={source.slug} source={source} />
                        ))}
                    </ul>
                </section>
            ));
        }
        body = (
            <>
                <div className="tw-mb-6 tw-flex tw-flex-wrap tw-items-center tw-justify-between tw-gap-4">
                    <p className="tw-text-ink-soft">
                        {pending > 0 ? (
                            <StatusBadge tone="warn">{`${pending} ${pending === 1 ? 'fila' : 'filas'} de sanciones sin revisar`}</StatusBadge>
                        ) : (
                            <StatusBadge tone="ok">Sanciones al día</StatusBadge>
                        )}
                    </p>
                    <label className="tw-flex tw-min-h-[44px] tw-cursor-pointer tw-items-center tw-gap-2">
                        <input
                            type="checkbox"
                            checked={onlyDue}
                            onChange={(e) => setOnlyDue(e.target.checked)}
                            className={`tw-h-5 tw-w-5 tw-accent-magenta ${focusRing}`}
                        />
                        <span>Solo por revisar</span>
                    </label>
                </div>
                {list}
            </>
        );
    }

    return (
        <>
            <PageHeader
                title="Fuentes"
                description="La actualización se hace con los scripts; aquí solo se vigila."
            />
            {body}
        </>
    );
};

export default Fuentes;
