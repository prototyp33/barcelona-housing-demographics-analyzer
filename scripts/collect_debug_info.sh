#!/bin/bash
# Script para recopilar información de debug del dashboard Streamlit

echo "=========================================="
echo "Información de Debug - Streamlit Dashboard"
echo "=========================================="
echo ""

echo "📅 Fecha: $(date)"
echo ""

echo "🐍 Python Version:"
python3 --version
echo ""

echo "📦 Streamlit Version:"
streamlit --version 2>/dev/null || echo "Streamlit no encontrado"
echo ""

echo "💻 Sistema Operativo:"
uname -a
echo ""

echo "📁 Estructura de directorios relevantes:"
echo "  - .streamlit/:"
ls -la .streamlit/ 2>/dev/null || echo "    No existe"
echo ""
echo "  - data/logs/:"
ls -la data/logs/ 2>/dev/null || echo "    No existe"
echo ""

echo "📄 Últimas líneas del log (si existe):"
if [ -f "data/logs/dashboard.log" ]; then
    echo "--- Últimas 30 líneas ---"
    tail -30 data/logs/dashboard.log
else
    echo "  No hay archivo de log"
fi
echo ""

echo "⚙️ Configuración de Streamlit:"
if [ -f ".streamlit/config.toml" ]; then
    cat .streamlit/config.toml
else
    echo "  No existe config.toml"
fi
echo ""

echo "🔐 Secrets (solo estructura, sin valores):"
if [ -f ".streamlit/secrets.toml" ]; then
    echo "  Archivo existe (no mostrando contenido por seguridad)"
    echo "  Tamaño: $(wc -l < .streamlit/secrets.toml) líneas"
else
    echo "  No existe secrets.toml"
fi
echo ""

echo "📊 Estado de la base de datos:"
if [ -f "data/processed/database.db" ]; then
    echo "  Base de datos existe"
    echo "  Tamaño: $(du -h data/processed/database.db | cut -f1)"
    python3 << 'PYEOF'
import sqlite3
from pathlib import Path

db_path = Path("data/processed/database.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar WAL mode
    result = cursor.execute("PRAGMA journal_mode;").fetchone()
    print(f"  WAL mode: {result[0] if result else 'unknown'}")
    
    # Contar tablas
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"  Tablas: {len(tables)}")
    
    conn.close()
PYEOF
else
    echo "  Base de datos no encontrada"
fi
echo ""

echo "✅ Verificación de imports:"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from src.app.main import configure_page
    print("  ✅ main.py importa correctamente")
except Exception as e:
    print(f"  ❌ Error importando main.py: {e}")

try:
    from src.app.data_loader import load_kpis
    print("  ✅ data_loader.py importa correctamente")
except Exception as e:
    print(f"  ❌ Error importando data_loader.py: {e}")
PYEOF

echo ""
echo "=========================================="
echo "Fin de información de debug"
echo "=========================================="
