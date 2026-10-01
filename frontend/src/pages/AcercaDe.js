import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const AcercaDe = () => {
    return (
        <>
        <Navbar />
        <main style = {{marginTop : "120px"}}  className="container">
            <div className="bg-light p-4 rounded shadow-sm">
            <h1 className="mb-4 text-center">Acerca de Amicuz</h1>

            <section className="mb-4">
                <p>
                <strong>Amicuz</strong> es una plataforma digital diseñada para ofrecer orientación legal en materia de tránsito vehicular
                en la Ciudad de México. Nació como una iniciativa para acercar el conocimiento legal a la ciudadanía mediante el uso de inteligencia artificial
                y tecnologías accesibles, al alcance de todos.
                </p>
            </section>

            <section className="mb-4">
                <h4 className="fw-semibold">Nuestra misión</h4>
                <p>
                Democratizar el acceso a la información legal en temas de movilidad urbana y tránsito, ayudando a los ciudadanos a conocer sus derechos y obligaciones
                mediante herramientas tecnológicas de fácil uso basadas en documentos oficiales.
                </p>
            </section>

            <section className="mb-4">
                <h4 className="fw-semibold">Nuestra visión</h4>
                <p>
                Ser una referencia en México como asistente legal digital en temas de tránsito, fomentando una ciudadanía informada y empoderada,
                y colaborando activamente en la transformación digital de los servicios legales en beneficio social.
                </p>
            </section>

            <section className="mb-4">
                <h4 className="fw-semibold">Nuestros valores</h4>
                <ul>
                <li><strong>Transparencia:</strong> Basamos toda la información en documentos legales públicos.</li>
                <li><strong>Accesibilidad:</strong> Creamos una interfaz simple para cualquier ciudadano.</li>
                <li><strong>Compromiso social:</strong> Nuestra meta es brindar ayuda real a quien lo necesite.</li>
                <li><strong>Innovación:</strong> Utilizamos inteligencia artificial de forma ética y responsable.</li>
                </ul>
            </section>

            <section className="mb-4">
                <h4 className="fw-semibold">Compromiso ciudadano y tecnológico</h4>
                <p>
                En Amicuz creemos que la tecnología puede ser una aliada para la justicia. Por eso trabajamos con responsabilidad en la integración
                de inteligencia artificial que respeta los principios legales, éticos y sociales.
                Aspiramos a que cada usuario tenga en sus manos una herramienta que le permita actuar con conocimiento, seguridad y confianza.
                </p>
            </section>
            </div>
        </main>
        <Footer />
        </>
    );
};

export default AcercaDe;
