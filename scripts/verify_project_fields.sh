#!/bin/bash
# Verify GitHub Projects Custom Fields Configuration
# Verifica que todos los issues tengan los campos requeridos

set -e

echo "🔍 Verifying GitHub Projects Custom Fields"
echo ""

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Campos requeridos para epics
REQUIRED_FIELDS=(
    "Start Date"
    "Target Date"
    "Epic"
    "Release"
    "Phase"
    "Priority"
    "Effort (weeks)"
)

echo "## Checking Epic Issues"
echo ""

EPIC_ISSUES=$(gh issue list --label epic --json number,title,body --jq '.[] | .number')

for issue_num in $EPIC_ISSUES; do
    echo "📋 Issue #$issue_num"
    
    body=$(gh issue view "$issue_num" --json body --jq '.body')
    
    missing_fields=()
    
    for field in "${REQUIRED_FIELDS[@]}"; do
        # Buscar campo en body (case insensitive)
        if ! echo "$body" | grep -qi "\*\*${field}:\*\*\|${field}:"; then
            missing_fields+=("$field")
        fi
    done
    
    if [ ${#missing_fields[@]} -eq 0 ]; then
        echo "   ✅ All required fields present"
    else
        echo "   ⚠️  Missing fields: ${missing_fields[*]}"
    fi
    
    echo ""
done

echo "## Summary"
echo ""

TOTAL=$(echo "$EPIC_ISSUES" | wc -l | tr -d ' ')
echo "Total Epic Issues: $TOTAL"
echo ""
echo "✅ Verification complete!"
echo ""
echo "To populate missing fields, run:"
echo "  ./scripts/populate_project_fields.sh"

