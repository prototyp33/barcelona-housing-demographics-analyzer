#!/bin/bash
# Open all Spike milestone issues in browser for easy subscription

echo "🔔 Opening Spike issues in browser for subscription..."
echo ""

gh issue list --milestone "Spike Completion" --json number,url,title | \
  jq -r '.[] | "Opening #\(.number): \(.title)\n\(.url)"' | \
  while IFS= read -r line; do
    if [[ $line == http* ]]; then
      echo "  → $line"
      if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$line"
      elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$line"
      fi
      sleep 1  # Small delay between opens
    else
      echo "$line"
    fi
  done

echo ""
echo "✅ All issues opened. Click 'Subscribe' on each issue to receive notifications."
echo ""
echo "Or subscribe to the milestone directly:"
echo "https://github.com/prototyp33/barcelona-housing-demographics-analyzer/milestone/21"

