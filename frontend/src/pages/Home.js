import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import Button from '../components/ui/Button';
import SloganAnimado from '../components/SloganAnimado';
import CdmxMapBackground from '../components/chat/CdmxMapBackground';
import infraccionimage from '../assets/infraccion.png';
import { buscarAgentes } from '../services/agentesService';
import ResultadoBusquedaAgentes from '../components/agentes/ResultadoBusquedaAgentes';
import marcoJuridico from '../content/guia/articulos/marco-juridico.json';


const OFRECEMOS = [
    {
        folio: '01 · ASESORÍA ↗',
        title: 'Asesoría legal con IA',
        description: 'Pregunta con tus palabras y recibe una respuesta con el artículo y la página oficial en que se apoya.',
        to: '/asesoria-ia',
    },
    {
        folio: '02 · RECURSOS ↗',
        title: 'Guía del conductor',
        description: 'Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto en la CDMX.',
        to: '/Bienvenida#guia',
    },
    {
        folio: '03 · AGENTES ↗',
        title: 'Consultar agentes facultados',
        description: 'Verifica por placa o nombre si un agente de tránsito aparece en la lista oficial de personal autorizado para multar.',
        to: '/ConsultarAgenteTransito',
    },
    {
        folio: '04 · CÁLCULO ↗',
        title: 'Calculadoras',
        description: 'Convierte multas de UMA a pesos y consulta cuándo te toca verificar según tu placa.',
        to: '/Bienvenida#calculadoras',
    },
];

// Same list as the Marco jurídico guide page, so the landing page and the assistant's sources never drift apart.
const DOCUMENTOS = marcoJuridico.documentos.map((doc) => ({ label: doc.titulo, href: doc.url }));

const Home = () => {
    const [placa, setPlaca] = useState('');
    const [cargando, setCargando] = useState(false);
    const [resultado, setResultado] = useState(null);
    const [errorBusqueda, setErrorBusqueda] = useState(null);

    const verificarAgente = async () => {
        if (placa.trim().length < 2) {
            setResultado(null);
            setErrorBusqueda('Escribe una placa o al menos dos letras del nombre del agente.');
            return;
        }

        setCargando(true);
        setErrorBusqueda(null);
        setResultado(null);

        try {
            setResultado(await buscarAgentes(placa));
        } catch (error) {
            setErrorBusqueda(error.message || 'Error al buscar el agente');
        } finally {
            setCargando(false);
        }
    };

    return (
        <>
            <Navbar />
            <main className="tw-pt-16">
                <section className="tw-relative tw-isolate tw-overflow-hidden tw-bg-gris tw-px-6 tw-pt-10 tw-pb-12">
                    <CdmxMapBackground labelSize={10} labelOpacity={0.5} />
                    <div className="tw-mx-auto tw-max-w-[640px]">
                        {/* <span className="tw-block tw-font-mono tw-text-[11.5px] tw-uppercase tw-tracking-widest tw-text-azul tw-font-bold tw-mb-3.5">
                            Asesoría de tránsito · CDMX
                        </span> */}
                        <h1 className="tw-font-display tw-font-semibold tw-text-[clamp(1.8rem,4vw,2.5rem)] tw-leading-[1.1] tw-text-ink tw-mb-3.5 [text-wrap:balance]">
                            Conduce seguro, <span className="tw-text-magenta">conoce tus derechos</span>
                        </h1>
                        <SloganAnimado />
                        <p className="tw-text-[1.02rem] tw-text-ink-soft tw-max-w-[46ch] tw-mb-6">
                            Verifica si el agente que te detuvo está facultado para infraccionar, consulta tu multa,
                            entiende el reglamento, y usa nuestro chat de IA basado en documentos oficiales.
                        </p>

                        <div className="tw-bg-paper-raised tw-border tw-border-rule tw-rounded-md tw-px-5 tw-py-[18px] tw-max-w-[420px] tw-shadow-[0_4px_14px_rgba(22,24,29,0.06)]">
                            <span className="tw-block tw-text-[0.82rem] tw-font-bold tw-text-ink tw-mb-2.5">
                                Verificar agente por placa o nombre
                            </span>
                            <div className="tw-flex tw-gap-2.5">
                                <input
                                    type="text"
                                    placeholder="Placa o nombre"
                                    aria-label="Placa o nombre del agente"
                                    maxLength={100}
                                    value={placa}
                                    onChange={(e) => setPlaca(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && verificarAgente()}
                                    className="tw-flex-1 tw-min-w-0 tw-font-mono tw-font-semibold tw-tracking-wider tw-text-[1.05rem] tw-border-[1.5px] tw-border-azul tw-rounded tw-bg-[#F4F6FC] tw-text-azul tw-text-center tw-px-3 tw-py-2.5 placeholder:tw-text-azul/50 focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
                                />
                                <Button onClick={verificarAgente} disabled={cargando} variant="dark" size="md">
                                    {cargando ? 'Verificando…' : 'Verificar'}
                                </Button>
                            </div>

                            {cargando && (
                                <div key="cargando" className="tw-flex tw-justify-center tw-py-4 tw-animate-fade-in-up">
                                    <div className="tw-w-5 tw-h-5 tw-border-2 tw-border-azul tw-border-t-transparent tw-rounded-full tw-animate-spin"></div>
                                </div>
                            )}

                            {!cargando && errorBusqueda && (
                                <div key="error" className="tw-mt-3 tw-bg-azul/5 tw-border tw-border-azul/20 tw-rounded tw-px-4 tw-py-3.5 tw-animate-fade-in-up">
                                    <p className="tw-text-ink-soft tw-text-sm tw-leading-relaxed tw-m-0">
                                        {errorBusqueda}
                                    </p>
                                </div>
                            )}

                            {!cargando && resultado && (
                                <div key="ok" className="tw-mt-3 tw-animate-fade-in-up">
                                    <ResultadoBusquedaAgentes resultado={resultado} />
                                </div>
                            )}

                            <p className="tw-text-[0.78rem] tw-text-ink-soft tw-mt-2 tw-mb-0">
                                Cruzamos el número contra el registro oficial de agentes facultados de la CDMX.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Qué puedes hacer aquí — cada bloque lleva su folio, el elemento de firma del sistema */}
                <section className="tw-px-6 tw-py-11">
                    <div className="tw-mx-auto tw-max-w-5xl">
                        <div className="tw-font-mono tw-text-[11px] tw-tracking-widest tw-uppercase tw-text-ink-soft tw-mb-[18px]">
                            Servicios a tu disposición
                        </div>
                        <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 lg:tw-grid-cols-4 tw-gap-px tw-bg-rule tw-border tw-border-rule tw-rounded tw-overflow-hidden">
                            {OFRECEMOS.map((item) => (
                                <Link
                                    key={item.folio}
                                    to={item.to}
                                    className="tw-block tw-bg-paper-raised tw-px-[22px] tw-pt-[22px] tw-pb-5 tw-no-underline tw-text-inherit hover:tw-bg-gris/40 tw-transition-colors"
                                >
                                    <div className="tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-2.5">
                                        {item.folio}
                                    </div>
                                    <h4 className="tw-font-sans tw-text-[0.98rem] tw-font-bold tw-text-ink tw-m-0 tw-mb-1.5">
                                        {item.title}
                                    </h4>
                                    <p className="tw-text-[0.87rem] tw-text-ink-soft tw-m-0">
                                        {item.description}
                                    </p>
                                </Link>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ¿Quiénes somos? — misma información, reordenada con el nuevo sistema visual */}
                <section className="tw-px-6 tw-py-11 tw-bg-paper">
                    <div className="tw-mx-auto tw-max-w-5xl tw-grid tw-grid-cols-1 md:tw-grid-cols-2 tw-gap-10 tw-items-center">
                        <div>
                            <h2 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-4">
                                ¿Quiénes somos?
                            </h2>
                            <p className="tw-text-ink-soft tw-leading-relaxed tw-mb-4">
                                Avizum es un proyecto independiente, diseñado y desarrollado por Alexis Vences, para
                                brindar asesoría legal en materia de tránsito en la Ciudad de México. Está pensado para
                                facilitar el acceso a la información pública para todos y la justicia por igual; esta página utiliza
                                inteligencia artificial para facilitar la comprensión de los reglamentos, artículos,
                                sanciones, procedimientos y derechos ciudadanos relacionados con el tránsito vehicular.
                            </p>
                            <p className="tw-text-ink-soft tw-leading-relaxed tw-m-0">
                                La misión del proyecto es apoyar a los ciudadanos en la defensa de sus derechos viales, poniendo
                                a su alcance una plataforma fácil de usar, confiable y sustentada únicamente en
                                documentos legales oficiales procesados con inteligencia artificial.
                            </p>
                        </div>
                        <div className="tw-text-center">
                            <img
                                src={infraccionimage}
                                alt="Ilustración sobre Avizum"
                                className="tw-max-w-[90%] tw-h-auto tw-inline-block"
                            />
                        </div>
                    </div>
                </section>

                {/* Descargo de responsabilidad y documentos legales de referencia */}
                <section className="tw-px-6 tw-py-11">
                    <div className="tw-mx-auto tw-max-w-5xl tw-bg-gris tw-border tw-border-rule tw-rounded tw-p-6">
                        <p className="tw-text-ink-soft tw-text-sm tw-leading-relaxed tw-mb-4">
                            <strong className="tw-text-ink">Descargo de responsabilidad:</strong> la información
                            proporcionada por esta plataforma tiene como objetivo brindar orientación basada
                            exclusivamente en los documentos legales emitidos por el Gobierno de la Ciudad de México en
                            materia de tránsito vehicular. Esta herramienta está diseñada como un apoyo informativo y
                            de consulta, y en ningún caso sustituye el asesoramiento legal profesional o la
                            intervención de autoridades competentes.
                        </p>
                        <hr className="tw-border-rule tw-my-4" />
                        <p className="tw-font-semibold tw-text-ink tw-text-sm tw-mb-3">
                            Documentos legales asociados al tránsito vehicular en la Ciudad de México:
                        </p>
                        <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-2">
                            {DOCUMENTOS.map((doc) => (
                                <li key={doc.href}>
                                    <a
                                        href={doc.href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="tw-text-azul hover:tw-text-magenta tw-text-sm tw-font-medium"
                                    >
                                        {doc.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                </section>
            </main>
            <Footer />
        </>
    );
};

export default Home;
