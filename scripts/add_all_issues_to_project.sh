#!/bin/bash
# Add all new issues (Epics Fase 2-4 + Spike Issues) to GitHub Project

set -e

PROJECT_NUMBER=1
OWNER="prototyp33"
REPO="barcelona-housing-demographics-analyzer"

echo "🔗 Agregando todas las issues al proyecto GitHub..."
echo ""

# Epics Fase 2-4
EPICS=(194 195 196)

echo "## Agregando Epic Placeholders (Fase 2-4)..."
for epic_num in "${EPICS[@]}"; do
    if gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
        --url "https://github.com/$OWNER/$REPO/issues/$epic_num" 2>/dev/null; then
        echo "   ✅ Epic #$epic_num agregado"
    else
        OUTPUT=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
            --url "https://github.com/$OWNER/$REPO/issues/$epic_num" 2>&1)
        if echo "$OUTPUT" | grep -qi "already exists\|already in"; then
            echo "   ✅ Epic #$epic_num ya está en el proyecto"
        else
            echo "   ⚠️  Error al agregar Epic #$epic_num: $OUTPUT"
        fi
    fi
done
echo ""

# Issues del Spike
MILESTONE="Spike Validation (Dec 16-20)"
echo "## Agregando Issues del Spike..."
SPIKE_ISSUES=$(gh issue list --milestone "$MILESTONE" --json number --jq '.[].number')

if [ -z "$SPIKE_ISSUES" ]; then
    echo "   ⚠️  No se encontraron issues del spike"
else
    echo "$SPIKE_ISSUES" | while read -r issue_num; do
        if gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
            --url "https://github.com/$OWNER/$REPO/issues/$issue_num" 2>/dev/null; then
            echo "   ✅ Issue #$issue_num agregada"
        else
            OUTPUT=$(gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
                --url "https://github.com/$OWNER/$REPO/issues/$issue_num" 2>&1)
            if echo "$OUTPUT" | grep -qi "already exists\|already in"; then
                echo "   ✅ Issue #$issue_num ya está en el proyecto"
            else
                echo "   ⚠️  Error al agregar Issue #$issue_num: $OUTPUT"
            fi
        fi
    done
fi
echo ""

echo "========================================="
echo "✅ Issues agregadas al proyecto"
echo "========================================="
echo ""
echo "📊 Ver proyecto:"
echo "   https://github.com/$OWNER/$REPO/projects/$PROJECT_NUMBER"
echo ""
echo "📋 Próximo paso: Configurar custom fields en GitHub Projects UI"

