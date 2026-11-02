# Despliegue de Avizum (guía paso a paso)

Pila elegida para unos ~10 usuarios. Los precios y planes de cada proveedor cambian: revisa su página antes de
contratar y no los des por sentados.

| Pieza | Servicio | Notas |
| --- | --- | --- |
| Frontend (React, estático) | Cloudflare Pages | `npm run build` -> carpeta `build/` |
| Backend (FastAPI) | Docker en Render | `backend/Dockerfile`; alternativas Railway o Fly.io (al final) |
| Base de datos | Neon (PostgreSQL con pgvector) | |
| Correo | Resend | verificación de correo y restablecimiento de contraseña |
| Errores | Sentry | opcional (`SENTRY_DSN` vacío = desactivado) |
| Modelo de IA | OpenAI | `OPENAI_API_KEY` |

Convención de dominios usada abajo (cámbialos por los tuyos): web en `https://avizum.example.org`, API en
`https://api.avizum.example.org`.

## Lista de verificación general

- [ ] 0. **Urgente antes de nada: rotar la contraseña de Neon filtrada** (sección "Antes de abrir al público").
- [ ] 1. Dominio comprado y DNS administrable (Cloudflare recomendado).
- [ ] 2. Proyecto Neon creado, extensiones habilitadas, cadenas de conexión guardadas.
- [ ] 3. Servicio web en Render creado desde el Dockerfile, variables de entorno puestas, migraciones corridas.
- [ ] 4. Cloudflare Pages creado, `REACT_APP_API_URL` puesta, CSP revisada.
- [ ] 5. Resend: dominio verificado (SPF, DKIM, DMARC) y `REQUIRE_VERIFIED_EMAIL` activado.
- [ ] 6. Primer administrador creado.
- [ ] 7. Datos legales cargados (fuentes e índice).
- [ ] 8. Respaldos cifrados configurados y restauración probada.
- [ ] 9. Prueba de humo completa.
- [ ] 10. Lista "Antes de abrir al público" cumplida.

## 1. Dominio y DNS

1. Compra el dominio (cualquier registrador) y, si quieres, delega los DNS a Cloudflare (gratis): así administras todo en un solo panel.
2. Decide los subdominios: `avizum.example.org` (o el dominio raíz) para la web y `api.avizum.example.org` para la API.
3. Los registros concretos (CNAME a Pages, CNAME a Render, SPF/DKIM de Resend) se crean en los pasos siguientes, cuando cada servicio te dice qué valor poner.

## 2. Neon (base de datos)

1. Crea cuenta y un proyecto en neon.tech. Elige una región cercana a la de Render (misma costa de EE. UU. si es posible) para reducir latencia. Anota la versión mayor de PostgreSQL del proyecto (la usa el respaldo, `PG_MAJOR`).
2. En **Connection Details** hay dos tipos de cadena:
   - **Directa** (host sin `-pooler`): úsala para **Alembic/migraciones** y para respaldos (`pg_dump`). El pooler en modo transacción no es adecuado para DDL ni para `pg_dump`, y las sentencias preparadas de psycopg dan problemas con él.
   - **Pooled** (host con `-pooler`): sirve si la base se queda sin conexiones. Con ~10 usuarios no hace falta; usa la directa también para la API y evita problemas con sentencias preparadas de psycopg.
   - Conclusión para este proyecto: **usa la cadena directa en todo** (API, migraciones y respaldos). Si algún día cambias la API al pooler, habría que añadir `prepare_threshold=None` a la conexión de psycopg y probar el chat.
3. Convierte la cadena al formato de SQLAlchemy + psycopg v3 y exige TLS:

   ```
   postgresql+psycopg://USUARIO:CONTRASENA@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require
   ```

   (Neon la entrega como `postgresql://...`; añade `+psycopg` después de `postgresql`.) Para el respaldo se usa la forma sin `+psycopg` (`postgresql://...?sslmode=require`).
4. **Extensiones.** Las migraciones ejecutan `CREATE EXTENSION IF NOT EXISTS` para `pg_trgm` (migración 03), `vector` y `unaccent` (migración 04); no tienes que crearlas a mano. Neon incluye las tres y permite crearlas al rol propietario por defecto (el que trae la cadena de conexión). Si prefieres crearlas tú antes, en el SQL Editor de Neon: `CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS unaccent;`. Si una migración falla con "permission denied to create extension", la cadena usa un rol sin permiso: usa el rol propietario.
5. El esquema lo crea **solo Alembic**. No cargues `database/schema.sql` (documenta tablas heredadas y no coincide con el modelo actual).
6. Neon pausa los proyectos inactivos en algunos planes: la primera petición tras una pausa puede tardar unos segundos. Es normal.

## 3. Render (backend)

1. Sube el repositorio a GitHub (ya está) y en Render: **New > Web Service > Build and deploy from a Git repository**.
2. Ajustes:
   - **Language/Runtime**: Docker.
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Build Context Directory**: `backend`
   - **Health Check Path**: `/api/v1/health`
   - **Pre-Deploy Command**: `sh scripts/predeploy.sh` (corre `alembic upgrade head` con la `DATABASE_URL` del servicio antes de que arranque la versión nueva; si falla, el despliegue se cancela y la versión anterior sigue sirviendo. Si tu plan no ofrece pre-deploy, corre `sh scripts/predeploy.sh` desde la pestaña Shell tras cada despliegue.)
   - **Instancias**: 1. La API usa **un solo worker** a propósito: el limitador de peticiones (`app/core/rate_limit.py`) guarda sus contadores en la memoria del proceso; con N workers (o N instancias) cada límite se multiplicaría por N. Para escalar, sube el tamaño de la máquina, no el número de procesos, hasta que el limitador pase a Redis.
3. Variables de entorno (Environment). Genera el secreto con `openssl rand -hex 32` en tu máquina y pégalo solo en el panel de Render (nunca en el repositorio):

   | Variable | Valor |
   | --- | --- |
   | `ENVIRONMENT` | `production` (activa JSON en logs y las comprobaciones de arranque, ver abajo; oculta `/docs`) |
   | `DATABASE_URL` | cadena de Neon con `postgresql+psycopg://` y `?sslmode=require` |
   | `JWT_SECRET_KEY` | salida de `openssl rand -hex 32` (distinta por entorno) |
   | `CORS_ORIGINS` | `https://avizum.example.org` (sin barra final; varios separados por coma; nada de localhost) |
   | `FRONTEND_URL` | `https://avizum.example.org` (base de los enlaces de los correos, sin barra final) |
   | `TRUSTED_PROXY_COUNT` | `1` con Render directo; `2` si el dominio de la API pasa por el proxy naranja de Cloudflare delante de Render. Ver "IP del cliente" |
   | `RESEND_API_KEY` | clave de Resend (vacía: los correos solo se escriben en el log) |
   | `MAIL_FROM` | `Avizum <no-reply@avizum.example.org>` (dominio verificado en Resend; si queda `example.com` y hay clave, la app no arranca) |
   | `REQUIRE_VERIFIED_EMAIL` | `false` hasta comprobar que Resend entrega; luego `true` |
   | `OPENAI_API_KEY` | clave de OpenAI |
   | `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL` | opcional; por defecto `gpt-5-mini` y `text-embedding-3-small` (el modelo de embeddings debe ser el mismo con el que se indexó) |
   | `GOOGLE_CLIENT_ID` | ID de cliente OAuth web (público); vacío desactiva el acceso con Google |
   | `SENTRY_DSN` | DSN del proyecto de Sentry (opcional; vacío = desactivado) |
   | `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` | opcional; por defecto `ENVIRONMENT` y `0.0` |
   | `GIT_SHA` | opcional; sha del commit, se reporta como release de Sentry |
   | `LOG_LEVEL`, `LOG_FORMAT` | `INFO` y `auto` |
   | `DAILY_USER_COST_USD_LIMIT` | tope de gasto por usuario en 24 h (por defecto `0.25`; `0` lo desactiva) |
   | `GLOBAL_DAILY_COST_USD_LIMIT` | interruptor global de gasto en 24 h (por defecto `0` = apagado; **ponle un valor** mientras sea una prueba abierta) |
   | `CHAT_DAILY_MESSAGE_LIMIT` | mensajes por usuario y día (por defecto `40`) |
   | `LLM_PRICE_INPUT_PER_MILLION`, `LLM_PRICE_OUTPUT_PER_MILLION` | precios USD por millón de tokens con los que se calcula el gasto; actualízalos si OpenAI cambia sus tarifas |
   | `UMA_VALUE`, `UMA_VALID_FROM`, `UMA_VALID_UNTIL` | actualizar cada febrero (INEGI) |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | por defecto `60` |

   No definas `PORT` (Render la inyecta; el contenedor usa 8000 si falta). No cambies `FORWARDED_ALLOW_IPS` ni lo pongas a `*` (ver abajo). **No** actives `AI_ALLOW_LEGACY_FAISS_DESERIALIZATION` ni nada del directorio `ai/`.
4. **Qué bloquea el arranque (`production_problems()`).** Con `ENVIRONMENT=production` la app se niega a arrancar (el servicio queda en "Deploy failed" y el log dice `Unsafe production configuration: ...`) si:
   - `JWT_SECRET_KEY` es el valor de desarrollo o mide menos de 32 caracteres: un secreto conocido permitiría falsificar sesiones de cualquier usuario, incluido un administrador.
   - Hay `RESEND_API_KEY` pero `MAIL_FROM` aún contiene `example.com`: los correos se rechazarían en silencio y nadie podría verificar su cuenta.
   - `CORS_ORIGINS` contiene `localhost`: dejaría a cualquier página local hablar con la API de producción con credenciales.
5. Dominio propio de la API: en Render, **Settings > Custom Domains**, añade `api.avizum.example.org` y crea en tu DNS el CNAME que te indica. Render emite el certificado TLS solo.
6. Despliega y comprueba desde fuera: `curl https://api.avizum.example.org/api/v1/health` (`{"status":"ok"}`) y `/api/v1/health/ready` (`{"status":"ready"}`, prueba la base de datos).

### IP del cliente detrás de un proxy

Los límites por dirección (login, registro, búsqueda de agentes) necesitan la IP real. Detrás de Render, todas las peticiones llegan desde el proxy, así que sin configuración todos los usuarios compartirían un mismo contador. `TRUSTED_PROXY_COUNT=N` indica cuántos proxies de confianza añaden su dirección al final de `X-Forwarded-For`; la IP del cliente es la entrada N contando desde la derecha. Lo que el cliente escriba a la izquierda se ignora, y si la cabecera trae menos de N entradas se usa la dirección del socket. Con `0` (por defecto) la cabecera no se lee nunca, así no se puede falsificar en desarrollo.

Verifica el valor correcto una vez (la IP no se escribe en los logs a propósito): desde una red, haz intentos de login fallidos repetidos con un correo inexistente hasta recibir 429 (el límite está en `app/api/routes.py`, `rate_limit("login", ...)`); desde otra red distinta (por ejemplo datos del celular) el login debe seguir respondiendo 401. Si ambas redes reciben 429, el valor es demasiado bajo (todos comparten IP); si nadie recibe 429, es demasiado alto o `0`.

El contenedor arranca uvicorn con `--proxy-headers`, pero con `FORWARDED_ALLOW_IPS=127.0.0.1` (nadie): **no pongas `*`**, porque uvicorn confiaría en la entrada más a la izquierda de `X-Forwarded-For`, que controla el cliente.

## 4. Cloudflare Pages (frontend)

1. Cloudflare > Workers & Pages > Create > Pages > Connect to Git, elige el repositorio.
2. Ajustes de build:
   - **Root directory**: `frontend`
   - **Build command**: `CI=false npm run build` (con `CI=true` CRA convierte los avisos de ESLint en errores; hoy hay avisos conocidos)
   - **Build output directory**: `build`
   - **Variable `NODE_VERSION`**: `24` (la misma que usa el CI)
3. Variables de entorno de build (se incrustan en el JavaScript; son públicas, no pongas secretos):
   - `REACT_APP_API_URL` = `https://api.avizum.example.org/api/v1`
   - `REACT_APP_GOOGLE_CLIENT_ID` = el mismo ID que `GOOGLE_CLIENT_ID` del backend (vacío oculta el botón)
4. `frontend/public/_redirects` hace que las rutas de React (`/login`, `/chat`...) sigan funcionando al recargar, y `frontend/public/_headers` añade las cabeceras de seguridad. Ambos se copian a `build/` solos.
5. **Antes de desplegar, edita `_headers`**: sustituye `https://api.example.org` por el origen real de tu API (sin `/api/v1`).
6. Custom domain: en el proyecto de Pages, **Custom domains > Set up a domain** (`avizum.example.org`). Cloudflare crea el DNS si el dominio está en su cuenta.
7. En Google Cloud Console (credenciales OAuth web), añade `https://avizum.example.org` a los orígenes JavaScript autorizados.

### Content-Security-Policy: de Report-Only a obligatoria

`_headers` envía la política como `Content-Security-Policy-Report-Only`: el navegador no bloquea nada, solo anota en la consola lo que bloquearía. Se hizo así porque la lista se dedujo del código sin un navegador real, y una política obligatoria escrita a ciegas podría romper el inicio de sesión con Google. Lo que permite:

- Scripts: propios y `https://accounts.google.com/gsi/client` (Google Sign-In). CRA no incrusta scripts en `index.html`.
- Estilos: propios, `'unsafe-inline'` (estilos en línea de React y CRA/Tailwind), Google Fonts, jsdelivr (bootstrap-icons) y `https://accounts.google.com/gsi/style`.
- Fuentes: `fonts.gstatic.com` y jsdelivr.
- Conexiones: el origen de la API y `https://accounts.google.com/gsi/`.
- Marcos: `https://accounts.google.com/gsi/` (botón y One Tap de Google). `frame-ancestors 'none'` impide que otros incrusten la web.
- Imágenes: propias, `data:` y `googleusercontent.com`.

Para activarla:

1. Despliega, abre el sitio en Chrome con las herramientas de desarrollador (Consola) y recorre: inicio, registro, login con correo, login con Google, chat con una respuesta completa, panel de administración, restablecer contraseña.
2. Busca mensajes `[Report Only] Refused to load ...`. Cada uno es algo que la política bloquearía: añade ese origen a la directiva correspondiente.
3. Cuando una pasada completa no muestre ninguno, cambia en `_headers` el nombre `Content-Security-Policy-Report-Only` por `Content-Security-Policy`, despliega y repite el recorrido. Si algo se rompe, vuelve a Report-Only (un cambio de una línea).

HSTS (`Strict-Transport-Security`) lo envía el borde (Cloudflare Pages vía `_headers` para la web; Render para la API), no la aplicación. Cuando todo funcione con HTTPS, valora añadir `preload` solo si estás seguro: es difícil de revertir.

La API, por su parte, añade a **todas** sus respuestas `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store` (`SecurityHeadersMiddleware` en `app/main.py`), y el flujo SSE del chat envía además `Cache-Control: no-cache` y `X-Accel-Buffering: no` para que ningún proxy lo guarde en búfer.

## 5. Resend (correo)

1. Crea cuenta en resend.com y **Domains > Add Domain** con tu dominio (o un subdominio como `mail.avizum.example.org`).
2. Resend muestra registros DNS; créalos en Cloudflare con el proxy **desactivado** (nube gris) para los CNAME/TXT de correo:
   - **SPF** (TXT en el subdominio de envío) y **DKIM** (TXT/CNAME `resend._domainkey...`): los valores exactos los da Resend; copia y pega.
   - **DMARC** (TXT en `_dmarc.avizum.example.org`): empieza con `v=DMARC1; p=none; rua=mailto:dmarc@avizum.example.org` para observar; endurece a `quarantine` cuando los informes salgan limpios.
3. Pulsa **Verify** en Resend (puede tardar de minutos a horas).
4. Crea una API key con permiso de envío solamente y ponla en `RESEND_API_KEY` en Render; ajusta `MAIL_FROM` a una dirección de ese dominio.
5. Registra una cuenta de prueba: debe llegar el correo de verificación. Solo entonces pon `REQUIRE_VERIFIED_EMAIL=true`.

## 6. Primer administrador

1. Regístrate normalmente en la web con tu correo.
2. En Render, pestaña **Shell** del servicio (o `docker exec` si lo corres en otro lado):

   ```bash
   python -m scripts.promote_admin tu-correo@example.org
   ```

   (La imagen ya tiene el entorno virtual en el `PATH`; no hace falta `uv run`.) Cierra sesión y vuelve a entrar. Desde ahí los demás roles se gestionan en el panel de administración.

## 7. Carga inicial de datos (fuentes legales e índice)

La imagen de producción **no** incluye PyMuPDF ni tiktoken (grupo `ingest`) ni el directorio `data/`, a propósito: son herramientas de uso puntual y solo agrandarían la superficie de ataque. Estos pasos se corren **desde tu máquina**, con el repositorio clonado, apuntando a la base de producción:

```bash
cd backend
uv sync --group dev --group ingest
# En una terminal NUEVA, sin guardar en historial, con la cadena DIRECTA de Neon y tu clave de OpenAI:
export DATABASE_URL='postgresql+psycopg://...neon.tech/neondb?sslmode=require'
export OPENAI_API_KEY='...'
uv run alembic upgrade head                       # solo si aún no corrió el pre-deploy
uv run python -m scripts.fetch_sources            # descarga y registra las fuentes oficiales (data/sources.json)
uv run python -m scripts.ingest_sources           # parte, vectoriza y guarda en legal_chunks (--only <slug>, --force)
unset DATABASE_URL OPENAI_API_KEY
```

Precauciones: (a) esto escribe en producción; haz antes un respaldo manual (workflow "Backup DB") y revisa dos veces que `DATABASE_URL` apunta donde crees. (b) No pegues las cadenas en un archivo del repositorio (`.env` está ignorado por git, pero sigue siendo un archivo en tu disco: bórralo al terminar). (c) Los embeddings cuestan dinero en OpenAI. (d) Las sanciones verificadas están en `data/sanctions/verified.json`; `scripts.sanctions extract` las carga en la base (ver `docs/superpowers/specs/`).

**Reformas legales**: hasta que existan las fases C/D de vigilancia de fuentes (posteriores al lanzamiento), reindexar es un proceso **manual**: ante una reforma, vuelve a correr `fetch_sources` y `ingest_sources` (con `--only <slug>` o `--force`) como arriba, y revisa las sanciones afectadas.

## 8. Respaldos cifrados

El workflow `.github/workflows/backup-db.yml` corre a diario (y a demanda en Actions > Backup DB > Run workflow): `pg_dump` de Neon, cifrado con `age` y subida como artefacto con 14 días de retención.

**Por qué el cifrado es obligatorio.** El repositorio es **público**: los artefactos de un repositorio público los puede descargar cualquier usuario de GitHub con sesión iniciada. Un volcado contiene datos personales (correos, conversaciones, hashes de contraseña). Subirlo sin cifrar equivale a publicarlo. Por eso el workflow solo sube un `.age` cifrado con la clave **pública**, y falla antes de volcar nada si esa clave falta (no existe ruta que suba un volcado sin cifrar). La clave **privada** no se sube nunca a GitHub.

Configuración (una sola vez):

1. En tu máquina: `age-keygen -o avizum-backup.key` (imprime la clave pública `age1...`). Guarda `avizum-backup.key` **fuera del repositorio**, en un gestor de contraseñas y en una copia aparte (sin ella los respaldos son inservibles).
2. GitHub > Settings > Secrets and variables > Actions: secreto `DATABASE_URL_BACKUP` (cadena **directa** de Neon con `postgresql://` y `?sslmode=require`; idealmente de un rol de solo lectura) y `AGE_PUBLIC_KEY` (la clave `age1...`; puede ser variable o secreto). Opcional: variable `PG_MAJOR` si Neon no usa PostgreSQL 17 (el cliente `pg_dump` debe ser de versión igual o mayor que el servidor).
3. Ejecuta el workflow una vez a mano y verifica que sube `avizum-db-backup`.

**Alternativa**: un bucket privado (Cloudflare R2, Backblaze B2, S3) con acceso solo por clave. Cambia el último paso del workflow por una subida con credenciales en secretos. Sigue siendo buena idea cifrar con `age` antes de subir.

**Restauración** (probar al menos una vez a una base de prueba, no a producción):

```bash
# 1. Descarga el artefacto desde la pestaña Actions y descomprime el .zip.
# 2. Descifra con tu clave privada
age --decrypt -i avizum-backup.key -o avizum.dump avizum-YYYYMMDDTHHMMSSZ.dump.age
# 3. Crea una base vacía (en Neon: nueva rama o base) con las extensiones disponibles y restaura
pg_restore --no-owner --no-privileges --exit-on-error -d "postgresql://USUARIO:CONTRASENA@HOST/baseNueva?sslmode=require" avizum.dump
# 4. Comprueba, y borra el volcado en claro
psql "postgresql://.../baseNueva?sslmode=require" -c "select count(*) from users; select version_num from alembic_version;"
shred -u avizum.dump
```

El volcado trae los `CREATE EXTENSION` de `vector`, `pg_trgm` y `unaccent`. Para volver a producción tras un desastre, apunta `DATABASE_URL` de Render a la base restaurada. Neon también ofrece restauración a un punto en el tiempo (historial limitado según el plan): úsala como primera opción para errores recientes.

## 9. Prueba de humo (después de cada despliegue importante)

- [ ] `GET /api/v1/health` y `/api/v1/health/ready` responden 200.
- [ ] Registro de una cuenta nueva (con casilla de términos).
- [ ] Llega el correo de verificación; el enlace verifica la cuenta.
- [ ] Inicio de sesión con correo y contraseña.
- [ ] Inicio de sesión con Google, con la casilla de términos marcada (y sin marcar: debe pedirla).
- [ ] Chat: una pregunta de tránsito responde en streaming, con citas.
- [ ] Panel de administración: la lista de usuarios y el resumen cargan (con la cuenta administradora).
- [ ] Restablecer contraseña: llega el correo y el enlace permite cambiarla.
- [ ] Un 429 aparece al abusar (ver "IP del cliente") y no bloquea a otra red.
- [ ] Consola del navegador sin mensajes de CSP inesperados.
- [ ] Un error provocado a propósito aparece en Sentry sin correos ni texto de chat.

## 10. Reversión (rollback)

- **Código del backend**: en Render, **Events/Deploys > Rollback** a un despliegue anterior. Ojo: las migraciones **no** se deshacen solas. Si la versión nueva traía una migración, la anterior debe ser compatible con el esquema nuevo; si no lo es, primero `alembic downgrade -1` (desde un entorno con la cadena directa de Neon, tras un respaldo manual) y luego el rollback. Las migraciones destructivas requieren restaurar un respaldo.
- **Frontend**: en Cloudflare Pages, **Deployments > Rollback** (o "Promote" de un despliegue anterior).
- **Datos**: restauración a punto en el tiempo de Neon o el respaldo cifrado (sección 8).
- **Secretos comprometidos**: rota primero el secreto (Neon, OpenAI, Resend, `JWT_SECRET_KEY`; cambiar este último cierra todas las sesiones) y luego redespliega.

## Antes de abrir al público

- [ ] **Rotar la contraseña de Neon filtrada (urgente).** El commit `48a6c2f` incluyó una credencial y el repositorio es **público**: asume que ya fue copiada. En Neon, restablece la contraseña del rol (o crea un rol nuevo, cambia `DATABASE_URL` y borra el viejo), actualiza `DATABASE_URL` en Render y los secretos de GitHub, y revisa los registros de acceso de Neon. Borrar el archivo del historial con git no basta; la rotación es lo único que cuenta. Revisa también que ninguna otra clave (OpenAI, Resend, Google) haya estado en el historial.
- [ ] **Revisión por un abogado** de los Términos (`Terminos.js`) y el Aviso de privacidad (`AvisoLegal.js`); hoy son borradores. Al cambiar el texto publicado, sube `TERMS_VERSION` en `backend/app/core/config.py` y `TERMINOS_VERSION` en `Terminos.js`.
- [ ] **Completar los marcadores legales** de `AvisoLegal.js`: `[Nombre del responsable]`, `[Domicilio del responsable]`, plazos de conservación (cuenta, conversaciones, registros técnicos), `[correo para derechos ARCO]`, `[Proveedor de correo]`, `[Proveedor de hospedaje]`.
- [ ] **Nombrar en el aviso de privacidad a los encargados**: Neon (base de datos), Render (alojamiento de la API), Cloudflare (frontend y DNS), Resend (correo), OpenAI (las preguntas del chat se envían para generar la respuesta), Sentry (errores; ver `docs/operations.md`) y Google (inicio de sesión), indicando para qué datos y dónde se alojan.
- [ ] **Hoja de revisión de sanciones** (`data/sanctions/review/`): la revisión humana debe estar hecha y aplicada (`scripts.sanctions apply`) antes de que el asistente dé montos de multas con aire de autoridad.
- [ ] `GLOBAL_DAILY_COST_USD_LIMIT` con un valor y un límite de gasto/alerta en el panel de OpenAI.
- [ ] CSP en modo obligatorio (o decisión consciente de dejarla en Report-Only), respaldo restaurado al menos una vez, prueba de humo completa.
- [ ] `REQUIRE_VERIFIED_EMAIL=true` con Resend funcionando.
- [ ] Prueba de carga ligera del chat (varias preguntas simultáneas) para confirmar que el único worker aguanta.

## Notas para Railway y Fly.io

El contenedor es el mismo: contexto `backend/`, `backend/Dockerfile`, variables de la tabla de arriba.

- **Railway**: New Project > Deploy from GitHub repo; en Settings pon *Root Directory* `backend` (usa el `Dockerfile` ahí), *Healthcheck Path* `/api/v1/health` y como *Pre-deploy command* `sh scripts/predeploy.sh`. Railway inyecta `PORT`. Mantén una sola réplica. Revisa cuántos proxies hay delante para `TRUSTED_PROXY_COUNT` con la prueba de dos redes.
- **Fly.io**: `fly launch --dockerfile backend/Dockerfile --no-deploy` (desde la raíz, con el contexto en `backend/`), define `internal_port = 8000` en `fly.toml`, `[deploy] release_command = "sh scripts/predeploy.sh"`, un chequeo HTTP a `/api/v1/health`, y `fly secrets set` para las variables sensibles. Usa `min_machines_running = 1` y **una sola máquina** (el limitador está en memoria). Verifica `TRUSTED_PROXY_COUNT` con la prueba de dos redes.
