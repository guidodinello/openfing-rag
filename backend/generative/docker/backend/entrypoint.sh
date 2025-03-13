#!/bin/bash
set -e

# Ensure correct line endings
if [ "$(head -c 2 "$0")" = "#!" ]; then
    echo "Line endings are correct"
else
    echo "Converting line endings"
    sed -i 's/\r$//' "$0"
fi

# Verify Poetry and Python environment
echo "Verifying environment..."
echo "Poetry: $(which poetry)"
echo "Python: $(which python)"

# Install dependencies if they're not already installed
if [ ! -d "/app/.venv" ]; then
    echo "Installing dependencies..."
    poetry install --no-interaction
else
    echo "Virtual environment found at /app/.venv"
fi

echo "Waiting for PostgreSQL..."
until nc -z db 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL started"

# Run migrations
echo "Running database migrations..."
poetry run alembic upgrade head

if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting development server..."
    poetry run dev
else
    echo "Starting production server..."
    poetry run start
fi
