#!/bin/bash
# Script para obtener información TCP de cloudflared

echo "=========================================="
echo "Información TCP de cloudflared"
echo "=========================================="
echo ""

# Verificar si cloudflared está corriendo
if ! pgrep -f "cloudflared.*tcp" > /dev/null; then
    echo "❌ cloudflared no está corriendo"
    echo "Inicia con: ./scripts/start_cloudflared_tunnel.sh"
    exit 1
fi

echo "✅ cloudflared está corriendo"
echo ""

# Intentar obtener hostname de los logs o procesos
HOSTNAME=$(ps aux | grep cloudflared | grep -oE '[a-z0-9-]+\.trycloudflare\.com' | head -1)

if [ -z "$HOSTNAME" ]; then
    echo "⚠️  No se pudo detectar hostname automáticamente"
    echo "Revisa la salida de cloudflared para ver el hostname"
    echo ""
    echo "Busca una línea que diga:"
    echo "  https://xxxx-xx-xx-xx-xx.trycloudflare.com"
    echo ""
    echo "El hostname es: xxxx-xx-xx-xx-xx.trycloudflare.com"
else
    echo "Hostname detectado: $HOSTNAME"
    echo ""
    echo "=========================================="
    echo "Configuración para Looker Studio"
    echo "=========================================="
    echo ""
    echo "JDBC URL:"
    echo "  jdbc:postgresql://${HOSTNAME}:5432/barcelona_housing"
    echo ""
    echo "O BASIC Connection:"
    echo "  Hostname: $HOSTNAME"
    echo "  Port: 5432"
    echo "  Database: barcelona_housing"
    echo "  Username: adrianiraeguialvear"
    echo "  Password: (tu contraseña de PostgreSQL)"
    echo ""
fi

echo ""
echo "⚠️  Nota: Si el puerto 5432 no funciona, cloudflared puede estar"
echo "   usando un puerto diferente. Revisa los logs de cloudflared"
echo "   para ver el puerto TCP real."
echo ""
