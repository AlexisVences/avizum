import { verifyEmail, resendVerification, forgotPassword, resetPassword } from '../emailAccountService';

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
afterEach(() => localStorage.clear());

test('verifyEmail posts the token', async () => {
  fetch.mockResolvedValue(respuesta(200, {}));
  await verifyEmail('abc');
  const [url, init] = fetch.mock.calls[0];
  expect(url).toMatch(/\/auth\/verify-email$/);
  expect(init.method).toBe('POST');
  expect(JSON.parse(init.body)).toEqual({ token: 'abc' });
});

test('verifyEmail surfaces the server detail and status', async () => {
  fetch.mockResolvedValue(respuesta(400, { detail: 'Enlace vencido' }));
  await expect(verifyEmail('abc')).rejects.toMatchObject({ message: 'Enlace vencido', status: 400 });
});

test('verifyEmail uses a Spanish fallback when there is no body', async () => {
  fetch.mockResolvedValue(respuesta(500));
  await expect(verifyEmail('abc')).rejects.toThrow('El enlace no es válido o ya expiró.');
});

test('resendVerification sends the bearer token and no body', async () => {
  fetch.mockResolvedValue(respuesta(202));
  await resendVerification();
  const [url, init] = fetch.mock.calls[0];
  expect(url).toMatch(/\/auth\/resend-verification$/);
  expect(init.headers.Authorization).toBe('Bearer tok');
  expect(init.body).toBeUndefined();
});

test('resendVerification reports 429 with a clear message', async () => {
  fetch.mockResolvedValue(respuesta(429, { detail: 'Too many' }));
  await expect(resendVerification()).rejects.toMatchObject({ status: 429, message: expect.stringMatching(/Demasiados intentos/) });
});

test('forgotPassword posts the email without auth header', async () => {
  fetch.mockResolvedValue(respuesta(202, {}));
  await forgotPassword('a@b.com');
  const [url, init] = fetch.mock.calls[0];
  expect(url).toMatch(/\/auth\/forgot-password$/);
  expect(JSON.parse(init.body)).toEqual({ email: 'a@b.com' });
  expect(init.headers.Authorization).toBeUndefined();
});

test('resetPassword posts token and password; 422 detail list is joined', async () => {
  fetch.mockResolvedValue(respuesta(200, {}));
  await resetPassword('t', 'Nueva123!');
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ token: 't', password: 'Nueva123!' });

  fetch.mockResolvedValue(respuesta(422, { detail: [{ msg: 'Muy corta' }, { msg: 'Sin número' }] }));
  await expect(resetPassword('t', 'x')).rejects.toMatchObject({ message: 'Muy corta, Sin número', status: 422 });
});

test('a network failure gives the Spanish connection message', async () => {
  fetch.mockRejectedValue(new TypeError('Failed to fetch'));
  await expect(forgotPassword('a@b.com')).rejects.toThrow(/No pudimos conectar/);
});
