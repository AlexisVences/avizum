import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import HeroBienvenida from '../HeroBienvenida';

jest.mock('framer-motion', () => require('../testMocks').framerMock);

describe('HeroBienvenida', () => {
    test('the headline is "Hola, nombre." in bold, then the question in magenta on the next line', () => {
        render(<HeroBienvenida nombre="Alex" />);
        const h1 = screen.getByRole('heading', { level: 1 });
        const saludo = screen.getByText('Hola, Alex.');
        const pregunta = screen.getByText('¿Cómo podemos ayudarte?');

        expect(h1).toContainElement(saludo);
        expect(h1).toContainElement(pregunta);
        expect(saludo.className).toMatch(/tw-font-bold/);
        expect(saludo.className).toMatch(/tw-block/);
        expect(pregunta.className).toMatch(/tw-text-magenta/);
        expect(pregunta.className).toMatch(/tw-block/);
        // greeting comes first in document order
        expect(saludo.compareDocumentPosition(pregunta) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    test('keeps the lead text and the subtitle, with the question only once', () => {
        render(<HeroBienvenida nombre="Alex" />);
        expect(
            screen.getByText('Bienvenido a Amicuz, tu plataforma de confianza para consultas legales de tránsito y tu vehículo en la Ciudad de México.')
        ).toBeInTheDocument();
        expect(screen.getByText('Elige la opción que mejor se acomode a tus necesidades')).toBeInTheDocument();
        expect(screen.getAllByText('¿Cómo podemos ayudarte?')).toHaveLength(1);
    });

    test.each([undefined, null, '', '   '])('falls back to the original welcome when the name is %p', (nombre) => {
        render(<HeroBienvenida nombre={nombre} />);
        expect(screen.queryByText(/^Hola,/)).not.toBeInTheDocument();
        expect(screen.getByText('Bienvenido a Amicuz')).toBeInTheDocument();
        expect(screen.getByText('¿Cómo podemos ayudarte?')).toBeInTheDocument();
    });

    test('renders the decorative logo background hidden from assistive tech', () => {
        const { container } = render(<HeroBienvenida nombre="Alex" />);
        const fondo = container.querySelector('img[aria-hidden="true"]');
        expect(fondo).toBeInTheDocument();
        expect(fondo).toHaveAttribute('alt', '');
    });
});
