import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GestionarPerfil from '../GestionarPerfil';
import authService from '../../services/authService';
import { updateUser } from '../../services/userService';

// react-router-dom v7 and framer-motion (ESM) don't load under CRA's Jest.
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
    useNavigate: () => jest.fn(),
}));
jest.mock('../../components/NavBar2', () => () => null);
jest.mock('../../components/Footer', () => () => null);
jest.mock('../../services/authService', () => ({ __esModule: true, default: { getCurrentUser: jest.fn() } }));
jest.mock('../../services/userService', () => ({ updateUser: jest.fn() }));

const usuario = { id: 7, nombre: 'Alex', apellido: 'Vences', correo: 'alex@correo.com', rol: 'user' };

beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    authService.getCurrentUser.mockReturnValue(usuario);
});

describe('GestionarPerfil', () => {
    test('shows the user data with name/lastname locked and the email always locked', () => {
        render(<GestionarPerfil />);
        expect(screen.getByRole('heading', { level: 1, name: /Gestión de perfil/i })).toBeInTheDocument();
        expect(screen.getByLabelText('Nombre')).toHaveValue('Alex');
        expect(screen.getByLabelText('Nombre')).toBeDisabled();
        expect(screen.getByLabelText('Apellido')).toHaveValue('Vences');
        expect(screen.getByLabelText('Apellido')).toBeDisabled();
        expect(screen.getByLabelText('Correo electrónico')).toHaveValue('alex@correo.com');
        expect(screen.getByLabelText('Correo electrónico')).toBeDisabled();
        expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument();
    });

    test('has no avatar image', () => {
        render(<GestionarPerfil />);
        expect(screen.queryByRole('img')).not.toBeInTheDocument();
    });

    test('the pencil button unlocks only its own field', () => {
        render(<GestionarPerfil />);
        fireEvent.click(screen.getByRole('button', { name: 'Editar nombre' }));
        expect(screen.getByLabelText('Nombre')).toBeEnabled();
        expect(screen.getByLabelText('Apellido')).toBeDisabled();
    });

    test('saving sends the changes, keeps the email, confirms and stores the user', async () => {
        updateUser.mockResolvedValue({ ok: true });
        render(<GestionarPerfil />);
        fireEvent.click(screen.getByRole('button', { name: 'Editar nombre' }));
        fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Alexis' } });
        fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));

        await waitFor(() => expect(screen.getByText('Cambios guardados correctamente')).toBeInTheDocument());
        expect(updateUser).toHaveBeenCalledWith('alex@correo.com', {
            nombre: 'Alexis',
            apellido: 'Vences',
            rol: 'user',
            email: 'alex@correo.com',
        });
        // regression: the email used to go blank after a successful save
        expect(screen.getByLabelText('Correo electrónico')).toHaveValue('alex@correo.com');
        expect(JSON.parse(localStorage.getItem('user'))).toMatchObject({ nombre: 'Alexis', apellido: 'Vences' });
        expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument();
        expect(screen.getByLabelText('Nombre')).toBeDisabled();
    });

    test('shows the error when saving fails and keeps the save button available', async () => {
        updateUser.mockRejectedValue(new Error('Servidor caído'));
        jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<GestionarPerfil />);
        fireEvent.click(screen.getByRole('button', { name: 'Editar apellido' }));
        fireEvent.change(screen.getByLabelText('Apellido'), { target: { value: 'Otro' } });
        fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));

        expect(await screen.findByText('Servidor caído')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /guardar cambios/i })).toBeInTheDocument();
    });

    test('a later successful save clears an earlier error', async () => {
        updateUser.mockRejectedValueOnce(new Error('Servidor caído')).mockResolvedValueOnce({ ok: true });
        jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<GestionarPerfil />);
        fireEvent.click(screen.getByRole('button', { name: 'Editar nombre' }));
        fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Alexis' } });
        fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));
        await screen.findByText('Servidor caído');
        fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));
        await screen.findByText('Cambios guardados correctamente');
        expect(screen.queryByText('Servidor caído')).not.toBeInTheDocument();
    });

    test('without a session it says so and offers to log in', () => {
        authService.getCurrentUser.mockReturnValue(null);
        render(<GestionarPerfil />);
        expect(screen.getByText(/No hay usuario autenticado|No se encontró información/)).toBeInTheDocument();
        expect(screen.getByRole('link', { name: /iniciar sesión/i })).toHaveAttribute('href', '/Login');
    });
});
