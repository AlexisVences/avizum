import React from 'react';

const BuscadorGuia = ({ value, onChange }) => (
    <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Busca por tema, por ejemplo: multas, corralón, seguro…"
        aria-label="Buscar en la guía del conductor"
        className="tw-w-full tw-border tw-border-rule tw-rounded tw-px-4 tw-py-2.5 tw-text-sm focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
    />
);

export default BuscadorGuia;
