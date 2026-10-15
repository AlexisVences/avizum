import { fireEvent, render, screen } from '@testing-library/react';
import ConversationSidebar from '../ConversationSidebar';

const conversations = [{ id: 1, title: 'Placas en banqueta' }, { id: 2, title: null }];

const setup = (overrides = {}) => {
  const handlers = { onSelect: jest.fn(), onNew: jest.fn(), onRename: jest.fn(), onDelete: jest.fn(), onClose: jest.fn() };
  render(<ConversationSidebar conversations={conversations} activeId={1} busy={false} open={false} {...handlers} {...overrides} />);
  return handlers;
};

test('lists conversations, marks the open one and names untitled ones', () => {
  setup();
  expect(screen.getByRole('button', { name: 'Placas en banqueta' })).toHaveAttribute('aria-current', 'true');
  expect(screen.getByRole('button', { name: 'Conversación sin título' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Nueva consulta' })).toBeInTheDocument(); // the action, not a row
});

test('selecting a conversation and starting a new one', () => {
  const h = setup();
  fireEvent.click(screen.getByRole('button', { name: 'Placas en banqueta' }));
  expect(h.onSelect).toHaveBeenCalledWith(1);
  fireEvent.click(screen.getByRole('button', { name: 'Nueva consulta' }));
  expect(h.onNew).toHaveBeenCalled();
});

test('renaming saves on Enter and ignores an empty name', () => {
  const h = setup();
  fireEvent.click(screen.getByRole('button', { name: 'Renombrar Placas en banqueta' }));
  const input = screen.getByLabelText('Nombre de la conversación');
  fireEvent.change(input, { target: { value: '  Multa por celular  ' } });
  fireEvent.keyDown(input, { key: 'Enter' });
  expect(h.onRename).toHaveBeenCalledWith(1, 'Multa por celular');

  fireEvent.click(screen.getByRole('button', { name: 'Renombrar Placas en banqueta' }));
  const again = screen.getByLabelText('Nombre de la conversación');
  fireEvent.change(again, { target: { value: '   ' } });
  fireEvent.keyDown(again, { key: 'Enter' });
  expect(h.onRename).toHaveBeenCalledTimes(1);
});

test('deleting asks for confirmation first and can be cancelled', () => {
  const h = setup();
  fireEvent.click(screen.getByRole('button', { name: 'Eliminar Placas en banqueta' }));
  expect(h.onDelete).not.toHaveBeenCalled();
  expect(screen.getByText('¿Eliminar esta conversación?')).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
  expect(h.onDelete).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole('button', { name: 'Eliminar Placas en banqueta' }));
  fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
  expect(h.onDelete).toHaveBeenCalledWith(1);
});

test('while an answer is generating the list cannot be switched', () => {
  setup({ busy: true });
  expect(screen.getByRole('button', { name: 'Placas en banqueta' })).toBeDisabled();
});
