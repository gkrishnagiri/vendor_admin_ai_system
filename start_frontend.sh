#!/bin/bash

echo "⏳ Waiting for backend API to be ready on port 8002..."
while ! curl -s http://127.0.0.1:8002/health > /dev/null; do
    sleep 2
done

echo "✅ Backend is ready!"
echo "🧹 Cleaning up port 3005..."
fuser -k 3005/tcp 2>/dev/null || true
sleep 1

echo "⚙️ Starting Admin UI Frontend..."
cd "$(dirname "$0")/frontend/admin_ui"
npm run dev -- --strictPort
