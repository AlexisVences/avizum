export const focusRing =
    'focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';

export const fieldClasses = `tw-mt-1 tw-block tw-min-h-[44px] tw-rounded tw-border tw-border-rule tw-bg-white tw-px-3 ${focusRing}`;

const dateFormat = new Intl.DateTimeFormat('es-MX', {
    timeZone: 'America/Mexico_City',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
});

// «20 oct 2026» on the Mexico City calendar; null when there is no date.
export const formatDate = (iso) => (iso ? dateFormat.format(new Date(iso)) : null);

export const fullName = (first, last) => [first, last].filter(Boolean).join(' ');
