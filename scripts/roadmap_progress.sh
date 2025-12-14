#!/bin/bash
# Roadmap Progress Report

echo "📊 ROADMAP PROGRESS REPORT"
echo "Date: $(date '+%Y-%m-%d')"
echo "========================================="
echo ""

# Progress by milestone
for milestone in "v2.0 Foundation" "v2.1 Enhanced Analytics" "v2.2 Dashboard Polish" "v2.3 Complete Coverage" "v3.0 Public API + Scoring"; do
  echo "## $milestone"
  
  TOTAL=$(gh issue list --milestone "$milestone" --json number 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
  CLOSED=$(gh issue list --milestone "$milestone" --state closed --json number 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
  
  if [ "$TOTAL" -gt 0 ] 2>/dev/null; then
    PROGRESS=$(echo "scale=1; $CLOSED * 100 / $TOTAL" | bc 2>/dev/null || echo "0")
    echo "  Progress: $CLOSED/$TOTAL ($PROGRESS%)"
  else
    echo "  Progress: No issues yet"
  fi
  
  # Epics in milestone
  EPICS=$(gh issue list --milestone "$milestone" --label epic --json number,title,state 2>/dev/null | jq -r '.[] | "#\(.number): \(.title) (\(.state))"' 2>/dev/null)
  if [ -n "$EPICS" ]; then
    echo "  Epics:"
    echo "$EPICS" | sed 's/^/    /'
  fi
  
  echo ""
done

# Overall roadmap health
echo "## Overall Roadmap Health"
echo ""

# Days to next release
NEXT_RELEASE=$(gh milestone list --json title,dueOn 2>/dev/null | jq -r 'sort_by(.dueOn) | .[] | select(.dueOn != null) | .dueOn' 2>/dev/null | head -1)
if [ -n "$NEXT_RELEASE" ] && [ "$NEXT_RELEASE" != "null" ]; then
  # macOS compatible date calculation
  if [[ "$OSTYPE" == "darwin"* ]]; then
    NEXT_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$NEXT_RELEASE" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "${NEXT_RELEASE%%T*}" +%s 2>/dev/null)
    CURRENT_EPOCH=$(date +%s)
  else
    NEXT_EPOCH=$(date -d "$NEXT_RELEASE" +%s 2>/dev/null)
    CURRENT_EPOCH=$(date +%s)
  fi
  
  if [ -n "$NEXT_EPOCH" ] && [ -n "$CURRENT_EPOCH" ]; then
    DAYS_LEFT=$(( (NEXT_EPOCH - CURRENT_EPOCH) / 86400 ))
    echo "Next Release: ${NEXT_RELEASE%%T*} ($DAYS_LEFT days)"
  fi
fi

# At-risk items
AT_RISK=$(gh issue list --label blocked --json number,title,milestone 2>/dev/null | jq -r '.[] | "#\(.number): \(.title) (Milestone: \(.milestone.title // "None"))"' 2>/dev/null)
if [ -n "$AT_RISK" ]; then
  echo ""
  echo "⚠️ At-Risk Items:"
  echo "$AT_RISK" | sed 's/^/  /'
else
  echo ""
  echo "✅ No blocked items"
fi

echo ""
echo "========================================="

