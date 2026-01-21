#!/bin/bash
# ==============================================================================
# Barcelona Housing Analytics - Dashboard Comprehensive Health Check
# ==============================================================================
# Verificación exhaustiva de todos los componentes del dashboard.
# Cubre: dependencias, estructura, base de datos, vistas, funciones, datos.
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
print_section() { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

ERRORS=0
WARNINGS=0

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔍 Dashboard Comprehensive Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ==============================================================================
# 1. VERIFICACIÓN DE ENTORNO Y DEPENDENCIAS
# ==============================================================================
print_section "1. Entorno y Dependencias"

# Python
print_info "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION"
else
    print_error "Python 3 no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Dependencias Python críticas
print_info "Verificando dependencias Python..."
REQUIRED_PACKAGES=(
    "streamlit"
    "pandas"
    "plotly"
    "geopandas"
    "sqlite3"
    "numpy"
    "requests"
)
for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        VERSION=$(python3 -c "import $package; print(getattr($package, '__version__', 'N/A'))" 2>/dev/null || echo "installed")
        print_success "$package ($VERSION)"
    else
        print_error "$package no instalado"
        ERRORS=$((ERRORS + 1))
    fi
done

# ==============================================================================
# 2. ESTRUCTURA DE DIRECTORIOS Y ARCHIVOS
# ==============================================================================
print_section "2. Estructura de Directorios y Archivos"

# Directorios críticos
print_info "Verificando estructura de directorios..."
REQUIRED_DIRS=(
    "src/app"
    "src/app/views"
    "src/app/components"
    "src/app/api_client.py"
    "data/processed"
    "data/exports"
)
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ] || [ -f "$PROJECT_ROOT/$dir" ]; then
        print_success "$dir existe"
    else
        print_error "$dir no existe"
        ERRORS=$((ERRORS + 1))
    fi
done

# Archivos críticos del dashboard
print_info "Verificando archivos críticos del dashboard..."
REQUIRED_FILES=(
    "src/app/main.py"
    "src/app/config.py"
    "src/app/data_loader.py"
    "src/app/styles.py"
    "src/app/components.py"
    "src/app/api_client.py"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        print_success "$file existe"
    else
        print_error "$file no existe"
        ERRORS=$((ERRORS + 1))
    fi
done

# Vistas del dashboard (13 vistas)
print_info "Verificando vistas del dashboard..."
DASHBOARD_VIEWS=(
    "src/app/views/market_cockpit.py"
    "src/app/views/overview.py"
    "src/app/views/map_analysis.py"
    "src/app/views/demographics.py"
    "src/app/views/correlations.py"
    "src/app/views/data_quality.py"
    "src/app/views/market_view.py"
    "src/app/views/advanced_analytics.py"
    "src/app/views/alerts.py"
    "src/app/views/recommendations.py"
    "src/app/views/investment_analysis.py"
    "src/app/views/market_intelligence.py"
    "src/app/views/data_dictionary.py"
)
for view in "${DASHBOARD_VIEWS[@]}"; do
    if [ -f "$PROJECT_ROOT/$view" ]; then
        print_success "$(basename $view)"
    else
        print_warning "$(basename $view) no encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# ==============================================================================
# 3. BASE DE DATOS - ESTRUCTURA Y TABLAS
# ==============================================================================
print_section "3. Base de Datos - Estructura"

if [ ! -f "$DB_PATH" ]; then
    print_error "Base de datos no encontrada en $DB_PATH"
    print_info "Ejecuta el ETL primero: python src/etl/pipeline.py"
    ERRORS=$((ERRORS + 1))
else
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    print_success "Base de datos existe ($DB_SIZE)"
    
    # Verificar que la base de datos no esté vacía
    if [ ! -s "$DB_PATH" ]; then
        print_error "Base de datos está vacía"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Verificar tablas críticas
    print_info "Verificando tablas críticas..."
    CRITICAL_TABLES=(
        "dim_barrios"
        "fact_precios"
        "fact_demografia"
        "fact_renta"
        "fact_regulacion"
        "fact_presion_turistica"
        "fact_seguridad"
        "fact_ruido"
    )
    
    for table in "${CRITICAL_TABLES[@]}"; do
        COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
        if [ "$COUNT" = "0" ] 2>/dev/null; then
            # Verificar si la tabla existe
            EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" 2>/dev/null | wc -l)
            if [ "$EXISTS" -gt 0 ]; then
                print_warning "  Tabla $table: existe pero está vacía"
                WARNINGS=$((WARNINGS + 1))
            else
                print_warning "  Tabla $table: no existe"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            print_success "  Tabla $table: $COUNT registros"
        fi
    done
    
    # Verificar vistas optimizadas
    print_info "Verificando vistas optimizadas..."
    OPTIMIZED_VIEWS=(
        "vw_gentrification_risk"
        "vw_resumen_por_distrito"
        "v_barrio_scorecard"
    )
    
    for view in "${OPTIMIZED_VIEWS[@]}"; do
        EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='view' AND name='$view';" 2>/dev/null | wc -l)
        if [ "$EXISTS" -gt 0 ]; then
            print_success "  Vista $view: existe"
        else
            print_warning "  Vista $view: no existe (opcional pero recomendada)"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
fi

# ==============================================================================
# 4. INTEGRIDAD DE DATOS
# ==============================================================================
print_section "4. Integridad de Datos"

if [ -f "$DB_PATH" ]; then
    # Verificar 73 barrios
    print_info "Verificando integridad de barrios..."
    BARRIO_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM dim_barrios;" 2>/dev/null || echo "0")
    if [ "$BARRIO_COUNT" -eq 73 ]; then
        print_success "Barrios: $BARRIO_COUNT/73 (completo)"
    elif [ "$BARRIO_COUNT" -gt 0 ]; then
        print_warning "Barrios: $BARRIO_COUNT/73 (incompleto)"
        WARNINGS=$((WARNINGS + 1))
    else
        print_error "Barrios: 0 (crítico)"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Verificar GeoJSON en barrios
    GEOJSON_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM dim_barrios WHERE geometry_json IS NOT NULL AND geometry_json != '';" 2>/dev/null || echo "0")
    if [ "$GEOJSON_COUNT" -gt 0 ]; then
        print_success "Barrios con GeoJSON: $GEOJSON_COUNT/$BARRIO_COUNT"
    else
        print_warning "Barrios con GeoJSON: 0 (mapas no funcionarán)"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Verificar años disponibles
    print_info "Verificando años disponibles..."
    MIN_YEAR=$(sqlite3 "$DB_PATH" "SELECT MIN(anio) FROM fact_precios WHERE anio IS NOT NULL;" 2>/dev/null || echo "0")
    MAX_YEAR=$(sqlite3 "$DB_PATH" "SELECT MAX(anio) FROM fact_precios WHERE anio IS NOT NULL;" 2>/dev/null || echo "0")
    if [ "$MAX_YEAR" != "0" ] && [ "$MIN_YEAR" != "0" ]; then
        YEAR_RANGE=$((MAX_YEAR - MIN_YEAR + 1))
        print_success "Rango de años: $MIN_YEAR - $MAX_YEAR ($YEAR_RANGE años)"
    else
        print_warning "Rango de años: no disponible"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Verificar datos recientes (últimos 2 años)
    RECENT_YEAR=$(sqlite3 "$DB_PATH" "SELECT MAX(anio) FROM fact_precios;" 2>/dev/null || echo "0")
    CURRENT_YEAR=$(date +%Y)
    if [ "$RECENT_YEAR" -ge $((CURRENT_YEAR - 1)) ]; then
        print_success "Datos más recientes: $RECENT_YEAR"
    else
        print_warning "Datos más recientes: $RECENT_YEAR (puede estar desactualizado)"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    # Verificar cobertura de datos por tabla
    print_info "Verificando cobertura de datos..."
    COVERAGE_TABLES=("fact_precios" "fact_demografia" "fact_renta")
    for table in "${COVERAGE_TABLES[@]}"; do
        BARRIOS_WITH_DATA=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT barrio_id) FROM $table;" 2>/dev/null || echo "0")
        if [ "$BARRIOS_WITH_DATA" -gt 0 ]; then
            COVERAGE_PCT=$((BARRIOS_WITH_DATA * 100 / 73))
            if [ "$COVERAGE_PCT" -ge 50 ]; then
                print_success "  $table: $BARRIOS_WITH_DATA/73 barrios ($COVERAGE_PCT%)"
            else
                print_warning "  $table: $BARRIOS_WITH_DATA/73 barrios ($COVERAGE_PCT% - baja cobertura)"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            print_warning "  $table: sin datos"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
fi

# ==============================================================================
# 5. FUNCIONES DE CARGA DE DATOS
# ==============================================================================
print_section "5. Funciones de Carga de Datos"

if [ -f "$DB_PATH" ]; then
    print_info "Verificando funciones críticas de carga..."
    
    # Crear script Python temporal para verificar funciones
    TEMP_CHECK_SCRIPT=$(mktemp)
    cat > "$TEMP_CHECK_SCRIPT" << 'PYTHON_EOF'
import sys
import os
sys.path.insert(0, os.environ.get('PROJECT_ROOT', '.'))

try:
    from src.app.data_loader import (
        load_distritos, load_precios, load_barrios, load_kpis,
        load_critical_kpis, load_available_years, load_top_vulnerable_barrios
    )
    
    # Verificar que las funciones existen y son callables
    functions = [
        ('load_distritos', load_distritos),
        ('load_barrios', load_barrios),
        ('load_kpis', load_kpis),
        ('load_available_years', load_available_years),
        ('load_critical_kpis', load_critical_kpis),
    ]
    
    errors = []
    for name, func in functions:
        if not callable(func):
            errors.append(f"{name}: no es callable")
    
    if errors:
        print("ERRORS:", "|".join(errors))
        sys.exit(1)
    else:
        print("OK")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
PYTHON_EOF
    
    export PROJECT_ROOT
    if python3 "$TEMP_CHECK_SCRIPT" 2>&1 | grep -q "OK"; then
        print_success "Funciones de carga importables y callables"
    else
        ERROR_MSG=$(python3 "$TEMP_CHECK_SCRIPT" 2>&1)
        print_error "Error verificando funciones: $ERROR_MSG"
        ERRORS=$((ERRORS + 1))
    fi
    rm -f "$TEMP_CHECK_SCRIPT"
fi

# ==============================================================================
# 6. CONFIGURACIÓN Y ESTILOS
# ==============================================================================
print_section "6. Configuración y Estilos"

# Configuración Streamlit
print_info "Verificando configuración Streamlit..."
if [ -f "$PROJECT_ROOT/.streamlit/config.toml" ]; then
    print_success "Configuración Streamlit encontrada"
    
    # Verificar configuraciones críticas
    if grep -q "port = 8501" "$PROJECT_ROOT/.streamlit/config.toml" 2>/dev/null; then
        print_success "  Puerto configurado: 8501"
    fi
    
    if grep -q "page_title" "$PROJECT_ROOT/.streamlit/config.toml" 2>/dev/null; then
        print_success "  Configuración de página presente"
    fi
    
    # Verificar compatibilidad CORS/XSRF
    if grep -q "enableCORS = false" "$PROJECT_ROOT/.streamlit/config.toml" 2>/dev/null && \
       grep -q "enableXsrfProtection = true" "$PROJECT_ROOT/.streamlit/config.toml" 2>/dev/null; then
        print_warning "  Configuración incompatible: enableCORS=false con enableXsrfProtection=true"
        print_info "    Streamlit requiere enableCORS=true cuando XSRF está habilitado"
        print_info "    Solución: Cambiar enableCORS a true en .streamlit/config.toml"
        WARNINGS=$((WARNINGS + 1))
    else
        print_success "  Configuración CORS/XSRF compatible"
    fi
else
    print_warning "Configuración Streamlit no encontrada (opcional pero recomendada)"
    WARNINGS=$((WARNINGS + 1))
fi

# Verificar estilos
print_info "Verificando estilos..."
if [ -f "$PROJECT_ROOT/src/app/styles.py" ]; then
    # Verificar que tiene funciones críticas
    if grep -q "def inject_global_css" "$PROJECT_ROOT/src/app/styles.py" 2>/dev/null; then
        print_success "Estilos: inject_global_css presente"
    else
        print_warning "Estilos: inject_global_css no encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
    
    if grep -q "def render_kpi_card" "$PROJECT_ROOT/src/app/styles.py" 2>/dev/null; then
        print_success "Estilos: render_kpi_card presente"
    else
        print_warning "Estilos: render_kpi_card no encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# ==============================================================================
# 7. COMPONENTES PERSONALIZADOS
# ==============================================================================
print_section "7. Componentes Personalizados"

print_info "Verificando componentes..."
COMPONENT_FUNCTIONS=(
    "card_standard"
    "render_breadcrumbs"
    "render_empty_state"
)
for component in "${COMPONENT_FUNCTIONS[@]}"; do
    if grep -q "def $component" "$PROJECT_ROOT/src/app/components.py" 2>/dev/null; then
        print_success "Componente $component presente"
    else
        print_warning "Componente $component no encontrado"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# ==============================================================================
# 8. API CLIENT (OPCIONAL)
# ==============================================================================
print_section "8. API Client (Opcional)"

if [ -f "$PROJECT_ROOT/src/app/api_client.py" ]; then
    print_success "API Client presente"
    
    # Verificar si la API está disponible
    print_info "Verificando disponibilidad de API..."
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API disponible en http://localhost:8000"
    else
        print_info "API no disponible (modo offline - normal si no se usa API)"
    fi
else
    print_warning "API Client no encontrado (opcional)"
    WARNINGS=$((WARNINGS + 1))
fi

# ==============================================================================
# 9. PUERTO Y RECURSOS
# ==============================================================================
print_section "9. Puerto y Recursos"

print_info "Verificando puerto 8501..."
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Puerto 8501 ya está en uso"
    WARNINGS=$((WARNINGS + 1))
else
    print_success "Puerto 8501 disponible"
fi

# Verificar espacio en disco
print_info "Verificando recursos del sistema..."
DISK_SPACE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
print_success "Espacio en disco disponible: $DISK_SPACE"

# ==============================================================================
# 10. VERIFICACIÓN DE IMPORTS (SINTAXIS)
# ==============================================================================
print_section "10. Verificación de Sintaxis"

print_info "Verificando sintaxis de archivos críticos..."
CRITICAL_PY_FILES=(
    "src/app/main.py"
    "src/app/config.py"
    "src/app/data_loader.py"
    "src/app/styles.py"
)

SYNTAX_ERRORS=0
for file in "${CRITICAL_PY_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        if python3 -m py_compile "$PROJECT_ROOT/$file" 2>/dev/null; then
            print_success "$(basename $file): sintaxis OK"
        else
            print_error "$(basename $file): error de sintaxis"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# ==============================================================================
# RESUMEN FINAL
# ==============================================================================
print_section "Resumen"

echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_success "¡Perfecto! El dashboard está completamente listo para ejecutarse."
    echo ""
    echo "  Para iniciar el dashboard:"
    echo "    ./scripts/dashboard/run_dashboard.sh"
    echo "    o"
    echo "    make dashboard"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    print_warning "Listo con $WARNINGS advertencia(s)."
    echo ""
    echo "  El dashboard debería funcionar, pero algunas funcionalidades pueden estar limitadas."
    echo "  Revisa las advertencias arriba para optimizar la experiencia."
    echo ""
    
    # Sugerir fix para fact_demografia si está vacía
    if [ -f "$DB_PATH" ]; then
        DEMO_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM fact_demografia;" 2>/dev/null || echo "0")
        if [ "$DEMO_COUNT" = "0" ]; then
            echo "  💡 Para corregir la advertencia de fact_demografia vacía:"
            echo "     ./scripts/dashboard/fix_demografia_warning.sh"
            echo ""
        fi
    fi
    
    echo "  Para iniciar el dashboard:"
    echo "    ./scripts/dashboard/run_dashboard.sh"
    exit 0
else
    print_error "Se encontraron $ERRORS error(es) y $WARNINGS advertencia(s)."
    echo ""
    echo "  ❌ Corrige los errores antes de ejecutar el dashboard."
    echo ""
    echo "  Comandos útiles:"
    echo "    - Generar base de datos: python src/etl/pipeline.py"
    echo "    - Instalar dependencias: pip install -r requirements.txt"
    echo "    - Verificar sintaxis: python3 -m py_compile <archivo.py>"
    echo "    - Corregir demografía: ./scripts/dashboard/fix_demografia_warning.sh"
    exit 1
fi
