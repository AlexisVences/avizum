import React from 'react';
import { Link } from 'react-router-dom';

const CategoriaCard = ({ categoria }) => (
    <Link
        to={`/guia/${categoria.slug}`}
        className="tw-block tw-bg-paper-raised tw-border tw-border-rule tw-rounded tw-px-5 tw-py-4 tw-no-underline tw-text-inherit hover:tw-border-azul tw-transition-colors"
    >
        <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-1.5">
            {categoria.numero} · {categoria.etiqueta}
        </span>
        <span className="tw-block tw-text-ink tw-font-semibold tw-text-sm">
            {categoria.titulo}
        </span>
    </Link>
);

export default CategoriaCard;
