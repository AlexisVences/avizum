import { API_URL, authHeaders, extractErrorMessage } from './api';

export async function buscarAgentes(consulta) {
    const response = await fetch(`${API_URL}/agents/search?q=${encodeURIComponent(consulta.trim())}`, {
        headers: { ...authHeaders() },
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(extractErrorMessage(data, 'No pudimos consultar el registro de agentes. Intenta de nuevo.'));
    }
    return data;
}
