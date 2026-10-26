import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor, within, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Usuarios from '../pages/Usuarios';
import * as adminService from '../../services/adminService';

jest.mock('../../services/adminService', () => ({
    ...jest.requireActual('../../services/adminService'),
    listUsers: jest.fn(),
    updateUser: jest.fn(),
    deleteUser: jest.fn(),
}));

beforeAll(() => {
    window.HTMLDialogElement.prototype.showModal = function showModal() {
        this.setAttribute('open', '');
    };
    window.HTMLDialogElement.prototype.close = function close() {
        this.removeAttribute('open');
    };
});

const row = (id, extra = {}) => ({
    id,
    firstName: `Nombre${id}`,
    lastName: `Apellido${id}`,
    email: `p${id}@correo.mx`,
    role: 'user',
    isActive: true,
    emailVerified: true,
    createdAt: '2026-09-01T10:00:00Z',
    lastActivityAt: '2026-10-20T10:00:00Z',
    questionsCount: 3,
    ...extra,
});

const page = (items, total = items.length) => ({ items, total, page: 1, pageSize: 20 });

beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('token', 'abc');
    localStorage.setItem('user', JSON.stringify({ id: 1, nombre: 'Ana', apellido: 'Pérez', correo: 'ana@correo.mx', rol: 'admin' }));
});

describe('Usuarios', () => {
    test('carga la primera página y muestra el total', async () => {
        adminService.listUsers.mockResolvedValue(page([row(2), row(3)], 45));
        render(<Usuarios />);
        expect(await screen.findByText('Nombre2 Apellido2')).toBeInTheDocument();
        expect(screen.getByText('Mostrando 1–20 de 45')).toBeInTheDocument();
        expect(adminService.listUsers).toHaveBeenCalledWith(
            expect.objectContaining({ page: 1, sort: 'created', descending: true })
        );
    });

    test('escribir en la búsqueda pide la lista filtrada tras 300 ms', async () => {
        jest.useFakeTimers();
        try {
            adminService.listUsers.mockResolvedValue(page([row(2)]));
            render(<Usuarios />);
            await act(async () => {});
            adminService.listUsers.mockClear();
            fireEvent.change(screen.getByRole('searchbox', { name: 'Buscar personas' }), { target: { value: 'ruiz' } });
            await act(async () => {
                jest.advanceTimersByTime(299);
            });
            expect(adminService.listUsers).not.toHaveBeenCalled();
            await act(async () => {
                jest.advanceTimersByTime(1);
            });
            expect(adminService.listUsers).toHaveBeenCalledTimes(1);
            expect(adminService.listUsers).toHaveBeenCalledWith(expect.objectContaining({ q: 'ruiz', page: 1 }));
            await act(async () => {});
        } finally {
            jest.useRealTimers();
        }
    });

    test('la espera de la búsqueda no devuelve a la primera página si el texto no cambió', async () => {
        jest.useFakeTimers();
        try {
            adminService.listUsers.mockResolvedValue(page([row(2)], 45));
            render(<Usuarios />);
            await act(async () => {});
            userEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
            await act(async () => {
                jest.advanceTimersByTime(400);
            });
            expect(adminService.listUsers).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }));
        } finally {
            jest.useRealTimers();
        }
    });

    test('cambiar rol pide confirmación y solo entonces llama updateUser', async () => {
        adminService.listUsers.mockResolvedValue(page([row(2)]));
        adminService.updateUser.mockResolvedValue({});
        render(<Usuarios />);
        userEvent.click(await screen.findByRole('button', { name: 'Nombre2 Apellido2' }));
        const panel = screen.getByRole('complementary', { name: 'Detalle de la persona' });
        userEvent.selectOptions(within(panel).getByLabelText('Rol'), 'admin');
        userEvent.click(within(panel).getByRole('button', { name: 'Cambiar rol' }));
        expect(adminService.updateUser).not.toHaveBeenCalled();
        const dialog = screen.getByRole('dialog');
        userEvent.click(within(dialog).getByRole('button', { name: 'Cambiar rol' }));
        await waitFor(() => expect(adminService.updateUser).toHaveBeenCalledWith(2, { role: 'admin' }));
    });

    test('eliminar deshabilita Confirmar hasta escribir el correo exacto', async () => {
        adminService.listUsers.mockResolvedValue(page([row(2)]));
        adminService.deleteUser.mockResolvedValue(null);
        render(<Usuarios />);
        userEvent.click(await screen.findByRole('button', { name: 'Nombre2 Apellido2' }));
        const panel = screen.getByRole('complementary', { name: 'Detalle de la persona' });
        userEvent.click(within(panel).getByRole('button', { name: 'Eliminar cuenta' }));
        const dialog = screen.getByRole('dialog');
        const confirm = within(dialog).getByRole('button', { name: 'Eliminar cuenta' });
        expect(confirm).toBeDisabled();
        userEvent.type(within(dialog).getByRole('textbox'), 'p2@correo.mx');
        expect(confirm).toBeEnabled();
        userEvent.click(confirm);
        await waitFor(() => expect(adminService.deleteUser).toHaveBeenCalledWith(2, 'p2@correo.mx'));
    });

    test('en la fila propia las acciones están deshabilitadas y se explica por qué', async () => {
        adminService.listUsers.mockResolvedValue(page([row(1, { firstName: 'Ana', lastName: 'Pérez', role: 'admin' })]));
        render(<Usuarios />);
        userEvent.click(await screen.findByRole('button', { name: 'Ana Pérez' }));
        const panel = screen.getByRole('complementary', { name: 'Detalle de la persona' });
        expect(within(panel).getByRole('button', { name: 'Cambiar rol' })).toBeDisabled();
        expect(within(panel).getByRole('button', { name: 'Desactivar cuenta' })).toBeDisabled();
        expect(within(panel).getByRole('button', { name: 'Eliminar cuenta' })).toBeDisabled();
        expect(within(panel).getByText(/No puedes cambiar tu propia cuenta/)).toBeInTheDocument();
    });

    test('un error del servicio muestra ErrorState con Reintentar, no una lista vacía', async () => {
        adminService.listUsers.mockRejectedValueOnce(new adminService.AdminApiError('Servicio caído', 500));
        adminService.listUsers.mockResolvedValue(page([row(2)]));
        render(<Usuarios />);
        expect(await screen.findByText('Servicio caído')).toBeInTheDocument();
        expect(screen.queryByText(/No encontramos/)).not.toBeInTheDocument();
        userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        expect(await screen.findByText('Nombre2 Apellido2')).toBeInTheDocument();
    });

    test('sin resultados muestra EmptyState con la sugerencia de quitar filtros', async () => {
        adminService.listUsers.mockResolvedValue(page([], 0));
        render(<Usuarios />);
        userEvent.selectOptions(await screen.findByLabelText('Estado'), 'false');
        expect(await screen.findByText('No encontramos personas')).toBeInTheDocument();
        expect(screen.getByText(/quitar algún filtro/)).toBeInTheDocument();
        adminService.listUsers.mockResolvedValue(page([row(2)]));
        userEvent.click(screen.getByRole('button', { name: 'Quitar filtros' }));
        expect(await screen.findByText('Nombre2 Apellido2')).toBeInTheDocument();
    });

    test('ordenar por un encabezado marca aria-sort y pide el orden', async () => {
        adminService.listUsers.mockResolvedValue(page([row(2)]));
        render(<Usuarios />);
        await screen.findByText('Nombre2 Apellido2');
        const th = screen.getByRole('columnheader', { name: /Preguntas/ });
        expect(th).toHaveAttribute('aria-sort', 'none');
        userEvent.click(within(th).getByRole('button'));
        await waitFor(() => expect(th).toHaveAttribute('aria-sort', 'descending'));
        expect(adminService.listUsers).toHaveBeenLastCalledWith(
            expect.objectContaining({ sort: 'questions', descending: true })
        );
    });

    test('un código de error conocido se muestra con texto propio', async () => {
        adminService.listUsers.mockResolvedValue(page([row(2, { role: 'admin' })]));
        adminService.updateUser.mockRejectedValue(new adminService.AdminApiError('x', 409, 'last_admin'));
        render(<Usuarios />);
        userEvent.click(await screen.findByRole('button', { name: 'Nombre2 Apellido2' }));
        const panel = screen.getByRole('complementary', { name: 'Detalle de la persona' });
        userEvent.click(within(panel).getByRole('button', { name: 'Desactivar cuenta' }));
        userEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Desactivar cuenta' }));
        expect(await within(panel).findByRole('alert')).toHaveTextContent('Debe quedar al menos un administrador activo');
    });
});
