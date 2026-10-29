import React from 'react';
import cdmxMap from '../../assets/cdmxMap';
import '../../styles/AsesoriaIA.css';

// The map is decorative and fixed: it sits behind the whole conversation and never scrolls. Coordinates come from
// assets/cdmxMap.js (generated from the official alcaldías boundaries, see frontend/scripts/build_cdmx_map.py).
// The view box is wider than the map to leave room for the names; "slice" crops it to fill the screen, so on a phone only
// the middle of the map shows and the names fall outside.
const VIEW = { x: -1000, y: -600, width: 2000, height: 1200 };
const GAP = 70; // between the map's box and a name
const LABEL_COLOR = '#B3BCC9';

const Label = ({ x, y, anchor = 'start', size = 15, spacing = '0.28em', opacity = 1, children }) => (
  <text x={x} y={y} textAnchor={anchor} fontSize={size} letterSpacing={spacing} fill={LABEL_COLOR} fillOpacity={opacity} fontFamily="Public Sans, sans-serif" fontWeight="600">
    {children}
  </text>
);

// `names` prints the alcaldías around the map: right for the empty screen, off during a conversation so they never sit
// under the text of an answer. `glow` adds the soft brand aura (blue in the middle, magenta along the bottom) under the map.
// `labelSize` / `labelOpacity` shrink and fade the names and the corner marks for places where the map is only a texture.
export default function CdmxMapBackground({ names = true, glow = false, labelSize = 15, labelOpacity = 1 }) {
  const { box, alcaldias, labels } = cdmxMap;
  return (
    <div aria-hidden="true" className="tw-pointer-events-none tw-absolute tw-inset-0 -tw-z-10 tw-overflow-hidden">
      {glow && <div className="asesoria-glow tw-absolute tw-inset-0" />}
      <svg
        viewBox={`${VIEW.x} ${VIEW.y} ${VIEW.width} ${VIEW.height}`}
        preserveAspectRatio="xMidYMid slice"
        className="tw-h-full tw-w-full"
        focusable="false"
      >
        <defs>
          <radialGradient id="cdmx-map-fade" cx="50%" cy="50%" r="62%">
            <stop offset="0%" stopColor="#F7F6F3" stopOpacity="0" />
            <stop offset="70%" stopColor="#F7F6F3" stopOpacity="0" />
            <stop offset="100%" stopColor="#F7F6F3" stopOpacity="0.55" />
          </radialGradient>
        </defs>
        <g fill="#DCE2EB" fillOpacity="0.22" stroke="#FFFFFF" strokeOpacity="0.5" strokeWidth="1.2" strokeLinejoin="round">
          {alcaldias.map((alcaldia) => (
            <path key={alcaldia.name} data-alcaldia={alcaldia.name} d={alcaldia.d} />
          ))}
        </g>
        <rect x={VIEW.x} y={VIEW.y} width={VIEW.width} height={VIEW.height} fill="url(#cdmx-map-fade)" />

        {names && labels.map((label) => {
          const right = label.side === 'right';
          return (
            <Label key={label.text} x={right ? box.maxX + GAP : box.minX - GAP} y={label.y} anchor={right ? 'start' : 'end'} size={labelSize} opacity={labelOpacity}>
              {label.text}
            </Label>
          );
        })}
      </svg>
      {/* Pinned to the screen's corners, so a crop of the map never cuts them. */}
      <span style={{ opacity: labelOpacity }} className="tw-absolute tw-left-[7%] tw-top-[8%] tw-font-sans tw-text-sm tw-font-semibold tw-tracking-[0.4em] tw-text-[#B3BCC9]">CDMX</span>
      <span style={{ opacity: labelOpacity }} className="tw-absolute tw-right-[5%] tw-top-[6%] tw-flex tw-flex-col tw-items-center tw-gap-1 tw-font-sans tw-text-xs tw-font-semibold tw-text-[#B3BCC9]">
        <svg width="26" height="30" viewBox="-14 -30 28 46" focusable="false"><path d="M0 -30 L14 14 L0 6 L-14 14 Z" fill="currentColor" fillOpacity="0.8" /></svg>
        N
      </span>
    </div>
  );
}
