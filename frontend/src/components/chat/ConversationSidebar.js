import React, { useState } from 'react';
import { FaPen, FaPlus, FaTimes, FaTrash } from 'react-icons/fa';
import logo from '../../assets/logo.png';
import authService from '../../services/authService';

// bg-transparent: buttons otherwise show the browser's grey "buttonface" background.
const iconButton = 'tw-rounded-full tw-border-0 tw-bg-transparent tw-p-2 tw-text-ink-soft hover:tw-text-ink focus:tw-text-ink';

function Row({ conversation, active, busy, onSelect, onRename, onDelete }) {
  const [mode, setMode] = useState('view'); // 'view' | 'rename' | 'confirm'
  const [title, setTitle] = useState(conversation.title || '');
  const label = conversation.title || 'Conversación sin título';

  if (mode === 'rename') {
    const save = () => {
      const clean = title.trim();
      if (clean && clean !== conversation.title) onRename(conversation.id, clean);
      setMode('view');
    };
    return (
      <li className="tw-flex tw-h-11 tw-items-center">
        <input
          autoFocus
          value={title}
          maxLength={80}
          aria-label="Nombre de la conversación"
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') save();
            if (event.key === 'Escape') setMode('view');
          }}
          onBlur={save}
          className="tw-h-11 tw-w-full tw-rounded-[22px] tw-border-0 tw-bg-paper-raised tw-px-4 tw-text-sm tw-text-ink focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/40"
        />
      </li>
    );
  }

  if (mode === 'confirm') {
    return (
      <li className="tw-flex tw-min-h-11 tw-items-center tw-gap-2 tw-px-4 tw-text-sm">
        <span className="tw-flex-1 tw-text-danger">¿Eliminar esta conversación?</span>
        <button type="button" onClick={() => onDelete(conversation.id)} className="tw-border-0 tw-bg-transparent tw-font-semibold tw-text-danger">Eliminar</button>
        <button type="button" onClick={() => setMode('view')} className="tw-border-0 tw-bg-transparent tw-text-ink-soft">Cancelar</button>
      </li>
    );
  }

  return (
    <li className={`tw-group tw-flex tw-h-11 tw-items-center tw-rounded-[22px] tw-transition-colors ${active ? 'tw-bg-ink/[.07]' : 'hover:tw-bg-ink/[.05]'}`}>
      <button
        type="button"
        disabled={busy}
        onClick={() => onSelect(conversation.id)}
        aria-current={active ? 'true' : undefined}
        className="tw-h-full tw-min-w-0 tw-flex-1 tw-truncate tw-border-0 tw-bg-transparent tw-pl-4 tw-pr-2 tw-text-left tw-text-sm tw-text-ink disabled:tw-opacity-60"
      >
        {label}
      </button>
      <span className="tw-flex tw-pr-1 tw-opacity-0 group-hover:tw-opacity-100 group-focus-within:tw-opacity-100">
        <button type="button" aria-label={`Renombrar ${label}`} onClick={() => { setTitle(conversation.title || ''); setMode('rename'); }} className={iconButton}>
          <FaPen size={11} />
        </button>
        <button type="button" aria-label={`Eliminar ${label}`} onClick={() => setMode('confirm')} className={iconButton}>
          <FaTrash size={11} />
        </button>
      </span>
    </li>
  );
}

function Account() {
  const [open, setOpen] = useState(false);
  const user = authService.getCurrentUser?.() || {};
  const name = [user.nombre, user.apellido].filter(Boolean).join(' ') || 'Mi cuenta';
  const initial = (user.nombre || user.correo || 'A').trim().charAt(0).toUpperCase();

  const logout = () => {
    authService.logout();
    window.location.assign('/');
  };

  return (
    <div className="tw-relative tw-shrink-0 tw-p-3">
      {open && (
        <div role="menu" className="tw-absolute tw-inset-x-3 tw-bottom-[calc(100%-4px)] tw-rounded-3xl tw-bg-paper-raised tw-p-2 tw-shadow-[0_12px_32px_-12px_rgba(22,24,29,.25)]">
          <a role="menuitem" href="/Gestionar-perfil" className="tw-flex tw-h-11 tw-items-center tw-rounded-[22px] tw-px-4 tw-text-sm tw-text-ink tw-no-underline hover:tw-bg-ink/[.05]">
            Gestionar perfil
          </a>
          <button type="button" role="menuitem" onClick={logout} className="tw-flex tw-h-11 tw-w-full tw-items-center tw-rounded-[22px] tw-border-0 tw-bg-transparent tw-px-4 tw-text-left tw-text-sm tw-text-ink hover:tw-bg-ink/[.05]">
            Cerrar sesión
          </button>
        </div>
      )}
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="tw-flex tw-h-12 tw-w-full tw-items-center tw-gap-3 tw-rounded-3xl tw-border-0 tw-bg-transparent tw-px-2 tw-text-left tw-transition-colors hover:tw-bg-ink/[.05]"
      >
        <span aria-hidden="true" className="tw-flex tw-h-8 tw-w-8 tw-shrink-0 tw-items-center tw-justify-center tw-rounded-full tw-bg-magenta tw-text-sm tw-font-semibold tw-text-white">
          {initial}
        </span>
        <span className="tw-min-w-0 tw-flex-1 tw-truncate tw-text-sm tw-text-ink">{name}</span>
      </button>
    </div>
  );
}

// On narrow screens it is a drawer opened from a floating button; from `md` up it is a fixed 272px column.
// Hierarchy comes from tone (a slightly darker surface than the main area), not from borders.
export default function ConversationSidebar({ conversations, activeId, busy, open, onClose, onSelect, onNew, onRename, onDelete }) {
  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Cerrar historial"
          onClick={onClose}
          className="tw-fixed tw-inset-0 tw-z-30 tw-cursor-default tw-border-0 tw-bg-ink/30 md:tw-hidden"
        />
      )}
      <aside
        aria-label="Conversaciones"
        className={`tw-fixed tw-inset-y-0 tw-left-0 tw-z-40 tw-flex tw-w-[272px] tw-shrink-0 tw-flex-col tw-bg-gris tw-transition-transform md:tw-static md:tw-z-auto md:tw-translate-x-0 ${
          open ? 'tw-translate-x-0' : '-tw-translate-x-full'
        }`}
      >
        <div className="tw-flex tw-items-center tw-justify-between tw-px-5 tw-pb-4 tw-pt-5">
          <a href="/Bienvenida" className="tw-flex tw-items-center tw-gap-2.5 tw-no-underline">
            <img src={logo} alt="" className="tw-h-8 tw-w-auto" />
            <span className="tw-font-display tw-text-lg tw-font-semibold tw-tracking-tight tw-text-ink">Avizum</span>
          </a>
          <button type="button" aria-label="Cerrar historial" onClick={onClose} className={`${iconButton} tw-h-11 tw-w-11 md:tw-hidden`}>
            <FaTimes />
          </button>
        </div>
        <div className="tw-px-3 tw-pb-5">
          <button
            type="button"
            onClick={() => { onNew(); onClose(); }}
            disabled={busy}
            className="tw-flex tw-h-12 tw-w-full tw-items-center tw-gap-2.5 tw-rounded-3xl tw-border-0 tw-bg-ink/[.07] tw-px-5 tw-text-sm tw-font-medium tw-text-ink tw-transition-colors hover:tw-bg-ink/[.11] disabled:tw-opacity-60"
          >
            <FaPlus aria-hidden="true" size={12} /> Nueva consulta
          </button>
        </div>
        <p className="tw-m-0 tw-px-6 tw-pb-2 tw-text-xs tw-font-medium tw-text-ink-soft">Recientes</p>
        <ul className="tw-m-0 tw-flex-1 tw-list-none tw-space-y-0.5 tw-overflow-y-auto tw-px-3 tw-pb-2">
          {conversations.length === 0 && <li className="tw-px-4 tw-py-2 tw-text-sm tw-text-ink-soft">Aún no tienes conversaciones.</li>}
          {conversations.map((conversation) => (
            <Row
              key={conversation.id}
              conversation={conversation}
              active={conversation.id === activeId}
              busy={busy}
              onSelect={(id) => { onSelect(id); onClose(); }}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))}
        </ul>
        <Account />
      </aside>
    </>
  );
}
