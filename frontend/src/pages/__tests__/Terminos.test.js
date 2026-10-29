import { render, screen } from '@testing-library/react';
import Terminos from '../Terminos';

jest.mock('../../components/Navbar', () => () => <nav />);
jest.mock('../../components/Footer', () => () => <footer />);

test('muestra el título, el banner de borrador con la versión y las secciones clave', () => {
  render(<Terminos />);
  expect(screen.getByRole('heading', { level: 1, name: 'Términos de uso' })).toBeInTheDocument();
  const banner = screen.getByRole('note');
  expect(banner).toHaveTextContent('Borrador pendiente de revisión por un abogado');
  expect(banner).toHaveTextContent('2026-10-29-borrador');
  ['Qué es Avizum', 'Uso prohibido', 'Limitación de responsabilidad', 'Ley aplicable y jurisdicción'].forEach((name) =>
    expect(screen.getByRole('heading', { name })).toBeInTheDocument()
  );
  expect(screen.getByRole('link', { name: 'página de contacto' })).toHaveAttribute('href', '/Contacto');
});
