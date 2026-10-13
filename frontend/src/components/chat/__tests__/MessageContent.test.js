import { render, screen } from '@testing-library/react';
import MessageContent, { withCitationLinks } from '../MessageContent';

const citations = [
  { n: 23, orden: 1, source_title: 'Reglamento de Tránsito', article: '44', fraction: 'I', page: 56, url: 'https://x.mx/r.pdf#page=56' },
  { n: 7, orden: 2, source_title: 'Código Fiscal', article: '230', fraction: null, page: 172, url: 'https://x.mx/cf.pdf#page=172' },
];

describe('withCitationLinks', () => {
  test('turns each known marker into a link labelled with its order of use', () => {
    expect(withCitationLinks('Debe portarla [23] y pagar [7].', citations, false)).toBe('Debe portarla [1](#cita-23) y pagar [2](#cita-7).');
  });

  test('a marker that is only half written while streaming is not shown either', () => {
    expect(withCitationLinks('La ley dice [', citations, true)).toBe('La ley dice');
    expect(withCitationLinks('La ley dice [2', citations, true)).toBe('La ley dice');
    expect(withCitationLinks('La ley dice [23]', citations, true)).toBe('La ley dice');
    expect(withCitationLinks('Ya terminó [23]', citations, false)).toBe('Ya terminó [1](#cita-23)');
  });

  test('hides markers while the answer is still arriving and drops unknown ones', () => {
    expect(withCitationLinks('Texto [23] y [99].', citations, true)).toBe('Texto y.');
    expect(withCitationLinks('Texto [23] y [99].', citations, false)).toBe('Texto [1](#cita-23) y.');
  });
});

describe('MessageContent', () => {
  test('renders Markdown and links a citation to the official PDF page in a new tab', () => {
    render(<MessageContent content={'**Sí**, debe portarla [23].\n\n- primero\n- segundo'} citations={citations} />);
    expect(screen.getByText('Sí').tagName).toBe('STRONG');
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    const link = screen.getByRole('link', { name: /Fuente 1: Reglamento de Tránsito, art\. 44 fr\. I/ });
    expect(link).toHaveAttribute('href', 'https://x.mx/r.pdf#page=56');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });

  test('raw HTML and scripts from the model never reach the page', () => {
    const { container } = render(<MessageContent content={'Hola <script>alert(1)</script><img src=x onerror=alert(1)> [x](javascript:alert(1))'} />);
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('a[href^="javascript"]')).toBeNull();
  });

  test('an ordinary link opens in a new tab without leaking the opener', () => {
    render(<MessageContent content="Consulta [la SSC](https://www.ssc.cdmx.gob.mx)." />);
    const link = screen.getByRole('link', { name: 'la SSC' });
    expect(link).toHaveAttribute('target', '_blank');
    expect(link.getAttribute('rel')).toContain('noreferrer');
  });
});
