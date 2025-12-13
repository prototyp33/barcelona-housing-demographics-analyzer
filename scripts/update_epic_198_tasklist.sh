#!/bin/bash
# Update Epic #198 with comprehensive tasklist showing all sub-issues and dependencies

set -e

EPIC_NUMBER=198

echo "📋 Actualizando Epic #$EPIC_NUMBER con tasklist completo..."
echo ""

TASKLIST_BODY="## Sub-Issues Progress

### Equipo A (Data Infrastructure)

#### Data Source Validation (Monday-Tuesday)
- [ ] #199: Portal Dades (Demográficos) → Blocks: #205, #207, #208
  - **Estimate:** 8h
  - **Sync:** Tuesday EOD - Deliver sample CSV to Equipo B
  - **Outcome:** Coverage >95% barrios

- [ ] #200: INE API (Económicos) → Blocks: #205, #207, #208
  - **Estimate:** 8h
  - **Sync:** Tuesday EOD - Deliver sample CSV to Equipo B
  - **Outcome:** Coverage >80% barrios

- [ ] #201: Catastro (Geográficos) → Blocks: #205, #207, #204
  - **Estimate:** 8h
  - **Sync:** Tuesday EOD - Confirm geometries available
  - **Outcome:** 73 barrios validated

#### Data Integration (Wednesday)
- [ ] #205: barrio_id Linking → Blocks: #204, #207
  - **Estimate:** 8h
  - **Depends on:** #199, #200, #201
  - **Sync:** Wednesday PM - Present linking results
  - **Outcome:** >90% linking success rate

#### Schema & Quality (Thursday-Friday)
- [ ] #204: PostgreSQL Schema v2.0 → Blocks: #187 (Fase 1)
  - **Estimate:** 10h
  - **Depends on:** #199, #200, #201, #205, #208 (feedback)
  - **Sync:** Wednesday PM (preliminary), Thursday PM (final)
  - **Outcome:** Schema design for 8 fact + 2 dim tables

- [ ] #207: Data Quality Assessment → Blocks: GO decision
  - **Estimate:** 6h
  - **Depends on:** #199, #200, #201
  - **Sync:** Thursday PM - Present scorecard
  - **Outcome:** Completeness >95%, Validity >98%

#### Framework (Monday-Tuesday)
- [ ] #206: Validation Framework
  - **Estimate:** 6h
  - **Depends on:** None (independent)
  - **Sync:** Tuesday AM - Framework ready for Equipo B
  - **Outcome:** Train/test split, cross-validation tools

---

### Equipo B (Analytics & Modeling)

#### Model Development (Monday-Thursday)
- [ ] #208: Hedonic Pricing Model → Blocks: GO decision
  - **Estimate:** 12h
  - **Depends on:** #199, #200 (soft - can start with mock data Monday)
  - **Sync:** Tuesday EOD (receive data), Thursday PM (present performance)
  - **Outcome:** R² ≥0.55, ≥5 significant variables
  - **Critical:** GO/NO-GO criterion

- [ ] #209: DiD Viability Assessment → Informs: GO decision
  - **Estimate:** 8h
  - **Depends on:** #208 (soft), #199 (temporal data)
  - **Sync:** Thursday PM - Present viability assessment
  - **Outcome:** Control group identified, parallel trends validated

---

### GO Decision Criteria (Friday Dec 20, 3:00 PM)

**Must meet ALL criteria for GO:**

- [ ] Data availability >90% (#199, #200, #201)
- [ ] Hedonic R² ≥0.55 (#208)
- [ ] barrio_id linking >90% (#205)
- [ ] Data quality >95% (#207)
- [ ] PostgreSQL schema designed (#204)

**Decision Outcomes:**

- ✅ **GO** → Proceed with #187, #194, #195, #196
- ❌ **NO-GO** → Pivot to alternative project
- ⚠️ **GO with caveats** → Adjust scope of Fases 1-4

---

### Total Effort Breakdown

**Equipo A:** 54h
- #199: 8h
- #200: 8h
- #201: 8h
- #204: 10h
- #205: 8h
- #206: 6h
- #207: 6h

**Equipo B:** 20h
- #208: 12h
- #209: 8h

**Total Spike:** 74h (Dec 16-20, 2025)

---

### Critical Path

\`\`\`
Monday AM:
  → #199, #200, #201, #206 (parallel start)

Tuesday EOD:
  → #199, #200, #201 deliver data to #208, #209
  → #206 framework ready

Wednesday PM:
  → #205 linking results
  → #204 preliminary schema

Thursday PM:
  → #208 model performance
  → #209 DiD viability
  → #207 data quality scorecard
  → #204 final schema

Friday PM:
  → GO/NO-GO decision
\`\`\`"

# Agregar tasklist al body del epic
echo "Agregando tasklist al Epic #$EPIC_NUMBER..."
gh issue comment "$EPIC_NUMBER" --body "$TASKLIST_BODY"

echo ""
echo "✅ Epic #$EPIC_NUMBER actualizado con tasklist completo"
echo ""
echo "📊 Ver epic:"
echo "   https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/$EPIC_NUMBER"

