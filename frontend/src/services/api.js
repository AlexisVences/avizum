// Set REACT_APP_API_URL in deployment; localhost keeps development explicit.
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// FastAPI errors carry `detail`: a string (HTTPException), a list of validation errors (422) or, on the chat
// routes, an object `{ code, message }`.
export const extractErrorMessage = (data, fallback) => {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && !Array.isArray(detail) && typeof detail.message === 'string') {
    return detail.message;
  }
  if (Array.isArray(detail) && detail.length) {
    return detail.map((e) => e.msg).filter(Boolean).join(', ') || fallback;
  }
  return fallback;
};
