import { API_URL, apiFetch, authHeaders, extractErrorMessage } from './api';

export const createUser = async (userData) => {
  const response = await apiFetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ first_name: userData.nombre, last_name: userData.apellido, email: userData.email, password: userData.password, accepted_terms: userData.acceptedTerms === true }),
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

export const updateUser = async (viejoUsuario, userData) => {
  // Only send what changed: email and current_password are optional on the API.
  const body = { first_name: userData.nombre, last_name: userData.apellido };
  if (userData.email) body.email = userData.email;
  if (userData.password) body.password = userData.password;
  if (userData.currentPassword) body.current_password = userData.currentPassword;

  const response = await apiFetch(`${API_URL}/users/me`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(extractErrorMessage(data, 'Error al guardar los cambios'));
    error.status = response.status;
    throw error;
  }
  return data;
};
