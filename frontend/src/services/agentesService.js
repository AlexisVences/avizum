import { API_URL, authHeaders } from './api';

export async function consultarAgente(placa) {
  try {
    const response = await fetch(`${API_URL}/agents/${encodeURIComponent(placa)}`,{
      method: "GET",
      headers: {
        "Content-Type": "application/json", ...authHeaders()
      }
    });
    if (!response.ok) {
      throw new Error('El agente no está registrado en la Gaceta Oficial, puedes impugnar la multa ante el Tribunal de Justicia Administrativa de la CDMX.');
    }
    const agente = await response.json();
    return { success: true, agente };
  } catch (error) {
    console.error("Error al consultar agente:", error);
    throw error;
  }
}
