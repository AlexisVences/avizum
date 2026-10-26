import React from 'react';

const Skeleton = ({ lines = 3 }) => (
    <div role="status" aria-label="Cargando" className="tw-space-y-3">
        {Array.from({ length: lines }, (_, i) => (
            <div
                key={i}
                aria-hidden="true"
                className="tw-h-4 tw-rounded tw-bg-gris motion-safe:tw-animate-pulse"
                style={{ width: i === lines - 1 ? '60%' : '100%' }}
            />
        ))}
    </div>
);

export default Skeleton;
