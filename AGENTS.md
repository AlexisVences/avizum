# Repository Guidelines

## Project Structure & Module Organization

`frontend/` is the React single-page application: UI lives in `src/components/`, route views in `src/pages/`, API clients in `src/services/`, and styles/assets in `src/styles/` and `src/assets/`. `backend/` is the active FastAPI monolith. Keep HTTP routes in `app/api/`, configuration and security in `app/core/`, models in `app/models/`, and integration logic in `app/services/`. Alembic migrations live in `backend/migrations/`; tests live in `backend/tests/`.

`backend/node-api/` and `ai/` are legacy Express and Flask/RAG references; do not add production features there. Legal PDFs, agent data, and embeddings belong under `data/`.

## Build, Test, and Development Commands

Run these from the indicated directory:

```bash
cd backend && uv sync --group dev        # install backend and test dependencies
cd backend && uv run alembic upgrade head # apply database migrations
cd backend && uv run uvicorn app.main:app --reload # run API on port 8000
cd backend && uv run pytest               # run FastAPI tests
cd frontend && npm install && npm start   # run the React app
cd frontend && npm run build              # produce a production client build
cd frontend && npm test                   # run React tests interactively
```

Copy `backend/.env.example` to `.env` and set database and JWT values before running the API. Set `REACT_APP_API_URL=http://localhost:8000/api/v1` when needed.

## Coding Style & Naming Conventions

Use four-space indentation and type annotations where practical in Python. Follow the configured Ruff limit of 100 characters. Use `snake_case` for Python modules, functions, and variables; `PascalCase` for classes and models. Keep route handlers thin and place reusable business logic in services.

For React, use `PascalCase` component/page filenames (for example, `AdministrarUsuarios.js`), camelCase variables/functions, and keep API calls in `src/services/`. Preserve the project’s existing JavaScript and CSS conventions; Create React App’s ESLint configuration runs with the frontend tooling.

## Testing Guidelines

Add backend tests in `backend/tests/test_*.py`, using pytest and shared fixtures in `conftest.py`. Test authentication, ownership, validation, and response status codes whenever changing an endpoint. Run `uv run pytest` before submitting. Add focused React Testing Library tests for changed UI behavior where coverage exists.

## Commit & Pull Request Guidelines

Recent history uses concise, imperative messages, often with Conventional Commit prefixes: `refactor: migrate backend to FastAPI`. Follow that pattern, e.g. `feat: add agent import endpoint`. Keep commits scoped. PRs should explain the user-visible and database/API impact, link relevant issues, list validation performed, and include screenshots for UI changes. Highlight new migrations, configuration variables, or security-sensitive behavior explicitly.
