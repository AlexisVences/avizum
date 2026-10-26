import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, within, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Resumen from '../pages/Resumen';
import * as adminService from '../../services/adminService';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
}));
jest.mock('recharts', () => {
    const Passthrough = ({ children }) => <div>{children}</div>;
    return {
        ResponsiveContainer: Passthrough,
        LineChart: Passthrough,
        Line: () => null,
        XAxis: () => null,
        YAxis: () => null,
        Tooltip: () => null,
        CartesianGrid: () => null,
    };
});
jest.mock('../../services/adminService', () => ({
    ...jest.requireActual('../../services/adminService'),
    getOverview: jest.fn(),
}));

const overview = (extra = {}) => ({
    days: 30,
    since: '2026-09-26T00:00:00Z',
    questions: 1240,
    activeUsers: 87,
    newUsers: 12,
    answersWithError: 5,
    errorRate: 0.004,
    feedbackUp: 40,
    feedbackDown: 5,
    feedbackRate: 0.89,
    feedbackRated: 45,
    tokensInput: 1000,
    tokensOutput: 2000,
    costUsd: '2.25',
    agentLookups: 33,
    series: [
        { date: '2026-10-01', questions: 4 },
        { date: '2026-10-02', questions: 0 },
        { date: '2026-10-03', questions: 9 },
    ],
    attention: [],
    ...extra,
});

beforeEach(() => {
    jest.clearAllMocks();
});

describe('Resumen', () => {
    test('muestra «Sin calificaciones» y no 0 % cuando no hay feedback', async () => {
        adminService.getOverview.mockResolvedValue(
            overview({ feedbackRate: null, feedbackRated: 0, feedbackUp: 0, feedbackDown: 0 })
        );
        render(<Resumen />);
        expect(await screen.findByText('Sin calificaciones')).toBeInTheDocument();
        expect(screen.queryByText(/^0 %/)).not.toBeInTheDocument();
    });

    test('muestra 89 % de 45 calificaciones', async () => {
        adminService.getOverview.mockResolvedValue(overview());
        render(<Resumen />);
        const satisfaccion = await screen.findByRole('group', { name: 'Satisfacción' });
        expect(satisfaccion).toHaveTextContent('89 % de 45 calificaciones');
        expect(screen.getByText('$2.25')).toBeInTheDocument();
        expect(screen.getByText('Calculado con los precios de lista del modelo')).toBeInTheDocument();
        expect(screen.getByText('1,240')).toBeInTheDocument();
    });

    test('cambiar de periodo vuelve a pedir con days=7', async () => {
        adminService.getOverview.mockResolvedValue(overview());
        render(<Resumen />);
        await screen.findByRole('group', { name: 'Satisfacción' });
        expect(adminService.getOverview).toHaveBeenLastCalledWith({ days: 30 });
        const group = screen.getByRole('radiogroup');
        expect(within(group).getByRole('radio', { name: '30 días' })).toBeChecked();
        await act(async () => {
            await userEvent.click(within(group).getByRole('radio', { name: '7 días' }));
        });
        expect(adminService.getOverview).toHaveBeenLastCalledWith({ days: 7 });
        expect(await screen.findByRole('group', { name: 'Satisfacción' })).toBeInTheDocument();
    });

    test('un error muestra ErrorState y no cifras en cero', async () => {
        adminService.getOverview.mockRejectedValue(new Error('El servidor no responde'));
        render(<Resumen />);
        expect(await screen.findByRole('alert')).toHaveTextContent('El servidor no responde');
        expect(screen.queryByText('Preguntas')).not.toBeInTheDocument();
        expect(screen.queryByText('0')).not.toBeInTheDocument();
        adminService.getOverview.mockResolvedValue(overview());
        await act(async () => {
            await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        });
        expect(await screen.findByRole('group', { name: 'Satisfacción' })).toHaveTextContent('89 %');
    });

    test('la tabla equivalente de la gráfica tiene una fila por día', async () => {
        adminService.getOverview.mockResolvedValue(overview());
        render(<Resumen />);
        const table = await screen.findByRole('table', { name: 'Preguntas por día' });
        // Una fila de encabezado más una por día.
        expect(within(table).getAllByRole('row')).toHaveLength(4);
    });

    test('Todo al día cuando attention está vacío', async () => {
        adminService.getOverview.mockResolvedValue(overview());
        render(<Resumen />);
        expect(await screen.findByText('Todo al día')).toBeInTheDocument();
    });

    test('lista los asuntos de atención como enlaces', async () => {
        adminService.getOverview.mockResolvedValue(
            overview({
                attention: [
                    { kind: 'unreviewed_down', label: 'respuestas con 👎 sin revisar', count: 3, href: '/admin/calidad' },
                ],
            })
        );
        render(<Resumen />);
        const link = await screen.findByRole('link', { name: /3 respuestas con 👎 sin revisar/ });
        expect(link).toHaveAttribute('href', '/admin/calidad');
        expect(screen.queryByText('Todo al día')).not.toBeInTheDocument();
    });

    test('sin respuestas muestra «Sin respuestas» en vez de un porcentaje', async () => {
        adminService.getOverview.mockResolvedValue(overview({ errorRate: null, answersWithError: 0 }));
        render(<Resumen />);
        expect(await screen.findByText('Sin respuestas')).toBeInTheDocument();
    });
});
