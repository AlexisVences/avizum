// Set REACT_APP_API_URL in deployment; localhost keeps development explicit.
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const authHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};
