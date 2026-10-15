# Revisión de sanciones — `reglamento-transito` (solo lo que cambió)

Marca `[x]` en cada fila que coincida con el artículo, `[!]` en la que esté mal (y anota por qué debajo).
Una fila que no marques **no se sirve** al agente. Lo resaltado `⟦…⟧` es la cláusula de la que salió el monto.

## Tanda 3 — fragmentos con algo que el extractor no pudo resolver
_3 filas en 1 fragmentos._

#### Art. 27

> Artículo 27.- Además de las obligaciones contenidas en los artículos que anteceden, los conductores de vehículos que transporten sustancias tóxicas o peligrosas deben: I. Sujetarse estrictamente a circular por las rutas, horarios y los itinerarios de carga y descarga autorizados y dados a conocer por la Secretaría y por Seguridad Pública; Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente y, sin perjuicio de lo dispuesto por la Ley. Párrafo modificado G.O. CDMX 10/10/25 II. Abstenerse de realizar paradas que no estén señaladas en la operación del servicio; ⟦Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley.⟧ Párrafo modificado G.O. CDMX 10/10/25 III. En caso de congestionamiento vehicular que interrumpa la circulación, el conductor deberá solicitar a los agentes prioridad para continuar su marcha, mostrándoles la documentación que ampare el riesgo sobre el producto que transporta, con el propósito de salvaguardar la integridad física de las personas y bienes.; IV. Deberán ir señalizados y balizados de conformidad con lo establecido en las normas oficiales mexicanas con relación a este tipo de transporte; y ⟦Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley.⟧ Párrafo modificado G.O. CDMX 10/10/25 V. Cumplir con los lineamientos en materia de sustancias peligrosas que para tal efecto expidan las autoridades competentes. ⟦Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo dispuesto por la Ley.⟧ Párrafo modificado G.O. CDMX 10/10/25

- [ ] `reglamento-transito:27:-:1:aaebeb04` **fracción II**
  - encabezado: «Además de las obligaciones contenidas en los artículos que anteceden, los conductores de vehículos que transporten sustancias tóxicas o peligrosas deben:»
  - conducta: «Abstenerse de realizar paradas que no estén señaladas en la operación del servicio»
  - sanción: **100 / 200 / 300 UMA**
- [ ] `reglamento-transito:27:-:2:aaebeb04` **fracción IV**
  - encabezado: «Además de las obligaciones contenidas en los artículos que anteceden, los conductores de vehículos que transporten sustancias tóxicas o peligrosas deben:»
  - conducta: «Deberán ir señalizados y balizados de conformidad con lo establecido en las normas oficiales mexicanas con relación a este tipo de transporte»
  - sanción: **200 / 300 / 400 UMA**
- [ ] `reglamento-transito:27:-:3:aaebeb04` **fracción V**
  - encabezado: «Además de las obligaciones contenidas en los artículos que anteceden, los conductores de vehículos que transporten sustancias tóxicas o peligrosas deben:»
  - conducta: «Cumplir con los lineamientos en materia de sustancias peligrosas que para tal efecto expidan las autoridades competentes.»
  - sanción: **200 / 300 / 400 UMA**
- ⚠️ **fraccion_sin_sancion:** fracciones sin sanción en el texto: III

## Tanda 4 — una cláusula por fracción, sin incisos (deterministas): revisa la muestra ★ y aprueba la tanda
_16 filas en 15 fragmentos._

- [ ] **APROBAR TODA LA TANDA 4** (revisé las marcadas con ★ y el resto sigue el mismo patrón)

#### Art. 8 · fracción VI ★

- [ ] `reglamento-transito:8:VI:0:ec773431` **toda la disposición**
  - encabezado: «Los conductores de todo tipo de vehículos deben:»
  - conducta: «Alinearse a la derecha y reducir la velocidad cuando otro vehículo intente adelantarlo;»
  - cláusula: «Los conductores de vehículos motorizados que infrinjan la presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y tres puntos de penalización a la licencia para conducir o en caso de infr…»
  - sanción: **5 / 7 / 10 UMA**; 3 pt licencia, 1 pt matrícula (licencia O matrícula, según la vía)

#### Art. 8 · fracción VII

- [ ] `reglamento-transito:8:VII:0:9cfa08f3` **toda la disposición**
  - encabezado: «Los conductores de todo tipo de vehículos deben:»
  - conducta: «Los conductores de todo tipo de vehículos deben:»
  - cláusula: «Los conductores de vehículos motorizados que infrinjan la presente disposición serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y tres puntos de penalización a la licencia para conducir o en caso de infr…»
  - sanción: **5 / 7 / 10 UMA**; 3 pt licencia, 1 pt matrícula (licencia O matrícula, según la vía)

#### Art. 12

- [ ] `reglamento-transito:12:-:0:20958cac` **toda la disposición**
  - encabezado: «Está prohibido remolcar o empujar otros vehículos motorizados si no es por medio de una grúa, excepto cuando:»
  - conducta: «Está prohibido remolcar o empujar otros vehículos motorizados si no es por medio de una grúa, excepto cuando:»
  - cláusula: «Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la licencia para conducir.»
  - sanción: **10 / 15 / 20 UMA**; 3 pt licencia

#### Art. 26

- [ ] `reglamento-transito:26:-:0:d6995919` **fracción I**
  - encabezado: «Queda prohibido a los conductores de vehículos de transporte de carga:»
  - conducta: «Circular por carriles centrales y segundos niveles de las vías de acceso controlado cuando se trate de vehículos de peso bruto vehicular de diseño superior a 3,857 Kg o donde el señalamiento restricti…»
  - cláusula: «Los conductores que infrinjan la presente disposición serán sancionados con una multa equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente y tres puntos a la licencia para conducir, sin perjuicio de lo dispuesto por la Ley.»
  - sanción: **100 / 200 / 300 UMA**; 3 pt licencia

#### Art. 33 · fracción II

- [ ] `reglamento-transito:33:II:1:b838b480` **toda la disposición**
  - encabezado: «Aun cuando se encuentre presente el conductor o alguna otra persona, los vehículos motorizados estacionados serán inmovilizados por el agente autorizado para in»
  - conducta: «Aquella persona que retire inmovilizadores sin que el interesado hubiese cubierto los adeudos con motivo de infracciones registradas en el sistema de infracciones del Gobierno de la Ciudad de México, …»
  - cláusula: «Aquella persona que retire inmovilizadores sin que el interesado hubiese cubierto los adeudos con motivo de infracciones registradas en el sistema de infracciones del Gobierno de la Ciudad de México, o previa autorización expresa de Seguridad Ciudadana, será s…»
  - sanción: **40 UMA** (monto único)

#### Art. 35

- [ ] `reglamento-transito:35:-:0:a5c7a8de` **fracción I**
  - encabezado: «Está prohibido abandonar en la vía pública un vehículo o remolque que se encuentre inservible, destruido o inutilizado. Se entiende por estado de abandono, los »
  - conducta: «Que no sean movidos por más de 15 días, o acumulen residuos que generen un foco de infección, malos olores o fauna nociva»
  - cláusula: «El incumplimiento a la presente disposición, se sancionará con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **10 / 15 / 20 UMA**

#### Art. 36 ★

- [ ] `reglamento-transito:36:-:0:8639c9e8` **toda la disposición**
  - encabezado: «Los conductores de vehículos motorizados que accedan a vías concesionadas o permisionadas están obligados a realizar el pago correspondiente de acuerdo a las ta»
  - conducta: «Los conductores de vehículos motorizados que accedan a vías concesionadas o permisionadas están obligados a realizar el pago correspondiente de acuerdo a las tarifas establecidas, salvo que:»
  - cláusula: «El incumplimiento del pago de las tarifas establecidas por parte de los conductores, se sancionará con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **10 / 15 / 20 UMA**

#### Art. 39

- [ ] `reglamento-transito:39:-:0:9555eed3` **toda la disposición**
  - conducta: «Los conductores de automóviles que viajen con pasajeros menores de doce años de edad o que midan menos de 1.45 metros de altura, deberán asegurarse que éstos ocupen una de las plazas traseras sobre la…»
  - cláusula: «Los conductores que no cumplan con lo establecido en el presente artículo serán sancionados con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente un punto de penalización a la placa de matrícula y un punto a la licencia para c…»
  - sanción: **5 / 7 / 10 UMA**; 1 pt licencia, 1 pt matrícula (ambos se suman)

#### Art. 45 · fracción I

- [ ] `reglamento-transito:45:I:0:cc652cb6` **toda la disposición**
  - encabezado: «Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de contar con:»
  - conducta: «Placas de matrícula frontal y posterior, o permiso vigente expedido por la Secretaría, correspondiente al tipo de vehículo, o en su defecto, la copia certificada de la denuncia de la pérdida de las pl…»
  - cláusula: «El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **20 / 25 / 30 UMA**

#### Art. 45 · fracción II

- [ ] `reglamento-transito:45:II:0:9572c83d` **toda la disposición**
  - encabezado: «Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de contar con:»
  - conducta: «La calcomanía de circulación permanente;»
  - cláusula: «El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **20 / 25 / 30 UMA**

#### Art. 45 · fracción III

- [ ] `reglamento-transito:45:III:0:c3a62e55` **toda la disposición**
  - encabezado: «Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de contar con:»
  - conducta: «El holograma y constancia de verificación vehicular vigente con excepción de motocicletas y VEMEPE. Los vehículos motorizados de los Estados que conforman la Comisión Ambiental de la Megalópolis y que…»
  - cláusula: «El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **20 / 25 / 30 UMA**

#### Art. 45 · fracción IV

- [ ] `reglamento-transito:45:IV:0:c0c07aca` **toda la disposición**
  - encabezado: «Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de contar con:»
  - conducta: «Tarjeta de circulación vigente, en formato físico o digital.»
  - cláusula: «El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.»
  - sanción: **20 / 25 / 30 UMA**

#### Art. 47 ★

- [ ] `reglamento-transito:47:-:0:6cdcf226` **toda la disposición**
  - encabezado: «Los conductores de vehículos motorizados deberán acatar los programas ambientales y no circular en vehículos que tengan restricciones y/o en las eco zonas o zon»
  - conducta: «Los conductores de vehículos motorizados deberán acatar los programas ambientales y no circular en vehículos que tengan restricciones y/o en las eco zonas o zonas de movilidad sustentable, los días y …»
  - cláusula: «Aquellos conductores de vehículos motorizados que incumplan con lo establecido en este artículo o emitan humo ostensiblemente contaminante sea cual fuere la entidad federativa en la que fueron matriculados, serán sancionados con una multa equivalente a 20, 25 …»
  - sanción: **20 / 25 / 30 UMA**

#### Art. 50

- [ ] `reglamento-transito:50:-:0:563fb289` **toda la disposición**
  - conducta: «En caso de que se certifique que el conductor sobrepase el límite de alcohol permitido, se encuentre en estado de ebriedad o de intoxicación de alcohol, narcóticos, estupefacientes o psicotrópicos al …»
  - cláusula: «En caso de que se certifique que el conductor sobrepase el límite de alcohol permitido, se encuentre en estado de ebriedad o de intoxicación de alcohol, narcóticos, estupefacientes o psicotrópicos al conducir, se sancionará con arresto administrativo inconmuta…»
  - sanción: sin monto en UMA; 6 pt licencia; otras: arresto administrativo inconmutable de 20 a 36 horas; remitido al depósito vehicular
- [ ] `reglamento-transito:50:-:1:563fb289` **toda la disposición**
  - conducta: «En caso de que el infractor no sea el propietario del vehículo remitido al depósito y el conductor no hubiere dentro de los treinta días posteriores a la imposición de la infracción, cumplido la sanci…»
  - cláusula: «En caso de que el infractor no sea el propietario del vehículo remitido al depósito y el conductor no hubiere dentro de los treinta días posteriores a la imposición de la infracción, cumplido la sanción impuesta en su totalidad, el propietario deberá cubrir un…»
  - sanción: **60 UMA** (monto único); otras: remitido al depósito

#### Art. 66

- [ ] `reglamento-transito:66:-:0:03630e42` **toda la disposición**
  - conducta: «Las personas cuya licencia haya sido cancelada y conduzcan algún vehículo en el lapso a que se refiere el párrafo anterior»
  - cláusula: «Las personas cuya licencia haya sido cancelada y conduzcan algún vehículo en el lapso a que se refiere el párrafo anterior, serán sancionadas con la remisión del vehículo al depósito y una multa de ciento ochenta veces la Unidad de Medida y Actualización vigen…»
  - sanción: **180 UMA** (monto único); otras: remisión del vehículo al depósito

