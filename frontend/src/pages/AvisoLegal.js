import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const AvisoLegal = () => {
    return (
        <>
        <Navbar />
        <main style={{ marginTop: "120px" }} className="container">
                <div style = {{backgroundColor : '#DFE9F5'}} className="p-4 rounded shadow-sm">
                <h1 className="mb-4 text-center">Aviso Legal</h1>
                
                <section className="mb-4">
                    <h4 className="fw-semibold">Identificación del sitio web</h4>
                    <p>
                    El presente sitio web, <strong>Avizum</strong>, es una plataforma desarrollada con fines informativos
                    y de orientación legal en materia de tránsito vehicular dentro de la Ciudad de México.
                    Avizum no representa a ninguna entidad pública ni sustituye la asesoría legal profesional directa.
                    </p>
                </section>

                <section className="mb-4">
                    <h4 className="fw-semibold">Objeto del servicio</h4>
                    <p>
                    Avizum proporciona a los usuarios información procesada mediante inteligencia artificial basada en documentos
                    oficiales emitidos por las autoridades del Gobierno de la Ciudad de México. Su propósito es facilitar el
                    acceso a normas, procedimientos y derechos relacionados con la movilidad y el tránsito.
                    </p>
                </section>

                <section className="mb-4">
                    <h4 className="fw-semibold">Limitación de responsabilidad</h4>
                    <p>
                    La información ofrecida por Avizum es de carácter orientativo y no tiene valor vinculante ante autoridades o procedimientos judiciales.
                    El uso de la información proporcionada por esta plataforma es responsabilidad exclusiva del usuario.
                    No nos hacemos responsables por el uso indebido, interpretación errónea o consecuencias legales derivadas del uso de la plataforma.
                    </p>
                </section>

                <section className="mb-4">
                    <h4 className="fw-semibold">Propiedad intelectual</h4>
                    <p>
                    Los contenidos, logotipos, textos, imágenes y código fuente de este sitio son propiedad de los desarrolladores de Avizum
                    y se encuentran protegidos por la normativa nacional e internacional de propiedad intelectual e industrial.
                    </p>
                </section>

                <section className="mb-4">
                    <h4 className="fw-semibold">Protección de datos personales</h4>
                    <p>
                    Avizum no almacena ni utiliza datos personales sin consentimiento explícito del usuario. Toda información proporcionada
                    será utilizada exclusivamente con fines de funcionamiento interno del sistema. Nos comprometemos a respetar
                    y proteger los datos conforme a la Ley de Protección de Datos Personales vigente en México.
                    </p>
                </section>


                </div>
        </main>
        <Footer />
        </>
    );
};

export default AvisoLegal;
