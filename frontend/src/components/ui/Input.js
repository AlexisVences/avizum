import React, { useId } from "react";

/**
 * Labeled text input. Pass `mono` for data-shaped values (plates, folios).
 */
const Input = ({ label, id, mono = false, className = "", ...rest }) => {
    const generatedId = useId();
    const inputId = id || generatedId;
    return (
        <div className={className}>
            {label && (
                <label htmlFor={inputId} className="tw-block tw-text-sm tw-font-semibold tw-text-ink tw-mb-1">
                    {label}
                </label>
            )}
            <input
                id={inputId}
                className={`tw-w-full tw-rounded tw-border tw-border-rule tw-bg-paper-raised tw-px-3.5 tw-py-2 tw-text-ink placeholder:tw-text-ink-soft/60 focus:tw-outline-none focus:tw-border-azul focus:tw-ring-2 focus:tw-ring-azul/20 disabled:tw-bg-gris disabled:tw-text-ink-soft disabled:tw-cursor-not-allowed ${mono ? "tw-font-mono tw-tracking-wider" : ""}`}
                {...rest}
            />
        </div>
    );
};

export default Input;
