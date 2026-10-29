import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import AsesoriaIA from '../AsesoriaIA';
import * as chat from '../../services/chatService';

// react-router-dom v7 doesn't resolve under CRA's Jest; the page only reads the location.
jest.mock('react-router-dom', () => ({ useLocation: () => ({ pathname: '/asesoria-ia' }) }));
jest.mock('../../components/NavBar2', () => () => <nav data-testid="site-nav" />);
jest.mock('../../services/chatService', () => ({
  ...jest.requireActual('../../services/chatService'),
  listConversations: jest.fn(),
  createConversation: jest.fn(),
  renameConversation: jest.fn(),
  deleteConversation: jest.fn(),
  listMessages: jest.fn(),
  setFeedback: jest.fn(),
  clearFeedback: jest.fn(),
  streamMessage: jest.fn(),
}));
const { ChatError } = jest.requireActual('../../services/chatService');

const citation = { n: 1, orden: 1, source_slug: 'reglamento-transito', source_title: 'Reglamento de Tránsito', article: '44', fraction: 'I', page: 56, url: 'https://x.mx/r.pdf#page=56' };

const renderPage = () => render(<AsesoriaIA />);

beforeEach(() => {
  jest.resetAllMocks();
  window.scrollTo = jest.fn();
  chat.listConversations.mockResolvedValue([]);
  chat.listMessages.mockResolvedValue([]);
  chat.createConversation.mockResolvedValue({ id: 3, title: null, created_at: 'x', updated_at: 'x' });
});

test('starts with a welcome and suggestions; picking one asks it', async () => {
  chat.streamMessage.mockResolvedValue();
  renderPage();
  expect(await screen.findByRole('heading', { name: /¿En qué te\s*ayudo\s*\?/ })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /inmovilizador/ }));
  await waitFor(() => expect(chat.streamMessage).toHaveBeenCalled());
  expect(chat.streamMessage.mock.calls[0][0].content).toMatch(/inmovilizador/);
});

test('a question is answered live: tool indicator, text, citation chip and votes', async () => {
  let finish;
  chat.streamMessage.mockImplementation(({ onEvent }) => new Promise((resolve) => {
    onEvent('message_start', { user_message_id: 10 });
    onEvent('tool_start', { name: 'buscar_legislacion', args: {} });
    finish = () => {
      onEvent('tool_end', { name: 'buscar_legislacion', ok: true });
      onEvent('token', { text: 'Sí, debe portarla [1].' });
      onEvent('citations', [citation]);
      onEvent('done', { assistant_message_id: 11, text: 'Sí, debe portarla [1].', usage: {} });
      resolve();
    };
  }));
  renderPage();
  await screen.findByRole('heading', { name: /¿En qué te\s*ayudo\s*\?/ });

  fireEvent.change(screen.getByLabelText('Tu pregunta'), { target: { value: '¿Debo portar licencia?' } });
  fireEvent.keyDown(screen.getByLabelText('Tu pregunta'), { key: 'Enter' });

  expect(await screen.findByText('Buscando en la legislación…')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Enviar pregunta' })).toBeDisabled();

  act(() => { finish(); }); // the stream's dispatches must happen inside act
  expect(await screen.findByText(/Sí, debe portarla/)).toBeInTheDocument();
  expect(screen.queryByText('Buscando en la legislación…')).toBeNull();
  const chip = screen.getByRole('link', { name: /art\. 44, fr\. I · pág\. 56/ });
  expect(chip).toHaveAttribute('href', 'https://x.mx/r.pdf#page=56');
  expect(screen.getByRole('button', { name: 'Respuesta útil' })).toBeInTheDocument();
});

test('the daily limit is explained and the typed question is not lost', async () => {
  chat.streamMessage.mockRejectedValue(new ChatError('Llegaste al límite de 40 mensajes por día. Vuelve mañana.', { status: 429, code: 'limite_diario' }));
  renderPage();
  await screen.findByRole('heading', { name: /¿En qué te\s*ayudo\s*\?/ });

  fireEvent.change(screen.getByLabelText('Tu pregunta'), { target: { value: 'otra duda' } });
  fireEvent.keyDown(screen.getByLabelText('Tu pregunta'), { key: 'Enter' });

  const alert = await screen.findByRole('alert');
  expect(within(alert).getByText(/límite de 40 mensajes/)).toBeInTheDocument();
  await waitFor(() => expect(screen.getByLabelText('Tu pregunta')).toHaveValue('otra duda'));
});

test('a full conversation offers to start a new one', async () => {
  chat.streamMessage.mockRejectedValue(new ChatError('Esta conversación llegó a su límite.', { status: 409, code: 'conversacion_llena' }));
  renderPage();
  await screen.findByRole('heading', { name: /¿En qué te\s*ayudo\s*\?/ });
  fireEvent.change(screen.getByLabelText('Tu pregunta'), { target: { value: 'hola' } });
  fireEvent.keyDown(screen.getByLabelText('Tu pregunta'), { key: 'Enter' });

  const alert = await screen.findByRole('alert');
  fireEvent.click(within(alert).getByRole('button', { name: 'Nueva conversación' }));
  expect(await screen.findByRole('heading', { name: /¿En qué te\s*ayudo\s*\?/ })).toBeInTheDocument();
});

test('an expired session sends the person back to log in', async () => {
  chat.listConversations.mockRejectedValue(new ChatError('Authentication required', { status: 401 }));
  renderPage();
  const alert = await screen.findByRole('alert');
  expect(within(alert).getByText(/sesión expiró/)).toBeInTheDocument();
  expect(within(alert).getByRole('link', { name: 'Iniciar sesión' })).toHaveAttribute('href', '/Login');
});

test('opening an existing conversation shows its saved messages with citations and votes', async () => {
  chat.listConversations.mockResolvedValue([{ id: 7, title: 'Licencia', created_at: 'x', updated_at: 'y' }]);
  chat.listMessages.mockResolvedValue([
    { id: 1, role: 'user', content: '¿Licencia?', status: 'complete', citations: null, created_at: 'x', feedback: null },
    { id: 2, role: 'assistant', content: 'Sí [1].', status: 'complete', citations: [citation], created_at: 'x', feedback: 1 },
  ]);
  renderPage();
  fireEvent.click(await screen.findByRole('button', { name: 'Licencia' }));
  expect(await screen.findByText('¿Licencia?')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Respuesta útil' })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getAllByRole('link', { name: /Reglamento de Tránsito/ }).length).toBeGreaterThan(0);
});
