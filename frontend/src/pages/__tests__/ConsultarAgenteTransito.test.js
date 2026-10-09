import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConsultarAgenteTransito from '../ConsultarAgenteTransito';
import { buscarAgentes } from '../../services/agentesService';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
    useSearchParams: () => [new URLSearchParams('')],
}));
jest.mock('../../components/NavBar2', () => () => null);
jest.mock('../../components/Footer', () => () => null);
jest.mock('../../services/agentesService', () => ({ buscarAgentes: jest.fn() }));

beforeEach(() => jest.clearAllMocks());

test('searches by name and renders results', async () => {
    buscarAgentes.mockResolvedValue({ query: 'karla zavala', matched_by: 'name', source: { title: 'Acuerdo 30/2026', url: 'https://g.example/a.pdf', last_reform_date: '2026-06-10' }, results: [
        { plate: '1168287', full_name: 'ZAVALA TOVAR KARLA PAOLA', authorization_type: 'via_publica', corporation: null, alcaldias: null },
    ] });
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: 'karla zavala' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(screen.getByText('ZAVALA TOVAR KARLA PAOLA')).toBeInTheDocument());
    expect(buscarAgentes).toHaveBeenCalledWith('karla zavala');
});

test('asks for at least two characters without calling the API', () => {
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: 'a' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    expect(screen.getByText(/escribe una placa o al menos dos letras/i)).toBeInTheDocument();
    expect(buscarAgentes).not.toHaveBeenCalled();
});

test('shows the service error message', async () => {
    buscarAgentes.mockRejectedValue(new Error('No pudimos consultar el registro de agentes. Intenta de nuevo.'));
    render(<ConsultarAgenteTransito />);
    fireEvent.change(screen.getByLabelText('Placa o nombre del agente'), { target: { value: '1168287' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await waitFor(() => expect(screen.getByText(/no pudimos consultar el registro/i)).toBeInTheDocument());
});
