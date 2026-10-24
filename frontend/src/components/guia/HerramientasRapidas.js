import React from 'react';
import { getHerramientas } from '../../services/guiaService';
import UmaCalculadora from './UmaCalculadora';
import VerificacionCalculadora from './VerificacionCalculadora';

const HERRAMIENTAS_COMPONENTES = {
    'uma-a-pesos': UmaCalculadora,
    'cuando-verifico': VerificacionCalculadora,
};

const HerramientasRapidas = () => {
    const herramientas = getHerramientas().filter((herramienta) => HERRAMIENTAS_COMPONENTES[herramienta.slug]);

    return (
        <div className="tw-max-w-5xl tw-mx-auto tw-grid tw-grid-cols-1 md:tw-grid-cols-2 tw-gap-6">
            {herramientas.map((herramienta) => {
                const Calculadora = HERRAMIENTAS_COMPONENTES[herramienta.slug];
                return (
                    <div key={herramienta.slug}>
                        <h3 className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink tw-mb-1">
                            {herramienta.titulo}
                        </h3>
                        <p className="tw-text-ink-soft tw-text-sm tw-mb-3">{herramienta.descripcion}</p>
                        <Calculadora />
                    </div>
                );
            })}
        </div>
    );
};

export default HerramientasRapidas;
