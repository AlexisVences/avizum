import React from "react";

const VARIANTS = {
    neutral: "tw-bg-gris tw-text-ink-soft",
    verified: "tw-bg-verde/10 tw-text-verde",
};

const Badge = ({ variant = "neutral", className = "", children }) => (
    <span className={`tw-inline-flex tw-items-center tw-rounded-full tw-px-2.5 tw-py-1 tw-text-xs tw-font-semibold ${VARIANTS[variant]} ${className}`}>
        {children}
    </span>
);

export default Badge;
