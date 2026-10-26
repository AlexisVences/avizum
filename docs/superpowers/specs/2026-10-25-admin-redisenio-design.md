# Rediseño completo del panel de administrador

**Fecha:** 2026-10-25 · **Estado:** aprobado por el cliente el 2026-10-25 con las recomendaciones de la sección 10. Siguiente paso: plan de implementación.

## 1. Para qué sirve este panel

Avizum es un asistente legal con IA para conductores de la CDMX. Quien administra el sistema necesita, en este orden:

1. **Saber si el asistente está contestando bien** (calidad), porque una respuesta legal equivocada es el mayor riesgo del producto.
2. **Saber cuánto se usa y cuánto cuesta** (uso y gasto en OpenAI).
3. **Controlar quién tiene acceso** (usuarios, roles, cuentas sospechosas).
4. **Mantener al día la base de conocimiento** (fuentes oficiales, revisión anual).
5. **Poder demostrar qué hizo cada administrador** (registro de auditoría).

Hoy el panel solo tiene una lista de usuarios a medio funcionar y tres gráficas, dos de ellas vacías. No cubre ninguno de los cinco puntos.

## 2. Auditoría de lo que existe (evidencia: capturas en escritorio y móvil, lectura del código y del backend)

### Graves (seguridad y datos engañosos)
| # | Hallazgo | Dónde |
|---|---|---|
| 1 | **Cualquier persona con sesión abre el panel.** `RutaProtegida` solo revisa que exista un usuario, no su rol. Verificado en el navegador: un usuario con rol `user` entra a `/BienvenidaAdmin`. El backend sí bloquea los datos, pero la interfaz queda expuesta. | `services/rutaProtegida.js` |
| 2 | **«Cerrar sesión» no cierra la sesión.** Es un enlace a `/`; el token y el usuario siguen en `localStorage`. | `components/NavBarAdmin.js` |
| 3 | **El backend permite que un administrador se quite el rol a sí mismo o deje el sistema sin administradores.** `PATCH /admin/users/{id}` asigna cualquier campo sin guardas y no deja registro. | `backend/app/api/routes.py` |
| 4 | **Las métricas mienten.** «Promedio de feedback 0.9 ⭐» es en realidad el 89% de 👍 mostrado como si fuera una calificación de estrellas. «No Calificaciones: 0» es un valor fijo en el código, no un dato. | `pages/Estadisticas.js` |
| 5 | **Si el backend falla, se ve como «0 consultas»**, porque los errores solo van a la consola y el estado inicial es cero. | `pages/Estadisticas.js` |

### Funcionalidad rota o muerta
| # | Hallazgo |
|---|---|
| 6 | **«Eliminar» no funciona nunca**: el servicio lanza «aún no disponible» y la pantalla lo traga en silencio. El botón y su confirmación siguen visibles. |
| 7 | **«Editar» solo guarda el rol.** Nombre, apellido y correo se pueden escribir en el formulario pero no se envían. El rol es un campo de texto libre (`type="rol"` no existe) en vez de una lista cerrada. |
| 8 | **Columna «Consultas» siempre vacía**: la API no devuelve ese dato. |
| 9 | **Dos de las tres gráficas están vacías para siempre**: las barras «por semana» (la API solo da el total del mes) y el pastel «Tipos de consultas» (ya no hay categorías). |
| 10 | **Cinco llamadas idénticas** al mismo endpoint de estadísticas en cada carga. |
| 11 | **La lista carga a todos los usuarios de golpe** y filtra en el navegador: no escala. Ninguna acción de la interfaz usa `is_active`, que el backend sí soporta. |
| 12 | `console.log` con los datos de todos los usuarios en la consola del navegador (datos personales). |

### Diseño y experiencia
| # | Hallazgo |
|---|---|
| 13 | **No parece parte de Avizum.** Usa Bootstrap azul/verde por defecto y `framer-motion`; el resto del sitio usa Tailwind con la paleta de la marca. La marca dice «Abogadazo», no «Avizum». |
| 14 | **El título «Panel administrador» se escribe con espaciado de letras usando el carácter invisible `ㅤ`** (relleno hangul). Los lectores de pantalla lo deletrean letra por letra y en pantalla se ve «Paneladministrador» sin espacio. |
| 15 | **Foto de juzgado de stock como fondo** al 10%: ruido que no aporta información. |
| 16 | **Márgenes superiores arbitrarios** (10 y 12 rem) para librar una barra fija; el contenido empieza a media pantalla. |
| 17 | **Sin navegación del panel**: para pasar de usuarios a estadísticas hay que volver a la portada. Sin sección activa, sin migas de pan. |
| 18 | **Móvil:** la tabla se corta (la columna «Rol» queda a medias) y el conteo «9 usuario(s)» se parte en dos líneas. |
| 19 | **Los modales no son accesibles**: sin rol de diálogo, sin foco atrapado, sin cierre con Escape. |
| 20 | **Cero pruebas** de las tres pantallas del panel; la carga es un texto «Cargando estadísticas...». Pie de página del sitio público dentro de un panel interno. |

## 3. Qué dice la investigación (resumen; las fuentes están al final)

- **Un panel de administración se usa decenas de veces al día**: importa más la velocidad y la claridad que la primera impresión. Los mejores hacen obvias las prioridades y dejan actuar sobre un problema sin saltar de página.
- **Cada tablero debe responder una pregunta definida** (vigilar, reportar o analizar), no mostrar todo. Los indicadores clave van arriba; el detalle, debajo.
- **Para apps con IA** (Langfuse y similares): se vigilan **costo, latencia, errores y calidad**, desglosados por usuario y por sesión. La calidad se mide con **retroalimentación explícita (👍/👎) enlazada a la conversación completa**, de modo que se pueda filtrar lo mal calificado e inspeccionar el contexto. Eso es exactamente una «cola de revisión».
- **Tablas:** paginación del servidor cuando hay más de ~20 filas; paginación (no scroll infinito) cuando se busca algo concreto; orden visible con flecha en el encabezado; **filtros fuera de la tabla**, combinables y con estado activo claro.
- **Cuentas de administrador:** registrar **todas** las acciones de los administradores y los cambios de privilegios; mínimo de administradores; confirmación explícita para cambios de alto impacto; nunca registrar contraseñas, tokens ni datos sensibles (OWASP Logging Cheat Sheet: cuándo, dónde, quién y qué).

## 4. Principios del rediseño

1. **Cada pantalla responde una pregunta.** No hay gráficas decorativas: si un dato no existe, la pantalla lo dice y no dibuja un cero.
2. **Una sola identidad con el chat:** mismo fondo papel, tipografía y magenta de marca. Sin Bootstrap en el panel.
3. **Acción donde está el problema:** desde «Atención» se llega con un clic a lo que hay que resolver.
4. **Nunca fallar en silencio:** cada error, carga y vacío tiene su texto y su siguiente paso.
5. **Lo peligroso pide confirmación y deja huella:** cambio de rol, desactivar, eliminar.

## 5. Arquitectura de información

Barra lateral fija (en móvil, cajón), con cinco secciones, como la barra del chat:

```
┌─────────────┬───────────────────────────────────────────────┐
│ Avizum      │  Resumen            [ 7 días | 30 días | 90 ] │
│ Admin       │  ───────────────────────────────────────────  │
│             │  Preguntas   Personas   Satisfacción  Costo   │
│ ▸ Resumen   │  1,240       87         91 %          $2.41   │
│   Calidad ① │  ───────────────────────────────────────────  │
│   Usuarios  │  Preguntas por día  ╱╲_╱╲╱╲___                │
│   Fuentes   │  ───────────────────────────────────────────  │
│   Actividad │  Requiere atención                            │
│             │   · 3 respuestas con 👎 sin revisar  → Calidad │
│ [A] Alexis  │   · 2 fuentes por revisar este año   → Fuentes │
└─────────────┴───────────────────────────────────────────────┘
```

1. **Resumen.** Periodo seleccionable. Cifras clave en una sola banda con divisores finos (no tarjetas idénticas): preguntas, personas activas, satisfacción (% de 👍 entre las calificadas, con el número de calificaciones), respuestas con error, costo estimado, consultas de agentes. Una serie diaria de preguntas. Lista **«Requiere atención»** con enlaces.
2. **Calidad.** Cola de respuestas para revisar: 👎, con error, o sin ninguna cita. Cada fila abre la pregunta, la respuesta, las fuentes citadas y lo que consultó el agente. Acciones: **marcar revisada** (con nota) y **exportar como caso de evaluación** al formato de `data/eval/*.jsonl`. Cierra el ciclo que ya está en el spec: «los 👎 de producción se revisan y se convierten en casos nuevos».
3. **Usuarios.** Tabla con búsqueda, filtros (rol, estado, correo verificado), orden, paginación en servidor; columnas: nombre, correo, rol, estado, verificado, alta, última actividad, preguntas. Panel lateral por persona. Acciones: cambiar rol, desactivar o reactivar, (decisión 2) eliminar. Guardas: no puedes quitarte tu propio rol ni desactivarte, ni dejar al sistema sin administradores.
4. **Fuentes.** Las 32 fuentes agrupadas por tipo, con versión vigente, fecha de reforma o de consulta, número de fragmentos y enlace a la página oficial. Marca **«Por revisar»** cuando pasó un año desde la consulta o descarga (la revisión anual que acordamos). Solo lectura: la actualización sigue siendo por los scripts. Muestra también cuántas filas de sanciones esperan revisión.
5. **Actividad.** Registro de auditoría de las acciones de administradores: quién, qué, a quién, cuándo. Filtro por persona y por tipo de acción.

## 6. Cambios de backend (hoy no existe lo necesario)

| Endpoint | Para qué |
|---|---|
| `GET /admin/overview?days=` | Cifras del Resumen y serie diaria; costo estimado = tokens × precio configurado en `Settings`. |
| `GET /admin/users?q&role&active&verified&sort&page` | Lista paginada y filtrada, con última actividad y número de preguntas. |
| `PATCH /admin/users/{id}` (mejorado) | Guardas (no a ti mismo, no al último admin), `token_version` al desactivar, y registro de auditoría. |
| `DELETE /admin/users/{id}` (si se aprueba, decisión 2) | Eliminación en cascada con confirmación escrita y registro. |
| `GET /admin/review-queue` y `POST /admin/review-queue/{message_id}` | Cola de calidad y marca de revisión. |
| `GET /admin/sources` | Fuentes con versión, fechas, fragmentos y alerta de revisión. |
| `GET /admin/audit` | Registro de auditoría. |

**Migraciones nuevas:** `admin_audit_log` (quién, acción, objetivo, detalle JSON, fecha) y `message_reviews` (mensaje, estado, nota, quién, cuándo). El registro **no** guarda contraseñas, tokens ni textos de preguntas (solo identificadores).

## 7. Sistema visual (el panel hereda el del chat)

- **Color:** papel `#F7F6F3` (fondo), tinta `#16181D`, tinta suave `#52544D`, **magenta `#C4005F`** (acción principal y estado activo), azul `#1C3F94` (datos y enlaces), verde `#1B6E51` y rojo `#B3261E` solo para estados.
- **Tipografía:** Fraunces para el título de cada sección y las **cifras grandes** (con numerales tabulares); Public Sans para todo lo demás. Sin mayúsculas espaciadas decorativas.
- **Lo memorable:** las cifras del Resumen en Fraunces dentro de una sola banda, y la cola de revisión con respuesta y fuentes lado a lado. Todo lo demás es callado.
- **Gráficas:** una línea para la serie diaria; sin pastel. Colores de la marca, ejes legibles, tabla equivalente para lectores de pantalla.
- **Calidad mínima:** foco de teclado visible, diálogos nativos `<dialog>` con foco atrapado y Escape, `prefers-reduced-motion`, tablas que en móvil se vuelven tarjetas, esqueletos de carga.

## 8. Fases propuestas (cada una se puede usar sola)

| Fase | Contenido | Por qué en este orden |
|---|---|---|
| **0. Base** | Guarda de rutas por rol; cierre de sesión real; estructura con barra lateral y diseño; quitar Bootstrap, el fondo de juzgado y el título con `ㅤ`; marca Avizum. | Cierra los hallazgos 1, 2, 13 a 17 y 20 y da el esqueleto a todo lo demás. |
| **1. Usuarios** | Lista paginada y filtrada; cambio de rol y desactivar con guardas y confirmación; registro de auditoría; pantalla de Actividad. | Cierra 3, 6, 7, 8, 11, 12, 19; es lo más peligroso hoy. |
| **2. Resumen** | `overview`, banda de cifras honestas, serie diaria, costo estimado, «Requiere atención». | Reemplaza las métricas engañosas (4, 5, 9, 10). |
| **3. Calidad** | Cola de revisión y exportar como caso de evaluación. | El valor más grande para el producto; depende de la fase 2 para el aviso de «sin revisar». |
| **4. Fuentes** | Estado de la base de conocimiento y alerta de revisión anual. | Cierra el ciclo de mantenimiento acordado. |

Cada fase incluye pruebas de backend y de frontend y verificación en navegador real (escritorio y móvil), como en el chat.

## 9. Fuera de alcance (anti-objetivos)

- No se edita el contenido de fuentes ni de la guía desde el panel (sigue siendo por archivos y scripts).
- No hay roles intermedios (solo `user` y `admin`) ni permisos por sección.
- No se muestran nombres de personas junto a sus preguntas en la cola de calidad (ver decisión 1).
- Sin alertas por correo ni exportaciones masivas en esta ronda.

## 10. Decisiones (aprobadas por el cliente: «sí, todo»)

1. **Privacidad de la cola de calidad.** Revisar una respuesta mal calificada implica leer la pregunta de una persona. Recomendación: mostrar solo las conversaciones con 👎 (o error), sin nombre ni correo, y añadirlo al Aviso de privacidad.
2. **Eliminar cuentas.** Hoy no existe. Recomendación: **desactivar** ahora y ofrecer **eliminar de verdad** (borra conversaciones) con confirmación escrita y registro, para atender solicitudes de derechos de datos personales.
3. **Alcance de esta ronda.** ¿Las cinco fases, o empezar por 0 a 2 y revisar?
4. **Nombre:** el panel dirá **Avizum** (no «Abogadazo»). ¿Correcto?

## Fuentes consultadas

- Eleken, *Admin dashboard UI*: https://www.eleken.co/blog-posts/admin-dashboard-ui
- Edana, *Designing an effective dashboard UX*: https://edana.ch/en/2025/11/25/designing-an-effective-dashboard-ux-best-practices-and-a-universal-architecture/
- Langfuse, *Product analytics for LLM apps*: https://langfuse.com/blog/product-analytics-for-LLM-apps
- Langfuse, *Metrics overview*: https://langfuse.com/docs/metrics/overview.md
- GitLab Pajamas, *Table*: https://design.gitlab.com/components/table
- Maersk Design System, *Search, filter and sort*: https://designsystem.maersk.com/guidelines/search-filter-and-sort/sort-patterns/index.html
- Michelin Design System, *Table*: https://designsystem.michelin.com/components/table
- OWASP, *Logging Cheat Sheet*: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Google Workspace, *Security best practices for administrator accounts*: https://support.google.com/a/answer/9011373

*Limitaciones de la investigación:* varias fuentes son blogs de proveedores (fechas de 2024 a 2026), por lo que se toman como orientación. No se encontró en la búsqueda la guía de Nielsen Norman Group sobre tablas; las pautas de tablas salen de sistemas de diseño de GitLab, Maersk y Michelin.

**Resolución:** (1) la cola de calidad muestra solo conversaciones con 👎 o error, sin nombre ni correo, y se menciona en el Aviso de privacidad; (2) se incluye eliminar cuentas de verdad, con confirmación escrita y registro; (3) las cinco fases; (4) la marca del panel es Avizum. El cliente pidió además que el resultado se vea como una página profesional.
