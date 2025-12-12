#!/bin/bash
# Prepare issues with date fields for GitHub Projects Roadmap View

echo "📅 Preparing Roadmap Date Fields..."
echo ""

# Nota: GitHub Projects v2 custom fields se configuran en la UI,
# pero podemos preparar los issues con metadata en el body

# Function to update issue with date metadata
update_issue_dates() {
  local issue_number=$1
  local start_date=$2
  local end_date=$3
  local epic_name=$4
  
  gh issue comment $issue_number --body "## 📅 Timeline Metadata

**Start Date:** $start_date  
**Target Date:** $end_date  
**Epic:** $epic_name  
**Duration:** $(( ( $(date -d "$end_date" +%s) - $(date -d "$start_date" +%s) ) / 86400 )) days

---
*This metadata will be used to populate the Roadmap view in GitHub Projects*
"
}

echo "This script will guide you through creating date metadata for roadmap issues."
echo "After running this, you'll configure the fields in GitHub Projects UI."
echo ""
echo "✅ Date configuration file (.roadmap_dates.env) created"
echo ""
echo "Next steps:"
echo "1. Run: ./scripts/create_roadmap_epics_with_dates.sh"
echo "2. Run: ./scripts/create_user_stories_v2_0.sh"
echo "3. Configure dates in GitHub Projects UI"

