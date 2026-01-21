#!/bin/bash
# Setup rápido de ngrok para Looker Studio

echo "=========================================="
echo "Setup ngrok para Looker Studio"
echo "=========================================="

NGROK_DIR="$HOME/.ngrok"
NGROK_BIN="$NGROK_DIR/ngrok"

# Verificar si ngrok ya está instalado
if [ -f "$NGROK_BIN" ]; then
    echo "✅ ngrok ya está instalado"
    "$NGROK_BIN" version
else
    echo "Instalando ngrok..."
    
    # Crear directorio
    mkdir -p "$NGROK_DIR"
    
    # Descargar ngrok
    echo "Descargando ngrok..."
    curl -o /tmp/ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-arm64.zip
    
    # Extraer
    unzip -q /tmp/ngrok.zip -d "$NGROK_DIR"
    chmod +x "$NGROK_BIN"
    
    # Limpiar
    rm /tmp/ngrok.zip
    
    echo "✅ ngrok instalado en $NGROK_BIN"
fi

echo ""
echo "=========================================="
echo "Iniciando túnel ngrok..."
echo "=========================================="
echo ""
echo "⚠️  IMPORTANTE:"
echo "  1. ngrok creará un túnel a tu PostgreSQL local"
echo "  2. La URL cambiará cada vez que reinicies ngrok"
echo "  3. Usa la URL 'Forwarding' en Looker Studio"
echo ""
echo "Presiona Ctrl+C para detener ngrok"
echo ""
echo "Esperando conexión..."
echo ""

# Iniciar ngrok
"$NGROK_BIN" tcp 5432
