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
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
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
        });
        expect(updateUser.mock.calls[0][1]).not.toHaveProperty('email');
        expect(updateUser.mock.calls[0][1]).not.toHaveProperty('currentPassword');
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

describe('GestionarPerfil: cambio de correo y contraseña', () => {
    const editarCorreo = (valor) => {
        fireEvent.click(screen.getByRole('button', { name: 'Editar correo' }));
        fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: valor } });
    };
    const guardar = () => fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));

    test('current password is hidden when only the name changes', () => {
        render(<GestionarPerfil />);
        fireEvent.click(screen.getByRole('button', { name: 'Editar nombre' }));
        fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Alexis' } });
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
    });

    test('an email differing only in case does not count as a change', () => {
        render(<GestionarPerfil />);
        editarCorreo('ALEX@correo.com');
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /guardar/i })).not.toBeInTheDocument();
    });

    test('changing the email shows a required current password and blocks saving without it', async () => {
        render(<GestionarPerfil />);
        editarCorreo('nuevo@correo.com');
        expect(screen.getByLabelText('Contraseña actual')).toBeRequired();
        guardar();
        expect(await screen.findByText('Ingresa tu contraseña actual para continuar')).toBeInTheDocument();
        expect(updateUser).not.toHaveBeenCalled();
    });

    test('changing the email sends current_password and the new email', async () => {
        updateUser.mockResolvedValue({ ok: true });
        render(<GestionarPerfil />);
        editarCorreo('Nuevo@Correo.com');
        fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'Secreta123' } });
        guardar();
        await screen.findByText('Cambios guardados correctamente');
        expect(updateUser).toHaveBeenCalledWith('alex@correo.com', expect.objectContaining({
            email: 'Nuevo@Correo.com',
            currentPassword: 'Secreta123',
        }));
        expect(updateUser.mock.calls[0][1]).not.toHaveProperty('password');
        expect(JSON.parse(localStorage.getItem('user')).correo).toBe('Nuevo@Correo.com');
    });

    test('changing the password shows and requires the current password, and sends both', async () => {
        updateUser.mockResolvedValue({ ok: true });
        render(<GestionarPerfil />);
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Nueva12345' } });
        expect(screen.getByLabelText('Contraseña actual')).toBeRequired();
        fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'Vieja123' } });
        guardar();
        await screen.findByText('Cambios guardados correctamente');
        const enviado = updateUser.mock.calls[0][1];
        expect(enviado).toMatchObject({ password: 'Nueva12345', currentPassword: 'Vieja123' });
        expect(enviado).not.toHaveProperty('email');
    });

    test('403 shows the wrong current password message', async () => {
        updateUser.mockRejectedValue(Object.assign(new Error('Current password is required and must be correct'), { status: 403 }));
        jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<GestionarPerfil />);
        editarCorreo('nuevo@correo.com');
        fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'mala' } });
        guardar();
        expect(await screen.findByText('La contraseña actual no es correcta')).toBeInTheDocument();
    });

    test('403 for a Google-only account asks to set a password first', async () => {
        updateUser.mockRejectedValue(Object.assign(new Error('Set a password before changing your email'), { status: 403 }));
        jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<GestionarPerfil />);
        editarCorreo('nuevo@correo.com');
        fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'x' } });
        guardar();
        expect(await screen.findByText(/Primero crea una contraseña/)).toBeInTheDocument();
    });

    test('409 shows the email already registered message', async () => {
        updateUser.mockRejectedValue(Object.assign(new Error('Email already registered'), { status: 409 }));
        jest.spyOn(console, 'error').mockImplementation(() => {});
        render(<GestionarPerfil />);
        editarCorreo('otro@correo.com');
        fireEvent.change(screen.getByLabelText('Contraseña actual'), { target: { value: 'x' } });
        guardar();
        expect(await screen.findByText('Ese correo ya está registrado')).toBeInTheDocument();
    });
});

describe('GestionarPerfil: cuentas sin contraseña (Google)', () => {
    const editarCorreo = (valor) => {
        fireEvent.click(screen.getByRole('button', { name: 'Editar correo' }));
        fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: valor } });
    };
    const guardar = () => fireEvent.click(screen.getByRole('button', { name: /guardar cambios/i }));
    const soloGoogle = () => authService.getCurrentUser.mockReturnValue({ ...usuario, tienePassword: false });

    test('a Google-only user sets a first password without the current password field', async () => {
        soloGoogle();
        updateUser.mockResolvedValue({ ok: true });
        render(<GestionarPerfil />);
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Nueva12345' } });
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
        guardar();
        await screen.findByText('Cambios guardados correctamente');
        const enviado = updateUser.mock.calls[0][1];
        expect(enviado.password).toBe('Nueva12345');
        expect(enviado).not.toHaveProperty('currentPassword');
    });

    test('a Google-only user changing the email sees the message and no request is made', async () => {
        soloGoogle();
        render(<GestionarPerfil />);
        editarCorreo('nuevo@correo.com');
        expect(screen.queryByLabelText('Contraseña actual')).not.toBeInTheDocument();
        guardar();
        expect(
            await screen.findByText('Primero crea una contraseña para tu cuenta y después podrás cambiar tu correo')
        ).toBeInTheDocument();
        expect(updateUser).not.toHaveBeenCalled();
    });

    test('a user with a password still has to give the current one', () => {
        authService.getCurrentUser.mockReturnValue({ ...usuario, tienePassword: true });
        render(<GestionarPerfil />);
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Nueva12345' } });
        expect(screen.getByLabelText('Contraseña actual')).toBeRequired();
    });

    test('a stored session without the flag behaves as if it had a password', () => {
        render(<GestionarPerfil />);
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Nueva12345' } });
        expect(screen.getByLabelText('Contraseña actual')).toBeInTheDocument();
    });

    test('after the first password is set the flag becomes true and the next change asks for it', async () => {
        soloGoogle();
        updateUser.mockResolvedValue({ ok: true });
        render(<GestionarPerfil />);
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Nueva12345' } });
        guardar();
        await screen.findByText('Cambios guardados correctamente');
        expect(JSON.parse(localStorage.getItem('user')).tienePassword).toBe(true);
        fireEvent.change(screen.getByLabelText('Nueva contraseña'), { target: { value: 'Otra123456' } });
        expect(screen.getByLabelText('Contraseña actual')).toBeRequired();
    });
});
