# Guía del conductor — contenido real para las 16 categorías + 2 calculadoras

> **Disparador:** este plan NO se ejecuta solo. Se ejecuta únicamente cuando,
> en una sesión futura, el usuario diga algo como "haz los next steps" / "sigue
> con el plan de contenido" / "implementa lo que falta de la guía" — eso
> significa: hacer todo lo que describe este documento, categoría por
> categoría, en el orden dado abajo.

## Contexto

La arquitectura de "Guía del conductor" ya está completa y en producción
(`docs/superpowers/plans/2026-10-02-guia-del-conductor.md`, mergeado a `main`).
`GuiaCategoria.js` y `GuiaArticulo.js` son genéricos: sirven para cualquier
categoría sin tocar código. Lo único que falta es **contenido real,
verificado, con fuente citada** — nunca inventado. Esto fue una decisión
explícita del usuario (confirmada dos veces en la sesión del 2026-10-02): solo
se publica lo que tiene fuente oficial real, siguiendo la misma filosofía
anti-fabricación que ya usa el resto del proyecto (`legal_ai.py` responde 503
en vez de inventar una respuesta).

**Decisión de proceso confirmada por el usuario:** investigar con búsqueda web
usando fuentes oficiales (dominios `.gob.mx`, INEGI, SEDEMA, etc.), citar la
fuente en cada artículo. Orden de trabajo: **las 2 calculadoras primero**
(datos puramente numéricos, bajo riesgo, ya tienen página lista), luego el
resto por bloque.

## Estado actual de los datos

`frontend/src/content/guia/categorias.json` — 17 categorías completas, solo
`marco-juridico` (01) con `published: true`. Las demás 16 + las 2
herramientas de `herramientas.json` están en `published: false`.

## Paso 0 — Las 2 calculadoras (datos ya investigados y verificados hoy)

Esto es lo único de este plan que ya tiene investigación hecha — solo falta
transcribir a los archivos de config y publicar.

### UMA 2026 (`frontend/src/content/guia/config/uma.json`)

```json
{ "valorDiario": 117.31, "anio": 2026, "fuente": "https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf" }
```

Verificado contra dos fuentes independientes el 2026-10-02:
- Comunicado de prensa INEGI 1/26 (oficial): https://www.inegi.org.mx/contenidos/saladeprensa/boletines/2026/uma/uma2026.pdf
- Publicado en el DOF el 9 de enero de 2026; vigente desde el 1 de febrero de 2026
- Valores: diario $117.31, mensual $3,566.22, anual $42,794.64 (incremento 3.69% vs 2025)

**Nota importante a verificar en la sesión que ejecute esto:** confirmar que
la fecha de esa sesión ya sea posterior al 1 de febrero de 2026 — si no, el
valor vigente en ese momento todavía sería el de 2025 ($113.14 diario). Si se
ejecuta antes de esa fecha, hay que decidir si mostrar el valor saliente de
2025, el entrante de 2026 con fecha de vigencia, o ambos.

### Calendario de verificación — segundo semestre 2026 (`frontend/src/content/guia/config/verificacion.json`)

```json
{
  "calendario": [
    { "digitos": [5, 6], "periodo": "Julio-Agosto", "color": "Amarillo" },
    { "digitos": [7, 8], "periodo": "Agosto-Septiembre", "color": "Rosa" },
    { "digitos": [3, 4], "periodo": "Septiembre-Octubre", "color": "Rojo" },
    { "digitos": [1, 2], "periodo": "Octubre-Noviembre", "color": "Verde" },
    { "digitos": [9, 0], "periodo": "Noviembre-Diciembre", "color": "Azul" }
  ],
  "fuente": "https://sedema.cdmx.gob.mx/programas/programa/verificacion-vehicular"
}
```

Verificado el 2026-10-02 contra SEDEMA (Secretaría del Medio Ambiente CDMX),
vigente del 1 de julio al 31 de diciembre de 2026. Costo de la verificación:
$765 MXN para todos los hologramas (dato para el texto de la herramienta, no
para el cálculo). Fuente oficial: https://sedema.cdmx.gob.mx/programas/programa/verificacion-vehicular

**Nota a verificar en la sesión que ejecute esto:** este es el calendario del
**segundo semestre 2026** (jul-dic). Si para entonces ya cambió de semestre,
hay que volver a buscar el calendario vigente — no reusar estos datos sin
confirmar la fecha actual primero.

### Pasos para publicar las calculadoras

1. Actualizar los dos archivos de config de arriba (confirmando vigencia de fecha primero).
2. En `frontend/src/content/guia/herramientas.json`, cambiar `published` a `true` para `uma-a-pesos` y `cuando-verifico`.
3. En `frontend/src/content/guia/categorias.json`, decidir si la categoría 17 "Calculadoras" también pasa a `published: true` (hoy está en `false`; si se deja así, `/guia/calculadoras` seguirá mostrando 404 y las herramientas solo serán accesibles por URL directa desde donde se enlacen — confirmar con el usuario si quiere que la categoría 17 aparezca en el grid de `/Bienvenida#guia`).
4. Verificar manualmente con Playwright (sesión simulada vía localStorage, igual que en el plan original): `/guia/calculadoras/uma-a-pesos` muestra el resultado real al teclear una cantidad; `/guia/calculadoras/cuando-verifico` muestra el periodo correcto para cada dígito 0-9.
5. `npm run build` + suite de Jest completa (los tests existentes de `umaCalculator`/`verificacionCalculator` ya cubren la lógica; no deberían necesitar cambios, solo los datos de config cambian).
6. Commit.

## Paso 1 en adelante — las 16 categorías de contenido

Para cada categoría: investigar con WebSearch (dominios oficiales
preferidos: `gob.mx`, `cdmx.gob.mx`, `profeco.gob.mx`, `condusef.gob.mx`,
`sat.gob.mx`, `gaceta.cdmx.gob.mx`, Reglamento de Tránsito / Ley de Movilidad
ya citados en `marco-juridico`), redactar el artículo en
`frontend/src/content/guia/articulos/<slug>.json` con `fuentes` real citada,
`published: true`, y verificar con Playwright que se vea bien antes de
comitear. Un commit por categoría (o por bloque, a discreción de quien
ejecute esto) para que cada paso sea revisable por separado.

Orden sugerido (por bloque, ya que así lo prefirió el usuario como alternativa
si no da un orden específico — ir confirmando con el usuario antes de cada
bloque si prefiere otro orden):

### Bloque "Tu auto" (el más mencionado explícitamente por el usuario)
- **05 — Comprar un auto usado** (`comprar-auto-usado`): qué revisar legalmente (REPUVE, tenencias/adeudos, factura, verificación), trámite de cambio de propietario.
- **06 — Comprar un auto nuevo** (`comprar-auto-nuevo`): factura, garantía, requisitos de emplacamiento.
- **07 — Vender tu auto** (`vender-tu-auto`): carta responsiva, aviso de no uso de placas o baja, responsabilidad post-venta.
- **08 — Trámites vehiculares** (`tramites-vehiculares`): emplacamiento, refrendo, cambio de propietario, duplicado de tarjeta de circulación — procedimientos y costos CDMX vigentes.
- **09 — Verificación y Hoy No Circula** (`verificacion-y-hoy-no-circula`): el *artículo* explicativo (distinto de la calculadora) — qué es, excepciones, sanciones por no verificar.
- **10 — Seguros** (`seguros`): obligatoriedad del seguro de responsabilidad civil en CDMX (vigente desde 2019), qué cubre, qué pasa si no lo tienes.

### Bloque "Multas y sanciones"
- **03 — Multas y fotocívicas** (`multas-y-fotocivicas`): tabla de infracciones comunes y su sanción en UMA (ligar con el valor real ya investigado), cómo pagar, cómo impugnar.
- **04 — Tu auto en el corralón** (`tu-auto-en-el-corralon`): procedimiento para recuperar el auto, costos, documentos necesarios.

### Bloque "Leyes y derechos" (las 3 que faltan de este bloque — 01 ya está)
- **02 — Si te detiene un agente** (`si-te-detiene-un-agente`): derechos del conductor, qué puede y no puede pedir un agente, cómo identificar a un agente facultado (ligar con la categoría ya pública `/ConsultarAgenteTransito`).
- **12 — Alcoholímetro** (`alcoholimetro`): procedimiento del operativo, límites legales, sanciones.
- **14 — Mitos vs realidad** (`mitos-vs-realidad`): usar el campo `mito_realidad` del esquema de artículo (ya soportado por `ArticuloContenido.js`, sin necesidad de tocar código) — mitos comunes sobre multas/agentes y su realidad legal.

### Bloque "En el camino"
- **11 — Si chocas** (`si-chocas`): qué hacer en un accidente, cuándo llamar al seguro vs. a la autoridad, responsabilidades.
- **13 — Motos, bicis y peatones** (`motos-bicis-y-peatones`): reglas específicas de movilidad para estos usuarios de la vía.

### Bloque "Herramientas" (contenido de referencia, no calculadoras)
- **15 — Glosario** (`glosario`): requiere decidir una variante nueva de `tipo` en el esquema de artículo (ej. `tipo: "glosario"`, lista de `{termino, definicion}`) — pequeño cambio de código en `ArticuloContenido.js` para soportar esa variante, análogo a como ya soporta `documentos`/`prosa`/`mito_realidad`.
- **16 — Directorio oficial** (`directorio-oficial`): igual, probablemente necesita una variante `tipo: "directorio"` (lista de `{nombre, telefono, sitio, direccion}` de dependencias oficiales relevantes — SEMOVI, SEDEMA, Tribunal de Justicia Administrativa, etc.).

## Checklist de verificación por categoría (repetir en cada una)

- [ ] Investigar con WebSearch, priorizando dominios oficiales.
- [ ] Confirmar al menos una fuente primaria (no solo agregadores/blogs) antes de redactar.
- [ ] Escribir `frontend/src/content/guia/articulos/<slug>.json` con `fuentes` real.
- [ ] Cambiar `published: true` en `categorias.json` para esa categoría.
- [ ] Verificar con Playwright: `/guia/<slug>` (o `/guia/<slug>/<articulo>` si la categoría termina con 2+ artículos) se ve bien, sin errores de consola.
- [ ] Confirmar que el grid de `/Bienvenida#guia` ahora muestra la nueva categoría y que el buscador/filtros la encuentran.
- [ ] `npm run build` limpio.
- [ ] Commit (mensaje describiendo la categoría publicada y su fuente).

## Fuera de alcance de este plan

- No se toca `/Home` — la guía sigue siendo exclusiva de `/Bienvenida`, sin cambios a esa decisión.
- No se crean páginas nuevas de React — todo pasa por los componentes genéricos ya existentes, salvo las 2 variantes de `tipo` nuevas para glosario/directorio (cambio pequeño y localizado en `ArticuloContenido.js`, ya anticipado en el plan original).
- Precios, multas en pesos, y cualquier cifra legal deben recalcularse contra el valor de UMA vigente en el momento de redactar cada categoría — no asumir que el valor de UMA 2026 capturado arriba sigue vigente si pasó mucho tiempo entre sesiones.
