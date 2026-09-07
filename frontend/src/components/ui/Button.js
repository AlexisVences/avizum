import React from "react";
import { Link } from "react-router-dom";

const VARIANTS = {
    primary: "tw-bg-magenta tw-text-white hover:tw-bg-magenta/90",
    dark: "tw-bg-ink tw-text-white hover:tw-bg-ink/90",
    outline: "tw-bg-transparent tw-text-ink tw-border tw-border-ink/25 hover:tw-border-ink/60",
};

const SIZES = {
    sm: "tw-px-3.5 tw-py-1.5 tw-text-sm",
    md: "tw-px-5 tw-py-2.5 tw-text-sm",
    lg: "tw-px-6 tw-py-3 tw-text-base",
};

/**
 * Shared CTA. Pass `to` for an in-app link (renders react-router Link),
 * `href` for an external link (renders <a>), or neither for a <button>.
 */
const Button = ({ to, href, variant = "primary", size = "md", className = "", children, ...rest }) => {
    const classes = `tw-inline-flex tw-items-center tw-justify-center tw-rounded tw-font-semibold tw-transition-colors tw-no-underline disabled:tw-opacity-50 disabled:tw-pointer-events-none ${VARIANTS[variant]} ${SIZES[size]} ${className}`;

    if (to) {
        return (
            <Link to={to} className={classes} {...rest}>
                {children}
            </Link>
        );
    }
    if (href) {
        return (
            <a href={href} className={classes} {...rest}>
                {children}
            </a>
        );
    }
    return (
        <button className={classes} {...rest}>
            {children}
        </button>
    );
};

export default Button;
