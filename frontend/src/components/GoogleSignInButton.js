import React, { useEffect, useRef } from 'react';

const SCRIPT_SRC = 'https://accounts.google.com/gsi/client';
export const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;

let scriptPromise;
const loadGoogleScript = () => {
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = SCRIPT_SRC;
      script.async = true;
      script.onload = resolve;
      script.onerror = () => {
        scriptPromise = undefined;
        reject(new Error('No se pudo cargar Google'));
      };
      document.head.appendChild(script);
    });
  }
  return scriptPromise;
};

// Google draws its own button; it hands back a signed ID token (`credential`) that the backend verifies.
// Without REACT_APP_GOOGLE_CLIENT_ID the button is simply not shown.
export default function GoogleSignInButton({ onCredential, text = 'continue_with' }) {
  const container = useRef(null);
  const callback = useRef(onCredential);
  callback.current = onCredential;

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return undefined;
    let cancelled = false;
    loadGoogleScript()
      .then(() => {
        if (cancelled || !container.current || !window.google?.accounts?.id) return;
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response) => callback.current(response.credential),
        });
        window.google.accounts.id.renderButton(container.current, {
          type: 'standard', theme: 'outline', size: 'large', text, shape: 'pill', locale: 'es', width: 320,
        });
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [text]);

  if (!GOOGLE_CLIENT_ID) return null;
  return <div ref={container} data-testid="google-button" className="tw-flex tw-justify-center" />;
}
