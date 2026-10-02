import React, { useState } from 'react';
import verificacionConfig from '../../content/guia/config/verificacion.json';
import { obtenerPeriodoVerificacion } from '../../utils/verificacionCalculator';

const VerificacionCalculadora = () => {
    const [digito, setDigito] = useState('');
    const sinDatos = !verificacionConfig.calendario || verificacionConfig.calendario.length === 0;
    const resultado = sinDatos ? null : obtenerPeriodoVerificacion(digito, verificacionConfig.calendario);

    if (sinDatos) {
        return (
            <div className="tw-border tw-border-rule tw-rounded tw-p-5">
                <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                    Todavía no tenemos cargado el calendario oficial de verificación. Vuelve pronto.
                </p>
            </div>
        );
    }

    return (
        <div className="tw-border tw-border-rule tw-rounded tw-p-5">
            <label className="tw-block tw-text-sm tw-font-semibold tw-text-ink tw-mb-2" htmlFor="placa-digito">
                Último dígito de tu placa
            </label>
            <input
                id="placa-digito"
                type="number"
                min="0"
                max="9"
                value={digito}
                onChange={(e) => setDigito(e.target.value)}
                className="tw-w-full tw-border tw-border-azul tw-rounded tw-px-3 tw-py-2 tw-font-mono tw-text-azul focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
            />
            <p className="tw-mt-4 tw-text-ink tw-text-lg tw-font-semibold">
                {resultado ? `${resultado.periodo} · ${resultado.color}` : '—'}
            </p>
        </div>
    );
};

export default VerificacionCalculadora;
