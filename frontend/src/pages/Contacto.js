import React from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const Contacto = () => {
    return (
        <>
        <Navbar />
        <main style = {{marginTop: "120px"}}  className="container">
            <div className="bg-light p-4 rounded shadow-sm">
            <h1 className="mb-4 text-center">Contáctanos</h1>
            <p className="text-center">
                Si tienes dudas, sugerencias o necesitas apoyo relacionado con el funcionamiento de la plataforma,
                no dudes en contactarnos. Estamos para ayudarte.
            </p>

            <div className="row mt-4">
                {/* <div className="col-md-6">
                <form>
                    <div className="mb-3">
                    <label htmlFor="name" className="form-label">Nombre completo</label>
                    <input type="text" className="form-control" id="name" required />
                    </div>
                    <div className="mb-3">
                    <label htmlFor="email" className="form-label">Correo electrónico</label>
                    <input type="email" className="form-control" id="email" required />
                    </div>
                    <div className="mb-3">
                    <label htmlFor="message" className="form-label">Mensaje</label>
                    <textarea className="form-control" id="message" rows="5" required></textarea>
                    </div>
                    <button type="submit" className="btn btn-dark">Enviar mensaje</button>
                </form>
                </div> */}

                <div className="col-md-6">
                <div className="p-3">
                    <h5 className="fw-semibold">Información de contacto</h5>
                    <p><strong>Correo:</strong> contacto@avizum.mx</p>
                    <p><strong>Horario de atención:</strong> Lunes a Viernes, 9:00 AM - 6:00 PM</p>
                    <p><strong>Redes sociales:</strong></p>
                    <ul>
                    <li><a href="#" target="_blank" rel="noreferrer">Facebook</a></li>
                    <li><a href="#" target="_blank" rel="noreferrer">Twitter / X</a></li>
                    <li><a href="#" target="_blank" rel="noreferrer">Instagram</a></li>
                    </ul>
                    <p className="text-muted mt-3" style={{ fontSize: '0.9rem' }}>
                    Los medios de contacto son solo para fines de contacto general. No se ofrece asesoría legal personalizada por dichos medios.
                    </p>
                </div>
                </div>
            </div>
            </div>
        </main>
        <Footer />
        </>
    );
};

export default Contacto;
