# Vigilancia y actualización de las fuentes oficiales — plan

Fecha: 2026-10-20. Cierra el pendiente «descarga automática de nuevas reformas» (spec §14, Fase 5 punto 5).

## Objetivo

Que alguien se entere el mismo día (no «los lunes») de que un documento del que depende el asistente cambió o dejó de estar vigente, que el sistema deje **preparada** la versión nueva (descargada, parseada y comparada con la anterior) y que **publicarla** sea una decisión humana de un comando. Lo que cambia en la página (enlaces, fechas) sale solo de los datos, no de texto escrito a mano.

## Qué existe ya (se reutiliza)

- `official_sources`: versiones con SHA-256, fecha de reforma, `is_current` (una vigente por slug).
- `fetch_sources` (https, tope de tamaño, cadena de certificados de la Consejería), `ingest_sources` (parseo, troceo, embeddings), hook de `ingest_sources` que hace `refresh` de las **sanciones estructuradas**: si el hash del artículo cambia, las filas pasan a `stale` y el agente cae a la prosa (falla cerrada).
- `data/consejeria-catalog.json`: 350 documentos con su nombre, fecha de última reforma y URL del PDF.

## Cómo se detecta un cambio (tres señales, de la más barata a la más segura)

1. **Índice de la Consejería** (leyes, reglamentos, códigos; ~20 páginas en total). Cada documento trae «Última reforma publicada en la G.O. el …» y el PDF cambia de nombre con la versión (`…_6.4.pdf`). Se compara por documento vigilado: fecha de reforma, URL del PDF y si **sigue apareciendo** (si desaparece o dice «abrogada», se avisa como «posible pérdida de vigencia»).
2. **Hash del texto extraído** (no del archivo). Para las fuentes fuera de la Consejería (Acuerdo de agentes de la SSC, Protocolo de Actuación Policial, páginas de parquímetros) y como confirmación de la señal 1. Los PDFs regenerados con metadatos distintos darían falsas alarmas si se comparara el binario.
3. **Calendario** para lo que cambia sin documento nuevo: la UMA cada 1.º de febrero (INEGI, DOF de enero) y el Acuerdo de agentes (se publica uno nuevo cuando cambia la lista). Son recordatorios con fecha, no vigilancia web.

Falsos negativos conocidos: una reforma publicada en la Gaceta que la Consejería tarda semanas en reflejar en su índice. Por eso la vigilancia de la Gaceta Oficial (búsqueda de las leyes vigiladas en el sumario diario) queda como mejora opcional, no como parte del primer corte.

## Qué se hace cuando se detecta (etapas; cada una se puede detener)

| Etapa | Qué hace | Automática |
|---|---|---|
| 1. Detectar | Compara el índice/hash contra `official_sources` y escribe el hallazgo en una tabla `source_changes` (slug, señal, versión vieja/nueva, estado) | Sí |
| 2. Notificar | Un solo aviso por cambio (ver «Cómo te avisa») con: qué documento, fecha de reforma vieja/nueva, enlace | Sí |
| 3. Preparar (staging) | Descarga la versión nueva a `data/legal-sources/incoming/`, valida que sea PDF y que su texto no esté vacío, la parsea y la trocea **sin tocar** `legal_chunks` ni los embeddings | Sí |
| 4. Informe de diferencias | Compara artículo por artículo con la versión vigente: artículos nuevos, eliminados y con texto distinto (diff), conteo de fracciones, sanciones estructuradas que quedarían `stale`, artículos del guía que citan ese documento y casos de evaluación que lo usan | Sí |
| 5. Publicar | `scripts.sources promote <slug>`: marca la versión nueva como vigente, indexa y calcula embeddings solo de lo cambiado, corre el `refresh` de sanciones y la evaluación de regresión (recuperación + sanciones) | **No: lo ejecutas tú** |
| 6. Revisión de sanciones | Las filas `stale` entran a la hoja de revisión delta que ya existe (marcas y `apply`) | Humana |

**Por qué no se publica solo.** Un parseo que sale mal (artículos pegados, fracciones perdidas) degrada las respuestas sin avisar, y las sanciones ya demostraron que lo que parece un detalle (letra de inciso) cambia el monto. El costo de la etapa humana es un comando y leer el informe de diferencias; el costo de omitirla es publicar una ley mal leída. Si más adelante el informe resulta confiable en varias reformas, la etapa 5 puede automatizarse con condiciones (sin artículos eliminados, conteos dentro de ±2 %, regresión sin caídas).

## Qué se actualiza solo en la página

- Nuevo endpoint público `GET /api/v1/sources` con las fuentes vigentes (título, tipo, URL, fecha de reforma, fecha de descarga).
- La guía «Marco jurídico» y la lista de documentos del Home leen ese endpoint en lugar de `marco-juridico.json`; el pie de cada artículo de la guía («última reforma…») sale de la fuente asociada. Los enlaces de las citas ya salen de `official_sources`.
- Lo que **no** se actualiza solo: el texto escrito a mano de los artículos de la guía (montos, plazos). El informe de la etapa 4 lista qué artículos de la guía citan el documento que cambió, para revisarlos.

## Cómo te avisa (a elegir)

| Opción | Costo | Notas |
|---|---|---|
| **GitHub Actions + Issue** | Gratis | El repositorio ya está en GitHub. Una tarea programada corre la detección (diaria, 7:00 CDMX); si hay cambios abre un Issue con el informe y GitHub te manda correo y notificación móvil. Deja historial. Necesita guardar `DATABASE_URL` de solo lectura o correr sin base de datos (comparando contra `data/sources.json` + `data/watch-state.json` versionado) |
| **ntfy.sh o Telegram** | Gratis | Push inmediato al teléfono desde la misma tarea. Útil como segundo canal |
| **Correo (Resend/SMTP)** | Gratis hasta ~3,000/mes | Requiere dominio o remitente verificado |
| **Rutina de Claude programada** | Incluida en el plan | Puede correr la detección y avisar, pero depende de que el entorno de la rutina acceda al repositorio y a la base de datos; es la opción más frágil |

Recomendación: GitHub Actions con Issue (historial + correo) y, si lo quieres, ntfy como push.

La tarea de detección no necesita la base de datos si el estado «lo último que vimos» vive en un archivo versionado (`data/watch-state.json`: por slug, URL, fecha de reforma y hash del texto). Así el aviso funciona aunque el servidor aún no esté desplegado, y el comando de publicación (etapa 5) sí corre contra la base de datos real.

## Fases de trabajo y esfuerzo

| Fase | Entrega | Esfuerzo |
|---|---|---|
| A | Lector del índice de la Consejería + comparación + `watch-state.json` + `scripts.sources check` + pruebas con HTML real guardado como fixture | 4–6 h |
| B | GitHub Action programada + Issue (y ntfy opcional); prueba forzando un cambio simulado | 2–3 h |
| C | Staging + informe de diferencias por artículo (etapas 3 y 4) | 1 día |
| D | `promote` (indexado incremental, refresh de sanciones, regresión) y tabla `source_changes` | 1 día |
| E | Endpoint `/sources` y páginas que lo consumen | 3–4 h |
| F (opcional) | Vigilancia de la Gaceta Oficial y de páginas de parquímetros | 1 día |

El valor llega ya con A + B (avisar el mismo día); C–E convierten el aviso en un proceso corto de publicación.

## Riesgos y cómo se cubren

- **El HTML del índice cambia:** la lectura es estricta y, si no reconoce la estructura, el job **falla ruidosamente** (y avisa), nunca «no hay cambios».
- **Falsas alarmas por PDFs regenerados:** la decisión se toma con el hash del texto extraído, no del archivo.
- **Servidor de la Consejería con cadena de certificados incompleta:** se reutiliza el contexto TLS de `fetch_sources` (también dentro de la Action).
- **Reforma que rompe el parseo:** el informe lo muestra antes de publicar (conteos, artículos faltantes); nada entra a `legal_chunks` sin `promote`.
- **Reforma que cambia montos:** las sanciones afectadas quedan `stale` y el agente cae a la prosa hasta que se revisen.
- **Carga a sitios oficiales:** una pasada diaria de ~20 páginas, con intervalo entre peticiones y `User-Agent` identificado.
- **Pérdida de vigencia:** se avisa como hallazgo distinto («ya no aparece / abrogada») y no se borra nada automáticamente.

## Fuera de alcance de este plan

Descarga automática de los 350 documentos del catálogo (solo se vigilan los 13 usados), traducción de reformas en lenguaje claro, y vigilancia de normas estatales fuera de la CDMX.

## Estado (2026-10-20)

- **Fases A y B hechas.** `app/services/source_watch.py` + `app/services/source_http.py` (TLS y redirecciones compartidas con `fetch_sources`), `scripts/sources.py` (`init` / `check` / `accept`), línea base en `data/watch-state.json` (13 fuentes: 11 por el índice de la Consejería, 2 por hash), `tests/test_source_watch.py` con una muestra del índice real, y `.github/workflows/watch-sources.yml` (diario 07:00 CDMX; un Issue por cambio, sin duplicados).
- Verificado contra los sitios reales: `check` sin cambios sale 0; con la línea base alterada a propósito (fecha de reforma, nombre de PDF y hash) detecta los tres y sale 2. La lógica de apertura de Issues se probó con un `gh` simulado; el flujo completo en GitHub se prueba con **Run workflow** (Actions) la primera vez.
- Límites: la Action solo corre si el repositorio tiene actividad (GitHub desactiva los programados tras 60 días sin ella); el archivo `watch-state.json` debe estar en `main` (rama que usa el cron).
- Pendiente: fases C–F.
