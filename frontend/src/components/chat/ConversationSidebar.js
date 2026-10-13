import React, { useState } from 'react';
import { FaPen, FaPlus, FaTimes, FaTrash } from 'react-icons/fa';

// bg-transparent: buttons otherwise show the browser's grey "buttonface" background.
const iconButton = 'tw-rounded tw-border-0 tw-bg-transparent tw-p-1.5 tw-text-ink-soft hover:tw-text-ink focus:tw-text-ink';

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
      <li className="tw-px-2 tw-py-1">
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
          className="tw-w-full tw-rounded tw-border tw-border-azul tw-bg-paper-raised tw-px-2 tw-py-1 tw-text-sm"
        />
      </li>
    );
  }

  if (mode === 'confirm') {
    return (
      <li className="tw-flex tw-items-center tw-gap-2 tw-px-3 tw-py-2 tw-text-sm">
        <span className="tw-flex-1 tw-text-danger">¿Eliminar esta conversación?</span>
        <button type="button" onClick={() => onDelete(conversation.id)} className="tw-border-0 tw-bg-transparent tw-font-semibold tw-text-danger">Eliminar</button>
        <button type="button" onClick={() => setMode('view')} className="tw-border-0 tw-bg-transparent tw-text-ink-soft">Cancelar</button>
      </li>
    );
  }

  return (
    <li className={`tw-group tw-flex tw-items-center tw-rounded-lg ${active ? 'tw-bg-azul/10' : 'hover:tw-bg-gris'}`}>
      <button
        type="button"
        disabled={busy}
        onClick={() => onSelect(conversation.id)}
        aria-current={active ? 'true' : undefined}
        className="tw-min-w-0 tw-flex-1 tw-truncate tw-border-0 tw-bg-transparent tw-px-3 tw-py-2 tw-text-left tw-text-sm tw-text-ink disabled:tw-opacity-60"
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

// On narrow screens it is a drawer opened from the header; from `md` up it is a fixed column.
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
        className={`tw-fixed tw-bottom-0 tw-left-0 tw-top-16 tw-z-40 tw-flex tw-w-72 tw-flex-col tw-border-r tw-border-rule tw-bg-paper tw-transition-transform md:tw-static md:tw-z-auto md:tw-translate-x-0 ${
          open ? 'tw-translate-x-0' : '-tw-translate-x-full'
        }`}
      >
        <div className="tw-flex tw-items-center tw-gap-2 tw-p-3">
          <button
            type="button"
            onClick={() => { onNew(); onClose(); }}
            disabled={busy}
            className="tw-flex tw-flex-1 tw-items-center tw-justify-center tw-gap-2 tw-rounded-lg tw-bg-azul tw-px-3 tw-py-2 tw-text-sm tw-font-medium tw-text-white disabled:tw-opacity-60"
          >
            <FaPlus aria-hidden="true" /> Nueva conversación
          </button>
          <button type="button" aria-label="Cerrar historial" onClick={onClose} className={`${iconButton} md:tw-hidden`}>
            <FaTimes />
          </button>
        </div>
        <ul className="tw-m-0 tw-flex-1 tw-list-none tw-space-y-0.5 tw-overflow-y-auto tw-p-2">
          {conversations.length === 0 && <li className="tw-px-3 tw-py-2 tw-text-sm tw-text-ink-soft">Aún no tienes conversaciones.</li>}
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
      </aside>
    </>
  );
}
