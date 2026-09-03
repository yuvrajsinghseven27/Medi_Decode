#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/opt/homebrew/bin:$PATH"

echo "=================================================="
echo "🩺 Starting MediDecode Unified Server"
echo "=================================================="

# Check if venv exists
if [ ! -d "$DIR/backend/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$DIR/backend/.venv"
    "$DIR/backend/.venv/bin/pip" install -r "$DIR/backend/pyproject.toml" aiosqlite
fi

# Build frontend if dist does not exist
if [ ! -d "$DIR/frontend/dist" ]; then
    echo "Building frontend..."
    cd "$DIR/frontend"
    npm install
    npm run build
fi

# Seed database if it doesn't exist
if [ ! -f "$DIR/backend/medidecode.db" ]; then
    echo "Seeding local database..."
    "$DIR/backend/.venv/bin/python" "$DIR/backend/scripts/seed.py"
fi

echo "Launching unified app on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Health:   http://localhost:8000/healthz"
echo "=================================================="

cd "$DIR/backend"
"$DIR/backend/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload
