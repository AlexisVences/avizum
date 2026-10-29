import React, { useEffect, useState } from 'react';
import PageHeader from '../components/PageHeader';
import Skeleton from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Pagination from '../components/Pagination';
import useAdminList from '../hooks/useAdminList';
import { listAudit, listUsers } from '../../services/adminService';
import { fieldClasses, focusRing, fullName } from '../format';

const PAGE_SIZE = 20;
const TIME_ZONE = 'America/Mexico_City';


const ACTIONS = [
    { value: 'user.role_changed', label: 'Cambios de rol' },
    { value: 'user.deactivated', label: 'Cuentas desactivadas' },
    { value: 'user.reactivated', label: 'Cuentas reactivadas' },
    { value: 'user.deleted', label: 'Cuentas eliminadas' },
    { value: 'review.marked', label: 'Respuestas revisadas' },
];

const ROLE_LABEL = { user: 'usuario', admin: 'administrador' };
const roleLabel = (role) => ROLE_LABEL[role] || String(role ?? 'desconocido');

const SENTENCES = {
    'user.role_changed': (d, person) =>
        `cambió el rol de ${person}: de ${roleLabel(d.from)} a ${roleLabel(d.to)}`,
    'user.deactivated': (d, person) => `desactivó la cuenta de ${person}`,
    'user.reactivated': (d, person) => `reactivó la cuenta de ${person}`,
    'user.deleted': (d, person) => `eliminó la cuenta de ${person} (era ${roleLabel(d.role)})`,
    'review.marked': (d) => `marcó como revisada ${d.messageId == null ? 'una respuesta' : `la respuesta ${d.messageId}`}`,
};

export const describeEntry = ({ actorName, action, targetUserId, targetName, detail }) => {
    const build = SENTENCES[action];
    if (!build) return action;
    let person = 'una persona';
    if (targetName) person = targetName;
    else if (targetUserId != null) person = `la persona ${targetUserId}`;
    return `${actorName || 'Una cuenta eliminada'} ${build(detail || {}, person)}`;
};

const dateFormat = new Intl.DateTimeFormat('es-MX', {
    timeZone: TIME_ZONE,
    day: 'numeric',
    month: 'short',
    year: 'numeric',
});
const timeFormat = new Intl.DateTimeFormat('es-MX', {
    timeZone: TIME_ZONE,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
});

const ADMINS_QUERY = { role: 'admin', pageSize: 50 };

const Actividad = () => {
    const [action, setAction] = useState('');
    const [actorId, setActorId] = useState('');
    const [admins, setAdmins] = useState([]);
    const [page, setPage] = useState(1);

    // The filter is a convenience: if the list of administrators fails, the log still works.
    useEffect(() => {
        let active = true;
        listUsers(ADMINS_QUERY)
            .then((result) => {
                if (active) setAdmins(result?.items || []);
            })
            .catch(() => {});
        return () => {
            active = false;
        };
    }, []);

    const filtered = Boolean(action || actorId);
    const params = {
        action: action || undefined,
        actorId: actorId ? Number(actorId) : undefined,
        page,
        pageSize: PAGE_SIZE,
    };
    const { data, loading, error, reload } = useAdminList(listAudit, params);

    const items = data?.items || [];
    const total = data?.total || 0;

    // Si la página quedó fuera de rango, vuelve a la última real.
    useEffect(() => {
        if (data && data.items.length === 0 && data.total > 0 && page > 1) {
            setPage(Math.ceil(data.total / PAGE_SIZE));
        }
    }, [data, page]);

    let content;
    if (error) {
        content = <ErrorState message={error} onRetry={reload} />;
    } else if (!data) {
        content = <Skeleton lines={6} />;
    } else if (items.length === 0 && total > 0) {
        content = (
            <>
                <p className="tw-text-ink-soft">No hay registros en esta página.</p>
                <div className="tw-mt-4">
                    <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
                </div>
            </>
        );
    } else if (items.length === 0) {
        content = filtered ? (
            <EmptyState
                title="No hay actividad con estos filtros"
                hint="Prueba con otra acción o persona, o quita los filtros."
                action={
                    <button
                        type="button"
                        onClick={() => {
                            setAction('');
                            setActorId('');
                            setPage(1);
                        }}
                        className={`tw-rounded tw-bg-magenta tw-px-4 tw-py-2 tw-text-white ${focusRing}`}
                    >
                        Quitar filtros
                    </button>
                }
            />
        ) : (
            <EmptyState
                title="Todavía no hay actividad"
                hint="Los cambios de rol, desactivaciones y eliminaciones de cuentas aparecerán aquí."
            />
        );
    } else {
        content = (
            <>
                <div className={loading ? 'tw-opacity-60' : undefined} aria-busy={loading}>
                    <table className="tw-w-full tw-border-collapse tw-text-left">
                        <thead className="tw-hidden md:tw-table-header-group">
                            <tr className="tw-border-b tw-border-rule">
                                <th scope="col" className="tw-px-3 tw-py-2 tw-text-sm tw-font-semibold tw-text-ink-soft">
                                    Cuándo
                                </th>
                                <th scope="col" className="tw-px-3 tw-py-2 tw-text-sm tw-font-semibold tw-text-ink-soft">
                                    Qué pasó
                                </th>
                            </tr>
                        </thead>
                        <tbody className="tw-block md:tw-table-row-group">
                            {items.map((entry) => {
                                const when = new Date(entry.createdAt);
                                return (
                                    <tr
                                        key={entry.id}
                                        className="tw-mb-3 tw-block tw-rounded-lg tw-border tw-border-rule tw-bg-paper-raised tw-p-4 md:tw-mb-0 md:tw-table-row md:tw-rounded-none md:tw-border-0 md:tw-border-b md:tw-bg-transparent md:tw-p-0"
                                    >
                                        <td className="tw-block tw-text-sm tw-text-ink-soft md:tw-table-cell md:tw-whitespace-nowrap md:tw-px-3 md:tw-py-3 md:tw-text-base">
                                            <time dateTime={entry.createdAt}>
                                                <span>{dateFormat.format(when)}</span>
                                                {', '}
                                                <span>{timeFormat.format(when)}</span>
                                            </time>
                                        </td>
                                        <td className="tw-block tw-break-words md:tw-table-cell md:tw-px-3 md:tw-py-3">
                                            {describeEntry(entry)}
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
            <PageHeader title="Actividad" description="Quién hizo qué en la consola de administración." />
            <div className="tw-mb-6 tw-flex tw-flex-wrap tw-gap-4">
                <label className="tw-block tw-w-full tw-max-w-xs">
                    <span className="tw-text-sm tw-text-ink-soft">Persona</span>
                    <select
                        value={actorId}
                        onChange={(e) => {
                            setActorId(e.target.value);
                            setPage(1);
                        }}
                        className={`${fieldClasses} tw-w-full`}
                    >
                        <option value="">Todas</option>
                        {admins.map((admin) => (
                            <option key={admin.id} value={admin.id}>
                                {fullName(admin.firstName, admin.lastName)}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="tw-block tw-w-full tw-max-w-xs">
                    <span className="tw-text-sm tw-text-ink-soft">Acción</span>
                    <select
                        value={action}
                        onChange={(e) => {
                            setAction(e.target.value);
                            setPage(1);
                        }}
                        className={`${fieldClasses} tw-w-full`}
                    >
                        <option value="">Todas</option>
                        {ACTIONS.map(({ value, label }) => (
                            <option key={value} value={value}>
                                {label}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            {content}
        </>
    );
};

export default Actividad;
