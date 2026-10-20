# Evaluación del asistente legal de tránsito (Fase 4) — informe

Fecha: 2026-10-16. Modelo de producción evaluado: `gpt-5-mini` (`reasoning_effort` bajo). Todo lo de abajo sale de archivos
versionados: casos (`data/eval/*.jsonl`), corridas (`data/eval/runs/`), veredictos (`data/eval/reviews/`) y scripts
(`backend/scripts/eval_*.py`, `judge_agent.py`, `export_review.py`).

## 1. Qué se midió y cómo

- **Casos del agente:** 74 ejecutables (`agent_cases.jsonl`): conducción, estacionamiento, accidentes, multas y Fotocívicas, 11 de
  premisa falsa, 8 sin fundamento en el corpus, y rechazos (fuera de alcance, Estado de México, inyección de instrucciones, agentes).
  Los casos repetidos de los sets de recuperación se marcan `dup_of` y no se corren dos veces.
- **Casos de sanciones:** 26 (`sanction_cases.jsonl`) cuya verdad sale de la fila verificada por una persona
  (`data/sanctions/verified.json`), nunca del recuperador ni del modelo.
- **Corridas:** 2 intentos por caso (el modelo no es determinista); 3 en sanciones.
- **Revisión:** la hizo Claude leyendo cada respuesta junto al texto oficial citado (36 casos de la corrida base), no un juez
  automático; el juez LLM queda para regresión. Los chequeos deterministas (herramienta, textos prohibidos, montos esperados,
  montos de otra fila, montos no respaldados) corren sin API.

## 2. mini contra nano

| | mini | nano |
|---|---|---|
| Errores de ejecución | 0 | 0 (tras corregir el bug de sesión compartida) |
| Anomalías de cita | 7 marcas inválidas | 54 (35 respuestas con herramientas y **sin ninguna cita**) |
| Segundos por turno (consultas legales) | 7.6–9.4 | 9.1–10.5 |

nano cita peor y no gana en velocidad (hace más llamadas por turno): se descarta. Los costos de nano en los archivos se calcularon con
la tarifa de mini y están inflados; falta confirmar su tarifa vigente antes de publicar una cifra.

## 3. Hallazgos de la corrida base (mini) y qué se hizo

| Hallazgo | Gravedad | Resolución |
|---|---|---|
| Cinturón: 10, 15 o 20 UMA en lugar de 5, 7 o 10 (dos fracciones del Art. 37 repiten las letras de inciso con montos distintos) | grave | **Sanciones estructuradas** (ver §4); 0 confusiones de monto en 70 corridas |
| Art. 12 citado como causa de grúa (regula remolcar, no la remisión al depósito) | grave | no reaparece en las 2 corridas nuevas (cita Arts. 33 y 67); sin verificador general de fidelidad, queda como riesgo |
| Premisas falsas aceptadas | — | **0 de 11** en ambas corridas |
| Rechazos que ofrecen lo que no pueden hacer (fotos, estaciones, poemas) | menor | desaparecen con la lista cerrada de capacidades |
| Rechazos que nombran dependencias de otro estado | menor | una línea de alcance y puntero genérico, sin nombrar dependencias (jurisdicción por autoridad que interviene) |
| Llamadas de herramientas en paralelo rompían la sesión compartida de SQLAlchemy (28% de errores en nano) | bug | bloqueo por turno en `AgentContext`; sesión por corrida en el runner |

## 4. El cambio: sanciones estructuradas

Un extractor determinista (sin modelo) convierte cada artículo del Reglamento de Tránsito en filas «conducta → sanción»; una persona las
verifica (230 de 247 en la primera ronda, 17 rechazadas por conductas mal asignadas, no por montos); el agente las recibe junto al
fragmento, en la misma llamada. Solo se sirve lo verificado y con el hash del texto vigente; ante cualquier duda el agente cae a la prosa.
Detalle, desviaciones y límites: `docs/superpowers/plans/2026-10-15-sanciones-estructuradas.md`.

## 5. Resultados después del cambio

**Sanciones (25 casos × 3, mini):** monto exacto 69/70 (el fallo restante, re-medido, 3/3); monto de otra fila 0/70.

**Set de 74 casos (2 intentos), comparado con la corrida base:**

| | base | después |
|---|---|---|
| Errores | 0 | 0 |
| Segundos por turno (media / p95) | 7.4 / 14.1 | **6.6 / 10.6** |
| Herramientas por turno | 1.30 | **1.01** |
| Llamadas a `calcular_multa` | 14 | 4 |
| Costo por turno | USD 0.0027 | USD 0.0027 |
| Chequeos deterministas fallidos | — | 0 |
| `monto_no_respaldado` | — | 0 |
| Marcas de cita inválidas (se eliminan antes del usuario) | 7 | 15 |

Mejoras de calidad observadas al leer las respuestas: c74 ahora responde «No» de forma explícita en las dos corridas, los rechazos de
Estado de México y fuera de alcance quedaron cortos y sin ofertas fuera de capacidad.

## 6. Lo que sigue abierto (no se maquilla)

- **c75** (placas del Estado de México y cámaras): sigue describiendo la sanción por sistema tecnológico como amonestación o curso; el Art. 64
  dice que para matrículas de otra entidad es siempre multa. Persiste en las dos rondas.
- **c76**: remite a la Persona Juzgadora de Cultura Cívica para una boleta de tránsito (procedimiento que probablemente no aplica).
- **Verificador de fidelidad general** (c87): una cita válida junto a una afirmación que el texto no dice solo se detecta leyendo; el
  verificador de montos cubre cifras inventadas, no cifras reales de otra conducta.
- **Rangos de la Ley de Movilidad**, Cultura Cívica y Justicia Administrativa no están en la tabla estructurada; dependen de la prosa. La
  herramienta de cálculo ya evita inventar una media, pero una corrida de tres omite una de las dos categorías de transporte.
- **Marcas de cita inválidas** subieron de 7 a 15 en 148 corridas; se eliminan antes de llegar a la persona, pero conviene investigar si
  el modelo escribe el número de artículo entre corchetes.
- **Recomendación a confirmar en la fuente:** «no entregues documentos si no te presenta una boleta» (mensaje de `buscar_agente` cuando
  no hay coincidencia) frente al Art. 59 II e), donde el agente solicita los documentos para su revisión.
- **Pendiente de revisión humana:** 20 filas nuevas (`data/sanctions/review/reglamento-transito.cambios.md`), entre ellas el Art. 66.
- **Límite de la medición:** n pequeño (74 casos × 2); la revisión es de una sola persona-modelo más la auditoría del cliente, y el
  agente es no determinista. Las cifras son indicativas, no intervalos de confianza.

## 7. Backlog de mejora (decidido el 2026-10-16: se difiere, se pasa a la Fase 5)

Orden y esfuerzo estimado acordados; ninguno bloquea la Fase 5.

| # | Mejora | Esfuerzo | Nota |
|---|---|---|---|
| 1 | Marcas `[n]` inválidas (7 → 15): guardar la salida cruda del modelo y ajustar el prompt | ~1 h | Sospecha: números de artículo entre corchetes |
| 2 | Reescribir el consejo «no entregues documentos sin boleta» conforme al Art. 59 II e) y h) (se entregan para revisión y deben devolverse) | ~15 min | Requiere OK al texto / fuente |
| 3 | Precio de nano sin verificar | 5 min | Opcional |
| 4 | c75: nota estructurada del Art. 64 (siempre multa: placas de otra entidad, carriles confinados, personas morales, etc.) ligada al hash del artículo | ~2 h | Medir con c75, h38, h53, h54 |
| 5 | c76: verificar si el Art. 106 de Cultura Cívica sí aplica a infracciones de tránsito (puede no ser error) | ~1 h | Confirmar con criterio jurídico |
| 6 | Fidelidad de citas (c87): primero medir con el juez LLM sobre las 148 corridas (~USD 1); decidir verificador en línea o muestreo del 5 % según la tasa | 1 h medición; 2–3 días si se construye | |
| 7 | Rangos de Ley de Movilidad / Cultura Cívica / Justicia Administrativa en la tabla estructurada | 1–2 días + ~40 filas a revisar | Afecta sobre todo a concesionarios |
| 8 | Marcar y aplicar las 20 filas pendientes (Art. 66, caso e26) | ~10 min del usuario | `scripts.sanctions apply` |
