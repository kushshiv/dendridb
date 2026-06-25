#!/usr/bin/env bash
# Wait for PostgreSQL to accept connections (used in CI or custom setups).
set -euo pipefail

HOST="${POSTGRES_HOST:-localhost}"
PORT="${POSTGRES_PORT:-5432}"
USER="${POSTGRES_USER:-dendridb}"
DB="${POSTGRES_DB:-dendridb}"

echo "Waiting for PostgreSQL at ${HOST}:${PORT}..."
for i in $(seq 1 30); do
  if pg_isready -h "$HOST" -p "$PORT" -U "$USER" -d "$DB" >/dev/null 2>&1; then
    echo "PostgreSQL is ready."
    exit 0
  fi
  sleep 1
done

echo "PostgreSQL did not become ready in time." >&2
exit 1
