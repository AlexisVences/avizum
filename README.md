# Abogadazo

Abogadazo is a Mexican traffic-law consultation project. Its active backend is a single FastAPI modular monolith using PostgreSQL; the previous Express and Flask implementations remain temporarily as reference while the new API is adopted.

## Repository layout

```text
frontend/              React single-page application
backend/               Active FastAPI application, Alembic migrations and tests
backend/node-api/      Legacy Express API (not run)
ai/                    Legacy Flask/RAG reference and index build utility (not run)
data/
  agents/              Registry of authorized traffic agents (CSV)
  legal-sources/       PDF legal/reference sources retained from the project
  legal-embeddings/    Existing FAISS index built from legal sources
database/schema.sql    PostgreSQL schema
```

## Backend architecture

- React, React Router, Bootstrap, Axios, Recharts, and Create React App tooling
- `app/api`: versioned HTTP endpoints and authorization checks
- `app/models`: SQLAlchemy models for users, agents, consultations, responses and feedback
- `app/services/legal_ai.py`: lazy optional Ollama/LangChain RAG adapter
- `migrations`: the PostgreSQL source of truth, managed by Alembic

Authentication is Bearer JWT. Passwords are Argon2 hashes via `pwdlib`; registration always creates the `user` role. Only an existing administrator may grant or revoke roles through `/api/v1/admin/users/{id}`. Identity and ownership are derived from the token, never request user IDs.

## Local development

From `backend/`:

```bash
cp .env.example .env
# edit DATABASE_URL and JWT_SECRET_KEY
uv sync --group dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest
```

After registering the first trusted user, a database operator can bootstrap administration explicitly:

```bash
uv run python -m scripts.promote_admin <username>
```

The API is then available at `http://localhost:8000/api/v1`, including `GET /health`.

For the React client, set `REACT_APP_API_URL=http://localhost:8000/api/v1` if its default is unsuitable.

## AI / RAG

Legal consultation is intentionally optional and lazy-loaded. Install its dependencies with `uv sync --group ai`, run Ollama with the configured chat and embedding models, set `AI_ENABLED=true`, and configure `AI_INDEX_PATH`. The checked-in LangChain FAISS index has pickle metadata, so it is rejected by default. Set `AI_ALLOW_LEGACY_FAISS_DESERIALIZATION=true` only after rebuilding/validating it from trusted legal-source PDFs on the deployment machine. When unavailable, legal consultation returns HTTP 503 rather than a fabricated answer.

Database credentials are intentionally not stored in the repository. `backend/.env.example` contains safe placeholders.

## Migration notes and next step

The new schema deliberately replaces legacy `usuario`, `consulta`, and related tables; it does not silently alter a production database. Plan and test an explicit data migration before deploying against an existing database. The recommended next task is a trusted, reproducible legal-index build pipeline plus a one-time import command for the agent CSV and existing production data.
