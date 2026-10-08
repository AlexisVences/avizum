import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import AccionCard from '../AccionCard';

jest.mock('react-router-dom', () => require('../testMocks').routerMock);
jest.mock('framer-motion', () => require('../testMocks').framerMock);

describe('AccionCard', () => {
    test('with "to" renders a single link containing folio, title and CTA', () => {
        render(<AccionCard folio="01 · ASESORÍA" titulo="Asesoría legal gratuita" to="/asesoria-ia" cta="Entrar" />);
        const link = screen.getByRole('link', { name: /Asesoría legal gratuita/ });
        expect(link).toHaveAttribute('href', '/asesoria-ia');
        expect(link).toHaveTextContent('01 · ASESORÍA');
        expect(link).toHaveTextContent('Entrar');
    });

    test('with "onClick" renders a button that fires the handler', () => {
        const onClick = jest.fn();
        render(
            <AccionCard folio="02 · RECURSOS" titulo="Guía del conductor" descripcion="Leyes, trámites." onClick={onClick} cta="Explorar" />
        );
        fireEvent.click(screen.getByRole('button', { name: /Guía del conductor/ }));
        expect(onClick).toHaveBeenCalledTimes(1);
        expect(screen.getByText('Leyes, trámites.')).toBeInTheDocument();
    });

    test('omits the description when none is given', () => {
        const { container } = render(<AccionCard folio="03 · AGENTES" titulo="Agentes" to="/x" cta="Verificar" />);
        expect(container.querySelector('p')).toBeNull();
    });
});
