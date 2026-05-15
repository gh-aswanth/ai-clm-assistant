FROM python:3.13-slim

RUN groupadd --system app && useradd --system --create-home --gid app app
# Switch to the non-root user
# Copy uv from pre-built image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project metadata
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

# Copy the application code
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini
COPY backend/entrypoint.sh ./entrypoint.sh
COPY backend/generate_migration.sh ./generate_migration.sh
RUN chmod +x ./entrypoint.sh ./generate_migration.sh

# Set environment variables
ENV DATABASE_URL=sqlite:///./data/sql_app.db
ENV PYTHONPATH=/app
# Use the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Create data directory
RUN mkdir -p /app/data

# Expose the port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
