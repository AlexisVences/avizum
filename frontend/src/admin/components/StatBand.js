import React, { useId } from 'react';

const Stat = ({ label, value, hint }) => {
    const id = useId();
    return (
        <div role="group" aria-labelledby={id} className="tw-bg-paper-raised tw-px-4 tw-py-4 sm:tw-px-5">
            <p id={id} className="tw-text-sm tw-text-ink-soft">{label}</p>
            <p className="tw-mt-1 tw-font-display tw-text-3xl tw-font-semibold tw-leading-tight tw-text-ink [font-variant-numeric:tabular-nums]">
                {value}
            </p>
            {hint && <p className="tw-mt-1 tw-text-sm tw-text-ink-soft">{' '}{hint}</p>}
        </div>
    );
};

// Una sola banda: las celdas se separan con divisores finos (gap-px sobre fondo de regla).
const StatBand = ({ items }) => (
    <div className="tw-grid tw-grid-cols-2 tw-gap-px tw-overflow-hidden tw-rounded-lg tw-border tw-border-rule tw-bg-rule md:tw-grid-cols-3 2xl:tw-grid-cols-6">
        {items.map((item) => (
            <Stat key={item.label} {...item} />
        ))}
    </div>
);

export default StatBand;
