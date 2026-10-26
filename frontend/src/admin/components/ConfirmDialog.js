import React, { useEffect, useRef, useState } from 'react';

const ConfirmDialog = ({
    open,
    title,
    body,
    confirmLabel,
    tone = 'default',
    requireText,
    onConfirm,
    onCancel,
}) => {
    const ref = useRef(null);
    const [texto, setTexto] = useState('');

    useEffect(() => {
        const dialog = ref.current;
        if (!dialog) return;
        if (open) {
            setTexto('');
            if (!dialog.open) {
                // jsdom y navegadores antiguos pueden no tener showModal.
                if (typeof dialog.showModal === 'function') dialog.showModal();
                else dialog.setAttribute('open', '');
            }
        } else if (dialog.open) {
            if (typeof dialog.close === 'function') dialog.close();
            else dialog.removeAttribute('open');
        }
    }, [open]);

    const bloqueado = Boolean(requireText) && texto !== requireText;
    const colorConfirmar = tone === 'danger' ? 'tw-bg-danger' : 'tw-bg-magenta';

    const cancelar = (e) => {
        e.preventDefault();
        onCancel();
    };

    return (
        <dialog
            ref={ref}
            aria-labelledby="confirm-dialog-title"
            onCancel={cancelar}
            onKeyDown={(e) => {
                if (e.key === 'Escape') cancelar(e);
            }}
            className="tw-w-full tw-max-w-md tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-6 tw-text-ink backdrop:tw-bg-black/40"
        >
            <h2 id="confirm-dialog-title" className="tw-font-display tw-text-xl">
                {title}
            </h2>
            <p className="tw-mt-2 tw-text-ink-soft">{body}</p>
            {requireText && (
                <label className="tw-mt-4 tw-block">
                    <span className="tw-text-sm tw-text-ink-soft">
                        {`Escribe ${requireText} para continuar`}
                    </span>
                    <input
                        type="text"
                        value={texto}
                        onChange={(e) => setTexto(e.target.value)}
                        className="tw-mt-1 tw-w-full tw-rounded tw-border tw-border-rule tw-px-3 tw-py-2 focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-azul"
                    />
                </label>
            )}
            <div className="tw-mt-6 tw-flex tw-justify-end tw-gap-2">
                <button
                    type="button"
                    onClick={onCancel}
                    className="tw-rounded tw-border tw-border-rule tw-px-4 tw-py-2 focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-azul"
                >
                    Cancelar
                </button>
                <button
                    type="button"
                    disabled={bloqueado}
                    onClick={onConfirm}
                    className={`tw-rounded ${colorConfirmar} tw-px-4 tw-py-2 tw-text-white disabled:tw-opacity-50 focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul`}
                >
                    {confirmLabel}
                </button>
            </div>
        </dialog>
    );
};

export default ConfirmDialog;
