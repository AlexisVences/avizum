import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminLayout from '../AdminLayout';

// react-router-dom v7 does not load under CRA's Jest.
const mockNavigate = jest.fn();
let mockPath = '/admin';
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
    Outlet: () => <p>Contenido de la página</p>,
    useLocation: () => ({ pathname: mockPath }),
    useNavigate: () => mockNavigate,
}));

const renderLayout = (path = '/admin') => {
    mockPath = path;
    return render(<AdminLayout />);
};

beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('token', 'abc');
    localStorage.setItem('user', JSON.stringify({ id: 1, nombre: 'Ana', apellido: 'Pérez', rol: 'admin' }));
});

describe('AdminLayout', () => {
    test('muestra los cinco enlaces y marca el de la ruta actual', () => {
        renderLayout('/admin/calidad');
        const nav = screen.getByRole('navigation', { name: 'Administración' });
        const links = within(nav).getAllByRole('link');
        expect(links.map((l) => [l.textContent, l.getAttribute('href')])).toEqual([
            ['Resumen', '/admin'],
            ['Calidad', '/admin/calidad'],
            ['Usuarios', '/admin/usuarios'],
            ['Fuentes', '/admin/fuentes'],
            ['Actividad', '/admin/actividad'],
        ]);
        expect(within(nav).getByRole('link', { name: 'Calidad' })).toHaveAttribute('aria-current', 'page');
        expect(within(nav).getByRole('link', { name: 'Resumen' })).not.toHaveAttribute('aria-current');
        expect(screen.getByText('Contenido de la página')).toBeInTheDocument();
    });

    test('Resumen solo está activo en /admin exacto', () => {
        renderLayout('/admin/usuarios');
        expect(screen.getByRole('link', { name: 'Resumen' })).not.toHaveAttribute('aria-current');
        expect(screen.getByRole('link', { name: 'Usuarios' })).toHaveAttribute('aria-current', 'page');
    });

    test('Cerrar sesión borra token y usuario de localStorage', () => {
        renderLayout();
        userEvent.click(screen.getByRole('button', { name: 'Cerrar sesión' }));
        expect(localStorage.getItem('token')).toBeNull();
        expect(localStorage.getItem('user')).toBeNull();
        expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    test('el círculo del perfil es magenta y muestra la inicial', () => {
        renderLayout();
        const initial = screen.getByText('A', { selector: 'span' });
        expect(initial).toHaveClass('tw-bg-magenta');
        expect(screen.getByText('Ana Pérez')).toBeInTheDocument();
    });

    test('en móvil el menú se abre con el botón', () => {
        renderLayout();
        const aside = screen.getByTestId('admin-sidebar');
        expect(aside).toHaveClass('-tw-translate-x-full');
        const button = screen.getByRole('button', { name: 'Abrir menú' });
        expect(button).toHaveAttribute('aria-expanded', 'false');
        userEvent.click(button);
        expect(aside).toHaveClass('tw-translate-x-0');
        expect(screen.getByRole('button', { name: 'Abrir menú' })).toHaveAttribute('aria-expanded', 'true');
        userEvent.click(screen.getByRole('button', { name: 'Cerrar menú' }));
        expect(aside).toHaveClass('-tw-translate-x-full');
    });
});
