import React from 'react';
import { Link } from 'react-router-dom';

// Renders article prose, turning [texto](destino) into links. Internal
// destinations start with "/" and navigate within the SPA; http(s) ones open in
// a new tab. Any other destination is left as plain text.
const PATRON_ENLACE = /\[([^\]]+)\]\(([^)\s]+)\)/g;
const CLASE_ENLACE = 'tw-text-azul hover:tw-text-magenta tw-font-semibold';

const ProsaConEnlaces = ({ texto }) => {
    const partes = [];
    let ultimo = 0;
    let coincidencia;
    PATRON_ENLACE.lastIndex = 0;

    while ((coincidencia = PATRON_ENLACE.exec(texto)) !== null) {
        const [completo, etiqueta, destino] = coincidencia;
        partes.push(texto.slice(ultimo, coincidencia.index));

        if (destino.startsWith('/')) {
            partes.push(
                <Link key={coincidencia.index} to={destino} className={CLASE_ENLACE}>
                    {etiqueta}
                </Link>
            );
        } else if (/^https?:\/\//.test(destino)) {
            partes.push(
                <a
                    key={coincidencia.index}
                    href={destino}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={CLASE_ENLACE}
                >
                    {etiqueta}
                </a>
            );
        } else {
            partes.push(completo);
        }
        ultimo = coincidencia.index + completo.length;
    }
    partes.push(texto.slice(ultimo));

    return <>{partes}</>;
};

export default ProsaConEnlaces;
