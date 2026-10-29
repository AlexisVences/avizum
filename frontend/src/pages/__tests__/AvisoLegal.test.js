import { render, screen } from '@testing-library/react';
import AvisoLegal from '../AvisoLegal';

// react-router-dom v7 doesn't resolve under CRA's Jest; the layout pieces are not what is tested here.
jest.mock('../../components/Navbar', () => () => <nav />);
jest.mock('../../components/Footer', () => () => <footer />);

test('muestra el título, el banner de borrador y las secciones clave', () => {
  render(<AvisoLegal />);
  expect(screen.getByRole('heading', { level: 1, name: 'Aviso de privacidad' })).toBeInTheDocument();
  expect(screen.getByRole('note')).toHaveTextContent('Borrador pendiente de revisión por un abogado');
  [
    'Responsable del tratamiento',
    'Datos personales que recabamos',
    'Terceros, transferencias y remisiones',
    'Conservación',
    'Derechos ARCO y revocación del consentimiento',
    'Cookies y almacenamiento local',
  ].forEach((name) => expect(screen.getByRole('heading', { name })).toBeInTheDocument());
  expect(screen.getByText(/OpenAI procesa el texto/)).toBeInTheDocument();
});

test('conserva el aviso de revisión de respuestas sin fuente', () => {
  render(<AvisoLegal />);
  const section = screen.getByRole('heading', { name: 'Revisión de respuestas' }).closest('section');
  expect(section).toHaveTextContent(
    'Las respuestas que reciban una calificación negativa, terminen en error o no citen ninguna fuente pueden ser revisadas por el equipo de Avizum, sin nombre ni correo, para mejorar el servicio'
  );
});
