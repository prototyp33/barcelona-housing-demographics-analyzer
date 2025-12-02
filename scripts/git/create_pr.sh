#!/usr/bin/env bash

set -e

# Script helper para crear Pull Request con template
# Uso: ./scripts/git/create_pr.sh

# Obtener branch actual
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "❌ Error: Estás en la branch main. Cambia a una feature branch."
    exit 1
fi

# Verificar que gh CLI está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: gh CLI no está instalado."
    echo "Instala desde: https://cli.github.com/"
    exit 1
fi

# Extraer número de issue del nombre de branch (si existe)
ISSUE_NUM=$(echo "$CURRENT_BRANCH" | grep -oE '[0-9]+' | head -1)

# Determinar tipo de PR desde el nombre de branch
if [[ $CURRENT_BRANCH == fix/* ]]; then
    PR_TYPE="Fix"
    PR_LABEL="bug"
elif [[ $CURRENT_BRANCH == feature/* ]]; then
    PR_TYPE="Feature"
    PR_LABEL="enhancement"
elif [[ $CURRENT_BRANCH == refactor/* ]]; then
    PR_TYPE="Refactor"
    PR_LABEL="enhancement"
elif [[ $CURRENT_BRANCH == etl/* ]]; then
    PR_TYPE="ETL"
    PR_LABEL="etl"
elif [[ $CURRENT_BRANCH == dashboard/* ]]; then
    PR_TYPE="Dashboard"
    PR_LABEL="dashboard"
elif [[ $CURRENT_BRANCH == docs/* ]]; then
    PR_TYPE="Docs"
    PR_LABEL="documentation"
elif [[ $CURRENT_BRANCH == test/* ]]; then
    PR_TYPE="Test"
    PR_LABEL="testing"
else
    PR_TYPE="Update"
    PR_LABEL="enhancement"
fi

# Obtener título del último commit
LAST_COMMIT_MSG=$(git log -1 --pretty=%B | head -1)

# Crear título del PR
if [ -n "$ISSUE_NUM" ]; then
    PR_TITLE="${PR_TYPE}: ${LAST_COMMIT_MSG} (#${ISSUE_NUM})"
else
    PR_TITLE="${PR_TYPE}: ${LAST_COMMIT_MSG}"
fi

# Template de PR
PR_BODY="## ✨ Descripción

$(git log -1 --pretty=%B | tail -n +2)

## 📝 Cambios principales

$(git diff origin/main...HEAD --name-status | sed 's/^/- /')

## 🧪 Testing

- [ ] Tests unitarios pasan localmente (\`pytest\`)
- [ ] ETL smoke test ejecutado (\`python scripts/process_and_load.py\`)
- [ ] Dashboard se visualiza correctamente (si aplica)
- [ ] Validación con datos reales

## ✅ Checklist

- [ ] Mi código sigue las guías de estilo del proyecto (PEP 8, type hints)
- [ ] He realizado una auto-revisión de mi propio código
- [ ] He comentado mi código, especialmente en áreas complejas
- [ ] He realizado los cambios correspondientes en la documentación
- [ ] Mis cambios no introducen nuevas advertencias
- [ ] He añadido tests que demuestran que mi solución funciona"

# Añadir referencia a issue si existe
if [ -n "$ISSUE_NUM" ]; then
    PR_BODY="$PR_BODY

## 🔗 Issue Relacionado

Fixes #$ISSUE_NUM"
fi

echo "🚀 Creando Pull Request..."
echo "📋 Título: $PR_TITLE"
echo "🏷️  Label: $PR_LABEL"
echo "🌿 Branch: $CURRENT_BRANCH"
echo ""

# Crear PR
gh pr create \
  --title "$PR_TITLE" \
  --body "$PR_BODY" \
  --label "$PR_LABEL"

echo ""
echo "✅ Pull Request creado exitosamente!"
echo "🔗 Ver PR: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/pulls"

