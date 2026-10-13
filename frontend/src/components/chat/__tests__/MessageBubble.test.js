import { fireEvent, render, screen } from '@testing-library/react';
import MessageBubble from '../MessageBubble';

const citation = { n: 3, orden: 1, source_title: 'Reglamento de Tránsito', article: '44', fraction: 'I', page: 56, url: 'https://x.mx/r.pdf#page=56' };
const answer = (overrides = {}) => ({ key: 'm-9', id: 9, role: 'assistant', content: 'Debe portarla [3].', status: 'complete', citations: [citation], feedback: null, ...overrides });

test('a finished answer shows the source chip that opens the PDF at the page', () => {
  render(<MessageBubble message={answer()} onVote={jest.fn()} />);
  const chip = screen.getByRole('link', { name: /Reglamento de Tránsito · art\. 44, fr\. I · pág\. 56/ });
  expect(chip).toHaveAttribute('href', 'https://x.mx/r.pdf#page=56');
});

test('votes call back with the message id and mark the chosen thumb', () => {
  const onVote = jest.fn();
  const { rerender } = render(<MessageBubble message={answer()} onVote={onVote} />);
  fireEvent.click(screen.getByRole('button', { name: 'Respuesta útil' }));
  expect(onVote).toHaveBeenCalledWith(9, 1);

  rerender(<MessageBubble message={answer({ feedback: -1 })} onVote={onVote} />);
  expect(screen.getByRole('button', { name: 'Respuesta no útil' })).toHaveAttribute('aria-pressed', 'true');
});

test('while streaming: no votes, no raw markers and no chips yet', () => {
  render(<MessageBubble message={answer({ id: null, status: 'streaming', content: 'Debe portarla [3] y' })} onVote={jest.fn()} />);
  expect(screen.queryByRole('button', { name: 'Respuesta útil' })).toBeNull();
  expect(screen.queryByText(/\[3\]/)).toBeNull();
  expect(screen.queryByRole('list', { name: 'Fuentes consultadas' })).toBeNull();
});

test('an empty answer that is still streaming shows an ellipsis', () => {
  render(<MessageBubble message={answer({ id: null, status: 'streaming', content: '', citations: [] })} />);
  expect(screen.getByLabelText('Escribiendo')).toBeInTheDocument();
});

test('a failed answer is shown as an error without votes', () => {
  render(<MessageBubble message={answer({ status: 'error', content: 'No pude generar la respuesta.' })} onVote={jest.fn()} />);
  expect(screen.getByText('No pude generar la respuesta.')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Respuesta útil' })).toBeNull();
});

test('the user question is plain text, never interpreted as Markdown or HTML', () => {
  render(<MessageBubble message={{ key: 'm-1', id: 1, role: 'user', content: '**no negrita** <b>no html</b>', status: 'complete', citations: [] }} />);
  expect(screen.getByText('**no negrita** <b>no html</b>')).toBeInTheDocument();
});
