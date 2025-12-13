#!/bin/bash
# Fix parent epic references in Fase 1 sub-issues
# Add "Part of #187" to each sub-issue if missing

set -e

EPIC_NUMBER=187
SUB_ISSUES=(188 189 190 191 192 193)

echo "🔧 Actualizando referencias al parent epic en sub-issues..."
echo ""

for issue_num in "${SUB_ISSUES[@]}"; do
    echo "📝 Verificando issue #$issue_num..."
    
    # Obtener el body actual
    CURRENT_BODY=$(gh issue view "$issue_num" --json body --jq '.body')
    
    # Verificar si ya tiene la referencia correcta
    if echo "$CURRENT_BODY" | grep -q "Part of #$EPIC_NUMBER"; then
        echo "   ✅ Issue #$issue_num ya tiene referencia correcta"
    else
        # Agregar referencia al inicio del body
        NEW_BODY="## Parent Epic

Part of #$EPIC_NUMBER

---

$CURRENT_BODY"
        
        # Actualizar el issue
        echo "$NEW_BODY" | gh issue edit "$issue_num" --body-file -
        echo "   ✅ Issue #$issue_num actualizado con referencia al Epic #$EPIC_NUMBER"
    fi
    echo ""
done

echo "✅ Verificación completada"
echo ""
echo "📊 Verificar:"
echo "   gh issue list --milestone 'Fase 1: Database Infrastructure' --label 'user-story'"

