#!/bin/bash
# Create Epic Issues for Roadmap

echo "🗺️ Creating Roadmap Epic Issues..."
echo ""

# EPIC: PostgreSQL + Schema (v2.0)
gh issue create \
  --title "[EPIC] PostgreSQL Database & Schema v2.0" \
  --body "## 🎯 Goal
Setup PostgreSQL + PostGIS with complete schema v2.0

## 📊 Success Metrics
- Database uptime: ≥99%
- Query performance: <500ms (p95)
- Schema deployed with all tables

## 🔗 Stories
- [ ] Setup PostgreSQL on Render/Supabase
- [ ] Configure PostGIS extension
- [ ] Implement dim_barrios table
- [ ] Implement fact_precios table
- [ ] Implement fact_demografia table
- [ ] Add indexes & constraints

## 📅 Timeline
**Release:** v2.0 (Jan 27, 2026)
**Effort:** 2 weeks" \
  --label "epic,database,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "✅ Created: PostgreSQL Database & Schema"

# EPIC: Hedonic Model (v2.0)
gh issue create \
  --title "[EPIC] Hedonic Pricing Model" \
  --body "## 🎯 Goal
Implement hedonic pricing model with R² ≥0.55

## 📊 Success Metrics
- R² ajustado: ≥0.55
- Diagnostics: ≥4/5 tests passing
- MAPE: <15%

## 🔗 Stories
- [ ] Feature engineering
- [ ] OLS estimation
- [ ] Diagnostic tests
- [ ] Model serialization
- [ ] Documentation notebook

## 📅 Timeline
**Release:** v2.0 (Jan 27, 2026)
**Effort:** 2 weeks" \
  --label "epic,modeling,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "✅ Created: Hedonic Pricing Model"

# EPIC: Dashboard MVP (v2.0)
gh issue create \
  --title "[EPIC] Streamlit Dashboard MVP" \
  --body "## 🎯 Goal
Launch dashboard with Market Cockpit + Barrio Deep Dive pages

## 📊 Success Metrics
- Pages live: 2
- Load time: <5s
- Beta users: 10+

## 🔗 Stories
- [ ] Streamlit app structure
- [ ] Market Cockpit page
- [ ] Barrio Deep Dive page
- [ ] Authentication
- [ ] Deployment

## 📅 Timeline
**Release:** v2.0 (Jan 27, 2026)
**Effort:** 2 weeks" \
  --label "epic,dashboard,v2.0,p0-critical" \
  --milestone "v2.0 Foundation" && echo "✅ Created: Streamlit Dashboard MVP"

# EPIC: Diff-in-Diff Analysis (v2.1)
gh issue create \
  --title "[EPIC] Diff-in-Diff Regulatory Impact Analysis" \
  --body "## 🎯 Goal
Implement Diff-in-Diff to estimate effect of Ley 12/2023

## 📊 Success Metrics
- Model estimated
- Effect quantified (% change in contracts)
- Visualization page live

## 🔗 Stories
- [ ] Define treatment/control groups
- [ ] Test parallel trends assumption
- [ ] Estimate DiD model
- [ ] Create Regulatory Impact page
- [ ] Document methodology

## 📅 Timeline
**Release:** v2.1 (Feb 24, 2026)
**Effort:** 2 weeks" \
  --label "epic,modeling,v2.1,p0-critical" \
  --milestone "v2.1 Enhanced Analytics" && echo "✅ Created: Diff-in-Diff Analysis"

# EPIC: Public API (v3.0)
gh issue create \
  --title "[EPIC] Public REST API" \
  --body "## 🎯 Goal
Launch public REST API with authentication

## 📊 Success Metrics
- Endpoints: ≥5 (barrios, precios, demographics, model predictions)
- Rate limiting: 100 req/min
- Documentation: OpenAPI/Swagger

## 🔗 Stories
- [ ] FastAPI setup
- [ ] JWT authentication
- [ ] Endpoints implementation
- [ ] Rate limiting
- [ ] API documentation
- [ ] Usage monitoring

## 📅 Timeline
**Release:** v3.0 (May 26, 2026)
**Effort:** 2 weeks" \
  --label "epic,api,v3.0,p0-critical" \
  --milestone "v3.0 Public API + Scoring" && echo "✅ Created: Public REST API"

echo ""
echo "✅ Roadmap epic issues created!"
echo ""
echo "View epics: gh issue list --label epic"

