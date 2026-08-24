import { API_URL, authHeaders } from './api';
const requestStats = async () => {
  const response = await fetch(`${API_URL}/admin/statistics`, { headers: authHeaders() });
  if (!response.ok) throw new Error('Error al obtener estadísticas');
  return response.json();
};
export const getDailyStats = async () => {
  
  const data = await requestStats(); return { success: true, consultas_hoy: data.consultations_today };
};

export const getMonthlyStats = async () => {
  const data = await requestStats(); return { success: true, consultas_mes: data.consultations_month };
};

export const getMonthlyStatsAgents = async () => {
  const data = await requestStats(); return { success: true, consultas_mes: data.agent_lookups_month };
};

export const getConsultationTypes = async () => {
  const data = await requestStats();
  // Recharts' Pie needs an array of {name, value}, not the {category: count} dict the backend returns.
  const tipos_consulta = Object.entries(data.consultations_by_category || {}).map(([name, value]) => ({ name, value }));
  return { success: true, tipos_consulta };
};

export const getFeedbackStats = async () => {
  const data = await requestStats();
  // average_feedback_rating comes back as a numeric string (Postgres AVG -> Decimal) or null when there's no feedback yet.
  const promedio = data.average_feedback_rating === null ? 0 : Number(data.average_feedback_rating);
  return { success: true, promedio };
};
