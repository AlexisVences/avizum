# Sanciones estructuradas — plan de implementación

> **Estado: EN CURSO (2026-10-15).** Pasos 1 y 2 hechos (migraciones `20261015_07` y `_08`, modelo `LegalSanction`, extractor determinista `app/services/ingestion/sanctions.py` con 17 pruebas). Pasos 3 a 6 pendientes.

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

### 3. Hoja de revisión (humana, obligatoria)
- [ ] Script que genera una hoja lado a lado (artículo con la cláusula resaltada | filas propuestas) para el 100% de las fracciones multi-cláusula y todo lo que falle una validación.
- [ ] Carga a `data/sanctions/verified.json` con revisor, fecha y `chunk_hash`; importación a la BD como `verified`.

### 4. Servir al agente
- [ ] Adjuntar filas `verified` en `search_legislation` y `fetch_article` (misma llamada), con pesos mínimo/medio/máximo y con el 50% por pronto pago.
- [ ] `calcular_multa` acepta `sancion_id`; sigue aceptando múltiplos libres para cálculos fuera de la tabla.
- [ ] Verificador determinista al cierre del turno: toda terna "N, M o K veces la UMA" de la respuesta debe existir en las filas o en el texto de los fragmentos citados; si no, anomalía `monto_no_respaldado`.
- [ ] Prompt: elegir la fila cuya conducta coincide; si dos aplican, enumerarlas; sin monto si ninguna coincide. Capacidades en lista cerrada. Jurisdicción: si la autoridad es de otro estado, una línea de alcance y puntero genérico, sin nombrar dependencias; si la autoridad es de la CDMX (p. ej. placas foráneas en cámaras de la CDMX) se responde.

### 5. Evaluación
- [ ] Casos generados de las filas verificadas (una pregunta por fragmento multi-cláusula, ~20-25) con `--repeat 3`.
- [ ] Criterio de salida: 100% de aciertos de monto en esos casos, **cero** `monto_no_respaldado`, d03 corregido, sin regresión en el recall@5 del retrieval, y latencia/costo medidos contra la línea base (se espera menos latencia en preguntas de monto por una ronda menos).

### 6. Reingesta
- [ ] `refresh_sanctions(slug)` idempotente: detecta fragmentos con hash distinto, extrae, valida y deja filas `pending`, con reporte ("N cambiaron, M por revisar").
- [ ] Engancharlo a `scripts.ingest_sources`. El script automático de actualización del final solo tendrá que llamarlo.
- [ ] Indicador de salud: % de fragmentos con sanción que tienen fila `verified` vigente; el reporte lo marca si baja de un umbral.

## Fuera de alcance de este plan

- **c87** (cita del Art. 12 como causal de grúa): es una cita válida con una afirmación que el texto no dice; necesita un verificador de fidelidad general, más caro, y va en una fase aparte.
- El disparador automático de actualización (detectar la reforma y descargar el PDF): sigue pendiente al final, como estaba.

## Review Focus

1. Ninguna ruta sirve una fila no `verified`, con hash distinto o de una fuente no vigente (pruebas en las Tasks 2 y 4).
2. El monto de una fila sale siempre de `clause_text` y nunca de la salida de un modelo.
3. La Task 5 compara contra la línea base, no contra un criterio nuevo.
