#!/bin/bash
# Update Epic #187 with references to all sub-issues

set -e

EPIC_NUMBER=187
MILESTONE="Fase 1: Database Infrastructure"

echo "📋 Actualizando Epic #$EPIC_NUMBER con referencias a sub-issues..."
echo ""

# Obtener todos los sub-issues
SUB_ISSUES=$(gh issue list --milestone "$MILESTONE" --label "user-story" --json number,title --jq '.[] | "#\(.number): \(.title)"')

if [ -z "$SUB_ISSUES" ]; then
    echo "⚠️  No se encontraron sub-issues"
    exit 1
fi

# Contar sub-issues
COUNT=$(echo "$SUB_ISSUES" | wc -l | tr -d ' ')

echo "Encontrados $COUNT sub-issues:"
echo "$SUB_ISSUES" | while IFS= read -r issue; do
    echo "   ✅ $issue"
done

echo ""

# Crear comentario con referencias
COMMENT_BODY="## Sub-Issues Creados

$SUB_ISSUES

**Total:** $COUNT sub-issues para Fase 1

---

## Resumen de Esfuerzo

| Issue | Título | Horas |
|-------|--------|-------|
| DATA-101 | Create 8 fact tables | 8h |
| DATA-102 | Create 2 dimension tables | 6h |
| DATA-103 | Create indexes & constraints | 4h |
| DATA-104 | Update schema.sql | 4h |
| INFRA-101 | Setup test DB on Render | 3h |
| DOCS-101 | Document schema v2.0 | 2h |
| **TOTAL** | | **27h** |

---

## Custom Fields a Configurar en GitHub Projects UI

Ver referencia completa: \`docs/FASE1_CUSTOM_FIELDS_REFERENCE.md\`

### Epic #$EPIC_NUMBER
- **Epic:** DATA
- **Priority:** P0
- **Size:** XL
- **Estimate:** 49
- **Start Date:** 2026-01-06
- **Target Date:** 2026-01-17
- **Release:** v2.0 Foundation
- **Phase:** Infrastructure
- **Quarter:** Q1 2026
- **Effort (weeks):** 1.2

---

## Próximos Pasos

1. ✅ Issues creados
2. ⏭️ Configurar custom fields en GitHub Projects UI
3. ⏭️ Asignar issues a desarrolladores
4. ⏭️ Iniciar trabajo en DATA-102 (foundation tables primero)

---

**Última actualización:** $(date '+%Y-%m-%d %H:%M')"

# Agregar comentario al Epic
gh issue comment "$EPIC_NUMBER" --body "$COMMENT_BODY"

echo "✅ Epic #$EPIC_NUMBER actualizado con referencias a sub-issues"
echo ""
echo "📊 Ver Epic: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$EPIC_NUMBER"

