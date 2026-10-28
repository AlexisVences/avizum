import React, { useEffect, useRef, useState } from 'react';
import { FaTimes } from 'react-icons/fa';
import { deleteUser, updateUser } from '../../services/adminService';
import { focusRing, formatDate, fullName } from '../format';
import ConfirmDialog from './ConfirmDialog';
import StatusBadge from './StatusBadge';

const ROLES = { user: 'Usuario', admin: 'Administrador' };

const ERROR_TEXT = {
    cannot_modify_self: 'No puedes cambiar tu propia cuenta. Pídele a otra persona administradora que lo haga.',
    last_admin: 'Debe quedar al menos un administrador activo en Avizum.',
    confirmation_mismatch: 'El correo escrito no coincide con el de la cuenta.',
};

const actionButton = `tw-min-h-[44px] tw-w-full tw-rounded tw-border tw-border-rule tw-bg-paper-raised tw-px-4 tw-py-2 tw-text-left disabled:tw-opacity-50 ${focusRing}`;

const UserPanel = ({ user, currentUserId, onChanged, onClose }) => {
    const [role, setRole] = useState(user.role);
    const [dialog, setDialog] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    const closeRef = useRef(null);
    const isSelf = user.id === currentUserId;

    useEffect(() => {
        closeRef.current?.focus();
    }, []);

    const run = async (action, { closeAfter = false } = {}) => {
        setBusy(true);
        setError(null);
        try {
            await action();
            setDialog(null);
            onChanged();
            if (closeAfter) onClose();
        } catch (err) {
            setDialog(null);
            setError(ERROR_TEXT[err?.code] || err?.message || 'No pudimos completar la operación. Intenta de nuevo.');
        } finally {
            setBusy(false);
        }
    };

    const activeLabel = user.isActive ? 'Desactivar cuenta' : 'Reactivar cuenta';
    const name = fullName(user.firstName, user.lastName);

    return (
        <>
            <aside
                aria-label="Detalle de la persona"
                onKeyDown={(e) => {
                    if (e.key === 'Escape' && !dialog) onClose();
                }}
                className="tw-fixed tw-inset-y-0 tw-right-0 tw-z-40 tw-flex tw-w-full tw-flex-col tw-overflow-y-auto tw-border-l tw-border-rule tw-bg-paper-raised tw-p-6 tw-shadow-xl md:tw-w-[380px]"
            >
                <div className="tw-flex tw-items-start tw-justify-between tw-gap-3">
                    <div className="tw-min-w-0">
                        <h2 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink">{name}</h2>
                        <p className="tw-break-all tw-text-ink-soft">{user.email}</p>
                    </div>
                    <button
                        type="button"
                        ref={closeRef}
                        aria-label="Cerrar detalle"
                        onClick={onClose}
                        className={`tw-h-11 tw-w-11 tw-shrink-0 tw-rounded-full tw-border-0 tw-bg-transparent tw-text-ink-soft hover:tw-text-ink ${focusRing}`}
                    >
                        <FaTimes className="tw-mx-auto" />
                    </button>
                </div>

                <div className="tw-mt-4 tw-flex tw-flex-wrap tw-gap-2">
                    <StatusBadge tone={user.isActive ? 'ok' : 'danger'}>{user.isActive ? 'Activa' : 'Inactiva'}</StatusBadge>
                    <StatusBadge tone={user.emailVerified ? 'ok' : 'warn'}>
                        {user.emailVerified ? 'Correo verificado' : 'Correo sin verificar'}
                    </StatusBadge>
                    <StatusBadge>{ROLES[user.role] || user.role}</StatusBadge>
                </div>

                <dl className="tw-mt-6 tw-grid tw-grid-cols-2 tw-gap-4">
                    <div>
                        <dt className="tw-text-sm tw-text-ink-soft">Preguntas</dt>
                        <dd className="tw-m-0 tw-font-display tw-text-2xl">{user.questionsCount}</dd>
                    </div>
                    <div>
                        <dt className="tw-text-sm tw-text-ink-soft">Última actividad</dt>
                        <dd className="tw-m-0">{formatDate(user.lastActivityAt) || 'Sin actividad'}</dd>
                    </div>
                    <div>
                        <dt className="tw-text-sm tw-text-ink-soft">Alta</dt>
                        <dd className="tw-m-0">{formatDate(user.createdAt)}</dd>
                    </div>
                </dl>

                {error && (
                    <p role="alert" className="tw-mt-6 tw-rounded tw-border tw-border-danger tw-px-3 tw-py-2 tw-text-danger">
                        {error}
                    </p>
                )}

                <div className="tw-mt-6 tw-space-y-4">
                    {isSelf && (
                        <p className="tw-text-ink-soft">{ERROR_TEXT.cannot_modify_self}</p>
                    )}
                    <div className="tw-space-y-2">
                        <label className="tw-block">
                            <span className="tw-text-sm tw-text-ink-soft">Rol</span>
                            <select
                                value={role}
                                disabled={isSelf}
                                onChange={(e) => setRole(e.target.value)}
                                className={`tw-mt-1 tw-block tw-min-h-[44px] tw-w-full tw-rounded tw-border tw-border-rule tw-bg-white tw-px-3 disabled:tw-opacity-50 ${focusRing}`}
                            >
                                <option value="user">Usuario</option>
                                <option value="admin">Administrador</option>
                            </select>
                        </label>
                        <button
                            type="button"
                            disabled={isSelf || busy || role === user.role}
                            onClick={() => setDialog('role')}
                            className={`${actionButton} tw-text-ink`}
                        >
                            Cambiar rol
                        </button>
                    </div>
                    <button type="button" disabled={isSelf || busy} onClick={() => setDialog('active')} className={`${actionButton} tw-text-ink`}>
                        {activeLabel}
                    </button>
                    <button
                        type="button"
                        disabled={isSelf || busy}
                        onClick={() => setDialog('delete')}
                        className={`${actionButton} tw-text-danger`}
                    >
                        Eliminar cuenta
                    </button>
                </div>
            </aside>

            <ConfirmDialog
                open={dialog === 'role'}
                title="Cambiar rol"
                body={`${name} pasará a ser ${(ROLES[role] || role).toLowerCase()}.`}
                confirmLabel="Cambiar rol"
                onConfirm={() => run(() => updateUser(user.id, { role }))}
                onCancel={() => setDialog(null)}
            />
            <ConfirmDialog
                open={dialog === 'active'}
                title={activeLabel}
                body={
                    user.isActive
                        ? `${name} ya no podrá iniciar sesión hasta que reactives su cuenta.`
                        : `${name} podrá volver a iniciar sesión.`
                }
                confirmLabel={activeLabel}
                onConfirm={() => run(() => updateUser(user.id, { isActive: !user.isActive }))}
                onCancel={() => setDialog(null)}
            />
            <ConfirmDialog
                open={dialog === 'delete'}
                title="Eliminar cuenta"
                body={`Se borrarán la cuenta de ${name} y todo su historial de conversaciones. No se puede deshacer.`}
                confirmLabel="Eliminar cuenta"
                tone="danger"
                requireText={user.email}
                onConfirm={() => run(() => deleteUser(user.id, user.email), { closeAfter: true })}
                onCancel={() => setDialog(null)}
            />
        </>
    );
};

export default UserPanel;
