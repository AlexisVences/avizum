import React from 'react';
import { Link } from 'react-router-dom';
import Badge from '../ui/Badge';

const ASUNTOS_INTERNOS_URL = 'https://www.ssc.cdmx.gob.mx/organizacion-policial/direcciones-generales/direccion-general-de-asuntos-internos';

const AUTORIZACION = {
    via_publica: {
        etiqueta: 'Vía pública',
        variante: 'verified',
        texto: 'está facultado para infraccionar en la vía pública de la CDMX con equipo electrónico portátil.',
    },
    sistemas_tecnologicos: {
        etiqueta: 'Fotocívicas',
        variante: 'neutral',
        texto: 'está autorizado para firmar boletas emitidas mediante sistemas tecnológicos (fotocívicas).',
    },
};

const linkClase = 'tw-text-azul hover:tw-text-magenta tw-font-semibold';

const Fuente = ({ source }) => (
    <p className="tw-text-[0.78rem] tw-text-ink-soft tw-mt-3 tw-mb-0">
        Fuente oficial:{' '}
        <a href={source.url} target="_blank" rel="noopener noreferrer" className={linkClase}>
            {source.title}
        </a>
    </p>
);

const ResultadoBusquedaAgentes = ({ resultado }) => {
    const { results, source } = resultado;

    if (!source) {
        return (
            <div className="tw-bg-azul/5 tw-border tw-border-azul/20 tw-rounded tw-px-4 tw-py-3.5 tw-text-sm tw-text-ink-soft tw-leading-relaxed">
                El registro oficial de agentes no está disponible en este momento. Consulta directamente la
                Gaceta Oficial de la Ciudad de México.
            </div>
        );
    }

    if (results.length === 0) {
        return (
            <div className="tw-bg-azul/5 tw-border tw-border-azul/20 tw-rounded tw-px-4 tw-py-3.5 tw-text-sm tw-text-ink-soft tw-leading-relaxed">
                <p className="tw-m-0 tw-mb-2">
                    <strong className="tw-text-ink">No aparece en la lista vigente.</strong> Solo el personal
                    publicado en la Gaceta Oficial puede expedir y firmar boletas de tránsito.
                </p>
                <p className="tw-m-0 tw-mb-2">
                    Pide al agente su identificación y número de placa, y no entregues documentos sin que te
                    expida una boleta. Puedes reportar irregularidades ante{' '}
                    <a href={ASUNTOS_INTERNOS_URL} target="_blank" rel="noopener noreferrer" className={linkClase}>
                        Asuntos Internos de la SSC
                    </a>.
                </p>
                <p className="tw-m-0">
                    Si ya te impusieron una boleta, revisa cómo impugnarla en{' '}
                    <Link to="/guia/multas-y-fotocivicas" className={linkClase}>Multas y fotocívicas</Link>.
                </p>
                <Fuente source={source} />
            </div>
        );
    }

    return (
        <div>
            <ul className="tw-list-none tw-p-0 tw-m-0 tw-space-y-3">
                {results.map((agente) => {
                    const autorizacion = AUTORIZACION[agente.authorization_type];
                    return (
                        <li key={`${agente.plate}-${agente.authorization_type}`} className="tw-border tw-border-rule tw-rounded tw-p-4">
                            <div className="tw-flex tw-items-center tw-justify-between tw-mb-2">
                                <span className="tw-font-mono tw-text-lg tw-font-bold tw-text-ink tw-tracking-wider">{agente.plate}</span>
                                <Badge variant={autorizacion.variante}>{autorizacion.etiqueta}</Badge>
                            </div>
                            <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                                <strong className="tw-text-ink">{agente.full_name}</strong> {autorizacion.texto}
                            </p>
                            {agente.corporation && (
                                <p className="tw-text-ink-soft tw-text-sm tw-mt-1 tw-mb-0">Corporación: {agente.corporation}</p>
                            )}
                            {agente.alcaldias && agente.alcaldias.length > 0 && (
                                <p className="tw-text-ink-soft tw-text-sm tw-mt-1 tw-mb-0">Alcaldías: {agente.alcaldias.join(', ')}</p>
                            )}
                        </li>
                    );
                })}
            </ul>
            <Fuente source={source} />
        </div>
    );
};

export default ResultadoBusquedaAgentes;
