#!/bin/bash
# Script para configurar PostgreSQL para Looker Studio

set -e

echo "=========================================="
echo "Configuración PostgreSQL para Looker Studio"
echo "=========================================="

POSTGRES_VERSION="16"
PG_DATA_DIR="/opt/homebrew/var/postgresql@${POSTGRES_VERSION}"
PG_CONF="${PG_DATA_DIR}/postgresql.conf"
PG_HBA="${PG_DATA_DIR}/pg_hba.conf"

# Verificar que PostgreSQL está instalado
if [ ! -d "$PG_DATA_DIR" ]; then
    echo "❌ PostgreSQL no encontrado en $PG_DATA_DIR"
    exit 1
fi

echo ""
echo "1. Configurando listen_addresses..."
if grep -q "^listen_addresses = 'localhost'" "$PG_CONF" || grep -q "^#listen_addresses = 'localhost'" "$PG_CONF"; then
    # Backup
    cp "$PG_CONF" "${PG_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Cambiar a escuchar en todas las interfaces
    sed -i '' "s/^#*listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
    echo "✅ Configurado listen_addresses = '*'"
else
    echo "⚠️  listen_addresses ya está configurado"
fi

echo ""
echo "2. Configurando pg_hba.conf para IPs de Google..."
GOOGLE_IPS="142.251.74.0/23"
GOOGLE_IPS_V6="2001:4860:4807::/48"

# Verificar si ya existe
if grep -q "$GOOGLE_IPS" "$PG_HBA"; then
    echo "⚠️  IPs de Google ya están configuradas en pg_hba.conf"
else
    # Backup
    cp "$PG_HBA" "${PG_HBA}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Añadir reglas para Google (al principio, antes de otras reglas)
    {
        echo "# Looker Studio - Google IPs"
        echo "host    all             all             ${GOOGLE_IPS}          md5"
        echo "host    all             all             ${GOOGLE_IPS_V6}       md5"
        echo ""
        cat "$PG_HBA"
    } > "${PG_HBA}.new"
    mv "${PG_HBA}.new" "$PG_HBA"
    
    echo "✅ Añadidas IPs de Google a pg_hba.conf"
fi

echo ""
echo "3. Configurando contraseña para usuario..."
read -p "¿Quieres configurar una contraseña para el usuario PostgreSQL? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -sp "Introduce nueva contraseña: " PASSWORD
    echo
    read -sp "Confirma contraseña: " PASSWORD_CONFIRM
    echo
    
    if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
        echo "❌ Las contraseñas no coinciden"
        exit 1
    fi
    
    psql -d barcelona_housing -c "ALTER USER $(whoami) WITH PASSWORD '$PASSWORD';" > /dev/null 2>&1
    echo "✅ Contraseña configurada"
    echo ""
    echo "⚠️  Guarda esta contraseña para usar en Looker Studio"
else
    echo "⚠️  No se configuró contraseña. Asegúrate de tener una configurada."
fi

echo ""
echo "4. Reiniciando PostgreSQL..."
brew services restart postgresql@${POSTGRES_VERSION}
sleep 2

echo ""
echo "5. Verificando configuración..."
if netstat -an | grep -q "\.5432"; then
    echo "✅ PostgreSQL está escuchando en puerto 5432"
else
    echo "⚠️  No se detectó PostgreSQL en puerto 5432"
fi

# Obtener IP pública
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "No disponible")
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

echo ""
echo "=========================================="
echo "✅ Configuración Completa"
echo "=========================================="
echo ""
echo "Información para Looker Studio:"
echo ""
echo "BASIC Connection:"
echo "  Hostname or IP address: $PUBLIC_IP"
echo "  Port: 5432"
echo "  Database: barcelona_housing"
echo "  Username: $(whoami)"
echo "  Password: (la que configuraste)"
echo ""
echo "O JDBC URL:"
echo "  jdbc:postgresql://${PUBLIC_IP}:5432/barcelona_housing"
echo ""
echo "⚠️  IMPORTANTE:"
echo "  1. Configura PORT FORWARDING en tu router:"
echo "     Puerto externo: 5432 → IP interna: $LOCAL_IP:5432"
echo ""
echo "  2. Si tu IP pública cambia, actualiza Looker Studio"
echo ""
echo "  3. Considera usar un servicio DNS dinámico"
echo ""
echo "  4. Para producción, migra a PostgreSQL en la nube"
echo ""
