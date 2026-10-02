import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getHerramientaPorSlug } from '../services/guiaService';
import UmaCalculadora from '../components/guia/UmaCalculadora';
import VerificacionCalculadora from '../components/guia/VerificacionCalculadora';

const HERRAMIENTAS_COMPONENTES = {
    'uma-a-pesos': UmaCalculadora,
    'cuando-verifico': VerificacionCalculadora,
};

const GuiaCalculadora = () => {
    const { herramientaSlug } = useParams();
    const herramienta = getHerramientaPorSlug(herramientaSlug);
    const Calculadora = HERRAMIENTAS_COMPONENTES[herramientaSlug];

    if (!herramienta || !Calculadora) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">404</p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos esta herramienta
                        </h1>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
                    <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                        17 · CÁLCULO
                    </span>
                    <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-2">
                        {herramienta.titulo}
                    </h1>
                    <p className="tw-text-ink-soft tw-mb-8">{herramienta.descripcion}</p>
                    <Calculadora />
                </div>
            </main>
            <Footer />
        </>
    );
};

export default GuiaCalculadora;
