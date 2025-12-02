#!/usr/bin/env bash

set -e

# Script para migrar branches existentes a la nueva convención
# Uso: ./scripts/git/migrate_branch.sh <old_branch_name> [new_type] [issue_number]

OLD_BRANCH=$1
NEW_TYPE=${2:-feature}
ISSUE_NUM=$3

if [ -z "$OLD_BRANCH" ]; then
    echo "❌ Error: Debes proporcionar el nombre de la branch antigua"
    echo ""
    echo "Uso: ./scripts/git/migrate_branch.sh <old_branch_name> [new_type] [issue_number]"
    echo ""
    echo "Ejemplos:"
    echo "  ./scripts/git/migrate_branch.sh feature-ideas-analysis feature"
    echo "  ./scripts/git/migrate_branch.sh fix-deduplication-and-verify-geometry fix 13"
    exit 1
fi

# Verificar que la branch existe
if ! git show-ref --verify --quiet refs/heads/"$OLD_BRANCH" && ! git show-ref --verify --quiet refs/remotes/origin/"$OLD_BRANCH"; then
    echo "❌ Error: La branch '$OLD_BRANCH' no existe"
    exit 1
fi

# Crear nuevo nombre
if [ -n "$ISSUE_NUM" ]; then
    NEW_BRANCH="${NEW_TYPE}/${ISSUE_NUM}-$(echo "$OLD_BRANCH" | sed 's/feature-//;s/fix-//' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')"
else
    NEW_BRANCH="${NEW_TYPE}/$(echo "$OLD_BRANCH" | sed 's/feature-//;s/fix-//' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')"
fi

echo "🔄 Migrando branch:"
echo "   Antigua: $OLD_BRANCH"
echo "   Nueva:   $NEW_BRANCH"
echo ""

# Si la branch existe localmente
if git show-ref --verify --quiet refs/heads/"$OLD_BRANCH"; then
    echo "📥 Cambiando a branch local..."
    git checkout "$OLD_BRANCH"
    
    # Actualizar con origin si existe remota
    if git show-ref --verify --quiet refs/remotes/origin/"$OLD_BRANCH"; then
        echo "🔄 Actualizando con cambios remotos..."
        git pull origin "$OLD_BRANCH" || true
    fi
    
    # Renombrar localmente
    echo "✏️  Renombrando branch local..."
    git branch -m "$OLD_BRANCH" "$NEW_BRANCH"
    
    # Si existe remota, renombrar también
    if git show-ref --verify --quiet refs/remotes/origin/"$OLD_BRANCH"; then
        echo "📤 Renombrando branch remota..."
        git push origin "$NEW_BRANCH"
        git push origin --delete "$OLD_BRANCH"
        git branch --set-upstream-to=origin/"$NEW_BRANCH" "$NEW_BRANCH"
    else
        echo "📤 Creando branch remota..."
        git push origin "$NEW_BRANCH"
        git branch --set-upstream-to=origin/"$NEW_BRANCH" "$NEW_BRANCH"
    fi
else
    # Solo existe remotamente
    echo "📥 Creando branch local desde remota..."
    git checkout -b "$NEW_BRANCH" origin/"$OLD_BRANCH"
    
    echo "📤 Renombrando branch remota..."
    git push origin "$NEW_BRANCH"
    git push origin --delete "$OLD_BRANCH"
    git branch --set-upstream-to=origin/"$NEW_BRANCH" "$NEW_BRANCH"
fi

echo ""
echo "✅ Migración completada!"
echo ""
echo "🌿 Branch actual: $NEW_BRANCH"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Verifica que todo está correcto: git log --oneline -5"
echo "   2. Si hay cambios pendientes, haz commit"
echo "   3. Sincroniza con main: ./scripts/git/sync_with_main.sh"
echo "   4. Crea PR: ./scripts/git/create_pr.sh"

