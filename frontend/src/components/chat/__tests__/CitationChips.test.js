import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import CitationChips from '../CitationChips';

const law = {
  n: 1, orden: 1, source_title: 'Reglamento de Tránsito', article: '45', fraction: 'IV', page: 59,
  url: 'https://x.mx/r.pdf#page=59',
};
const ficha = {
  n: 2, orden: 2, source_title: 'SEMOVI CDMX — Cambio de propietario (ficha oficial)', article: 'Requisitos', fraction: null, page: null,
  url: 'https://www.semovi.cdmx.gob.mx/cambio',
};

test('a law citation names the article, fraction and page of the PDF', () => {
  render(<CitationChips citations={[law]} />);
  expect(screen.getByText('Reglamento de Tránsito · art. 45, fr. IV · pág. 59')).toBeInTheDocument();
});

test('a ficha citation names its section, not an article, and has no page', () => {
  render(<CitationChips citations={[ficha]} />);
  expect(screen.getByText('SEMOVI CDMX — Cambio de propietario (ficha oficial) · Requisitos')).toBeInTheDocument();
  expect(screen.getByRole('link')).toHaveAttribute('href', 'https://www.semovi.cdmx.gob.mx/cambio');
});

test('a whole source without an article still reads as the complete document', () => {
  render(<CitationChips citations={[{ ...law, article: '', fraction: null, page: null }]} />);
  expect(screen.getByText('Reglamento de Tránsito · documento completo')).toBeInTheDocument();
});

test('a citation whose URL is not http(s) is shown as text, not as a link', () => {
  render(<CitationChips citations={[{ ...law, url: 'javascript:alert(1)' }]} />);
  expect(screen.queryByRole('link')).toBeNull();
  expect(screen.getByText('Reglamento de Tránsito · art. 45, fr. IV · pág. 59')).toBeInTheDocument();
});
