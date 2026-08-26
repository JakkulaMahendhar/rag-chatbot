#!/bin/sh
set -e

# Render's managed Postgres exposes one connection string with no driver
# suffix (postgresql://...), but SQLAlchemy needs the driver in the scheme
# for both the async engine and Alembic. Derive both from it here instead
# of in app code, so this only activates on Render - local/Compose usage
# sets DATABASE_URL/DATABASE_URL_SYNC directly and never sets this var, so
# this block is a no-op there.
if [ -n "$DATABASE_CONNECTION_STRING" ]; then
    export DATABASE_URL=$(echo "$DATABASE_CONNECTION_STRING" | sed 's#^postgresql://#postgresql+asyncpg://#')
    export DATABASE_URL_SYNC=$(echo "$DATABASE_CONNECTION_STRING" | sed 's#^postgresql://#postgresql+psycopg2://#')
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
