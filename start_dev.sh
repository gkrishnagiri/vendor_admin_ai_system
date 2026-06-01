#!/bin/bash
set -e

echo "🚀 Starting Docker Postgres..."
if [ "$(docker inspect -f '{{.State.Running}}' ai_agents_postgres 2>/dev/null)" != "true" ]; then
    docker start ai_agents_postgres 2>/dev/null || docker compose up -d
fi
echo "✅ Postgres is running"

echo "🧹 Cleaning up port 8002..."
fuser -k 8002/tcp 2>/dev/null || true

echo "🐍 Managing backend_v2 environment..."
cd backend_v2

if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with uv..."
    uv venv
    echo "📦 Initializing dependencies..."
    uv pip install -e .
    echo "🎭 Installing Playwright browsers..."
    ./.venv/bin/python3 -m playwright install chromium
    touch .venv/.last_sync
fi

# Only sync if pyproject.toml is newer than the last sync marker
if [ "pyproject.toml" -nt ".venv/.last_sync" ]; then
    echo "📦 Syncing dependencies with uv..."
    uv pip install -e .
    touch .venv/.last_sync
else
    echo "⏩ Dependencies up to date, skipping sync."
fi

echo "🔌 Activating virtual environment..."
source .venv/bin/activate

echo "🚀 Starting FastAPI (v2) with hot-reload..."
export PYTHONPATH=$PYTHONPATH:.
uvicorn api.main:app --port 8002 --reload