import React, { useRef, useState } from 'react';
import GoogleSignInButton, { GOOGLE_CLIENT_ID } from './GoogleSignInButton';
import TermsCheckbox from './TermsCheckbox';

const TERMS_MESSAGE = 'Para continuar debes aceptar los Términos de uso y el Aviso de privacidad. Marca la casilla y vuelve a presionar el botón de Google.';

// Divider, consent checkbox and Google button. The button stays usable without ticking (returning users are never
// blocked); only if the backend says a new account would be created does the checkbox become required.
// `signIn(credential, acceptedTerms)` must reject on failure; `onError(message)` receives any other failure.
export default function GoogleAuthSection({ text, signIn, onError }) {
    const [accepted, setAccepted] = useState(false);
    const [termsError, setTermsError] = useState('');
    const checkbox = useRef(null);

    if (!GOOGLE_CLIENT_ID) return null;

    const handleCredential = async (credential) => {
        setTermsError('');
        try {
            await signIn(credential, accepted);
        } catch (err) {
            if (err.code === 'terms_required') {
                setTermsError(TERMS_MESSAGE);
                checkbox.current?.scrollIntoView?.({ block: 'center' }); // jsdom has no scrollIntoView
                checkbox.current?.focus();
            } else {
                onError(err.message);
            }
        }
    };

    return (
        <>
            <div className="tw-flex tw-items-center tw-gap-3 tw-my-5 tw-text-xs tw-text-ink-soft">
                <span className="tw-h-px tw-flex-1 tw-bg-rule" />o<span className="tw-h-px tw-flex-1 tw-bg-rule" />
            </div>
            <div className="tw-mb-3">
                <TermsCheckbox
                    id="googleAcceptTerms"
                    lead="Acepto los"
                    checked={accepted}
                    inputRef={checkbox}
                    error={termsError}
                    onChange={(value) => { setAccepted(value); if (value) setTermsError(''); }}
                />
            </div>
            <GoogleSignInButton onCredential={handleCredential} text={text} />
        </>
    );
}
