import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FaUserEdit } from "react-icons/fa";
import { FiSave } from "react-icons/fi";
import "../styles/Perfil.css";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import avatar from "../assets/avatar.png";
import { updateUser } from "../services/userService";
import authService from "../services/authService";

const Perfil = () => {
    // Obtener usuario del authService de forma segura
    const storedUser = authService.getCurrentUser();
    const userId = storedUser?.id;

    // Estado inicial con datos del usuario
    const [userData, setUserData] = useState({
        nombre: "",
        apellido: "",
        correo: "",
    });

    const [editando, setEditando] = useState({ nombre: false, apellido: false });
    const [inputs, setInputs] = useState({
        nombre: "",
        apellido: "",
    });
    const [loading, setLoading] = useState(false); // Cambiado a false porque usamos datos locales
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    // Cargar datos del usuario al montar el componente
    useEffect(() => {
    const user = authService.getCurrentUser();
    if (user) {
        setUserData({
            nombre: user.nombre || "",
            apellido: user.apellido || "",
            correo: user.correo || "",
        });
        setInputs({
            nombre: user.nombre || "",
            apellido: user.apellido || "",
        });
    } else {
        setError("No se encontró información del usuario. Por favor, inicie sesión nuevamente.");
    }
}, []);

    const handleChange = (e) => {
        setInputs({ ...inputs, [e.target.name]: e.target.value });
    };

    const guardarCambios = async () => {
        if (!userId) {
            setError("No se puede actualizar el usuario sin ID");
            return;
        }

        try {
            // Preparar datos para actualizar
            const updatedData = {
                nombre: inputs.nombre,
                apellido: inputs.apellido,
                rol: storedUser.rol,
                email: storedUser.correo
            };
            // Llamar al servicio de actualización
            const response = await updateUser(storedUser.correo,updatedData);

            if (!response) {
                throw new Error("No se recibió respuesta del servidor");
            }

            // Actualizar el estado local con los nuevos datos
            setUserData(updatedData);

            // Actualizar el usuario en el localStorage
            const updatedUser = {
                ...storedUser,
                nombre: inputs.nombre,
                apellido: inputs.apellido
            };
            localStorage.setItem('user', JSON.stringify(updatedUser));

            // Desactivar modo edición
            setEditando({ nombre: false, apellido: false });

            // Mostrar mensaje de éxito
            setSuccessMessage("Cambios guardados correctamente");
            setTimeout(() => setSuccessMessage(null), 3000);

        } catch (err) {
            setError(err.message || "Error al guardar los cambios");
            console.error("Update error:", err);
        }
    };

    const cambiosPendientes =
        inputs.nombre !== userData.nombre || inputs.apellido !== userData.apellido;

    if (!storedUser) {
        return (
            <div className="alert alert-danger text-center my-5">
                {error || "No hay usuario autenticado"}
            </div>
        );
    }

    return (
        <>
            <NavBar2 />
            <div className="container perfil-container my-5 mt-5">
                <motion.div
                    className="text-center mb-5"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                >
                    <h2 className="display-4 fw-bold">Gestión de Perfil</h2>
                    <p className="fw-light text-muted">
                        Aquí puedes revisar y actualizar tu información personal
                    </p>
                </motion.div>

                {successMessage && (
                    <div className="alert alert-success text-center">
                        {successMessage}
                    </div>
                )}

                {error && (
                    <div className="alert alert-danger text-center">
                        {error}
                    </div>
                )}

                <motion.div
                    className="perfil-card shadow-lg p-4 rounded-4 mx-auto"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.8 }}
                    style={{ maxWidth: "600px", backgroundColor: "#f8f9fa" }}
                >
                    <div className="text-center mb-4">
                        <img
                            src={avatar}
                            alt="Avatar"
                            className="rounded-circle mb-2"
                            width="100"
                            height="100"
                        />
                        <h5 className="fw-bold mb-0">{userData.nombre} {userData.apellido}</h5>
                        <p className="fw-light text-muted">Usuario registrado</p>
                    </div>

                    {/* Nombre */}
                    <div className="mb-3">
                        <label className="form-label fw-bold">Nombre</label>
                        <div className="input-group">
                            <input
                                type="text"
                                className="form-control"
                                name="nombre"
                                value={inputs.nombre}
                                onChange={handleChange}
                                disabled={!editando.nombre}
                            />
                            <button
                                className="btn btn-outline-secondary"
                                onClick={() => setEditando({ ...editando, nombre: !editando.nombre })}
                            >
                                <FaUserEdit />
                            </button>
                        </div>
                    </div>

                    {/* Apellido */}
                    <div className="mb-3">
                        <label className="form-label fw-bold">Apellido</label>
                        <div className="input-group">
                            <input
                                type="text"
                                className="form-control"
                                name="apellido"
                                value={inputs.apellido}
                                onChange={handleChange}
                                disabled={!editando.apellido}
                            />
                            <button
                                className="btn btn-outline-secondary"
                                onClick={() => setEditando({ ...editando, apellido: !editando.apellido })}
                            >
                                <FaUserEdit />
                            </button>
                        </div>
                    </div>

                    {/* Correo */}
                    <div className="mb-3">
                        <label className="form-label fw-bold">Correo electrónico</label>
                        <input
                            type="email"
                            className="form-control"
                            value={userData.correo}
                            disabled
                        />
                    </div>

                    {/* Botón guardar */}
                    {cambiosPendientes && (
                        <div className="text-center mt-4">
                            <motion.button
                                className="btn btn-success px-4"
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={guardarCambios}
                            >
                                <FiSave className="me-2" />
                                Guardar Cambios
                            </motion.button>
                        </div>
                    )}
                </motion.div>
            </div>
            <Footer className="tw-pt-4" />
        </>
    );
};

export default Perfil;
