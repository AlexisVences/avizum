# Revisión lado a lado — hoja de cambios (`reglamento-transito`)

**Qué se revisa y por qué.** Cada fila de abajo es un monto de sanción que el sistema extrajo del Reglamento de Tránsito de la CDMX; si la dejas sin marcar, el asistente **no** la sirve como monto firme. Aquí tienes, fila por fila, lo que dice la hoja, el texto oficial tal como está en la base de datos (tabla `legal_chunks`, solo la fuente vigente `reglamento-transito`, source_id 11) y qué comparar. Las filas están ordenadas por riesgo: 27, 50, 66, 33·II y luego el resto.

**Aviso importante.** Mis «Observaciones» no son una validación ni una decisión: solo señalan diferencias o ambigüedades de texto que pude ver. La autoridad es el texto legal oficial, y tú decides. No marqué ninguna casilla en las hojas.

- **Valor de la UMA que usa el sistema:** 117.31 pesos, vigente del 2026-02-01 al 2027-01-31 (fuente declarada: INEGI, DOF 9 de enero de 2026). Está en `backend/app/core/config.py` (`uma_value`, `uma_valid_from`, `uma_valid_until`, `uma_source`; se puede cambiar por variable de entorno).
- **Cómo aplicar tus decisiones:** edita `data/sanctions/review/reglamento-transito.cambios.md` (copia la línea de casilla de cada fila, sustituyendo la existente) y ejecuta:

```
cd backend && uv run python -m scripts.sanctions apply --reviewer "Alexis" --sheet ../data/sanctions/review/reglamento-transito.cambios.md
```

- **Qué pasa con cada marca:** `[x]` = verificada y se sirve; `[!]` = rechazada (no se sirve; anota el motivo en la línea de abajo); sin marcar = queda pendiente y no se sirve como monto firme. Una fila verificada pasa a *stale* (deja de servirse) si el texto del fragmento cambia o la fuente deja de ser vigente. La casilla «APROBAR TODA LA TANDA 4» (línea 55 de la hoja) existe, pero **no la marques**: revisa fila por fila con este documento.
- Las líneas de la hoja (`línea N`) son las del archivo `reglamento-transito.cambios.md` al momento de generar este documento; si lo editas, el id con hash (entre comillas invertidas) sigue siendo la referencia segura.
- Los blockquotes son copia literal del texto en la base de datos (con sus saltos de línea originales); `[…]` marca partes omitidas por no ser relevantes para la fila.

---

## 1. Art. 27 · fracción II

- **Hoja:** línea 32 · id `reglamento-transito:27:-:1:aaebeb04:fe6b7c37`
- **Lo que dice la hoja:** 100 / 200 / 300 UMA. Sin puntos, sin arresto, sin depósito. Conducta: abstenerse de realizar paradas no señaladas en la operación del servicio.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8972`:_

> Artículo 27.- Además de las obligaciones contenidas en los artículos que anteceden, los conductores de
> vehículos que transporten sustancias tóxicas o peligrosas deben:
>
> […]
>
> II.
> Abstenerse de realizar paradas que no estén señaladas en la operación del servicio;
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo
> dispuesto por la Ley.
> Párrafo modificado G.O. CDMX 10/10/25

**Qué comparar:** Monto mínimo/medio/máximo (100, 200, 300 UMA); que el párrafo de sanción esté debajo de la fracción II y no de otra; que no mencione puntos, arresto ni depósito.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:27:-:1:aaebeb04:fe6b7c37` **fracción II**
```

Si está mal:

```
- [!] `reglamento-transito:27:-:1:aaebeb04:fe6b7c37` **fracción II**
  - motivo: (escribe aquí qué no coincide)
```

---

## 2. Art. 27 · fracción IV

- **Hoja:** línea 36 · id `reglamento-transito:27:-:2:aaebeb04:332ab75a`
- **Lo que dice la hoja:** 200 / 300 / 400 UMA. Sin puntos, sin arresto, sin depósito. Conducta: ir señalizados y balizados conforme a las NOM.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8972`:_

> Artículo 27.- Además de las obligaciones contenidas en los artículos que anteceden, los conductores de
> vehículos que transporten sustancias tóxicas o peligrosas deben:
>
> […]
>
> IV.
> Deberán ir señalizados y balizados de conformidad con lo establecido en las normas oficiales
> mexicanas con relación a este tipo de transporte; y
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo
> dispuesto por la Ley.
> Párrafo modificado G.O. CDMX 10/10/25

**Qué comparar:** Monto mínimo/medio/máximo (200, 300, 400 UMA); que sea el párrafo de la fracción IV (no el de la III, que no tiene sanción).

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:27:-:2:aaebeb04:332ab75a` **fracción IV**
```

Si está mal:

```
- [!] `reglamento-transito:27:-:2:aaebeb04:332ab75a` **fracción IV**
  - motivo: (escribe aquí qué no coincide)
```

---

## 3. Art. 27 · fracción V

- **Hoja:** línea 40 · id `reglamento-transito:27:-:3:aaebeb04:7bb4d677`
- **Lo que dice la hoja:** 200 / 300 / 400 UMA. Sin puntos, sin arresto, sin depósito. Conducta: cumplir los lineamientos en materia de sustancias peligrosas.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8972`:_

> Artículo 27.- Además de las obligaciones contenidas en los artículos que anteceden, los conductores de
> vehículos que transporten sustancias tóxicas o peligrosas deben:
>
> […]
>
> V.
> Cumplir con los lineamientos en materia de sustancias peligrosas que para tal efecto expidan las
> autoridades competentes.
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 200, 300 o 400 veces la Unidad de Medida y Actualización vigente, sin perjuicio de lo
> dispuesto por la Ley.
> Párrafo modificado G.O. CDMX 10/10/25

**Qué comparar:** Monto mínimo/medio/máximo (200, 300, 400 UMA); que no mencione puntos, arresto ni depósito.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:27:-:3:aaebeb04:7bb4d677` **fracción V**
```

Si está mal:

```
- [!] `reglamento-transito:27:-:3:aaebeb04:7bb4d677` **fracción V**
  - motivo: (escribe aquí qué no coincide)
```

---

## 4. Art. 50 · primer párrafo de sanción (alcohol/narcóticos)

- **Hoja:** línea 168 · id `reglamento-transito:50:-:0:563fb289:85cb5ef4`
- **Lo que dice la hoja:** Sin monto en UMA; 6 puntos a la licencia; arresto administrativo inconmutable de 20 a 36 horas; vehículo remitido al depósito vehicular.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9050`:_

> En caso de que se certifique que el conductor sobrepase el límite de alcohol permitido, se encuentre en
> estado de ebriedad o de intoxicación de alcohol, narcóticos, estupefacientes o psicotrópicos al conducir,
> se sancionará con arresto administrativo inconmutable de 20 a 36 horas, y seis puntos de penalización a
> la licencia para conducir, sin menoscabo de lo estipulado en la Ley y demás reglamentos aplicables, en
> tanto que el vehículo será remitido al depósito vehicular, salvo que se encuentre dentro de los supuestos
> previstos en el primer párrafo del artículo 68 de este Reglamento.

_(Párrafos 1 a 3 del artículo, con los límites de alcohol, omitidos por no contener sanción.)_

**Qué comparar:** Arresto (20 a 36 horas, inconmutable); puntos (seis); que NO haya monto en UMA en este párrafo; depósito vehicular y sus excepciones.

**Observación (no es una validación; el texto legal manda):** Posible faltante, no es un error de cifras: el texto dice que el vehículo será remitido al depósito «salvo que se encuentre dentro de los supuestos previstos en el primer párrafo del artículo 68 de este Reglamento». La fila solo dice «remitido al depósito vehicular», sin esa excepción. Arresto (20 a 36 horas) y puntos (seis) coinciden con el texto. Para saber qué dice el artículo 68 habría que abrirlo aparte; no lo cité aquí.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:50:-:0:563fb289:85cb5ef4` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:50:-:0:563fb289:85cb5ef4` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 5. Art. 50 · multa al propietario (60 UMA)

- **Hoja:** línea 172 · id `reglamento-transito:50:-:1:563fb289:02e19434`
- **Lo que dice la hoja:** 60 UMA (monto único); otras: remitido al depósito.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9050`:_

> En caso de que el infractor no sea el propietario del vehículo remitido al depósito y el conductor no hubiere
> dentro de los treinta días posteriores a la imposición de la infracción, cumplido la sanción impuesta en su
> totalidad, el propietario deberá cubrir una multa de 60 veces la Unidad de Medida y Actualización Vigente,
> para solicitar que le sea entregada la unidad.

**Qué comparar:** Monto (60 UMA, único); quién la paga (el propietario, no el conductor); condición (infractor distinto del propietario y sanción no cumplida en 30 días); para qué es (solicitar la entrega de la unidad).

**Observación (no es una validación; el texto legal manda):** El monto (60 veces la UMA) coincide. Pero la multa es condicional (el infractor no es el propietario y no cumplió su sanción dentro de los treinta días) y el texto dice que se paga «para solicitar que le sea entregada la unidad»; la fila resume «otras: remitido al depósito», que no es la sanción de este párrafo (el vehículo ya está en el depósito). Decide si esa condición basta con lo que muestra la hoja.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:50:-:1:563fb289:02e19434` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:50:-:1:563fb289:02e19434` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 6. Art. 66 · licencia cancelada y conduce

- **Hoja:** línea 179 · id `reglamento-transito:66:-:0:03630e42:45b07499`
- **Lo que dice la hoja:** 180 UMA (monto único); remisión del vehículo al depósito. Sin puntos ni arresto.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9082`:_

> Artículo 66.- Las licencia para conducir se cancelarán al acumular doce puntos de penalización.
>
> […]
>
> La reexpedición de una licencia que se haya extinguido por penalización procederá sólo después de
> transcurridos tres años.
> Las personas cuya licencia haya sido cancelada y conduzcan algún vehículo en el lapso a que se refiere el
> párrafo anterior, serán sancionadas con la remisión del vehículo al depósito y una multa de ciento ochenta
> veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto («ciento ochenta» = 180 UMA, único); remisión del vehículo al depósito; que no haya puntos ni arresto; supuesto: licencia cancelada y conduce durante los tres años de la reexpedición.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:66:-:0:03630e42:45b07499` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:66:-:0:03630e42:45b07499` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 7. Art. 33 · fracción II · retiro de inmovilizador (40 UMA)

- **Hoja:** línea 89 · id `reglamento-transito:33:II:1:b838b480:dfd682ce`
- **Lo que dice la hoja:** 40 UMA (monto único). Conducta: quien retire inmovilizadores sin que el interesado haya cubierto adeudos o sin autorización expresa de Seguridad Ciudadana.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9000`:_

> Artículo 33.- Aun cuando se encuentre presente el conductor o alguna otra persona, los vehículos
> motorizados estacionados serán inmovilizados por el agente autorizado para infraccionar, cuando:
>
> […]
>
> Se deroga.
> Seguridad Ciudadana puede auxiliarse de terceros para la inmovilización de vehículos, previo convenio,
> permiso o autorización que haya celebrado para ello.
> Aquella persona que retire inmovilizadores sin que el interesado hubiese cubierto los adeudos con motivo
> de infracciones registradas en el sistema de infracciones del Gobierno de la Ciudad de México, o previa
> autorización expresa de Seguridad Ciudadana, será sancionada con una multa de 40 veces la Unidad de
> Medida y Actualización vigente.

_(Las líneas 3 a 46 del fragmento —fracción II completa con incisos a) a f), la multa de 5, 7 o 10 UMA y los párrafos sobre liberación del vehículo— se omiten; son otra sanción distinta.)_

**Qué comparar:** Monto (40 veces la UMA, único); a quién se le aplica (a «aquella persona que retire inmovilizadores», no al conductor); condiciones (sin que el interesado haya cubierto los adeudos, o sin autorización expresa de Seguridad Ciudadana); que no haya puntos ni arresto.

**Observación (no es una validación; el texto legal manda):** Ambigüedad de ubicación: el monto (40 veces la UMA) coincide, pero el párrafo aparece al final del fragmento de la fracción II, después de «Se deroga.» y del párrafo «Seguridad Ciudadana puede auxiliarse de terceros...», sin llevar numeral propio, así que no queda claro si pertenece solo a la fracción II o a todo el artículo 33 (la fracción I también habla de inmovilizador). Además, el sujeto sancionado es un tercero que retira el inmovilizador, no el conductor infractor. Revisa la fracción y el contexto en el PDF oficial.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:33:II:1:b838b480:dfd682ce` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:33:II:1:b838b480:dfd682ce` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 8. Art. 8 · fracción VI

- **Hoja:** línea 59 · id `reglamento-transito:8:VI:0:ec773431:7a2f38ac`
- **Lo que dice la hoja:** 5 / 7 / 10 UMA; 3 puntos a la licencia o 1 punto a la matrícula (agente → licencia; sistema tecnológico → matrícula; no se suman). Conducta: alinearse a la derecha y reducir la velocidad cuando otro vehículo intente adelantarlo.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8891`:_

> Artículo 8.- Los conductores de todo tipo de vehículos deben:
> VI.
> Alinearse a la derecha y reducir la velocidad cuando otro vehículo intente adelantarlo;

_Fragmento `legal_chunks.id = 8892`:_

> Artículo 8.- Los conductores de todo tipo de vehículos deben:
> VII.
> Los conductores de vehículos motorizados que infrinjan la presente disposición serán sancionados
> con una multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente y tres
> puntos de penalización a la licencia para conducir o en caso de infracciones captadas a través de
> sistemas tecnológicos se sancionará con un punto a la matrícula vehicular.

**Qué comparar:** Que la cláusula realmente corresponda a la fracción VI; monto (5, 7, 10 UMA); puntos (tres a la licencia, o uno a la matrícula si lo capta un sistema tecnológico).

**Observación (no es una validación; el texto legal manda):** Discrepancia estructural en el texto oficial: la sanción NO está escrita debajo de la fracción VI, sino debajo de un encabezado «VII.» que no trae conducta propia (en la fracción VII solo aparece la cláusula). Verifiqué esto también en el PDF oficial `data/legal-sources/reglamento-transito.pdf` (página 13): después de «VI. Alinearse a la derecha…» viene «VII.» seguido directamente de la sanción. No puedo saber si es una errata de la Gaceta (la sanción sería de la VI) o si la fracción VII está incompleta. Los montos y puntos de la fila coinciden con la cláusula citada.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:8:VI:0:ec773431:7a2f38ac` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:8:VI:0:ec773431:7a2f38ac` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 9. Art. 12 · fila general (I a III)

- **Hoja:** línea 67 · id `reglamento-transito:12:-:0:20958cac:d1626927`
- **Lo que dice la hoja:** 10 / 15 / 20 UMA; 3 puntos a la licencia. Depende de las fracciones I a III.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8935`:_

> Artículo 12.- Está prohibido remolcar o empujar otros vehículos motorizados si no es por medio de una
> grúa, excepto cuando:
> I.
> Se trate de remolques u otros vehículos expresamente diseñados para este fin;
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la
> licencia para conducir.
> II. El vehículo se encuentre obstruyendo la circulación; y
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la
> licencia para conducir.
> III. El vehículo a remolcar o empujar represente un peligro para sí o para terceros, en éste caso sólo se
> permitirá hasta ponerlo en un lugar seguro.
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente y tres puntos a la
> licencia para conducir.

**Qué comparar:** Monto (10, 15, 20 UMA); puntos (tres); a qué conducta aplica.

**Observación (no es una validación; el texto legal manda):** Montos y puntos coinciden. Rareza del texto: la misma cláusula de sanción aparece repetida debajo de cada una de I, II y III, que son las EXCEPCIONES a la prohibición («excepto cuando: I… II… III…»), no la conducta prohibida. Es decir, el texto literal parece sancionar a quien actúa en esos casos. La fila lo trata como la sanción de la prohibición general. Decide si esa lectura es razonable.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:12:-:0:20958cac:d1626927` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:12:-:0:20958cac:d1626927` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 10. Art. 12 · fracción IV (VEMEPE)

- **Hoja:** línea 73 · id `reglamento-transito:12:-:1:20958cac:e254e393`
- **Lo que dice la hoja:** 10 / 15 / 20 UMA; 3 puntos a la licencia. Conducta: VEMEPE no pueden remolcar ni empujar otros vehículos.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8935`:_

> Artículo 12.- Está prohibido remolcar o empujar otros vehículos motorizados si no es por medio de una
> grúa, excepto cuando:
>
> […]
>
> Se exceptúan de lo anterior a los vehículos de transporte público en cualquiera de sus modalidades, que
> sólo podrán ser remolcados por una grúa.
> Derogado.
> IV. Tratándose de VEMEPE, queda prohibido remolcar o empujar otros vehículos no motorizados y
> motorizados, así como cualquier tipo de remolque o dispositivos de cualquier otro tipo de
> tracción.

**Qué comparar:** Que exista una sanción debajo de la fracción IV; monto (10, 15, 20 UMA); puntos (tres).

**Observación (no es una validación; el texto legal manda):** El texto de la fracción IV NO trae sanción propia: termina en «…dispositivos de cualquier otro tipo de tracción.» sin cláusula debajo. Las cláusulas de 10, 15 o 20 UMA y tres puntos están debajo de I, II y III, antes de «Se exceptúan…», «Derogado.» y la fracción IV. La fila aplica a la IV la cláusula de las otras («la presente disposición»); eso es una interpretación, no algo escrito debajo de la IV.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:12:-:1:20958cac:e254e393` **fracción IV**
```

Si está mal:

```
- [!] `reglamento-transito:12:-:1:20958cac:e254e393` **fracción IV**
  - motivo: (escribe aquí qué no coincide)
```

---

## 11. Art. 26 · fracción I

- **Hoja:** línea 81 · id `reglamento-transito:26:-:0:d6995919:c72b34d8`
- **Lo que dice la hoja:** 100 / 200 / 300 UMA; 3 puntos a la licencia. Conducta: circular por carriles centrales o segundos niveles de vías de acceso controlado (vehículos de carga de más de 3,857 kg).

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 8971`:_

> Artículo 26.- Queda prohibido a los conductores de vehículos de transporte de carga:
> I.
> Circular por carriles centrales y segundos niveles de las vías de acceso controlado cuando se trate
> de vehículos de peso bruto vehicular de diseño superior a 3,857 Kg o donde el señalamiento
> restrictivo así lo indique, y
> Los conductores que infrinjan la presente disposición serán sancionados con una multa
> equivalente a 100, 200 o 300 veces la Unidad de Medida y Actualización vigente y tres puntos a la
> licencia para conducir, sin perjuicio de lo dispuesto por la Ley.

**Qué comparar:** Monto (100, 200, 300 UMA); puntos (tres); el peso (3,857 kg) en la conducta.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:26:-:0:d6995919:c72b34d8` **fracción I**
```

Si está mal:

```
- [!] `reglamento-transito:26:-:0:d6995919:c72b34d8` **fracción I**
  - motivo: (escribe aquí qué no coincide)
```

---

## 12. Art. 35 · fracción I

- **Hoja:** línea 97 · id `reglamento-transito:35:-:0:a5c7a8de:f5194938`
- **Lo que dice la hoja:** 10 / 15 / 20 UMA. Sin puntos. Conducta: vehículo sin moverse más de 15 días o con residuos que generen foco de infección.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9012`:_

> Artículo 35.- Está prohibido abandonar en la vía pública un vehículo o remolque que se encuentre
> inservible, destruido o inutilizado. Se entiende por estado de abandono, los vehículos que:
> I.
> Que no sean movidos por más de 15 días, o acumulen residuos que generen un foco de infección,
> malos olores o fauna nociva ó
> El incumplimiento a la presente disposición, se sancionará con una multa equivalente a 10, 15 o 20
> veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (10, 15, 20 UMA); que no haya puntos; los 15 días en la conducta.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:35:-:0:a5c7a8de:f5194938` **fracción I**
```

Si está mal:

```
- [!] `reglamento-transito:35:-:0:a5c7a8de:f5194938` **fracción I**
  - motivo: (escribe aquí qué no coincide)
```

---

## 13. Art. 36

- **Hoja:** línea 105 · id `reglamento-transito:36:-:0:8639c9e8:449a86cc`
- **Lo que dice la hoja:** 10 / 15 / 20 UMA. Sin puntos. Depende de las fracciones I a III. Conducta: no pagar la tarifa de vías concesionadas.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9013`:_

> Artículo 36.- Los conductores de vehículos motorizados que accedan a vías concesionadas o
> permisionadas están obligados a realizar el pago correspondiente de acuerdo a las tarifas establecidas,
> salvo que:
> I.
> Exista algún anuncio por parte de la autoridad que indique el libre acceso a causa de alguna
> contingencia o por necesidades de interés público;
> El incumplimiento del pago de las tarifas establecidas por parte de los conductores, se sancionará
> con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente.
> II. Se trate de vehículos de transporte público de pasajeros cuyas rutas incluyan tramos en estas vías;
> y
> El incumplimiento del pago de las tarifas establecidas por parte de los conductores, se sancionará
> con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente.
> III. Se trate de vehículos de emergencia que se dirijan a atender alguna incidencia.
> El incumplimiento del pago de las tarifas establecidas por parte de los conductores, se sancionará
> con una multa equivalente a 10, 15 o 20 veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (10, 15, 20 UMA); que no haya puntos; a qué conducta aplica.

**Observación (no es una validación; el texto legal manda):** Montos coinciden. Misma rareza que el Art. 12: la cláusula está repetida debajo de I, II y III, que son las excepciones al pago («salvo que: I… II… III…»). La fila la toma como sanción de la obligación general de pagar. Decide si esa lectura es razonable.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:36:-:0:8639c9e8:449a86cc` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:36:-:0:8639c9e8:449a86cc` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 14. Art. 39

- **Hoja:** línea 114 · id `reglamento-transito:39:-:0:9555eed3:82dcf282`
- **Lo que dice la hoja:** 5 / 7 / 10 UMA; 1 punto a la licencia y 1 a la matrícula (se aplican ambos).

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9025`:_

> Artículo 39.- Los conductores de automóviles que viajen con pasajeros menores de doce años de edad o
> que midan menos de 1.45 metros de altura, deberán asegurarse que éstos ocupen una de las plazas traseras
> sobre la hilera inmediatamente posterior a los asientos del conductor o del copiloto que cuente con
>
> […]
>
> su peso o talla y se desactive el sistema de bolsas de aire.
> Los conductores que no cumplan con lo establecido en el presente artículo serán sancionados con una
> multa equivalente a 5, 7 o 10 veces la Unidad de Medida y Actualización vigente un punto de penalización
> a la placa de matrícula y un punto a la licencia para conducir.

**Qué comparar:** Monto (5, 7, 10 UMA); un punto a la placa de matrícula y un punto a la licencia, ambos (el texto los une con «y»).

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:39:-:0:9555eed3:82dcf282` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:39:-:0:9555eed3:82dcf282` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 15. Art. 45 · fracción I (placas)

- **Hoja:** línea 121 · id `reglamento-transito:45:I:0:cc652cb6:ebe69967`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Conducta: placas de matrícula frontal y posterior o permiso vigente.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9041`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
> I.
> Placas de matrícula frontal y posterior, o permiso vigente expedido por la Secretaría,
> correspondiente al tipo de vehículo, o en su defecto, la copia certificada de la denuncia de la
> pérdida de las placas de matrícula ante el agente del Ministerio Público o la constancia de hechos
> ante el Juez Cívico, la cual no deberá exceder del término de 10 días hábiles a partir de la fecha de
> su expedición; mismos que deberán:
>
> […]
>
> c) Coincidir; con la calcomanía permanente de circulación, con la tarjeta de circulación y con los
> registros del control vehicular, en caso de no ser así, el agente autorizado para infraccionar
> deberá retener las placas de circulación frontal y posterior, lo cual hará constar en la boleta de
> sanción. Las placas de circulación retenidas por no coincidir con el vehículo en circulación le
> serán devueltas a la persona que acredite su legítima propiedad en las oficinas de Seguridad
> Ciudadana; mientras que el vehículo será remitido al depósito vehicular.

_Fragmento `legal_chunks.id = 9045`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
>
> […]
>
> El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa
> equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que la cláusula de sanción aplique a la fracción I; depósito vehicular (en el inciso c)).

**Observación (no es una validación; el texto legal manda):** La sanción no está en el fragmento de la fracción I: aparece en el último párrafo, después de la fracción V («El incumplimiento de las obligaciones señaladas en el presente artículo…»). El texto dice «presente artículo», lo que apunta a que cubre I a V, pero conviene confirmarlo. Además el inciso c) de la fracción I dice «el vehículo será remitido al depósito vehicular» cuando las placas no coinciden; la fila no registra depósito y la cláusula de sanción citada solo habla de multa. Revisa si eso importa para tu uso.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:45:I:0:cc652cb6:ebe69967` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:45:I:0:cc652cb6:ebe69967` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 16. Art. 45 · fracción II

- **Hoja:** línea 129 · id `reglamento-transito:45:II:0:9572c83d:4a09c3ec`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Conducta: calcomanía de circulación permanente.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9042`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
> II. La calcomanía de circulación permanente;

_Fragmento `legal_chunks.id = 9045`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
>
> […]
>
> El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa
> equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que la cláusula de sanción aplique a esta fracción.

**Observación (no es una validación; el texto legal manda):** Misma observación que la fracción I: el fragmento de esta fracción no trae sanción; la cláusula (20, 25 o 30 UMA) está al final del artículo, después de la fracción V, y habla de «las obligaciones señaladas en el presente artículo». Los montos coinciden con la fila; lo que debes confirmar es que esa cláusula general cubra esta fracción.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:45:II:0:9572c83d:4a09c3ec` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:45:II:0:9572c83d:4a09c3ec` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 17. Art. 45 · fracción III

- **Hoja:** línea 137 · id `reglamento-transito:45:III:0:c3a62e55:8a2f436d`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Conducta: holograma y constancia de verificación vehicular vigente.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9043`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
> III. El holograma y constancia de verificación vehicular vigente con excepción de motocicletas y
> VEMEPE. Los vehículos motorizados de los Estados que conforman la Comisión Ambiental de la
> Megalópolis y que circulen en el territorio de la Ciudad de México están obligados a portar su
> holograma y constancia de verificación vehicular vigente respectiva.

_Fragmento `legal_chunks.id = 9045`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
>
> […]
>
> El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa
> equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que la cláusula de sanción aplique a esta fracción.

**Observación (no es una validación; el texto legal manda):** Misma observación que la fracción I: el fragmento de esta fracción no trae sanción; la cláusula (20, 25 o 30 UMA) está al final del artículo, después de la fracción V, y habla de «las obligaciones señaladas en el presente artículo». Los montos coinciden con la fila; lo que debes confirmar es que esa cláusula general cubra esta fracción.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:45:III:0:c3a62e55:8a2f436d` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:45:III:0:c3a62e55:8a2f436d` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 18. Art. 45 · fracción IV

- **Hoja:** línea 145 · id `reglamento-transito:45:IV:0:c0c07aca:7f69dd80`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Conducta: tarjeta de circulación vigente (física o digital).

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9044`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
> IV. Tarjeta de circulación vigente, en formato físico o digital.

_Fragmento `legal_chunks.id = 9045`:_

> Artículo 45.- Los vehículos motorizados que circulen en el territorio de la Ciudad de México deberán de
> contar con:
>
> […]
>
> El incumplimiento de las obligaciones señaladas en el presente artículo, se sancionarán con una multa
> equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que la cláusula de sanción aplique a esta fracción.

**Observación (no es una validación; el texto legal manda):** Misma observación que la fracción I: el fragmento de esta fracción no trae sanción; la cláusula (20, 25 o 30 UMA) está al final del artículo, después de la fracción V, y habla de «las obligaciones señaladas en el presente artículo». Los montos coinciden con la fila; lo que debes confirmar es que esa cláusula general cubra esta fracción.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:45:IV:0:c0c07aca:7f69dd80` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:45:IV:0:c0c07aca:7f69dd80` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 19. Art. 47 · incumplir programas ambientales / restricciones

- **Hoja:** línea 153 · id `reglamento-transito:47:-:0:6cdcf226:b45f8a46`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Depende de las excepciones I a VII.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9047`:_

> Artículo 47.- Los conductores de vehículos motorizados deberán acatar los programas ambientales y no
> circular en vehículos que tengan restricciones y/o en las eco zonas o zonas de movilidad sustentable, los
> días y horas correspondientes.
> Quedan exceptuados los siguientes vehículos:
>
> […]
>
> VII. Los demás que determinen las disposiciones jurídicas y administrativas aplicables.
> Aquellos conductores de vehículos motorizados que incumplan con lo establecido en este artículo o emitan
> humo ostensiblemente contaminante sea cual fuere la entidad federativa en la que fueron matriculados,
> serán sancionados con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización
> vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que no haya puntos; que las excepciones I a VII sean las listadas.

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:47:-:0:6cdcf226:b45f8a46` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:47:-:0:6cdcf226:b45f8a46` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## 20. Art. 47 · humo ostensiblemente contaminante

- **Hoja:** línea 159 · id `reglamento-transito:47:-:1:6cdcf226:e2ad7d30`
- **Lo que dice la hoja:** 20 / 25 / 30 UMA. Sin puntos. Conducta: emitir humo ostensiblemente contaminante, sea cual sea la entidad de matrícula.

**Texto oficial (BD):**

_Fragmento `legal_chunks.id = 9047`:_

> VII. Los demás que determinen las disposiciones jurídicas y administrativas aplicables.
> Aquellos conductores de vehículos motorizados que incumplan con lo establecido en este artículo o emitan
> humo ostensiblemente contaminante sea cual fuere la entidad federativa en la que fueron matriculados,
> serán sancionados con una multa equivalente a 20, 25 o 30 veces la Unidad de Medida y Actualización
> vigente.

**Qué comparar:** Monto (20, 25, 30 UMA); que el humo contaminante esté en la misma cláusula (misma multa que la fila anterior).

**Observación (no es una validación; el texto legal manda):** Sin discrepancias que yo detecte.

**Casilla para pegar en la hoja:**

Si coincide:

```
- [x] `reglamento-transito:47:-:1:6cdcf226:e2ad7d30` **toda la disposición**
```

Si está mal:

```
- [!] `reglamento-transito:47:-:1:6cdcf226:e2ad7d30` **toda la disposición**
  - motivo: (escribe aquí qué no coincide)
```

---

## Resumen

| # | Fila | Línea en la hoja | Observación señalada |
|---|---|---|---|
| 1 | Art. 27 · fracción II | 32 | No |
| 2 | Art. 27 · fracción IV | 36 | No |
| 3 | Art. 27 · fracción V | 40 | No |
| 4 | Art. 50 · primer párrafo de sanción (alcohol/narcóticos) | 168 | Sí |
| 5 | Art. 50 · multa al propietario (60 UMA) | 172 | Sí |
| 6 | Art. 66 · licencia cancelada y conduce | 179 | No |
| 7 | Art. 33 · fracción II · retiro de inmovilizador (40 UMA) | 89 | Sí |
| 8 | Art. 8 · fracción VI | 59 | Sí |
| 9 | Art. 12 · fila general (I a III) | 67 | Sí |
| 10 | Art. 12 · fracción IV (VEMEPE) | 73 | Sí |
| 11 | Art. 26 · fracción I | 81 | No |
| 12 | Art. 35 · fracción I | 97 | No |
| 13 | Art. 36 | 105 | Sí |
| 14 | Art. 39 | 114 | No |
| 15 | Art. 45 · fracción I (placas) | 121 | Sí |
| 16 | Art. 45 · fracción II | 129 | Sí |
| 17 | Art. 45 · fracción III | 137 | Sí |
| 18 | Art. 45 · fracción IV | 145 | Sí |
| 19 | Art. 47 · incumplir programas ambientales / restricciones | 153 | No |
| 20 | Art. 47 · humo ostensiblemente contaminante | 159 | No |

Empieza por las marcadas «Sí». Ninguna observación es una validación.

- [x] `reglamento-transito:27:-:1:aaebeb04:fe6b7c37` **fracción II**
- [x] `reglamento-transito:27:-:2:aaebeb04:332ab75a` **fracción IV**
- [x] `reglamento-transito:27:-:3:aaebeb04:7bb4d677` **fracción V**
- [!] `reglamento-transito:50:-:0:563fb289:85cb5ef4` **toda la disposición**
  - motivo: Incompleta. Omite la excepción del art. 68 párr. 1: vehículos con sustancias tóxicas/peligrosas o con distintivo para personas con discapacidad NO van al depósito; el conductor va al Juez Cívico y se espera a otro conductor. Arresto inconmutable 20–36 h y 6 puntos sí coinciden. Corregir el campo de depósito y reenviar.
- [!] `reglamento-transito:50:-:1:563fb289:02e19434` **toda la disposición**
  - motivo: Mal estructurada. La multa de 60 UMA la paga el PROPIETARIO (no el infractor), solo si el infractor no es el propietario y no cumplió su sanción en 30 días, y es requisito para que le entreguen la unidad. "Otras: remitido al depósito" no es consecuencia de este párrafo. Reestructurar (sujeto=propietario, condición, finalidad) y reenviar.
- [x] `reglamento-transito:66:-:0:03630e42:45b07499` **toda la disposición**
- [!] `reglamento-transito:33:II:1:b838b480:dfd682ce` **toda la disposición**
  - motivo: Monto y conducta correctos pero mal anclada. El párrafo de 40 UMA es el último párrafo del art. 33 y aplica a cualquier inmovilizador; la fracción II tiene su propia multa (5/7/10 UMA). Re-anclar a "art. 33, último párrafo" (sujeto: quien retire el inmovilizador) y reenviar.
- [x] `reglamento-transito:8:VI:0:ec773431:7a2f38ac` **toda la disposición**
- [x] `reglamento-transito:12:-:0:20958cac:d1626927` **toda la disposición**
- [!] `reglamento-transito:12:-:1:20958cac:e254e393` **fracción IV**
  - motivo: Sin sanción expresa. La fracción IV (VEMEPE) no tiene cláusula propia; las de 10/15/20 UMA están bajo I–III y se refieren a remolcar vehículos motorizados sin grúa. Aplicarla a la IV es analogía, contraria a legalidad/tipicidad. No servir monto: responder que la conducta está prohibida pero la fracción no fija multa específica.
- [x] `reglamento-transito:26:-:0:d6995919:c72b34d8` **fracción I**
- [x] `reglamento-transito:35:-:0:a5c7a8de:f5194938` **fracción I**
- [x] `reglamento-transito:36:-:0:8639c9e8:449a86cc` **toda la disposición**
- [x] `reglamento-transito:39:-:0:9555eed3:82dcf282` **toda la disposición**
- [x] `reglamento-transito:45:I:0:cc652cb6:ebe69967` **toda la disposición**
- [x] `reglamento-transito:45:II:0:9572c83d:4a09c3ec` **toda la disposición**
- [x] `reglamento-transito:45:III:0:c3a62e55:8a2f436d` **toda la disposición**
- [x] `reglamento-transito:45:IV:0:c0c07aca:7f69dd80` **toda la disposición**
- [x] `reglamento-transito:47:-:0:6cdcf226:b45f8a46` **toda la disposición**
- [x] `reglamento-transito:47:-:1:6cdcf226:e2ad7d30` **toda la disposición**