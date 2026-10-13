import React from 'react';

const LABELS = {
  buscar_legislacion: 'Buscando en la legislación…',
  obtener_articulo: 'Leyendo el artículo…',
  buscar_agente: 'Consultando la lista oficial de agentes…',
  calcular_multa: 'Calculando el monto…',
};

export default function ToolIndicator({ tool }) {
  if (!tool) return null;
  return (
    <p role="status" className="tw-mt-2 tw-flex tw-items-center tw-gap-2 tw-text-sm tw-text-ink-soft">
      <span aria-hidden="true" className="tw-inline-block tw-h-2 tw-w-2 tw-animate-pulse tw-rounded-full tw-bg-magenta" />
      {LABELS[tool.name] || 'Consultando las fuentes…'}
    </p>
  );
}
