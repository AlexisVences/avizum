import { API_URL, apiFetch, authHeaders, extractErrorMessage } from './api';

export class AdminApiError extends Error {
  constructor(message, status = 0, code = null) {
    super(message);
    this.name = 'AdminApiError';
    this.status = status;
    this.code = code;
  }
}

const isPlainObject = (value) =>
  value !== null && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype;

const toCamel = (key) => key.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());

// Recursively converts snake_case object keys to camelCase; values are left untouched.
export const camelize = (value) => {
  if (Array.isArray(value)) return value.map(camelize);
  if (isPlainObject(value)) {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [toCamel(k), camelize(v)]));
  }
  return value;
};

const buildQuery = (params) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    search.append(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : '';
};

const request = async (path, { method = 'GET', body, raw = false } = {}) => {
  const headers = { ...authHeaders() };
  const options = { method, headers };
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await apiFetch(`${API_URL}${path}`, options);
  } catch (error) {
    throw new AdminApiError(error.message);
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  if (!response.ok) {
    const detail = data?.detail;
    const code = detail && typeof detail === 'object' && typeof detail.code === 'string' ? detail.code : null;
    throw new AdminApiError(
      extractErrorMessage(data, 'No pudimos completar la operación. Intenta de nuevo.'),
      response.status,
      code
    );
  }
  return raw ? data : camelize(data);
};

export const listUsers = ({ q, role, active, verified, sort, descending, page, pageSize } = {}) =>
  request(
    `/admin/users${buildQuery({
      q,
      role,
      active,
      verified,
      sort,
      descending,
      page,
      page_size: pageSize,
    })}`
  );

export const updateUser = (id, { role, isActive } = {}) => {
  const body = {};
  if (role !== undefined) body.role = role;
  if (isActive !== undefined) body.is_active = isActive;
  return request(`/admin/users/${id}`, { method: 'PATCH', body });
};

export const deleteUser = (id, confirmEmail) =>
  request(`/admin/users/${id}`, { method: 'DELETE', body: { confirm_email: confirmEmail } });

export const listAudit = ({ actorId, action, page, pageSize } = {}) =>
  request(`/admin/audit${buildQuery({ actor_id: actorId, action, page, page_size: pageSize })}`);

export const getOverview = ({ days } = {}) => request(`/admin/overview${buildQuery({ days })}`);

export const listReviewQueue = ({ reason, reviewed, page, pageSize } = {}) =>
  request(`/admin/review-queue${buildQuery({ reason, reviewed, page, page_size: pageSize })}`);

export const markReviewed = (messageId, note) =>
  request(`/admin/review-queue/${messageId}/review`, { method: 'POST', body: { note } });

// The case is a line of the evaluation file: its keys must reach the clipboard exactly as the backend wrote them.
export const getEvalCase = (messageId) =>
  request(`/admin/review-queue/${messageId}/eval-case`, { raw: true });
