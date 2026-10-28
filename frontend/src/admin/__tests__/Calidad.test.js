import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, within, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Calidad from '../pages/Calidad';
import * as adminService from '../../services/adminService';

jest.mock('../../services/adminService', () => ({
    ...jest.requireActual('../../services/adminService'),
    listReviewQueue: jest.fn(),
    markReviewed: jest.fn(),
    getEvalCase: jest.fn(),
}));

const item = (id, extra = {}) => ({
    messageId: id,
    askedAt: '2026-10-20T18:30:00Z',
    reasons: ['negative'],
    question: `Pregunta número ${id}`,
    answer: `Respuesta número ${id} según el reglamento [23].`,
    citations: [
        {
            sourceSlug: 'reglamento',
            sourceTitle: 'Reglamento de Tránsito',
            article: '44',
            fraction: 'I',
            page: 56,
            url: 'https://x.mx/r.pdf#page=56',
        },
    ],
    tools: ['buscar_normativa'],
    reviewed: false,
    note: null,
    ...extra,
});

const page = (items, total = items.length) => ({ items, total, page: 1, pageSize: 20 });

const settled = () =>
    waitFor(() => expect(screen.getByRole('list', { name: 'Respuestas' })).toHaveAttribute('aria-busy', 'false'));

beforeEach(() => {
    jest.clearAllMocks();
});

describe('Calidad', () => {
    test('muestra pregunta, respuesta y fuentes de la fila elegida', async () => {
        adminService.listReviewQueue.mockResolvedValue(page([item(1), item(2, { reasons: ['error', 'uncited'] })]));
        render(<Calidad />);
        const detail = await screen.findByRole('region', { name: 'Detalle de la respuesta' });
        expect(within(detail).getByText('Pregunta número 1')).toBeInTheDocument();
        expect(within(detail).getByText(/Respuesta número 1 según el reglamento/)).toBeInTheDocument();
        expect(within(detail).getByText(/Reglamento de Tránsito · art\. 44, fr\. I · pág\. 56/)).toBeInTheDocument();
        expect(within(detail).getByText('buscar_normativa')).toBeInTheDocument();

        await userEvent.click(screen.getByRole('button', { name: /Pregunta número 2/ }));
        const detail2 = screen.getByRole('region', { name: 'Detalle de la respuesta' });
        expect(within(detail2).getByText('Pregunta número 2')).toBeInTheDocument();
        expect(within(screen.getByRole('list', { name: 'Respuestas' })).getByText('Con error')).toBeInTheDocument();
        expect(within(screen.getByRole('list', { name: 'Respuestas' })).getByText('Sin citas')).toBeInTheDocument();
        expect(within(screen.getByRole('list', { name: 'Respuestas' })).getByText('Mal calificada')).toBeInTheDocument();
    });

    test('Marcar como revisada llama al servicio con la nota y la pasa a Revisadas', async () => {
        adminService.listReviewQueue.mockImplementation(async ({ reviewed }) =>
            reviewed ? page([item(1, { reviewed: true, note: 'Falta el art. 12' })]) : page([item(1), item(2)])
        );
        adminService.markReviewed.mockResolvedValue({ messageId: 1, reviewed: true, note: 'Falta el art. 12' });
        render(<Calidad />);
        const detail = await screen.findByRole('region', { name: 'Detalle de la respuesta' });
        await userEvent.type(within(detail).getByLabelText('Nota'), 'Falta el art. 12');
        expect(within(detail).getByText('16 / 500')).toBeInTheDocument();
        await act(async () => {
            await userEvent.click(within(detail).getByRole('button', { name: 'Marcar como revisada' }));
        });

        await waitFor(() => expect(adminService.markReviewed).toHaveBeenCalledWith(1, 'Falta el art. 12'));
        // Sale de «Por revisar» y se elige la siguiente.
        await waitFor(() =>
            expect(
                within(screen.getByRole('region', { name: 'Detalle de la respuesta' })).getByText('Pregunta número 2')
            ).toBeInTheDocument()
        );
        expect(screen.queryByRole('button', { name: /Pregunta número 1/ })).not.toBeInTheDocument();

        await act(async () => {
            await userEvent.click(screen.getByRole('tab', { name: 'Revisadas' }));
        });
        expect(await screen.findByRole('button', { name: /Pregunta número 1/ })).toBeInTheDocument();
        expect(adminService.listReviewQueue).toHaveBeenLastCalledWith(expect.objectContaining({ reviewed: true }));
        expect(await screen.findByText('Falta el art. 12')).toBeInTheDocument();
        await settled();
    });

    test('muestra el mensaje del servidor si la nota es rechazada', async () => {
        adminService.listReviewQueue.mockResolvedValue(page([item(1)]));
        adminService.markReviewed.mockRejectedValue(new Error('La nota es demasiado larga'));
        render(<Calidad />);
        await userEvent.click(await screen.findByRole('button', { name: 'Marcar como revisada' }));
        expect(await screen.findByText('La nota es demasiado larga')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Pregunta número 1/ })).toBeInTheDocument();
    });

    test('Copiar como caso de evaluación escribe una línea JSON válida en el portapapeles', async () => {
        const caso = { id: 'q-1', question: 'Pregunta número 1', coverage: 'covered', expected: [], notes: 'n', verified: false };
        adminService.listReviewQueue.mockResolvedValue(page([item(1)]));
        adminService.getEvalCase.mockResolvedValue(caso);
        const writeText = jest.fn().mockResolvedValue();
        Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
        render(<Calidad />);
        await userEvent.click(await screen.findByRole('button', { name: 'Copiar como caso de evaluación' }));
        await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
        const line = writeText.mock.calls[0][0];
        expect(line).not.toContain('\n');
        expect(JSON.parse(line)).toEqual(caso);
        expect(adminService.getEvalCase).toHaveBeenCalledWith(1);
        expect(await screen.findByText('Copiado')).toBeInTheDocument();
    });

    test('si el portapapeles falla, lo dice y deja la línea para copiarla a mano', async () => {
        adminService.listReviewQueue.mockResolvedValue(page([item(1)]));
        adminService.getEvalCase.mockResolvedValue({ id: 'q-1' });
        Object.defineProperty(navigator, 'clipboard', {
            value: { writeText: jest.fn().mockRejectedValue(new Error('denegado')) },
            configurable: true,
        });
        render(<Calidad />);
        await userEvent.click(await screen.findByRole('button', { name: 'Copiar como caso de evaluación' }));
        expect(await screen.findByRole('alert')).toHaveTextContent('No pudimos copiar al portapapeles');
        expect(screen.getByLabelText('Caso de evaluación')).toHaveValue('{"id":"q-1"}');
        expect(screen.queryByText('Copiado')).not.toBeInTheDocument();
    });

    test('cola vacía: «No hay respuestas por revisar»', async () => {
        adminService.listReviewQueue.mockResolvedValue(page([]));
        render(<Calidad />);
        expect(await screen.findByText('No hay respuestas por revisar')).toBeInTheDocument();
    });

    test('error con Reintentar', async () => {
        adminService.listReviewQueue.mockRejectedValueOnce(new Error('Sin conexión con el servidor'));
        adminService.listReviewQueue.mockResolvedValueOnce(page([item(1)]));
        render(<Calidad />);
        expect(await screen.findByRole('alert')).toHaveTextContent('Sin conexión con el servidor');
        expect(screen.queryByText('No hay respuestas por revisar')).not.toBeInTheDocument();
        await act(async () => {
            await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        });
        expect(await screen.findByRole('button', { name: /Pregunta número 1/ })).toBeInTheDocument();
        await settled();
    });

    test('filtrar por motivo vuelve a pedir la cola con ese motivo', async () => {
        adminService.listReviewQueue.mockResolvedValue(page([item(1)]));
        render(<Calidad />);
        await screen.findByRole('button', { name: /Pregunta número 1/ });
        await act(async () => {
            await userEvent.selectOptions(screen.getByLabelText('Motivo'), 'error');
        });
        await waitFor(() =>
            expect(adminService.listReviewQueue).toHaveBeenLastCalledWith(
                expect.objectContaining({ reason: 'error', reviewed: false, page: 1 })
            )
        );
        await settled();
    });
});
