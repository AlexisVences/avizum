# Fuentes candidatas para las preguntas "incómodas" (revisión del catálogo de la Consejería, 2026-10-09)

Catálogo completo: `data/consejeria-catalog.json` (350 documentos: 185 leyes, 158 reglamentos, 7 códigos). Índice origen: `https://data.consejeria.cdmx.gob.mx/index.php/leyes/{leyes,reglamentos,codigos}` (27 por página, `?start=N`).

## Ya indexadas
Reglamento de Tránsito (Consejería, reforma 30-jun-2026; reemplaza al PDF de la SSC del 6-may-2026), Ley de Movilidad (27-ago-2025), Ley de Cultura Cívica (21-ago-2026), Ley de Procedimiento Administrativo (2019), Ley de Justicia Administrativa (2019), Código Fiscal (solo arts. 230 y 231), Reglamento para el Control de Estacionamiento en Vía Pública (14-may-2024), Ley de Responsabilidades Administrativas (24-dic-2025).

## Indexadas después (solo lo relativo a tránsito, por indicación del cliente)
- **Código Penal para el DF** (reforma 21-ago-2026): arts. 123, 130, 135, 139, 140, 157, 242, 332, 338, 340 (`articles` en el manifiesto).
- **Reglamento de la Ley de Cultura Cívica** (Gaceta 25-sep-2024): arts. 24, 25, 29, 34, 63, 85, 103, 104, 105, 123, 124, 125, 127 (daño culposo por tránsito de vehículos, fuga, depósito).
- **Protocolo General de Actuación Policial (SSC)**: secciones 2.1, 4.2 y 4.5 (formato `layout: "sections"`, págs. 8-59). **Excluida la 4.9** (manifestaciones), aunque contiene la única mención al "registro y documentación de la actuación de las autoridades"; añadirla si el cliente lo decide.
- Quedan fuera por no tratar de tránsito: Reglamento de la Ley de Movilidad (revisar), Ley del Sistema de Seguridad Ciudadana, Reglamento Interior de la SSC, Ley del uso de la fuerza, Ley Constitucional de Derechos Humanos.

## Pendientes de decisión o de código (por prioridad)
_(La primera fila ya se resolvió: ver arriba.)_
| Documento | Para qué | Bloqueo |
|---|---|---|
| Protocolo General de Actuación Policial de la SSC (`ssc.cdmx.gob.mx/.../PROTOCOLO-GRAL-DE-ACTUACION-POLICIALSSC.pdf`, 68 págs.) | p. 33: "cometer una infracción de tránsito no es motivo para que se realice una inspección de vehículo"; p. 59: se garantiza a toda persona "la observación y, en su caso, el registro y documentación de la actuación de las autoridades" (**en el capítulo de manifestaciones**, no en retenes de tránsito). Cubre q04/q06/q16 solo en parte | No tiene "Artículo N": necesita un parser/chunker por secciones y un `kind` nuevo (`protocolo`) |
| Reglamento de la Ley de Cultura Cívica | Hechos de tránsito: si hay fuga o abandono de la víctima "será competencia del Ministerio Público"; depósito vehicular | Ninguno (formato de artículos). Falta aprobar |
| Código Penal para el DF (reforma 21-ago-2026) | "No auxilie a la víctima o se dé a la fuga" como agravante en lesiones y homicidio culposos por tránsito (q17) | **Decisión de alcance** (derecho penal) y elegir artículos concretos con el campo `articles` |
| Reglamento de la Ley de Movilidad (6-may-2026) | Definiciones de grúa, depósitos | Valor incierto; revisar si agrega algo al Reglamento de Tránsito |
| Ley del Sistema de Seguridad Ciudadana, Reglamento Interior de la SSC, Ley que regula el uso de la fuerza, Ley Constitucional de Derechos Humanos | Marco general de actuación policial y derechos | No respondieron ninguna pregunta del set; valor bajo por ahora |

## Huecos que ningún documento del catálogo cubre
- **Días y horarios de parquímetros**: el Reglamento de Estacionamiento NO los trae. Art. 4 fr. XXIII: los publica la SAF en la Gaceta Oficial; Art. 53: la Secretaría debe mantener un sitio con "días y horarios, tarifas aplicables, montos de sanciones y derechos por retiro de candado". Falta el acuerdo de Gaceta (el agente puede citar esos dos artículos para decir dónde consultarlo).
- **Que un agente pida bajar del auto** y **grabar al agente en un retén**: ni leyes ni reglamentos ni protocolos lo regulan de forma expresa.

## Pendiente a largo plazo: descarga y preproceso automáticos
Cuando termine el RAG, construir un script que, a partir del catálogo y del manifiesto, **descargue, valide, versione, parsee, trocee e indexe** las fuentes sin intervención manual, y avise cuando la Consejería publique una versión nueva (la Consejería actualiza sin aviso y su índice mezcla versiones viejas y nuevas; en esta sesión encontramos 3 fuentes atrasadas). Base ya existente: `data/consejeria-catalog.json`, `scripts.fetch_sources` (TLS estricto, versionado), `scripts.ingest_sources`. Falta: scraping periódico del índice, comparación de fecha de última reforma, alerta, y manejo de formatos distintos (protocolos sin artículos).

## Parquímetros: fuentes operativas (no normativas) aportadas por el cliente, 2026-10-09
Complementan el hueco de "días y horarios". Son datos **operativos que cambian**, no leyes; si se usan en respuestas hay que rotularlos como tales y citar la fuente.

**1. Preguntas frecuentes de ecoParq** — `https://www.ecoparq.cdmx.gob.mx/preguntasfrecuentes/preguntas-frecuentes` (HTML, ~10 mil caracteres de texto). Contenido verificado el 2026-10-09:
- Tarifa autorizada desde el 1-ene-2026: **$3.40 por cada 15 minutos** (Art. 259 del Código Fiscal); retiro de candado inmovilizador **$340.00** (Art. 230).
- Horario general: lunes a viernes de 08:00 a 20:00 en los polígonos Benito Juárez Norte y Sur, Anzures, Lomas de Chapultepec y Florida.
- Polanco: además del horario habitual, horario ampliado en la zona delimitada por Arquímedes, Horacio, Molière y Reforma, **miércoles a sábado de 08:00 a 01:00 del día siguiente**.
- Roma e Hipódromo: lunes a miércoles de 08:00 a 20:00 y **jueves a sábado de 08:00 a 01:00 del día siguiente**.
- **Juárez y Cuauhtémoc no las opera la Secretaría de Movilidad** sino SERVIMET S.A. (a través de Operadora de Estacionamientos Viales). Pendiente: su horario completo y qué reglas aplican.

**2. Tres carteles de ecoParq** (imágenes; sin URL de origen todavía, pedirla al cliente). Transcripción:
- *Ubicación de los Kioscos Digitales* (colonias Cuauhtémoc y Juárez; lunes a viernes 8:00 a 20:00): Cuauhtémoc: Río Elba 60, Río de la Plata 24, Río Lerma 231, Río Nazas 179, Río Lerma 101, Río Balsas 18, Río Pánuco 46, Río Lerma 7. Juárez: Hamburgo 262, Hamburgo 188, Hamburgo 98, Havre 15, Londres 61, Marsella 35, Roma 41, Versalles 6.
- *Artículo 259 del Código Fiscal*: dice **$3.25 por cada 15 minutos**. **Desactualizado**: el Código Fiscal vigente (reforma 19-dic-2025) y ecoParq dicen $3.40. No usar esta imagen para tarifas. Formas de pago: alcancías, kioscos digitales y aplicaciones (Estacionamiento Digital, "¡Yo! Estacionándome").
- *¿Por qué lo inmovilizan?* Reproduce el Art. 33 fr. II del Reglamento de Tránsito (placas foráneas en zonas de cobro). Liberación: 55 1269 6059, 56 1587 2279 y 56 1589 5873, atención de 8:00 a 21:30. **Teléfonos y horario son dato operativo sin respaldo legal**: verificar antes de mostrarlos.

**Qué falta**: tratar la página de ecoParq como fuente tipo `guia` del portal oficial (parser HTML nuevo) o como contenido curado con fecha; decidirlo al cerrar el RAG. Mientras tanto, el Código Fiscal Art. 259 (tarifa y delegación del horario a la Secretaría/Gaceta) y los Arts. 4 fr. XXIII y 53 del Reglamento de Estacionamiento ya están indexados.

**3. Página de SERVIMET** (Juárez y Cuauhtémoc) — `https://www.servimet.cdmx.gob.mx/parquimetros/informacion-general`. La página de portada tiene poco texto (~1,100 caracteres): enlaces a "Programa de Parquímetros", "Operación", "Pago de derechos de estacionamiento" y "Si inmovilizaron tu vehículo", más atención ciudadana (Av. Fray Servando Teresa de Mier 77, Col. Centro; tel. 55 5661-6244; lunes a viernes 09:00 a 15:00 y 17:00 a 19:00). **El detalle está en subpáginas que aún no se han revisado**: pendiente de leer "Operación" y "Si inmovilizaron tu vehículo".

### Anotado para el script de actualización automática (al final del proyecto)
- Vigilar la **página de preguntas frecuentes de ecoParq** y las subpáginas de **SERVIMET** (hash del texto; avisar si cambian tarifas, horarios o colonias).
- Revisar **cada diciembre/enero** el Código Fiscal (Art. 259: tarifa; Arts. 230-231: grúa y almacenaje), porque se actualizan por año.
- Buscar acuerdos de la Gaceta que modifiquen **horarios y días por zona** (Art. 4 fr. XXIII del Reglamento de Estacionamiento).
- Comparar contra la tarifa de la ley: si el portal y el Código Fiscal difieren, prevalece el Código Fiscal y se avisa.
- **UMA:** cambia cada febrero (INEGI, publicada en el DOF en enero; vigente del 1-feb al 31-ene). Hoy en `.env`/`Settings` (`UMA_VALUE`, `UMA_VALID_FROM`, `UMA_VALID_UNTIL`): verificada el 2026-10-10 en $117.31 (2026). El script debe leerla de INEGI y avisar; `calcular_multa` ya advierte si la fecha cae fuera de la vigencia.
