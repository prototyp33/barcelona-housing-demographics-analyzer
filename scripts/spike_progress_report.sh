#!/bin/bash
# SPIKE Progress Report Generator

echo "📊 SPIKE: Data Validation - Progress Report"
echo "Date: $(date '+%Y-%m-%d %H:%M')"
echo "==========================================="
echo ""

# Issues por estado
echo "## Issues by Status"
echo ""

TOTAL=$(gh issue list --milestone "Spike Completion" --json state | jq 'length')
OPEN=$(gh issue list --milestone "Spike Completion" --state open --json state | jq 'length')
CLOSED=$(gh issue list --milestone "Spike Completion" --state closed --json state | jq 'length')

echo "Total Issues: $TOTAL"
echo "Open: $OPEN"
echo "Closed: $CLOSED"
echo "Progress: $(echo "scale=1; $CLOSED * 100 / $TOTAL" | bc)%"
echo ""

# Issues bloqueados
echo "## Blocked Issues"
BLOCKED=$(gh issue list --milestone "Spike Completion" --label "blocked" --json number,title)
if [ "$BLOCKED" == "[]" ]; then
  echo "✅ No blocked issues"
else
  echo "$BLOCKED" | jq -r '.[] | "❌ #\(.number): \(.title)"'
fi
echo ""

# Issues en progreso
echo "## In Progress"
gh issue list --milestone "Spike Completion" --state open --json number,title,assignees | \
  jq -r '.[] | select(.assignees | length > 0) | "🔄 #\(.number): \(.title) (@\(.assignees[0].login))"'

echo ""

# Próximos issues (sin asignar)
echo "## Next Up (Unassigned)"
gh issue list --milestone "Spike Completion" --state open --json number,title,assignees | \
  jq -r '.[] | select(.assignees | length == 0) | "📋 #\(.number): \(.title)"'

echo ""

# Time to deadline
DEADLINE="2025-12-20"
# macOS compatible date calculation
if [[ "$OSTYPE" == "darwin"* ]]; then
  DEADLINE_EPOCH=$(date -j -f "%Y-%m-%d" "$DEADLINE" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$DEADLINE 00:00:00" +%s)
  CURRENT_EPOCH=$(date +%s)
else
  DEADLINE_EPOCH=$(date -d "$DEADLINE" +%s)
  CURRENT_EPOCH=$(date +%s)
fi
DAYS_LEFT=$(( (DEADLINE_EPOCH - CURRENT_EPOCH) / 86400 ))

echo "## Timeline"
echo "Deadline: $DEADLINE"
echo "Days remaining: $DAYS_LEFT"

if [ $DAYS_LEFT -lt 2 ]; then
  echo "⚠️ URGENT: Less than 2 days remaining!"
fi

echo ""
echo "==========================================="
echo "Run daily standup: gh issue comment 149 --body \"[Your update]\""

