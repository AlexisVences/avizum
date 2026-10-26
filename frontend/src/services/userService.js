import { API_URL, apiFetch, authHeaders, extractErrorMessage } from './api';

export const createUser = async (userData) => {
  const response = await apiFetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password }),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(extractErrorMessage(data, 'Error al crear el usuario'));
  }

  return data;
};

export const getUser = async (userId) => {
  const response = await apiFetch(`${API_URL}/users/me`, { headers: authHeaders() });
  return await response.json();
};

export const updateUser = async (viejoUsuario,userData) => {
  const response = await apiFetch(`${API_URL}/users/me`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password || undefined }),
  });
  return await response.json();
};
