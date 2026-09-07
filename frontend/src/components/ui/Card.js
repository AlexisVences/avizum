import React from "react";

/**
 * Base surface for grouped content. `folio` is the signature "reference
 * number" mark from the design system (e.g. "01 · ASESORÍA") -- optional.
 */
const Card = ({ folio, className = "", children }) => (
    <div className={`tw-bg-paper-raised tw-border tw-border-rule tw-rounded tw-p-5 ${className}`}>
        {folio && (
            <div className="tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-2.5">
                {folio}
            </div>
        )}
        {children}
    </div>
);

export default Card;
