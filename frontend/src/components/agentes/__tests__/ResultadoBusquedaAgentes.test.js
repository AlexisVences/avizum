import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import ResultadoBusquedaAgentes from '../ResultadoBusquedaAgentes';

jest.mock('react-router-dom', () => ({
    Link: ({ to, children, ...rest }) => <a href={to} {...rest}>{children}</a>,
}));

const fuente = { title: 'Acuerdo 30/2026 (GOCDMX 10-jun-2026)', url: 'https://gaceta.example/30-2026.pdf', last_reform_date: '2026-06-10' };

test('shows each authorization with its own label and the official source link', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '730249', matched_by: 'plate', source: fuente, results: [
        { plate: '730249', full_name: 'ZENIL OJEDA RICARDO', authorization_type: 'via_publica', corporation: null, alcaldias: null },
        { plate: '730249', full_name: 'ZENIL OJEDA RICARDO', authorization_type: 'sistemas_tecnologicos', corporation: null, alcaldias: null },
    ] }} />);
    expect(screen.getByText('Vía pública')).toBeInTheDocument();
    expect(screen.getByText('Fotocívicas')).toBeInTheDocument();
    expect(screen.getByText(/infraccionar en la vía pública/i)).toBeInTheDocument();
    expect(screen.getByText(/sistemas tecnológicos/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: fuente.title });
    expect(link).toHaveAttribute('href', fuente.url);
    expect(link).toHaveAttribute('target', '_blank');
});

test('shows corporation and alcaldías only when the official list provides them', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: 'x', matched_by: 'name', source: fuente, results: [
        { plate: '1', full_name: 'PEREZ LOPEZ ANA', authorization_type: 'via_publica', corporation: 'Policía Auxiliar', alcaldias: ['Cuauhtémoc', 'Iztapalapa'] },
    ] }} />);
    expect(screen.getByText(/Policía Auxiliar/)).toBeInTheDocument();
    expect(screen.getByText(/Cuauhtémoc, Iztapalapa/)).toBeInTheDocument();
});

test('not found: says "no aparece en la lista vigente" with guidance, never calls the officer fake', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '999999', matched_by: 'plate', source: fuente, results: [] }} />);
    expect(screen.getByText(/no aparece en la lista vigente/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /asuntos internos/i })).toHaveAttribute('href', 'https://www.ssc.cdmx.gob.mx/organizacion-policial/direcciones-generales/direccion-general-de-asuntos-internos');
    expect(screen.getByRole('link', { name: /multas y fotocívicas/i })).toHaveAttribute('href', '/guia/multas-y-fotocivicas');
    expect(screen.getByRole('link', { name: fuente.title })).toBeInTheDocument();
    expect(screen.queryByText(/falso/i)).not.toBeInTheDocument();
});

test('registry unavailable: never claims the officer is missing from the list', () => {
    render(<ResultadoBusquedaAgentes resultado={{ query: '1', matched_by: 'plate', source: null, results: [] }} />);
    expect(screen.getByText(/registro oficial de agentes no está disponible/i)).toBeInTheDocument();
    expect(screen.queryByText(/no aparece/i)).not.toBeInTheDocument();
});
