#!/usr/bin/env bash

set -e

# Script para sincronizar feature branch con main
# Uso: ./scripts/git/sync_with_main.sh

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "❌ Error: Ya estás en main. Este script es para feature branches."
    exit 1
fi

echo "🔄 Sincronizando $CURRENT_BRANCH con main..."
echo ""

# Verificar que no hay cambios sin commitear (opcional, pero recomendado)
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: Tienes cambios sin commitear."
    read -p "¿Quieres guardarlos en stash antes de continuar? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "💾 Guardando cambios en stash..."
        git stash push -m "Auto-stash antes de sync con main - $(date +%Y-%m-%d)"
        STASHED=true
    else
        echo "❌ Abortando. Commit o stash tus cambios primero."
        exit 1
    fi
else
    STASHED=false
fi

# Fetch últimos cambios
echo "📥 Obteniendo últimos cambios de origin..."
git fetch origin

# Verificar si hay cambios en main
LOCAL_MAIN=$(git rev-parse main)
REMOTE_MAIN=$(git rev-parse origin/main)

if [ "$LOCAL_MAIN" = "$REMOTE_MAIN" ]; then
    echo "✅ main ya está actualizado. No hay cambios nuevos."
else
    echo "🔄 main tiene cambios nuevos. Actualizando..."
    git checkout main
    git pull origin main
    git checkout "$CURRENT_BRANCH"
fi

# Rebase con main
echo "🔀 Haciendo rebase con origin/main..."
if git rebase origin/main; then
    echo "✅ Rebase completado exitosamente"
else
    echo "⚠️  Rebase con conflictos. Resuelve los conflictos y luego:"
    echo "   1. git add <archivos_resueltos>"
    echo "   2. git rebase --continue"
    echo "   3. Ejecuta este script nuevamente"
    
    # Restaurar stash si existía
    if [ "$STASHED" = true ]; then
        echo ""
        echo "📦 Restaurando cambios guardados..."
        git stash pop
    fi
    
    exit 1
fi

# Restaurar cambios guardados
if [ "$STASHED" = true ]; then
    echo ""
    echo "📦 Restaurando cambios guardados..."
    if git stash pop; then
        echo "✅ Cambios restaurados"
    else
        echo "⚠️  Hubo conflictos al restaurar stash. Resuélvelos manualmente."
    fi
fi

echo ""
echo "✅ Sincronización completada!"
echo ""
echo "📤 Próximo paso:"
echo "   git push origin $CURRENT_BRANCH --force-with-lease"
echo ""
echo "⚠️  Nota: Usa --force-with-lease (no --force) para mayor seguridad"

