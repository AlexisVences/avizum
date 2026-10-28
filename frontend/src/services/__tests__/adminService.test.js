import {
  AdminApiError,
  camelize,
  deleteUser,
  getEvalCase,
  getOverview,
  listAudit,
  listReviewQueue,
  listUsers,
  markReviewed,
  updateUser,
} from '../adminService';

const respuesta = (status, body) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => {
    if (body === undefined) throw new Error('sin cuerpo');
    return body;
  },
});

beforeEach(() => {
  global.fetch = jest.fn();
  localStorage.setItem('token', 'tok');
});

afterEach(() => {
  localStorage.clear();
});

test('camelize convierte claves anidadas y deja intactos los valores', () => {
  expect(
    camelize({ first_name: 'Ana', items: [{ is_active: true, detail: null }], note: 'a_b' })
  ).toEqual({ firstName: 'Ana', items: [{ isActive: true, detail: null }], note: 'a_b' });
  expect(camelize(null)).toBeNull();
  expect(camelize('x_y')).toBe('x_y');
});

test('listUsers arma la URL con solo los parámetros presentes', async () => {
  global.fetch.mockResolvedValue(
    respuesta(200, {
      items: [{ id: 1, first_name: 'Ana', is_active: true, questions_count: 2 }],
      total: 1,
      page: 2,
      page_size: 20,
    })
  );
  const result = await listUsers({ q: 'ana', active: false, page: 2, role: undefined, sort: '' });
  const [url, options] = global.fetch.mock.calls[0];
  const search = new URL(url).searchParams;
  expect([...search.keys()].sort()).toEqual(['active', 'page', 'q']);
  expect(search.get('active')).toBe('false');
  expect(search.get('q')).toBe('ana');
  expect(url).toContain('/admin/users?');
  expect(options.headers.Authorization).toBe('Bearer tok');
  expect(result).toEqual({
    items: [{ id: 1, firstName: 'Ana', isActive: true, questionsCount: 2 }],
    total: 1,
    page: 2,
    pageSize: 20,
  });
});

test('un 409 con detail.code lanza AdminApiError con ese code y su mensaje', async () => {
  global.fetch.mockResolvedValue(
    respuesta(409, { detail: { code: 'last_admin', message: 'Debe quedar un administrador.' } })
  );
  const error = await updateUser(3, { role: 'user' }).catch((e) => e);
  expect(error).toBeInstanceOf(AdminApiError);
  expect(error.status).toBe(409);
  expect(error.code).toBe('last_admin');
  expect(error.message).toBe('Debe quedar un administrador.');
});

test('un error con detail de texto deja code en null', async () => {
  global.fetch.mockResolvedValue(respuesta(404, { detail: 'No existe.' }));
  const error = await listAudit({}).catch((e) => e);
  expect(error.code).toBeNull();
  expect(error.message).toBe('No existe.');
});

test('un fallo de red lanza el mensaje de conexión de apiFetch', async () => {
  global.fetch.mockRejectedValue(new TypeError('Failed to fetch'));
  const error = await listUsers({}).catch((e) => e);
  expect(error).toBeInstanceOf(AdminApiError);
  expect(error.message).toMatch(/No pudimos conectar con el servidor/);
  expect(error.status).toBe(0);
  expect(error.code).toBeNull();
});

test('updateUser envía solo los campos presentes en snake_case', async () => {
  global.fetch.mockResolvedValue(respuesta(200, { id: 3, first_name: 'Ana', is_active: false }));
  const user = await updateUser(3, { isActive: false });
  const [url, options] = global.fetch.mock.calls[0];
  expect(url).toMatch(/\/admin\/users\/3$/);
  expect(options.method).toBe('PATCH');
  expect(JSON.parse(options.body)).toEqual({ is_active: false });
  expect(user).toEqual({ id: 3, firstName: 'Ana', isActive: false });
});

test('deleteUser envía confirm_email en el cuerpo y devuelve null en 204', async () => {
  global.fetch.mockResolvedValue(respuesta(204));
  const result = await deleteUser(5, 'ana@example.com');
  const [url, options] = global.fetch.mock.calls[0];
  expect(url).toMatch(/\/admin\/users\/5$/);
  expect(options.method).toBe('DELETE');
  expect(JSON.parse(options.body)).toEqual({ confirm_email: 'ana@example.com' });
  expect(options.headers['Content-Type']).toBe('application/json');
  expect(result).toBeNull();
});

test('listAudit pide solo los filtros presentes y cameliza', async () => {
  global.fetch.mockResolvedValue(
    respuesta(200, {
      items: [{ id: 1, actor_name: 'Root', target_user_id: 4 }],
      total: 1,
      page: 1,
      page_size: 20,
    })
  );
  const result = await listAudit({ actorId: 7, action: 'user.delete' });
  const search = new URL(global.fetch.mock.calls[0][0]).searchParams;
  expect([...search.keys()].sort()).toEqual(['action', 'actor_id']);
  expect(search.get('actor_id')).toBe('7');
  expect(result.items[0]).toEqual({ id: 1, actorName: 'Root', targetUserId: 4 });
  expect(result.pageSize).toBe(20);
});

test('getOverview pide el periodo y devuelve claves en camelCase con el costo como texto', async () => {
  global.fetch.mockResolvedValue(
    respuesta(200, {
      days: 7,
      active_users: 3,
      error_rate: null,
      feedback_rate: 0.5,
      cost_usd: '2.25',
      series: [{ date: '2026-10-20', questions: 4 }],
      attention: [],
    })
  );
  const result = await getOverview({ days: 7 });
  const [url] = global.fetch.mock.calls[0];
  expect(url).toContain('/admin/overview?days=7');
  expect(result).toEqual({
    days: 7,
    activeUsers: 3,
    errorRate: null,
    feedbackRate: 0.5,
    costUsd: '2.25',
    series: [{ date: '2026-10-20', questions: 4 }],
    attention: [],
  });
});

test('listReviewQueue pide motivo, revisión y paginación y cameliza', async () => {
  global.fetch.mockResolvedValue(
    respuesta(200, {
      items: [
        {
          message_id: 9,
          asked_at: '2026-10-20T18:30:00Z',
          reasons: ['negative'],
          citations: [{ source_title: 'Reglamento', page: 3 }],
        },
      ],
      total: 1,
      page: 2,
      page_size: 20,
    })
  );
  const result = await listReviewQueue({ reason: 'negative', reviewed: false, page: 2, pageSize: 20 });
  const search = new URL(global.fetch.mock.calls[0][0]).searchParams;
  expect(search.get('reason')).toBe('negative');
  expect(search.get('reviewed')).toBe('false');
  expect(search.get('page')).toBe('2');
  expect(search.get('page_size')).toBe('20');
  expect(result.items[0].messageId).toBe(9);
  expect(result.items[0].askedAt).toBe('2026-10-20T18:30:00Z');
  expect(result.items[0].citations[0].sourceTitle).toBe('Reglamento');
});

test('listReviewQueue omite el motivo cuando no se filtra', async () => {
  global.fetch.mockResolvedValue(respuesta(200, { items: [], total: 0, page: 1, page_size: 20 }));
  await listReviewQueue({ reviewed: true });
  const search = new URL(global.fetch.mock.calls[0][0]).searchParams;
  expect(search.has('reason')).toBe(false);
  expect(search.get('reviewed')).toBe('true');
});

test('markReviewed envía la nota por POST y devuelve el resultado en camelCase', async () => {
  global.fetch.mockResolvedValue(respuesta(200, { message_id: 9, reviewed: true, note: 'ok' }));
  const result = await markReviewed(9, 'ok');
  const [url, options] = global.fetch.mock.calls[0];
  expect(url).toMatch(/\/admin\/review-queue\/9\/review$/);
  expect(options.method).toBe('POST');
  expect(JSON.parse(options.body)).toEqual({ note: 'ok' });
  expect(result).toEqual({ messageId: 9, reviewed: true, note: 'ok' });
});

test('markReviewed propaga el mensaje del 422', async () => {
  global.fetch.mockResolvedValue(
    respuesta(422, { detail: [{ msg: 'String should have at most 500 characters' }] })
  );
  await expect(markReviewed(9, 'x'.repeat(501))).rejects.toMatchObject({
    status: 422,
    message: expect.stringContaining('500'),
  });
});

test('getEvalCase devuelve el objeto tal cual, sin cambiar sus claves', async () => {
  const caso = { id: 'q-9', question: 'p', coverage: 'covered', expected: [{ source_slug: 'reglamento', article: '44' }], notes: '', verified: false };
  global.fetch.mockResolvedValue(respuesta(200, caso));
  const result = await getEvalCase(9);
  expect(global.fetch.mock.calls[0][0]).toMatch(/\/admin\/review-queue\/9\/eval-case$/);
  expect(result).toEqual(caso);
});
