#!/bin/bash
# Helper script to run the Streamlit dashboard with correct Python path

# Set PYTHONPATH to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Kill any existing Streamlit processes on port 8501
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Wait a moment for port to be released
sleep 1

# Run Streamlit
echo "🚀 Starting Barcelona Housing Demographics Dashboard..."
echo "📍 URL: http://localhost:8501"
echo ""
streamlit run src/app/main.py
