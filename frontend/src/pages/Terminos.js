import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export const TERMINOS_VERSION = "2026-10-29-borrador";

const secciones = [
    {
        titulo: "Qué es Avizum",
        texto: [
            "Avizum es un asistente informativo sobre el reglamento de tránsito de la Ciudad de México. Ofrece información general, no asesoría legal: su uso no crea una relación abogado-cliente.",
            "Las respuestas pueden contener errores u omisiones. Antes de tomar una decisión, verifica la información con la fuente oficial citada, con la autoridad competente o con un abogado.",
        ],
    },
    {
        titulo: "Uso permitido",
        texto: [
            "Puedes usar Avizum para consultar, de forma personal, información sobre tránsito y movilidad en la Ciudad de México.",
        ],
    },
    {
        titulo: "Uso prohibido",
        lista: [
            "Abusar del servicio, o extraer su contenido de forma automatizada (scraping, bots) sin autorización.",
            "Usarlo con fines ilegales o para perjudicar a terceros.",
            "Suplantar la identidad de otra persona o crear cuentas con datos falsos.",
            "Intentar vulnerar la seguridad del sitio o saturar sus servidores.",
        ],
    },
    {
        titulo: "Cuentas y seguridad",
        texto: [
            "Eres responsable de la confidencialidad de tu contraseña y de la actividad realizada con tu cuenta. Avísanos si sospechas un uso no autorizado. Podemos suspender cuentas que incumplan estos términos.",
        ],
    },
    {
        titulo: "Respuestas generadas con inteligencia artificial",
        texto: [
            "Las respuestas del chat son generadas por un modelo de inteligencia artificial a partir de documentos oficiales. Aunque indicamos las fuentes que se consultaron, el modelo puede interpretar mal un texto o no encontrar la norma aplicable. No incluyas datos sensibles en tus mensajes.",
        ],
    },
    {
        titulo: "Fuentes",
        texto: [
            "Las fuentes son documentos públicos oficiales y se muestra la fecha de la reforma vigente con la que fueron cargados. Una reforma posterior puede no estar reflejada todavía.",
        ],
    },
    {
        titulo: "Disponibilidad",
        texto: [
            "El servicio se ofrece tal como está, sin garantía de disponibilidad continua. Puede interrumpirse por mantenimiento, fallas o causas ajenas a nosotros.",
        ],
    },
    {
        titulo: "Limitación de responsabilidad",
        texto: [
            "En la medida en que la ley lo permita, Avizum y sus responsables no responden por daños, multas, sanciones o pérdidas derivados de confiar en la información del servicio.",
        ],
    },
    {
        titulo: "Cambios a estos términos",
        texto: [
            "Podemos modificar estos términos. Cuando el cambio sea relevante lo avisaremos en el sitio o por correo, y se indicará una nueva versión y fecha. Si continúas usando el servicio tras el aviso, entendemos que aceptas los cambios.",
        ],
    },
    {
        titulo: "Contacto",
        contacto: true,
    },
    {
        titulo: "Ley aplicable y jurisdicción",
        texto: [
            "Estos términos se rigen por las leyes de los Estados Unidos Mexicanos. Para cualquier controversia, las partes se someten a los tribunales competentes de la Ciudad de México.",
        ],
    },
];

const Terminos = () => {
    return (
        <>
            <Navbar />
            <main className="tw-pt-16">
                <div className="tw-bg-gris tw-px-4 tw-py-10">
                    <div className="tw-mx-auto tw-max-w-3xl tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-6 sm:tw-p-8">
                        <div role="note" className="tw-bg-danger/5 tw-border tw-border-danger/20 tw-text-danger tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-6">
                            <strong>Borrador pendiente de revisión por un abogado.</strong>{" "}
                            Versión: {TERMINOS_VERSION}
                        </div>
                        <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mt-0 tw-mb-2">
                            Términos de uso
                        </h1>
                        <p className="tw-text-sm tw-text-ink-soft tw-mt-0 tw-mb-6">
                            Responsable: [Nombre del responsable]
                        </p>

                        {secciones.map((s) => (
                            <section key={s.titulo} className="tw-mb-6">
                                <h2 className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink tw-mt-0 tw-mb-2">
                                    {s.titulo}
                                </h2>
                                {s.texto && s.texto.map((t) => (
                                    <p key={t} className="tw-text-ink tw-leading-relaxed tw-mt-0 tw-mb-2">{t}</p>
                                ))}
                                {s.lista && (
                                    <ul className="tw-text-ink tw-leading-relaxed tw-pl-5 tw-m-0">
                                        {s.lista.map((t) => <li key={t}>{t}</li>)}
                                    </ul>
                                )}
                                {s.contacto && (
                                    <p className="tw-text-ink tw-leading-relaxed tw-m-0">
                                        Para dudas sobre estos términos escríbenos desde la{" "}
                                        <a href="/Contacto" className="tw-font-semibold tw-text-azul hover:tw-text-magenta">página de contacto</a>.
                                    </p>
                                )}
                            </section>
                        ))}
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default Terminos;
