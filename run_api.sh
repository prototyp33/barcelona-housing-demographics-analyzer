#!/bin/bash
# Helper script to run the FastAPI backend with correct Python path

# Set PYTHONPATH to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Kill any existing uvicorn processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Wait a moment for port to be released
sleep 1

# Run FastAPI with uvicorn
echo "🚀 Starting Barcelona Housing API..."
echo "📍 API URL: http://localhost:8000"
echo "📚 Docs URL: http://localhost:8000/docs"
echo ""
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
