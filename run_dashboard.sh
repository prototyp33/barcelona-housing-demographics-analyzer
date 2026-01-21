#!/bin/bash
# ==============================================================================
# Barcelona Housing Analytics - Dashboard Launcher (Legacy)
# ==============================================================================
# Este script se mantiene para compatibilidad. Para más opciones, usa:
#   ./scripts/dashboard/run_dashboard.sh
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Redirigir al script mejorado si existe
if [ -f "$SCRIPT_DIR/scripts/dashboard/run_dashboard.sh" ]; then
    exec "$SCRIPT_DIR/scripts/dashboard/run_dashboard.sh" "$@"
else
    # Fallback al comportamiento original
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    lsof -ti:8501 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "🚀 Starting Barcelona Housing Demographics Dashboard..."
    echo "📍 URL: http://localhost:8501"
    echo ""
    streamlit run src/app/main.py
fi
