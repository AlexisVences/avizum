import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Actividad from '../pages/Actividad';
import * as adminService from '../../services/adminService';

jest.mock('../../services/adminService', () => ({
    ...jest.requireActual('../../services/adminService'),
    listAudit: jest.fn(),
}));

const row = (id, extra = {}) => ({
    id,
    createdAt: '2026-10-20T18:30:00Z',
    actorName: 'Alexis Vences',
    action: 'user.role_changed',
    targetUserId: 12,
    detail: { from: 'user', to: 'admin' },
    ...extra,
});

const page = (items, total = items.length) => ({ items, total, page: 1, pageSize: 20 });

beforeEach(() => {
    jest.clearAllMocks();
});

describe('Actividad', () => {
    test('muestra quién, qué, a quién y cuándo en español', async () => {
        adminService.listAudit.mockResolvedValue(
            page([
                row(1),
                row(2, { action: 'user.deactivated', detail: {} }),
                row(3, { action: 'user.reactivated', detail: {} }),
                row(4, { action: 'user.deleted', detail: { role: 'user' } }),
                row(5, { action: 'review.marked', targetUserId: null, detail: { messageId: 340 } }),
                row(6, { actorName: null, action: 'user.deactivated', detail: {} }),
                row(7, { action: 'algo.raro', detail: {} }),
            ])
        );
        render(<Actividad />);
        expect(
            await screen.findAllByText('Alexis Vences cambió el rol de la persona 12: de usuario a administrador')
        ).not.toHaveLength(0);
        expect(screen.getAllByText('Alexis Vences desactivó la cuenta de la persona 12')).not.toHaveLength(0);
        expect(screen.getAllByText('Alexis Vences reactivó la cuenta de la persona 12')).not.toHaveLength(0);
        expect(screen.getAllByText('Alexis Vences eliminó la cuenta de la persona 12 (era usuario)')).not.toHaveLength(0);
        expect(screen.getAllByText('Alexis Vences marcó como revisada la respuesta 340')).not.toHaveLength(0);
        expect(screen.getAllByText('Una cuenta eliminada desactivó la cuenta de la persona 12')).not.toHaveLength(0);
        expect(screen.getAllByText('algo.raro')).not.toHaveLength(0);
        // 18:30 UTC = 12:30 en Ciudad de México (México ya no usa horario de verano).
        expect(screen.getAllByText(/20 oct 2026/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/12:30/).length).toBeGreaterThan(0);
    });

    test('filtra por acción', async () => {
        adminService.listAudit.mockResolvedValueOnce(page([row(1)])).mockResolvedValue(page([]));
        render(<Actividad />);
        await screen.findAllByText(/cambió el rol/);
        await act(async () => {
            await userEvent.selectOptions(screen.getByLabelText('Acción'), 'user.deleted');
        });
        expect(await screen.findByText('No hay actividad de este tipo')).toBeInTheDocument();
        expect(adminService.listAudit).toHaveBeenLastCalledWith(
            expect.objectContaining({ action: 'user.deleted', page: 1 })
        );
    });

    test('estado vacío con texto', async () => {
        adminService.listAudit.mockResolvedValue(page([]));
        render(<Actividad />);
        expect(await screen.findByText('Todavía no hay actividad')).toBeInTheDocument();
    });

    test('error con Reintentar', async () => {
        adminService.listAudit.mockRejectedValueOnce(new Error('Falló la carga')).mockResolvedValue(page([row(1)]));
        render(<Actividad />);
        expect(await screen.findByText('Falló la carga')).toBeInTheDocument();
        await act(async () => {
            await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        });
        expect((await screen.findAllByText(/cambió el rol/)).length).toBeGreaterThan(0);
    });
});
