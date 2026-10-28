import React from 'react';
import { FaFilePdf, FaGlobe } from 'react-icons/fa';
import isWebUrl from '../../utils/isWebUrl';

// A ficha is a transcribed official web page: it has a section ("Requisitos") instead of an article, and no page.
export const isWebPage = (c) => Boolean(c.article) && !c.page;

export const placeOf = (c) => {
  if (!c.article) return 'documento completo';
  if (isWebPage(c)) return c.article;
  return `art. ${c.article}${c.fraction ? `, fr. ${c.fraction}` : ''}`;
};

const labelOf = (c) => `${c.source_title} · ${placeOf(c)}${c.page ? ` · pág. ${c.page}` : ''}`;

// One chip per source the answer actually used, each opening the official PDF at the page of the fragment (or the official web page).
export default function CitationChips({ citations }) {
  if (!citations?.length) return null;
  return (
    <ul className="tw-mt-3 tw-flex tw-list-none tw-flex-wrap tw-gap-2 tw-p-0" aria-label="Fuentes consultadas">
      {citations.map((citation) => {
        const chip = (
          <>
            <span className="tw-font-semibold">{citation.orden}</span>
            {isWebPage(citation) ? <FaGlobe aria-hidden="true" className="tw-shrink-0" /> : <FaFilePdf aria-hidden="true" className="tw-shrink-0" />}
            <span className="tw-truncate">{labelOf(citation)}</span>
          </>
        );
        const chipClasses = 'tw-inline-flex tw-max-w-full tw-items-center tw-gap-2 tw-rounded-full tw-border tw-border-azul/30 tw-bg-azul/5 tw-px-3 tw-py-1 tw-text-xs tw-text-azul';
        return (
          <li key={citation.n} className="tw-max-w-full">
            {isWebUrl(citation.url) ? (
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`${chipClasses} tw-no-underline hover:tw-bg-azul/10`}
              >
                {chip}
              </a>
            ) : (
              <span className={chipClasses}>{chip}</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
