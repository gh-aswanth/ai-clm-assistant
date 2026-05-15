#!/bin/bash
set -e

# Run migrations
echo "Checking for pending database migrations..."
uv run alembic upgrade head
echo "Database is up to date."

# Start the application
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
