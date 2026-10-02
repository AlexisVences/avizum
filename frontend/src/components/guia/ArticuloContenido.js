import React from 'react';
import { Link } from 'react-router-dom';

const ArticuloContenido = ({ categoria, articulo }) => (
    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
        <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
            {categoria.numero} · {categoria.etiqueta}
        </span>
        <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-2">
            {articulo.titulo}
        </h1>
        <p className="tw-font-mono tw-text-[12px] tw-text-ink-soft tw-mb-8">
            Actualizado: {articulo.actualizado}
            {articulo.fuentes && articulo.fuentes.length > 0 && (
                <> · Fuente: {articulo.fuentes.map((f) => f.nombre).join(', ')}</>
            )}
        </p>

        {articulo.tipo === 'documentos' && articulo.documentos && (
            <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-3 tw-mb-10">
                {articulo.documentos.map((doc) => (
                    <li
                        key={doc.url}
                        className="tw-flex tw-flex-wrap tw-items-center tw-gap-3 tw-border tw-border-rule tw-rounded tw-px-4 tw-py-3.5"
                    >
                        <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-magenta tw-bg-magenta/10 tw-rounded tw-px-2 tw-py-1">
                            {doc.tipo}
                        </span>
                        <span className="tw-flex-1 tw-min-w-[200px] tw-text-ink tw-font-semibold tw-text-sm">
                            {doc.titulo}
                        </span>
                        <a
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="tw-text-azul hover:tw-text-magenta tw-text-sm tw-font-bold tw-no-underline"
                        >
                            PDF ↗
                        </a>
                    </li>
                ))}
            </ul>
        )}

        {articulo.tipo === 'prosa' && (
            <div className="tw-text-ink tw-leading-relaxed tw-mb-10 tw-whitespace-pre-line">
                {articulo.cuerpo}
            </div>
        )}

        {articulo.mito_realidad && articulo.mito_realidad.length > 0 && (
            <div className="tw-flex tw-flex-col tw-gap-4 tw-mb-10">
                {articulo.mito_realidad.map((par, index) => (
                    <div key={index} className="tw-border tw-border-rule tw-rounded tw-overflow-hidden">
                        <div className="tw-bg-magenta/10 tw-px-4 tw-py-3">
                            <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-magenta">MITO</span>
                            <p className="tw-text-ink tw-text-sm tw-m-0 tw-mt-1">{par.mito}</p>
                        </div>
                        <div className="tw-bg-verde/10 tw-px-4 tw-py-3">
                            <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-verde">REALIDAD</span>
                            <p className="tw-text-ink tw-text-sm tw-m-0 tw-mt-1">{par.realidad}</p>
                        </div>
                    </div>
                ))}
            </div>
        )}

        {articulo.fuentes && articulo.fuentes.length > 0 && (
            <div className="tw-border-t tw-border-rule tw-pt-6 tw-mb-10">
                <p className="tw-font-semibold tw-text-ink tw-text-sm tw-mb-3">Fuentes</p>
                <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-2">
                    {articulo.fuentes.map((fuente) => (
                        <li key={fuente.url}>
                            <a href={fuente.url} target="_blank" rel="noopener noreferrer" className="tw-text-azul hover:tw-text-magenta tw-text-sm">
                                {fuente.nombre}
                            </a>
                        </li>
                    ))}
                </ul>
            </div>
        )}

        <Link
            to="/asesoria-ia"
            className="tw-inline-flex tw-items-center tw-gap-2 tw-bg-ink tw-text-white tw-font-semibold tw-text-sm tw-rounded tw-px-5 tw-py-2.5 tw-no-underline hover:tw-bg-ink/90"
        >
            ¿Dudas? Pregúntale a la IA legal →
        </Link>
    </div>
);

export default ArticuloContenido;
