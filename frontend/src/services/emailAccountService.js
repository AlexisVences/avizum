import { API_URL, apiFetch, authHeaders, extractErrorMessage } from './api';

const post = async (path, body, fallback, { auth = false } = {}) => {
  const response = await apiFetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(auth ? authHeaders() : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(
      response.status === 429
        ? 'Demasiados intentos. Espera unos minutos e inténtalo de nuevo.'
        : extractErrorMessage(data, fallback)
    );
    error.status = response.status;
    throw error;
  }
  return data;
};

export const verifyEmail = (token) =>
  post('/auth/verify-email', { token }, 'El enlace no es válido o ya expiró.');

export const resendVerification = () =>
  post('/auth/resend-verification', undefined, 'No pudimos reenviar el correo. Intenta de nuevo.', { auth: true });

export const forgotPassword = (email) =>
  post('/auth/forgot-password', { email }, 'No pudimos procesar tu solicitud. Intenta de nuevo.');

export const resetPassword = (token, password) =>
  post('/auth/reset-password', { token, password }, 'El enlace no es válido o ya expiró.');
