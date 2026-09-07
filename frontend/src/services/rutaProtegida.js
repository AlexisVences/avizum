import React from "react";
import { Navigate } from "react-router-dom";
import authService from "../services/authService";

/**
 * Componente que protege rutas privadas.
 * Si el usuario no está logueado, lo redirige a la página de Login.
 */
const RutaProtegida = ({ children }) => {
    const user = authService.getCurrentUser();

    if (!user) {
        return <Navigate to="/Login" replace />;
    }

    return children;
};

export default RutaProtegida;
