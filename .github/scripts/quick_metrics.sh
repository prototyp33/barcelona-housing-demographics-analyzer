#!/bin/bash
echo "📊 BARCELONA HOUSING ANALYZER - QUICK METRICS"
echo "=============================================="
echo ""
echo "📅 Date: $(date '+%Y-%m-%d %H:%M CET')"
echo ""
echo "🎯 SPIKE ISSUES (Dec 16-20)"
gh issue list --label spike --state all --json number,title,state,labels | \
  jq -r '.[] | "  #\(.number) [\(.state)] \(.title)"'
echo ""
echo "🔥 CRITICAL OPEN ISSUES"
gh issue list --label p0-critical --state open --limit 10 --json number,title,assignees | \
  jq -r '.[] | "  #\(.number) \(.title) [Owner: \(.assignees[0].login // "UNASSIGNED")]"'
echo ""
echo "📊 ISSUE BREAKDOWN BY STATUS"
echo "  Backlog: $(gh issue list --state open | grep -c 'backlog' || echo 0)"
echo "  In Progress: $(gh issue list --state open | grep -c 'in-progress' || echo 0)"
echo "  In Review: $(gh issue list --state open | grep -c 'in-review' || echo 0)"
echo ""
echo "⚠️ NEEDS ATTENTION"
echo "  Needs Refinement: $(gh issue list --label needs-refinement --state open | wc -l)"
echo "  Blocked: $(gh issue list --label blocked --state open | wc -l)"
echo "  No Labels: $(gh issue list --state open --json labels | jq '[.[] | select(.labels | length == 0)] | length')"
