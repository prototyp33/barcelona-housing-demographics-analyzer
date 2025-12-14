#!/bin/bash
# Verify Fase 1 setup is complete
# Run this after configuring custom fields

set -e

echo "🔍 Verificando Setup Completo de Fase 1..."
echo ""

MILESTONE="Fase 1: Database Infrastructure"
EPIC_NUMBER=187

# Verificar Epic
echo "## Epic Principal"
EPIC=$(gh issue view "$EPIC_NUMBER" --json number,title,state,labels --jq '{number: .number, title: .title, state: .state, labels: [.labels[].name] | join(", ")}')
echo "$EPIC"
echo ""

# Verificar Sub-Issues
echo "## Sub-Issues"
SUB_ISSUES=$(gh issue list --milestone "$MILESTONE" --label "user-story" --json number,title,state --jq '.[] | "#\(.number): \(.title) (\(.state))"')

if [ -z "$SUB_ISSUES" ]; then
    echo "⚠️  No se encontraron sub-issues"
else
    echo "$SUB_ISSUES"
    COUNT=$(echo "$SUB_ISSUES" | wc -l | tr -d ' ')
    echo ""
    echo "Total: $COUNT sub-issues"
fi

echo ""

# Verificar referencias al parent epic
echo "## Verificación de Referencias al Parent Epic"
echo ""

for issue in 188 189 190 191 192 193; do
    BODY=$(gh issue view "$issue" --json body --jq '.body')
    # Verificar si tiene "Part of #187" o "#187" en sección Parent Epic
    if echo "$BODY" | grep -q "Part of #$EPIC_NUMBER" || (echo "$BODY" | grep -q "## Parent Epic" && echo "$BODY" | grep -q "#$EPIC_NUMBER"); then
        echo "   ✅ #$issue: Referencia correcta"
    else
        echo "   ⚠️  #$issue: Falta referencia al Epic #$EPIC_NUMBER"
    fi
done

echo ""
echo "========================================="
echo "📋 Próximos Pasos"
echo "========================================="
echo ""
echo "1. Si faltan referencias, ejecutar:"
echo "   ./scripts/fix_fase1_parent_references.sh"
echo ""
echo "2. Actualizar Epic con resumen:"
echo "   ./scripts/update_epic_187_summary.sh"
echo ""
echo "3. Configurar custom fields en GitHub Projects UI"
echo "   Ver: docs/FASE1_CUSTOM_FIELDS_REFERENCE.md"
echo ""

