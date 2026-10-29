import React, { useEffect, useRef } from "react";
import Navbar from "./Navbar";
import logo from "../assets/logo.png";

/** Shared shell for the account pages (same look as Login). The heading takes focus when `focusKey` changes. */
const AuthCard = ({ title, focusKey, children }) => {
  const headingRef = useRef(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, [focusKey]);

  return (
    <>
      <Navbar />
      <main className="tw-pt-16">
        <div className="tw-min-h-[calc(100vh-4rem)] tw-bg-gris tw-flex tw-items-center tw-justify-center tw-px-4 tw-py-10">
          <div className="tw-w-full tw-max-w-md tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-8">
            <div className="tw-flex tw-items-center tw-gap-2.5 tw-mb-6">
              <img src={logo} alt="Avizum" className="tw-h-8 tw-w-auto tw-shrink-0" />
              <h1
                ref={headingRef}
                tabIndex={-1}
                className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-m-0 focus:tw-outline-none"
              >
                {title}
              </h1>
            </div>
            {children}
          </div>
        </div>
      </main>
    </>
  );
};

export const ErrorBox = ({ children }) => (
  <div role="alert" className="tw-bg-danger/5 tw-border tw-border-danger/20 tw-text-danger tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-4">
    {children}
  </div>
);

export const StatusBox = ({ children }) => (
  <div role="status" className="tw-bg-verde/10 tw-border tw-border-verde/30 tw-text-verde tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-4">
    {children}
  </div>
);

export const linkClass = "tw-font-semibold tw-text-azul hover:tw-text-magenta tw-no-underline";

export default AuthCard;
