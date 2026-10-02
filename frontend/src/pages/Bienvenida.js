import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import "../styles/Bienvenida.css";
import fondoHome from "../assets/home.png";
import ConsultaLegal from "../assets/ConsultaLegal.png";
// import multa from "../assets/multa.jpg";
import agentes from "../assets/agentes.jpg";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import { buscarEnGuia } from "../services/guiaService";
import BuscadorGuia from "../components/guia/BuscadorGuia";
import FiltroChips from "../components/guia/FiltroChips";
import CategoriaCard from "../components/guia/CategoriaCard";

// import { consultarAgente } from '../services/agentesService';

const BLOQUES = ["Todo", "Leyes y derechos", "Multas y sanciones", "Tu auto", "En el camino", "Herramientas"];

const Bienvenida = () => {
    const guiaRef = useRef(null);
    const [busqueda, setBusqueda] = useState('');
    const [bloqueActivo, setBloqueActivo] = useState('Todo');
    // const [placaBusqueda, setPlacaBusqueda] = useState('');
    // const [agenteEncontrado, setAgenteEncontrado] = useState(null);
    // const [errorBusqueda, setErrorBusqueda] = useState(null);
    // const [cargando, setCargando] = useState(false);

    const categoriasVisibles = buscarEnGuia(busqueda).filter(
        (categoria) => bloqueActivo === 'Todo' || categoria.bloque === bloqueActivo
    );

    return (
        <>
        <NavBar2 />
        <div className="bienvenida-container">
            <div
            className="hero-section"
            style={{ backgroundImage: `url(${fondoHome})` }}
            >
            <div className="hero-overlay">
                <motion.div
                className="welcome-box text-center p-5 rounded-4 shadow-lg"
                initial={{ opacity: 0, y: -50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 1 }}
                >
                <h1 className="display-4">Bienvenido a Amicuz</h1>
                <p className="lead mt-3">
                    Tu plataforma de confianza para resolver cualquier situación legal de tránsito.
                </p>
                </motion.div>
            </div>
            </div>

            {/* Texto de guía */}
            <div className="container text-center mt-5">
            <h2 className="display-4 text-dark mb-2">
                ¿Cómo podemos ayudarte?
            </h2>
            <h5 className="fw-light text-muted">
                Elige la opción que mejor se acomode a tus necesidades
            </h5>
            </div>
            <br />

            {/* Índice de servicios */}
            <div className="container servicios-grid py-4">
            <div className="row g-4">
                <motion.div
                    className="col-12 col-md-4 d-flex justify-content-center align-items-center"
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0 }}
                    viewport={{ once: true }}
                >
                    <Link to="/asesoria-ia" className="text-decoration-none text-white w-100">
                        <div className="card servicio-card text-white text-center border-0 rounded-4 overflow-hidden shadow-lg h-100">
                            <div className="card-img-wrapper">
                                <img src={ConsultaLegal} className="card-img-top img-fluid" alt="Asesoría legal gratuita" />
                            </div>
                            <div className="card-body bg-dark bg-opacity-75">
                                <h5 className="card-title fw-bold mb-0">Asesoría legal gratuita</h5>
                            </div>
                        </div>
                    </Link>
                </motion.div>

                <motion.div
                    className="col-12 col-md-4 d-flex justify-content-center align-items-center"
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    viewport={{ once: true }}
                >
                    <div className="tw-w-full tw-h-full tw-max-w-[330px] tw-mx-auto tw-bg-paper-raised tw-border tw-border-rule tw-rounded-2xl tw-shadow-lg tw-p-4 tw-flex tw-flex-col">
                        <span className="tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-2">
                            02 · RECURSOS
                        </span>
                        <h5 className="tw-font-sans tw-font-bold tw-text-ink tw-mb-2">Guía del conductor</h5>
                        <p className="tw-text-ink-soft tw-text-sm tw-flex-1">
                            Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto en la CDMX.
                        </p>
                        <button
                            type="button"
                            onClick={() => guiaRef.current && guiaRef.current.scrollIntoView({ behavior: 'smooth' })}
                            className="tw-self-start tw-bg-ink tw-text-white tw-font-semibold tw-text-sm tw-rounded tw-px-4 tw-py-2 tw-border-0 hover:tw-bg-ink/90"
                        >
                            Explorar →
                        </button>
                    </div>
                </motion.div>

                <motion.div
                    className="col-12 col-md-4 d-flex justify-content-center align-items-center"
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.4 }}
                    viewport={{ once: true }}
                >
                    <Link to="/ConsultarAgenteTransito" className="text-decoration-none text-white w-100">
                        <div className="card servicio-card text-white text-center border-0 rounded-4 overflow-hidden shadow-lg h-100">
                            <div className="card-img-wrapper">
                                <img src={agentes} className="card-img-top img-fluid" alt="Consultar agentes facultados" />
                            </div>
                            <div className="card-body bg-dark bg-opacity-75">
                                <h5 className="card-title fw-bold mb-0">Consultar agentes facultados</h5>
                            </div>
                        </div>
                    </Link>
                </motion.div>
            </div>
            </div>

            {/* Sección de Consulta de agentes */}
            {/*
            <div ref={agentesRef} className="container py-5">
            <hr className="my-5 border border-dark border-2 opacity-75" />
            <h3 className="fw-bold text-center mb-3">
                Consultar agentes de tránsito facultados para infraccionar sobre vía pública
            </h3>
            <p className="fw-light text-center text-muted">
                Esta herramienta te permite verificar si un agente de tránsito está autorizado para levantar infracciones en la Ciudad de México. Los datos fueron recopilados de la Gaceta Oficial de la CDMX.
            </p>
            <div className="my-4 text-center">
                <input
                type="text"
                className="form-control w-50 mx-auto"
                placeholder="Ingresa el número de placa del agente"
                value={placaBusqueda}
                onChange={(e) => setPlacaBusqueda(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleBuscarAgente()}
                />
                <button 
                    className="btn btn-primary mt-3"
                    onClick={handleBuscarAgente}
                    disabled={cargando}
                >
                    {cargando ? 'Buscando...' : 'Buscar Agente'}
                </button>
            </div>
            <div className="mx-auto rounded" style={{ maxWidth: "600px" }}>
                {cargando ? (
                            <div className="text-center p-4">
                                <div className="spinner-border text-primary" role="status">
                                </div>
                            </div>
                        ) : errorBusqueda ? (
                            <div className="alert alert-danger text-center">
                                {errorBusqueda}
                            </div>
                        ) : agenteEncontrado ? (
                            <div className="card">
                                <div className="card-body">
                                    <h5 className="card-title">Información del Agente</h5>
                                    <p className="card-text">
                                        <strong>Placa:</strong> {agenteEncontrado.agente?.placa}<br />
                                        <strong>Nombre:</strong> {agenteEncontrado.agente?.nombre}<br />
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="alert alert-info text-center">
                                Ingresa una placa para buscar agentes facultados
                            </div>
                        )}
            </div>
            </div>*/}

            {/* Guía del conductor */}
            <div id="guia" ref={guiaRef} className="container py-5">
                <hr className="my-5 border border-dark border-2 opacity-75" />
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
                            {categoriasVisibles.map((categoria) => (
                                <CategoriaCard key={categoria.slug} categoria={categoria} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
        <Footer />
        </>
    );
};

export default Bienvenida;
