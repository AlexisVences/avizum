import React from 'react';
import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import Footer from '../Footer';

// react-router-dom v7 doesn't resolve under CRA's Jest; only Link is used here.
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
}));

describe('Footer', () => {
    test('is pushed to the bottom of a flex-column page (auto top margin) with the usual 4rem gap', () => {
        const { container } = render(<Footer />);
        const envoltura = container.firstChild;
        expect(envoltura.className).toMatch(/tw-mt-auto/);
        expect(envoltura.className).toMatch(/tw-pt-16/);
        expect(envoltura.querySelector('footer')).toBeInTheDocument();
    });

    test('className replaces the default gap but keeps the bottom-pinning margin', () => {
        const { container } = render(<Footer className="tw-pt-0" />);
        const envoltura = container.firstChild;
        expect(envoltura.className).toMatch(/tw-mt-auto/);
        expect(envoltura.className).toMatch(/tw-pt-0/);
        expect(envoltura.className).not.toMatch(/tw-pt-16/);
    });

    test('keeps its links', () => {
        const { getByRole } = render(<Footer />);
        expect(getByRole('link', { name: 'Acerca de' })).toHaveAttribute('href', '/Acerca-de');
        expect(getByRole('link', { name: 'Contacto' })).toHaveAttribute('href', '/Contacto');
        expect(getByRole('link', { name: 'Aviso Legal' })).toHaveAttribute('href', '/Aviso-legal');
    });
});
