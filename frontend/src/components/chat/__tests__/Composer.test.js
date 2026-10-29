import { fireEvent, render, screen } from '@testing-library/react';
import Composer from '../Composer';

const box = () => screen.getByLabelText('Tu pregunta');

test('Enter sends the trimmed text and clears the box; Shift+Enter only adds a line', () => {
  const onSend = jest.fn();
  render(<Composer onSend={onSend} canSend />);
  fireEvent.change(box(), { target: { value: '  ¿placas?  ' } });

  fireEvent.keyDown(box(), { key: 'Enter', shiftKey: true });
  expect(onSend).not.toHaveBeenCalled();

  fireEvent.keyDown(box(), { key: 'Enter' });
  expect(onSend).toHaveBeenCalledWith('¿placas?');
  expect(box()).toHaveValue('');
});

test('while an answer is generating the button is disabled and Enter does nothing, but typing still works', () => {
  const onSend = jest.fn();
  render(<Composer onSend={onSend} canSend={false} />);
  fireEvent.change(box(), { target: { value: 'siguiente pregunta' } });

  expect(screen.getByRole('button', { name: 'Enviar pregunta' })).toBeDisabled();
  fireEvent.keyDown(box(), { key: 'Enter' });
  expect(onSend).not.toHaveBeenCalled();
  expect(box()).toHaveValue('siguiente pregunta');
});

test('an empty message cannot be sent', () => {
  render(<Composer onSend={jest.fn()} canSend />);
  fireEvent.change(box(), { target: { value: '   ' } });
  expect(screen.getByRole('button', { name: 'Enviar pregunta' })).toBeDisabled();
});

test('shows the counter and blocks a message over the limit', () => {
  render(<Composer onSend={jest.fn()} canSend maxChars={10} />);
  fireEvent.change(box(), { target: { value: 'x'.repeat(11) } });
  expect(screen.getByText('11/10')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Enviar pregunta' })).toBeDisabled();
});

test('a refused message comes back into the box', () => {
  const { rerender } = render(<Composer onSend={jest.fn()} canSend draft="" />);
  rerender(<Composer onSend={jest.fn()} canSend draft="la pregunta que no se envió" />);
  expect(box()).toHaveValue('la pregunta que no se envió');
});

test.each(['dock', 'hero'])('the legal disclaimer is rendered exactly once in the %s variant', (variant) => {
  render(<Composer onSend={jest.fn()} canSend variant={variant} />);
  expect(screen.getAllByText(/no sustituye a un abogado/)).toHaveLength(1);
  expect(screen.getByTestId('chat-disclaimer')).toHaveTextContent(
    'Avizum ofrece información general sobre el reglamento de tránsito y no sustituye a un abogado. Verifica siempre con la fuente oficial citada.'
  );
});
