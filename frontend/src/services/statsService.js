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
  const data = await requestStats(); return { success: true, tipos_consulta: data.consultations_by_category };
};

export const getFeedbackStats = async () => {
  const data = await requestStats(); return { success: true, promedio: data.average_feedback_rating };
};
