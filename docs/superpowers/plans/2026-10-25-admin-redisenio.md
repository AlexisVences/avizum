# Rediseño del panel de administrador: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Reemplazar las tres pantallas del administrador por una consola profesional de cinco secciones (Resumen, Calidad, Usuarios, Fuentes, Actividad), con su backend, sin métricas engañosas y con acciones peligrosas protegidas y auditadas.

**Architecture:** Un router nuevo `app/api/admin.py` (todo detrás de `AdminUser`) y servicios en `app/services/admin/` (una responsabilidad por archivo). En el frontend, un árbol nuevo `src/admin/` bajo la ruta `/admin/*` con un layout de barra lateral, un kit mínimo de componentes y un servicio `adminService.js`. Las rutas y pantallas viejas se eliminan fase por fase, cuando su reemplazo ya funciona.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest; React 19, React Router 7, Tailwind 3 (prefijo `tw-`), Recharts (ya instalado), Jest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-25-admin-redisenio-design.md` (aprobado el 2026-10-25).

## Global Constraints

- Texto de interfaz en español, en minúscula tras la primera letra (sentence case), tuteando; la marca es **Avizum**, nunca «Abogadazo». Los botones dicen la acción exacta («Desactivar cuenta», no «Aceptar»).
- Sin Bootstrap ni `framer-motion` dentro de `src/admin/`. Clases Tailwind con prefijo `tw-`. Colores del tema: `paper` #F7F6F3, `ink` #16181D, `ink-soft` #52544D, `magenta` #C4005F (acción y estado activo), `azul` #1C3F94 (datos y enlaces), `verde` #1B6E51 y `danger` #B3261E solo para estados. Fraunces (`tw-font-display`) para títulos y cifras grandes; Public Sans para el resto. Sin mayúsculas espaciadas decorativas.
- Todo endpoint nuevo exige `AdminUser` y responde 403 a un usuario normal y 401 sin sesión.
- Paginación del servidor: `page` desde 1, `page_size` por defecto 20 y máximo 50.
- Fechas y «día»: calendario de `America/Mexico_City` (`MEXICO_CITY` en `routes.py`).
- El registro de auditoría **nunca** guarda contraseñas, tokens ni textos de preguntas o respuestas: solo identificadores y valores de estado.
- La cola de calidad **no** expone nombre, correo ni identificador de la persona que preguntó.
- Ninguna pantalla falla en silencio: cada carga, error y vacío tiene su texto; un error nunca se muestra como cero.
- Foco de teclado visible, `prefers-reduced-motion` respetado, diálogos nativos `<dialog>`, tablas que en móvil se convierten en tarjetas.
- Convenciones del repo: Python con anotaciones y líneas ≤100; React con archivos `PascalCase`; pruebas de backend con el fixture `client` de `conftest.py` (`(http, factory)`).

## Review Focus

1. **Un administrador intenta quitarse el rol, desactivarse o eliminarse, o dejar al sistema sin administradores** → 409 con código legible; nunca ocurre (Task 1.3 y 1.4).
2. **Páginas vacías o fuera de rango** (`page` mayor que la última, `page_size=1000`, búsqueda sin resultados) → lista vacía con `total` correcto, o el tope de 50; nunca 500 (Task 1.2).
3. **Persona sin ningún mensaje** al ordenar por actividad o preguntas → aparece con «sin actividad» y 0, no desaparece ni rompe el orden (Task 1.2).
4. **Frontera de día y días sin preguntas** en la serie diaria → cada día del periodo aparece con 0 y las preguntas de las 23:30 hora de la CDMX cuentan en ese día (Task 2.2).
5. **Eliminar a alguien que tiene conversaciones, 👍/👎 y consultas de agentes** → se borra todo lo suyo, el registro de auditoría sobrevive sin datos personales y la cola de calidad no queda con filas huérfanas (Task 1.4 y 3.2).

---

## Mapa de archivos

**Backend (crear):** `app/api/admin.py`, `app/services/admin/__init__.py`, `users.py`, `overview.py`, `review.py`, `sources.py`, `audit.py`, `attention.py`, `app/schemas/admin.py`, `migrations/versions/20261025_12_admin_audit_log.py`, `20261025_13_message_reviews.py`, `tests/admin_support.py`, `tests/test_admin_users.py`, `test_admin_audit.py`, `test_admin_overview.py`, `test_admin_review.py`, `test_admin_sources.py`.
**Backend (modificar):** `app/models/domain.py` (modelos `AdminAuditLog`, `MessageReview`), `app/api/routes.py` (quitar `/admin/*` al migrarlos), `app/core/config.py` (precios), `tests/test_api.py` (retirar pruebas de `/admin/statistics`), `database/schema.sql` (regenerar).
**Frontend (crear):** `src/admin/` con `AdminLayout.js`, `RutaAdmin.js`, `pages/{Resumen,Calidad,Usuarios,Fuentes,Actividad}.js`, `components/{PageHeader,Skeleton,EmptyState,ErrorState,ConfirmDialog,StatusBadge,Pagination,StatBand,DailyChart,UserPanel,ReviewDetail}.js`, `hooks/useAdminList.js`, y sus `__tests__/`; `src/services/adminService.js`.
**Frontend (modificar):** `App.js` (rutas), `pages/Login.js` (destino del administrador), `pages/AvisoLegal.js` (privacidad), `services/userService.js` (quitar funciones de administrador).
**Frontend (eliminar):** `pages/BienvenidaAdmin.js`, `pages/AdministrarUsuarios.js`, `pages/Estadisticas.js`, `components/NavBarAdmin.js`, `services/statsService.js`, `styles/BienvenidaAdmin.css`, `styles/AdministrarUsuario.css`.

---

# Fase 0: base

### Task 0.1: guarda por rol y cierre de sesión real

**Files:** Create `src/admin/RutaAdmin.js`, `src/admin/__tests__/RutaAdmin.test.js`. Modify `src/pages/Login.js`.

**Interfaces:** Produces `RutaAdmin({ children })`: sin usuario → `<Navigate to="/Login" replace />`; usuario con `rol !== 'admin'` → `<Navigate to="/Bienvenida" replace />`; administrador → `children`. Lee `authService.getCurrentUser()`.

- [x] **Step 1:** Escribir `RutaAdmin.test.js` (con `react-router-dom` mockeado como en las pruebas existentes) con tres pruebas: `sin sesión va a Login`, `un usuario normal no ve el panel y va a Bienvenida`, `un administrador ve el contenido`.
- [x] **Step 2:** Ejecutar `CI=true npx react-scripts test --watchAll=false src/admin/__tests__/RutaAdmin.test.js`. Esperado: FAIL (módulo inexistente).
- [x] **Step 3:** Implementar `RutaAdmin` en `src/admin/RutaAdmin.js`.
- [x] **Step 4:** En `Login.js` cambiar el destino del administrador de `/BienvenidaAdmin` a `/admin`; ajustar su prueba existente si la hay.
- [x] **Step 5:** Ejecutar la prueba. Esperado: PASS. Commit `feat(admin): guard admin routes by role`.

### Task 0.2: kit mínimo de componentes

**Files:** Create en `src/admin/components/`: `PageHeader.js`, `Skeleton.js`, `EmptyState.js`, `ErrorState.js`, `ConfirmDialog.js`, `StatusBadge.js`, `Pagination.js` y `__tests__/kit.test.js`.

**Interfaces (Produces):**
- `PageHeader({ title, description?, actions? })`: un `<h1>` en Fraunces.
- `Skeleton({ lines = 3 })`: `role="status"` con `aria-label="Cargando"`.
- `EmptyState({ title, hint?, action? })` y `ErrorState({ message, onRetry })`: el segundo muestra el mensaje y un botón «Reintentar».
- `ConfirmDialog({ open, title, body, confirmLabel, tone = 'default' | 'danger', requireText?, onConfirm, onCancel })`: `<dialog>` nativo con `showModal()`; Escape llama `onCancel`; si hay `requireText` el botón de confirmar queda deshabilitado hasta que el campo coincida exactamente.
- `StatusBadge({ tone: 'ok' | 'warn' | 'danger' | 'neutral', children })`: el texto siempre acompaña al color.
- `Pagination({ page, pageSize, total, onChange })`: «Mostrando 21–40 de 135», botones «Anterior»/«Siguiente» deshabilitados en los extremos.

- [x] **Step 1:** Escribir las pruebas con estas aserciones: `ConfirmDialog` abre con `role="dialog"`, Escape llama `onCancel`, con `requireText="ana@x.mx"` el botón está deshabilitado hasta escribir ese texto; `ErrorState` llama `onRetry` al pulsar «Reintentar»; `Pagination` con `page=2, pageSize=20, total=45` muestra «Mostrando 21–40 de 45» y con `total=0` muestra «Sin resultados»; `Skeleton` anuncia «Cargando».
- [x] **Step 2:** Ejecutar la prueba. Esperado: FAIL.
- [x] **Step 3:** Implementar los siete componentes (jsdom no implementa `showModal`: el componente debe tolerar su ausencia y en la prueba se define un doble mínimo).
- [x] **Step 4:** Ejecutar la prueba. Esperado: PASS. Commit `feat(admin): shared UI kit`.

### Task 0.3: layout con barra lateral y rutas `/admin/*`

**Files:** Create `src/admin/AdminLayout.js`, `src/admin/pages/{Resumen,Calidad,Usuarios,Fuentes,Actividad}.js` (cada una, por ahora, `PageHeader` con su título y un `EmptyState` «En construcción»), `src/admin/__tests__/AdminLayout.test.js`. Modify `src/App.js`.

**Interfaces:** Produces `AdminLayout()` con `<Outlet />`. Barra lateral con los cinco enlaces (`Resumen` `/admin`, `Calidad` `/admin/calidad`, `Usuarios` `/admin/usuarios`, `Fuentes` `/admin/fuentes`, `Actividad` `/admin/actividad`) donde el activo lleva `aria-current="page"`; al pie, círculo magenta con la inicial, nombre y botón «Cerrar sesión» que llama `authService.logout()` y navega a `/`. En móvil, botón «Abrir menú» y cajón.

- [x] **Step 1:** Pruebas: `muestra los cinco enlaces y marca el de la ruta actual`, `Cerrar sesión borra token y usuario de localStorage` (aserción sobre `localStorage`, no sobre un mock), `el círculo del perfil es magenta y muestra la inicial`, `en móvil el menú se abre con el botón`.
- [x] **Step 2:** Ejecutar. Esperado: FAIL.
- [x] **Step 3:** Implementar el layout (Tailwind, sin Bootstrap; mismo ancho y estilo de barra que `ConversationSidebar`). En `App.js` añadir `<Route path="/admin" element={<RutaProtegida><RutaAdmin><AdminLayout /></RutaAdmin></RutaProtegida>}>` con rutas hijas índice, `calidad`, `usuarios`, `fuentes`, `actividad`; las rutas viejas `/BienvenidaAdmin`, `/AdministrarUsuario` y `/Estadisticas` pasan a `<Navigate to="/admin" replace />` (se eliminan sus archivos en las fases 1 y 2).
- [x] **Step 4:** Ejecutar toda la suite del frontend. Esperado: PASS. Verificar en el navegador (servidor de desarrollo + `page.route` para la API): el administrador entra a `/admin`; un usuario con `rol: 'user'` es llevado a `/Bienvenida`; capturas de escritorio y móvil. Commit `feat(admin): layout, navigation and routes`.

---

# Fase 1: usuarios y auditoría

### Task 1.1: registro de auditoría

**Files:** Create `migrations/versions/20261025_12_admin_audit_log.py` (down_revision `20261020_11`), `app/services/admin/__init__.py`, `app/services/admin/audit.py`, `tests/test_admin_audit.py`, `tests/admin_support.py`. Modify `app/models/domain.py`.

**Interfaces (Produces):**
- Modelo `AdminAuditLog(id, created_at, actor_id → users.id ON DELETE SET NULL, action: str(40), target_user_id: int | None` **sin** llave foránea, `detail: JSONB)`; índice por `created_at` descendente.
- `class AuditAction(str, Enum)`: `USER_ROLE_CHANGED = "user.role_changed"`, `USER_DEACTIVATED`, `USER_REACTIVATED`, `USER_DELETED`, `REVIEW_MARKED = "review.marked"`.
- `record_audit(db: Session, *, actor_id: int, action: AuditAction, target_user_id: int | None = None, detail: dict[str, str | int | bool | None] | None = None) -> AdminAuditLog` (hace `flush`, no `commit`). Lanza `ValueError` si una clave de `detail` está en `{"password", "token", "email", "question", "answer", "content"}`.
- `tests/admin_support.py`: `make_user(factory, *, email: str, role: UserRole = UserRole.USER, is_active: bool = True, verified: bool = True) -> tuple[User, dict[str, str]]` que crea la persona y devuelve `{"Authorization": "Bearer …"}` usando `create_access_token(str(user.id), user.token_version)`.

- [x] **Step 1:** Escribir `test_admin_audit.py`: `record_audit guarda quién, qué y a quién`, `rechaza claves prohibidas en detail` (parametrizada con las seis), `el registro sobrevive al borrado del actor` (borrar el usuario y comprobar `actor_id is None`).
- [x] **Step 2:** Ejecutar `uv run pytest tests/test_admin_audit.py -q`. Esperado: FAIL.
- [x] **Step 3:** Implementar modelo, migración (con `downgrade`), `audit.py` y `admin_support.py`.
- [x] **Step 4:** Ejecutar la prueba y luego `uv run alembic upgrade head` contra la base local. Esperado: PASS y migración aplicada.
- [x] **Step 5:** Regenerar `database/schema.sql` (`pg_dump --schema-only`, como indica `CLAUDE.md`). Commit `feat(admin): audit log table and recorder`.

### Task 1.2: listado de usuarios paginado y filtrado

**Files:** Create `app/api/admin.py` (router con prefijo `/admin`, incluido desde `routes.py`), `app/schemas/admin.py`, `app/services/admin/users.py`, `tests/test_admin_users.py`. Modify `app/api/routes.py` (borrar `GET /admin/users`).

**Interfaces (Produces):**
- Esquemas `AdminUserRow(id, first_name, last_name, email, role, is_active, email_verified, created_at, last_activity_at: datetime | None, questions_count: int)` y `Page[T](items, total, page, page_size)`.
- `list_users(db, *, q: str | None, role: UserRole | None, active: bool | None, verified: bool | None, sort: Literal["name","created","activity","questions"] = "created", descending: bool = True, page: int = 1, page_size: int = 20) -> tuple[list[AdminUserRow], int]`. `q` busca sin acentos ni mayúsculas en nombre, apellido y correo. `last_activity_at` es el último mensaje de la persona; `questions_count` cuenta sus mensajes de rol usuario.
- `GET /admin/users` con esos parámetros de consulta (`page_size` máximo 50, validado con `Query(ge=1, le=50)`).

- [x] **Step 1:** Pruebas: `un usuario normal recibe 403`; `q encuentra por correo y por nombre sin acentos` (buscar «lopez» encuentra «López»); `filtra por rol, estado y verificado`; `pagina: 45 personas, page_size 20, page 3 → 5 filas y total 45`; `page fuera de rango devuelve items vacíos y total correcto`; `page_size 1000 responde 422`; `una persona sin mensajes tiene last_activity_at nulo y questions_count 0 y aparece al ordenar por activity y por questions`; `ordena por preguntas descendente`.
- [x] **Step 2:** Ejecutar. Esperado: FAIL.
- [x] **Step 3:** Implementar con una sola consulta agregada (subconsulta de mensajes por usuario unida con `outerjoin`); usar `func.immutable_unaccent` como en `retrieval.py`. Poner nulos al final en el orden por actividad.
- [x] **Step 4:** Ejecutar `uv run pytest tests/test_admin_users.py -q`. Esperado: PASS. Commit `feat(admin): paginated user list`.

### Task 1.3: cambio de rol y desactivación con guardas

**Files:** Modify `app/services/admin/users.py`, `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_users.py`; borrar `PATCH /admin/users/{id}` de `routes.py`.

**Interfaces (Produces):**
- `class AdminRuleError(Exception)` con `code: str` y `message: str`; códigos `cannot_modify_self` y `last_admin`. El router los traduce a **409** con `detail={"code": ..., "message": ...}` (formato que `extractErrorMessage` ya entiende).
- `update_user(db, *, actor: User, target_id: int, role: UserRole | None, is_active: bool | None) -> User`: aplica las guardas, sube `token_version` al desactivar, y registra `USER_ROLE_CHANGED` (detail `{"from": …, "to": …}`), `USER_DEACTIVATED` o `USER_REACTIVATED`. No hace nada (ni registra) si el valor no cambia.
- `PATCH /admin/users/{user_id}` recibe `AdminUserUpdate(role?, is_active?)`.

- [x] **Step 1:** Pruebas: `un administrador no puede cambiar su propio rol ni desactivarse (409 cannot_modify_self)`; `no se puede quitar el rol ni desactivar al último administrador activo (409 last_admin)`; `con dos administradores sí se puede degradar a otro`; `desactivar invalida su sesión` (su token anterior da 401 y `token_version` subió); `reactivar permite iniciar sesión`; `cada cambio queda en admin_audit_log con actor y objetivo`; `repetir el mismo valor no crea registro`; `un usuario inexistente da 404`.
- [x] **Step 2:** Ejecutar. Esperado: FAIL.
- [x] **Step 3:** Implementar `update_user` y el manejo de `AdminRuleError` en el router.
- [x] **Step 4:** Ejecutar la prueba. Esperado: PASS. Commit `feat(admin): role and active changes with guards and audit`.

### Task 1.4: eliminar cuenta

**Files:** Modify `app/services/admin/users.py`, `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_users.py`.

**Interfaces (Produces):** `delete_user(db, *, actor: User, target_id: int, confirm_email: str) -> None`: exige `confirm_email` igual al correo de la persona (sin distinguir mayúsculas), aplica las mismas guardas (`cannot_modify_self`, `last_admin`), borra al usuario (las conversaciones, mensajes y 👍/👎 se borran por `ON DELETE CASCADE`; `agent_lookups.user_id` queda nulo) y registra `USER_DELETED` con `detail={"role": …}` **sin** el correo. Error nuevo `confirmation_mismatch` (409). `DELETE /admin/users/{user_id}` con cuerpo `{"confirm_email": str}` responde 204.

- [x] **Step 1:** Pruebas: `sin la confirmación correcta responde 409 confirmation_mismatch y no borra`; `borra a la persona con sus conversaciones, mensajes y calificaciones`; `las consultas de agentes de esa persona se conservan sin usuario`; `el registro de auditoría sobrevive, con target_user_id y sin correo en detail`; `no puede eliminarse a sí mismo ni al último administrador`.
- [x] **Step 2:** Ejecutar. Esperado: FAIL.
- [x] **Step 3:** Implementar.
- [x] **Step 4:** Ejecutar. Esperado: PASS. Commit `feat(admin): delete account with typed confirmation`.

### Task 1.5: consulta del registro de auditoría

**Files:** Modify `app/services/admin/audit.py`, `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_audit.py`.

**Interfaces (Produces):** `list_audit(db, *, actor_id: int | None, action: AuditAction | None, page: int = 1, page_size: int = 20) -> tuple[list[AuditRow], int]` con `AuditRow(id, created_at, actor_name: str | None, action, target_user_id, detail)`; `GET /admin/audit` (más reciente primero).

- [x] **Step 1:** Pruebas: `lista lo más reciente primero`, `filtra por persona y por acción`, `devuelve actor_name nulo si el actor ya no existe`, `403 a un usuario normal`.
- [x] **Step 2:** Ejecutar. Esperado: FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): audit log endpoint`.

### Task 1.6: servicio del frontend

**Files:** Create `src/services/adminService.js`, `src/services/__tests__/adminService.test.js`.

**Interfaces (Produces):** `class AdminApiError extends Error { status: number; code: string | null }`; `listUsers(params: { q?, role?, active?, verified?, sort?, descending?, page?, pageSize? }) -> Promise<{ items, total, page, pageSize }>` (convierte a camelCase); `updateUser(id, { role?, isActive? })`; `deleteUser(id, confirmEmail)`; `listAudit({ actorId?, action?, page? })`. Todas usan `apiFetch` y `authHeaders`, y ante un error lanzan `AdminApiError` con el mensaje de `extractErrorMessage` y el `code` del `detail` si existe.

- [x] **Step 1:** Pruebas con `fetch` simulado: `listUsers arma la URL con solo los parámetros presentes`, `un 409 con detail.code lanza AdminApiError con ese code y su mensaje`, `un fallo de red lanza el mensaje de conexión de apiFetch`, `deleteUser envía confirm_email en el cuerpo`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): admin API client`.

### Task 1.7: pantalla de usuarios

**Files:** Create `src/admin/pages/Usuarios.js` (reemplaza el marcador), `src/admin/components/UserPanel.js`, `src/admin/hooks/useAdminList.js`, `src/admin/__tests__/Usuarios.test.js`.

**Interfaces:** `useAdminList(fetcher, params) -> { data, loading, error, reload }` (vuelve a pedir cuando cambian los parámetros; ignora respuestas viejas). `UserPanel({ user, currentUserId, onChanged, onClose })`.

**Comportamiento:** barra de herramientas con búsqueda (espera 300 ms), filtros Rol / Estado / Correo, orden por encabezado con flecha y `aria-sort`, y paginación; en móvil cada fila es una tarjeta. Al elegir una persona se abre un panel lateral con sus datos y tres acciones: **Cambiar rol** (lista cerrada Usuario/Administrador + `ConfirmDialog`), **Desactivar cuenta / Reactivar cuenta** (`ConfirmDialog`) y **Eliminar cuenta** (`ConfirmDialog` de tono `danger` con `requireText` = correo). En tu propia fila las acciones están deshabilitadas con la razón visible. Los códigos `cannot_modify_self`, `last_admin` y `confirmation_mismatch` se muestran con texto propio.

- [x] **Step 1:** Pruebas: `carga la primera página y muestra el total`; `escribir en la búsqueda pide la lista filtrada tras 300 ms`; `cambiar rol pide confirmación y solo entonces llama updateUser`; `eliminar deshabilita Confirmar hasta escribir el correo exacto`; `en la fila propia las acciones están deshabilitadas y se explica por qué`; `un error del servicio muestra ErrorState con Reintentar, no una lista vacía`; `sin resultados muestra EmptyState con la sugerencia de quitar filtros`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS.
- [x] **Step 5:** Verificar en el navegador (escritorio y móvil, API simulada con 45 personas): paginación, filtros, diálogo con Escape, tarjetas en móvil. Commit `feat(admin): users screen`.

### Task 1.8: pantalla de actividad y limpieza de lo viejo

**Files:** Create `src/admin/pages/Actividad.js` y `src/admin/__tests__/Actividad.test.js`. Delete `src/pages/AdministrarUsuarios.js`, `src/styles/AdministrarUsuario.css`. Modify `src/services/userService.js` (quitar `getAllUsers`, `updateUserRole`, `deleteUser`), `App.js` (quitar la ruta vieja `/AdministrarUsuario`).

- [x] **Step 1:** Pruebas de `Actividad`: `muestra quién, qué, a quién y cuándo en español` (p. ej. «Alexis cambió el rol de la persona 12: de usuario a administrador»), `filtra por acción`, `estado vacío con texto`, `error con Reintentar`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar y eliminar los archivos viejos. **Step 4:** Suite completa del frontend en verde y `npx react-scripts build` compila. Commit `feat(admin): activity screen; remove old user screen`.

---

# Fase 2: resumen

### Task 2.1: precios del modelo en configuración

**Files:** Modify `app/core/config.py`, `.env.example`. Test: `tests/test_admin_overview.py`.

**Interfaces (Produces):** `Settings.llm_price_input_per_million: Decimal = Decimal("0.25")` y `llm_price_output_per_million: Decimal = Decimal("2.00")` (precios de lista de `gpt-5-mini` ya usados por `scripts/ask.py`), documentados como estimación.

- [x] **Step 1–4:** Prueba `los precios tienen un valor por defecto positivo`; implementar; PASS. Commit `feat(admin): configurable model prices`.

### Task 2.2: endpoint del resumen

**Files:** Create `app/services/admin/overview.py`, `app/services/admin/attention.py`. Modify `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_overview.py`.

**Interfaces (Produces):**
- `class AttentionItem(kind: str, label: str, count: int, href: str)` y `collect_attention(db) -> list[AttentionItem]` (en esta fase devuelve `[]`; las fases 3 y 4 añaden proveedores).
- `build_overview(db, *, days: Literal[7, 30, 90], now: datetime | None = None) -> Overview` con `Overview(days, since, questions, active_users, new_users, answers_with_error, error_rate: float | None, feedback_up, feedback_down, feedback_rate: float | None, feedback_rated, tokens_input, tokens_output, cost_usd: Decimal, agent_lookups, series: list[DayPoint(date, questions)], attention)`. `error_rate` y `feedback_rate` son `None` sin datos (no 0). `cost_usd` = tokens × precios de `Settings`, redondeado a centavos con mitades hacia arriba. `series` trae **un punto por cada día del periodo**, en hora de la CDMX.
- `GET /admin/overview?days=7|30|90` (por defecto 30; otro valor → 422).

- [x] **Step 1:** Pruebas: `cuenta solo preguntas de personas dentro del periodo`; `active_users cuenta personas distintas`; `la serie incluye todos los días con 0 donde no hubo preguntas`; `un mensaje a las 23:30 de la CDMX cae en su día y no en el siguiente UTC`; `feedback_rate es None sin calificaciones y 0.89 con 40 positivas y 5 negativas, con feedback_rated = 45`; `error_rate cuenta respuestas con status error entre las respuestas`; `el costo usa los precios de Settings` (1,000,000 tokens de entrada y 1,000,000 de salida → 2.25); `days=15 responde 422`; `403 a un usuario normal`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): overview endpoint`.

### Task 2.3: pantalla de resumen

**Files:** Create `src/admin/components/StatBand.js`, `src/admin/components/DailyChart.js`, `src/admin/__tests__/Resumen.test.js`. Modify `src/admin/pages/Resumen.js`, `src/services/adminService.js` (`getOverview({ days })`).

**Interfaces:** `StatBand({ items: { label, value, hint? }[] })`: una sola banda con divisores finos y cifras en Fraunces con numerales tabulares. `DailyChart({ points })`: línea con Recharts en colores de la marca y una `<table>` equivalente solo para lectores de pantalla.

**Comportamiento:** selector de periodo (7/30/90 días, `role="radiogroup"`); cifras: Preguntas, Personas activas, Satisfacción, Respuestas con error, Costo estimado, Consultas de agentes. Si `feedbackRate` es `null`, la cifra dice «Sin calificaciones» (no 0 %); si hay datos, «89 % de 45 calificaciones». «Costo estimado» lleva la nota «Calculado con los precios de lista del modelo». Bloque «Requiere atención» con enlaces, o «Todo al día» si no hay nada.

- [x] **Step 1:** Pruebas: `muestra «Sin calificaciones» y no 0 % cuando no hay feedback`; `muestra 89 % de 45 calificaciones`; `cambiar de periodo vuelve a pedir con days=7`; `un error muestra ErrorState y no cifras en cero`; `la tabla equivalente de la gráfica tiene una fila por día`; `Todo al día cuando attention está vacío`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS.

### Task 2.4: retirar las estadísticas viejas

**Files:** Delete `src/pages/Estadisticas.js`, `src/pages/BienvenidaAdmin.js`, `src/components/NavBarAdmin.js`, `src/services/statsService.js`, `src/styles/BienvenidaAdmin.css`. Modify `App.js` (quitar rutas viejas y sus imports), `app/api/routes.py` (borrar `/admin/statistics` y el import que quede sin uso), `tests/test_api.py` (borrar las dos pruebas de estadísticas viejas; su cobertura pasa a `test_admin_overview.py`).

- [x] **Step 1:** Borrar y ajustar. **Step 2:** `uv run pytest -q` y la suite del frontend. Esperado: todo en verde. **Step 3:** `npx react-scripts build` compila sin advertencias nuevas. Verificar en el navegador el Resumen (escritorio y móvil). Commit `feat(admin): overview screen; remove old statistics`.

---

# Fase 3: calidad

### Task 3.1: tabla de revisiones

**Files:** Create `migrations/versions/20261025_13_message_reviews.py` (down_revision `20261025_12`). Modify `app/models/domain.py`. Test: `tests/test_admin_review.py`.

**Interfaces (Produces):** modelo `MessageReview(id, message_id → messages.id ON DELETE CASCADE, único, reviewer_id → users.id ON DELETE SET NULL, note: str | None (≤500), created_at)`.

- [x] **Step 1–4:** Prueba `una revisión por mensaje y se borra con el mensaje`; implementar; PASS; regenerar `database/schema.sql`. Commit `feat(admin): message reviews table`.

### Task 3.2: cola de calidad

**Files:** Create `app/services/admin/review.py`. Modify `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_review.py`.

**Interfaces (Produces):**
- `ReviewReason` = `"negative" | "error" | "uncited"`. Una respuesta entra si tiene 👎, o `status = error`, o (`status = complete`, sin citas y con al menos una llamada a herramienta en `tool_calls`: una negativa por alcance sin búsquedas **no** entra).
- `list_review_queue(db, *, reason: ReviewReason | None, reviewed: bool | None, page: int, page_size: int) -> tuple[list[ReviewItem], int]` con `ReviewItem(message_id, asked_at, reasons: list[ReviewReason], question: str, answer: str, citations: list[dict], tools: list[str], reviewed: bool, note: str | None)`. `question` es el mensaje de la persona inmediatamente anterior en la conversación. **Ningún campo identifica a la persona.**
- `GET /admin/review-queue` (más reciente primero).

- [x] **Step 1:** Pruebas: `una respuesta con 👎 entra con razón negative`; `una con error entra`; `una completa sin citas pero con búsquedas entra como uncited`; `una negativa por alcance (sin herramientas) no entra`; `una bien calificada y citada no entra`; `la pregunta mostrada es la anterior de esa conversación`; `el cuerpo de la respuesta no contiene nombre, correo ni user_id` (aserción sobre las claves del JSON y sobre el texto serializado); `filtra por reviewed y por reason`; `al eliminar a la persona sus filas desaparecen de la cola`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): review queue endpoint`.

### Task 3.3: marcar revisada y exportar como caso de evaluación

**Files:** Modify `app/services/admin/review.py`, `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_review.py`.

**Interfaces (Produces):**
- `mark_reviewed(db, *, actor: User, message_id: int, note: str | None) -> MessageReview` (idempotente; registra `REVIEW_MARKED` con `detail={"message_id": …}`); `POST /admin/review-queue/{message_id}/review` con `{"note": str | None}` (nota > 500 caracteres → 422); mensaje fuera de la cola → 404.
- `eval_case_for(db, message_id: int) -> dict` con el formato de `data/eval/*.jsonl`: `{"id": "p<message_id>", "question", "coverage": "full", "expected": [{"source": slug, "article": article}, …] (de las citas con source_slug), "notes": "Exportado de producción; etiquetas por verificar", "verified": false}`; `GET /admin/review-queue/{message_id}/eval-case`.

- [x] **Step 1:** Pruebas: `marcar dos veces no duplica ni falla`; `la revisión guarda la nota y quién`; `queda en la auditoría`; `eval-case devuelve verified false y expected desde las citas`; `un mensaje que no está en la cola da 404`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): mark reviewed and export eval case`.

### Task 3.4: aviso en «Requiere atención»

**Files:** Modify `app/services/admin/attention.py`, `tests/test_admin_overview.py`.

**Interfaces:** `collect_attention` suma `AttentionItem("review", "respuestas por revisar", count, "/admin/calidad")` cuando hay entradas sin revisar en la cola; no aparece con cero.

- [x] **Step 1–4:** Pruebas `aparece con 3 sin revisar` y `desaparece al marcarlas`; implementar reutilizando la consulta de la cola; PASS. Commit `feat(admin): review queue in attention list`.

### Task 3.5: pantalla de calidad

**Files:** Create `src/admin/pages/Calidad.js` (reemplaza el marcador), `src/admin/components/ReviewDetail.js`, `src/admin/__tests__/Calidad.test.js`. Modify `adminService.js` (`listReviewQueue`, `markReviewed`, `getEvalCase`).

**Comportamiento:** lista a la izquierda (pestañas «Por revisar» / «Revisadas», filtro por motivo con textos «Mal calificada», «Con error», «Sin citas») y detalle a la derecha: pregunta, respuesta renderizada con `MessageContent` y `CitationChips` del chat, herramientas consultadas, nota y dos acciones: **Marcar como revisada** y **Copiar como caso de evaluación** (copia la línea JSON al portapapeles y confirma «Copiado»). En móvil, lista y detalle son pantallas sucesivas con «Volver a la lista». Sin ningún nombre de persona.

- [x] **Step 1:** Pruebas: `muestra pregunta, respuesta y fuentes de la fila elegida`; `Marcar como revisada llama al servicio con la nota y la pasa a Revisadas`; `Copiar como caso de evaluación escribe una línea JSON válida en el portapapeles`; `cola vacía: «No hay respuestas por revisar»`; `error con Reintentar`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Verificar en el navegador (escritorio y móvil).

### Task 3.6: aviso de privacidad

**Files:** Modify `src/pages/AvisoLegal.js`. Test: `src/pages/__tests__/AvisoLegal.test.js`.

- [x] **Step 1:** Prueba: la sección «Protección de datos personales» contiene el texto «Las respuestas que reciban una calificación negativa o terminen en error pueden ser revisadas por el equipo de Avizum, sin nombre ni correo, para mejorar el servicio».
- [x] **Step 2:** FAIL. **Step 3:** Añadir el párrafo (conservando el estilo de la página). **Step 4:** PASS. Commit `feat(admin): quality screen and privacy notice`.

---

# Fase 4: fuentes

### Task 4.1: estado de las fuentes

**Files:** Create `app/services/admin/sources.py`. Modify `app/api/admin.py`, `app/schemas/admin.py`, `tests/test_admin_sources.py`.

**Interfaces (Produces):** `list_sources(db, *, today: date | None = None) -> list[SourceRow]` con `SourceRow(slug, title, kind, url, last_reform_date, retrieved_at, chunk_count, versions: int, review_due: bool, review_due_since: date | None)`; una fila por fuente **vigente** (`is_current`), ordenada por tipo y título; `review_due` es verdadero cuando `retrieved_at + 365 días < today`. `pending_sanctions(db) -> int` cuenta filas de `legal_sanctions` con `status = pending`. `GET /admin/sources` devuelve `{"sources": [...], "pending_sanctions": int}`.

- [x] **Step 1:** Pruebas: `solo lista la versión vigente de cada fuente y cuenta cuántas versiones hay`; `chunk_count cuenta los fragmentos de la versión vigente`; `review_due es verdadero a los 366 días y falso a los 365`; `una fuente sin fragmentos (el acuerdo de agentes) aparece con 0`; `pending_sanctions cuenta solo las pendientes`; `403 a un usuario normal`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): sources status endpoint`.

### Task 4.2: avisos de fuentes y sanciones

**Files:** Modify `app/services/admin/attention.py`, `tests/test_admin_overview.py`.

**Interfaces:** `collect_attention` suma `AttentionItem("sources", "fuentes por revisar este año", n, "/admin/fuentes")` y `AttentionItem("sanctions", "filas de sanciones sin revisar", n, "/admin/fuentes")`; cada una solo si `n > 0`.

- [x] **Step 1–4:** Pruebas `aparecen con datos` y `no aparecen con cero`; implementar; PASS. Commit `feat(admin): source and sanction alerts`.

### Task 4.3: pantalla de fuentes

**Files:** Create `src/admin/pages/Fuentes.js` (reemplaza el marcador), `src/admin/__tests__/Fuentes.test.js`. Modify `adminService.js` (`listSources`).

**Comportamiento:** fuentes agrupadas por tipo con filtro «Por revisar»; cada fila: título (enlace a la página oficial en pestaña nueva), fecha de reforma o de consulta, fragmentos, versiones y un `StatusBadge` «Por revisar» (con fecha desde la que lo está) o «Al día». Arriba, una nota «La actualización se hace con los scripts; aquí solo se vigila», y la cifra de sanciones sin revisar. En móvil, tarjetas.

- [x] **Step 1:** Pruebas: `agrupa por tipo`; `«Por revisar» lleva texto además de color`; `el enlace abre en pestaña nueva con rel noopener`; `el filtro «Por revisar» oculta las demás`; `error con Reintentar`.
- [x] **Step 2:** FAIL. **Step 3:** Implementar. **Step 4:** PASS. Commit `feat(admin): sources screen`.

---

# Fase 5: cierre

### Task 5.1: verificación final y documentación

**Files:** Modify `docs/superpowers/specs/2026-10-08-asistente-legal-design.md` (bitácora), `README.md` (mención breve del panel).

- [x] **Step 1:** Ejecutar `cd backend && uv run pytest -q` y `cd frontend && CI=true npx react-scripts test --watchAll=false` y `npx react-scripts build`. Esperado: todo en verde, sin advertencias nuevas.
- [x] **Step 2:** En el navegador, con la API simulada y con datos realistas, capturar las cinco pantallas en 1440×900 y 390×844 y revisar: foco visible con Tab en cada pantalla, Escape cierra los diálogos, ninguna pantalla muestra cero ante un error (apagar la API y recargar), un usuario `rol: user` nunca ve `/admin`.
- [x] **Step 3:** Con el backend real y una base local (`docker compose up -d db`, `alembic upgrade head`), crear un administrador con `scripts.promote_admin` y recorrer: listar, cambiar rol de otra persona, desactivar, eliminar, marcar una respuesta revisada. Confirmar que cada acción aparece en Actividad.
- [x] **Step 4:** Escribir la bitácora en el spec (qué se hizo, medición, hallazgos) y la línea del README. Commit `docs(admin): admin console log`.

---

## Self-review

- **Cobertura del spec:** hallazgos 1, 2, 13–17, 20 → Fase 0; 3, 6–8, 11, 12, 18, 19 → Fase 1; 4, 5, 9, 10 → Fase 2; cola de calidad, exportación y privacidad (decisión 1) → Fase 3; fuentes y revisión anual → Fase 4; eliminar cuentas (decisión 2) → Task 1.4; las cinco fases (decisión 3) y marca Avizum (decisión 4) → restricciones globales. El hallazgo 12 (`console.log` de usuarios) desaparece con la pantalla vieja (Task 1.8).
- **Consistencia de tipos:** `AdminRuleError.code` ∈ {`cannot_modify_self`, `last_admin`, `confirmation_mismatch`}, usados igual en 1.3, 1.4 y 1.7; `AuditAction` definido en 1.1 y usado en 1.3, 1.4, 1.5 y 3.3; `AttentionItem`/`collect_attention` definidos en 2.2 y ampliados en 3.4 y 4.2; `Page[T]` y `AdminApiError` definidos antes de usarse.
- **Proporción:** el plan nombra archivos, firmas, valores del spec y las aserciones de cada prueba; los cuerpos los escribe quien implementa.

## Estado

Completado el 2026-10-29 según el código y el historial de commits; las pruebas no se volvieron a ejecutar para esta nota.
