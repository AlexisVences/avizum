import React, { useState } from 'react';
import umaConfig from '../../content/guia/config/uma.json';
import { convertirUmaAPesos } from '../../utils/umaCalculator';

const UmaCalculadora = () => {
    const [cantidad, setCantidad] = useState('');
    const sinDatos = umaConfig.valorDiario === null;
    const resultado = sinDatos ? null : convertirUmaAPesos(cantidad, umaConfig.valorDiario);

    if (sinDatos) {
        return (
            <div className="tw-border tw-border-rule tw-rounded tw-p-5">
                <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                    Todavía no tenemos cargado el valor oficial de la UMA. Vuelve pronto.
                </p>
            </div>
        );
    }

    return (
        <div className="tw-border tw-border-rule tw-rounded tw-p-5">
            <label className="tw-block tw-text-sm tw-font-semibold tw-text-ink tw-mb-2" htmlFor="uma-input">
                Cantidad en UMA
            </label>
            <input
                id="uma-input"
                type="number"
                min="0"
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                className="tw-w-full tw-border tw-border-azul tw-rounded tw-px-3 tw-py-2 tw-font-mono tw-text-azul focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
            />
            <p className="tw-mt-4 tw-text-ink tw-text-lg tw-font-semibold">
                {resultado === null ? '—' : `$${resultado.toLocaleString('es-MX', { minimumFractionDigits: 2 })} MXN`}
            </p>
        </div>
    );
};

export default UmaCalculadora;
