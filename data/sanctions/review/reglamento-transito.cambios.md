# Revisión de sanciones — `reglamento-transito` (solo lo que cambió)
<!--sheet delta=1-->

Marca `[x]` en cada fila que coincida con el artículo, `[!]` en la que esté mal (y anota por qué debajo).
Una fila que no marques **no se sirve** al agente. Lo resaltado `⟦…⟧` es la cláusula de la que salió el monto.

## Tanda 2 — sanciones que el texto limita a un tipo de vehículo o situación (`applies_to`)
_2 filas en 1 fragmentos._

#### Art. 50

> Artículo 50.- Queda prohibido conducir vehículos motorizados cuando se tenga una cantidad de alcohol en la sangre superior a 0.8 gramos por litro o de alcohol en aire espirado superior a 0.4 miligramos por litro, así como bajo el influjo de narcóticos, estupefacientes o psicotrópicos. Los conductores de vehículos destinados al servicio de transporte público de pasajeros, transporte escolar o de personal, vehículos de emergencia, de transporte de carga o de transporte de sustancias tóxicas o peligrosas, no deben presentar ninguna cantidad de alcohol en la sangre o en aire espirado, síntomas simples de aliento alcohólico o de estar bajo los efectos de narcóticos, estupefacientes o psicotrópicos al conducir. Los conductores de vehículos motorizados a quienes se les encuentre cometiendo actos que violen las disposiciones del presente Reglamento o que muestren síntomas de que conducen bajo los efectos de alcohol o narcóticos, estupefacientes o psicotrópicos, están obligados a someterse a las pruebas de detección de ingestión de alcohol o de narcóticos, estupefacientes o psicotrópicos, cuando lo solicite la autoridad competente. ⟦En caso de que se certifique que el conductor sobrepase el límite de alcohol permitido, se encuentre en estado de ebriedad o de intoxicación de alcohol, narcóticos, estupefacientes o psicotrópicos al conducir, se sancionará con arresto administrativo inconmutable de 20 a 36 horas, y seis puntos de penalización a la licencia para conducir, sin menoscabo de lo estipulado en la Ley y demás reglamentos aplicables, en tanto que el vehículo será remitido al depósito vehicular, salvo que se encuentre dentro de los supuestos previstos en el primer párrafo del artículo 68 de este Reglamento.⟧ Para la devolución del vehículo en los depósitos, se deberá comprobar el cumplimiento total de la sanción impuesta al infractor, además de cubrir los derechos y requisitos establecidos en los párrafos sexto y séptimo del artículo 67 del Reglamento. ⟦En caso de que el infractor no sea el propietario del vehículo remitido al depósito y el conductor no hubiere dentro de los treinta días posteriores a la imposición de la infracción, cumplido la sanción impuesta en su totalidad, el propietario deberá cubrir una multa de 60 veces la Unidad de Medida y Actualización Vigente, para solicitar que le sea entregada la unidad.⟧

- [x] `reglamento-transito:50:-:0:563fb289:eb05961b` **toda la disposición**
  - conducta: «En caso de que se certifique que el conductor sobrepase el límite de alcohol permitido, se encuentre en estado de ebriedad o de intoxicación de alcohol, narcóticos, estupefacientes o psicotrópicos al conducir»
  - sanción: sin monto en UMA; 6 pt licencia; otras: arresto administrativo inconmutable de 20 a 36 horas; remitido al depósito vehicular, salvo que se encuentre dentro de los supuestos previstos en el primer párrafo del artículo 68 de este Reglamento
- [x] `reglamento-transito:50:-:1:563fb289:2a289eef` **toda la disposición** — **solo si:** el propietario del vehículo (no el infractor), si el conductor no cumplió la sanción en los 30 días siguientes a la infracción
  - **depende de:** «para solicitar que le sea entregada la unidad»
  - conducta: «En caso de que el infractor no sea el propietario del vehículo remitido al depósito y el conductor no hubiere dentro de los treinta días posteriores a la imposición de la infracción, cumplido la sanción impuesta en su …»
  - sanción: **60 UMA** (monto único)

## Tanda 3 — fragmentos con algo que el extractor no pudo resolver
_0 filas en 6 fragmentos._

#### Art. 6 · fracción V

> Artículo 6.- Para garantizar la seguridad de los peatones, los conductores de vehículos están obligados a otorgar: V. Prioridad de uso en las calles de prioridad peatonal, dónde los peatones podrán circular en todo lo ancho de la vía y en cualquier sentido. El conductor de un vehículo no motorizado que no respete la preferencia de paso y/o la prioridad de uso de los peatones de acuerdo a lo dispuesto en este artículo será amonestado y/o apercibido verbalmente por los agentes y/o agentes autorizados para infraccionar, y orientado a conducirse de conformidad a las disposiciones aplicables. El conductor de un vehículo motorizado que no respete la preferencia de paso y/o la prioridad de uso de los peatones de acuerdo a lo dispuesto en este artículo será sancionado con base en la siguiente tabla: Tipo de vehículo Sanción con multa equivalente en veces la Unidad de Medida y Actualización vigente Sanción mínima Sanción media Sanción máxima Sanción con puntos de penalización en licencia para conducir Conductores de vehículos de uso particular. 10 a 20 veces 10 veces 15 veces 20 veces 3 puntos Conductores de vehículos de transporte de carga. 40 a 60 veces 40 veces 50 veces 60 veces 3 puntos Conductores de vehículos 60 a 80 veces 60 veces 70 veces 80 veces 3 puntos de transporte público de pasajeros.

- ⚠️ **tabla:** Art. 6: penalidades en una tabla por tipo de vehículo; capturar a mano

#### Art. 8 · fracción VII

> Artículo 8.- Los conductores de todo tipo de vehículos deben: VII. Los conductores de vehículos motorizados que infrinjan la presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y tres puntos de penalización a la licencia para conducir o en caso de infracciones captadas a través de sistemas tecnológicos se sancionará con un punto a la matrícula vehicular.

- ⚠️ **fraccion_solo_clausula:** fracción VII: el texto es solo la cláusula; aplica a las demás fracciones del artículo — «Los conductores de vehículos motorizados que infrinjan la presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y tres puntos d»

#### Art. 12

> Artículo 12.- Está prohibido remolcar o empujar otros vehículos motorizados si no es por medio de una grúa, excepto cuando: I. Se trate de remolques u otros vehículos expresamente diseñados para este fin; Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la licencia para conducir. II. El vehículo se encuentre obstruyendo la circulación; y Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la licencia para conducir. III. El vehículo a remolcar o empujar represente un peligro para sí o para terceros, en éste caso sólo se permitirá hasta ponerlo en un lugar seguro. Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la licencia para conducir. Se exceptúan de lo anterior a los vehículos de transporte público en cualquiera de sus modalidades, que sólo podrán ser remolcados por una grúa. Derogado. IV. Tratándose de VEMEPE, queda prohibido remolcar o empujar otros vehículos no motorizados y motorizados, así como cualquier tipo de remolque o dispositivos de cualquier otro tipo de tracción.

- ⚠️ **prohibicion_sin_sancion:** fracción IV: prohibe una conducta pero el texto no fija una multa propia; no se sirve ningún monto

#### Art. 20

> Artículo 20.- Los conductores de motocicletas y vehículos motorizados eléctricos personales (VEMEPE) deben sujetarse a lo dispuesto en el capítulo II de este Título, exceptuando aquellas provisiones que por la naturaleza propia de los vehículos no sean aplicables. Adicionalmente los conductores de motocicletas y vehículos motorizados eléctricos personales (VEMEPE) deben: I. Utilizar un carril completo de circulación; El motociclista que incumpla lo dispuesto en la presente disposición, será sancionado con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y un punto a la licencia para conducir. II. Adelantar otro vehículo sólo por el lado izquierdo; y El motociclista que incumpla lo dispuesto en la presente disposición, será sancionado con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y un punto a la licencia para conducir. III. Respetar las reglas de preferencia de paso estipuladas en el artículo 10. IV. Los vehículos motorizados eléctricos personales (VEMEPE) Tipo A deberán circular solo por vías secundarias y zonas de tránsito calmado. V. Los vehículos motorizados eléctricos personales (VEMEPE) Tipo B podrán circular por cualquier vía, excepto vías ciclistas, carriles confinados, carriles centrales de vías de acceso controlado y carriles centrales de vías primarias, para tal caso, en donde las vías primarias no cuenten con carriles laterales deberán circular por el carril de extrema derecha. VI. Los vehículos motorizados eléctricos personales (VEMEPE) que se definen como monopatín eléctrico (Tipo A o B), deberán circular solo por vías secundarias y zonas de tránsito calmado; así mismo, podrán hacer uso de las vías ciclistas conservando una velocidad máxima de 25 kilómetros por hora y que no ponga en riesgo a los demás usuarios de la vía. El motociclista que incumpla lo dispuesto en la presente disposición, será sancionado con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y un punto a la licencia para conducir.

- ⚠️ **fraccion_sin_sancion:** fracciones sin sanción en el texto: III, IV, V

#### Art. 27

> Artículo 27.- Además de las obligaciones contenidas en los artículos que anteceden, los conductores de vehículos que transporten sustancias tóxicas o peligrosas deben: I. Sujetarse estrictamente a circular por las rutas, horarios y los itinerarios de carga y descarga autorizados y dados a conocer por la Secretaría y por Seguridad Pública; Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente y, sin perjuicio de lo dispuesto por la Ley. Párrafo modificado G.O. CDMX 10/10/25 II. Abstenerse de realizar paradas que no estén señaladas en la operación del servicio; Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley. Párrafo modificado G.O. CDMX 10/10/25 III. En caso de congestionamiento vehicular que interrumpa la circulación, el conductor deberá solicitar a los agentes prioridad para continuar su marcha, mostrándoles la documentación que ampare el riesgo sobre el producto que transporta, con el propósito de salvaguardar la integridad física de las personas y bienes.; IV. Deberán ir señalizados y balizados de conformidad con lo establecido en las normas oficiales mexicanas con relación a este tipo de transporte; y Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley. Párrafo modificado G.O. CDMX 10/10/25 V. Cumplir con los lineamientos en materia de sustancias peligrosas que para tal efecto expidan las autoridades competentes. Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley. Párrafo modificado G.O. CDMX 10/10/25

- ⚠️ **fraccion_sin_sancion:** fracciones sin sanción en el texto: III

#### Art. 44 · fracción IV

> Artículo 44.- Los conductores de cualquier tipo de vehículo deben cumplir con los requisitos legales especificados por cada tipo de vehículo del que se trate: IV. Los conductores de vehículos de transporte escolar, de personal y turístico deberán: a) Conducir con licencia vigente correspondiente al tipo de vehículo; b) Utilizar la cromática autorizada por la Secretaría; y, c) Contar con el permiso o concesión correspondiente. El incumplimiento de las obligaciones señaladas en los incisos a) y b) de la presente disposición, se sancionará con una multa equivalente a 60, 70 o 80 veces la Unidad de Medida y Actualización vigente, sin menoscabo de lo estipulado por la Ley y su reglamento respectivo.

- ⚠️ **cobertura_incompleta:** fracción IV: incisos sin cláusula: ['c']

## Tanda 4 — una cláusula por fracción, sin incisos (deterministas): revisa la muestra ★ y aprueba la tanda
_2 filas en 2 fragmentos._

- [ ] **APROBAR TODA LA TANDA 4** (revisé las marcadas con ★ y el resto sigue el mismo patrón) <!--fp:d29759edbf-->

#### Art. 33 · fracción II ★

- [ ] `reglamento-transito:33:II:1:b838b480:7cbd88d9` **NIVEL ARTÍCULO (aplica a todo el artículo, no solo a la fracción donde está escrito)**
  - conducta: «Aquella persona que retire inmovilizadores sin que el interesado hubiese cubierto los adeudos con motivo de infracciones registradas en el sistema de infracciones del Gobierno de la Ciudad de México, o previa …»
  - cláusula: «Aquella persona que retire inmovilizadores sin que el interesado hubiese cubierto los adeudos con motivo de infracciones registradas en el sistema de infracciones del Gobierno de la Ciudad de México, o previa autorización expresa de Seguridad Ciudadana, será sancionada con una multa de 40 veces la …»
  - sanción: **40 UMA** (monto único)

#### Art. 34 · fracción I

- [x] `reglamento-transito:34:I:0:f027ca97:c3f7a689` **toda la disposición**
  - **antes (lo que revisaste):** «Efectuar reparaciones a vehículos, salvo en casos de emergencia.» → 1/5/10 UMA
  - encabezado: «En la vía pública está prohibido:»
  - conducta: «Efectuar reparaciones a vehículos, salvo en casos de emergencia.»
  - cláusula: «Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 1, 5 o 10 veces la Unidad de Medida y Actualización vigente o seis a doce horas de arresto administrativo;»
  - sanción: **1 / 5 / 10 UMA**; otras: o seis a doce horas de arresto administrativo

