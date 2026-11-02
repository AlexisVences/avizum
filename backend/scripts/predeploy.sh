#!/bin/sh
# Run database migrations before the new version starts taking traffic.
# Render: set this as the service's "Pre-Deploy Command" (sh scripts/predeploy.sh). It uses the service's DATABASE_URL.
# Neon: use the DIRECT (non-pooled) connection string here; see docs/deployment.md.
# The first migration runs CREATE EXTENSION (vector, pg_trgm, unaccent); the role must be allowed to (Neon's default
# owner role is). Migrations are idempotent: running this twice is harmless.
set -eu
cd "$(dirname "$0")/.."
: "${DATABASE_URL:?DATABASE_URL is not set}"
exec alembic upgrade head
