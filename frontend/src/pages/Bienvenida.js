import React, { useRef, useState } from "react";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import authService from "../services/authService";
import { buscarEnGuia } from "../services/guiaService";
import BuscadorGuia from "../components/guia/BuscadorGuia";
import FiltroChips from "../components/guia/FiltroChips";
import CategoriaCard from "../components/guia/CategoriaCard";
import HeroBienvenida from "../components/bienvenida/HeroBienvenida";
import AccionCard from "../components/bienvenida/AccionCard";
import Revelar from "../components/bienvenida/Revelar";

const BLOQUES = ["Todo", "Leyes y derechos", "Multas y sanciones", "Tu auto", "En el camino", "Herramientas"];

const nombreDeSesion = () => {
    try {
        const usuario = authService.getCurrentUser();
        return usuario && usuario.nombre ? usuario.nombre : '';
    } catch (error) {
        return '';
    }
};

const Bienvenida = () => {
    const guiaRef = useRef(null);
    const [busqueda, setBusqueda] = useState('');
    const [bloqueActivo, setBloqueActivo] = useState('Todo');

    const categoriasVisibles = buscarEnGuia(busqueda).filter(
        (categoria) => bloqueActivo === 'Todo' || categoria.bloque === bloqueActivo
    );

    return (
        <>
            <NavBar2 />
            <main className="tw-flex-1 tw-bg-gris">
                <HeroBienvenida nombre={nombreDeSesion()} />

                {/* Índice de servicios */}
                <section className="tw-bg-paper tw-px-6 tw-pb-16">
                    <div className="tw-mx-auto tw-max-w-5xl tw-grid tw-grid-cols-1 md:tw-grid-cols-3 tw-gap-5">
                        <AccionCard
                            folio="01 · ASESORÍA"
                            titulo="Asesoría legal gratuita"
                            to="/asesoria-ia"
                            cta="Entrar"
                            retraso={0}
                        />
                        <AccionCard
                            folio="02 · RECURSOS"
                            titulo="Guía del conductor"
                            descripcion="Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto en la CDMX."
                            onClick={() => guiaRef.current && guiaRef.current.scrollIntoView({ behavior: 'smooth' })}
                            cta="Explorar"
                            retraso={0.12}
                        />
                        <AccionCard
                            folio="03 · AGENTES"
                            titulo="Consultar agentes facultados"
                            to="/ConsultarAgenteTransito"
                            cta="Verificar"
                            retraso={0.24}
                        />
                    </div>
                </section>

                {/* Guía del conductor */}
                <section id="guia" ref={guiaRef} className="tw-bg-gris tw-px-6 tw-py-16">
                    <Revelar>
                        <div className="tw-max-w-3xl tw-mx-auto tw-text-center tw-mb-8">
                            <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                                02 · RECURSOS
                            </span>
                            <h2 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-3">
                                Guía del conductor <span className="tw-text-magenta">en la CDMX</span>
                            </h2>
                            <p className="tw-text-ink-soft">
                                Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto — organizado por tema, para que encuentres justo lo que necesitas.
                            </p>
                        </div>
                    </Revelar>

                    <div className="tw-max-w-3xl tw-mx-auto tw-mb-6">
                        <BuscadorGuia value={busqueda} onChange={setBusqueda} />
                    </div>

                    <div className="tw-max-w-3xl tw-mx-auto tw-mb-8">
                        <FiltroChips bloques={BLOQUES} activo={bloqueActivo} onSelect={setBloqueActivo} />
                    </div>

                    <div className="tw-max-w-5xl tw-mx-auto">
                        {categoriasVisibles.length === 0 ? (
                            <p className="tw-text-center tw-text-ink-soft">
                                No encontramos categorías que coincidan con tu búsqueda.
                            </p>
                        ) : (
                            <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 md:tw-grid-cols-3 tw-gap-4">
                                {categoriasVisibles.map((categoria, indice) => (
                                    <Revelar key={categoria.slug} retraso={Math.min(indice, 5) * 0.06}>
                                        <CategoriaCard categoria={categoria} />
                                    </Revelar>
                                ))}
                            </div>
                        )}
                    </div>
                </section>
            </main>
            <Footer className="tw-pt-0" />
        </>
    );
};

export default Bienvenida;
