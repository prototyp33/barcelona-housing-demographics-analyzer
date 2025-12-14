#!/bin/bash
# Create Epic Issues with Complete Date Information

# Load dates
if [ -f ".roadmap_dates.env" ]; then
  source .roadmap_dates.env
else
  echo "❌ Error: .roadmap_dates.env not found"
  echo "Run: ./scripts/prepare_roadmap_dates.sh first"
  exit 1
fi

echo "🗺️ Creating Roadmap Epic Issues with Dates..."
echo ""

# ============================================
# v2.0 EPICS
# ============================================

# EPIC: PostgreSQL + Schema
gh issue create \
  --title "[EPIC] PostgreSQL Database & Schema v2.0" \
  --body "## 🎯 Goal
Setup PostgreSQL + PostGIS with complete schema v2.0

## 📅 Timeline
- **Start Date:** $DATA_001_START
- **Target Date:** $DATA_002_END
- **Duration:** 12 days
- **Release:** v2.0 (Jan 27, 2026)
- **Epic ID:** DATA-001 + DATA-002

## 📊 Success Metrics
- Database uptime: ≥99%
- Query performance: <500ms (p95)
- Schema deployed with all tables

## 🔗 User Stories
- [ ] #TBD: Setup PostgreSQL on Render/Supabase
- [ ] #TBD: Configure PostGIS extension
- [ ] #TBD: Implement dim_barrios table
- [ ] #TBD: Implement fact_precios table
- [ ] #TBD: Implement fact_demografia table
- [ ] #TBD: Add indexes & constraints

## 📈 Dependencies
- **Blocks:** ETL-001, ETL-002 (cannot load data without schema)

## 📝 Notes
- Use Render PostgreSQL (Starter plan \$7/mo) or Supabase free tier
- PostGIS required for geospatial queries (distance calculations)
- Schema based on Spike validation results" \
  --label "epic,database,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created: PostgreSQL & Schema"

# EPIC: ETL Pipeline
gh issue create \
  --title "[EPIC] ETL Pipeline - Price & Demographics Extractors" \
  --body "## 🎯 Goal
Build automated extractors for INE (prices) and Portal de Dades (demographics)

## 📅 Timeline
- **Start Date:** $ETL_001_START
- **Target Date:** $ETL_002_END
- **Duration:** 7 days
- **Release:** v2.0 (Jan 27, 2026)
- **Epic ID:** ETL-001 + ETL-002

## 📊 Success Metrics
- Data coverage: ≥20 barrios for v2.0
- Extraction success rate: ≥95%
- Automated daily refresh: implemented

## 🔗 User Stories
- [ ] #TBD: INE API integration
- [ ] #TBD: Portal de Dades CKAN integration
- [ ] #TBD: Data validation pipeline
- [ ] #TBD: Error handling & retry logic
- [ ] #TBD: Logging & monitoring

## 📈 Dependencies
- **Depends on:** PostgreSQL schema (DATA-001/002)
- **Blocks:** Analytics (AN-001)

## 📝 Notes
- Based on Spike validation (see issue #140-142)
- Use pandas for transformation
- Schedule: Daily refresh at 6 AM CET" \
  --label "epic,etl,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created: ETL Pipeline"

# EPIC: Hedonic Pricing Model
gh issue create \
  --title "[EPIC] Hedonic Pricing Model" \
  --body "## 🎯 Goal
Implement and deploy hedonic pricing model with R² ≥0.55

## 📅 Timeline
- **Start Date:** $AN_001_START
- **Target Date:** $AN_001_END
- **Duration:** 7 days
- **Release:** v2.0 (Jan 27, 2026)
- **Epic ID:** AN-001

## 📊 Success Metrics
- R² ajustado: ≥0.55
- Diagnostic tests: ≥4/5 passing
- Coefficient signs: economically plausible
- MAPE: <15%

## 🔗 User Stories
- [ ] #TBD: Feature engineering (log transforms, derived vars)
- [ ] #TBD: OLS model estimation with statsmodels
- [ ] #TBD: Diagnostic tests (5 tests)
- [ ] #TBD: Model serialization (pickle/joblib)
- [ ] #TBD: Prediction API (internal)
- [ ] #TBD: Documentation notebook

## 📈 Dependencies
- **Depends on:** ETL data available (ETL-001/002)
- **Blocks:** Dashboard price breakdown (VIZ-002)

## 📝 Notes
- Model specification from Spike (see issue #144-145)
- Variables: ln(precio) ~ ln(superficie) + antiguedad + plantas + ascensor + distance_center
- Target R²: 0.55-0.65 (validated in Spike)" \
  --label "epic,modeling,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created: Hedonic Model"

# EPIC: Dashboard MVP
gh issue create \
  --title "[EPIC] Streamlit Dashboard MVP" \
  --body "## 🎯 Goal
Launch Streamlit dashboard with Market Cockpit + Barrio Deep Dive pages

## 📅 Timeline
- **Start Date:** $VIZ_001_START
- **Target Date:** $VIZ_002_END
- **Duration:** 7 days
- **Release:** v2.0 (Jan 27, 2026)
- **Epic ID:** VIZ-001 + VIZ-002

## 📊 Success Metrics
- Pages live: 2 (Market Cockpit + Barrio Deep Dive)
- Load time: <5s
- Beta users: ≥10 successful logins
- Mobile compatible: Yes

## 🔗 User Stories
- [ ] #TBD: Streamlit app structure & navigation
- [ ] #TBD: PostgreSQL connection layer
- [ ] #TBD: Market Cockpit page (price evolution, KPIs)
- [ ] #TBD: Barrio Deep Dive page (demographics, comparisons)
- [ ] #TBD: Authentication (Streamlit Auth or custom)
- [ ] #TBD: Export functionality (CSV/Excel)

## 📈 Dependencies
- **Depends on:** Data in PostgreSQL (ETL-001/002)
- **Depends on:** Hedonic model (AN-001) for price breakdown

## 📝 Notes
- Framework: Streamlit (Python)
- Hosting: Render or Streamlit Cloud
- Authentication: Start with simple password, upgrade to OAuth in v2.2" \
  --label "epic,dashboard,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created: Dashboard MVP"

# EPIC: Deployment Infrastructure
gh issue create \
  --title "[EPIC] Deployment Infrastructure & CI/CD" \
  --body "## 🎯 Goal
Deploy dashboard to production with automated CI/CD pipeline

## 📅 Timeline
- **Start Date:** $INFRA_001_START
- **Target Date:** $INFRA_001_END
- **Duration:** 1 day
- **Release:** v2.0 (Jan 27, 2026)
- **Epic ID:** INFRA-001

## 📊 Success Metrics
- Uptime: ≥95%
- Deployment time: <5 minutes
- CI/CD: automated tests + deployment on merge to main

## 🔗 User Stories
- [ ] #TBD: Setup Render/Railway account & project
- [ ] #TBD: Configure environment variables
- [ ] #TBD: GitHub Actions workflow (test + deploy)
- [ ] #TBD: SSL certificate & custom domain
- [ ] #TBD: Monitoring (UptimeRobot + Sentry)

## 📈 Dependencies
- **Depends on:** Dashboard ready (VIZ-001/002)
- **Blocks:** Beta testing

## 📝 Notes
- Platform: Render (recommended) or Railway
- Cost: ~\$7-15/mo (Render Starter + PostgreSQL)
- Domain: barcelona-housing.app (to be purchased)" \
  --label "epic,infrastructure,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "  ✅ Created: Deployment"

# ============================================
# v2.1 EPICS
# ============================================

# EPIC: Diff-in-Diff Analysis
gh issue create \
  --title "[EPIC] Diff-in-Diff Regulatory Impact Analysis" \
  --body "## 🎯 Goal
Implement Diff-in-Diff analysis to estimate causal effect of Ley 12/2023

## 📅 Timeline
- **Start Date:** $AN_002_START
- **Target Date:** $AN_002_END
- **Duration:** 14 days
- **Release:** v2.1 (Feb 24, 2026)
- **Epic ID:** AN-002

## 📊 Success Metrics
- DiD model estimated
- Effect quantified (% change in rental contracts post-regulation)
- Parallel trends test: passed
- Visualization page live

## 🔗 User Stories
- [ ] #TBD: Define treatment group (Barcelona) vs control (AMB municipalities)
- [ ] #TBD: Test parallel trends assumption
- [ ] #TBD: Estimate DiD model with fixed effects
- [ ] #TBD: Robustness checks (placebo tests)
- [ ] #TBD: Create Regulatory Impact Analyzer page
- [ ] #TBD: Documentation of methodology

## 📈 Dependencies
- **Depends on:** v2.0 deployed (baseline data available)
- **Blocks:** None (feature addition)

## 📝 Notes
- Treatment: Barcelona (zona tensionada desde abril 2023)
- Control: Municipios AMB sin regulación
- Specification: Y_it = β0 + β1·Post + β2·Treated + β3·(Post×Treated) + ε
- Expected challenge: Spillover effects, finding clean control group" \
  --label "epic,modeling,v2.1,p0-critical" \
  --milestone "v2.1 Enhanced Analytics" && echo "  ✅ Created: Diff-in-Diff"

# ============================================
# v3.0 EPICS
# ============================================

# EPIC: Public API
gh issue create \
  --title "[EPIC] Public REST API" \
  --body "## 🎯 Goal
Launch public REST API with authentication and rate limiting

## 📅 Timeline
- **Start Date:** $API_001_START
- **Target Date:** $API_001_END
- **Duration:** 14 days
- **Release:** v3.0 (May 26, 2026)
- **Epic ID:** API-001

## 📊 Success Metrics
- Endpoints: ≥5 (barrios, precios, demographics, predictions, scoring)
- Rate limiting: 100 req/min per API key
- Documentation: OpenAPI/Swagger live
- First external users: ≥3 developers

## 🔗 User Stories
- [ ] #TBD: FastAPI project setup
- [ ] #TBD: JWT authentication implementation
- [ ] #TBD: Endpoints (GET /barrios, GET /precios, POST /predict, etc.)
- [ ] #TBD: Rate limiting (Redis-based)
- [ ] #TBD: OpenAPI documentation generation
- [ ] #TBD: Usage analytics (track API calls)
- [ ] #TBD: API key management dashboard

## 📈 Dependencies
- **Depends on:** v2.x features stable (models, data, etc.)
- **Blocks:** None (new capability)

## 📝 Notes
- Framework: FastAPI (Python)
- Authentication: JWT tokens
- Rate limiting: slowapi or Redis
- Hosting: Separate Render service (API-only)
- Cost: +\$7/mo for dedicated API service" \
  --label "epic,api,v3.0,p0-critical" \
  --milestone "v3.0 Public API + Scoring" && echo "  ✅ Created: Public API"

echo ""
echo "========================================="
echo "🎉 All Epic Issues Created with Dates!"
echo "========================================="
echo ""
echo "Epic Issues Created:"
echo "  - PostgreSQL & Schema ($DATA_001_START to $DATA_002_END)"
echo "  - ETL Pipeline ($ETL_001_START to $ETL_002_END)"
echo "  - Hedonic Model ($AN_001_START to $AN_001_END)"
echo "  - Dashboard MVP ($VIZ_001_START to $VIZ_002_END)"
echo "  - Deployment ($INFRA_001_START to $INFRA_001_END)"
echo "  - Diff-in-Diff ($AN_002_START to $AN_002_END)"
echo "  - Public API ($API_001_START to $API_001_END)"
echo ""
echo "Next Step: Configure these in GitHub Projects Roadmap View"

