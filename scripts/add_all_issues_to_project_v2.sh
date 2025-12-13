#!/bin/bash
# Add all new issues (Epics Fase 2-4 + Spike Issues) to GitHub Project
# Version 2: Improved error handling and timeout

set -e

PROJECT_NUMBER=1
OWNER="prototyp33"
REPO="barcelona-housing-demographics-analyzer"
TIMEOUT=10  # seconds per command

echo "🔗 Agregando todas las issues al proyecto GitHub..."
echo ""

# Function to add issue with timeout
add_issue_to_project() {
    local issue_num=$1
    local issue_type=$2
    
    echo -n "   Agregando $issue_type #$issue_num... "
    
    # Try with timeout
    OUTPUT=$(timeout $TIMEOUT gh project item-add "$PROJECT_NUMBER" --owner "$OWNER" \
        --url "https://github.com/$OWNER/$REPO/issues/$issue_num" 2>&1) || true
    
    if [ $? -eq 0 ] && [ -z "$OUTPUT" ]; then
        echo "✅ agregado"
        return 0
    elif echo "$OUTPUT" | grep -qi "already exists\|already in\|already added"; then
        echo "✅ ya está en el proyecto"
        return 0
    else
        echo "⚠️  error: $OUTPUT"
        return 1
    fi
}

# Epics Fase 2-4
EPICS=(194 195 196)

echo "## Agregando Epic Placeholders (Fase 2-4)..."
SUCCESS_COUNT=0
ERROR_COUNT=0

for epic_num in "${EPICS[@]}"; do
    if add_issue_to_project "$epic_num" "Epic"; then
        ((SUCCESS_COUNT++))
    else
        ((ERROR_COUNT++))
    fi
    sleep 1  # Small delay between requests
done
echo ""

# Issues del Spike
MILESTONE="Spike Validation (Dec 16-20)"
echo "## Agregando Issues del Spike..."
SPIKE_ISSUES=$(gh issue list --milestone "$MILESTONE" --json number --jq '.[].number' 2>/dev/null || echo "")

if [ -z "$SPIKE_ISSUES" ]; then
    echo "   ⚠️  No se encontraron issues del spike"
    echo "   Verificar milestone: $MILESTONE"
else
    echo "$SPIKE_ISSUES" | while read -r issue_num; do
        if [ -n "$issue_num" ]; then
            add_issue_to_project "$issue_num" "Issue"
            sleep 1  # Small delay between requests
        fi
    done
fi
echo ""

echo "========================================="
echo "✅ Proceso completado"
echo "========================================="
echo ""
echo "📊 Ver proyecto:"
echo "   https://github.com/$OWNER/$REPO/projects/$PROJECT_NUMBER"
echo ""
echo "📋 Si hubo errores, agregar issues manualmente via GitHub UI:"
echo "   1. Ir al proyecto"
echo "   2. Click en 'Add item'"
echo "   3. Buscar issue por número (#194, #195, etc.)"
echo ""

