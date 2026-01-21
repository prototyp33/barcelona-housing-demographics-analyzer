#!/bin/bash
# Iniciar túnel cloudflared para Looker Studio (gratis, sin tarjeta)

echo "=========================================="
echo "Túnel cloudflared para Looker Studio"
echo "=========================================="
echo ""

if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared no está instalado"
    echo ""
    echo "Instalando cloudflared..."
    brew install cloudflare/cloudflare/cloudflared
    echo ""
fi

echo "⚠️  IMPORTANTE:"
echo "  1. Este túnel conecta Looker Studio a tu PostgreSQL local"
echo "  2. La URL cambiará cada vez que reinicies cloudflared"
echo "  3. Mantén esta ventana abierta mientras uses Looker Studio"
echo ""
echo "Cuando cloudflared inicie, verás una línea como:"
echo "  +--------------------------------------------------------------------------------------------+"
echo "  |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable): |"
echo "  |  https://xxxx-xx-xx-xx-xx.trycloudflare.com                                               |"
echo "  +--------------------------------------------------------------------------------------------+"
echo ""
echo "Pero para PostgreSQL necesitamos TCP, así que verás:"
echo "  tcp://xxxx-xx-xx-xx-xx.trycloudflare.com:PORT"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""
echo "=========================================="
echo ""

# Iniciar cloudflared con TCP
cloudflared tunnel --url tcp://localhost:5432
