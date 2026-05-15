#!/bin/bash
set -e

# Load environment variables if needed
export PYTHONPATH=/app
export DATABASE_URL=sqlite:///./data/sql_app.db

if [ -z "$1" ]; then
    echo "Please provide a migration message: ./generate_migration.sh \"your description\""
    exit 1
fi

echo "Generating migration: $1"
uv run alembic revision --autogenerate -m "$1"
echo "Migration file created in migrations/versions/"
