import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import GoogleAuthSection from '../GoogleAuthSection';

let mockCredential;
jest.mock('../GoogleSignInButton', () => ({
    __esModule: true,
    GOOGLE_CLIENT_ID: 'client-id',
    default: ({ onCredential }) => { mockCredential = onCredential; return <div data-testid="google-button" />; },
}));

const setup = (signIn) => {
    const onError = jest.fn();
    render(<GoogleAuthSection text="signin_with" signIn={signIn} onError={onError} />);
    return onError;
};

test('muestra el checkbox con enlaces a términos y aviso', () => {
    setup(jest.fn());
    expect(screen.getByRole('checkbox', { name: /Acepto los Términos de uso y el Aviso de privacidad/ })).not.toBeChecked();
    expect(screen.getByRole('link', { name: 'Términos de uso' })).toHaveAttribute('href', '/terminos');
    expect(screen.getByRole('link', { name: 'Aviso de privacidad' })).toHaveAttribute('href', '/Aviso-legal');
});

test('envía accepted_terms false por defecto y true al marcar', async () => {
    const signIn = jest.fn().mockResolvedValue();
    setup(signIn);
    await act(async () => { await mockCredential('cred'); });
    expect(signIn).toHaveBeenLastCalledWith('cred', false);
    fireEvent.click(screen.getByRole('checkbox'));
    await act(async () => { await mockCredential('cred'); });
    expect(signIn).toHaveBeenLastCalledWith('cred', true);
});

test('terms_required muestra alerta, marca el checkbox como inválido y lo enfoca', async () => {
    const err = Object.assign(new Error('x'), { code: 'terms_required' });
    const onError = setup(jest.fn().mockRejectedValue(err));
    await act(async () => { await mockCredential('cred'); });
    expect(screen.getByRole('alert')).toHaveTextContent(/Para continuar debes aceptar los Términos de uso y el Aviso de privacidad/);
    expect(screen.getByRole('alert')).toHaveTextContent(/vuelve a presionar el botón de Google/);
    const box = screen.getByRole('checkbox');
    expect(box).toHaveAttribute('aria-invalid', 'true');
    expect(box).toHaveFocus();
    expect(onError).not.toHaveBeenCalled();
    fireEvent.click(box);
    expect(screen.queryByRole('alert')).toBeNull();
});

test('otros errores se delegan a onError y no tocan el checkbox', async () => {
    const onError = setup(jest.fn().mockRejectedValue(new Error('No pudimos verificar')));
    await act(async () => { await mockCredential('cred'); });
    await waitFor(() => expect(onError).toHaveBeenCalledWith('No pudimos verificar'));
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByRole('checkbox')).toHaveAttribute('aria-invalid', 'false');
});

test('el éxito no muestra errores', async () => {
    const onError = setup(jest.fn().mockResolvedValue());
    await act(async () => { await mockCredential('cred'); });
    expect(onError).not.toHaveBeenCalled();
    expect(screen.queryByRole('alert')).toBeNull();
});
