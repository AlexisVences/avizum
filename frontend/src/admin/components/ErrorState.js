import React from 'react';

const ErrorState = ({ message, onRetry }) => (
    <div
        role="alert"
        className="tw-rounded-lg tw-border tw-border-danger tw-bg-paper-raised tw-px-6 tw-py-8 tw-text-center"
    >
        <p className="tw-text-danger">{message}</p>
        <button
            type="button"
            onClick={onRetry}
            className="tw-mt-4 tw-rounded tw-bg-magenta tw-px-4 tw-py-2 tw-text-white focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul"
        >
            Reintentar
        </button>
    </div>
);

export default ErrorState;
