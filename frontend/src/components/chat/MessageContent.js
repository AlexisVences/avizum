import React, { useMemo } from 'react';
import Markdown from 'react-markdown';

// Only what an answer needs. Raw HTML is dropped (skipHtml) and everything outside this list is unwrapped to text.
const ALLOWED = ['p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'br', 'blockquote', 'h1', 'h2', 'h3', 'h4'];

// The model writes "[23]"; the user should see the order of use (¹ ² ³) linking to the official PDF at the page.
// While the answer is still arriving the markers are hidden: the citations event comes last, so they cannot be
// resolved yet and a raw "[23]" would flicker on screen.
export const withCitationLinks = (text, citations, streaming) => {
  const byNumber = new Map((citations || []).map((c) => [c.n, c]));
  // A marker still being typed ("[2" at the end of the text so far) must not show up either.
  const visible = streaming ? text.replace(/\s?\[\d{0,3}$/, '') : text;
  return visible.replace(/\s?\[(\d{1,3})\]/g, (_, n) => {
    const citation = byNumber.get(Number(n));
    return streaming || !citation ? '' : ` [${citation.orden}](#cita-${n})`;
  });
};

export default function MessageContent({ content, citations = [], streaming = false }) {
  const source = useMemo(() => withCitationLinks(content, citations, streaming), [content, citations, streaming]);

  const components = useMemo(() => {
    const byNumber = new Map(citations.map((c) => [String(c.n), c]));
    return {
      p: (props) => <p className="tw-mb-3 last:tw-mb-0 tw-leading-relaxed" {...stripNode(props)} />,
      ul: (props) => <ul className="tw-mb-3 tw-list-disc tw-pl-5 last:tw-mb-0" {...stripNode(props)} />,
      ol: (props) => <ol className="tw-mb-3 tw-list-decimal tw-pl-5 last:tw-mb-0" {...stripNode(props)} />,
      li: (props) => <li className="tw-mb-1" {...stripNode(props)} />,
      strong: (props) => <strong className="tw-font-semibold" {...stripNode(props)} />,
      blockquote: (props) => <blockquote className="tw-border-l-2 tw-border-rule tw-pl-3 tw-text-ink-soft" {...stripNode(props)} />,
      code: (props) => <code className="tw-rounded tw-bg-gris tw-px-1 tw-font-mono tw-text-[0.9em]" {...stripNode(props)} />,
      a: ({ href = '', children }) => {
        if (href.startsWith('#cita-')) {
          const citation = byNumber.get(href.slice('#cita-'.length));
          if (!citation) return null;
          const where = `${citation.source_title}${citation.article ? `, art. ${citation.article}` : ''}${citation.fraction ? ` fr. ${citation.fraction}` : ''}`;
          return (
            <sup>
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                title={where}
                aria-label={`Fuente ${citation.orden}: ${where}`}
                className="tw-ml-0.5 tw-rounded tw-bg-azul/10 tw-px-1 tw-font-semibold tw-text-azul tw-no-underline hover:tw-bg-azul/20"
              >
                {children}
              </a>
            </sup>
          );
        }
        // The only links an answer may have are citations (built by the backend from the official documents).
        // Any other link the model writes is shown as plain text, so an answer cannot send anyone elsewhere.
        return <span>{children}</span>;
      },
    };
  }, [citations]);

  return (
    <Markdown skipHtml allowedElements={ALLOWED} unwrapDisallowed components={components}>
      {source}
    </Markdown>
  );
}

// react-markdown passes the syntax node as a prop; it must not reach the DOM.
function stripNode({ node, ...rest }) {
  return rest;
}
