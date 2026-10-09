import React, { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { buscarAgentes } from "../services/agentesService";
import ResultadoBusquedaAgentes from "../components/agentes/ResultadoBusquedaAgentes";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import Button from "../components/ui/Button";

const ConsultarAgenteTransito = () => {
    const [searchParams] = useSearchParams();
    const [consulta, setConsulta] = useState(searchParams.get('placa') || searchParams.get('q') || '');
    const [resultado, setResultado] = useState(null);
    const [errorBusqueda, setErrorBusqueda] = useState(null);
    const [cargando, setCargando] = useState(false);

    const handleBuscarAgente = async () => {
        if (consulta.trim().length < 2) {
            setResultado(null);
            setErrorBusqueda('Escribe una placa o al menos dos letras del nombre del agente.');
            return;
        }
        setCargando(true);
        setErrorBusqueda(null);
        setResultado(null);
        try {
            setResultado(await buscarAgentes(consulta));
        } catch (error) {
            setErrorBusqueda(error.message);
        } finally {
            setCargando(false);
        }
    };

    return (
        <>
            <NavBar2 />
            <main className="tw-flex-1 tw-pt-16 tw-bg-gris">
                <div className="tw-px-4 tw-py-12">
                    <div className="tw-mx-auto tw-max-w-lg">
                        <span className="tw-block tw-text-center tw-font-mono tw-text-[11.5px] tw-uppercase tw-tracking-widest tw-text-azul tw-font-bold tw-mb-3.5">
                            03 · Agentes
                        </span>
                        <h1 className="tw-font-display tw-text-center tw-text-3xl tw-font-semibold tw-text-ink tw-mb-3">
                            Verifica al oficial
                        </h1>
                        <p className="tw-text-center tw-text-ink-soft tw-mb-8">
                            Ingresa el número de placa o el nombre del agente para confirmar si aparece en la lista
                            oficial de personal autorizado para infraccionar en la CDMX.
                        </p>

                        <div className="tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-6">
                            <div className="tw-flex tw-gap-2.5">
                                <input
                                    type="text"
                                    placeholder="Placa o nombre"
                                    aria-label="Placa o nombre del agente"
                                    value={consulta}
                                    onChange={(e) => setConsulta(e.target.value)}
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

                                {!cargando && resultado && <ResultadoBusquedaAgentes resultado={resultado} />}

                                {!cargando && !errorBusqueda && !resultado && (
                                    <p className="tw-text-center tw-text-sm tw-text-ink-soft tw-m-0">
                                        Ingresa una placa o un nombre para verificar al agente.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
            <Footer className="tw-pt-0" />
        </>
    );
};

export default ConsultarAgenteTransito;
