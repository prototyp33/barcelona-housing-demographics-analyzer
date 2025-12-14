#!/bin/bash
# Create User Stories for v2.0 with Dates

if [ -f ".roadmap_dates.env" ]; then
  source .roadmap_dates.env
else
  echo "❌ Error: .roadmap_dates.env not found"
  exit 1
fi

echo "📝 Creating User Stories for v2.0..."
echo ""

# Get epic numbers (assuming they were just created or exist)
EPIC_DATA=$(gh issue list --label "epic,database,v2.0" --json number --jq '.[0].number' 2>/dev/null || echo "")
EPIC_ETL=$(gh issue list --label "epic,etl,v2.0" --json number --jq '.[0].number' 2>/dev/null || echo "")
EPIC_AN=$(gh issue list --label "epic,modeling,v2.0" --json number --jq '.[0].number' 2>/dev/null || echo "")
EPIC_VIZ=$(gh issue list --label "epic,dashboard,v2.0" --json number --jq '.[0].number' 2>/dev/null || echo "")

if [ -z "$EPIC_DATA" ] || [ -z "$EPIC_ETL" ] || [ -z "$EPIC_AN" ] || [ -z "$EPIC_VIZ" ]; then
  echo "⚠️ Warning: Some epics not found. Creating stories anyway..."
  echo "  EPIC_DATA: $EPIC_DATA"
  echo "  EPIC_ETL: $EPIC_ETL"
  echo "  EPIC_AN: $EPIC_AN"
  echo "  EPIC_VIZ: $EPIC_VIZ"
fi

# Calculate dates (macOS compatible)
calc_date() {
  local base_date=$1
  local days=$2
  if [[ "$OSTYPE" == "darwin"* ]]; then
    date -j -v+${days}d -f "%Y-%m-%d" "$base_date" +%Y-%m-%d 2>/dev/null || echo "$base_date"
  else
    date -d "$base_date + $days days" +%Y-%m-%d
  fi
}

# ============================================
# DATA Stories
# ============================================

# Story: Setup PostgreSQL
DATA_001_1_END=$(calc_date "$DATA_001_START" 3)
gh issue create \
  --title "[DATA-001.1] Setup PostgreSQL on Render" \
  --body "## 📋 User Story
As a developer, I need PostgreSQL database operational so that I can store housing data.

## 📅 Timeline
- **Start:** $DATA_001_START
- **Target:** $DATA_001_1_END
- **Duration:** 3 days
- **Epic:** #$EPIC_DATA

## ✅ Acceptance Criteria
- [ ] Render PostgreSQL instance created (Starter plan)
- [ ] PostGIS extension enabled
- [ ] Connection tested from local dev environment
- [ ] Environment variables configured (.env)
- [ ] Database accessible via psql CLI

## 🔗 Dependencies
- **Blocks:** DATA-001.2 (schema implementation)

## 📝 Implementation Notes
\`\`\`bash
# Render setup
render postgresql create barcelona-housing-db --plan starter

# Enable PostGIS
psql -h <host> -U <user> -d barcelona_housing -c \"CREATE EXTENSION postgis;\"
\`\`\`

## 🧪 Testing
- [ ] Run: \`psql -h <host> -U <user> -d barcelona_housing -c \"SELECT PostGIS_version();\"\`
- [ ] Expected: Version 3.x output" \
  --label "user-story,database,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created DATA-001.1: Setup PostgreSQL"

# Story: Implement Schema
gh issue create \
  --title "[DATA-002.1] Implement Database Schema v2.0" \
  --body "## 📋 User Story
As a data engineer, I need database schema implemented so that ETL can load data.

## 📅 Timeline
- **Start:** $DATA_001_1_END
- **Target:** $DATA_002_END
- **Duration:** 9 days
- **Epic:** #$EPIC_DATA

## ✅ Acceptance Criteria
- [ ] dim_barrios table created
- [ ] fact_precios table created
- [ ] fact_demografia table created
- [ ] fact_demografia_ampliada table created
- [ ] All foreign keys configured
- [ ] Indexes added (barrio_id, fecha)
- [ ] Schema migration script in \`migrations/\`

## 🔗 Dependencies
- **Depends on:** DATA-001.1 (PostgreSQL running)
- **Blocks:** ETL-001, ETL-002

## 📝 Implementation
See: \`src/database/schema_v2.sql\`

\`\`\`sql
-- Example
CREATE TABLE dim_barrios (
  barrio_id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  distrito VARCHAR(100),
  geometry GEOMETRY(POLYGON, 4326)
);
\`\`\`" \
  --label "user-story,database,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created DATA-002.1: Schema Implementation"

# ============================================
# ETL Stories
# ============================================

# Story: INE Extractor
ETL_001_1_END=$(calc_date "$ETL_001_START" 3)
gh issue create \
  --title "[ETL-001.1] Build INE Price Data Extractor" \
  --body "## 📋 User Story
As a data engineer, I need automated INE extractor so that price data is refreshed daily.

## 📅 Timeline
- **Start:** $ETL_001_START
- **Target:** $ETL_001_1_END
- **Duration:** 3 days
- **Epic:** #$EPIC_ETL

## ✅ Acceptance Criteria
- [ ] Script: \`src/extraction/extract_ine.py\`
- [ ] Extracts data for specified barrios
- [ ] Handles API errors gracefully
- [ ] Logs to \`logs/ine_extraction.log\`
- [ ] Saves to \`data/raw/ine_precios_{date}.csv\`
- [ ] Unit tests pass

## 🔗 Dependencies
- **Depends on:** DATA-002.1 (schema ready)
- **Blocks:** AN-001 (model needs data)

## 📝 Implementation
Based on Spike issue #140 research.

\`\`\`python
def extract_ine_data(barrios: List[str], start_date: str, end_date: str):
    # TODO: Implement
    pass
\`\`\`" \
  --label "user-story,etl,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created ETL-001.1: INE Extractor"

# Story: Portal de Dades Extractor
gh issue create \
  --title "[ETL-002.1] Build Portal de Dades Demographics Extractor" \
  --body "## 📋 User Story
As a data engineer, I need demographics extractor so that dashboard shows population data.

## 📅 Timeline
- **Start:** $ETL_002_START
- **Target:** $ETL_002_END
- **Duration:** 7 days (parallel with ETL-001)
- **Epic:** #$EPIC_ETL

## ✅ Acceptance Criteria
- [ ] Script: \`src/extraction/extract_portal_dades.py\`
- [ ] Integrates with CKAN API
- [ ] Extracts: population, age distribution, income
- [ ] Validates data quality (≥95% completeness)
- [ ] Loads to \`fact_demografia\` table

## 🔗 Dependencies
- **Depends on:** DATA-002.1 (schema ready)

## 📝 Implementation
Use CKAN API: \`https://opendata-ajuntament.barcelona.cat/data/api/3/\`" \
  --label "user-story,etl,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created ETL-002.1: Portal Dades Extractor"

# ============================================
# Analytics Stories
# ============================================

# Story: Hedonic Model Implementation
gh issue create \
  --title "[AN-001.1] Implement Hedonic Pricing Model" \
  --body "## 📋 User Story
As a data scientist, I need hedonic model implemented so that prices can be explained and predicted.

## 📅 Timeline
- **Start:** $AN_001_START
- **Target:** $AN_001_END
- **Duration:** 7 days
- **Epic:** #$EPIC_AN

## ✅ Acceptance Criteria
- [ ] Notebook: \`notebooks/02_hedonic_model.ipynb\`
- [ ] Model script: \`src/analysis/hedonic_model.py\`
- [ ] R² ajustado ≥0.55
- [ ] ≥4/5 diagnostic tests passing
- [ ] Model saved: \`models/hedonic_v1.pkl\`
- [ ] Prediction function available

## 🔗 Dependencies
- **Depends on:** ETL-001, ETL-002 (data loaded)
- **Blocks:** VIZ-002 (price breakdown viz)

## 📝 Implementation
Based on Spike issues #144-145.

\`\`\`python
# Model specification
ln(precio) = β0 + β1·ln(superficie) + β2·antiguedad + β3·plantas + β4·ascensor + ε
\`\`\`

## 🎯 Target Metrics (from Spike)
- R²: 0.55-0.65
- MAPE: <15%" \
  --label "user-story,modeling,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created AN-001.1: Hedonic Model"

# ============================================
# Dashboard Stories
# ============================================

# Story: Market Cockpit Page
VIZ_002_1_END=$(calc_date "$VIZ_002_START" 3)
gh issue create \
  --title "[VIZ-002.1] Build Market Cockpit Page" \
  --body "## 📋 User Story
As a user, I want to see overall market trends so that I understand Barcelona's housing market.

## 📅 Timeline
- **Start:** $VIZ_002_START
- **Target:** $VIZ_002_1_END
- **Duration:** 3 days
- **Epic:** #$EPIC_VIZ

## ✅ Acceptance Criteria
- [ ] Page: \`src/pages/01_Market_Cockpit.py\`
- [ ] KPI cards: Avg price, YoY change, Total listings
- [ ] Chart: Price evolution (line chart, last 5 years)
- [ ] Table: Top 10 movers (biggest % change)
- [ ] Barrio selector (dropdown)
- [ ] Loads in <5s

## 🔗 Dependencies
- **Depends on:** ETL data in PostgreSQL

## 📝 Design
- Use Plotly for charts
- Streamlit columns for KPIs
- Color scheme: Blue/Green (positive), Red (negative)" \
  --label "user-story,dashboard,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created VIZ-002.1: Market Cockpit"

# Story: Barrio Deep Dive Page
gh issue create \
  --title "[VIZ-003.1] Build Barrio Deep Dive Page" \
  --body "## 📋 User Story
As a user, I want detailed barrio analytics so that I can compare neighborhoods.

## 📅 Timeline
- **Start:** $VIZ_002_1_END
- **Target:** $VIZ_002_END
- **Duration:** 4 days
- **Epic:** #$EPIC_VIZ

## ✅ Acceptance Criteria
- [ ] Page: \`src/pages/02_Barrio_Deep_Dive.py\`
- [ ] Barrio selector (dropdown)
- [ ] Demographics section (population, age, income)
- [ ] Price breakdown (chart from hedonic model)
- [ ] Nearby barrios comparison (table)
- [ ] Download button (CSV export)

## 🔗 Dependencies
- **Depends on:** AN-001 (hedonic model for breakdown)

## 📝 Design
Show:
1. Demographics (charts)
2. Price decomposition: \"Your €350k breaks down to: Location (€120k), Size (€80k), etc.\"
3. Comparison with 3 nearest barrios" \
  --label "user-story,dashboard,v2.0,p1-high" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created VIZ-003.1: Barrio Deep Dive"

echo ""
echo "========================================="
echo "🎉 User Stories Created for v2.0!"
echo "========================================="
echo ""
echo "Total Stories: 6"
echo "  - DATA: 2 stories"
echo "  - ETL: 2 stories"
echo "  - AN: 1 story"
echo "  - VIZ: 2 stories"
echo ""
echo "Next: Add these to GitHub Project and set dates in Roadmap view"

