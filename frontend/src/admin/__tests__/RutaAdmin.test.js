import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import RutaAdmin from '../RutaAdmin';
import authService from '../../services/authService';

// react-router-dom v7 does not load under CRA's Jest.
jest.mock('react-router-dom', () => ({
    Navigate: ({ to, replace }) => (
        <div data-testid="navigate" data-to={to} data-replace={String(!!replace)} />
    ),
}));
jest.mock('../../services/authService', () => ({
    __esModule: true,
    default: { getCurrentUser: jest.fn() },
}));

const renderGuard = () =>
    render(
        <RutaAdmin>
            <p>Panel secreto</p>
        </RutaAdmin>
    );

beforeEach(() => jest.clearAllMocks());

describe('RutaAdmin', () => {
    test('sin sesión va a Login', () => {
        authService.getCurrentUser.mockReturnValue(null);
        renderGuard();
        expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/Login');
        expect(screen.getByTestId('navigate')).toHaveAttribute('data-replace', 'true');
        expect(screen.queryByText('Panel secreto')).not.toBeInTheDocument();
    });

    test('un usuario normal no ve el panel y va a Bienvenida', () => {
        authService.getCurrentUser.mockReturnValue({ id: 1, rol: 'user' });
        renderGuard();
        expect(screen.getByTestId('navigate')).toHaveAttribute('data-to', '/Bienvenida');
        expect(screen.queryByText('Panel secreto')).not.toBeInTheDocument();
    });

    test('un administrador ve el contenido', () => {
        authService.getCurrentUser.mockReturnValue({ id: 2, rol: 'admin' });
        renderGuard();
        expect(screen.getByText('Panel secreto')).toBeInTheDocument();
        expect(screen.queryByTestId('navigate')).not.toBeInTheDocument();
    });
});
