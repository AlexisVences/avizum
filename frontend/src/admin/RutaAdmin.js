import React from 'react';
import { Navigate } from 'react-router-dom';
import authService from '../services/authService';

// Guarda de rutas del panel: solo el rol 'admin' ve el contenido.
const RutaAdmin = ({ children }) => {
    const usuario = authService.getCurrentUser();
    if (!usuario) return <Navigate to="/Login" replace />;
    if (usuario.rol !== 'admin') return <Navigate to="/Bienvenida" replace />;
    return children;
};

export default RutaAdmin;
