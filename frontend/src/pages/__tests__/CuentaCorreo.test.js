import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import VerificarCorreo from '../VerificarCorreo';
import OlvideContrasena from '../OlvideContrasena';
import RestablecerContrasena from '../RestablecerContrasena';
import { verifyEmail, resendVerification, forgotPassword, resetPassword } from '../../services/emailAccountService';

let mockParams = new URLSearchParams();
jest.mock('react-router-dom', () => ({
  Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
  useNavigate: () => jest.fn(),
  useSearchParams: () => [mockParams],
}));
jest.mock('../../components/Navbar', () => () => null);
jest.mock('../../services/emailAccountService');

const deferred = () => {
  let resolve, reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
};
const fallo = (message, status) => Object.assign(new Error(message), { status });

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  mockParams = new URLSearchParams();
});

describe('VerificarCorreo', () => {
  test('without a token shows an error and never calls the API', () => {
    render(<VerificarCorreo />);
    expect(screen.getByRole('alert')).toHaveTextContent(/falta el código/i);
    expect(verifyEmail).not.toHaveBeenCalled();
  });

  test('verifies once on mount, shows loading then success with a login link when logged out', async () => {
    mockParams = new URLSearchParams('token=abc');
    const d = deferred();
    verifyEmail.mockReturnValue(d.promise);
    render(<VerificarCorreo />);
    expect(screen.getByText(/Verificando tu correo/)).toBeInTheDocument();
    d.resolve({});
    expect(await screen.findByText('Tu correo quedó verificado.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Iniciar sesión' })).toHaveAttribute('href', '/Login');
    expect(verifyEmail).toHaveBeenCalledTimes(1);
    expect(verifyEmail).toHaveBeenCalledWith('abc');
  });

  test('success when logged in links to the app and updates the stored flag', async () => {
    mockParams = new URLSearchParams('token=abc');
    localStorage.setItem('token', 't');
    localStorage.setItem('user', JSON.stringify({ id: 1, emailVerificado: false }));
    verifyEmail.mockResolvedValue({});
    render(<VerificarCorreo />);
    expect(await screen.findByRole('link', { name: 'Ir a la aplicación' })).toHaveAttribute('href', '/Bienvenida');
    expect(JSON.parse(localStorage.getItem('user')).emailVerificado).toBe(true);
  });

  test('a bad token shows the error; logged out offers login instead of a resend', async () => {
    mockParams = new URLSearchParams('token=abc');
    verifyEmail.mockRejectedValue(fallo('Enlace vencido', 400));
    render(<VerificarCorreo />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Enlace vencido');
    expect(screen.queryByRole('button', { name: /nuevo enlace/i })).not.toBeInTheDocument();
  });

  test('a bad token while logged in lets the user request a new link', async () => {
    mockParams = new URLSearchParams('token=abc');
    localStorage.setItem('token', 't');
    verifyEmail.mockRejectedValue(fallo('Enlace vencido', 400));
    const d = deferred();
    resendVerification.mockReturnValue(d.promise);
    render(<VerificarCorreo />);
    const boton = await screen.findByRole('button', { name: 'Solicitar un nuevo enlace' });
    fireEvent.click(boton);
    expect(screen.getByRole('button', { name: 'Enviando...' })).toBeDisabled();
    d.resolve();
    expect(await screen.findByText(/Te enviamos un nuevo enlace/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Solicitar un nuevo enlace' })).toBeDisabled();
  });

  test('a failed resend shows its error', async () => {
    mockParams = new URLSearchParams('token=abc');
    localStorage.setItem('token', 't');
    verifyEmail.mockRejectedValue(fallo('Enlace vencido', 400));
    resendVerification.mockRejectedValue(fallo('Demasiados intentos', 429));
    render(<VerificarCorreo />);
    fireEvent.click(await screen.findByRole('button', { name: 'Solicitar un nuevo enlace' }));
    await waitFor(() => expect(screen.getAllByRole('alert')).toHaveLength(2));
    expect(screen.getByText('Demasiados intentos')).toBeInTheDocument();
  });
});

describe('OlvideContrasena', () => {
  const enviar = () => {
    fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: ' a@b.com ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar instrucciones' }));
  };

  test('disables the button while sending and then shows the neutral message', async () => {
    const d = deferred();
    forgotPassword.mockReturnValue(d.promise);
    render(<OlvideContrasena />);
    enviar();
    expect(screen.getByRole('button', { name: 'Enviando...' })).toBeDisabled();
    expect(forgotPassword).toHaveBeenCalledWith('a@b.com');
    d.resolve();
    expect(await screen.findByText('Si el correo está registrado, te enviamos instrucciones')).toBeInTheDocument();
    expect(screen.queryByLabelText('Correo electrónico')).not.toBeInTheDocument();
  });

  test('shows a connection error and keeps the form', async () => {
    forgotPassword.mockRejectedValue(new Error('No pudimos conectar con el servidor.'));
    render(<OlvideContrasena />);
    enviar();
    expect(await screen.findByRole('alert')).toHaveTextContent(/No pudimos conectar/);
    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument();
    expect(screen.queryByText(/te enviamos instrucciones/)).not.toBeInTheDocument();
  });
});

describe('RestablecerContrasena', () => {
  const llenar = (a, b) => {
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: a } });
    fireEvent.change(screen.getByLabelText('Confirma tu contraseña'), { target: { value: b } });
    fireEvent.click(screen.getByRole('button', { name: 'Restablecer contraseña' }));
  };

  test('without a token shows an error and a link to request a new one', () => {
    render(<RestablecerContrasena />);
    expect(screen.getByRole('alert')).toHaveTextContent(/falta el código/i);
    expect(screen.getByRole('link', { name: /nuevo enlace/i })).toHaveAttribute('href', '/olvide-contrasena');
    expect(screen.queryByLabelText('Nueva contraseña')).not.toBeInTheDocument();
  });

  test('a mismatch is caught on the client', () => {
    mockParams = new URLSearchParams('token=t');
    render(<RestablecerContrasena />);
    llenar('Segura123!', 'Otra123!');
    expect(screen.getByRole('alert')).toHaveTextContent('Las contraseñas no coinciden');
    expect(resetPassword).not.toHaveBeenCalled();
  });

  test('success shows the message and a login link, with a disabled button while saving', async () => {
    mockParams = new URLSearchParams('token=t');
    const d = deferred();
    resetPassword.mockReturnValue(d.promise);
    render(<RestablecerContrasena />);
    llenar('Segura123!', 'Segura123!');
    expect(screen.getByRole('button', { name: 'Guardando...' })).toBeDisabled();
    expect(resetPassword).toHaveBeenCalledWith('t', 'Segura123!');
    d.resolve({});
    expect(await screen.findByText('Tu contraseña se actualizó correctamente.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Iniciar sesión' })).toHaveAttribute('href', '/Login');
  });

  test('a bad token (400) replaces the form with the error and a new-link option', async () => {
    mockParams = new URLSearchParams('token=t');
    resetPassword.mockRejectedValue(fallo('Enlace usado', 400));
    render(<RestablecerContrasena />);
    llenar('Segura123!', 'Segura123!');
    expect(await screen.findByRole('alert')).toHaveTextContent('Enlace usado');
    expect(screen.getByRole('link', { name: /nuevo enlace/i })).toBeInTheDocument();
    expect(screen.queryByLabelText('Nueva contraseña')).not.toBeInTheDocument();
  });

  test('a weak password (422) keeps the form so the user can retry', async () => {
    mockParams = new URLSearchParams('token=t');
    resetPassword.mockRejectedValue(fallo('La contraseña es muy débil', 422));
    render(<RestablecerContrasena />);
    llenar('abc', 'abc');
    expect(await screen.findByRole('alert')).toHaveTextContent('La contraseña es muy débil');
    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Restablecer contraseña' })).toBeEnabled();
  });
});
