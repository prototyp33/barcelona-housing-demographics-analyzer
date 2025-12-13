#!/bin/bash
# Populate GitHub Projects Custom Fields - Auto-detect Issues
# Este script detecta issues existentes y popula campos automáticamente

set -e

echo "🔧 Populating GitHub Projects Custom Fields (Auto-detect)"
echo ""

# Verificar que gh está instalado y autenticado
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) not installed"
    exit 1
fi

# Configuración
REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Función helper para calcular effort en semanas
calculate_effort() {
    local start=$1
    local end=$2
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        start_sec=$(date -j -f "%Y-%m-%d" "$start" +%s 2>/dev/null || echo "0")
        end_sec=$(date -j -f "%Y-%m-%d" "$end" +%s 2>/dev/null || echo "0")
    else
        start_sec=$(date -d "$start" +%s 2>/dev/null || echo "0")
        end_sec=$(date -d "$end" +%s 2>/dev/null || echo "0")
    fi
    
    if [ "$start_sec" = "0" ] || [ "$end_sec" = "0" ]; then
        echo "0"
        return
    fi
    
    days=$(( (end_sec - start_sec) / 86400 ))
    if command -v bc &> /dev/null; then
        weeks=$(echo "scale=1; $days / 7" | bc)
        echo "$weeks"
    else
        # Fallback sin bc
        weeks=$(( days * 10 / 7 ))
        echo "${weeks:0:1}.${weeks:1:1}"
    fi
}

# Función para extraer información de issue title
detect_epic_from_title() {
    local title=$1
    
    if echo "$title" | grep -qi "PostgreSQL\|Database\|Schema"; then
        echo "DATA"
    elif echo "$title" | grep -qi "ETL\|Extractor\|Pipeline"; then
        echo "ETL"
    elif echo "$title" | grep -qi "Hedonic\|Model\|Analytics\|DiD"; then
        echo "AN"
    elif echo "$title" | grep -qi "Dashboard\|Streamlit\|Visualization"; then
        echo "VIZ"
    elif echo "$title" | grep -qi "API\|REST\|FastAPI"; then
        echo "API"
    elif echo "$title" | grep -qi "Deploy\|Infrastructure\|CI/CD"; then
        echo "INFRA"
    elif echo "$title" | grep -qi "UX\|Design\|User Experience"; then
        echo "UX"
    elif echo "$title" | grep -qi "Performance\|Optimization\|Cache"; then
        echo "PERF"
    elif echo "$title" | grep -qi "Documentation\|Docs\|Guide"; then
        echo "DOCS"
    else
        echo "DATA"  # Default
    fi
}

# Función para detectar release desde milestone
detect_release_from_milestone() {
    local milestone=$1
    
    case "$milestone" in
        *"v2.0"*|*"Foundation"*)
            echo "v2.0 Foundation"
            ;;
        *"v2.1"*|*"Enhanced Analytics"*)
            echo "v2.1 Enhanced Analytics"
            ;;
        *"v2.2"*|*"Polish"*)
            echo "v2.2 Dashboard Polish"
            ;;
        *"v2.3"*|*"Coverage"*)
            echo "v2.3 Complete Coverage"
            ;;
        *"v3.0"*|*"API"*)
            echo "v3.0 Public API"
            ;;
        *)
            echo "Backlog"
            ;;
    esac
}

# Función para detectar phase desde title/labels
detect_phase_from_issue() {
    local title=$1
    local labels=$2
    
    if echo "$title $labels" | grep -qi "Extract\|Extractor\|Data source"; then
        echo "Extraction"
    elif echo "$title $labels" | grep -qi "Clean\|Process\|Transform\|Linking"; then
        echo "Processing"
    elif echo "$title $labels" | grep -qi "Model\|Analysis\|Hedonic\|DiD"; then
        echo "Modeling"
    elif echo "$title $labels" | grep -qi "Report\|Dashboard\|Visualization"; then
        echo "Reporting"
    elif echo "$title $labels" | grep -qi "Monitor\|Track\|Update\|Maintain"; then
        echo "Tracking"
    else
        echo "Extraction"  # Default
    fi
}

# Función para obtener fechas por release
get_dates_for_release() {
    local release=$1
    
    case "$release" in
        "v2.0 Foundation")
            echo "2026-01-06:2026-01-27"
            ;;
        "v2.1 Enhanced Analytics")
            echo "2026-01-27:2026-02-24"
            ;;
        "v2.2 Dashboard Polish")
            echo "2026-02-24:2026-03-24"
            ;;
        "v2.3 Complete Coverage")
            echo "2026-03-24:2026-04-21"
            ;;
        "v3.0 Public API")
            echo "2026-04-21:2026-05-26"
            ;;
        *)
            echo "2026-01-06:2026-01-27"  # Default
            ;;
    esac
}

echo "## Detecting Epic Issues"
echo ""

# Obtener todos los epics
EPICS=$(gh issue list --label epic --json number,title,milestone,labels --jq '.[] | "\(.number)|\(.title)|\(.milestone.title // "None")|\(.labels | map(.name) | join(","))"')

if [ -z "$EPICS" ]; then
    echo "⚠️  No epic issues found"
    echo ""
else
    echo "Found $(echo "$EPICS" | wc -l | tr -d ' ') epic issues"
    echo ""
    
    while IFS='|' read -r issue_num title milestone labels; do
        echo "📋 Issue #$issue_num: $title"
        
        # Detectar campos
        epic=$(detect_epic_from_title "$title")
        release=$(detect_release_from_milestone "$milestone")
        
        # Obtener fechas del mapeo
        date_range=$(get_dates_for_release "$release")
        IFS=':' read -r start_date target_date <<< "$date_range"
        
        phase=$(detect_phase_from_issue "$title" "$labels")
        priority="P0"  # Default para epics
        
        effort=$(calculate_effort "$start_date" "$target_date")
        
        echo "   Start: $start_date"
        echo "   Target: $target_date"
        echo "   Epic: $epic"
        echo "   Release: $release"
        echo "   Phase: $phase"
        echo "   Effort: $effort weeks"
        echo ""
        
        # Obtener body actual
        body=$(gh issue view "$issue_num" --json body --jq -r '.body' 2>/dev/null || echo "")
        
        # Verificar si ya tiene campos
        if echo "$body" | grep -q "\*\*Start Date:\*\*"; then
            echo "   ⏭️  Issue already has project fields"
            echo ""
            continue
        fi
        
        # Agregar campos al body
        {
            echo ""
            echo "## Project Fields"
            echo ""
            echo "**Start Date:** $start_date"
            echo "**Target Date:** $target_date"
            echo "**Epic:** $epic"
            echo "**Release:** $release"
            echo "**Quarter:** Q1 2026"
            echo "**Phase:** $phase"
            echo "**Priority:** $priority"
            echo "**Effort (weeks):** $effort"
        } > /tmp/fields_$issue_num.txt
        
        # Combinar body existente con nuevos campos
        if [ -n "$body" ]; then
            echo "$body" > /tmp/issue_body_$issue_num.md
            cat /tmp/fields_$issue_num.txt >> /tmp/issue_body_$issue_num.md
        else
            cat /tmp/fields_$issue_num.txt > /tmp/issue_body_$issue_num.md
        fi
        
        # Actualizar issue
        if gh issue edit "$issue_num" --body-file /tmp/issue_body_$issue_num.md 2>/dev/null; then
            echo "   ✅ Updated issue body with project fields"
        else
            echo "   ⚠️  Failed to update issue (may need authentication)"
        fi
        
        echo ""
        
    done <<< "$EPICS"
fi

echo "## Summary"
echo ""
echo "✅ Project fields population complete!"
echo ""
echo "📊 Next steps:"
echo "   1. Verify fields in GitHub Projects UI"
echo "   2. Manually update any missing dates if needed"
echo "   3. Configure Roadmap View"
echo ""

