import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import ProsaConEnlaces from '../ProsaConEnlaces';

// react-router-dom v7 doesn't resolve under CRA's Jest; only Link is used here.
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
}));

describe('ProsaConEnlaces', () => {
    test('renders plain text unchanged', () => {
        render(<ProsaConEnlaces texto={'Línea uno\nLínea dos'} />);
        expect(screen.getByText(/Línea uno/)).toBeInTheDocument();
        expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });

    test('turns an internal [texto](/ruta) into a router link', () => {
        render(<ProsaConEnlaces texto="Ver [Multas y fotocívicas](/guia/multas-y-fotocivicas) para más." />);
        const link = screen.getByRole('link', { name: 'Multas y fotocívicas' });
        expect(link).toHaveAttribute('href', '/guia/multas-y-fotocivicas');
        expect(link).not.toHaveAttribute('target');
    });

    test('opens external links in a new tab safely', () => {
        render(<ProsaConEnlaces texto="Portal: [SEMOVI](https://www.semovi.cdmx.gob.mx)." />);
        const link = screen.getByRole('link', { name: 'SEMOVI' });
        expect(link).toHaveAttribute('href', 'https://www.semovi.cdmx.gob.mx');
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    test('keeps the surrounding text and handles several links', () => {
        const { container } = render(
            <ProsaConEnlaces texto="A [uno](/guia/a) y [dos](/guia/b) fin" />
        );
        expect(screen.getAllByRole('link')).toHaveLength(2);
        expect(container.textContent).toBe('A uno y dos fin');
    });

    test('does not link a javascript: destination', () => {
        render(<ProsaConEnlaces texto="[x](javascript:alert(1))" />);
        expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });
});
