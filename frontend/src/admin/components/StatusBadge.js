import React from 'react';

const TONES = {
    ok: 'tw-border-verde tw-text-verde',
    warn: 'tw-border-magenta tw-text-magenta',
    danger: 'tw-border-danger tw-text-danger',
    neutral: 'tw-border-rule tw-text-ink-soft',
};

const StatusBadge = ({ tone = 'neutral', children }) => (
    <span
        className={`tw-inline-flex tw-items-center tw-rounded-full tw-border tw-bg-paper-raised tw-px-2.5 tw-py-0.5 tw-text-sm ${
            TONES[tone] || TONES.neutral
        }`}
    >
        {children}
    </span>
);

export default StatusBadge;
