#!/bin/bash
# ==============================================================================
# Barcelona Housing Analytics - Dashboard Helper
# ==============================================================================
# Script interactivo con múltiples opciones para gestionar el dashboard.
#
# Uso:
#   ./scripts/dashboard/dashboard_helper.sh
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

print_header() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  🏠 Barcelona Housing Analytics - Dashboard Helper${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_menu() {
    echo -e "${BLUE}Opciones disponibles:${NC}"
    echo ""
    echo "  1) 🚀 Iniciar dashboard (modo normal)"
    echo "  2) 🔧 Iniciar dashboard (modo desarrollo)"
    echo "  3) 🔍 Verificar estado del dashboard"
    echo "  4) 🛑 Detener dashboard (puerto 8501)"
    echo "  5) 📊 Ver logs del dashboard"
    echo "  6) 🧹 Limpiar cache de Streamlit"
    echo "  7) 📦 Verificar dependencias"
    echo "  8) 🌐 Abrir dashboard en navegador"
    echo "  9) 📝 Ver configuración"
    echo "  0) ❌ Salir"
    echo ""
}

run_dashboard() {
    local mode=$1
    echo ""
    echo -e "${GREEN}Iniciando dashboard...${NC}"
    "$SCRIPT_DIR/run_dashboard.sh" $mode
}

check_dashboard() {
    echo ""
    "$SCRIPT_DIR/check_dashboard.sh"
}

stop_dashboard() {
    echo ""
    echo -e "${YELLOW}Deteniendo procesos de Streamlit en puerto 8501...${NC}"
    if lsof -ti:8501 | xargs kill -9 2>/dev/null; then
        echo -e "${GREEN}✅ Dashboard detenido${NC}"
    else
        echo -e "${YELLOW}⚠️  No se encontraron procesos en el puerto 8501${NC}"
    fi
}

view_logs() {
    echo ""
    echo -e "${BLUE}Buscando logs del dashboard...${NC}"
    
    LOG_FILES=(
        "$PROJECT_ROOT/data/logs/dashboard.log"
        "$HOME/.streamlit/logs/*.log"
    )
    
    FOUND=false
    for log_pattern in "${LOG_FILES[@]}"; do
        for log_file in $log_pattern; do
            if [ -f "$log_file" ]; then
                echo -e "${GREEN}Log encontrado: $log_file${NC}"
                echo ""
                tail -50 "$log_file"
                FOUND=true
                break
            fi
        done
    done
    
    if [ "$FOUND" = false ]; then
        echo -e "${YELLOW}⚠️  No se encontraron archivos de log${NC}"
    fi
}

clear_cache() {
    echo ""
    echo -e "${YELLOW}Limpiando cache de Streamlit...${NC}"
    
    CACHE_DIRS=(
        "$PROJECT_ROOT/.streamlit/cache"
        "$HOME/.streamlit/cache"
    )
    
    for cache_dir in "${CACHE_DIRS[@]}"; do
        if [ -d "$cache_dir" ]; then
            rm -rf "$cache_dir"/*
            echo -e "${GREEN}✅ Cache limpiado: $cache_dir${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Cache limpiado${NC}"
}

check_dependencies() {
    echo ""
    "$SCRIPT_DIR/check_dashboard.sh"
}

open_browser() {
    echo ""
    echo -e "${BLUE}Abriendo dashboard en navegador...${NC}"
    
    if command -v open &> /dev/null; then
        open "http://localhost:8501"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8501"
    else
        echo -e "${YELLOW}⚠️  No se pudo abrir el navegador automáticamente${NC}"
        echo -e "${BLUE}Abre manualmente: http://localhost:8501${NC}"
    fi
}

view_config() {
    echo ""
    echo -e "${BLUE}Configuración del dashboard:${NC}"
    echo ""
    
    if [ -f "$PROJECT_ROOT/.streamlit/config.toml" ]; then
        echo -e "${GREEN}📄 .streamlit/config.toml:${NC}"
        cat "$PROJECT_ROOT/.streamlit/config.toml"
        echo ""
    else
        echo -e "${YELLOW}⚠️  .streamlit/config.toml no encontrado${NC}"
    fi
    
    if [ -f "$PROJECT_ROOT/src/app/config.py" ]; then
        echo -e "${GREEN}📄 src/app/config.py (PAGE_CONFIG):${NC}"
        grep -A 10 "PAGE_CONFIG" "$PROJECT_ROOT/src/app/config.py" | head -15
    fi
}

main() {
    while true; do
        print_header
        print_menu
        
        read -p "$(echo -e ${CYAN}Selecciona una opción: ${NC})" choice
        
        case $choice in
            1)
                run_dashboard
                break
                ;;
            2)
                run_dashboard "--dev"
                break
                ;;
            3)
                check_dashboard
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            4)
                stop_dashboard
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            5)
                view_logs
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            6)
                clear_cache
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            7)
                check_dependencies
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            8)
                open_browser
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            9)
                view_config
                read -p "$(echo -e ${YELLOW}Presiona Enter para continuar...${NC})"
                ;;
            0)
                echo ""
                echo -e "${GREEN}¡Hasta luego!${NC}"
                echo ""
                exit 0
                ;;
            *)
                echo ""
                echo -e "${RED}❌ Opción inválida. Por favor, selecciona una opción del 0 al 9.${NC}"
                sleep 1
                ;;
        esac
    done
}

main
