import React, { useEffect, useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { FaBars, FaTimes } from 'react-icons/fa';
import logo from '../assets/logo.png';
import authService from '../services/authService';

const LINKS = [
    { to: '/admin', label: 'Resumen' },
    { to: '/admin/calidad', label: 'Calidad' },
    { to: '/admin/usuarios', label: 'Usuarios' },
    { to: '/admin/fuentes', label: 'Fuentes' },
    { to: '/admin/actividad', label: 'Actividad' },
];

const focusRing = 'focus-visible:tw-outline focus-visible:tw-outline-2 focus-visible:tw-outline-offset-2 focus-visible:tw-outline-azul';

const isActive = (pathname, to) => {
    const clean = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;
    return to === '/admin' ? clean === '/admin' : clean === to || clean.startsWith(`${to}/`);
};

// Mismo ancho (272px) y estilo que la barra del chat: fija desde `md`, cajón en pantallas estrechas.
const AdminLayout = () => {
    const { pathname } = useLocation();
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    const user = authService.getCurrentUser() || {};
    const name = [user.nombre, user.apellido].filter(Boolean).join(' ') || 'Administrador';
    const initial = (user.nombre || user.correo || 'A').trim().charAt(0).toUpperCase();

    useEffect(() => {
        setOpen(false);
    }, [pathname]);

    const logout = () => {
        authService.logout();
        navigate('/');
    };

    return (
        <div className="tw-flex tw-min-h-screen tw-bg-paper tw-font-sans tw-text-ink">
            {open && (
                <button
                    type="button"
                    tabIndex={-1}
                    aria-hidden="true"
                    onClick={() => setOpen(false)}
                    className="tw-fixed tw-inset-0 tw-z-30 tw-cursor-default tw-border-0 tw-bg-ink/30 md:tw-hidden"
                />
            )}
            <aside
                data-testid="admin-sidebar"
                aria-label="Panel de administración"
                className={`tw-fixed tw-inset-y-0 tw-left-0 tw-z-40 tw-flex tw-w-[272px] tw-shrink-0 tw-flex-col tw-bg-gris motion-safe:tw-transition-transform md:tw-sticky md:tw-top-0 md:tw-z-auto md:tw-h-screen md:tw-translate-x-0 ${
                    open ? 'tw-translate-x-0' : '-tw-translate-x-full'
                }`}
            >
                <div className="tw-flex tw-items-center tw-justify-between tw-px-5 tw-pb-4 tw-pt-5">
                    <Link to="/admin" className={`tw-flex tw-items-center tw-gap-2.5 tw-no-underline ${focusRing}`}>
                        <img src={logo} alt="" className="tw-h-8 tw-w-auto" />
                        <span className="tw-font-display tw-text-lg tw-font-semibold tw-tracking-tight tw-text-ink">Avizum</span>
                    </Link>
                    <button
                        type="button"
                        aria-label="Cerrar menú"
                        onClick={() => setOpen(false)}
                        className={`tw-h-11 tw-w-11 tw-rounded-full tw-border-0 tw-bg-transparent tw-text-ink-soft hover:tw-text-ink md:tw-hidden ${focusRing}`}
                    >
                        <FaTimes className="tw-mx-auto" />
                    </button>
                </div>
                <nav aria-label="Administración" className="tw-flex-1 tw-overflow-y-auto tw-px-3">
                    <ul className="tw-m-0 tw-list-none tw-space-y-0.5 tw-p-0">
                        {LINKS.map(({ to, label }) => {
                            const active = isActive(pathname, to);
                            return (
                                <li key={to}>
                                    <Link
                                        to={to}
                                        aria-current={active ? 'page' : undefined}
                                        className={`tw-flex tw-h-11 tw-items-center tw-rounded-[22px] tw-px-4 tw-text-sm tw-no-underline tw-transition-colors ${focusRing} ${
                                            active
                                                ? 'tw-bg-ink/[.07] tw-font-semibold tw-text-magenta'
                                                : 'tw-text-ink hover:tw-bg-ink/[.05]'
                                        }`}
                                    >
                                        {label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>
                <div className="tw-shrink-0 tw-p-3">
                    <div className="tw-flex tw-items-center tw-gap-3 tw-px-2 tw-py-2">
                        <span aria-hidden="true" className="tw-flex tw-h-8 tw-w-8 tw-shrink-0 tw-items-center tw-justify-center tw-rounded-full tw-bg-magenta tw-text-sm tw-font-semibold tw-text-white">
                            {initial}
                        </span>
                        <span className="tw-min-w-0 tw-flex-1 tw-truncate tw-text-sm tw-text-ink">{name}</span>
                    </div>
                    <button
                        type="button"
                        onClick={logout}
                        className={`tw-mt-1 tw-flex tw-h-11 tw-w-full tw-items-center tw-rounded-[22px] tw-border-0 tw-bg-transparent tw-px-4 tw-text-left tw-text-sm tw-text-ink hover:tw-bg-ink/[.05] ${focusRing}`}
                    >
                        Cerrar sesión
                    </button>
                </div>
            </aside>
            <div className="tw-min-w-0 tw-flex-1">
                <div className="tw-flex tw-h-14 tw-items-center tw-px-4 md:tw-hidden">
                    <button
                        type="button"
                        aria-label="Abrir menú"
                        aria-expanded={open}
                        onClick={() => setOpen(true)}
                        className={`tw-flex tw-h-11 tw-w-11 tw-items-center tw-justify-center tw-rounded-full tw-border-0 tw-bg-transparent tw-text-ink ${focusRing}`}
                    >
                        <FaBars />
                    </button>
                </div>
                <main className="tw-mx-auto tw-w-full tw-max-w-6xl tw-px-4 tw-pb-12 md:tw-px-8 md:tw-pt-8">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default AdminLayout;
