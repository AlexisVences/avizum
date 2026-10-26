import React from 'react';

const botonClases =
    'tw-rounded tw-border tw-border-rule tw-bg-paper-raised tw-px-3 tw-py-1.5 tw-text-ink disabled:tw-opacity-50 focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';

const Pagination = ({ page, pageSize, total, onChange }) => {
    if (total <= 0) {
        return <p className="tw-text-ink-soft">Sin resultados</p>;
    }
    const desde = (page - 1) * pageSize + 1;
    const hasta = Math.min(page * pageSize, total);
    return (
        <nav aria-label="Paginación" className="tw-flex tw-items-center tw-justify-between tw-gap-4">
            <p className="tw-text-ink-soft">{`Mostrando ${desde}–${hasta} de ${total}`}</p>
            <div className="tw-flex tw-gap-2">
                <button type="button" className={botonClases} disabled={page <= 1} onClick={() => onChange(page - 1)}>
                    Anterior
                </button>
                <button type="button" className={botonClases} disabled={hasta >= total} onClick={() => onChange(page + 1)}>
                    Siguiente
                </button>
            </div>
        </nav>
    );
};

export default Pagination;
