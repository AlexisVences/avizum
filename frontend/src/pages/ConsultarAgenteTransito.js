import React, { useState } from "react";
import { consultarAgente } from "../services/agentesService";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";

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
            <main className="tw-pt-16">
                <div className="tw-min-h-[calc(100vh-4rem)] tw-bg-gris tw-px-4 tw-py-12">
                    <div className="tw-mx-auto tw-max-w-lg">
                        <span className="tw-block tw-text-center tw-font-mono tw-text-[11.5px] tw-uppercase tw-tracking-widest tw-text-azul tw-font-bold tw-mb-3.5">
                            03 · Agentes
                        </span>
                        <h1 className="tw-font-display tw-text-center tw-text-3xl tw-font-semibold tw-text-ink tw-mb-3">
                            Verifica al oficial
                        </h1>
                        <p className="tw-text-center tw-text-ink-soft tw-mb-8">
                            Ingresa el número de placa de un agente para confirmar si está autorizado
                            para levantar infracciones sobre vía pública en la CDMX.
                        </p>

                        <div className="tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-6">
                            <div className="tw-flex tw-gap-2.5">
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    placeholder="Número de placa"
                                    aria-label="Número de placa del agente"
                                    value={placaBusqueda}
                                    onChange={(e) => setPlacaBusqueda(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleBuscarAgente()}
                                    className="tw-flex-1 tw-min-w-0 tw-font-mono tw-font-semibold tw-tracking-wider tw-text-[1.05rem] tw-border-[1.5px] tw-border-azul tw-rounded tw-bg-[#F4F6FC] tw-text-azul tw-text-center tw-px-3 tw-py-2.5 placeholder:tw-text-azul/50 focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
                                />
                                <Button onClick={handleBuscarAgente} disabled={cargando} variant="dark" size="md">
                                    {cargando ? 'Buscando…' : 'Buscar'}
                                </Button>
                            </div>

                            <div className="tw-mt-6">
                                {cargando && (
                                    <div className="tw-flex tw-justify-center tw-py-6">
                                        <div className="tw-w-6 tw-h-6 tw-border-2 tw-border-azul tw-border-t-transparent tw-rounded-full tw-animate-spin"></div>
                                    </div>
                                )}

                                {!cargando && errorBusqueda && (
                                    <div className="tw-bg-azul/5 tw-border tw-border-azul/20 tw-text-ink-soft tw-text-sm tw-rounded tw-px-4 tw-py-3.5 tw-leading-relaxed">
                                        {errorBusqueda}
                                    </div>
                                )}

                                {!cargando && agenteEncontrado && (
                                    <div className="tw-border tw-border-rule tw-rounded tw-p-4">
                                        <div className="tw-flex tw-items-center tw-justify-between tw-mb-3">
                                            <span className="tw-font-mono tw-text-lg tw-font-bold tw-text-ink tw-tracking-wider">
                                                {agenteEncontrado.agente.plate}
                                            </span>
                                            <Badge variant="verified">Verificado</Badge>
                                        </div>
                                        <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                                            <strong className="tw-text-ink">{agenteEncontrado.agente.name}</strong> está
                                            facultado para infraccionar en la vía pública de la CDMX.
                                        </p>
                                    </div>
                                )}

                                {!cargando && !errorBusqueda && !agenteEncontrado && (
                                    <p className="tw-text-center tw-text-sm tw-text-ink-soft tw-m-0">
                                        Ingresa una placa para verificar si el agente está autorizado.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default ConsultarAgenteTransito;
