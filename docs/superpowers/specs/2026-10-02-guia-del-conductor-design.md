# Guía del conductor — design spec

Date: 2026-10-02
Status: approved by user, ready for implementation plan

## 1. Purpose

Add a content section, "Guía del conductor", reachable only from the logged-in
`/Bienvenida` page. It replaces the current "Guías y recursos legales" card and
its associated "Documentos legales que rigen el tránsito" section with a
richer, data-driven reference library: searchable/filterable categories, an
article template, and two calculator tools.

**Explicitly out of scope for this pass:** anything on `/Home` (the public
landing). No link to the guide exists anywhere outside `/Bienvenida`. That is
a deliberate, confirmed decision — revisit later, separately.

## 2. Access control

Every new route is wrapped in `RutaProtegida`, exactly like the rest of
`/Bienvenida`'s sub-pages (`/Gestionar-perfil`, `/asesoria-ia`, etc.). There is
no public entry point. This was an explicit decision, not an oversight.

## 3. Routes

No standalone `/guia` index route. The search + category grid is a section
embedded directly in `Bienvenida.js` (anchor `#guia`), replacing the current
"Documentos legales que rigen el tránsito" `<div ref={documentosRef}>` block.
Card 02's "Explorar →" CTA keeps today's smooth-scroll-to-ref behavior —
confirmed explicitly, not changed.

| Route | Component | Purpose |
|---|---|---|
| `/guia/:categoriaSlug` | `GuiaCategoria` | Lists the published articles in a category. For the `calculadoras` category, lists its tools (from `herramientas.json`) instead of articles. |
| `/guia/:categoriaSlug/:articuloSlug` | `GuiaArticulo` | Generic article template (prose, or a document-list / mito-realidad body variant). |
| `/guia/calculadoras/:herramientaSlug` | `GuiaCalculadora` | Dedicated calculator template — not the article shape. React Router (v7, already in use) ranks this literal `calculadoras` segment over the sibling dynamic `:categoriaSlug` pattern automatically, so both routes coexist without manual ordering tricks. |

All three added to `App.js` alongside the existing `RutaProtegida`-wrapped
routes.

## 4. Content model (`src/content/guia/`)

All copy lives in data files. Components render; they never hardcode copy.

### `categorias.json`

Array of 17 entries:

```json
{
  "id": "01",
  "numero": "01",
  "etiqueta": "LEYES",
  "titulo": "Marco jurídico",
  "bloque": "Leyes y derechos",
  "slug": "marco-juridico",
  "orden": 1,
  "published": true
}
```

Full list (etiqueta/título/bloque are verbatim from the approved spec; slug
and orden are derived — flag in review if a different slug is preferred):

| # | Etiqueta | Título | Bloque | Slug | Published |
|---|---|---|---|---|---|
| 01 | LEYES | Marco jurídico | Leyes y derechos | `marco-juridico` | **true** |
| 02 | DERECHOS | Si te detiene un agente | Leyes y derechos | `si-te-detiene-un-agente` | false |
| 03 | MULTAS | Multas y fotocívicas | Multas y sanciones | `multas-y-fotocivicas` | false |
| 04 | CORRALÓN | Tu auto en el corralón | Multas y sanciones | `tu-auto-en-el-corralon` | false |
| 05 | COMPRA | Comprar un auto usado | Tu auto | `comprar-auto-usado` | false |
| 06 | COMPRA | Comprar un auto nuevo | Tu auto | `comprar-auto-nuevo` | false |
| 07 | VENTA | Vender tu auto | Tu auto | `vender-tu-auto` | false |
| 08 | TRÁMITES | Trámites vehiculares | Tu auto | `tramites-vehiculares` | false |
| 09 | AMBIENTE | Verificación y Hoy No Circula | Tu auto | `verificacion-y-hoy-no-circula` | false |
| 10 | SEGUROS | Seguros | Tu auto | `seguros` | false |
| 11 | ACCIDENTES | Si chocas | En el camino | `si-chocas` | false |
| 12 | ALCOHOL | Alcoholímetro | Leyes y derechos | `alcoholimetro` | false |
| 13 | MOVILIDAD | Motos, bicis y peatones | En el camino | `motos-bicis-y-peatones` | false |
| 14 | MITOS | Mitos vs realidad | Leyes y derechos | `mitos-vs-realidad` | false |
| 15 | GLOSARIO | Glosario | Herramientas | `glosario` | false |
| 16 | CONTACTO | Directorio oficial | Herramientas | `directorio-oficial` | false |
| 17 | CÁLCULO | Calculadoras | Herramientas | `calculadoras` | false |

Only category 01 is `published: true` — the only one with real, sourced
content today. This is a confirmed decision, not a gap: per the project's
existing stance on never fabricating legal information (see
`legal_ai.py`'s 503-over-fabrication rule), the other 16 categories ship as
complete, navigable data scaffolding but stay hidden until real content is
supplied. No "Próximamente" placeholders anywhere — unpublished means absent
from the grid, full stop.

### `articulos/*.json` — one file per article

Loaded automatically via `require.context('../content/guia/articulos', false, /\.json$/)`
(a standard webpack feature CRA ships with unmodified) — adding an article
later is dropping a new JSON file, no code change.

```json
{
  "titulo": "Marco jurídico",
  "categoria": "marco-juridico",
  "slug": "marco-juridico",
  "resumen": "Los cinco documentos oficiales que rigen el tránsito en la CDMX.",
  "tipo": "documentos",
  "documentos": [
    { "tipo": "REGLAMENTO", "titulo": "Reglamento de Tránsito de la CDMX", "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/reglamentos/REGLAMENTO_DE_TRANSITO_DE_LA_CIUDAD_DE_MEXICO_6.1.pdf" },
    { "tipo": "LEY", "titulo": "Ley de Movilidad de la CDMX", "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_MOVILIDAD_DE_LA_CDMX_3.2.pdf" },
    { "tipo": "LEY", "titulo": "Ley de Cultura Cívica en la CDMX", "url": "https://www.congresocdmx.gob.mx/media/documentos/49a0a80ee030f12d0f797c671da2918e508f30cb.pdf" },
    { "tipo": "LEY", "titulo": "Ley de Procedimiento Administrativo en la CDMX", "url": "https://data.consejeria.cdmx.gob.mx/images/leyes/leyes/LEY_DE_PROCEDIMIENTO_ADMINISTRATIVO_DE_LA_CDMX_1.1.pdf" },
    { "tipo": "ACUERDO", "titulo": "Lista de agentes facultados para infraccionar sobre vía pública en la CDMX", "url": "https://www.ssc.cdmx.gob.mx/storage/app/media/Transito/Actualizaciones/Acuedo-40-2024.pdf" }
  ],
  "fuentes": [],
  "actualizado": "2026-10",
  "keywords": ["reglamento", "ley de movilidad", "ley de cultura cívica", "ley de procedimiento administrativo", "marco legal", "agentes facultados"],
  "published": true
}
```

Generic shape for a normal prose article (for when future categories publish
real content):

```json
{
  "titulo": "...",
  "categoria": "<categoria-slug>",
  "slug": "...",
  "resumen": "...",
  "tipo": "prosa",
  "cuerpo": "<rich text / markdown-ish string>",
  "mito_realidad": [{ "mito": "...", "realidad": "..." }],
  "fuentes": [{ "nombre": "...", "url": "..." }],
  "actualizado": "YYYY-MM",
  "keywords": ["..."],
  "published": false
}
```

`GuiaArticulo` switches rendering by `tipo`: `"documentos"` → document-row
list (category 01 today); `"prosa"` → body text, plus a `mito_realidad` block
if present (category 14, once published). `glosario` (15) and `directorio`
(16) will likely need their own `tipo` variants when they get real content —
noted for later, not built now.

### `herramientas.json`

The two calculators don't fit the article shape (no body prose, no real
"fuentes" in the article sense) — separate file:

```json
[
  { "id": "uma-a-pesos", "slug": "uma-a-pesos", "titulo": "UMA → pesos", "descripcion": "Convierte un monto en UMA a pesos mexicanos.", "published": false },
  { "id": "cuando-verifico", "slug": "cuando-verifico", "titulo": "¿Cuándo verifico?", "descripcion": "Encuentra tu periodo de verificación según el último dígito de tu placa.", "published": false }
]
```

### `config/uma.json` and `config/verificacion.json`

Placeholder shape only — no fabricated official values:

```json
// uma.json
{ "valorDiario": null, "anio": null, "fuente": null }
```

```json
// verificacion.json
{ "calendario": [], "fuente": null }
```

Both calculator components are built fully functional against these shapes;
category 17 and both `herramientas.json` entries stay `published: false`
until real values are loaded, per explicit instruction.

## 5. Components

`src/components/guia/` (mirrors the existing `src/components/ui/` grouping
convention):

- `CategoriaCard.js` — one category tile (numero + etiqueta in magenta mono + título).
- `FiltroChips.js` — "Todo, Leyes y derechos, Multas y sanciones, Tu auto, En el camino, Herramientas".
- `BuscadorGuia.js` — client-side text input; matches category `titulo`/`etiqueta` and article `titulo`/`keywords`/`resumen`, case/accent-insensitive substring match. No new dependency — plain string normalization.
- `UmaCalculadora.js` / `VerificacionCalculadora.js` — the two tool widgets, rendered by `GuiaCalculadora`.

`src/pages/`: `GuiaCategoria.js`, `GuiaArticulo.js`, `GuiaCalculadora.js`.

## 6. `Bienvenida.js` changes

- `servicios[1]` ("Guías y recursos legales") becomes a distinct, richer card: mono label `02 · RECURSOS` (magenta), title "Guía del conductor", description "Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto en la CDMX.", CTA "Explorar →". This card visually diverges from its two siblings (which stay the plain image cards) — confirmed intentional.
- The `documentosRef` section is replaced by the `#guia` section: header (label "02 · RECURSOS", serif title "Guía del conductor" with "en la CDMX" in magenta, short description), `BuscadorGuia`, `FiltroChips`, and the category grid (`CategoriaCard` per published category, grouped/sortable by `bloque`).
- Styling for the new card content and the `#guia` section uses Tailwind (`tw-` prefix), reusing `tailwind.config.js` tokens (`azul`, `magenta`, `ink`, `ink-soft`, `paper`, `rule`, fonts `display`/`sans`/`mono`) — consistent with `Home.js`, even though the rest of `Bienvenida.js` remains Bootstrap/CSS-module styled. This creates one Tailwind "island" inside an otherwise Bootstrap page; acceptable and scoped to the touched elements only.
- Mobile: single-column grid, per existing requirement.

## 7. Testing / verification

No existing frontend automated test suite to extend (CRA scaffolding only,
unused). Verification is manual, via Playwright against the running dev
server, covering:

- No new console errors on `/Bienvenida`, `/guia/marco-juridico`, `/guia/marco-juridico/marco-juridico`.
- Card 02's smooth-scroll to `#guia` still works.
- Search/filter narrows the grid correctly; clearing search/"Todo" chip restores it.
- Keyboard navigation: tab reaches the search input, filter chips, and category cards in a sane order; Enter/Space activate a focused chip/card.
- `npm run build` stays clean (no new lint errors beyond the pre-existing, unrelated ones already present in the repo).

## 8. Explicitly deferred (not built this pass)

- Any link to the guide from `/Home` or anywhere outside `/Bienvenida`.
- Real content for categories 02–17 and both calculator config files — scaffolding only.
- `glosario`/`directorio` body-variant rendering (`tipo` values) — designed for, not implemented, since no content exists yet to drive their shape.
