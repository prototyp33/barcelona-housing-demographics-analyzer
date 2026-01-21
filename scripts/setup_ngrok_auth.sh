#!/bin/bash
# Script para configurar autenticación de ngrok

echo "=========================================="
echo "Configuración de ngrok"
echo "=========================================="
echo ""

NGROK_BIN="$HOME/.ngrok/ngrok"

if [ ! -f "$NGROK_BIN" ]; then
    echo "❌ ngrok no está instalado"
    echo "Ejecuta: ./scripts/quick_ngrok_setup.sh"
    exit 1
fi

echo "ngrok requiere una cuenta gratuita para funcionar."
echo ""
echo "Pasos:"
echo "  1. Crea cuenta en: https://dashboard.ngrok.com/signup"
echo "  2. Verifica tu email"
echo "  3. Obtén tu authtoken en: https://dashboard.ngrok.com/get-started/your-authtoken"
echo ""
read -p "¿Ya tienes tu authtoken? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Por favor:"
    echo "  1. Abre: https://dashboard.ngrok.com/signup"
    echo "  2. Crea cuenta y verifica email"
    echo "  3. Ve a: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  4. Copia tu authtoken"
    echo "  5. Vuelve a ejecutar este script"
    echo ""
    echo "O usa Heroku Postgres como alternativa (sin cuenta necesaria):"
    echo "  Ver: docs/QUICK_FIX_LOOKER_STUDIO.md"
    exit 0
fi

echo ""
read -sp "Pega tu authtoken aquí: " AUTHTOKEN
echo ""

if [ -z "$AUTHTOKEN" ]; then
    echo "❌ Authtoken vacío"
    exit 1
fi

echo ""
echo "Configurando authtoken..."
if "$NGROK_BIN" config add-authtoken "$AUTHTOKEN"; then
    echo "✅ Authtoken configurado correctamente"
    echo ""
    echo "Ahora puedes iniciar el túnel:"
    echo "  ./scripts/start_ngrok_tunnel.sh"
else
    echo "❌ Error configurando authtoken"
    exit 1
fi
