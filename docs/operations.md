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

## Chat spending limits

Every answer calls OpenAI, so the chat has a durable budget over a rolling 24 hours, computed from the append-only
`chat_usage` ledger (one row per accepted turn) times `LLM_PRICE_INPUT_PER_MILLION` / `LLM_PRICE_OUTPUT_PER_MILLION`,
so it holds across workers and restarts. The daily message limit (`CHAT_DAILY_MESSAGE_LIMIT`, Mexico City calendar day)
counts the same rows. `DAILY_USER_COST_USD_LIMIT` (default 0.25, roughly 50 normal questions) caps each account,
administrators included; `GLOBAL_DAILY_COST_USD_LIMIT` (default 0 = off) is a circuit breaker over all users. When a
limit is reached the API answers `429` with a Spanish message and `Retry-After`, stores nothing, creates no ledger row
and does not call the model. Set a cost limit to 0 to disable it. `REQUIRE_VERIFIED_EMAIL=true` makes the
message-sending endpoints answer `403` until the e-mail is verified.

- **Deleting conversations does not reset any limit.** The ledger has no foreign key to conversations or messages;
  its rows only disappear when the user's account is deleted.
- **Reservation.** Under a per-user advisory lock (`pg_advisory_xact_lock`) the checks and a `reserved` ledger row are
  committed together with the stored question, before the model is called, so parallel requests of one user cannot all
  pass before any spend is recorded. The reservation is `CHAT_RESERVE_INPUT_TOKENS` (default 12000) plus the question
  length / 3 as input and `CHAT_MAX_OUTPUT_TOKENS` (1800) as output, about 0.0066 USD; a turn that would push the
  24 h total over the cap is refused. A user has at most one turn in flight (any `reserved` row younger than
  `CHAT_IN_FLIGHT_SECONDS` gives `409 respuesta_en_curso`).
- **Settlement.** A completed turn stores its real tokens (`settled`). Failed turns (`error`) and client cancels
  (`cancelled`) keep the estimate unless the run reported tokens, because the provider still charges for them.
- **Stuck reservation.** If the process dies mid-turn the row stays `reserved`: after the in-flight window it stops
  blocking the user but keeps counting its estimate (about 0.0066 USD) until it leaves the 24 h window. A row whose
  actual tokens are 0 (usage unknown) also counts the estimate.
- The limits no longer read `messages`; the global breaker sums the last 24 hours using `ix_chat_usage_created`.
  Migration `20261029_16` backfills the last 48 hours from existing user messages so limits do not reset at deploy.
