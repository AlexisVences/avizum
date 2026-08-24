import { API_URL, authHeaders, extractErrorMessage } from './api';

export const createUser = async (userData) => {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: userData.usuario, first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password }),
  });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'Error al crear el usuario'));
  }
  
  return data;
};

export const getUser = async (userId) => {
  const response = await fetch(`${API_URL}/users/me`, { headers: authHeaders() });
  return await response.json();
};

export const updateUser = async (viejoUsuario,userData) => {
  const response = await fetch(`${API_URL}/users/me`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password || undefined }),
  });
  return await response.json();
};

export const deleteUser = async (userId) => {
  throw new Error('La eliminación de cuentas aún no está disponible en la nueva API.');
};

export const updateUserRole = async (userId, updates) => {
  const response = await fetch(`${API_URL}/admin/users/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(updates),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'Error al actualizar el usuario'));
  }
  return data;
};

export const getAllUsers = async () => {
  const response = await fetch(`${API_URL}/admin/users`, { headers: authHeaders() });
  const users = await response.json();
  return { clientes: users.map((user) => ({ ...user, usuario: user.username, nombre: user.first_name, apellido: user.last_name, rol: user.role })) };
};
