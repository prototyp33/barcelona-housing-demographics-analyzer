#!/bin/bash
# Iniciar túnel ngrok para Looker Studio

NGROK_BIN="$HOME/.ngrok/ngrok"

if [ ! -f "$NGROK_BIN" ]; then
    echo "❌ ngrok no está instalado"
    echo "Ejecuta: ./scripts/quick_ngrok_setup.sh"
    exit 1
fi

echo "=========================================="
echo "Túnel ngrok para Looker Studio"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANTE:"
echo "  1. Este túnel conecta Looker Studio a tu PostgreSQL local"
echo "  2. La URL cambiará cada vez que reinicies ngrok"
echo "  3. Mantén esta ventana abierta mientras uses Looker Studio"
echo ""
echo "Cuando ngrok inicie, verás una línea como:"
echo "  Forwarding  tcp://0.tcp.ngrok.io:12345 -> localhost:5432"
echo ""
echo "Copia la URL (ej: 0.tcp.ngrok.io:12345) y úsala en Looker Studio:"
echo "  JDBC URL: jdbc:postgresql://0.tcp.ngrok.io:12345/barcelona_housing"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""
echo "=========================================="
echo ""

# Iniciar ngrok
"$NGROK_BIN" tcp 5432
