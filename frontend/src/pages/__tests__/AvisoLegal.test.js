import { render, screen } from '@testing-library/react';
import AvisoLegal from '../AvisoLegal';

// react-router-dom v7 doesn't resolve under CRA's Jest; the layout pieces are not what is tested here.
jest.mock('../../components/Navbar', () => () => <nav />);
jest.mock('../../components/Footer', () => () => <footer />);

test('la sección «Protección de datos personales» avisa de la revisión de respuestas', () => {
  render(<AvisoLegal />);
  const section = screen.getByRole('heading', { name: 'Protección de datos personales' }).closest('section');
  expect(section).toHaveTextContent(
    'Las respuestas que reciban una calificación negativa o terminen en error pueden ser revisadas por el equipo de Avizum, sin nombre ni correo, para mejorar el servicio'
  );
});
