import React from 'react';
import '@testing-library/jest-dom';
import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Fuentes from '../pages/Fuentes';
import * as adminService from '../../services/adminService';

jest.mock('../../services/adminService', () => ({
    ...jest.requireActual('../../services/adminService'),
    listSources: jest.fn(),
}));

const source = (slug, extra = {}) => ({
    slug,
    title: `Título ${slug}`,
    kind: 'ley',
    url: `https://example.gob.mx/${slug}`,
    lastReformDate: '2026-06-30',
    retrievedAt: '2026-10-20T18:30:00Z',
    chunkCount: 12,
    versions: 1,
    reviewDue: false,
    reviewDueSince: null,
    ...extra,
});

const payload = (sources, pendingSanctions = 0) => ({ sources, pendingSanctions });

beforeEach(() => {
    jest.clearAllMocks();
});

describe('Fuentes', () => {
    test('agrupa por tipo', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { kind: 'ley' }),
                source('b', { kind: 'reglamento' }),
                source('c', { kind: 'tarifas' }),
                source('d', { kind: 'ficha' }),
                source('e', { kind: 'rarito' }),
            ])
        );
        render(<Fuentes />);
        expect(await screen.findByRole('heading', { name: 'Leyes' })).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Reglamentos' })).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Tarifas oficiales' })).toBeInTheDocument();
        expect(
            screen.getByRole('heading', { name: 'Fichas oficiales (páginas web transcritas)' })
        ).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Rarito' })).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: 'Códigos' })).not.toBeInTheDocument();
    });

    test('muestra fecha de reforma o de consulta, fragmentos y versiones', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { chunkCount: 1, versions: 1 }),
                source('b', { lastReformDate: null, chunkCount: 5, versions: 2 }),
            ])
        );
        render(<Fuentes />);
        expect(await screen.findAllByRole('listitem')).toHaveLength(2);
        expect(screen.getAllByText('Reforma: 30 jun 2026')).toHaveLength(1);
        expect(screen.getAllByText('Consultada/descargada: 20 oct 2026')).toHaveLength(1);
        expect(screen.getAllByText('1 fragmento')).toHaveLength(1);
        expect(screen.getAllByText('5 fragmentos')).toHaveLength(1);
        expect(screen.getAllByText('1 versión')).toHaveLength(1);
        expect(screen.getAllByText('2 versiones')).toHaveLength(1);
    });

    test('«Por revisar» lleva texto además de color', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { reviewDue: true, reviewDueSince: '2026-05-03' }),
                source('b'),
            ])
        );
        render(<Fuentes />);
        expect(await screen.findAllByRole('listitem')).toHaveLength(2);
        expect(screen.getAllByText('Por revisar desde 3 may 2026')).toHaveLength(1);
        expect(screen.getAllByText('Al día')).toHaveLength(1);
    });

    test('el enlace abre en pestaña nueva con rel noopener', async () => {
        adminService.listSources.mockResolvedValue(payload([source('a')]));
        render(<Fuentes />);
        const link = await screen.findByRole('link', { name: 'Título a' });
        expect(link).toHaveAttribute('href', 'https://example.gob.mx/a');
        expect(link).toHaveAttribute('target', '_blank');
        expect(link.getAttribute('rel')).toMatch(/noopener/);
        expect(link.getAttribute('rel')).toMatch(/noreferrer/);
    });

    test('una URL que no es http(s) no se vuelve enlace y el título sigue visible', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { url: 'javascript:alert(1)' }),
                source('b', { url: '/x' }),
                source('c', { url: 'data:text/html,hola' }),
                source('d'),
            ])
        );
        render(<Fuentes />);
        expect(await screen.findAllByRole('listitem')).toHaveLength(4);
        expect(screen.getAllByRole('link')).toHaveLength(1);
        expect(screen.getByRole('link', { name: 'Título d' })).toBeInTheDocument();
        ['a', 'b', 'c'].forEach((slug) => {
            expect(screen.getByText(`Título ${slug}`)).toBeInTheDocument();
            expect(screen.queryByRole('link', { name: `Título ${slug}` })).not.toBeInTheDocument();
        });
    });

    test('la fecha de consulta usa el calendario de Ciudad de México', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { lastReformDate: null, retrievedAt: '2026-10-21T03:00:00Z' }),
                source('b', { lastReformDate: null, retrievedAt: '2026-10-21T03:00:00' }),
            ])
        );
        render(<Fuentes />);
        await screen.findAllByRole('listitem');
        expect(screen.getAllByText('Consultada/descargada: 20 oct 2026')).toHaveLength(2);
    });

    test('el filtro «Por revisar» oculta las demás', async () => {
        adminService.listSources.mockResolvedValue(
            payload([
                source('a', { reviewDue: true, reviewDueSince: '2026-05-03' }),
                source('b', { kind: 'codigo' }),
            ])
        );
        render(<Fuentes />);
        expect(await screen.findAllByRole('listitem')).toHaveLength(2);
        await userEvent.click(screen.getByRole('checkbox', { name: 'Solo por revisar' }));
        expect(screen.queryByText('Título b')).not.toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: 'Códigos' })).not.toBeInTheDocument();
        expect(screen.getAllByText('Título a')).toHaveLength(1);
        expect(screen.getAllByRole('listitem')).toHaveLength(1);
    });

    test('sin fuentes por revisar el filtro muestra un estado vacío', async () => {
        adminService.listSources.mockResolvedValue(payload([source('a')]));
        render(<Fuentes />);
        await screen.findAllByRole('listitem');
        await userEvent.click(screen.getByRole('checkbox', { name: 'Solo por revisar' }));
        expect(screen.getByText('No hay fuentes por revisar')).toBeInTheDocument();
        expect(screen.queryByText('Título a')).not.toBeInTheDocument();
    });

    test('muestra la nota y la cifra de sanciones sin revisar', async () => {
        adminService.listSources.mockResolvedValue(payload([source('a')], 1200));
        const { unmount } = render(<Fuentes />);
        expect(
            await screen.findByText('La actualización se hace con los scripts; aquí solo se vigila.')
        ).toBeInTheDocument();
        expect(screen.getByText('1,200 filas de sanciones sin revisar')).toBeInTheDocument();
        unmount();
        adminService.listSources.mockResolvedValue(payload([source('a')], 0));
        render(<Fuentes />);
        expect(await screen.findByText('Sanciones al día')).toBeInTheDocument();
    });

    test('error con Reintentar', async () => {
        adminService.listSources.mockRejectedValueOnce(new Error('Servidor caído'));
        adminService.listSources.mockResolvedValue(payload([source('a')]));
        render(<Fuentes />);
        const alert = await screen.findByRole('alert');
        expect(within(alert).getByText('Servidor caído')).toBeInTheDocument();
        expect(screen.queryByText('No hay fuentes por revisar')).not.toBeInTheDocument();
        // The retry resolves right after the click: keep that update inside act.
        await act(async () => {
            userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        });
        expect(await screen.findAllByRole('listitem')).toHaveLength(1);
        expect(adminService.listSources).toHaveBeenCalledTimes(2);
    });
});
