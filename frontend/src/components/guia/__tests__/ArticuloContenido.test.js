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

const categoria = { numero: '15', etiqueta: 'GLOSARIO' };

const renderArticulo = (articulo) =>
    render(<ArticuloContenido categoria={categoria} articulo={articulo} />);

describe('ArticuloContenido tipo glosario', () => {
    const articulo = {
        titulo: 'Glosario',
        actualizado: '2026-10',
        tipo: 'glosario',
        glosario: [
            { termino: 'Boleta', definicion: 'Documento en donde se hace constar la infracción.' },
            { termino: 'Infracción', definicion: 'Conducta que transgrede una disposición.' },
        ],
        fuentes: [],
    };

    test('renders every term with its definition', () => {
        renderArticulo(articulo);
        expect(screen.getByText('Boleta')).toBeInTheDocument();
        expect(screen.getByText('Documento en donde se hace constar la infracción.')).toBeInTheDocument();
        expect(screen.getByText('Infracción')).toBeInTheDocument();
    });

    test('renders nothing extra when the glosario list is missing', () => {
        renderArticulo({ ...articulo, glosario: undefined });
        expect(screen.queryByText('Boleta')).not.toBeInTheDocument();
    });
});

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
