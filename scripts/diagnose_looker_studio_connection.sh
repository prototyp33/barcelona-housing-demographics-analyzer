#!/bin/bash
# Script de diagnóstico para conexión de Looker Studio a PostgreSQL

echo "=========================================="
echo "Diagnóstico de Conexión Looker Studio"
echo "=========================================="

POSTGRES_VERSION="16"
PG_DATA_DIR="/opt/homebrew/var/postgresql@${POSTGRES_VERSION}"
PG_CONF="${PG_DATA_DIR}/postgresql.conf"
PG_HBA="${PG_DATA_DIR}/pg_hba.conf"

echo ""
echo "1. Verificando estado de PostgreSQL..."
if brew services list | grep -q "postgresql.*started"; then
    echo "✅ PostgreSQL está corriendo"
else
    echo "❌ PostgreSQL NO está corriendo"
    echo "   Ejecuta: brew services start postgresql@${POSTGRES_VERSION}"
    exit 1
fi

echo ""
echo "2. Verificando listen_addresses..."
if grep -q "^listen_addresses = '\*'" "$PG_CONF" || grep -q "^listen_addresses = '*'" "$PG_CONF"; then
    echo "✅ PostgreSQL escucha en todas las interfaces (*)"
else
    echo "❌ PostgreSQL NO está configurado para escuchar en todas las interfaces"
    echo "   Configuración actual:"
    grep "^listen_addresses" "$PG_CONF" || echo "   (no encontrado, usando default: localhost)"
    echo ""
    echo "   Solución: Edita $PG_CONF y cambia a: listen_addresses = '*'"
fi

echo ""
echo "3. Verificando pg_hba.conf para IPs de Google..."
if grep -q "142.251.74" "$PG_HBA"; then
    echo "✅ IPs de Google configuradas en pg_hba.conf"
    echo "   Reglas encontradas:"
    grep "142.251.74\|2001:4860:4807" "$PG_HBA" | head -2
else
    echo "❌ IPs de Google NO están configuradas en pg_hba.conf"
    echo "   Solución: Ejecuta ./scripts/setup_postgresql_for_looker_studio.sh"
fi

echo ""
echo "4. Verificando que PostgreSQL escucha en puerto 5432..."
LISTENING=$(netstat -an | grep "\.5432" | grep LISTEN || echo "")
if [ -n "$LISTENING" ]; then
    echo "✅ PostgreSQL está escuchando en puerto 5432"
    echo "   Conexiones:"
    echo "$LISTENING" | head -3
else
    echo "❌ PostgreSQL NO está escuchando en puerto 5432"
fi

echo ""
echo "5. Verificando firewall de macOS..."
FIREWALL_STATUS=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null | grep -i "enabled" || echo "disabled")
echo "   Estado del firewall: $FIREWALL_STATUS"

if echo "$FIREWALL_STATUS" | grep -qi "enabled"; then
    echo "   ⚠️  Firewall está activado - puede estar bloqueando conexiones"
    echo "   Verifica que PostgreSQL está permitido"
fi

echo ""
echo "6. Verificando acceso a la base de datos..."
if psql -d barcelona_housing -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Base de datos 'barcelona_housing' es accesible localmente"
    
    # Verificar usuario y contraseña
    echo ""
    echo "   Usuario actual: $(whoami)"
    echo "   Verificando si el usuario tiene contraseña..."
    HAS_PASSWORD=$(psql -d barcelona_housing -t -c "SELECT passwd FROM pg_shadow WHERE usename = '$(whoami)';" 2>/dev/null | tr -d ' ')
    if [ "$HAS_PASSWORD" != "********" ] && [ -n "$HAS_PASSWORD" ]; then
        echo "   ✅ Usuario tiene contraseña configurada"
    else
        echo "   ⚠️  Usuario puede no tener contraseña configurada"
        echo "   Solución: ALTER USER $(whoami) WITH PASSWORD 'tu_contraseña';"
    fi
else
    echo "❌ No se puede acceder a la base de datos 'barcelona_housing'"
fi

echo ""
echo "7. Verificando IP pública..."
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "No disponible")
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo "   IP Pública: $PUBLIC_IP"
echo "   IP Local: $LOCAL_IP"

echo ""
echo "8. Verificando port forwarding..."
echo "   ⚠️  IMPORTANTE: Verifica manualmente en tu router:"
echo "   - Puerto externo 5432 → IP interna $LOCAL_IP:5432"
echo "   - Protocolo: TCP"
echo ""
echo "   Para verificar, intenta conectar desde fuera:"
echo "   psql -h $PUBLIC_IP -p 5432 -U $(whoami) -d barcelona_housing"

echo ""
echo "9. Verificando conectividad desde internet..."
echo "   Probando si el puerto 5432 es accesible desde fuera..."
TIMEOUT_RESULT=$(timeout 3 nc -zv $PUBLIC_IP 5432 2>&1 || echo "timeout")
if echo "$TIMEOUT_RESULT" | grep -q "succeeded\|open"; then
    echo "   ✅ Puerto 5432 parece estar abierto"
else
    echo "   ❌ Puerto 5432 NO es accesible desde fuera"
    echo "   Posibles causas:"
    echo "   - Port forwarding no configurado en router"
    echo "   - Firewall bloqueando"
    echo "   - ISP bloqueando puertos"
fi

echo ""
echo "10. Revisando logs de PostgreSQL..."
if [ -f "${PG_DATA_DIR}/log/postgresql*.log" ]; then
    echo "   Últimas líneas del log:"
    tail -5 ${PG_DATA_DIR}/log/postgresql*.log 2>/dev/null | head -5 || echo "   (no se pudo leer log)"
else
    echo "   ⚠️  Logs no encontrados en ${PG_DATA_DIR}/log/"
fi

echo ""
echo "=========================================="
echo "Resumen de Problemas Encontrados"
echo "=========================================="

ISSUES=0

if ! brew services list | grep -q "postgresql.*started"; then
    echo "❌ PostgreSQL no está corriendo"
    ISSUES=$((ISSUES + 1))
fi

if ! grep -q "^listen_addresses = '\*'" "$PG_CONF" && ! grep -q "^listen_addresses = '*'" "$PG_CONF"; then
    echo "❌ listen_addresses no está configurado como '*'"
    ISSUES=$((ISSUES + 1))
fi

if ! grep -q "142.251.74" "$PG_HBA"; then
    echo "❌ IPs de Google no están en pg_hba.conf"
    ISSUES=$((ISSUES + 1))
fi

if [ -z "$LISTENING" ]; then
    echo "❌ PostgreSQL no está escuchando en puerto 5432"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo "✅ No se encontraron problemas obvios de configuración"
    echo ""
    echo "Si aún tienes problemas, verifica:"
    echo "  1. Port forwarding en tu router"
    echo "  2. Firewall de tu ISP (algunos bloquean puertos)"
    echo "  3. El error específico en Looker Studio"
else
    echo ""
    echo "Ejecuta el script de configuración:"
    echo "  ./scripts/setup_postgresql_for_looker_studio.sh"
fi

echo ""
