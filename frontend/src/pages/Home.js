import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import Button from '../components/ui/Button';
import infraccionimage from '../assets/infraccion.png';

const OFRECEMOS = [
    {
        folio: '01 · ASESORÍA',
        title: 'Pregúntale a la IA legal',
        description: 'Respuestas basadas solo en el Reglamento de Tránsito y la Ley de Movilidad de la CDMX — nunca inventadas.',
    },
    {
        folio: '02 · MULTAS',
        title: 'Entiende tu infracción',
        description: 'Qué artículo aplica, cuántos puntos suma y cómo impugnarla si corresponde.',
    },
    {
        folio: '03 · AGENTES',
        title: 'Verifica al oficial',
        description: 'Confirma con su número de placa si está autorizado para infraccionar en vía pública.',
    },
    {
        folio: '04 · GUÍAS',
        title: 'Aprende el reglamento',
        description: 'Tipos de infracción, seguros obligatorios y procedimientos explicados sin jerga legal.',
    },
];

const DOCUMENTOS = [
    { label: 'Reglamento de Tránsito de la CDMX', href: 'https://data.consejeria.cdmx.gob.mx/images/leyes/reglamentos/REGLAMENTO_DE_TRANSITO_DE_LA_CIUDAD_DE_MEXICO_6.1.pdf' },
    { label: 'Ley de Movilidad de la CDMX', href: 'https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_MOVILIDAD_DE_LA_CDMX_3.2.pdf' },
    { label: 'Ley de cultura cívica en la CDMX', href: 'https://www.congresocdmx.gob.mx/media/documentos/49a0a80ee030f12d0f797c671da2918e508f30cb.pdf' },
    { label: 'Ley de procedimiento administrativo en la CDMX', href: 'https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_PROCEDIMIENTO_ADMINISTRATIVO_DE_LA_CDMX_1.1.pdf' },
    { label: 'Lista de agentes facultados para infraccionar sobre vía pública en la CDMX', href: 'https://www.ssc.cdmx.gob.mx/storage/app/media/Transito/Actualizaciones/Acuedo-40-2024.pdf' },
];

const Home = () => {
    const [placa, setPlaca] = useState('');
    const navigate = useNavigate();

    const irAVerificar = () => {
        navigate(`/ConsultarAgenteTransito${placa.trim() ? `?placa=${encodeURIComponent(placa.trim())}` : ''}`);
    };

    return (
        <>
            <Navbar />
            <main className="tw-pt-16">
                {/* Hero: la consulta de placa es la acción más urgente, sube al primer scroll */}
                <section className="tw-bg-gris tw-px-6 tw-pt-10 tw-pb-12">
                    <div className="tw-mx-auto tw-max-w-[640px]">
                        <span className="tw-block tw-font-mono tw-text-[11.5px] tw-uppercase tw-tracking-widest tw-text-azul tw-font-bold tw-mb-3.5">
                            Asesoría de tránsito · CDMX
                        </span>
                        <h1 className="tw-font-display tw-font-semibold tw-text-[clamp(1.8rem,4vw,2.5rem)] tw-leading-[1.1] tw-text-ink tw-mb-3.5 [text-wrap:balance]">
                            Antes de firmar nada, <span className="tw-text-magenta">revisa tus derechos.</span>
                        </h1>
                        <p className="tw-text-[1.02rem] tw-text-ink-soft tw-max-w-[46ch] tw-mb-6">
                            Verifica si el agente que te detuvo está facultado para infraccionar, consulta tu multa
                            y entiende el reglamento — en lenguaje llano, con IA basada solo en documentos oficiales.
                        </p>

                        <div className="tw-bg-paper-raised tw-border tw-border-rule tw-rounded-md tw-px-5 tw-py-[18px] tw-max-w-[420px] tw-shadow-[0_4px_14px_rgba(22,24,29,0.06)]">
                            <span className="tw-block tw-text-[0.82rem] tw-font-bold tw-text-ink tw-mb-2.5">
                                Verificar agente por número de placa
                            </span>
                            <div className="tw-flex tw-gap-2.5">
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    placeholder="057 196"
                                    aria-label="Número de placa del agente"
                                    value={placa}
                                    onChange={(e) => setPlaca(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && irAVerificar()}
                                    className="tw-flex-1 tw-min-w-0 tw-font-mono tw-font-semibold tw-tracking-wider tw-text-[1.05rem] tw-border-[1.5px] tw-border-azul tw-rounded tw-bg-[#F4F6FC] tw-text-azul tw-text-center tw-px-3 tw-py-2.5 placeholder:tw-text-azul/50 focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
                                />
                                <Button onClick={irAVerificar} variant="dark" size="md">
                                    Verificar
                                </Button>
                            </div>
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
                        <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 tw-gap-px tw-bg-rule tw-border tw-border-rule tw-rounded tw-overflow-hidden">
                            {OFRECEMOS.map((item) => (
                                <div key={item.folio} className="tw-bg-paper-raised tw-px-[22px] tw-pt-[22px] tw-pb-5">
                                    <div className="tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-2.5">
                                        {item.folio}
                                    </div>
                                    <h4 className="tw-font-sans tw-text-[0.98rem] tw-font-bold tw-text-ink tw-m-0 tw-mb-1.5">
                                        {item.title}
                                    </h4>
                                    <p className="tw-text-[0.87rem] tw-text-ink-soft tw-m-0">
                                        {item.description}
                                    </p>
                                </div>
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
                                Desarrollado por estudiantes de la Escuela Superior de Cómputo del Instituto Politécnico
                                Nacional, Abogadazo es una herramienta creada para brindar asesoría legal en materia de
                                tránsito en la Ciudad de México. Somos un equipo comprometido con facilitar el acceso a
                                la información pública para todos y la justicia por igual; esta página utiliza
                                inteligencia artificial para facilitar la comprensión de los reglamentos, artículos,
                                sanciones, procedimientos y derechos ciudadanos relacionados con el tránsito vehicular.
                            </p>
                            <p className="tw-text-ink-soft tw-leading-relaxed tw-m-0">
                                Nuestra misión es apoyar a los ciudadanos en la defensa de sus derechos viales, poniendo
                                a su alcance una plataforma fácil de usar, confiable y sustentada únicamente en
                                documentos legales oficiales procesados con inteligencia artificial.
                            </p>
                        </div>
                        <div className="tw-text-center">
                            <img
                                src={infraccionimage}
                                alt="Ilustración sobre Abogadazo"
                                className="tw-max-w-[90%] tw-h-auto tw-rounded-lg tw-border tw-border-rule tw-shadow-sm tw-inline-block"
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
                            Documentos legales referentes al tránsito vehicular en la Ciudad de México:
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
