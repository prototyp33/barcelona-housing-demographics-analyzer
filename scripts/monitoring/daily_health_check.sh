#!/bin/bash
# Daily Health Check Script
# Verifica salud general del sistema: APIs, datos, base de datos

set -e

echo "🏥 Daily Health Check - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Run this script from project root"
    exit 1
fi

# Activar venv si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Verificar APIs externas
echo "## Checking External APIs"
echo ""

python3 scripts/monitoring/check_api_availability.py \
    --url "https://opendata-ajuntament.barcelona.cat/data/api/3/action/package_list" \
    --name "Portal de Dades BCN" || echo -e "${RED}❌ Portal de Dades API failed${NC}"

python3 scripts/monitoring/check_api_availability.py \
    --url "https://www.ine.es/jaxiT3/Tabla.htm?t=1436" \
    --name "INE Estadística Registral" \
    --timeout 30 || echo -e "${RED}❌ INE API failed${NC}"

# Verificar frescura de datos (si DATABASE_URL está configurado)
if [ -n "$DATABASE_URL" ]; then
    echo ""
    echo "## Checking Data Freshness"
    echo ""
    
    python3 scripts/monitoring/check_data_freshness.py \
        --database-url "$DATABASE_URL" \
        --threshold-days 7 || echo -e "${RED}❌ Data freshness check failed${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  DATABASE_URL not set, skipping data freshness check${NC}"
fi

# Verificar estructura de directorios
echo ""
echo "## Checking Directory Structure"
echo ""

REQUIRED_DIRS=(
    "data/raw"
    "data/processed"
    "data/logs"
    "outputs/reports"
    "outputs/visualizations"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $dir exists${NC}"
    else
        echo -e "${RED}❌ $dir missing${NC}"
        mkdir -p "$dir"
        echo "   Created $dir"
    fi
done

# Resumen final
echo ""
echo "=========================================="
echo "Health check completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

