# Operations: logging, error tracking and health

## Settings to set in production (`backend/.env`)

| Variable | Production value |
| --- | --- |
| `ENVIRONMENT` | `production` (JSON logs by default; startup refuses unsafe config) |
| `LOG_FORMAT` | `auto` (JSON in production, text otherwise) or force `json` / `text` |
| `LOG_LEVEL` | `INFO` |
| `SENTRY_DSN` | Project DSN. Leave empty to disable error tracking entirely |
| `SENTRY_ENVIRONMENT` | Optional; defaults to `ENVIRONMENT` |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` (default, no tracing) unless you accept the cost |
| `GIT_SHA` | Commit sha injected by the deploy; reported as the Sentry release |

Run uvicorn normally; the app silences uvicorn's own access log and writes one line per request itself
(`logger=app.access`: method, route template, status, duration_ms, request_id, user_id).

## Request ids

Every response carries `X-Request-ID`. An incoming `X-Request-ID` is reused only if it matches `[A-Za-z0-9._-]{8,64}`;
otherwise a new one is generated. Unhandled errors answer `500 {"detail": "Internal server error", "request_id": "..."}`
so a user can quote the id and you can find the log line.

## Health

- `GET /api/v1/health`: liveness, no dependencies.
- `GET /api/v1/health/ready`: readiness, runs `SELECT 1`; `503 {"status": "unavailable"}` on failure (no error text).

## Privacy rules (hard constraints)

Chat text, e-mail addresses, passwords, JWTs and verification/reset tokens must never reach logs or error reports.

- Log route templates (`/api/v1/conversations/{conversation_id}`), never raw URLs or query strings.
- Never log request bodies or the `Authorization` header; the access log records only the user id from the token `sub`.
- Unhandled exceptions are logged as type plus stack frames, without the exception message (database errors can embed
  query parameters).
- Sentry runs with `send_default_pii=False`, `include_local_variables=False`, `max_request_body_size="never"`, and the
  `before_send` / `before_breadcrumb` hooks in `app/core/observability.py` remove bodies, cookies, query strings,
  sensitive headers, the user object, exception message text, and any value that looks like an e-mail, JWT or
  43-character url-safe token. When adding new logging, do not put user-provided values in messages or `extra`.

## Sentry is a third-party processor

If `SENTRY_DSN` is set, Sentry receives error events (stack traces, route, status, release, request id) from this
service. It must be named as a processor in the privacy notice (aviso de privacidad), including where its data is
hosted. Leave `SENTRY_DSN` empty to keep everything on your own infrastructure.
