import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import Skeleton from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import StatBand from '../components/StatBand';
import DailyChart from '../components/DailyChart';
import useAdminList from '../hooks/useAdminList';
import { getOverview } from '../../services/adminService';

const PERIODS = [7, 30, 90];
const focusRing =
    'focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';

const integer = new Intl.NumberFormat('es-MX');

// Porcentaje entero que nunca miente en los extremos: <100 no se redondea a 100 ni un valor distinto de 0 a 0.
export const formatPercent = (rate) => {
    const value = rate * 100;
    if (value > 0 && value < 1) return '<1 %';
    const rounded = Math.round(value);
    return `${rounded >= 100 && value < 100 ? 99 : rounded} %`;
};

// Formatea el costo desde el texto del servidor, sin aritmética de punto flotante.
export const formatCost = (cost) => {
    const [whole = '0', fraction = ''] = String(cost).split('.');
    const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    const extra = fraction.slice(2).replace(/0+$/, '');
    return `US$ ${grouped}.${fraction.slice(0, 2).padEnd(2, '0')}${extra}`;
};

const buildItems = (data) => {
    const satisfaction =
        data.feedbackRate === null
            ? { value: 'Sin calificaciones' }
            : {
                  value: formatPercent(data.feedbackRate),
                  hint: `de ${integer.format(data.feedbackRated)} calificaciones`,
              };
    const errors =
        data.errorRate === null
            ? { value: 'Sin respuestas' }
            : {
                  value: integer.format(data.answersWithError),
                  hint: `${formatPercent(data.errorRate)} de las respuestas`,
              };
    return [
        { label: 'Preguntas', value: integer.format(data.questions) },
        { label: 'Personas activas', value: integer.format(data.activeUsers) },
        { label: 'Satisfacción', ...satisfaction },
        { label: 'Respuestas con error', ...errors },
        {
            label: 'Costo estimado',
            value: formatCost(data.costUsd),
            hint: 'Calculado con los precios de lista del modelo',
        },
        { label: 'Consultas de agentes', value: integer.format(data.agentLookups) },
    ];
};

const PeriodSelector = ({ days, onChange }) => (
    <div role="radiogroup" aria-label="Periodo" className="tw-inline-flex tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-0.5">
        {PERIODS.map((value) => (
            <label key={value} className="tw-m-0 tw-cursor-pointer">
                <input
                    type="radio"
                    name="periodo"
                    value={value}
                    checked={days === value}
                    onChange={() => onChange(value)}
                    className="tw-peer tw-sr-only"
                />
                <span
                    className={`tw-block tw-rounded-md tw-px-3 tw-py-1.5 tw-text-sm tw-text-ink-soft peer-checked:tw-bg-magenta peer-checked:tw-text-white peer-focus-visible:tw-outline peer-focus-visible:tw-outline-2 peer-focus-visible:tw-outline-offset-2 peer-focus-visible:tw-outline-azul`}
                >
                    {value} días
                </span>
            </label>
        ))}
    </div>
);

const Attention = ({ items }) => (
    <section aria-labelledby="atencion" className="tw-mt-8">
        <h2 id="atencion" className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink">
            Requiere atención
        </h2>
        {items.length === 0 ? (
            <p className="tw-mt-2 tw-text-ink-soft">Todo al día</p>
        ) : (
            <ul className="tw-m-0 tw-mt-3 tw-list-none tw-divide-y tw-divide-rule tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-0">
                {items.map((item) => (
                    <li key={item.kind}>
                        <Link
                            to={item.href}
                            className={`tw-flex tw-items-center tw-justify-between tw-gap-3 tw-px-4 tw-py-3 tw-text-azul tw-no-underline hover:tw-underline ${focusRing}`}
                        >
                            <span>{`${item.count} ${item.label}`}</span>
                            <span aria-hidden="true">→</span>
                        </Link>
                    </li>
                ))}
            </ul>
        )}
    </section>
);

const Resumen = () => {
    const [days, setDays] = useState(30);
    const { data, loading, error, reload } = useAdminList(getOverview, { days });

    return (
        <>
            <PageHeader title="Resumen" actions={<PeriodSelector days={days} onChange={setDays} />} />
            {error ? (
                <ErrorState message={error} onRetry={reload} />
            ) : !data ? (
                <Skeleton lines={6} />
            ) : (
                <div className={loading ? 'tw-opacity-60' : undefined} aria-busy={loading}>
                    <StatBand items={buildItems(data)} />
                    <section aria-labelledby="serie" className="tw-mt-8">
                        <h2 id="serie" className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink">
                            Preguntas por día
                        </h2>
                        <div className="tw-mt-3 tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-4">
                            <DailyChart points={data.series} />
                        </div>
                    </section>
                    <Attention items={data.attention} />
                </div>
            )}
        </>
    );
};

export default Resumen;
