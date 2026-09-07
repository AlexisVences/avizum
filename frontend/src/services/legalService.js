import { API_URL, authHeaders } from './api';

export const consultarChatLegal = async (pregunta) => {
  try {
    const response = await fetch(`${API_URL}/legal-consultations`, {
      method: 'POST',
      headers: {
        "Content-Type": "application/json", ...authHeaders()
      },
      body: JSON.stringify({ question: pregunta })
    });
    
    if (!response.ok) {
      throw new Error('Error en la respuesta del servidor');
    }
    
    const data = await response.json();
    
    return { success: true, respuesta: data.answer, fuentes: data.citations, categoria: data.category, id_respuesta: data.response_id };
  } catch (error) {
    console.error('Error al consultar el chat legal:', error);
    throw error;
  }
};

export const enviarFeedbackLegal = async ({ respuesta, rating }) => {
  try {
    const response = await fetch(`${API_URL}/legal-responses/${respuesta}/feedback`, {
      method: 'PUT',
      headers: {
        "Content-Type": "application/json", ...authHeaders()
      },
      body: JSON.stringify({ response_id: respuesta, rating })
    });

    if (!response.ok) {
      throw new Error('Error al enviar feedback');
    }

    return { success: true };
  } catch (error) {
    console.error('Error al enviar calificación:', error);
    throw error;
  }
};
