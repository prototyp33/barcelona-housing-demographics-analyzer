#!/usr/bin/env bash

set -e

# Script para crear feature branch automáticamente desde una GitHub Issue
# Uso: ./scripts/git/create_feature_branch.sh <issue_number> [type]

ISSUE_NUM=$1
ISSUE_TYPE=${2:-feature}

if [ -z "$ISSUE_NUM" ]; then
    echo "❌ Error: Debes proporcionar un número de issue"
    echo ""
    echo "Uso: ./scripts/git/create_feature_branch.sh <issue_number> [type]"
    echo ""
    echo "Tipos válidos:"
    echo "  - feature  : Nueva funcionalidad (default)"
    echo "  - fix      : Corrección de bug"
    echo "  - refactor : Refactorización de código"
    echo "  - etl      : Trabajo relacionado con ETL"
    echo "  - dashboard: Mejoras del dashboard"
    echo "  - docs     : Documentación"
    echo "  - test     : Tests"
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/git/create_feature_branch.sh 49 fix"
    echo "  ./scripts/git/create_feature_branch.sh 52 feature"
    exit 1
fi

# Verificar que gh CLI está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: gh CLI no está instalado."
    echo "Instala desde: https://cli.github.com/"
    exit 1
fi

# Verificar que estamos en un repo git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: No estás en un repositorio Git"
    exit 1
fi

# Obtener título de la issue desde GitHub
echo "🔍 Obteniendo información de Issue #$ISSUE_NUM..."
ISSUE_TITLE=$(gh issue view $ISSUE_NUM --json title -q .title 2>/dev/null)

if [ -z "$ISSUE_TITLE" ]; then
    echo "❌ Error: No se encontró la Issue #$ISSUE_NUM"
    echo "Verifica que la issue existe y que tienes acceso al repositorio"
    exit 1
fi

# Crear nombre de branch normalizado
BRANCH_NAME=$(echo "$ISSUE_TITLE" | \
    tr '[:upper:]' '[:lower:]' | \
    sed 's/[^a-z0-9]/-/g' | \
    sed 's/--*/-/g' | \
    sed 's/^-//' | \
    sed 's/-$//' | \
    cut -c1-50)  # Limitar longitud

BRANCH_NAME="${ISSUE_TYPE}/${ISSUE_NUM}-${BRANCH_NAME}"

# Verificar que no existe la branch
if git show-ref --verify --quiet refs/heads/"$BRANCH_NAME"; then
    echo "⚠️  Warning: La branch '$BRANCH_NAME' ya existe localmente"
    read -p "¿Quieres cambiarte a ella? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout "$BRANCH_NAME"
        exit 0
    else
        exit 1
    fi
fi

# Actualizar main y crear branch
echo "🔄 Actualizando main..."
git checkout main
git pull origin main

echo "🌿 Creando branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

echo ""
echo "✅ Branch creada exitosamente!"
echo ""
echo "📋 Issue: #$ISSUE_NUM - $ISSUE_TITLE"
echo "🌿 Branch: $BRANCH_NAME"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Haz tus cambios"
echo "   2. Commit con: git commit -m \"$ISSUE_TYPE: <descripción> - Fixes #$ISSUE_NUM\""
echo "   3. Push con: git push origin $BRANCH_NAME"
echo "   4. Crea PR con: ./scripts/git/create_pr.sh"
echo ""

