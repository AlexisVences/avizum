import React from 'react';

const PageHeader = ({ title, description, actions }) => (
    <header className="tw-mb-6 tw-flex tw-flex-wrap tw-items-start tw-justify-between tw-gap-4">
        <div>
            <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink">{title}</h1>
            {description && <p className="tw-mt-1 tw-text-ink-soft">{description}</p>}
        </div>
        {actions && <div className="tw-flex tw-items-center tw-gap-2">{actions}</div>}
    </header>
);

export default PageHeader;
