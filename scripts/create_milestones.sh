#!/bin/bash
# Create Release Milestones for Roadmap

echo "📅 Creating Release Milestones..."
echo ""

# Milestone: v2.0 Foundation
gh api repos/prototyp33/barcelona-housing-demographics-analyzer/milestones -X POST \
  -f title="v2.0 Foundation" \
  -f description="PostgreSQL + Hedonic Model + Dashboard MVP" \
  -f due_on="2026-01-27T23:59:59Z" && echo "✅ Created: v2.0 Foundation"

# Milestone: v2.1 Enhanced Analytics
gh api repos/prototyp33/barcelona-housing-demographics-analyzer/milestones -X POST \
  -f title="v2.1 Enhanced Analytics" \
  -f description="Diff-in-Diff + Regulatory Impact + 40 barrios" \
  -f due_on="2026-02-24T23:59:59Z" && echo "✅ Created: v2.1 Enhanced Analytics"

# Milestone: v2.2 Dashboard Polish
gh api repos/prototyp33/barcelona-housing-demographics-analyzer/milestones -X POST \
  -f title="v2.2 Dashboard Polish" \
  -f description="UX redesign + Performance + Testing" \
  -f due_on="2026-03-24T23:59:59Z" && echo "✅ Created: v2.2 Dashboard Polish"

# Milestone: v2.3 Complete Coverage
gh api repos/prototyp33/barcelona-housing-demographics-analyzer/milestones -X POST \
  -f title="v2.3 Complete Coverage" \
  -f description="All 73 barrios + Data quality monitoring" \
  -f due_on="2026-04-21T23:59:59Z" && echo "✅ Created: v2.3 Complete Coverage"

# Milestone: v3.0 Public API
gh api repos/prototyp33/barcelona-housing-demographics-analyzer/milestones -X POST \
  -f title="v3.0 Public API + Scoring" \
  -f description="REST API + Investment opportunity scoring" \
  -f due_on="2026-05-26T23:59:59Z" && echo "✅ Created: v3.0 Public API + Scoring"

echo ""
echo "✅ All milestones created successfully!"
echo ""
echo "View milestones: gh milestone list"

