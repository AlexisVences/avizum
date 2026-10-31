import React from 'react';

const linkClass = 'tw-font-semibold tw-text-azul hover:tw-text-magenta';

// Consent checkbox shared by the registration form and the Google sign-in block.
export default function TermsCheckbox({ id, checked, onChange, error, lead = 'He leído y acepto los', inputRef }) {
    return (
        <div>
            <div className="tw-flex tw-items-start tw-gap-2">
                <input
                    id={id}
                    ref={inputRef}
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                    aria-required="true"
                    aria-invalid={error ? 'true' : 'false'}
                    aria-describedby={error ? `${id}-error` : undefined}
                    className="tw-mt-1"
                />
                <label htmlFor={id} className="tw-text-sm tw-text-ink">
                    {lead}{" "}
                    <a href="/terminos" target="_blank" rel="noopener noreferrer" className={linkClass}>Términos de uso</a>
                    {" "}y el{" "}
                    <a href="/Aviso-legal" target="_blank" rel="noopener noreferrer" className={linkClass}>Aviso de privacidad</a>
                </label>
            </div>
            {error && (
                <p id={`${id}-error`} role="alert" className="tw-text-danger tw-text-xs tw-mt-1 tw-mb-0">
                    {error}
                </p>
            )}
        </div>
    );
}
