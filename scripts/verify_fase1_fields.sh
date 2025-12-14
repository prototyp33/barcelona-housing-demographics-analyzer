#!/bin/bash
# Verify Fase 1 Custom Fields Configuration
# Este script verifica que las issues de Fase 1 existen y muestra sus números

set -e

echo "🔍 Verificando Issues de Fase 1..."
echo ""

MILESTONE="Fase 1: Database Infrastructure"

# Obtener Epic
EPIC=$(gh issue list --label epic --milestone "$MILESTONE" --json number,title --jq '.[0]')

if [ -z "$EPIC" ] || [ "$EPIC" == "null" ]; then
    echo "❌ Epic de Fase 1 no encontrado"
    echo "   Ejecutar primero: ./scripts/create_fase_1_issues.sh"
    exit 1
fi

EPIC_NUMBER=$(echo "$EPIC" | jq -r '.number')
EPIC_TITLE=$(echo "$EPIC" | jq -r '.title')

echo "✅ Epic encontrado:"
echo "   #$EPIC_NUMBER: $EPIC_TITLE"
echo ""

# Obtener sub-issues
echo "📋 Sub-issues de Fase 1:"
echo ""

ISSUES=$(gh issue list --milestone "$MILESTONE" --label "user-story" --json number,title --jq '.[] | "\(.number): \(.title)"')

if [ -z "$ISSUES" ]; then
    echo "⚠️  No se encontraron sub-issues"
    echo "   Verificar que el script create_fase_1_issues.sh se ejecutó correctamente"
else
    echo "$ISSUES" | while IFS= read -r issue; do
        echo "   ✅ $issue"
    done
fi

echo ""
echo "========================================="
echo "📊 Resumen"
echo "========================================="
echo ""
echo "Epic: #$EPIC_NUMBER"
echo "Sub-issues: $(echo "$ISSUES" | wc -l | tr -d ' ')"
echo ""
echo "📝 Próximos pasos:"
echo ""
echo "1. Ir a GitHub Projects → 'Barcelona Housing - Roadmap'"
echo "2. Buscar cada issue y configurar custom fields según:"
echo "   docs/FASE1_CUSTOM_FIELDS_REFERENCE.md"
echo ""
echo "3. O usar el CSV como referencia:"
echo "   data/reference/fase1_custom_fields.csv"
echo ""

