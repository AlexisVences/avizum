import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Singin from '../Singin';
import { createUser } from '../../services/userService';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
    useNavigate: () => jest.fn(),
}));
jest.mock('../../components/Navbar', () => () => null);
jest.mock('../../components/GoogleSignInButton', () => ({ __esModule: true, default: () => null, GOOGLE_CLIENT_ID: '' }));
jest.mock('../../services/authService', () => ({ __esModule: true, default: {} }));
jest.mock('../../services/userService', () => ({ createUser: jest.fn() }));

const fill = () => {
    fireEvent.change(screen.getByLabelText('Nombre'), { target: { id: 'nombre', value: 'Ana' } });
    fireEvent.change(screen.getByLabelText('Apellido'), { target: { id: 'apellido', value: 'Pérez' } });
    fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { id: 'email', value: 'ana@correo.com' } });
    fireEvent.change(screen.getByLabelText('Contraseña'), { target: { id: 'password', value: 'secreta123' } });
    fireEvent.change(screen.getByLabelText('Confirmar contraseña'), { target: { id: 'confirmPassword', value: 'secreta123' } });
};
const submit = () => fireEvent.submit(screen.getByRole('button', { name: 'Crear cuenta' }).closest('form'));

beforeEach(() => jest.clearAllMocks());

test('el checkbox de términos es obligatorio y muestra un error accesible', () => {
    render(<Singin />);
    fill();
    submit();
    expect(createUser).not.toHaveBeenCalled();
    expect(screen.getByRole('alert')).toHaveTextContent(/aceptar los Términos de uso/);
    expect(screen.getByRole('checkbox')).toHaveAttribute('aria-invalid', 'true');
});

test('los enlaces apuntan a términos y aviso de privacidad con rel seguro', () => {
    render(<Singin />);
    const terminos = screen.getByRole('link', { name: 'Términos de uso' });
    const aviso = screen.getByRole('link', { name: 'Aviso de privacidad' });
    expect(terminos).toHaveAttribute('href', '/terminos');
    expect(aviso).toHaveAttribute('href', '/Aviso-legal');
    [terminos, aviso].forEach((a) => {
        expect(a).toHaveAttribute('target', '_blank');
        expect(a).toHaveAttribute('rel', 'noopener noreferrer');
    });
});

test('al aceptar se envía acceptedTerms y se avisa de la verificación por correo', async () => {
    createUser.mockResolvedValue({});
    render(<Singin />);
    fill();
    fireEvent.click(screen.getByRole('checkbox', { name: /He leído y acepto/ }));
    submit();
    await waitFor(() => expect(createUser).toHaveBeenCalled());
    expect(createUser.mock.calls[0][0]).toMatchObject({ email: 'ana@correo.com', acceptedTerms: true });
    expect(await screen.findByText(/Te enviamos un correo para verificar tu cuenta/)).toBeInTheDocument();
});
