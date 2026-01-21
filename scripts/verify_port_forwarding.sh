#!/bin/bash
# Script para verificar que port forwarding está funcionando

echo "=========================================="
echo "Verificación de Port Forwarding"
echo "=========================================="
echo ""

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "No disponible")
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
GATEWAY=$(netstat -nr | grep default | awk '{print $2}' | head -1)

echo "Información de Red:"
echo "  IP Pública: $PUBLIC_IP"
echo "  IP Local: $LOCAL_IP"
echo "  Gateway (Router): $GATEWAY"
echo ""

echo "Para configurar Port Forwarding:"
echo "  1. Accede a tu router: http://$GATEWAY"
echo "  2. Busca 'Port Forwarding' o 'Virtual Server'"
echo "  3. Añade regla:"
echo "     - Puerto externo: 5432"
echo "     - IP interna: $LOCAL_IP"
echo "     - Puerto interno: 5432"
echo "     - Protocolo: TCP"
echo ""

echo "Verificando si PostgreSQL está configurado para conexiones remotas..."
if grep -q "^listen_addresses = '\*'" /opt/homebrew/var/postgresql@16/postgresql.conf 2>/dev/null || \
   grep -q "^listen_addresses = '*'" /opt/homebrew/var/postgresql@16/postgresql.conf 2>/dev/null; then
    echo "✅ PostgreSQL está configurado para escuchar en todas las interfaces"
else
    echo "❌ PostgreSQL NO está configurado para conexiones remotas"
    echo "   Ejecuta: ./scripts/setup_postgresql_for_looker_studio.sh"
fi

echo ""
echo "Verificando IPs de Google en pg_hba.conf..."
if grep -q "142.251.74" /opt/homebrew/var/postgresql@16/pg_hba.conf 2>/dev/null; then
    echo "✅ IPs de Google configuradas"
else
    echo "⚠️  IPs de Google no configuradas"
    echo "   Ejecuta: ./scripts/setup_postgresql_for_looker_studio.sh"
fi

echo ""
echo "=========================================="
echo "Configuración para Looker Studio"
echo "=========================================="
echo ""
echo "Hostname: $PUBLIC_IP"
echo "Port: 5432"
echo "Database: barcelona_housing"
echo "Username: adrianiraeguialvear"
echo "Password: (tu contraseña de PostgreSQL)"
echo ""
echo "JDBC URL:"
echo "  jdbc:postgresql://$PUBLIC_IP:5432/barcelona_housing"
echo ""
echo "⚠️  IMPORTANTE:"
echo "  - Si tu IP pública cambia, actualiza Looker Studio"
echo "  - Considera usar DNS dinámico para hostname permanente"
echo ""
