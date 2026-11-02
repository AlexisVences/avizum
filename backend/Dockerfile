# Avizum API. Build context is backend/ (Render: Dockerfile Path backend/Dockerfile, Docker Build Context backend).
# Only the FastAPI app, Alembic migrations and the helper scripts go in; no dev or ingest dependencies.
# The offline ingestion scripts need PyMuPDF/tiktoken and ../data, which are deliberately not in this image
# (see docs/deployment.md, "Carga inicial de datos").

# ---- build stage: resolve and install locked production dependencies with uv
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /usr/local/bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- runtime stage
FROM python:3.13-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/app/.venv/bin:$PATH" \
    PORT=8000 FORWARDED_ALLOW_IPS=127.0.0.1
RUN useradd --system --uid 10001 --create-home --shell /usr/sbin/nologin avizum
WORKDIR /app
COPY --from=build --chown=avizum:avizum /app/.venv /app/.venv
COPY --chown=avizum:avizum alembic.ini ./
COPY --chown=avizum:avizum app ./app
COPY --chown=avizum:avizum migrations ./migrations
COPY --chown=avizum:avizum scripts ./scripts
USER avizum
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/v1/health' % os.environ.get('PORT', '8000'), timeout=3)"]

# ONE worker on purpose: the rate limiter (app/core/rate_limit.py) keeps its counters in this process's memory, so N
# workers would multiply every limit by N. Scale up the machine, not the worker count, until the limiter moves to Redis.
# --proxy-headers only rewrites the client address for peers listed in FORWARDED_ALLOW_IPS, which defaults to
# 127.0.0.1 (nobody). Do NOT set it to "*": uvicorn would then trust the LEFTMOST X-Forwarded-For entry, which the client
# controls. Per-IP limits use TRUSTED_PROXY_COUNT in the app instead (docs/deployment.md).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\""]
