# Sanciones estructuradas — plan de implementación

> **Estado (2026-10-16): primera revisión humana HECHA (230 de 247 filas verificadas, 17 rechazadas); extractor `det-2` corrige lo que esa revisión encontró; quedan 19 filas nuevas por revisar (`reglamento-transito.cambios.md`).** Histórico previo: construido, a la espera de la revisión humana (2026-10-15). Pasos 1, 2, 4 y 6 hechos y probados (223 pruebas verdes); paso 3: herramientas hechas, **falta que una persona marque la hoja** `data/sanctions/review/reglamento-transito.md` y corra `scripts.sanctions apply`; paso 5: casos escritos (`data/eval/sanction_cases.jsonl`), se corren cuando haya filas verificadas. Mientras no haya filas `verified` el agente se comporta exactamente como antes.

**Problema (medido):** en la evaluación del agente (`data/eval/runs/`, mini ×2), d03 "¿cuánto cuesta no usar el cinturón?" falló en **los dos intentos** con 10, 15 o 20 UMA; el Art. 37 II dice 5, 7 o 10 (10/15/20 solo para el inciso c). Causa reproducida: el modelo recibió 37 II y 37 III (motocicletas), que usan **las mismas letras de inciso con montos distintos**, con el medio recortado (`[…]`) y la cláusula de sanción lejos de la conducta. Leyó "inciso b) → 10, 15 o 20" de la fracción equivocada. La expansión de fracciones hermanas que se añadió en la Fase 2 **aumentó** la confusión. Dimensión: 148 fragmentos con cláusula de sanción en el Reglamento, **77 con dos o más**; de 246 cláusulas, solo 31 declaran su alcance por inciso.

**Goal:** que el monto de una multa nunca dependa de que el modelo mapee prosa. El agente recibe, junto a cada fragmento, una lista cerrada de conductas con su sanción ya resuelta y verificada por una persona; si no está verificada, no se sirve y el agente se comporta como hoy.

**Architecture:** tabla `legal_sanctions` (una fila por conducta) ligada a `legal_chunks` por `chunk_id` y al texto exacto por `chunk_hash`. Los números salen por regex de la cláusula literal; un LLM solo decide a qué incisos aplica cada cláusula. Una fila nace `pending`, pasa a `verified` solo por revisión humana y se vuelve `stale` sola si el fragmento cambia. La fuente de verdad revisada vive en git (`data/sanctions/verified.json`) y la BD se reconstruye desde ahí. `buscar_legislacion` y `obtener_articulo` adjuntan las filas `verified` en la misma llamada (un `SELECT` por llave, sin ronda extra del modelo) con los pesos ya calculados con la UMA de `Settings`, de modo que `calcular_multa` deja de ser necesaria en el caso normal.

## Global Constraints

- **Fallar cerrado:** solo se sirven filas `verified` cuyo `chunk_hash` coincide con el texto actual del fragmento y cuya fuente es `is_current`. Lo demás cae al comportamiento actual (prosa).
- El LLM **nunca** produce un número: montos y puntos se extraen por regex de `clause_text`, que debe ser subcadena literal del fragmento.
- Sin ronda extra del modelo: no se agrega ninguna tool nueva en el camino normal.
- La UMA no se guarda en la tabla; los pesos se calculan en ejecución (`Settings`, con la advertencia de vigencia que ya existe).
- Las pruebas no tocan la red ni OpenAI.
- La línea base a batir es la corrida mini ×2 del 2026-10-15 (`data/eval/runs/20261015-114755-gpt-5-mini.jsonl`) y sus veredictos en `data/eval/reviews/`.

## Tasks

### 1. Migración y modelo — HECHO
- [x] `legal_sanctions` con `chunk_hash`, `status` (`pending|verified|rejected|stale`), `extractor_version`, `reviewed_by/at`.
- [x] Restricciones de BD: UMA ascendente y positiva, puntos no negativos, hash de 64, `(chunk_id, ordinal)` único, cascada con el fragmento.
- [x] Pruebas (`tests/test_legal_sanctions.py`), `database/schema.sql` regenerado.

### 2. Extractor y validaciones — HECHO
- [x] `app/services/ingestion/sanctions.py` (`EXTRACTOR_VERSION = "det-1"`): fracciones, incisos y cláusulas; ternas, montos únicos (también escritos en palabras, incluido "mil") y puntos por regex sobre la cláusula literal.
- [x] **Decisión: el extractor es 100% determinista, sin LLM.** Sobre el corpus indexado, las cláusulas del Reglamento declaran su alcance de forma regular ("la presente disposición", "los incisos a), b)…", "esta fracción", una cláusula pegada a cada fracción). Lo que no se puede leer **no se adivina**: se reporta como `Issue` y no produce fila. El LLM en dos corridas queda descartado en esta versión: agregar un modelo aquí solo reintroduciría el riesgo que se quiere quitar.
- [x] Validaciones: partición (incisos sin cláusula, citados que no existen, cubiertos dos veces, alcance mixto), literalidad (`clause_text` y `conduct_text` subcadenas del fragmento, probado sobre los casos reales), numeración consecutiva de incisos, rangos, y se ignora lo que no es sanción (p. ej. cobertura mínima del seguro, Art. 90 Ley de Movilidad).
- [x] Columna nueva `applies_to` (migración `20261015_08`): una sanción que el texto limita a un tipo de vehículo o situación ("En el caso de vehículos de transporte público de pasajeros y carga…", Art. 9) es una segunda fila de la misma conducta.
- [x] Casos dorados escritos a mano sobre fragmentos reales (`tests/fixtures/sanctions/chunks.json`): 37 II (el caso d03), 37 III (mismas letras, otros montos), 38 IV (incisos con punto), 43 (siete fracciones), 9 IV (override por tipo de vehículo), tabla (Art. 6 V) y rango (Cultura Cívica 31).
- [x] Pruebas con erratas reales del reglamento: "los incisos c), d) e), f) y g)" (sin coma, Art. 38 III) y ", y l)" (Art. 40 II); ambas fallaban en silencio en la primera versión y la validación de partición las detectó.

**Medido sobre el corpus indexado (12 fuentes, 1,997 fragmentos):** 248 filas candidatas, 244 del Reglamento de Tránsito; 30 fragmentos con dos o más cláusulas distintas. Sin resolver (reportado, sin fila): 1 tabla (Art. 6 V, a capturar a mano), 41 rangos (Cultura Cívica, Justicia Administrativa y Ley de Movilidad Art. 251: son rangos de un juez, no tres niveles) y 1 cobertura incompleta real (Art. 44 IV: el inciso c) no tiene sanción en el texto; el agente no debe inventarla).

### 3. Hoja de revisión (humana, obligatoria) — HERRAMIENTAS HECHAS, REVISIÓN PENDIENTE
- [x] `app/services/ingestion/sanction_store.py` y `scripts/sanctions.py` (`extract`, `review`, `apply`, `status`): candidatas `pending` idempotentes, hoja en Markdown con casillas, `verified.json` en git y recarga tras una reconstrucción.
- [x] Hoja por riesgo: tanda 1 = cláusulas que asignan montos por inciso (59 filas en 14 fragmentos), tanda 2 = `applies_to` (15), tanda 3 = lo no resuelto (2), tanda 4 = una cláusula por fracción (171; casilla maestra, muestra ★). La casilla maestra **solo** alcanza a la tanda 4 (hay prueba).
- [x] Las 3 filas de la tabla del Art. 6 V se capturaron a mano en `data/sanctions/manual.json`.
- [ ] **Una persona revisa la hoja y corre `uv run python -m scripts.sanctions apply --reviewer "Nombre"`**; luego se commitea `data/sanctions/verified.json`.

### 3b. Primera revisión humana y extractor `det-2` (2026-10-16)
La revisión (230 `[x]`, 17 `[!]`, ninguna fila aprobada en bloque en la tanda 4) encontró que **los montos casi siempre coinciden con su cláusula; lo que falla es a qué conducta se le pega**. Los 17 rechazos no se sirven. Causas y arreglos, cada uno con prueba sobre el texto real (`tests/fixtures/sanctions/articles.json`):
- **Excepciones leídas como infracciones** (Arts. 12, 36, 47): si el encabezado dice "excepto / salvo / exceptuados", las fracciones son exenciones y la fila es una sola, con la conducta del encabezado.
- **Cláusula con conducta propia** (Art. 33 II 40 UMA, Art. 50 propietario, Art. 66 licencia cancelada): si la cláusula no dice "la presente disposición / este artículo", su conducta es su propio sujeto, no la de la fracción.
- **Sanción sin multa** (Art. 50: arresto inconmutable de 20 a 36 horas, 6 puntos, depósito): ahora se extrae como fila sin monto en UMA, con la consecuencia en `otras`. Solo a nivel de artículo: los pasos de los Arts. 51-52 repiten el 50 y no generan fila.
- **Fracciones colapsadas** (Art. 27, nota de Gaceta "G.O. CDMX 10/10/25 II."): el marcador romano cuenta si es el siguiente número de la secuencia, no solo tras puntuación.
- **Conducta vacía o fusionada** (Arts. 8 VII, 26 I, 35 I): nuevas fronteras de oración (", y Los conductores…", "ó El incumplimiento…"); una fracción que es solo la cláusula toma el encabezado como conducta.
- **Cláusula de artículo** ("el presente artículo", Arts. 8 y 45): cubre las fracciones hermanas sin cláusula propia (filas heredadas, `pending`); las fracciones sin sanción en el texto se reportan (`fraccion_sin_sancion`: Art. 20 III-V, Art. 27 III).
- **Último carácter cortado** («propi», «nocturn»): era un `rstrip("; y o")`; ahora se quita la palabra conectora, no letras.
- **Puntos**: "placa de matrícula" (Art. 39) y nuevo `points_mode` (`alternativos_por_via` licencia o matrícula según la vía, `acumulativos` ambos); `lead_text` guarda el encabezado verbatim para que el agente sepa si la conducta es una prohibición o un deber. Ambos son contexto derivado del mismo texto (migración `20261016_09`) y no reabren una aprobación.
- **`other_consequences`** ahora son solo las frases de consecuencia (arresto, remisión al depósito…), no la cláusula completa.
- **Una aprobación es del contenido que la persona vio**: `load_verified` ya no restaura `verified` si el extractor propone otro contenido (queda `pending`, reportado como `diverged`); solo se toleran puntuación final, el prefijo "Artículo N.-", una conducta que antes salía recortada y `other_consequences` destilado.
- La hoja de revisión principal **nunca se sobrescribe** si tiene marcas; los cambios salen en `reglamento-transito.cambios.md` (`review --delta`, con "antes (lo que revisaste)") y se aplican con `apply --sheet`.

**Resultado:** las 230 aprobaciones siguen vigentes; 19 filas pendientes (3 en la tanda 3: Art. 27; 16 en la 4: versiones corregidas de lo rechazado y fracciones hermanas nuevas).

### 4. Servir al agente — HECHO
- [x] `app/services/sanctions_lookup.py`: solo filas `verified`, con `chunk_hash` igual al hash del texto actual (comparado en SQL) y fuente `is_current`.
- [x] `search_legislation` y `fetch_article` adjuntan `sanciones` por fragmento en la misma llamada (sin ronda extra): conducta, inciso, `aplica_a`, `veces_uma`, `pesos`, `pronto_pago_50` (no en Art. 30 XXI ni 33 II), puntos, vigencia de la UMA y los Arts. 62 y 64 citables.
- [x] **Desviación del plan:** `calcular_multa` **no** recibe `sancion_id`. Las filas ya traen los pesos, así que sería redundante, y exponer ids de base de datos fue un error medido: el modelo los citó como marcas (`[51]`, `[52]`). Las filas no llevan ningún id.
- [x] Verificador de montos al cierre del turno (`app/services/agent/amounts.py`): toda terna de UMA y todo monto en pesos de la respuesta debe salir de lo que las tools devolvieron en ese turno; si no, anomalía `monto_no_respaldado`.
- [x] Prompt: sección "Sanciones y montos", jurisdicción por autoridad que interviene (otra entidad: una línea de alcance y puntero genérico, sin nombrar dependencias), lista cerrada de capacidades y trato de tú.

**Límite conocido del verificador, probado a propósito:** no atrapa un monto que es real pero pertenece a otra conducta (10, 15 o 20 es un monto verdadero del inciso c de Art. 37 II). Eso lo resuelve elegir la fila correcta y lo mide la Tarea 5 con `no_confuser_amount`; el verificador solo evita cifras inventadas.

### 5. Evaluación — CASOS LISTOS, FALTA CORRERLOS CON FILAS VERIFICADAS
- [x] `data/eval/sanction_cases.jsonl`: 26 casos en lenguaje natural sobre conductas de la tanda 1, 2 y 4, con contrastes (cinturón vs casco, polarizado de particular vs transporte público, velocidad con override, tabla manual del Art. 6 V, licencia cancelada) y la laguna del Art. 44 IV (no debe dar la terna de a y b como si fuera la suya).
- [x] La verdad de cada caso sale de la fila verificada (`app/services/sanction_eval.py`): el runner salta los casos cuya fila no está verificada; el juez calcula `amount_ok` y `no_confuser_amount` con los montos de las filas hermanas.
- [ ] Correr: `uv run python -m scripts.eval_agent --cases ../data/eval/sanction_cases.jsonl --repeat 3`, luego `judge_agent --no-llm` y `eval_report`. Criterio de salida: `amount_ok` 100%, `no_confuser_amount` 100% y cero `monto_no_respaldado`.

**Experimento con el modelo real (mini, 12 preguntas × 2 corridas, filas verificadas de forma TRANSITORIA y revertidas; no sustituye la revisión humana; archivo en `data/eval/runs/_experiments/`):**
- d03 (cinturón): **correcto en las dos corridas** (5, 7 o 10 UMA, $586.55 / $821.17 / $1,173.10); antes fallaba en las dos.
- `calcular_multa` pasó de 4 llamadas a **0**; herramientas por turno 1.61 → 1.04; en preguntas de monto la latencia bajó (c45: 11.9 s → 5.9 s; d03: 8.2 s → 6.8 s). En el conjunto no hubo mejora de latencia ni de costo (media 8.2 → 8.8 s, USD 0.0031 → 0.0035): la generación domina y las filas agregan entrada.
- Montos revisados contra el artículo en c06, c20 y c45: correctos. c04 oscila entre "sí" y una respuesta dudosa: ruido de recuperación ya presente antes, no de las filas.

### 6. Reingesta — HECHO
- [x] `sanction_store.refresh_sanctions` (candidatas para texto nuevo o cambiado, verificadas restauradas desde git, `stale` por hash, indicador de salud) y enganchado a `scripts.ingest_sources` para `reglamento-transito`. El script automático de actualización del final solo tendrá que llamarlo.
- [x] Prueba: tras un `--force` con un artículo reformado, lo verificado vuelve y el artículo cambiado queda `pending`.

## Fuera de alcance de este plan

- **c87** (cita del Art. 12 como causal de grúa): es una cita válida con una afirmación que el texto no dice; necesita un verificador de fidelidad general, más caro, y va en una fase aparte.
- El disparador automático de actualización (detectar la reforma y descargar el PDF): sigue pendiente al final, como estaba.
- Ley de Movilidad, Cultura Cívica y Justicia Administrativa: 41 rangos y tablas que no se leen sin adivinar; se retoman con su propia revisión.
- Si la revisión humana confirma que `monto_no_respaldado` casi no da falsos positivos, evaluar mostrarlo al usuario como aviso (hoy solo se registra).
- Origen del consejo "no entregues documentos si no hay boleta" del mensaje de `buscar_agente` cuando no hay coincidencia: confirmar en la fuente oficial; el Art. 59 II e) dice que el agente solicita los documentos para su revisión.

## Review Focus

1. Ninguna ruta sirve una fila no `verified`, con hash distinto o de una fuente no vigente (pruebas en las Tasks 2 y 4).
2. El monto de una fila sale siempre de `clause_text` y nunca de la salida de un modelo.
3. La Task 5 compara contra la línea base, no contra un criterio nuevo.
