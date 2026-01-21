#!/bin/bash
# ==============================================================================
# Diagnóstico de fact_demografia - Identifica por qué está vacía
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DB_PATH="$PROJECT_ROOT/data/processed/database.db"
RAW_DEMO_DIR="$PROJECT_ROOT/data/raw/opendatabcn"

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔍 Diagnóstico: fact_demografia Vacía"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Verificar estado actual
print_info "1. Verificando estado de fact_demografia..."
DEMO_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM fact_demografia;" 2>/dev/null || echo "0")
print_info "   Registros actuales: $DEMO_COUNT"

# 2. Buscar archivos de demografía raw
print_info "2. Buscando archivos de demografía raw..."
DEMO_FILES=$(find "$RAW_DEMO_DIR" -name "*demographic*" -o -name "*demografia*" -o -name "*pad*" 2>/dev/null | head -10)

if [ -z "$DEMO_FILES" ]; then
    print_warning "   No se encontraron archivos de demografía en $RAW_DEMO_DIR"
    print_info "   Archivos disponibles:"
    ls -1 "$RAW_DEMO_DIR"/*.csv 2>/dev/null | head -5 | while read file; do
        echo "     - $(basename $file)"
    done
else
    print_success "   Archivos encontrados:"
    echo "$DEMO_FILES" | while read file; do
        if [ -f "$file" ]; then
            SIZE=$(du -h "$file" | cut -f1)
            LINES=$(wc -l < "$file" 2>/dev/null || echo "0")
            echo "     ✅ $(basename $file) ($SIZE, $LINES líneas)"
        fi
    done
fi

# 3. Verificar estructura de archivos demográficos
print_info "3. Analizando estructura de archivos demográficos..."
FIRST_DEMO_FILE=$(find "$RAW_DEMO_DIR" -name "*demographic*" -o -name "*demografia*" 2>/dev/null | head -1)

if [ -n "$FIRST_DEMO_FILE" ] && [ -f "$FIRST_DEMO_FILE" ]; then
    print_info "   Analizando: $(basename $FIRST_DEMO_FILE)"
    
    # Crear script Python temporal para analizar
    TEMP_SCRIPT=$(mktemp)
    cat > "$TEMP_SCRIPT" << 'PYTHON_EOF'
import sys
import pandas as pd
from pathlib import Path

file_path = sys.argv[1]
try:
    df = pd.read_csv(file_path, nrows=100)
    print(f"Columnas encontradas: {list(df.columns)}")
    print(f"Filas (muestra): {len(df)}")
    print(f"Columnas esperadas: ['Codi_Barri', 'SEXE', 'Valor', 'año' o 'Any' o 'Data_Referencia']")
    
    # Verificar columnas críticas
    required_cols = ['Codi_Barri', 'SEXE', 'Valor']
    year_cols = ['año', 'Any', 'Data_Referencia', 'anio']
    
    has_barrio = any('barri' in col.lower() or 'codi' in col.lower() for col in df.columns)
    has_sex = any('sex' in col.lower() for col in df.columns)
    has_valor = any('valor' in col.lower() or 'value' in col.lower() for col in df.columns)
    has_year = any(col.lower() in [y.lower() for y in year_cols] for col in df.columns)
    
    print(f"\nVerificación de columnas:")
    print(f"  Barrio: {'✅' if has_barrio else '❌'}")
    print(f"  Sexo: {'✅' if has_sex else '❌'}")
    print(f"  Valor: {'✅' if has_valor else '❌'}")
    print(f"  Año: {'✅' if has_year else '❌'}")
    
    if not (has_barrio and has_sex and has_valor):
        print("\n⚠️  Faltan columnas requeridas")
        print("   El archivo puede no tener el formato esperado")
    
    # Mostrar muestra de datos
    print(f"\nPrimeras 3 filas:")
    print(df.head(3).to_string())
    
except Exception as e:
    print(f"❌ Error leyendo archivo: {e}")
PYTHON_EOF
    
    python3 "$TEMP_SCRIPT" "$FIRST_DEMO_FILE" 2>&1
    rm -f "$TEMP_SCRIPT"
else
    print_warning "   No se encontró archivo de demografía para analizar"
fi

# 4. Verificar mapeo de barrios
print_info "4. Verificando mapeo de barrios..."
BARRIO_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM dim_barrios;" 2>/dev/null || echo "0")
print_info "   Barrios en dim_barrios: $BARRIO_COUNT"

# 5. Verificar fact_demografia_ampliada como alternativa
print_info "5. Verificando fact_demografia_ampliada como alternativa..."
AMPLIADA_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM fact_demografia_ampliada;" 2>/dev/null || echo "0")
if [ "$AMPLIADA_COUNT" -gt 0 ]; then
    print_success "   fact_demografia_ampliada tiene $AMPLIADA_COUNT registros"
    print_info "   El dashboard puede usar esta tabla como alternativa"
else
    print_warning "   fact_demografia_ampliada también está vacía"
fi

# 6. Recomendaciones
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  💡 Recomendaciones"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$DEMO_COUNT" = "0" ]; then
    print_warning "fact_demografia está vacía. Posibles causas:"
    echo ""
    echo "  1. Formato incorrecto del archivo CSV"
    echo "     - Debe tener columnas: Codi_Barri, SEXE, Valor, año/Any/Data_Referencia"
    echo ""
    echo "  2. Mapeo de territorios fallido"
    echo "     - Los códigos de barrio en el CSV no coinciden con dim_barrios"
    echo ""
    echo "  3. Datos sin valores válidos"
    echo "     - Todos los valores están vacíos o son inválidos"
    echo ""
    echo "  Soluciones:"
    echo ""
    echo "  a) Extraer datos demográficos nuevamente:"
    echo "     python scripts/extract_priority_sources.py --sources demografia"
    echo ""
    echo "  b) Verificar el formato del archivo CSV manualmente"
    echo ""
    echo "  c) Usar fact_demografia_ampliada si está disponible"
    echo ""
    echo "  d) Ejecutar script de procesamiento específico:"
    echo "     python scripts/process_demografia_detallada.py"
fi
