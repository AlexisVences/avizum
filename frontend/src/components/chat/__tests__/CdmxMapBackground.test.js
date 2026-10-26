import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import CdmxMapBackground from '../CdmxMapBackground';

test('it is decorative: hidden from assistive tech and never captures the pointer', () => {
  const { container } = render(<CdmxMapBackground />);
  const wrapper = container.firstChild;
  expect(wrapper).toHaveAttribute('aria-hidden', 'true');
  expect(wrapper).toHaveClass('tw-pointer-events-none');
});

test('it draws the 16 alcaldías and names the ones around the map', () => {
  const { container } = render(<CdmxMapBackground />);
  expect(container.querySelectorAll('path[data-alcaldia]')).toHaveLength(16);
  const names = [...container.querySelectorAll('text')].map((node) => node.textContent);
  expect(names).toEqual(expect.arrayContaining(['GUSTAVO A. MADERO', 'IZTAPALAPA', 'TLALPAN', 'COYOACÁN', 'ÁLVARO OBREGÓN']));
  expect(screen.getByText('CDMX')).toBeInTheDocument(); // pinned to the corner, not drawn in the map
});

test('the map is cropped to cover the screen rather than squeezed, so it never distorts', () => {
  const { container } = render(<CdmxMapBackground />);
  expect(container.querySelector('svg')).toHaveAttribute('preserveAspectRatio', 'xMidYMid slice');
});

test('the names of the alcaldías can be turned off so they never sit under an answer, keeping the map and the corner marks', () => {
  const { container } = render(<CdmxMapBackground names={false} />);
  expect([...container.querySelectorAll('svg text')]).toHaveLength(0);
  expect(container.querySelectorAll('path[data-alcaldia]')).toHaveLength(16);
  expect(screen.getByText('CDMX')).toBeInTheDocument();
});

test('the soft brand glow (blue in the middle, magenta along the bottom) is drawn behind the map only when asked', () => {
  const { container, rerender } = render(<CdmxMapBackground />);
  expect(container.querySelector('.asesoria-glow')).toBeNull();
  rerender(<CdmxMapBackground glow />);
  expect(container.querySelector('.asesoria-glow')).toBeInTheDocument();
});
