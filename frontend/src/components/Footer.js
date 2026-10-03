import React from "react";
import { Link } from "react-router-dom";

// Pages render their own <Footer/> inside App's flex-column <main>, so the
// wrapper's auto top margin pins it to the bottom of short pages. `className`
// sets the gap above it (default 4rem); pass "tw-pt-0" when the page ends in a
// full-bleed colored block that should touch the footer.
const Footer = ({ className = "tw-pt-16" }) => {
    return (
        <div className={`tw-mt-auto ${className}`}>
            <footer className="tw-border-t tw-border-rule tw-bg-gris">
                <div className="tw-mx-auto tw-max-w-5xl tw-px-4 tw-py-6 tw-flex tw-flex-wrap tw-gap-x-6 tw-gap-y-2 tw-items-center tw-justify-center tw-text-center">
                    <p className="tw-m-0 tw-text-sm tw-text-ink-soft">© 2025 Amicuz. Todos los derechos reservados.</p>
                    <Link to="/Acerca-de" className="tw-text-sm tw-font-medium tw-text-ink hover:tw-text-magenta tw-no-underline">Acerca de</Link>
                    <Link to="/Contacto" className="tw-text-sm tw-font-medium tw-text-ink hover:tw-text-magenta tw-no-underline">Contacto</Link>
                    <Link to="/Aviso-legal" className="tw-text-sm tw-font-medium tw-text-ink hover:tw-text-magenta tw-no-underline">Aviso Legal</Link>
                </div>
            </footer>
        </div>
    );
}

export default Footer;
