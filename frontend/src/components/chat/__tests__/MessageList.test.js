import { render, screen } from '@testing-library/react';
import MessageList from '../MessageList';

const answer = (overrides = {}) => ({ key: 'm-2', id: 2, role: 'assistant', content: 'Respuesta', status: 'streaming', citations: [], feedback: null, ...overrides });

test('scrolls to the bottom again when the source chips appear, even if the text did not change', () => {
  const scrollTo = jest.fn();
  Element.prototype.scrollTo = scrollTo;
  const user = { key: 'm-1', id: 1, role: 'user', content: 'hola', status: 'complete', citations: [], feedback: null };
  const { rerender } = render(<MessageList messages={[user, answer()]} tool={null} onVote={jest.fn()} onSuggest={jest.fn()} />);
  const before = scrollTo.mock.calls.length;

  const citation = { n: 1, orden: 1, source_title: 'Reglamento', article: '44', fraction: null, page: 5, url: 'https://x/r.pdf#page=5' };
  rerender(<MessageList messages={[user, answer({ status: 'complete', citations: [citation] })]} tool={null} onVote={jest.fn()} onSuggest={jest.fn()} />);

  expect(scrollTo.mock.calls.length).toBeGreaterThan(before);
});

test('shows the loading state and the tool indicator', () => {
  const { rerender } = render(<MessageList messages={[]} tool={null} loading onVote={jest.fn()} onSuggest={jest.fn()} />);
  expect(screen.getByRole('status')).toHaveTextContent('Cargando conversación');
  rerender(<MessageList messages={[answer({ content: '' })]} tool={{ name: 'calcular_multa' }} onVote={jest.fn()} onSuggest={jest.fn()} />);
  expect(screen.getByText('Calculando el monto…')).toBeInTheDocument();
});
