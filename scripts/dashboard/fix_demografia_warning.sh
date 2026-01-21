#!/bin/bash
# ==============================================================================
# Fix Demografía Warning - Cargar datos demográficos faltantes
# ==============================================================================
# Script para corregir la advertencia de fact_demografia vacía ejecutando
# el ETL de demografía o scripts específicos de carga.
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

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Fix: Cargar Datos Demográficos"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar que la base de datos existe
if [ ! -f "$DB_PATH" ]; then
    print_error "Base de datos no encontrada: $DB_PATH"
    print_info "Ejecuta primero el ETL completo: python src/etl/pipeline.py"
    exit 1
fi

# Verificar estado actual
print_info "Verificando estado actual de fact_demografia..."
CURRENT_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM fact_demografia;" 2>/dev/null || echo "0")

if [ "$CURRENT_COUNT" -gt 0 ]; then
    print_success "fact_demografia ya tiene $CURRENT_COUNT registros"
    print_info "No es necesario cargar datos adicionales"
    exit 0
fi

print_warning "fact_demografia está vacía ($CURRENT_COUNT registros)"
echo ""

# Verificar si hay datos raw disponibles
print_info "Verificando datos raw disponibles..."
RAW_DEMO_DIR="$PROJECT_ROOT/data/raw/opendatabcn"
PORTALDADES_DIR="$PROJECT_ROOT/data/raw/portaldades"

HAS_RAW_DATA=false
if [ -d "$RAW_DEMO_DIR" ] && [ "$(ls -A $RAW_DEMO_DIR 2>/dev/null)" ]; then
    print_success "Datos raw de OpenDataBCN encontrados"
    HAS_RAW_DATA=true
fi

if [ -d "$PORTALDADES_DIR" ] && [ "$(ls -A $PORTALDADES_DIR 2>/dev/null)" ]; then
    print_success "Datos raw de Portal de Dades encontrados"
    HAS_RAW_DATA=true
fi

if [ "$HAS_RAW_DATA" = false ]; then
    print_warning "No se encontraron datos raw de demografía"
    print_info "Opciones:"
    echo ""
    echo "  1. Ejecutar extracción de datos demográficos:"
    echo "     python scripts/extract_priority_sources.py --sources demografia"
    echo ""
    echo "  2. Ejecutar ETL completo (incluye demografía):"
    echo "     python src/etl/pipeline.py"
    echo ""
    echo -ne "${CYAN}¿Quieres ejecutar la extracción ahora? (s/n): ${NC}"
    read -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_info "Ejecutando extracción de datos demográficos..."
        cd "$PROJECT_ROOT"
        export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
        python3 scripts/extract_priority_sources.py --sources demografia || {
            print_error "Error en la extracción"
            exit 1
        }
    else
        print_info "Saliendo. Ejecuta manualmente cuando tengas los datos raw."
        exit 0
    fi
fi

# Opciones para cargar datos
echo ""
print_info "Opciones para cargar datos demográficos:"
echo ""
echo "  1) Ejecutar ETL completo (recomendado)"
echo "  2) Ejecutar solo procesamiento de demografía"
echo "  3) Usar script de enriquecimiento (si ya hay algunos datos)"
echo "  4) Cancelar"
echo ""

echo -ne "${CYAN}Selecciona una opción (1-4): ${NC}"
read choice

case $choice in
    1)
        print_info "Ejecutando ETL completo..."
        cd "$PROJECT_ROOT"
        export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
        if [ -f "scripts/process_and_load.py" ]; then
            python3 scripts/process_and_load.py || {
                print_error "Error ejecutando ETL"
                exit 1
            }
        else
            print_error "Script process_and_load.py no encontrado"
            exit 1
        fi
        ;;
    2)
        print_info "Ejecutando procesamiento de demografía..."
        cd "$PROJECT_ROOT"
        export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
        # Verificar si existe script específico
        if [ -f "scripts/process_demografia_detallada.py" ]; then
            python3 scripts/process_demografia_detallada.py || {
                print_error "Error procesando demografía"
                exit 1
            }
        else
            print_warning "Script específico no encontrado, ejecutando ETL completo..."
            if [ -f "scripts/process_and_load.py" ]; then
                python3 scripts/process_and_load.py || {
                    print_error "Error ejecutando ETL"
                    exit 1
                }
            else
                print_error "Script process_and_load.py no encontrado"
                exit 1
            fi
        fi
        ;;
    3)
        print_info "Ejecutando enriquecimiento de demografía..."
        cd "$PROJECT_ROOT"
        export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
        if [ -f "scripts/enrich_demographics.py" ]; then
            python3 scripts/enrich_demographics.py || {
                print_error "Error enriqueciendo demografía"
                exit 1
            }
        else
            print_error "Script de enriquecimiento no encontrado"
            exit 1
        fi
        ;;
    4)
        print_info "Operación cancelada"
        exit 0
        ;;
    *)
        print_error "Opción inválida"
        exit 1
        ;;
esac

# Verificar resultado
echo ""
print_info "Verificando resultado..."
NEW_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM fact_demografia;" 2>/dev/null || echo "0")

if [ "$NEW_COUNT" -gt 0 ]; then
    print_success "¡Datos cargados exitosamente!"
    print_success "fact_demografia ahora tiene $NEW_COUNT registros"
    echo ""
    print_info "Ejecuta el health check para verificar:"
    echo "  ./scripts/dashboard/check_dashboard.sh"
else
    print_warning "fact_demografia sigue vacía después de la carga"
    echo ""
    print_info "Ejecuta el diagnóstico para identificar el problema:"
    echo "  ./scripts/dashboard/diagnose_demografia.sh"
    echo ""
    print_info "Posibles causas:"
    echo "  - Formato incorrecto del archivo CSV de demografía"
    echo "  - Mapeo de territorios a barrios fallido"
    echo "  - Datos sin valores válidos"
    echo ""
    print_info "Alternativas:"
    echo "  - Verificar si fact_demografia_ampliada tiene datos"
    echo "  - Extraer datos demográficos nuevamente"
fi
