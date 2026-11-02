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
                    className={`tw-mt-1 ${error ? 'tw-outline tw-outline-2 tw-outline-offset-1 tw-outline-danger' : ''}`}
                />
                <label htmlFor={id} className="tw-text-sm tw-text-ink">
                    {lead}{" "}
                    <a href="/terminos" target="_blank" rel="noopener noreferrer" className={linkClass}>Términos de uso</a>
                    {" "}y el{" "}
                    <a href="/Aviso-legal" target="_blank" rel="noopener noreferrer" className={linkClass}>Aviso de privacidad</a>
                </label>
            </div>
            {error && (
                <p id={`${id}-error`} role="alert" className="tw-mt-2 tw-mb-0 tw-rounded tw-border tw-border-danger/40 tw-bg-danger/5 tw-px-3 tw-py-2 tw-text-sm tw-font-medium tw-text-danger">
                    {error}
                </p>
            )}
        </div>
    );
}
