#!/bin/sh
set -e

# See entrypoint.sh for why this exists - same derivation, needed here
# too since this runs as an independent Render service.
if [ -n "$DATABASE_CONNECTION_STRING" ]; then
    export DATABASE_URL=$(echo "$DATABASE_CONNECTION_STRING" | sed 's#^postgresql://#postgresql+asyncpg://#')
    export DATABASE_URL_SYNC=$(echo "$DATABASE_CONNECTION_STRING" | sed 's#^postgresql://#postgresql+psycopg2://#')
fi

# Migrations run in entrypoint.sh (the web service) only. Running
# `alembic upgrade head` here too is NOT safe despite being the same
# command - Compose/Render can start both services as soon as the
# database is healthy, and two concurrent ALTER TABLE statements race
# at the Postgres lock level: the second one blocks on the first,
# then fails with "column already exists" once it's unblocked and the
# column is already there. The worker's poll loop already tolerates
# the documents table not being ready yet (see app/worker.py), so it
# just retries until the web service's migration lands.
echo "Starting document processing worker..."
exec python -m app.worker
