# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Avizum is a Mexican traffic-law consultation project. The **active backend is a single FastAPI modular monolith using PostgreSQL** (`backend/`). Two other backends exist only as reference and must not receive new features:

- `backend/node-api/` — legacy Express API (not run)
- `ai/` — legacy Flask/RAG reference and index build utility (not run)

## Repository layout

```
frontend/              React single-page application
backend/                Active FastAPI application, Alembic migrations and tests
backend/node-api/       Legacy Express API (not run)
ai/                     Legacy Flask/RAG reference and index build utility (not run)
data/
  sources.json          Manifest of official sources (URL, reform date, expected counts)
  legal-sources/        Official PDFs (downloaded by scripts.fetch_sources, not committed)
database/schema.sql     PostgreSQL schema
```

Within `backend/`: HTTP routes live in `app/api/`, configuration and security in `app/core/`, SQLAlchemy models in `app/models/`, request/response schemas in `app/schemas/`, and integration logic (e.g. the AI adapter) in `app/services/`. Alembic migrations are the source of truth for the database schema and live in `backend/migrations/`.

Within `frontend/`: UI components in `src/components/`, route views in `src/pages/`, API clients in `src/services/`, styles/assets in `src/styles/` and `src/assets/`.

## Commands

Backend (run from `backend/`):

```bash
cp .env.example .env                          # then edit DATABASE_URL and JWT_SECRET_KEY
uv sync --group dev                           # install backend + test dependencies
uv run alembic upgrade head                   # apply database migrations
uv run uvicorn app.main:app --reload --host 0.0.0.0  # run API on http://localhost:8000 (0.0.0.0 so WSL2 can reach it from Windows)
uv run pytest                                 # run all tests
uv run pytest tests/test_api.py::test_name    # run a single test
uv run python -m scripts.promote_admin <email>  # bootstrap the first admin (after they register)
uv sync --group dev --group ingest            # adds PyMuPDF for source ingestion
uv run python -m scripts.fetch_sources        # download and register official sources (data/sources.json)
uv run python -m scripts.import_agents        # import the current authorized-agents acuerdo
```

The API is served under `/api/v1` (e.g. `GET /api/v1/health`).

Frontend (run from `frontend/`):

```bash
npm install
npm start                                     # dev server
npm run build                                 # production build
npm test                                      # React Testing Library, interactive watch mode
```

Set `REACT_APP_API_URL=http://localhost:8000/api/v1` for the frontend if the default doesn't match the backend.

AI / RAG (optional, lazy-loaded):

```bash
cd backend && uv sync --group ai
```

Requires Ollama running with the configured chat/embedding models, `AI_ENABLED=true`, and `AI_INDEX_PATH` set. No index is checked in (the legacy pickle-based FAISS index was removed); build one from the trusted PDFs in `data/legal-sources/`, and set `AI_ALLOW_LEGACY_FAISS_DESERIALIZATION=true` only for an index you built and validated on the deployment machine. When AI is unavailable, legal consultation returns HTTP 503 rather than a fabricated answer.

## Backend architecture

- Entry point `app/main.py` builds the app via `create_app()`, wiring CORS (from `settings.cors_origin_list`) and the single router from `app/api/routes.py`. All endpoints live in that one router file, prefixed `/api/v1`.
- `app/core/config.py` exposes a cached `Settings` (pydantic-settings, reads `.env`); `app/core/security.py` handles Argon2 password hashing (`pwdlib`) and JWT creation.
- `app/api/deps.py` defines the auth dependency chain: `current_user` decodes the Bearer JWT and loads the user; `admin_user` additionally requires `UserRole.ADMIN`. Route handlers take `CurrentUser` / `AdminUser` / `DbSession` as typed `Annotated` dependencies rather than reading `Depends(...)` inline.
- **Authentication is Bearer JWT.** Registration always creates the `user` role — there is no self-service admin signup. Only an existing administrator can promote/demote roles, via `PATCH /api/v1/admin/users/{id}`. Identity and ownership are always derived from the token's subject, never from a client-supplied user ID (see `submit_feedback` in `routes.py` checking `consultation.user_id != user.id`).
- `app/models/domain.py` holds all SQLAlchemy models: `User`, `OfficialSource` (versioned official documents, one current per slug), `AuthorizedAgent`, `AgentLookup`, `Consultation`, `LegalResponse`, `Feedback`. `Consultation` and `LegalResponse` are separate tables (one-to-one) so a consultation's question is recorded even if answer generation fails partway.
- `app/services/legal_ai.py` is a lazy, optional Ollama/LangChain RAG adapter used by the `/legal-consultations` endpoint; it raises `LegalAIUnavailable` when AI is disabled/misconfigured, which the route converts to a 503.
- Alembic migrations (`backend/migrations/`) are the source of truth for schema, mirrored conceptually in `database/schema.sql`. The new schema deliberately replaces legacy `usuario`/`consulta`-style tables from the old Flask/Express backends and does **not** auto-migrate an existing production database — a data migration must be planned and tested explicitly before deploying against one.
- Tests run against PostgreSQL (see `backend/tests/conftest.py`; requires the `db` service from `docker-compose.yml` running, or a `TEST_DATABASE_URL` override), overriding the `get_db` dependency and creating/dropping all tables per test via a `client` fixture that yields `(test_client, session_factory)`. This matches production so Postgres-only behavior (e.g. native enum columns) is actually exercised.

## Introducing new technology

When implementing a feature that introduces a new library, framework, or external technology not already used in this project, do two things before writing code:

1. Use Context7 to pull current, version-specific documentation for it instead of relying on training data.
2. Briefly check if a relevant Claude Code plugin exists for it and mention it if found — don't install anything without asking first.

This does not apply to routine work using technology already established in this project (FastAPI, SQLAlchemy, React, etc.) — only when something genuinely new is being introduced.

## Conventions

- Python: 4-space indentation, type annotations where practical, `snake_case` for modules/functions/variables, `PascalCase` for classes/models. Ruff line length is 100 (`backend/pyproject.toml`). Keep route handlers thin; put reusable business logic in `app/services/`.
- React: `PascalCase` component/page filenames (e.g. `AdministrarUsuarios.js`), camelCase variables/functions, API calls kept in `src/services/`. CRA's ESLint config runs with the frontend tooling.
- Add backend tests as `backend/tests/test_*.py` using pytest and the shared `conftest.py` fixtures; cover authentication, ownership, validation, and response status codes when changing an endpoint. Run `uv run pytest` before submitting changes.
- Commits/PRs: concise, imperative commit messages, often with Conventional Commit prefixes (e.g. `refactor: migrate backend to FastAPI`, `feat: add agent import endpoint`). PRs should explain user-visible and database/API impact, list validation performed, include screenshots for UI changes, and explicitly call out new migrations, configuration variables, or security-sensitive behavior.
- Database credentials are not stored in the repo; `backend/.env.example` / `ai/.env.example` contain safe placeholders only.
