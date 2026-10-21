import axios from 'axios';
import authService from '../authService';

jest.mock('axios');

const session = {
  access_token: 'jwt-123',
  user: { id: 7, first_name: 'Ana', last_name: 'López', email: 'ana@example.com', role: 'user' },
};

beforeEach(() => localStorage.clear());

test('Google sign-in sends the credential and stores the same session as a password login', async () => {
  axios.post.mockResolvedValue({ data: session });
  await authService.loginWithGoogle('google-id-token');
  expect(axios.post).toHaveBeenCalledWith(expect.stringMatching(/\/auth\/google$/), { credential: 'google-id-token' });
  expect(localStorage.getItem('token')).toBe('jwt-123');
  expect(authService.getCurrentUser()).toMatchObject({ id: 7, correo: 'ana@example.com', rol: 'user' });
});

test('a failed Google sign-in shows the server message and stores nothing', async () => {
  axios.post.mockRejectedValue({ response: { data: { detail: 'No pudimos verificar tu cuenta de Google' } } });
  await expect(authService.loginWithGoogle('bad')).rejects.toThrow('No pudimos verificar tu cuenta de Google');
  expect(localStorage.getItem('token')).toBeNull();
});
