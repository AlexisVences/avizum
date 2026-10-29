import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const P = ({ children }) => <p className="tw-text-ink tw-leading-relaxed tw-mt-0 tw-mb-2">{children}</p>;
const H = ({ children }) => (
    <h2 className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink tw-mt-0 tw-mb-2">{children}</h2>
);
const Section = ({ children }) => <section className="tw-mb-6">{children}</section>;
const List = ({ items }) => (
    <ul className="tw-text-ink tw-leading-relaxed tw-pl-5 tw-m-0">
        {items.map((t) => <li key={t}>{t}</li>)}
    </ul>
);

const AvisoLegal = () => {
    return (
        <>
            <Navbar />
            <main className="tw-pt-16">
                <div className="tw-bg-gris tw-px-4 tw-py-10">
                    <div className="tw-mx-auto tw-max-w-3xl tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-6 sm:tw-p-8">
                        <div role="note" className="tw-bg-danger/5 tw-border tw-border-danger/20 tw-text-danger tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-6">
                            <strong>Borrador pendiente de revisión por un abogado.</strong>
                        </div>
                        <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mt-0 tw-mb-2">
                            Aviso de privacidad
                        </h1>
                        <p className="tw-text-sm tw-text-ink-soft tw-mt-0 tw-mb-6">
                            Última actualización: 29 de octubre de 2026
                        </p>

                        <Section>
                            <H>Responsable del tratamiento</H>
                            <P>
                                [Nombre del responsable], con domicilio en [Domicilio del responsable], es responsable del tratamiento de
                                tus datos personales a través de <strong>Avizum</strong>, un asistente informativo sobre el reglamento de
                                tránsito de la Ciudad de México que no sustituye la asesoría de un abogado.
                            </P>
                        </Section>

                        <Section>
                            <H>Datos personales que recabamos</H>
                            <List items={[
                                "Nombre y apellido.",
                                "Correo electrónico.",
                                "Contraseña: se guarda únicamente como hash, nunca en texto legible.",
                                "Los mensajes que escribes en el chat y la calificación (pulgar arriba o abajo) que das a las respuestas.",
                                "Registros técnicos y dirección IP, para seguridad y para limitar el número de solicitudes.",
                            ]} />
                        </Section>

                        <Section>
                            <H>Finalidades</H>
                            <List items={[
                                "Prestarte el servicio: crear tu cuenta y responder tus consultas.",
                                "Seguridad del servicio y prevención de abusos.",
                                "Mejorar la calidad de las respuestas mediante su revisión por administradores.",
                                "Enviarte correos del servicio, como la verificación de tu cuenta y el restablecimiento de contraseña.",
                            ]} />
                        </Section>

                        <Section>
                            <H>Terceros, transferencias y remisiones</H>
                            <P>Para prestar el servicio, algunos datos son tratados por proveedores que actúan por nuestra cuenta:</P>
                            <List items={[
                                "OpenAI procesa el texto de tus mensajes del chat para generar las respuestas.",
                                "Google, si decides iniciar sesión con Google (Google Sign-In).",
                                "Proveedor de correo electrónico: [Proveedor de correo].",
                                "Proveedor de hospedaje: [Proveedor de hospedaje].",
                            ]} />
                            <P>
                                No vendemos tus datos personales. Por esto mismo, no incluyas datos sensibles (salud, origen étnico,
                                creencias, vida sexual, datos financieros, entre otros) ni información de terceros en el texto del chat.
                            </P>
                        </Section>

                        <Section>
                            <H>Revisión de respuestas</H>
                            <P>
                                Las respuestas que reciban una calificación negativa, terminen en error o no citen ninguna fuente pueden ser revisadas por el equipo
                                de Avizum, sin nombre ni correo, para mejorar el servicio.
                            </P>
                        </Section>

                        <Section>
                            <H>Conservación</H>
                            <P>
                                Conservamos los datos de tu cuenta mientras esté activa y, tras su eliminación, [plazo de conservación de la cuenta].
                                Las conversaciones se conservan por [plazo de conservación de conversaciones] y los registros técnicos por
                                [plazo de conservación de registros técnicos].
                            </P>
                        </Section>

                        <Section>
                            <H>Derechos ARCO y revocación del consentimiento</H>
                            <P>
                                Tienes derecho a Acceder, Rectificar, Cancelar u Oponerte al tratamiento de tus datos (derechos ARCO), así como a
                                revocar tu consentimiento. Para ejercerlos escríbenos desde la{" "}
                                <a href="/Contacto" className="tw-font-semibold tw-text-azul hover:tw-text-magenta">página de contacto</a>
                                {" "}o a [correo para derechos ARCO], indicando tu nombre, el correo de tu cuenta y el derecho que deseas ejercer.
                                Responderemos en los plazos que marca la ley.
                            </P>
                            <P>
                                Si consideras que tu derecho fue vulnerado, puedes acudir a la Secretaría Anticorrupción y Buen Gobierno,
                                autoridad en materia de protección de datos personales conforme a la Ley Federal de Protección de Datos
                                Personales en Posesión de los Particulares (publicada en el DOF el 20 de marzo de 2025).
                            </P>
                        </Section>

                        <Section>
                            <H>Cookies y almacenamiento local</H>
                            <P>
                                Guardamos tu token de sesión en el almacenamiento local (localStorage) de tu navegador para mantenerte
                                autenticado. Se elimina al cerrar sesión.
                            </P>
                        </Section>

                        <Section>
                            <H>Cambios a este aviso</H>
                            <P>
                                Cualquier cambio se publicará en esta página con una nueva fecha de actualización y, si es relevante,
                                te lo notificaremos por correo.
                            </P>
                        </Section>

                        <Section>
                            <H>Aviso legal</H>
                            <P>
                                La información de Avizum es orientativa, no tiene valor vinculante ante autoridades y no sustituye la
                                asesoría legal profesional. Consulta nuestros{" "}
                                <a href="/terminos" className="tw-font-semibold tw-text-azul hover:tw-text-magenta">Términos de uso</a>.
                            </P>
                        </Section>
                    </div>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default AvisoLegal;
