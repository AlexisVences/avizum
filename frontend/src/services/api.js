// Set REACT_APP_API_URL in deployment; localhost keeps development explicit.
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// FastAPI errors carry `detail`, either a string (HTTPException) or a list of
// validation errors (422) — never `message`.
export const extractErrorMessage = (data, fallback) => {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((e) => e.msg).filter(Boolean).join(', ') || fallback;
  }
  return fallback;
};
