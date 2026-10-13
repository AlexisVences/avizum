import React from 'react';
import { FaFilePdf } from 'react-icons/fa';

const labelOf = (c) => {
  const place = c.article ? `art. ${c.article}${c.fraction ? `, fr. ${c.fraction}` : ''}` : 'documento completo';
  return `${c.source_title} · ${place}${c.page ? ` · pág. ${c.page}` : ''}`;
};

// One chip per source the answer actually used, each opening the official PDF at the page of the fragment.
export default function CitationChips({ citations }) {
  if (!citations?.length) return null;
  return (
    <ul className="tw-mt-3 tw-flex tw-list-none tw-flex-wrap tw-gap-2 tw-p-0" aria-label="Fuentes consultadas">
      {citations.map((citation) => (
        <li key={citation.n} className="tw-max-w-full">
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="tw-inline-flex tw-max-w-full tw-items-center tw-gap-2 tw-rounded-full tw-border tw-border-azul/30 tw-bg-azul/5 tw-px-3 tw-py-1 tw-text-xs tw-text-azul tw-no-underline hover:tw-bg-azul/10"
          >
            <span className="tw-font-semibold">{citation.orden}</span>
            <FaFilePdf aria-hidden="true" className="tw-shrink-0" />
            <span className="tw-truncate">{labelOf(citation)}</span>
          </a>
        </li>
      ))}
    </ul>
  );
}
