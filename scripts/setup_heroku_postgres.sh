#!/bin/bash
# Script para migrar a Heroku Postgres (solución más fácil para Looker Studio)

# No usar set -e para manejar errores mejor

echo "=========================================="
echo "Migración a Heroku Postgres"
echo "=========================================="

# Verificar Heroku CLI
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI no está instalado"
    echo ""
    echo "Instalando Heroku CLI..."
    brew install heroku/brew/heroku
fi

echo ""
echo "1. Verificando login en Heroku..."
if ! heroku auth:whoami &> /dev/null; then
    echo "⚠️  No estás logueado en Heroku"
    echo "Abriendo navegador para login..."
    heroku login
else
    echo "✅ Ya estás logueado en Heroku"
    heroku auth:whoami
fi

echo ""
echo "2. Creando app en Heroku..."
read -p "Nombre para la app (o Enter para generar automático): " USER_APP_NAME

if [ -z "$USER_APP_NAME" ]; then
    APP_NAME="barcelona-housing-$(date +%s | tail -c 5)"
else
    APP_NAME="$USER_APP_NAME"
fi

echo "Creando app: $APP_NAME"
if heroku create "$APP_NAME" 2>&1; then
    echo "✅ App creada: $APP_NAME"
else
    # Si falla, puede que el nombre ya exista, intentar con otro
    if echo "$APP_NAME" | grep -q "already taken\|name is already taken"; then
        APP_NAME="barcelona-housing-$(date +%s)"
        echo "Nombre ocupado, intentando con: $APP_NAME"
        heroku create "$APP_NAME"
    else
        echo "⚠️  Error creando app. Intentando continuar..."
    fi
fi

echo ""
echo "3. Creando base de datos PostgreSQL..."
if heroku addons:create heroku-postgresql:mini --app "$APP_NAME" 2>&1; then
    echo "✅ Base de datos PostgreSQL creada"
else
    # Verificar si ya existe
    if heroku addons --app "$APP_NAME" | grep -q "postgres"; then
        echo "✅ Base de datos PostgreSQL ya existe"
    else
        echo "❌ Error creando base de datos"
        exit 1
    fi
fi

echo ""
echo "4. Obteniendo información de conexión..."
DATABASE_URL=$(heroku config:get DATABASE_URL --app "$APP_NAME")
if [ -z "$DATABASE_URL" ]; then
    echo "❌ No se pudo obtener DATABASE_URL"
    exit 1
fi

echo "✅ URL de conexión obtenida"

# Parsear URL (formato: postgres://user:pass@host:port/database)
# Extraer componentes
DB_INFO=$(heroku pg:credentials:url --app "$APP_NAME" | grep -A 5 "Connection" | tail -1)

echo ""
echo "5. Migrando datos desde PostgreSQL local..."
echo "   Esto puede tardar unos minutos..."
if heroku pg:push barcelona_housing "$DATABASE_URL" --app "$APP_NAME"; then
    echo "✅ Datos migrados exitosamente"
else
    echo "❌ Error migrando datos"
    echo "   Intenta manualmente:"
    echo "   heroku pg:push barcelona_housing DATABASE_URL --app $APP_NAME"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Migración Completa"
echo "=========================================="
echo ""
echo "Información para Looker Studio:"
echo ""
echo "Obtén las credenciales con:"
echo "  heroku pg:credentials:url --app $APP_NAME"
echo ""
echo "O usa la URL completa en JDBC:"
echo "  $DATABASE_URL"
echo ""
echo "Para ver todas las variables:"
echo "  heroku config --app $APP_NAME"
echo ""
echo "Para ver el estado de la base de datos:"
echo "  heroku pg:info --app $APP_NAME"
echo ""
