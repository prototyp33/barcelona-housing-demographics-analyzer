#!/bin/bash
export GITHUB_TOKEN=""

echo "Setting up Issues for Sprint 2026-01 (Milestone 33)..."

# Issues to update
ISSUES_TO_UPDATE=(13 52 58 55)
MILESTONE="Sprint 2026-01 (Phase 2: Fairness)"

for id in "${ISSUES_TO_UPDATE[@]}"; do
  echo "Updating issue #$id..."
  gh issue edit "$id" --milestone "$MILESTONE" --add-assignee prototyp33 || echo "Failed to update issue #$id"
done

# Issues to create
echo "Creating new Feature issues..."

gh issue create \
  --title "Feature: TMB/OSM stops ingestion (GTFS/Overpass)" \
  --body "Ingest public transport stops (Metro, Bus, Tram) from GTFS (TMB) or OSM Overpass API. Required for accessibility analysis.

Acceptance Criteria:
- Script to fetch data from TMB Open Data or OSM.
- Raw data stored in data/raw.
- Basic validation check." \
  --label "domain:etl" \
  --label "priority-high" \
  --label "type-feature" \
  --milestone "$MILESTONE" \
  --assignee prototyp33

gh issue create \
  --title "Feature: Accessibility feature engineering + load to SQLite" \
  --body "Calculate distance to nearest transport stops per barrio and other accessibility metrics. Update SQLite schema if necessary and load data.

Acceptance Criteria:
- Transformation script for accessibility features.
- New table or columns in SQLite.
- Integration tests for loading." \
  --label "domain:data-processing" \
  --label "priority-high" \
  --label "type-feature" \
  --milestone "$MILESTONE" \
  --assignee prototyp33

gh issue create \
  --title "Feature: Fairness A/B harness (v1 vs v2) + report artifact" \
  --body "Develop a harness to compare Model v1 vs Model v2 across different socioeconomic groups (Fairness analysis). Generate a summary report/artifact.

Acceptance Criteria:
- Comparison script (harness).
- Fairness metrics calculated (e.g., parity gap).
- Automated generation of a report artifact." \
  --label "domain:data-quality" \
  --label "priority-medium" \
  --label "type-feature" \
  --milestone "$MILESTONE" \
  --assignee prototyp33

echo "Sprint setup complete."
