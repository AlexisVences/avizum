// Shared test doubles (kept outside __tests__ so Jest doesn't treat it as a suite): react-router-dom v7 and framer-motion (ESM) don't load
// under CRA's Jest, and neither matters for what these tests assert.
import React from 'react';

export const routerMock = {
    Link: ({ to, children, ...rest }) => (
        <a href={to} {...rest}>
            {children}
        </a>
    ),
};

const strip = ({ initial, animate, whileInView, viewport, transition, ...rest }) => rest;

export const framerMock = {
    motion: new Proxy(
        {},
        { get: (_, tag) => ({ children, ...props }) => React.createElement(tag, strip(props), children) }
    ),
    useReducedMotion: () => false,
};
