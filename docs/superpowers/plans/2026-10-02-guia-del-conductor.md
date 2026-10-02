# Guía del conductor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a data-driven "Guía del conductor" reference library (search + 17 categories + article template + two calculators) reachable only from the logged-in `/Bienvenida` page.

**Architecture:** A pure-logic content layer (`src/content/guia/` JSON files + `src/services/guiaService.js`) feeds three new `RutaProtegida`-wrapped React Router routes (`/guia/:categoriaSlug`, `/guia/:categoriaSlug/:articuloSlug`, `/guia/calculadoras/:herramientaSlug`) plus a search/filter/grid section embedded directly in `Bienvenida.js`. Only category 01 ("Marco jurídico") ships with real, published content; everything else is complete scaffolding waiting on real copy.

**Tech Stack:** React 19, react-router-dom v7 (already in use), Tailwind (`tw-` prefix, existing tokens in `frontend/tailwind.config.js`), CRA/`react-scripts` (Jest + `@testing-library/*` already installed but unused), no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-02-guia-del-conductor-design.md`

## Global Constraints

- Every new route (`/guia/:categoriaSlug`, `/guia/:categoriaSlug/:articuloSlug`, `/guia/calculadoras/:herramientaSlug`) is wrapped in `RutaProtegida` — no public access, no exceptions.
- No link to the guide exists anywhere outside `/Bienvenida` (not in `NavBar2`, not on `/Home`) — confirmed, deliberate.
- Zero hardcoded copy in components — all category/article/tool text lives in `src/content/guia/*.json`.
- Only `published: true` items render in listings (the `#guia` grid, `GuiaCategoria`'s article list). Never show an empty-category tile or a "Próximamente" placeholder in a listing.
- Category 01 "Marco jurídico" is the only category with `published: true` today. Categories 02–17 and both `herramientas.json` entries stay `published: false` — do not invent legal content, UMA values, or a verification calendar.
- Reuse existing Tailwind tokens only (`azul #1C3F94`, `magenta #C4005F`, `ink #16181D`, `ink-soft #52544D`, `paper`, `paper-raised`, `rule`, `gris`, fonts `display`/`sans`/`mono`) — no new design tokens.
- `/Bienvenida`'s touched parts (card 02, `#guia` section) stay functional and data-driven but are **not** a polish target — the whole page is slated for a separate future rework (user confirmed 2026-10-02). The new dedicated pages (`GuiaCategoria`, `GuiaArticulo`, `GuiaCalculadora`) get normal design-quality treatment since they won't be redone.
- No existing frontend automated test suite beyond CRA's unused scaffolding. Pure-logic modules (`guiaService.js`, the two calculator utils) get real Jest unit tests (already-installed tooling, no config changes). Pages/components are verified manually via Playwright against the running dev server — per the approved spec, do not introduce a parallel component-testing track.
- `require.context` (standard webpack/CRA feature, already relied on nowhere else in this repo but requires no new dependency) auto-discovers article JSON files. Jest cannot execute `require.context`, so it lives in one small untested glue file (`loadArticulos.js`) — the pure query functions in `guiaService.js` take the loaded data as a default parameter, so tests pass fixtures directly and never touch `require.context`.

## Review Focus

- **Direct URL to an unpublished *article*** (e.g. a future `/guia/multas-y-fotocivicas/un-borrador`) — must render a clear "not found" page, never a half-built or blank page. `getArticuloPorSlug` filters on `published`; covered in Task 2's unit tests and Task 4's manual check.
- **Direct URL to a category with zero published articles** (e.g. `/guia/multas-y-fotocivicas` today) — must show a graceful "aún no hay contenido" message, not crash and not silently render nothing. Covered in Task 5.
- **Search with no matches** — must show an explicit "no encontramos..." message in the `#guia` grid, never a silently empty grid that looks broken. Covered in Task 7.
- **Logged-out access to any of the three new routes** — must redirect to `/Login` via `RutaProtegida`, exactly like every other `/Bienvenida` sub-route. Covered in Task 8.
- **Calculator used against the still-`null` placeholder config** (`uma.json`'s `valorDiario: null`, `verificacion.json`'s empty `calendario`) — must show a "sin datos oficiales todavía" message, never `NaN`, `undefined`, or a thrown error. Covered in Task 3 (pure function) and Task 6 (page).

---

### Task 1: Guía content data files

**Files:**
- Create: `frontend/src/content/guia/categorias.json`
- Create: `frontend/src/content/guia/articulos/marco-juridico.json`
- Create: `frontend/src/content/guia/herramientas.json`
- Create: `frontend/src/content/guia/config/uma.json`
- Create: `frontend/src/content/guia/config/verificacion.json`

**Interfaces:**
- Produces: the on-disk JSON shapes every later task reads. `categorias.json` is an array of `{ id, numero, etiqueta, titulo, bloque, slug, orden, published }`. An article file is `{ titulo, categoria, slug, resumen, tipo, documentos?, cuerpo?, mito_realidad?, fuentes, actualizado, keywords, published }`. `herramientas.json` is an array of `{ id, slug, titulo, descripcion, published }`.

- [ ] **Step 1: Create `categorias.json`**

```json
[
  { "id": "01", "numero": "01", "etiqueta": "LEYES", "titulo": "Marco jurídico", "bloque": "Leyes y derechos", "slug": "marco-juridico", "orden": 1, "published": true },
  { "id": "02", "numero": "02", "etiqueta": "DERECHOS", "titulo": "Si te detiene un agente", "bloque": "Leyes y derechos", "slug": "si-te-detiene-un-agente", "orden": 2, "published": false },
  { "id": "03", "numero": "03", "etiqueta": "MULTAS", "titulo": "Multas y fotocívicas", "bloque": "Multas y sanciones", "slug": "multas-y-fotocivicas", "orden": 3, "published": false },
  { "id": "04", "numero": "04", "etiqueta": "CORRALÓN", "titulo": "Tu auto en el corralón", "bloque": "Multas y sanciones", "slug": "tu-auto-en-el-corralon", "orden": 4, "published": false },
  { "id": "05", "numero": "05", "etiqueta": "COMPRA", "titulo": "Comprar un auto usado", "bloque": "Tu auto", "slug": "comprar-auto-usado", "orden": 5, "published": false },
  { "id": "06", "numero": "06", "etiqueta": "COMPRA", "titulo": "Comprar un auto nuevo", "bloque": "Tu auto", "slug": "comprar-auto-nuevo", "orden": 6, "published": false },
  { "id": "07", "numero": "07", "etiqueta": "VENTA", "titulo": "Vender tu auto", "bloque": "Tu auto", "slug": "vender-tu-auto", "orden": 7, "published": false },
  { "id": "08", "numero": "08", "etiqueta": "TRÁMITES", "titulo": "Trámites vehiculares", "bloque": "Tu auto", "slug": "tramites-vehiculares", "orden": 8, "published": false },
  { "id": "09", "numero": "09", "etiqueta": "AMBIENTE", "titulo": "Verificación y Hoy No Circula", "bloque": "Tu auto", "slug": "verificacion-y-hoy-no-circula", "orden": 9, "published": false },
  { "id": "10", "numero": "10", "etiqueta": "SEGUROS", "titulo": "Seguros", "bloque": "Tu auto", "slug": "seguros", "orden": 10, "published": false },
  { "id": "11", "numero": "11", "etiqueta": "ACCIDENTES", "titulo": "Si chocas", "bloque": "En el camino", "slug": "si-chocas", "orden": 11, "published": false },
  { "id": "12", "numero": "12", "etiqueta": "ALCOHOL", "titulo": "Alcoholímetro", "bloque": "Leyes y derechos", "slug": "alcoholimetro", "orden": 12, "published": false },
  { "id": "13", "numero": "13", "etiqueta": "MOVILIDAD", "titulo": "Motos, bicis y peatones", "bloque": "En el camino", "slug": "motos-bicis-y-peatones", "orden": 13, "published": false },
  { "id": "14", "numero": "14", "etiqueta": "MITOS", "titulo": "Mitos vs realidad", "bloque": "Leyes y derechos", "slug": "mitos-vs-realidad", "orden": 14, "published": false },
  { "id": "15", "numero": "15", "etiqueta": "GLOSARIO", "titulo": "Glosario", "bloque": "Herramientas", "slug": "glosario", "orden": 15, "published": false },
  { "id": "16", "numero": "16", "etiqueta": "CONTACTO", "titulo": "Directorio oficial", "bloque": "Herramientas", "slug": "directorio-oficial", "orden": 16, "published": false },
  { "id": "17", "numero": "17", "etiqueta": "CÁLCULO", "titulo": "Calculadoras", "bloque": "Herramientas", "slug": "calculadoras", "orden": 17, "published": false }
]
```

- [ ] **Step 2: Create `articulos/marco-juridico.json`**

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
  "keywords": ["reglamento", "ley de movilidad", "ley de cultura cívica", "ley de procedimiento administrativo", "marco legal", "agentes facultados", "acuerdo"],
  "published": true
}
```

- [ ] **Step 3: Create `herramientas.json`**

```json
[
  { "id": "uma-a-pesos", "slug": "uma-a-pesos", "titulo": "UMA → pesos", "descripcion": "Convierte un monto en UMA a pesos mexicanos.", "published": false },
  { "id": "cuando-verifico", "slug": "cuando-verifico", "titulo": "¿Cuándo verifico?", "descripcion": "Encuentra tu periodo de verificación según el último dígito de tu placa.", "published": false }
]
```

- [ ] **Step 4: Create `config/uma.json` and `config/verificacion.json`**

```json
{ "valorDiario": null, "anio": null, "fuente": null }
```

```json
{ "calendario": [], "fuente": null }
```

- [ ] **Step 5: Verify all five files are valid JSON**

Run (from `frontend/`):
```bash
node -e "['src/content/guia/categorias.json','src/content/guia/articulos/marco-juridico.json','src/content/guia/herramientas.json','src/content/guia/config/uma.json','src/content/guia/config/verificacion.json'].forEach(f => { JSON.parse(require('fs').readFileSync(f, 'utf8')); console.log(f, 'OK'); })"
```
Expected: five lines ending in `OK`, no errors.

Run:
```bash
node -e "console.log(require('./src/content/guia/categorias.json').length)"
```
Expected: `17`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/content/guia/categorias.json frontend/src/content/guia/articulos/marco-juridico.json frontend/src/content/guia/herramientas.json frontend/src/content/guia/config/uma.json frontend/src/content/guia/config/verificacion.json
git commit -m "feat: add guía del conductor content data files"
```

---

### Task 2: `guiaService.js` data-access layer

**Files:**
- Create: `frontend/src/content/guia/loadArticulos.js`
- Create: `frontend/src/services/guiaService.js`
- Test: `frontend/src/services/__tests__/guiaService.test.js`

**Interfaces:**
- Consumes: `categorias.json`, `herramientas.json` (Task 1, plain `import`), `loadArticulos.js`'s `cargarArticulos()`.
- Produces (used by Tasks 4, 5, 6, 7): `getCategoriasPublicadas(categorias?)`, `getCategoriaPorSlug(slug, categorias?)`, `getArticulosPorCategoria(categoriaSlug, articulos?)`, `getArticuloPorSlug(categoriaSlug, articuloSlug, articulos?)`, `getHerramientas(herramientas?)`, `getHerramientaPorSlug(slug, herramientas?)`, `buscarEnGuia(query, categorias?, articulos?)`. Every optional parameter defaults to the real on-disk data — callers in page components call these with just the required arguments (e.g. `getCategoriaPorSlug(categoriaSlug)`); tests pass fixture arrays explicitly.

- [ ] **Step 1: Create the untested `require.context` glue file**

`frontend/src/content/guia/loadArticulos.js`:
```js
// require.context is a webpack-only API — Jest can't execute it, so this
// file stays a thin, untested wrapper. guiaService.js's pure functions take
// the loaded data as a parameter, so they're testable without touching this.
const articuloModules = require.context('./articulos', false, /\.json$/);

export function cargarArticulos() {
    return articuloModules.keys().map((key) => articuloModules(key));
}
```

- [ ] **Step 2: Write the failing tests for `guiaService.js`**

`frontend/src/services/__tests__/guiaService.test.js`:
```js
import {
    getCategoriasPublicadas,
    getCategoriaPorSlug,
    getArticulosPorCategoria,
    getArticuloPorSlug,
    getHerramientas,
    getHerramientaPorSlug,
    buscarEnGuia,
} from '../guiaService';

const categoriasFixture = [
    { id: '01', numero: '01', etiqueta: 'LEYES', titulo: 'Marco jurídico', bloque: 'Leyes y derechos', slug: 'marco-juridico', orden: 1, published: true },
    { id: '02', numero: '02', etiqueta: 'DERECHOS', titulo: 'Si te detiene un agente', bloque: 'Leyes y derechos', slug: 'si-te-detiene-un-agente', orden: 2, published: false },
];

const articulosFixture = [
    {
        titulo: 'Marco jurídico', categoria: 'marco-juridico', slug: 'marco-juridico',
        resumen: 'Los cinco documentos oficiales.', tipo: 'documentos', documentos: [], fuentes: [],
        actualizado: '2026-10', keywords: ['reglamento', 'ley de movilidad'], published: true,
    },
    {
        titulo: 'Artículo sin publicar', categoria: 'marco-juridico', slug: 'borrador',
        resumen: 'Todavía no.', tipo: 'prosa', cuerpo: '...', fuentes: [],
        actualizado: '2026-10', keywords: [], published: false,
    },
];

const herramientasFixture = [
    { id: 'uma-a-pesos', slug: 'uma-a-pesos', titulo: 'UMA → pesos', descripcion: '...', published: false },
];

describe('getCategoriasPublicadas', () => {
    it('returns only published categories sorted by orden', () => {
        const resultado = getCategoriasPublicadas(categoriasFixture);
        expect(resultado).toHaveLength(1);
        expect(resultado[0].slug).toBe('marco-juridico');
    });
});

describe('getCategoriaPorSlug', () => {
    it('finds a category by slug regardless of published status', () => {
        expect(getCategoriaPorSlug('si-te-detiene-un-agente', categoriasFixture)?.titulo).toBe('Si te detiene un agente');
    });

    it('returns null for an unknown slug', () => {
        expect(getCategoriaPorSlug('no-existe', categoriasFixture)).toBeNull();
    });
});

describe('getArticulosPorCategoria', () => {
    it('returns only published articles for the category', () => {
        const resultado = getArticulosPorCategoria('marco-juridico', articulosFixture);
        expect(resultado).toHaveLength(1);
        expect(resultado[0].slug).toBe('marco-juridico');
    });
});

describe('getArticuloPorSlug', () => {
    it('returns the published article matching category and slug', () => {
        const articulo = getArticuloPorSlug('marco-juridico', 'marco-juridico', articulosFixture);
        expect(articulo?.titulo).toBe('Marco jurídico');
    });

    it('returns null for an unpublished article (treated as not found)', () => {
        expect(getArticuloPorSlug('marco-juridico', 'borrador', articulosFixture)).toBeNull();
    });

    it('returns null when the category does not match', () => {
        expect(getArticuloPorSlug('otra-categoria', 'marco-juridico', articulosFixture)).toBeNull();
    });
});

describe('getHerramientas', () => {
    it('returns only published tools', () => {
        expect(getHerramientas(herramientasFixture)).toHaveLength(0);
    });
});

describe('getHerramientaPorSlug', () => {
    it('finds a tool by slug even when unpublished', () => {
        expect(getHerramientaPorSlug('uma-a-pesos', herramientasFixture)?.titulo).toBe('UMA → pesos');
    });

    it('returns null for an unknown tool slug', () => {
        expect(getHerramientaPorSlug('no-existe', herramientasFixture)).toBeNull();
    });
});

describe('buscarEnGuia', () => {
    it('returns all published categories when the query is empty', () => {
        expect(buscarEnGuia('', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('matches by category title, case and accent insensitive', () => {
        expect(buscarEnGuia('JURIDICO', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('matches a category through one of its article keywords', () => {
        expect(buscarEnGuia('reglamento', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('returns an empty list when nothing matches', () => {
        expect(buscarEnGuia('xyz-no-existe', categoriasFixture, articulosFixture)).toHaveLength(0);
    });

    it('never returns an unpublished category even if its title matches', () => {
        expect(buscarEnGuia('detiene', categoriasFixture, articulosFixture)).toHaveLength(0);
    });
});
```

- [ ] **Step 3: Run the tests to verify they fail**

Run (from `frontend/`): `CI=true npx react-scripts test src/services/__tests__/guiaService.test.js --watchAll=false`
Expected: FAIL — `Cannot find module '../guiaService'`.

- [ ] **Step 4: Implement `guiaService.js`**

`frontend/src/services/guiaService.js`:
```js
import categoriasData from '../content/guia/categorias.json';
import herramientasData from '../content/guia/herramientas.json';
import { cargarArticulos } from '../content/guia/loadArticulos';

const articulosData = cargarArticulos();

const normalizar = (texto) =>
    (texto || '')
        .toString()
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toLowerCase();

export function getCategoriasPublicadas(categorias = categoriasData) {
    return categorias
        .filter((categoria) => categoria.published)
        .slice()
        .sort((a, b) => a.orden - b.orden);
}

export function getCategoriaPorSlug(slug, categorias = categoriasData) {
    return categorias.find((categoria) => categoria.slug === slug) || null;
}

export function getArticulosPorCategoria(categoriaSlug, articulos = articulosData) {
    return articulos
        .filter((articulo) => articulo.categoria === categoriaSlug && articulo.published)
        .slice()
        .sort((a, b) => a.titulo.localeCompare(b.titulo));
}

export function getArticuloPorSlug(categoriaSlug, articuloSlug, articulos = articulosData) {
    return (
        articulos.find(
            (articulo) =>
                articulo.categoria === categoriaSlug &&
                articulo.slug === articuloSlug &&
                articulo.published
        ) || null
    );
}

export function getHerramientas(herramientas = herramientasData) {
    return herramientas.filter((herramienta) => herramienta.published);
}

export function getHerramientaPorSlug(slug, herramientas = herramientasData) {
    // Unlike articles, a tool is safe to reach directly even while unpublished:
    // the UI always falls back to a "sin datos oficiales todavía" state (see
    // UmaCalculadora/VerificacionCalculadora in Task 6) — it never shows a
    // fabricated number, so there's no fabrication risk in exposing the route.
    return herramientas.find((herramienta) => herramienta.slug === slug) || null;
}

export function buscarEnGuia(query, categorias = categoriasData, articulos = articulosData) {
    const normalizada = normalizar(query);
    const categoriasPublicadas = getCategoriasPublicadas(categorias);

    if (!normalizada) {
        return categoriasPublicadas;
    }

    return categoriasPublicadas.filter((categoria) => {
        const coincideCategoria = [categoria.titulo, categoria.etiqueta].some((campo) =>
            normalizar(campo).includes(normalizada)
        );
        if (coincideCategoria) return true;

        return getArticulosPorCategoria(categoria.slug, articulos).some((articulo) =>
            [articulo.titulo, articulo.resumen, ...(articulo.keywords || [])].some((campo) =>
                normalizar(campo).includes(normalizada)
            )
        );
    });
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `CI=true npx react-scripts test src/services/__tests__/guiaService.test.js --watchAll=false`
Expected: PASS — all 13 tests green.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/content/guia/loadArticulos.js frontend/src/services/guiaService.js frontend/src/services/__tests__/guiaService.test.js
git commit -m "feat: add guía del conductor data-access service"
```

---

### Task 3: Calculator pure-logic utilities

**Files:**
- Create: `frontend/src/utils/umaCalculator.js`
- Create: `frontend/src/utils/verificacionCalculator.js`
- Test: `frontend/src/utils/__tests__/umaCalculator.test.js`
- Test: `frontend/src/utils/__tests__/verificacionCalculator.test.js`

**Interfaces:**
- Produces (used by Task 6's calculator components): `convertirUmaAPesos(cantidadUma, valorDiario) => number | null`, `obtenerPeriodoVerificacion(ultimoDigito, calendario) => { digitos: number[], periodo: string, color: string } | null`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/utils/__tests__/umaCalculator.test.js`:
```js
import { convertirUmaAPesos } from '../umaCalculator';

describe('convertirUmaAPesos', () => {
    it('multiplies the UMA quantity by the daily value', () => {
        expect(convertirUmaAPesos(10, 108.57)).toBeCloseTo(1085.7);
    });

    it('returns null when the official daily value is not loaded yet', () => {
        expect(convertirUmaAPesos(10, null)).toBeNull();
    });

    it('returns null for a non-numeric quantity', () => {
        expect(convertirUmaAPesos('abc', 108.57)).toBeNull();
    });

    it('returns 0 for a zero quantity', () => {
        expect(convertirUmaAPesos(0, 108.57)).toBe(0);
    });
});
```

`frontend/src/utils/__tests__/verificacionCalculator.test.js`:
```js
import { obtenerPeriodoVerificacion } from '../verificacionCalculator';

const calendarioFixture = [
    { digitos: [5, 6], periodo: 'Enero-Febrero', color: 'Amarillo' },
    { digitos: [7, 8], periodo: 'Marzo-Abril', color: 'Rosa' },
];

describe('obtenerPeriodoVerificacion', () => {
    it('finds the period matching the last digit', () => {
        expect(obtenerPeriodoVerificacion(5, calendarioFixture)).toEqual(calendarioFixture[0]);
    });

    it('returns null when the calendar has not been loaded yet', () => {
        expect(obtenerPeriodoVerificacion(5, [])).toBeNull();
    });

    it('returns null for a digit outside 0-9', () => {
        expect(obtenerPeriodoVerificacion(15, calendarioFixture)).toBeNull();
    });

    it('returns null for a non-numeric digit', () => {
        expect(obtenerPeriodoVerificacion('x', calendarioFixture)).toBeNull();
    });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `CI=true npx react-scripts test src/utils/__tests__ --watchAll=false`
Expected: FAIL — `Cannot find module '../umaCalculator'` / `'../verificacionCalculator'`.

- [ ] **Step 3: Implement both utilities**

`frontend/src/utils/umaCalculator.js`:
```js
export function convertirUmaAPesos(cantidadUma, valorDiario) {
    if (valorDiario === null || valorDiario === undefined) {
        return null;
    }
    const cantidad = Number(cantidadUma);
    if (Number.isNaN(cantidad)) {
        return null;
    }
    return cantidad * Number(valorDiario);
}
```

`frontend/src/utils/verificacionCalculator.js`:
```js
export function obtenerPeriodoVerificacion(ultimoDigito, calendario) {
    if (!Array.isArray(calendario) || calendario.length === 0) {
        return null;
    }
    const digito = Number(ultimoDigito);
    if (Number.isNaN(digito) || digito < 0 || digito > 9) {
        return null;
    }
    return calendario.find((entrada) => entrada.digitos.includes(digito)) || null;
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `CI=true npx react-scripts test src/utils/__tests__ --watchAll=false`
Expected: PASS — all 8 tests green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/umaCalculator.js frontend/src/utils/verificacionCalculator.js frontend/src/utils/__tests__/umaCalculator.test.js frontend/src/utils/__tests__/verificacionCalculator.test.js
git commit -m "feat: add guía del conductor calculator utilities"
```

---

### Task 4: `GuiaArticulo` page and route

**Files:**
- Create: `frontend/src/pages/GuiaArticulo.js`
- Modify: `frontend/src/App.js` (add import + route)

**Interfaces:**
- Consumes: `getCategoriaPorSlug`, `getArticuloPorSlug` (Task 2).
- Produces: the `/guia/:categoriaSlug/:articuloSlug` route, reused as-is by Task 7's category cards and Task 8's smoke test.

- [ ] **Step 1: Create `GuiaArticulo.js`**

`frontend/src/pages/GuiaArticulo.js`:
```jsx
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getArticuloPorSlug, getCategoriaPorSlug } from '../services/guiaService';

const GuiaArticulo = () => {
    const { categoriaSlug, articuloSlug } = useParams();
    const categoria = getCategoriaPorSlug(categoriaSlug);
    const articulo = getArticuloPorSlug(categoriaSlug, articuloSlug);

    if (!categoria || !articulo) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">
                            404
                        </p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos este artículo
                        </h1>
                        <p className="tw-text-ink-soft tw-mb-6">
                            Puede que el contenido todavía no esté publicado o que la dirección sea incorrecta.
                        </p>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
                    <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                        {categoria.numero} · {categoria.etiqueta}
                    </span>
                    <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-2">
                        {articulo.titulo}
                    </h1>
                    <p className="tw-font-mono tw-text-[12px] tw-text-ink-soft tw-mb-8">
                        Actualizado: {articulo.actualizado}
                        {articulo.fuentes && articulo.fuentes.length > 0 && (
                            <> · Fuente: {articulo.fuentes.map((f) => f.nombre).join(', ')}</>
                        )}
                    </p>

                    {articulo.tipo === 'documentos' && articulo.documentos && (
                        <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-3 tw-mb-10">
                            {articulo.documentos.map((doc) => (
                                <li
                                    key={doc.url}
                                    className="tw-flex tw-flex-wrap tw-items-center tw-gap-3 tw-border tw-border-rule tw-rounded tw-px-4 tw-py-3.5"
                                >
                                    <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-magenta tw-bg-magenta/10 tw-rounded tw-px-2 tw-py-1">
                                        {doc.tipo}
                                    </span>
                                    <span className="tw-flex-1 tw-min-w-[200px] tw-text-ink tw-font-semibold tw-text-sm">
                                        {doc.titulo}
                                    </span>
                                    <a
                                        href={doc.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="tw-text-azul hover:tw-text-magenta tw-text-sm tw-font-bold tw-no-underline"
                                    >
                                        PDF ↗
                                    </a>
                                </li>
                            ))}
                        </ul>
                    )}

                    {articulo.tipo === 'prosa' && (
                        <div className="tw-text-ink tw-leading-relaxed tw-mb-10 tw-whitespace-pre-line">
                            {articulo.cuerpo}
                        </div>
                    )}

                    {articulo.mito_realidad && articulo.mito_realidad.length > 0 && (
                        <div className="tw-flex tw-flex-col tw-gap-4 tw-mb-10">
                            {articulo.mito_realidad.map((par, index) => (
                                <div key={index} className="tw-border tw-border-rule tw-rounded tw-overflow-hidden">
                                    <div className="tw-bg-magenta/10 tw-px-4 tw-py-3">
                                        <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-magenta">MITO</span>
                                        <p className="tw-text-ink tw-text-sm tw-m-0 tw-mt-1">{par.mito}</p>
                                    </div>
                                    <div className="tw-bg-verde/10 tw-px-4 tw-py-3">
                                        <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-verde">REALIDAD</span>
                                        <p className="tw-text-ink tw-text-sm tw-m-0 tw-mt-1">{par.realidad}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {articulo.fuentes && articulo.fuentes.length > 0 && (
                        <div className="tw-border-t tw-border-rule tw-pt-6 tw-mb-10">
                            <p className="tw-font-semibold tw-text-ink tw-text-sm tw-mb-3">Fuentes</p>
                            <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-2">
                                {articulo.fuentes.map((fuente) => (
                                    <li key={fuente.url}>
                                        <a href={fuente.url} target="_blank" rel="noopener noreferrer" className="tw-text-azul hover:tw-text-magenta tw-text-sm">
                                            {fuente.nombre}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <Link
                        to="/asesoria-ia"
                        className="tw-inline-flex tw-items-center tw-gap-2 tw-bg-ink tw-text-white tw-font-semibold tw-text-sm tw-rounded tw-px-5 tw-py-2.5 tw-no-underline hover:tw-bg-ink/90"
                    >
                        ¿Dudas? Pregúntale a la IA legal →
                    </Link>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default GuiaArticulo;
```

- [ ] **Step 2: Wire the route in `App.js`**

Modify `frontend/src/App.js`. Add this import next to the existing `ConsultarAgenteTransito` import (around line 16):
```jsx
import GuiaArticulo from "./pages/GuiaArticulo"
```

Add this route next to the existing `/ConsultarAgenteTransito` route (around line 38):
```jsx
<Route path="/guia/:categoriaSlug/:articuloSlug" element={<RutaProtegida> <GuiaArticulo /> </RutaProtegida>} />
```

- [ ] **Step 3: Manually verify with Playwright**

With the dev server running and logged in (an existing session or a freshly registered+logged-in account):
1. Navigate to `/guia/marco-juridico/marco-juridico`.
2. Confirm the page shows: label "01 · LEYES", title "Marco jurídico", "Actualizado: 2026-10", and 5 document rows each with a type badge (REGLAMENTO/LEY/LEY/LEY/ACUERDO), the correct titles, and a working "PDF ↗" link (`target="_blank"`).
3. Confirm the "¿Dudas? Pregúntale a la IA legal →" link's `href` resolves to `/asesoria-ia`.
4. Navigate to `/guia/marco-juridico/no-existe` (an article slug that doesn't exist) — confirm the 404 message renders instead of a blank/broken page, and the "← Volver a Bienvenida" link works.
5. Open the browser console — confirm zero errors on both URLs.
6. Log out, navigate directly to `/guia/marco-juridico/marco-juridico` — confirm it redirects to `/Login` (via `RutaProtegida`).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/GuiaArticulo.js frontend/src/App.js
git commit -m "feat: add guía del conductor article page"
```

---

### Task 5: `GuiaCategoria` page and route

**Files:**
- Create: `frontend/src/pages/GuiaCategoria.js`
- Modify: `frontend/src/App.js` (add import + route)

**Interfaces:**
- Consumes: `getCategoriaPorSlug`, `getArticulosPorCategoria`, `getHerramientas` (Task 2).
- Produces: the `/guia/:categoriaSlug` route, linked from Task 7's category grid.

- [ ] **Step 1: Create `GuiaCategoria.js`**

`frontend/src/pages/GuiaCategoria.js`:
```jsx
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getCategoriaPorSlug, getArticulosPorCategoria, getHerramientas } from '../services/guiaService';

const GuiaCategoria = () => {
    const { categoriaSlug } = useParams();
    const categoria = getCategoriaPorSlug(categoriaSlug);

    if (!categoria || !categoria.published) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">404</p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos esta categoría
                        </h1>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    const esCalculadoras = categoria.slug === 'calculadoras';
    const items = esCalculadoras ? getHerramientas() : getArticulosPorCategoria(categoriaSlug);

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
                    <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                        {categoria.numero} · {categoria.etiqueta}
                    </span>
                    <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-8">
                        {categoria.titulo}
                    </h1>

                    {items.length === 0 && (
                        <p className="tw-text-ink-soft tw-text-sm">
                            Aún no hay contenido publicado en esta categoría.
                        </p>
                    )}

                    <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-3">
                        {items.map((item) => (
                            <li key={item.slug}>
                                <Link
                                    to={esCalculadoras ? `/guia/calculadoras/${item.slug}` : `/guia/${categoriaSlug}/${item.slug}`}
                                    className="tw-block tw-border tw-border-rule tw-rounded tw-px-4 tw-py-3.5 tw-no-underline tw-text-inherit hover:tw-bg-paper tw-transition-colors"
                                >
                                    <span className="tw-block tw-text-ink tw-font-semibold tw-text-sm">
                                        {item.titulo}
                                    </span>
                                    {(item.resumen || item.descripcion) && (
                                        <span className="tw-block tw-text-ink-soft tw-text-sm tw-mt-1">
                                            {item.resumen || item.descripcion}
                                        </span>
                                    )}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default GuiaCategoria;
```

- [ ] **Step 2: Wire the route in `App.js`**

Add this import next to Task 4's:
```jsx
import GuiaCategoria from "./pages/GuiaCategoria"
```

Add this route next to Task 4's route:
```jsx
<Route path="/guia/:categoriaSlug" element={<RutaProtegida> <GuiaCategoria /> </RutaProtegida>} />
```

- [ ] **Step 3: Manually verify with Playwright**

Logged in:
1. Navigate to `/guia/marco-juridico` — confirm it lists one item, "Marco jurídico", linking to `/guia/marco-juridico/marco-juridico`; click it and confirm it lands on Task 4's article page.
2. Navigate to `/guia/multas-y-fotocivicas` (a published-category-with-zero-articles case — this category itself is `published: false`, so this should hit the category-level 404, not an empty list — confirms the `!categoria.published` branch). Confirm the "No encontramos esta categoría" message renders, not a blank/broken page.
3. Navigate to `/guia/calculadoras` — category 17 is also `published: false` in `categorias.json` (per the confirmed "only category 01" decision), so this hits the same `!categoria.published` branch as step 2: confirm the "No encontramos esta categoría" message renders, not a crash and not a half-built "coming soon" page. (The `items.length === 0` empty-but-published-category branch this component also handles has no live data to exercise it yet — every currently-published category happens to have at least one published item. That branch is still correct by inspection/construction; it becomes manually verifiable the day a second category publishes before its first article does.)
4. Navigate to `/guia/no-existe` — confirm the "No encontramos esta categoría" 404 page renders.
5. Browser console — zero errors on all four URLs.
6. Logged out, navigate to `/guia/marco-juridico` — confirm redirect to `/Login`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/GuiaCategoria.js frontend/src/App.js
git commit -m "feat: add guía del conductor category listing page"
```

---

### Task 6: Calculator components, `GuiaCalculadora` page, and route

**Files:**
- Create: `frontend/src/components/guia/UmaCalculadora.js`
- Create: `frontend/src/components/guia/VerificacionCalculadora.js`
- Create: `frontend/src/pages/GuiaCalculadora.js`
- Modify: `frontend/src/App.js` (add import + route)

**Interfaces:**
- Consumes: `convertirUmaAPesos`, `obtenerPeriodoVerificacion` (Task 3); `getHerramientaPorSlug` (Task 2); `config/uma.json`, `config/verificacion.json` (Task 1).
- Produces: the `/guia/calculadoras/:herramientaSlug` route.

- [ ] **Step 1: Create `UmaCalculadora.js`**

`frontend/src/components/guia/UmaCalculadora.js`:
```jsx
import React, { useState } from 'react';
import umaConfig from '../../content/guia/config/uma.json';
import { convertirUmaAPesos } from '../../utils/umaCalculator';

const UmaCalculadora = () => {
    const [cantidad, setCantidad] = useState('');
    const sinDatos = umaConfig.valorDiario === null;
    const resultado = sinDatos ? null : convertirUmaAPesos(cantidad, umaConfig.valorDiario);

    if (sinDatos) {
        return (
            <div className="tw-border tw-border-rule tw-rounded tw-p-5">
                <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                    Todavía no tenemos cargado el valor oficial de la UMA. Vuelve pronto.
                </p>
            </div>
        );
    }

    return (
        <div className="tw-border tw-border-rule tw-rounded tw-p-5">
            <label className="tw-block tw-text-sm tw-font-semibold tw-text-ink tw-mb-2" htmlFor="uma-input">
                Cantidad en UMA
            </label>
            <input
                id="uma-input"
                type="number"
                min="0"
                value={cantidad}
                onChange={(e) => setCantidad(e.target.value)}
                className="tw-w-full tw-border tw-border-azul tw-rounded tw-px-3 tw-py-2 tw-font-mono tw-text-azul focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
            />
            <p className="tw-mt-4 tw-text-ink tw-text-lg tw-font-semibold">
                {resultado === null ? '—' : `$${resultado.toLocaleString('es-MX', { minimumFractionDigits: 2 })} MXN`}
            </p>
        </div>
    );
};

export default UmaCalculadora;
```

- [ ] **Step 2: Create `VerificacionCalculadora.js`**

`frontend/src/components/guia/VerificacionCalculadora.js`:
```jsx
import React, { useState } from 'react';
import verificacionConfig from '../../content/guia/config/verificacion.json';
import { obtenerPeriodoVerificacion } from '../../utils/verificacionCalculator';

const VerificacionCalculadora = () => {
    const [digito, setDigito] = useState('');
    const sinDatos = !verificacionConfig.calendario || verificacionConfig.calendario.length === 0;
    const resultado = sinDatos ? null : obtenerPeriodoVerificacion(digito, verificacionConfig.calendario);

    if (sinDatos) {
        return (
            <div className="tw-border tw-border-rule tw-rounded tw-p-5">
                <p className="tw-text-ink-soft tw-text-sm tw-m-0">
                    Todavía no tenemos cargado el calendario oficial de verificación. Vuelve pronto.
                </p>
            </div>
        );
    }

    return (
        <div className="tw-border tw-border-rule tw-rounded tw-p-5">
            <label className="tw-block tw-text-sm tw-font-semibold tw-text-ink tw-mb-2" htmlFor="placa-digito">
                Último dígito de tu placa
            </label>
            <input
                id="placa-digito"
                type="number"
                min="0"
                max="9"
                value={digito}
                onChange={(e) => setDigito(e.target.value)}
                className="tw-w-full tw-border tw-border-azul tw-rounded tw-px-3 tw-py-2 tw-font-mono tw-text-azul focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
            />
            <p className="tw-mt-4 tw-text-ink tw-text-lg tw-font-semibold">
                {resultado ? `${resultado.periodo} · ${resultado.color}` : '—'}
            </p>
        </div>
    );
};

export default VerificacionCalculadora;
```

- [ ] **Step 3: Create `GuiaCalculadora.js`**

`frontend/src/pages/GuiaCalculadora.js`:
```jsx
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getHerramientaPorSlug } from '../services/guiaService';
import UmaCalculadora from '../components/guia/UmaCalculadora';
import VerificacionCalculadora from '../components/guia/VerificacionCalculadora';

const HERRAMIENTAS_COMPONENTES = {
    'uma-a-pesos': UmaCalculadora,
    'cuando-verifico': VerificacionCalculadora,
};

const GuiaCalculadora = () => {
    const { herramientaSlug } = useParams();
    const herramienta = getHerramientaPorSlug(herramientaSlug);
    const Calculadora = HERRAMIENTAS_COMPONENTES[herramientaSlug];

    if (!herramienta || !Calculadora) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">404</p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos esta herramienta
                        </h1>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
                    <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                        17 · CÁLCULO
                    </span>
                    <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-2">
                        {herramienta.titulo}
                    </h1>
                    <p className="tw-text-ink-soft tw-mb-8">{herramienta.descripcion}</p>
                    <Calculadora />
                </div>
            </main>
            <Footer />
        </>
    );
};

export default GuiaCalculadora;
```

- [ ] **Step 4: Wire the route in `App.js`**

Add this import next to Task 5's:
```jsx
import GuiaCalculadora from "./pages/GuiaCalculadora"
```

Add this route **before** Task 5's `/guia/:categoriaSlug` route (the literal `calculadoras` segment is more specific; React Router v7 ranks it correctly regardless of declaration order, but keeping it first matches its specificity for a human reader):
```jsx
<Route path="/guia/calculadoras/:herramientaSlug" element={<RutaProtegida> <GuiaCalculadora /> </RutaProtegida>} />
```

- [ ] **Step 5: Manually verify with Playwright**

Logged in:
1. Navigate directly to `/guia/calculadoras/uma-a-pesos` (works despite `published: false` — see Task 2's `getHerramientaPorSlug` note). Confirm it shows title "UMA → pesos", its description, and the `UmaCalculadora` widget rendering "Todavía no tenemos cargado el valor oficial de la UMA. Vuelve pronto." (since `uma.json`'s `valorDiario` is still `null`) — not a crash, not `NaN`.
2. Navigate to `/guia/calculadoras/cuando-verifico` — confirm the analogous "Todavía no tenemos cargado el calendario oficial de verificación." message.
3. Navigate to `/guia/calculadoras/no-existe` — confirm the 404 message renders.
4. Browser console — zero errors on all three URLs.
5. Logged out, navigate to `/guia/calculadoras/uma-a-pesos` — confirm redirect to `/Login`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/guia/UmaCalculadora.js frontend/src/components/guia/VerificacionCalculadora.js frontend/src/pages/GuiaCalculadora.js frontend/src/App.js
git commit -m "feat: add guía del conductor calculator page"
```

---

### Task 7: `Bienvenida.js` — card 02 and the `#guia` section

**Files:**
- Create: `frontend/src/components/guia/CategoriaCard.js`
- Create: `frontend/src/components/guia/FiltroChips.js`
- Create: `frontend/src/components/guia/BuscadorGuia.js`
- Modify: `frontend/src/pages/Bienvenida.js`

**Interfaces:**
- Consumes: `buscarEnGuia` (Task 2).
- Produces: the only entry point into the whole feature (card 02's CTA + the `#guia` grid's category links, which point to Task 5's `/guia/:categoriaSlug` route).

- [ ] **Step 1: Create `CategoriaCard.js`**

`frontend/src/components/guia/CategoriaCard.js`:
```jsx
import React from 'react';
import { Link } from 'react-router-dom';

const CategoriaCard = ({ categoria }) => (
    <Link
        to={`/guia/${categoria.slug}`}
        className="tw-block tw-bg-paper-raised tw-border tw-border-rule tw-rounded tw-px-5 tw-py-4 tw-no-underline tw-text-inherit hover:tw-border-azul tw-transition-colors"
    >
        <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-1.5">
            {categoria.numero} · {categoria.etiqueta}
        </span>
        <span className="tw-block tw-text-ink tw-font-semibold tw-text-sm">
            {categoria.titulo}
        </span>
    </Link>
);

export default CategoriaCard;
```

- [ ] **Step 2: Create `FiltroChips.js`**

`frontend/src/components/guia/FiltroChips.js`:
```jsx
import React from 'react';

const FiltroChips = ({ bloques, activo, onSelect }) => (
    <div className="tw-flex tw-flex-wrap tw-gap-2 tw-justify-center" role="group" aria-label="Filtrar por bloque">
        {bloques.map((bloque) => (
            <button
                key={bloque}
                type="button"
                onClick={() => onSelect(bloque)}
                aria-pressed={activo === bloque}
                className={`tw-rounded-full tw-px-4 tw-py-1.5 tw-text-sm tw-font-semibold tw-border tw-transition-colors ${
                    activo === bloque
                        ? 'tw-bg-ink tw-text-white tw-border-ink'
                        : 'tw-bg-transparent tw-text-ink tw-border-ink/20 hover:tw-border-ink/50'
                }`}
            >
                {bloque}
            </button>
        ))}
    </div>
);

export default FiltroChips;
```

- [ ] **Step 3: Create `BuscadorGuia.js`**

`frontend/src/components/guia/BuscadorGuia.js`:
```jsx
import React from 'react';

const BuscadorGuia = ({ value, onChange }) => (
    <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Busca por tema, por ejemplo: multas, corralón, seguro…"
        aria-label="Buscar en la guía del conductor"
        className="tw-w-full tw-border tw-border-rule tw-rounded tw-px-4 tw-py-2.5 tw-text-sm focus:tw-outline-none focus:tw-ring-2 focus:tw-ring-azul/30"
    />
);

export default BuscadorGuia;
```

- [ ] **Step 4: Modify `Bienvenida.js`**

Add these imports near the top (next to the existing `NavBar2`/`Footer` imports):
```jsx
import { buscarEnGuia } from "../services/guiaService";
import BuscadorGuia from "../components/guia/BuscadorGuia";
import FiltroChips from "../components/guia/FiltroChips";
import CategoriaCard from "../components/guia/CategoriaCard";
```

Replace the component's state/refs and the `servicios` array — find:
```jsx
const Bienvenida = () => {
    const agentesRef = useRef(null);
    const documentosRef = useRef(null);
    // const [placaBusqueda, setPlacaBusqueda] = useState('');
    // const [agenteEncontrado, setAgenteEncontrado] = useState(null);
    // const [errorBusqueda, setErrorBusqueda] = useState(null);
    // const [cargando, setCargando] = useState(false);

    const servicios = [
        { img: ConsultaLegal, title: "Asesoría legal gratuita" },
        // { img: multa, title: "Consulta de multas" },
        { img: documentos, title: "Guías y recursos legales" },
        { img: agentes, title: "Consultar agentes facultados" },
    ];

    const handleCardClick = (title) => {
        if (title.includes("agentes") && agentesRef.current) {
        agentesRef.current.scrollIntoView({ behavior: "smooth" });
        } else if (title.includes("Guías") && documentosRef.current) {
        documentosRef.current.scrollIntoView({ behavior: "smooth" });
        }
    };
```

Replace with:
```jsx
const BLOQUES = ["Todo", "Leyes y derechos", "Multas y sanciones", "Tu auto", "En el camino", "Herramientas"];

const Bienvenida = () => {
    const agentesRef = useRef(null);
    const guiaRef = useRef(null);
    const [busqueda, setBusqueda] = useState('');
    const [bloqueActivo, setBloqueActivo] = useState('Todo');

    const categoriasVisibles = buscarEnGuia(busqueda).filter(
        (categoria) => bloqueActivo === 'Todo' || categoria.bloque === bloqueActivo
    );
```

(Note: `useState` must be added to the existing `import React, { useRef } from "react";` line → `import React, { useRef, useState } from "react";`. The `documentos` image import and the dead, already-commented-out `agentesRef` inline-search JSX block are left untouched — out of scope.)

Find the services grid block (the `.map()` over `servicios`) and replace it with three explicit cards, preserving the original visual order (Asesoría, Guía, Agentes) and the existing `motion.div` animation pattern:
```jsx
<div className="row g-4">
    <motion.div
        className="col-12 col-md-4 d-flex justify-content-center align-items-center"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0 }}
        viewport={{ once: true }}
    >
        <Link to="/asesoria-ia" className="text-decoration-none text-white w-100">
            <div className="card servicio-card text-white text-center border-0 rounded-4 overflow-hidden shadow-lg h-100">
                <div className="card-img-wrapper">
                    <img src={ConsultaLegal} className="card-img-top img-fluid" alt="Asesoría legal gratuita" />
                </div>
                <div className="card-body bg-dark bg-opacity-75">
                    <h5 className="card-title fw-bold mb-0">Asesoría legal gratuita</h5>
                </div>
            </div>
        </Link>
    </motion.div>

    <motion.div
        className="col-12 col-md-4 d-flex justify-content-center align-items-center"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        viewport={{ once: true }}
    >
        <div className="tw-w-100 tw-h-100 tw-bg-paper-raised tw-border tw-border-rule tw-rounded-4 tw-shadow-lg tw-p-4 tw-flex tw-flex-col">
            <span className="tw-font-mono tw-text-[11px] tw-font-bold tw-tracking-wide tw-text-magenta tw-mb-2">
                02 · RECURSOS
            </span>
            <h5 className="tw-font-sans tw-font-bold tw-text-ink tw-mb-2">Guía del conductor</h5>
            <p className="tw-text-ink-soft tw-text-sm tw-flex-1">
                Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto en la CDMX.
            </p>
            <button
                type="button"
                onClick={() => guiaRef.current && guiaRef.current.scrollIntoView({ behavior: 'smooth' })}
                className="tw-self-start tw-bg-ink tw-text-white tw-font-semibold tw-text-sm tw-rounded tw-px-4 tw-py-2 tw-border-0 hover:tw-bg-ink/90"
            >
                Explorar →
            </button>
        </div>
    </motion.div>

    <motion.div
        className="col-12 col-md-4 d-flex justify-content-center align-items-center"
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        viewport={{ once: true }}
    >
        <Link to="/ConsultarAgenteTransito" className="text-decoration-none text-white w-100">
            <div className="card servicio-card text-white text-center border-0 rounded-4 overflow-hidden shadow-lg h-100">
                <div className="card-img-wrapper">
                    <img src={agentes} className="card-img-top img-fluid" alt="Consultar agentes facultados" />
                </div>
                <div className="card-body bg-dark bg-opacity-75">
                    <h5 className="card-title fw-bold mb-0">Consultar agentes facultados</h5>
                </div>
            </div>
        </Link>
    </motion.div>
</div>
```

Finally, replace the `documentosRef` section (the whole `<div ref={documentosRef} className="container py-5">...</div>` block, including its `<hr>`, heading, paragraph, and `<ul>` of document links) with:
```jsx
{/* Guía del conductor */}
<div id="guia" ref={guiaRef} className="container py-5">
    <hr className="my-5 border border-dark border-2 opacity-75" />
    <div className="tw-max-w-3xl tw-mx-auto tw-text-center tw-mb-8">
        <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
            02 · RECURSOS
        </span>
        <h2 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-3">
            Guía del conductor <span className="tw-text-magenta">en la CDMX</span>
        </h2>
        <p className="tw-text-ink-soft">
            Leyes, trámites, multas y consejos para manejar, comprar y cuidar tu auto — organizado por tema, para que encuentres justo lo que necesitas.
        </p>
    </div>

    <div className="tw-max-w-3xl tw-mx-auto tw-mb-6">
        <BuscadorGuia value={busqueda} onChange={setBusqueda} />
    </div>

    <div className="tw-max-w-3xl tw-mx-auto tw-mb-8">
        <FiltroChips bloques={BLOQUES} activo={bloqueActivo} onSelect={setBloqueActivo} />
    </div>

    <div className="tw-max-w-5xl tw-mx-auto">
        {categoriasVisibles.length === 0 ? (
            <p className="tw-text-center tw-text-ink-soft">
                No encontramos categorías que coincidan con tu búsqueda.
            </p>
        ) : (
            <div className="tw-grid tw-grid-cols-1 sm:tw-grid-cols-2 md:tw-grid-cols-3 tw-gap-4">
                {categoriasVisibles.map((categoria) => (
                    <CategoriaCard key={categoria.slug} categoria={categoria} />
                ))}
            </div>
        )}
    </div>
</div>
```

- [ ] **Step 5: Manually verify with Playwright**

Logged in, navigate to `/Bienvenida`:
1. Confirm card 02 shows label "02 · RECURSOS", title "Guía del conductor", the description text, and an "Explorar →" button.
2. Click "Explorar →" — confirm the page smooth-scrolls to the `#guia` section (the section becomes visible in the viewport; `window.scrollY` increases).
3. Confirm the grid shows exactly one tile: "01 · LEYES" / "Marco jurídico". Click it — confirm it navigates to `/guia/marco-juridico` (Task 5's page).
4. Type "marco" into the search box — confirm the tile remains. Type "xyz-no-existe" — confirm the grid is replaced by "No encontramos categorías que coincidan con tu búsqueda." Clear the search — confirm the tile reappears.
5. Click the "Leyes y derechos" filter chip — confirm the tile remains (Marco jurídico belongs to that block) and `aria-pressed="true"` on that chip. Click "Multas y sanciones" — confirm the grid shows the no-matches message. Click "Todo" — confirm the tile reappears.
6. Keyboard navigation: starting from a point before the search input, press Tab repeatedly — confirm focus reaches the search input, then each filter chip in order, then the category card, in that order; confirm the card is reachable and activates with Enter.
7. Resize the viewport to 375px wide — confirm the grid renders as a single column.
8. Browser console — zero errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/guia/CategoriaCard.js frontend/src/components/guia/FiltroChips.js frontend/src/components/guia/BuscadorGuia.js frontend/src/pages/Bienvenida.js
git commit -m "feat: add guía del conductor entry point to Bienvenida"
```

---

### Task 8: Final integration verification

**Files:** none (verification-only task).

**Interfaces:** none — this task exercises everything Tasks 1–7 produced end to end.

- [ ] **Step 1: Run the full frontend build**

Run (from `frontend/`): `npm run build`
Expected: build succeeds. The only ESLint warnings present are the pre-existing, unrelated ones already in the repo (`Contacto.js` anchor-is-valid, `GestionarPerfil.js` unused vars, `authService.js` anonymous default export) — no new warnings from any `guia`-related file.

- [ ] **Step 2: Run the full Jest suite**

Run (from `frontend/`): `CI=true npx react-scripts test --watchAll=false`
Expected: all tests pass, including Task 2's 13 tests and Task 3's 8 tests (21 new tests total), zero failures.

- [ ] **Step 3: Full logged-in Playwright walkthrough**

1. Log in with an existing account.
2. `/Bienvenida` → click card 02's "Explorar →" → confirm smooth scroll to `#guia`.
3. In the grid, click "Marco jurídico" → lands on `/guia/marco-juridico`.
4. Click the "Marco jurídico" article row → lands on `/guia/marco-juridico/marco-juridico`, shows the 5 documents.
5. Click "¿Dudas? Pregúntale a la IA legal →" → lands on `/asesoria-ia`.
6. Navigate back (browser back button) twice → lands back on `/guia/marco-juridico`, then `/Bienvenida`.
7. Directly navigate to `/guia/calculadoras/uma-a-pesos` → confirm the "sin datos oficiales todavía" state renders without errors.
8. Browser console — zero errors across the entire walkthrough.

- [ ] **Step 4: Logged-out access check**

Log out (or open a fresh incognito-equivalent context with no token). For each of:
- `/guia/marco-juridico`
- `/guia/marco-juridico/marco-juridico`
- `/guia/calculadoras/uma-a-pesos`

Navigate directly and confirm each redirects to `/Login`.

- [ ] **Step 5: Confirm no references outside `/Bienvenida`**

Run (from `frontend/`):
```bash
grep -rn "guia/" src/pages/Home.js src/components/Navbar.js src/components/NavBar2.js src/components/Footer.js
```
Expected: no output (no matches) — confirms nothing outside `Bienvenida.js` links into the guide, per the explicit scope decision.

- [ ] **Step 6: Final commit (if Step 5's grep required any fix) or confirm clean tree**

```bash
git status
```
Expected: working tree matches the sum of Tasks 1–7's commits, nothing stray left uncommitted. If Step 5 found an accidental reference, remove it and commit:
```bash
git add -A
git commit -m "fix: remove stray guía reference outside Bienvenida"
```
