#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres to be reachable before applying migrations.
echo "[entrypoint] waiting for database..."
python - <<'PY'
import os, time, socket, sys
host = "postgres"
port = 5432
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] database reachable")
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit("database did not become reachable in time")
PY

echo "[entrypoint] running alembic upgrade head..."
alembic upgrade head

echo "[entrypoint] launching: $*"
exec "$@"