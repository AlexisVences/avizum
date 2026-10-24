import React from 'react';
import { Link } from 'react-router-dom';

const CLASE_TARJETA =
    'tw-block tw-w-full tw-text-left tw-bg-paper-raised tw-border tw-border-rule tw-rounded tw-px-5 tw-py-4 tw-no-underline tw-text-inherit hover:tw-border-azul tw-transition-colors';

// Con `onSeleccionar` la tarjeta no navega: ejecuta la acción (p. ej. deslizar
// a una sección de la misma página).
const CategoriaCard = ({ categoria, onSeleccionar }) => {
    const contenido = (
        <>
            <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-1.5">
                {categoria.numero} · {categoria.etiqueta}
            </span>
            <span className="tw-block tw-text-ink tw-font-semibold tw-text-sm">
                {categoria.titulo}
            </span>
        </>
    );

    if (onSeleccionar) {
        return (
            <button type="button" onClick={onSeleccionar} className={`${CLASE_TARJETA} tw-cursor-pointer`}>
                {contenido}
            </button>
        );
    }

    return (
        <Link to={`/guia/${categoria.slug}`} className={CLASE_TARJETA}>
            {contenido}
        </Link>
    );
};

export default CategoriaCard;
