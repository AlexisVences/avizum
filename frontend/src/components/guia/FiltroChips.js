import React from 'react';

const FiltroChips = ({ bloques, activo, onSelect }) => (
    <div className="tw-flex tw-flex-wrap tw-gap-2 tw-justify-center" role="group" aria-label="Filtrar por bloque">
        {bloques.map((bloque) => (
            <button
                key={bloque}
                type="button"
                onClick={() => onSelect(bloque)}
                aria-pressed={activo === bloque}
                className={`tw-rounded-full tw-px-4 tw-py-1.5 tw-text-sm tw-font-semibold tw-border tw-transition-colors ${
                    activo === bloque
                        ? 'tw-bg-ink tw-text-white tw-border-ink'
                        : 'tw-bg-transparent tw-text-ink tw-border-ink/20 hover:tw-border-ink/50'
                }`}
            >
                {bloque}
            </button>
        ))}
    </div>
);

export default FiltroChips;
