import React, { useState } from "react";
import { consultarAgente } from "../services/agentesService";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import "../styles/BienvenidaAdmin.css"

const ConsultarAgenteTransito = () => {
    const [placaBusqueda, setPlacaBusqueda] = useState('');
    const [agenteEncontrado, setAgenteEncontrado] = useState(null);
    const [errorBusqueda, setErrorBusqueda] = useState(null);
    const [cargando, setCargando] = useState(false);

    const handleBuscarAgente = async () => {
        if (!placaBusqueda.trim()) {
            setErrorBusqueda('Por favor ingresa un número de placa');
            return;
        }

        setCargando(true);
        setErrorBusqueda(null);
        setAgenteEncontrado(null);

        try {
            const resultado = await consultarAgente(placaBusqueda);
            setAgenteEncontrado(resultado);
        } catch (error) {
            setErrorBusqueda(error.message || 'Error al buscar el agente');
        } finally {
            setCargando(false);
        }
    };

    return (
        <>
        <NavBar2 /> 
            <div className="page-container">
            <div className="container" style={{ paddingTop: '10rem' }}>
            <div className="background-image"></div>
                <h2 className="text-center fw-bold mb-4">
                    Consulta de Agentes de Tránsito Autorizados
                </h2>
                <p className="text-center text-muted mb-4">
                    Ingresa el número de placa de un agente para verificar si está autorizado para levantar infracciones sobre vía pública en la CDMX.
                </p>

                <div className="text-center mb-4">
                    <input
                        type="text"
                        className="form-control w-50 mx-auto"
                        placeholder="Número de placa"
                        value={placaBusqueda}
                        onChange={(e) => setPlacaBusqueda(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleBuscarAgente()}
                    />
                    <button
                        className="btn btn-primary mt-3"
                        onClick={handleBuscarAgente}
                        disabled={cargando}
                    >
                        {cargando ? 'Buscando...' : 'Buscar'}
                    </button>
                </div>

                <div className="mx-auto" style={{ maxWidth: "600px" }}>
                    {cargando && (
                        <div className="text-center p-4">
                            <div className="spinner-border text-primary" role="status"></div>
                        </div>
                    )}
                    {errorBusqueda && (
                        <div className="alert alert-danger text-center">{errorBusqueda}</div>
                    )}
                    {agenteEncontrado && (
                        <div className="card">
                            <div className="card-body">
                                <h5 className="card-title">Información del Agente</h5>
                                <p className="card-text">
                                    <strong>Placa:</strong> {agenteEncontrado.agente.plate}<br />
                                    <strong>Nombre:</strong> {agenteEncontrado.agente.name}<br/>
                                    El agente consultado <strong>SI</strong> esta facultado para infraccionar en la CDMX.
                                </p>
                            </div>
                        </div>
                    )}
                    {!cargando && !errorBusqueda && !agenteEncontrado && (
                        <div className="alert alert-info text-center">
                            Ingresa una placa para buscar agentes facultados
                        </div>
                    )}
                </div>
            </div>
            </div>
            <Footer />
        </>
    );
};

export default ConsultarAgenteTransito;
