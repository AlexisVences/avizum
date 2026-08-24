// src/services/authService.js
import axios from 'axios';
import { API_URL, extractErrorMessage } from './api';

const login = async (credentials) => {
  try {
    const response = await axios.post(`${API_URL}/auth/login`, { username: credentials.username, password: credentials.password });
    
    const userData = {
      id: response.data.user.id,
      nombre: response.data.user.first_name,
      apellido: response.data.user.last_name,
      correo: response.data.user.email,
      rol: response.data.user.role
      // Agrega otros campos necesarios
    };

    // Si el backend devuelve un token en el objeto usuario, guárdalo
    localStorage.setItem('token', response.data.access_token);

    localStorage.setItem('user', JSON.stringify(userData));

    return response.data;
  } catch (error) {
    throw new Error(extractErrorMessage(error.response?.data, 'Credenciales incorrectas'));
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
  logout,
  getCurrentUser
};
