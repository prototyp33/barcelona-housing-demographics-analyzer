#!/bin/bash
echo "🔍 ROADMAP SETUP VERIFICATION"
echo "=============================="
echo ""

# Check epic issues
EPICS=$(gh issue list --label epic --json number 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
echo "Epic Issues: $EPICS"

# Check user stories
STORIES=$(gh issue list --label user-story --json number 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
echo "User Stories: $STORIES"

# Check milestones
MILESTONES=$(gh milestone list --json title 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
echo "Milestones: $MILESTONES"

# Check date configuration file
if [ -f ".roadmap_dates.env" ]; then
  echo "✅ Date configuration file exists"
else
  echo "❌ Missing .roadmap_dates.env"
fi

echo ""
echo "Manual Steps Remaining:"
echo "  1. Go to GitHub → Projects → Create 'Barcelona Housing - Product Roadmap'"
echo "  2. Add all epic + user-story issues to project"
echo "  3. For each issue, set Start Date and Target Date fields"
echo "  4. Configure Roadmap view (Group by: Release, Sort by: Start date)"
echo ""
echo "Estimated time: 15-20 minutes"

