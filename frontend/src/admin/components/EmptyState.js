import React from 'react';

const EmptyState = ({ title, hint, action }) => (
    <div className="tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-px-6 tw-py-10 tw-text-center">
        <p className="tw-font-display tw-text-xl tw-text-ink">{title}</p>
        {hint && <p className="tw-mt-1 tw-text-ink-soft">{hint}</p>}
        {action && <div className="tw-mt-4">{action}</div>}
    </div>
);

export default EmptyState;
