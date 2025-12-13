#!/bin/bash
# Verify Spike Setup is Complete
# Checks milestone, issues, project, and directory structure

set -e

echo "🔍 Verificando Setup del Spike..."
echo ""

MILESTONE="Spike Validation (Dec 16-20)"
PROJECT_NUMBER=1
OWNER="prototyp33"
REPO="barcelona-housing-demographics-analyzer"
SPIKE_DIR="spike-data-validation"

ERRORS=0
WARNINGS=0

# 1. Verificar Milestone
echo "## 1. Verificando Milestone"
MILESTONE_CHECK=$(gh api "repos/${OWNER}/${REPO}/milestones?state=all" --jq ".[] | select(.title == \"$MILESTONE\") | .title" 2>/dev/null || echo "")
if [ -n "$MILESTONE_CHECK" ]; then
    echo "   ✅ Milestone '$MILESTONE' existe"
else
    echo "   ⚠️  Milestone '$MILESTONE' no encontrado (puede ser normal si se creó con otro nombre)"
    ((WARNINGS++))
fi
echo ""

# 2. Verificar Issues del Spike
echo "## 2. Verificando Issues del Spike"
SPIKE_ISSUES=$(gh issue list --milestone "$MILESTONE" --json number,title,state --jq '.[] | "#\(.number): \(.title) (\(.state))"')

if [ -z "$SPIKE_ISSUES" ]; then
    echo "   ❌ No se encontraron issues del spike"
    ((ERRORS++))
else
    COUNT=$(echo "$SPIKE_ISSUES" | wc -l | tr -d ' ')
    echo "   ✅ Encontradas $COUNT issues del spike:"
    echo "$SPIKE_ISSUES" | while IFS= read -r issue; do
        echo "      - $issue"
    done
    
    # Verificar Master Tracker
    if echo "$SPIKE_ISSUES" | grep -q "Master Tracker"; then
        echo "   ✅ Master Tracker encontrado"
    else
        echo "   ⚠️  Master Tracker no encontrado"
        ((WARNINGS++))
    fi
    
    # Verificar que hay al menos 9 issues (Master + 8 sub-issues)
    if [ "$COUNT" -lt 9 ]; then
        echo "   ⚠️  Se esperaban al menos 9 issues (Master + 8 sub-issues), encontradas: $COUNT"
        ((WARNINGS++))
    fi
fi
echo ""

# 3. Verificar Estructura de Directorios
echo "## 3. Verificando Estructura de Directorios"
if [ -d "$SPIKE_DIR" ]; then
    echo "   ✅ Directorio $SPIKE_DIR existe"
    
    # Verificar subdirectorios
    REQUIRED_DIRS=("$SPIKE_DIR/data/raw" "$SPIKE_DIR/data/processed" "$SPIKE_DIR/data/logs" \
                   "$SPIKE_DIR/notebooks" "$SPIKE_DIR/outputs/reports" "$SPIKE_DIR/outputs/visualizations")
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo "   ✅ $dir existe"
        else
            echo "   ⚠️  $dir NO existe (crear si es necesario)"
            ((WARNINGS++))
        fi
    done
else
    echo "   ❌ Directorio $SPIKE_DIR NO existe"
    ((ERRORS++))
fi
echo ""

# 4. Verificar Archivos Clave
echo "## 4. Verificando Archivos Clave"
REQUIRED_FILES=("$SPIKE_DIR/README.md" "$SPIKE_DIR/requirements.txt" \
                "$SPIKE_DIR/notebooks/01-gracia-hedonic-model.ipynb" \
                "docs/templates/VIABILITY_REPORT_TEMPLATE.md" \
                "docs/templates/DECISION_RECORD_TEMPLATE.md")

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file existe"
    else
        echo "   ⚠️  $file NO existe"
        ((WARNINGS++))
    fi
done
echo ""

# 5. Verificar Issues en Proyecto (opcional)
echo "## 5. Verificando Issues en Proyecto GitHub"
PROJECT_ITEMS=$(gh project item-list "$PROJECT_NUMBER" --owner "$OWNER" --format json 2>/dev/null || echo "[]")

if [ "$PROJECT_ITEMS" != "[]" ] && [ -n "$PROJECT_ITEMS" ]; then
    SPIKE_IN_PROJECT=$(echo "$PROJECT_ITEMS" | jq -r ".items[] | select(.content.number >= 1) | .content.number" 2>/dev/null | head -1)
    if [ -n "$SPIKE_IN_PROJECT" ]; then
        echo "   ✅ Algunas issues del spike están en el proyecto"
    else
        echo "   ⚠️  Issues del spike no encontradas en el proyecto (agregar si es necesario)"
        ((WARNINGS++))
    fi
else
    echo "   ⚠️  No se pudo verificar items del proyecto (puede ser normal si el proyecto está vacío)"
    ((WARNINGS++))
fi
echo ""

# Resumen
echo "========================================="
echo "📊 Resumen de Verificación"
echo "========================================="
echo ""
echo "Errores: $ERRORS"
echo "Advertencias: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ Spike setup completo y listo!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Spike setup funcional pero con advertencias"
    exit 0
else
    echo "❌ Spike setup incompleto. Corregir errores antes de continuar."
    exit 1
fi

