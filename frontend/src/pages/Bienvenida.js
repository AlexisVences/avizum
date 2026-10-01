import React, { useRef } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import "../styles/Bienvenida.css";
import fondoHome from "../assets/home.png";
import ConsultaLegal from "../assets/ConsultaLegal.png";
// import multa from "../assets/multa.jpg";
import documentos from "../assets/documentos.png";
import agentes from "../assets/agentes.jpg";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";

// import { consultarAgente } from '../services/agentesService';

const Bienvenida = () => {
    const agentesRef = useRef(null);
    const documentosRef = useRef(null);
    // const [placaBusqueda, setPlacaBusqueda] = useState('');
    // const [agenteEncontrado, setAgenteEncontrado] = useState(null);
    // const [errorBusqueda, setErrorBusqueda] = useState(null);
    // const [cargando, setCargando] = useState(false);

    const servicios = [
        { img: ConsultaLegal, title: "Asesoría legal gratuita" },
        // { img: multa, title: "Consulta de multas" },
        { img: documentos, title: "Guías y recursos legales" },
        { img: agentes, title: "Consultar agentes facultados" },
    ];

    const handleCardClick = (title) => {
        if (title.includes("agentes") && agentesRef.current) {
        agentesRef.current.scrollIntoView({ behavior: "smooth" });
        } else if (title.includes("Guías") && documentosRef.current) {
        documentosRef.current.scrollIntoView({ behavior: "smooth" });
        }
    };

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
            {servicios.map((item, index) => {
                const isAsesoria = item.title === "Asesoría legal gratuita";
                const isAgentes = item.title === "Consultar agentes facultados";

                const cardContent = (
                    <div className="card servicio-card text-white text-center border-0 rounded-4 overflow-hidden shadow-lg h-100">
                    <div className="card-img-wrapper">
                        <img
                        src={item.img}
                        className="card-img-top img-fluid"
                        alt={item.title}
                        />
                    </div>
                    <div className="card-body bg-dark bg-opacity-75">
                        <h5 className="card-title fw-bold mb-0">{item.title}</h5>
                    </div>
                    </div>
                );

                return (
                    <motion.div
                    key={index}
                    className="col-12 col-md-4 d-flex justify-content-center align-items-center"
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.2 }}
                    viewport={{ once: true }}
                    style={{ cursor: "pointer" }}
                    onClick={() => {
                        if (!isAsesoria && !isAgentes) handleCardClick(item.title);
                    }}
                    >
                    {isAsesoria ? (
                        <Link to="/asesoria-ia" className="text-decoration-none text-white w-100">
                        {cardContent}
                        </Link>
                    ) : isAgentes ? (
                        <Link to="/ConsultarAgenteTransito" className="text-decoration-none text-white w-100">
                        {cardContent}
                        </Link>
                    ) : (
                        cardContent
                    )}
                    </motion.div>
                );
                })}


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

            {/* Sección de Documentos legales */}
            <div ref={documentosRef} className="container py-5">
            <hr className="my-5 border border-dark border-2 opacity-75" />
            <h3 className="fw-bold text-center mb-3">
                Documentos legales que rigen el tránsito en la Ciudad de México
            </h3>
            <p className="text-center text-muted fw-light mb-4">
                Estos documentos constituyen el marco jurídico bajo el cual operan tanto ciudadanos como autoridades en materia de tránsito en la capital. Consultarlos garantiza el conocimiento de tus derechos y obligaciones viales.
            </p>
            <ul className="list-group list-group-flush text-center">
                <li className="list-group-item">
                <a href="https://data.consejeria.cdmx.gob.mx/images/leyes/reglamentos/REGLAMENTO_DE_TRANSITO_DE_LA_CIUDAD_DE_MEXICO_6.1.pdf" target="_blank" rel="noopener noreferrer">
                    Reglamento de Tránsito de la CDMX
                </a>
                </li>
                <li className="list-group-item">
                <a href="https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_MOVILIDAD_DE_LA_CDMX_3.2.pdf" target="_blank" rel="noopener noreferrer">
                    Ley de Movilidad de la CDMX
                </a>
                </li>
                <li className="list-group-item">
                <a href="https://www.congresocdmx.gob.mx/media/documentos/49a0a80ee030f12d0f797c671da2918e508f30cb.pdf" target="_blank" rel="noopener noreferrer">
                    Ley de Cultura Cívica en la CDMX
                </a>
                </li>
                <li className="list-group-item">
                <a href="https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_PROCEDIMIENTO_ADMINISTRATIVO_DE_LA_CDMX_1.1.pdf" target="_blank" rel="noopener noreferrer">
                    Ley de Procedimiento Administrativo en la CDMX
                </a>
                </li>
                <li className="list-group-item">
                <a href="https://www.ssc.cdmx.gob.mx/storage/app/media/Transito/Actualizaciones/Acuedo-40-2024.pdf" target="_blank" rel="noopener noreferrer">
                    Lista de agentes facultados para infraccionar sobre vía pública en la CDMX
                </a>
                </li>
            </ul>
            </div>
        </div>
        <Footer />
        </>
    );
};

export default Bienvenida;
