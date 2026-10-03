import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import ArticuloContenido from '../ArticuloContenido';

// react-router-dom v7 doesn't resolve under CRA's Jest; only Link is used here.
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
}));

const categoria = { numero: '16', etiqueta: 'CONTACTO' };

const renderArticulo = (articulo) =>
    render(<ArticuloContenido categoria={categoria} articulo={articulo} />);

describe('ArticuloContenido tipo directorio', () => {
    const articulo = {
        titulo: 'Directorio oficial',
        actualizado: '2026-10',
        tipo: 'directorio',
        directorio: [
            {
                nombre: 'SEMOVI',
                telefono: '55 5555 5555',
                sitio: 'https://www.semovi.cdmx.gob.mx',
                direccion: 'Calle Falsa 123',
            },
            { nombre: 'Solo nombre y sitio', sitio: 'https://example.gob.mx' },
        ],
        fuentes: [],
    };

    test('renders name, phone, address and a safe external link', () => {
        renderArticulo(articulo);
        expect(screen.getByText('SEMOVI')).toBeInTheDocument();
        expect(screen.getByText('55 5555 5555')).toBeInTheDocument();
        expect(screen.getByText('Calle Falsa 123')).toBeInTheDocument();
        const link = screen.getAllByRole('link', { name: /sitio oficial/i })[0];
        expect(link).toHaveAttribute('href', 'https://www.semovi.cdmx.gob.mx');
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    test('omits phone and address rows when the entry has none', () => {
        renderArticulo(articulo);
        expect(screen.getByText('Solo nombre y sitio')).toBeInTheDocument();
        expect(screen.getAllByText(/^Tel\./)).toHaveLength(1);
    });
});

describe('ArticuloContenido tipo prosa', () => {
    test('renders [texto](/ruta) in the body as a link to the other card', () => {
        renderArticulo({
            titulo: 'Prueba',
            actualizado: '2026-10',
            tipo: 'prosa',
            cuerpo: 'Consulta [Multas y fotocívicas](/guia/multas-y-fotocivicas).',
            fuentes: [],
        });
        expect(screen.getByRole('link', { name: 'Multas y fotocívicas' })).toHaveAttribute(
            'href',
            '/guia/multas-y-fotocivicas'
        );
    });
});
