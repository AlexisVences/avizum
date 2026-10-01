import React, { useState } from "react";
import { Link } from "react-router-dom";
import logo from "../assets/logo.png";

const Navbar = () => {
    const [open, setOpen] = useState(false);

    return (
        <nav className="tw-fixed tw-top-0 tw-inset-x-0 tw-z-50 tw-bg-paper-raised/75 tw-backdrop-blur-md tw-backdrop-saturate-150 tw-border-b tw-border-rule/60">
            <div className="tw-w-full tw-px-4 sm:tw-px-6 lg:tw-px-8 tw-py-3 tw-flex tw-items-center tw-justify-between">
                <Link to="/" className="tw-flex tw-items-center tw-gap-2.5 tw-shrink-0 tw-no-underline" onClick={() => setOpen(false)}>
                    <img src={logo} alt="Amicuz" className="tw-h-8 tw-w-auto tw-shrink-0" />
                    <span className="tw-font-display tw-font-semibold tw-text-lg tw-tracking-tight tw-text-ink">
                        Amicuz
                    </span>
                </Link>

                <div className="tw-hidden sm:tw-flex tw-items-center tw-gap-2">
                    <Link to="/Login" className="tw-px-4 tw-py-2 tw-rounded tw-text-sm tw-font-semibold tw-text-ink tw-border tw-border-ink/20 hover:tw-border-ink/50 tw-transition-colors tw-no-underline">
                        Iniciar sesión
                    </Link>
                    <Link to="/Sing-in" className="tw-px-4 tw-py-2 tw-rounded tw-text-sm tw-font-semibold tw-text-white tw-bg-ink hover:tw-bg-magenta tw-transition-colors tw-no-underline">
                        Registrarse
                    </Link>
                </div>

                <button
                    type="button"
                    className="sm:tw-hidden tw-w-9 tw-h-9 tw-flex tw-flex-col tw-items-center tw-justify-center tw-gap-1.5 tw-rounded tw-border tw-border-ink/15"
                    aria-label={open ? "Cerrar menú" : "Abrir menú"}
                    aria-expanded={open}
                    onClick={() => setOpen(v => !v)}
                >
                    <span className={`tw-block tw-w-5 tw-h-0.5 tw-bg-ink tw-transition-transform ${open ? "tw-translate-y-2 tw-rotate-45" : ""}`}></span>
                    <span className={`tw-block tw-w-5 tw-h-0.5 tw-bg-ink tw-transition-opacity ${open ? "tw-opacity-0" : ""}`}></span>
                    <span className={`tw-block tw-w-5 tw-h-0.5 tw-bg-ink tw-transition-transform ${open ? "-tw-translate-y-2 -tw-rotate-45" : ""}`}></span>
                </button>
            </div>

            {open && (
                <div className="sm:tw-hidden tw-bg-paper-raised/75 tw-backdrop-blur-md tw-backdrop-saturate-150 tw-border-t tw-border-rule/60 tw-px-4 tw-py-3 tw-flex tw-flex-col tw-gap-2">
                    <Link to="/Login" onClick={() => setOpen(false)} className="tw-px-4 tw-py-2.5 tw-rounded tw-text-sm tw-font-semibold tw-text-center tw-text-ink tw-border tw-border-ink/20 tw-no-underline">
                        Iniciar sesión
                    </Link>
                    <Link to="/Sing-in" onClick={() => setOpen(false)} className="tw-px-4 tw-py-2.5 tw-rounded tw-text-sm tw-font-semibold tw-text-center tw-text-white tw-bg-ink tw-no-underline">
                        Registrarse
                    </Link>
                </div>
            )}
        </nav>
    );
};

export default Navbar;
