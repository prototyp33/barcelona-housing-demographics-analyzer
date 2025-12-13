#!/bin/bash
# Add Fase 1 issues to GitHub Project
# Verifica si están y las agrega si faltan

set -e

PROJECT_NUMBER=1
OWNER="prototyp33"
REPO="barcelona-housing-demographics-analyzer"
ISSUES=(187 188 189 190 191 192 193)

echo "🔍 Verificando issues de Fase 1 en el proyecto..."
echo ""

# Obtener issues actuales en el proyecto
echo "## Issues actuales en el proyecto:"
CURRENT_ITEMS=$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "   ⚠️  Error al obtener items del proyecto"
    echo "      Error: $CURRENT_ITEMS"
    echo ""
    echo "   💡 Verificar:"
    echo "      - ¿El proyecto #$PROJECT_NUMBER existe?"
    echo "      - ¿Tienes permisos para acceder al proyecto?"
    echo "      - Probar: gh project view $PROJECT_NUMBER --owner $OWNER"
    echo ""
    CURRENT_ITEMS="[]"
fi

if [ "$CURRENT_ITEMS" != "[]" ] && [ -n "$CURRENT_ITEMS" ]; then
    echo "$CURRENT_ITEMS" | jq -r '.items[] | "#\(.content.number) - \(.content.title)"' 2>/dev/null || echo "   (No se pudieron listar items)"
else
    echo "   (Proyecto vacío o error al obtener items)"
fi

echo ""
echo "## Verificando issues de Fase 1 (#187-#193)..."
echo ""

# Verificar y agregar cada issue
ADDED_COUNT=0
ALREADY_EXISTS_COUNT=0

for issue_num in "${ISSUES[@]}"; do
    # Verificar si el issue ya está en el proyecto
    if echo "$CURRENT_ITEMS" | jq -r ".items[] | select(.content.number == $issue_num) | .content.number" 2>/dev/null | grep -q "$issue_num"; then
        echo "   ✅ Issue #$issue_num ya está en el proyecto"
        ((ALREADY_EXISTS_COUNT++))
    else
        echo "   ⏭️  Agregando issue #$issue_num al proyecto..."
        
        # Agregar issue al proyecto
        OUTPUT=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
            --url "https://github.com/$OWNER/$REPO/issues/$issue_num" 2>&1)
        EXIT_CODE=$?
        
        if [ $EXIT_CODE -eq 0 ]; then
            echo "   ✅ Issue #$issue_num agregado exitosamente"
            ((ADDED_COUNT++))
        else
            # Verificar si el error es porque ya existe
            if echo "$OUTPUT" | grep -qi "already exists\|already in"; then
                echo "   ✅ Issue #$issue_num ya está en el proyecto"
                ((ALREADY_EXISTS_COUNT++))
            else
                echo "   ⚠️  Error al agregar issue #$issue_num"
                echo "      Error: $OUTPUT"
            fi
        fi
    fi
    echo ""
done

echo "========================================="
echo "📊 Resumen"
echo "========================================="
echo ""
echo "Total issues verificadas: ${#ISSUES[@]}"
echo "Ya existían: $ALREADY_EXISTS_COUNT"
echo "Agregadas: $ADDED_COUNT"
echo ""

if [ $ADDED_COUNT -gt 0 ]; then
    echo "✅ Issues agregadas al proyecto exitosamente"
    echo ""
    echo "📋 Próximo paso: Configurar custom fields en GitHub Projects UI"
    echo "   Ver: docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md"
else
    echo "✅ Todas las issues ya están en el proyecto"
    echo ""
    echo "📋 Próximo paso: Configurar custom fields en GitHub Projects UI"
    echo "   Ver: docs/FASE1_CUSTOM_FIELDS_QUICK_COPY.md"
fi

echo ""
echo "🔗 Ver proyecto:"
echo "   https://github.com/$OWNER/$REPO/projects/$PROJECT_NUMBER"

