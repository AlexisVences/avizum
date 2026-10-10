import { API_URL, authHeaders } from './api';
const requestStats = async () => {
  const response = await fetch(`${API_URL}/admin/statistics`, { headers: authHeaders() });
  if (!response.ok) throw new Error('Error al obtener estadísticas');
  return response.json();
};
export const getDailyStats = async () => {
  
  const data = await requestStats(); return { success: true, consultas_hoy: data.messages_today };
};

export const getMonthlyStats = async () => {
  const data = await requestStats(); return { success: true, consultas_mes: data.messages_month };
};

export const getMonthlyStatsAgents = async () => {
  const data = await requestStats(); return { success: true, consultas_mes: data.agent_lookups_month };
};

export const getConsultationTypes = async () => {
  // Messages are no longer classified by category, so the pie chart has nothing to show until Phase 3 redesigns this page.
  await requestStats();
  return { success: true, tipos_consulta: [] };
};

export const getFeedbackStats = async () => {
  const data = await requestStats();
  // feedback_positive_rate is the share of 👍 (0..1), or null when nobody has rated an answer yet.
  const promedio = data.feedback_positive_rate === null ? 0 : Number(data.feedback_positive_rate);
  return { success: true, promedio };
};
