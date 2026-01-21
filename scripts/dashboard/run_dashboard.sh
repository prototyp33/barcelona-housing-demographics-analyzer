#!/bin/bash
# ==============================================================================
# Barcelona Housing Analytics - Dashboard Launcher
# ==============================================================================
# Script mejorado para ejecutar el dashboard Streamlit con verificaciones
# y opciones de configuración.
#
# Uso:
#   ./scripts/dashboard/run_dashboard.sh              # Modo normal
#   ./scripts/dashboard/run_dashboard.sh --dev         # Modo desarrollo
#   ./scripts/dashboard/run_dashboard.sh --port 8502   # Puerto personalizado
#   ./scripts/dashboard/run_dashboard.sh --check        # Solo verificar
# ==============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
PORT=8501
MODE="normal"
CHECK_ONLY=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev|--development)
            MODE="dev"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [OPCIONES]"
            echo ""
            echo "Opciones:"
            echo "  --dev, --development    Modo desarrollo (auto-reload habilitado)"
            echo "  --port PORT             Puerto personalizado (default: 8501)"
            echo "  --check                 Solo verificar dependencias y configuración"
            echo "  --help, -h              Mostrar esta ayuda"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opción desconocida: $1${NC}"
            echo "Usa --help para ver las opciones disponibles"
            exit 1
            ;;
    esac
done

# Función para imprimir mensajes
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para verificar dependencias
check_dependencies() {
    print_info "Verificando dependencias..."
    
    local errors=0
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 no encontrado"
        errors=$((errors + 1))
    else
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python $PYTHON_VERSION encontrado"
    fi
    
    # Verificar Streamlit
    if ! python3 -c "import streamlit" 2>/dev/null; then
        print_error "Streamlit no está instalado"
        print_info "Instala con: pip install streamlit"
        errors=$((errors + 1))
    else
        STREAMLIT_VERSION=$(python3 -c "import streamlit; print(streamlit.__version__)" 2>/dev/null)
        print_success "Streamlit $STREAMLIT_VERSION instalado"
    fi
    
    # Verificar base de datos
    DB_PATH="$PROJECT_ROOT/data/processed/database.db"
    if [ ! -f "$DB_PATH" ]; then
        print_warning "Base de datos no encontrada en: $DB_PATH"
        print_info "Ejecuta el ETL primero para generar la base de datos"
    else
        DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
        print_success "Base de datos encontrada ($DB_SIZE)"
    fi
    
    # Verificar archivo principal
    MAIN_FILE="$PROJECT_ROOT/src/app/main.py"
    if [ ! -f "$MAIN_FILE" ]; then
        print_error "Archivo principal no encontrado: $MAIN_FILE"
        errors=$((errors + 1))
    else
        print_success "Archivo principal encontrado"
    fi
    
    # Verificar puerto disponible
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Puerto $PORT ya está en uso"
        if [ "$MODE" != "dev" ]; then
            print_info "Intentando liberar el puerto..."
            lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
    else
        print_success "Puerto $PORT disponible"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Se encontraron $errors error(es). Corrígelos antes de continuar."
        return 1
    fi
    
    return 0
}

# Función para configurar entorno
setup_environment() {
    print_info "Configurando entorno..."
    
    # Establecer PYTHONPATH
    export PYTHONPATH="${PYTHONPATH}:${PROJECT_ROOT}"
    cd "$PROJECT_ROOT"
    
    print_success "Entorno configurado"
}

# Función principal
main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🏠 Barcelona Housing Analytics - Dashboard Launcher"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Verificar dependencias
    if ! check_dependencies; then
        exit 1
    fi
    
    # Si solo se solicita verificación, salir aquí
    if [ "$CHECK_ONLY" = true ]; then
        print_success "Todas las verificaciones pasaron"
        exit 0
    fi
    
    # Configurar entorno
    setup_environment
    
    # Configurar opciones de Streamlit según modo
    STREAMLIT_ARGS="run src/app/main.py --server.port=$PORT"
    
    if [ "$MODE" = "dev" ]; then
        print_info "Modo desarrollo: auto-reload habilitado"
        STREAMLIT_ARGS="$STREAMLIT_ARGS --server.runOnSave=true --server.fileWatcherType=poll"
    fi
    
    echo ""
    print_info "Iniciando dashboard..."
    print_info "📍 URL: http://localhost:$PORT"
    print_info "📁 Directorio: $PROJECT_ROOT"
    if [ "$MODE" = "dev" ]; then
        print_info "🔄 Auto-reload: Habilitado"
    fi
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Ejecutar Streamlit
    streamlit $STREAMLIT_ARGS
}

# Ejecutar función principal
main
