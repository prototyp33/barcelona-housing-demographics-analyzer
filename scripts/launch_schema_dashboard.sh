#!/bin/bash
# Schema Health Dashboard Launcher
# Starts the API server and opens the dashboard in the browser

set -e

echo "🚀 Starting Schema Health Dashboard..."
echo ""

# Check if API is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ API server already running on port 8000"
else
    echo "🔧 Starting API server..."
    # Start API in background
    python3 -m src.api.main &
    API_PID=$!
    echo "   API server started (PID: $API_PID)"
    
    # Wait for API to be ready
    echo "   Waiting for API to be ready..."
    sleep 3
    
    # Check if API is responding
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API server is ready"
    else
        echo "❌ API server failed to start"
        exit 1
    fi
fi

echo ""
echo "📊 Opening Schema Health Dashboard..."
echo ""

# Get the absolute path to the dashboard
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DASHBOARD_PATH="$SCRIPT_DIR/../dashboard/schema-health.html"

# Open dashboard in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$DASHBOARD_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$DASHBOARD_PATH"
else
    echo "⚠️  Please open manually: $DASHBOARD_PATH"
fi

echo "✅ Dashboard launched!"
echo ""
echo "📍 Dashboard: file://$DASHBOARD_PATH"
echo "📍 API Docs: http://localhost:8000/docs"
echo "📍 Schema Health API: http://localhost:8000/schema-health/current"
echo ""
echo "💡 Tips:"
echo "   • Click 'Refresh' to update data"
echo "   • Click 'Create Snapshot' to save current state"
echo "   • Use CLI for quick checks: python scripts/schema_health_cli.py current"
echo ""
echo "Press Ctrl+C to stop the API server"
echo ""

# If we started the API, wait for it
if [ ! -z "$API_PID" ]; then
    wait $API_PID
fi
