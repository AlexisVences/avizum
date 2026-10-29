import React, { useEffect, useRef, useState } from 'react';
import PageHeader from '../components/PageHeader';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import StatusBadge from '../components/StatusBadge';
import Pagination from '../components/Pagination';
import UserPanel from '../components/UserPanel';
import useAdminList from '../hooks/useAdminList';
import { listUsers } from '../../services/adminService';
import authService from '../../services/authService';
import { fieldClasses, focusRing, formatDate } from '../format';

const PAGE_SIZE = 20;
const SEARCH_DELAY_MS = 300;
const NO_FILTERS = { role: '', active: '', verified: '' };


const COLUMNS = [
    { key: 'name', label: 'Persona' },
    { key: null, label: 'Rol' },
    { key: null, label: 'Estado' },
    { key: 'activity', label: 'Última actividad' },
    { key: 'questions', label: 'Preguntas' },
    { key: 'created', label: 'Alta' },
];

// Orden inicial de cada columna al activarla por primera vez.
const FIRST_DIRECTION = { name: false, created: true, activity: true, questions: true };

const Usuarios = () => {
    const currentUserId = authService.getCurrentUser()?.id;
    const [searchText, setSearchText] = useState('');
    const [q, setQ] = useState('');
    const [filters, setFilters] = useState(NO_FILTERS);
    const [sort, setSort] = useState('created');
    const [descending, setDescending] = useState(true);
    const [page, setPage] = useState(1);
    const [selectedId, setSelectedId] = useState(null);

    const qRef = useRef('');
    qRef.current = q;

    useEffect(() => {
        const timer = setTimeout(() => {
            const next = searchText.trim();
            // Solo vuelve a la primera página si el texto cambió de verdad.
            if (next === qRef.current) return;
            setQ(next);
            setPage(1);
        }, SEARCH_DELAY_MS);
        return () => clearTimeout(timer);
    }, [searchText]);

    const params = {
        q: q || undefined,
        role: filters.role || undefined,
        active: filters.active === '' ? undefined : filters.active === 'true',
        verified: filters.verified === '' ? undefined : filters.verified === 'true',
        sort,
        descending,
        page,
        pageSize: PAGE_SIZE,
    };
    const { data, loading, error, reload } = useAdminList(listUsers, params);

    const items = data?.items || [];
    const total = data?.total || 0;
    const selected = items.find((u) => u.id === selectedId) || null;
    const hasFilters = Boolean(q || filters.role || filters.active || filters.verified);

    // Si la página quedó fuera de rango (p. ej. tras eliminar a la última persona), vuelve a la última real.
    useEffect(() => {
        if (data && data.items.length === 0 && data.total > 0 && page > 1) {
            setPage(Math.ceil(data.total / PAGE_SIZE));
        }
    }, [data, page]);

    const changeFilter = (name) => (e) => {
        setFilters((f) => ({ ...f, [name]: e.target.value }));
        setPage(1);
    };

    const clearFilters = () => {
        setSearchText('');
        setQ('');
        setFilters(NO_FILTERS);
        setPage(1);
    };

    const toggleSort = (key) => {
        if (key === sort) setDescending((d) => !d);
        else {
            setSort(key);
            setDescending(FIRST_DIRECTION[key]);
        }
        setPage(1);
    };

    const ariaSort = (key) => (key !== sort ? 'none' : descending ? 'descending' : 'ascending');

    let content;
    if (error) {
        content = <ErrorState message={error} onRetry={reload} />;
    } else if (!data) {
        content = <Skeleton lines={6} />;
    } else if (items.length === 0 && total === 0) {
        content = hasFilters ? (
            <EmptyState
                title="No encontramos personas"
                hint="Prueba quitar algún filtro o cambiar la búsqueda."
                action={
                    <button
                        type="button"
                        onClick={clearFilters}
                        className={`tw-rounded tw-bg-magenta tw-px-4 tw-py-2 tw-text-white ${focusRing}`}
                    >
                        Quitar filtros
                    </button>
                }
            />
        ) : (
            <EmptyState title="Todavía no hay personas" hint="Cuando alguien cree una cuenta en Avizum, aparecerá aquí." />
        );
    } else {
        content = (
            <>
                <div className={loading ? 'tw-opacity-60' : undefined} aria-busy={loading}>
                    <table className="tw-w-full tw-border-collapse tw-text-left">
                        <thead className="tw-hidden md:tw-table-header-group">
                            <tr className="tw-border-b tw-border-rule">
                                {COLUMNS.map(({ key, label }) => (
                                    <th
                                        key={label}
                                        scope="col"
                                        aria-sort={key ? ariaSort(key) : undefined}
                                        className="tw-px-3 tw-py-2 tw-text-sm tw-font-semibold tw-text-ink-soft"
                                    >
                                        {key ? (
                                            <button
                                                type="button"
                                                onClick={() => toggleSort(key)}
                                                className={`tw-border-0 tw-bg-transparent tw-p-0 tw-font-semibold tw-text-ink-soft hover:tw-text-ink ${focusRing}`}
                                            >
                                                {label}
                                                <span aria-hidden="true">{key === sort ? (descending ? ' ↓' : ' ↑') : ''}</span>
                                            </button>
                                        ) : (
                                            label
                                        )}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="tw-block md:tw-table-row-group">
                            {items.map((u) => {
                                const name = [u.firstName, u.lastName].filter(Boolean).join(' ');
                                const isSelf = u.id === currentUserId;
                                return (
                                    <tr
                                        key={u.id}
                                        className={`tw-mb-3 tw-block tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-4 md:tw-mb-0 md:tw-table-row md:tw-rounded-none md:tw-border-0 md:tw-border-b md:tw-bg-transparent md:tw-p-0 ${
                                            u.id === selectedId ? 'md:tw-bg-ink/[.05]' : ''
                                        }`}
                                    >
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            <button
                                                type="button"
                                                onClick={() => setSelectedId(u.id)}
                                                className={`tw-border-0 tw-bg-transparent tw-p-0 tw-text-left tw-font-semibold tw-text-azul hover:tw-underline ${focusRing}`}
                                            >
                                                {name}
                                            </button>
                                            {isSelf && <span className="tw-ml-2 tw-text-sm tw-text-ink-soft">(tú)</span>}
                                            <div className="tw-break-all tw-text-sm tw-text-ink-soft">{u.email}</div>
                                        </td>
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            {u.role === 'admin' ? 'Administrador' : 'Usuario'}
                                        </td>
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            <span className="tw-flex tw-flex-wrap tw-gap-1">
                                                <StatusBadge tone={u.isActive ? 'ok' : 'danger'}>
                                                    {u.isActive ? 'Activa' : 'Inactiva'}
                                                </StatusBadge>
                                                {!u.emailVerified && <StatusBadge tone="warn">Sin verificar</StatusBadge>}
                                            </span>
                                        </td>
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            <span className="tw-text-ink-soft md:tw-hidden">Última actividad: </span>
                                            {formatDate(u.lastActivityAt) || 'Sin actividad'}
                                        </td>
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            <span className="tw-text-ink-soft md:tw-hidden">Preguntas: </span>
                                            {u.questionsCount}
                                        </td>
                                        <td className="tw-block md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            <span className="tw-text-ink-soft md:tw-hidden">Alta: </span>
                                            {formatDate(u.createdAt)}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
                <div className="tw-mt-4">
                    <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
                </div>
            </>
        );
    }

    return (
        <>
            <PageHeader title="Usuarios" description="Busca personas, cambia su rol o su estado." />
            <div className="tw-mb-6 tw-flex tw-flex-wrap tw-items-end tw-gap-4">
                <label className="tw-block tw-min-w-[220px] tw-flex-1">
                    <span className="tw-text-sm tw-text-ink-soft">Buscar</span>
                    <input
                        type="search"
                        aria-label="Buscar personas"
                        placeholder="Nombre o correo"
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        className={`${fieldClasses} tw-w-full`}
                    />
                </label>
                <label className="tw-block">
                    <span className="tw-text-sm tw-text-ink-soft">Rol</span>
                    <select value={filters.role} onChange={changeFilter('role')} className={fieldClasses}>
                        <option value="">Todos</option>
                        <option value="user">Usuario</option>
                        <option value="admin">Administrador</option>
                    </select>
                </label>
                <label className="tw-block">
                    <span className="tw-text-sm tw-text-ink-soft">Estado</span>
                    <select value={filters.active} onChange={changeFilter('active')} className={fieldClasses}>
                        <option value="">Todos</option>
                        <option value="true">Activas</option>
                        <option value="false">Inactivas</option>
                    </select>
                </label>
                <label className="tw-block">
                    <span className="tw-text-sm tw-text-ink-soft">Correo</span>
                    <select value={filters.verified} onChange={changeFilter('verified')} className={fieldClasses}>
                        <option value="">Todos</option>
                        <option value="true">Verificado</option>
                        <option value="false">Sin verificar</option>
                    </select>
                </label>
                <label className="tw-block md:tw-hidden">
                    <span className="tw-text-sm tw-text-ink-soft">Ordenar por</span>
                    <select
                        value={`${sort}:${descending}`}
                        onChange={(e) => {
                            const [key, desc] = e.target.value.split(':');
                            setSort(key);
                            setDescending(desc === 'true');
                            setPage(1);
                        }}
                        className={fieldClasses}
                    >
                        <option value="created:true">Más recientes</option>
                        <option value="created:false">Más antiguas</option>
                        <option value="name:false">Nombre (A–Z)</option>
                        <option value="activity:true">Actividad reciente</option>
                        <option value="questions:true">Más preguntas</option>
                    </select>
                </label>
            </div>
            {content}
            {selected && (
                <UserPanel
                    key={selected.id}
                    user={selected}
                    currentUserId={currentUserId}
                    onChanged={reload}
                    onClose={() => setSelectedId(null)}
                />
            )}
        </>
    );
};

export default Usuarios;
