import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import verificacionConfig from '../../content/guia/config/verificacion.json';
import umaConfig from '../../content/guia/config/uma.json';
import { obtenerPeriodoVerificacion } from '../../utils/verificacionCalculator';
import { convertirUmaAPesos } from '../../utils/umaCalculator';

const VerificacionCalculadora = () => {
    const [digito, setDigito] = useState('');
    const sinDatos = !verificacionConfig.calendario || verificacionConfig.calendario.length === 0;
    const resultado = sinDatos ? null : obtenerPeriodoVerificacion(digito, verificacionConfig.calendario);
    const multaExtemporanea =
        umaConfig.valorDiario === null ? null : convertirUmaAPesos(20, umaConfig.valorDiario);

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
            {resultado ? (
                <div className="tw-mt-4">
                    <p className="tw-text-ink tw-text-lg tw-font-semibold tw-m-0">
                        Engomado {resultado.color.toLowerCase()}
                    </p>
                    <ul className="tw-list-none tw-p-0 tw-mt-2 tw-mb-3 tw-text-ink tw-font-semibold">
                        <li>1.er semestre: {resultado.periodos[0]}</li>
                        <li>2.º semestre: {resultado.periodos[1]}</li>
                    </ul>
                    <p className="tw-text-ink-soft tw-text-sm tw-mt-0 tw-mb-3">
                        Si no verificas dentro de tu periodo, es verificación extemporánea:{' '}
                        multa de 20 UMA
                        {multaExtemporanea !== null &&
                            ` (≈ $${multaExtemporanea.toLocaleString('es-MX', { minimumFractionDigits: 2 })} MXN)`}
                        .
                    </p>
                    <a
                        href={verificacionConfig.fuente}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="tw-text-azul hover:tw-text-magenta tw-font-semibold tw-text-sm"
                    >
                        Ver verificentros cercanos (SEDEMA) ↗
                    </a>
                    <p className="tw-text-ink-soft tw-text-sm tw-mt-3 tw-mb-0">
                        Consulta casos particulares y excepciones con nuestro{' '}
                        <Link to="/asesoria-ia" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            asesor de IA
                        </Link>
                    </p>
                </div>
            ) : (
                <p className="tw-mt-4 tw-text-ink tw-text-lg tw-font-semibold tw-m-0">—</p>
            )}
        </div>
    );
};

export default VerificacionCalculadora;
