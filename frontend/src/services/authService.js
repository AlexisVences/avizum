// src/services/authService.js
import axios from 'axios';
import { API_URL, extractErrorMessage } from './api';

const storeSession = (data) => {
  const userData = {
    id: data.user.id,
    nombre: data.user.first_name,
    apellido: data.user.last_name,
    correo: data.user.email,
    rol: data.user.role,
  };
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(userData));
};

const login = async (credentials) => {
  try {
    const response = await axios.post(`${API_URL}/auth/login`, { email: credentials.email, password: credentials.password });
    storeSession(response.data);
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error.response?.data, 'Credenciales incorrectas'));
  }
};

const loginWithGoogle = async (credential) => {
  try {
    const response = await axios.post(`${API_URL}/auth/google`, { credential });
    storeSession(response.data);
    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error.response?.data, 'No pudimos iniciar sesión con Google. Intenta de nuevo.'));
  }
};

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

const getCurrentUser = () => {
  return JSON.parse(localStorage.getItem('user'));
};

export default {
  login,
  loginWithGoogle,
  logout,
  getCurrentUser
};
