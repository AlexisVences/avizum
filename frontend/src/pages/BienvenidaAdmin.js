import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FaChartBar, FaUsersCog } from "react-icons/fa";
import Footer from "../components/Footer";
import NavBarAdmin from "../components/NavBarAdmin";
import "../styles/BienvenidaAdmin.css"

const BienvenidaAdmin = () => {
        return (
        <>
        <NavBarAdmin />
        <div className="page-container">
        <div className="position-relative">
        {/* Fondo de imagen */}
        <div className="background-image"></div>

        {/* Contenido */}
        <div className="container" style={{ paddingTop: '10rem' }}>
            <motion.h1
            className="text-center mb-5 fw-light"
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            >
            P a n e lㅤa d m i n i s t r a d o r
            </motion.h1>
            <hr></hr>
            <br></br>
            <div className="row justify-content-center gap-4">
            <motion.div
                className="col-md-5 card text-center shadow p-4"
                whileHover={{ scale: 1.03 }}
                initial={{ opacity: 0, x: -100 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.7 }}
            >
                <FaChartBar size={50} className="mb-3 text-primary" />
                <h4 className="mb-3">Ver estadísticas</h4>
                <p>Consulta datos e indicadores del funcionamiento del sistema.</p>
                <Link to="/Estadisticas" className="btn btn-primary mt-3">
                Ir a estadísticas
                </Link>
            </motion.div>

            <motion.div
                className="col-md-5 card text-center shadow p-4"
                whileHover={{ scale: 1.03 }}
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.7 }}
            >
                <FaUsersCog size={50} className="mb-3 text-success" />
                <h4 className="mb-3">Administrar usuarios</h4>
                <p>Agrega, edita o elimina usuarios del sistema.</p>
                <Link to="/AdministrarUsuario" className="btn btn-success mt-3">
                Ir a usuarios
                </Link>
            </motion.div>
            </div>
        </div>
        </div>
        </div>
        <Footer />
        </>
    );
};

export default BienvenidaAdmin;
