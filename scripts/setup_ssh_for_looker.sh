#!/bin/bash
# Script para configurar SSH y PostgreSQL para conexión desde Looker Cloud

set -e

echo "=========================================="
echo "Configuración para Looker Cloud"
echo "=========================================="

# Verificar SSH
echo ""
echo "1. Verificando SSH..."
if system_profiler SPNetworkDataType | grep -q "Remote Login"; then
    echo "✅ Remote Login está habilitado"
else
    echo "⚠️  Remote Login NO está habilitado"
    echo ""
    echo "Por favor, habilita Remote Login:"
    echo "  1. System Preferences → Sharing"
    echo "  2. Activa 'Remote Login'"
    echo "  3. Asegúrate de que tu usuario tiene permisos"
    echo ""
    read -p "¿Ya lo habilitaste? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Por favor habilita Remote Login y vuelve a ejecutar este script"
        exit 1
    fi
fi

# Obtener IP pública
echo ""
echo "2. Obteniendo información de red..."
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "No disponible")

echo "   IP Local: $LOCAL_IP"
echo "   IP Pública: $PUBLIC_IP"
echo "   Hostname: $(hostname)"

# Verificar PostgreSQL
echo ""
echo "3. Verificando PostgreSQL..."
if brew services list | grep -q "postgresql.*started"; then
    echo "✅ PostgreSQL está corriendo"
else
    echo "⚠️  PostgreSQL NO está corriendo"
    echo "Iniciando PostgreSQL..."
    brew services start postgresql@16
fi

# Verificar base de datos
echo ""
echo "4. Verificando base de datos..."
if psql -d barcelona_housing -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Base de datos 'barcelona_housing' existe y es accesible"
else
    echo "❌ Error accediendo a la base de datos"
    exit 1
fi

# Resumen
echo ""
echo "=========================================="
echo "✅ Configuración Completa"
echo "=========================================="
echo ""
echo "Para conectar Looker Cloud:"
echo ""
echo "OPCIÓN 1: SSH Tunnel (Recomendado)"
echo "  SSH Host: $PUBLIC_IP (o tu dominio dinámico)"
echo "  SSH Port: 22"
echo "  SSH Username: $(whoami)"
echo "  Database Host (a través del túnel): localhost"
echo "  Database Port: 5432"
echo "  Database: barcelona_housing"
echo "  Username: $(whoami)"
echo ""
echo "OPCIÓN 2: Conexión Directa (Requiere configuración adicional)"
echo "  Host: $PUBLIC_IP"
echo "  Port: 5432"
echo "  Database: barcelona_housing"
echo "  Username: $(whoami)"
echo "  Password: (necesitarás configurar una contraseña)"
echo ""
echo "⚠️  IMPORTANTE:"
echo "  - Si tu IP pública cambia, necesitarás actualizar Looker"
echo "  - Considera usar un servicio DNS dinámico (No-IP, DuckDNS)"
echo "  - Para producción, migra a PostgreSQL en la nube"
echo ""
