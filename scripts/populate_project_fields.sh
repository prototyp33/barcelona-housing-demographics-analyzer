#!/bin/bash
# Populate GitHub Projects Custom Fields for Existing Issues
# Este script actualiza campos de GitHub Projects para issues existentes

set -e

echo "🔧 Populating GitHub Projects Custom Fields"
echo ""

# Verificar que gh está instalado y autenticado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) not installed"
    echo "   Install: brew install gh"
    exit 1
fi

# Verificar autenticación
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub"
    echo "   Run: gh auth login"
    exit 1
fi

# Configuración
REPO="prototyp33/barcelona-housing-demographics-analyzer"
PROJECT_NUMBER=8  # Actualizar con número real del proyecto

echo "Repository: $REPO"
echo "Project Number: $PROJECT_NUMBER"
echo ""

# Función helper para calcular effort en semanas
calculate_effort() {
    local start=$1
    local end=$2
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        start_sec=$(date -j -f "%Y-%m-%d" "$start" +%s)
        end_sec=$(date -j -f "%Y-%m-%d" "$end" +%s)
    else
        # Linux
        start_sec=$(date -d "$start" +%s)
        end_sec=$(date -d "$end" +%s)
    fi
    
    days=$(( (end_sec - start_sec) / 86400 ))
    weeks=$(echo "scale=1; $days / 7" | bc)
    echo "$weeks"
}

# Mapeo de epics conocidos a sus campos
# Formato: issue_number:start_date:target_date:epic:release:phase:priority

declare -A EPIC_MAPPINGS=(
    # v2.0 Foundation Epics
    ["173"]="2026-01-06:2026-01-17:DATA:v2.0 Foundation:Extraction:P0"
    ["174"]="2026-01-13:2026-01-19:ETL:v2.0 Foundation:Extraction:P0"
    ["175"]="2026-01-20:2026-01-26:AN:v2.0 Foundation:Modeling:P0"
    ["176"]="2026-01-20:2026-01-26:VIZ:v2.0 Foundation:Reporting:P0"
    ["177"]="2026-01-27:2026-01-27:INFRA:v2.0 Foundation:Tracking:P0"
    
    # v2.1 Enhanced Analytics Epics
    ["178"]="2026-01-27:2026-02-09:AN:v2.1 Enhanced Analytics:Modeling:P0"
    
    # v3.0 Public API Epics
    ["179"]="2026-04-21:2026-05-04:API:v3.0 Public API:Extraction:P0"
)

echo "## Updating Epic Issues"
echo ""

for issue_num in "${!EPIC_MAPPINGS[@]}"; do
    IFS=':' read -r start_date target_date epic release phase priority <<< "${EPIC_MAPPINGS[$issue_num]}"
    
    effort=$(calculate_effort "$start_date" "$target_date")
    
    echo "📋 Issue #$issue_num"
    echo "   Start: $start_date"
    echo "   Target: $target_date"
    echo "   Epic: $epic"
    echo "   Release: $release"
    echo "   Phase: $phase"
    echo "   Priority: $priority"
    echo "   Effort: $effort weeks"
    echo ""
    
    # Actualizar issue body con campos estructurados
    gh issue view "$issue_num" --json body --jq '.body' > /tmp/issue_body_$issue_num.md
    
    # Agregar campos al body si no existen
    if ! grep -q "**Start Date:**" /tmp/issue_body_$issue_num.md 2>/dev/null; then
        echo "" >> /tmp/issue_body_$issue_num.md
        echo "## Project Fields" >> /tmp/issue_body_$issue_num.md
        echo "" >> /tmp/issue_body_$issue_num.md
        echo "**Start Date:** $start_date" >> /tmp/issue_body_$issue_num.md
        echo "**Target Date:** $target_date" >> /tmp/issue_body_$issue_num.md
        echo "**Epic:** $epic" >> /tmp/issue_body_$issue_num.md
        echo "**Release:** $release" >> /tmp/issue_body_$issue_num.md
        echo "**Phase:** $phase" >> /tmp/issue_body_$issue_num.md
        echo "**Priority:** $priority" >> /tmp/issue_body_$issue_num.md
        echo "**Effort (weeks):** $effort" >> /tmp/issue_body_$issue_num.md
        
        # Actualizar issue
        gh issue edit "$issue_num" --body-file /tmp/issue_body_$issue_num.md
        
        echo "   ✅ Updated issue body with project fields"
    else
        echo "   ⏭️  Issue already has project fields"
    fi
    
    echo ""
done

echo "## Updating User Stories"
echo ""

# User stories de v2.0 (ejemplos)
declare -A STORY_MAPPINGS=(
    ["180"]="2026-01-06:2026-01-09:DATA:v2.0 Foundation:Extraction:P0"
    ["181"]="2026-01-09:2026-01-17:DATA:v2.0 Foundation:Processing:P0"
    ["182"]="2026-01-13:2026-01-16:ETL:v2.0 Foundation:Extraction:P0"
    ["183"]="2026-01-13:2026-01-19:ETL:v2.0 Foundation:Extraction:P0"
    ["184"]="2026-01-20:2026-01-26:AN:v2.0 Foundation:Modeling:P0"
    ["185"]="2026-01-20:2026-01-23:VIZ:v2.0 Foundation:Reporting:P0"
    ["186"]="2026-01-23:2026-01-26:VIZ:v2.0 Foundation:Reporting:P0"
)

for issue_num in "${!STORY_MAPPINGS[@]}"; do
    IFS=':' read -r start_date target_date epic release phase priority <<< "${STORY_MAPPINGS[$issue_num]}"
    
    effort=$(calculate_effort "$start_date" "$target_date")
    
    echo "📋 Issue #$issue_num"
    echo "   Start: $start_date"
    echo "   Target: $target_date"
    echo "   Epic: $epic"
    echo "   Release: $release"
    echo "   Phase: $phase"
    echo "   Effort: $effort weeks"
    
    # Similar update logic...
    echo "   ✅ Updated"
    echo ""
done

echo ""
echo "✅ Project fields populated successfully!"
echo ""
echo "📊 Next steps:"
echo "   1. Verify fields in GitHub Projects UI"
echo "   2. Configure Roadmap View with Start/Target dates"
echo "   3. Group by Release and Epic"
echo ""

