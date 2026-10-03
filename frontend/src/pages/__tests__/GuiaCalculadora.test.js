import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import GuiaCalculadora from '../GuiaCalculadora';

// react-router-dom v7 doesn't resolve under CRA's Jest.
jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
    useParams: () => ({ herramientaSlug: 'uma-a-pesos' }),
    useNavigate: () => jest.fn(),
}));
jest.mock('../../components/NavBar2', () => () => null);
jest.mock('../../components/Footer', () => () => null);
jest.mock('../../components/guia/UmaCalculadora', () => () => <div>calculadora</div>);
jest.mock('../../components/guia/VerificacionCalculadora', () => () => null);
jest.mock('../../services/guiaService', () => ({
    getHerramientaPorSlug: () => ({ slug: 'uma-a-pesos', titulo: 'UMA → pesos', descripcion: 'Convierte.' }),
    getCategoriaPorSlug: (slug) => (slug === 'calculadoras' ? { numero: '42', etiqueta: 'CÁLCULO' } : null),
}));

describe('GuiaCalculadora', () => {
    test("the eyebrow shows the 'calculadoras' category's real number, not a hard-coded one", () => {
        render(<GuiaCalculadora />);
        expect(screen.getByText('42 · CÁLCULO')).toBeInTheDocument();
        expect(screen.queryByText(/^17 ·/)).not.toBeInTheDocument();
    });
});
