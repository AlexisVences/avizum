import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import TypingDots from '../TypingDots';

test('it announces that the answer is being written, once, for assistive tech', () => {
  render(<TypingDots />);
  expect(screen.getByRole('status', { name: 'Escribiendo' })).toBeInTheDocument();
});

test('three dots move one after the other, and hold still when the person asks for less motion', () => {
  const { container } = render(<TypingDots />);
  const dots = container.querySelectorAll('[data-dot]');
  expect(dots).toHaveLength(3);
  dots.forEach((dot) => {
    expect(dot).toHaveClass('tw-animate-dot-bounce');
    expect(dot.className).toMatch(/motion-reduce:tw-animate-none/);
  });
  expect([...dots].map((dot) => dot.style.animationDelay)).toEqual(['0ms', '150ms', '300ms']);
});
