import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import HeroBienvenida from '../HeroBienvenida';

jest.mock('framer-motion', () => require('../testMocks').framerMock);

describe('HeroBienvenida', () => {
    test('greets the user by name', () => {
        render(<HeroBienvenida nombre="Alex" />);
        expect(screen.getByText('Hola, Alex.')).toBeInTheDocument();
    });

    test('keeps the original headline and lead text', () => {
        render(<HeroBienvenida nombre="Alex" />);
        expect(screen.getByRole('heading', { level: 1, name: /Bienvenido a Amicuz/ })).toBeInTheDocument();
        expect(
            screen.getByText('Tu plataforma de confianza para resolver cualquier situación legal de tránsito.')
        ).toBeInTheDocument();
    });

    test.each([undefined, null, '', '   '])('omits the greeting when the name is %p', (nombre) => {
        render(<HeroBienvenida nombre={nombre} />);
        expect(screen.queryByText(/^Hola,/)).not.toBeInTheDocument();
        expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    test('renders the decorative logo background hidden from assistive tech', () => {
        const { container } = render(<HeroBienvenida nombre="Alex" />);
        const fondo = container.querySelector('img[aria-hidden="true"]');
        expect(fondo).toBeInTheDocument();
        expect(fondo).toHaveAttribute('alt', '');
    });
});
