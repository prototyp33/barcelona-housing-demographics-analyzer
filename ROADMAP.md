# Roadmap del Proyecto: Barcelona Housing Market Intelligence Platform

**Fecha:** 12 de diciembre de 2025  
**Horizonte:** Q1-Q2 2026 (6 meses post-Spike)

---

## 1. Estructura del Roadmap

Voy a organizar el roadmap en **4 niveles**:

1. **Strategic View** (6 meses, quarterly OKRs)
2. **Release Plan** (v2.0 → v2.1 → v2.2)
3. **Execution Plan** (Phases & Sprints)
4. **Integration con GitHub** (Projects, Milestones, Issues)

---

## 2. Strategic View (Q1-Q2 2026)

### 2.1 Quarters & Objectives

```
┌─────────────────────────────────────────────────────────────┐
│                    Q1 2026 (Jan-Mar)                        │
├─────────────────────────────────────────────────────────────┤
│ 🎯 OBJECTIVE: Foundation & Core Analytics                  │
│                                                              │
│ Key Results:                                                │
│ 1. PostgreSQL database operational with 2020-2025 data     │
│ 2. Hedonic pricing model deployed (R² ≥0.55)               │
│ 3. Dashboard MVP with 3 core pages live                    │
│ 4. 50+ beta users testing platform                         │
│                                                              │
│ Releases:                                                    │
│ → v2.0 (Late Jan): Foundation + Basic Analytics            │
│ → v2.1 (Late Feb): Enhanced Analytics + DiD                │
│ → v2.2 (Late Mar): Dashboard Polish + Performance          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Q2 2026 (Apr-Jun)                        │
├─────────────────────────────────────────────────────────────┤
│ 🎯 OBJECTIVE: Scale & Advanced Features                    │
│                                                              │
│ Key Results:                                                │
│ 1. All 73 barrios with complete demographic data           │
│ 2. Investment scoring algorithm validated                  │
│ 3. Public API launched (v1.0)                              │
│ 4. 200+ active users, <2s avg page load                   │
│                                                              │
│ Releases:                                                    │
│ → v2.3 (Late Apr): Complete Barcelona Coverage             │
│ → v3.0 (Late May): Public API + Scoring                    │
│ → v3.1 (Late Jun): What-if Simulator + Mobile              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Release Plan (Detailed)

### 3.1 Release Timeline (Gantt-style)

```
Dec 2025    Jan 2026         Feb 2026         Mar 2026         Apr 2026
   │           │                │                │                │
   ▼           ▼                ▼                ▼                ▼
SPIKE ───> v2.0 ─────────> v2.1 ─────────> v2.2 ─────────> v2.3 ────>
Dec 16-20   Jan 27          Feb 24          Mar 24          Apr 21

├─────┤   ├──────────┤    ├──────────┤    ├──────────┤    ├──────────┤
1 week    6 weeks         4 weeks         4 weeks         4 weeks
          (Foundation)    (Analytics)     (Polish)        (Coverage)
```

---

### 3.2 v2.0: Foundation (Jan 27, 2026)

**Duration:** 6 weeks (Jan 6 - Jan 27)  
**Team Size:** 2 eng + 1 data sci + 1 PM  
**Scope:** Minimum Viable Analytics Platform

#### Features

| Feature ID | Description | Priority | Estimate |
|------------|-------------|----------|----------|
| **DATA-001** | PostgreSQL + PostGIS setup | P0 | 1 week |
| **DATA-002** | Schema v2.0 implementation | P0 | 1 week |
| **ETL-001** | INE price data extractor (automated) | P0 | 1 week |
| **ETL-002** | Portal de Dades demographics extractor | P0 | 1 week |
| **ETL-003** | Catastro attributes extractor | P1 | 1 week |
| **AN-001** | Hedonic pricing model (OLS) | P0 | 2 weeks |
| **VIZ-001** | Streamlit dashboard base | P0 | 1 week |
| **VIZ-002** | Market Cockpit page | P0 | 1 week |
| **VIZ-003** | Barrio Deep Dive page | P1 | 1 week |
| **INFRA-001** | Deployment pipeline (Render/Railway) | P0 | 3 days |

#### Success Criteria

```yaml
go_live_criteria:
  data:
    - barrios_coverage: ≥20 (out of 73)
    - temporal_coverage: "2020-2025"
    - data_quality: ≥95% completeness
  
  model:
    - hedonic_r2: ≥0.55
    - coefficient_signs: plausible
    - diagnostics: ≥4/5 tests passing
  
  dashboard:
    - pages_live: ≥2 (Market Cockpit + Barrio Deep Dive)
    - load_time: <5s
    - mobile_compatible: true
  
  deployment:
    - uptime: ≥95%
    - ci_cd: automated tests passing
    - documentation: complete (README, API docs)
```

#### Phases (2-week sprints)

**Sprint 1 (Jan 6-17): Data Layer**
- PostgreSQL setup & schema
- ETL extractors (INE + Portal de Dades)
- Initial data load (20 barrios pilot)

**Sprint 2 (Jan 13-24): Analytics**
- Hedonic model implementation
- Model validation & diagnostics
- Notebook documentation

**Sprint 3 (Jan 20-27): Dashboard + Deploy**
- Streamlit pages (Market Cockpit + Barrio)
- Deployment to Render/Railway
- Beta testing with 10 users

---

### 3.3 v2.1: Enhanced Analytics (Feb 24, 2026)

**Duration:** 4 weeks (Jan 27 - Feb 24)  
**Scope:** Advanced econometric models + expanded coverage

#### Features

| Feature ID | Description | Priority | Estimate |
|------------|-------------|----------|----------|
| **AN-002** | Diff-in-Diff analysis (Ley 12/2023) | P0 | 2 weeks |
| **AN-003** | Price decomposition algorithm | P1 | 1 week |
| **ETL-004** | INCASÒL data integration | P1 | 1 week |
| **VIZ-004** | Regulatory Impact Analyzer page | P0 | 1 week |
| **VIZ-005** | Interactive map (Plotly/Folium) | P0 | 1 week |
| **DATA-003** | Expand to 40 barrios | P1 | 1 week |
| **PERF-001** | Query optimization (indexes, views) | P1 | 3 days |

#### Success Criteria

```yaml
v2_1_criteria:
  analytics:
    - did_model: implemented
    - regulatory_effect: quantified
    - decomposition: working
  
  coverage:
    - barrios: ≥40 (out of 73)
    - time_series: monthly 2020-2025
  
  performance:
    - query_time: <2s (p95)
    - dashboard_load: <3s
```

---

### 3.4 v2.2: Dashboard Polish (Mar 24, 2026)

**Duration:** 4 weeks (Feb 24 - Mar 24)  
**Scope:** UX improvements + performance + documentation

#### Features

| Feature ID | Description | Priority | Estimate |
|------------|-------------|----------|----------|
| **VIZ-006** | Demographic Trends page | P1 | 1 week |
| **UX-001** | Dashboard redesign (professional UI) | P0 | 2 weeks |
| **UX-002** | Export to PDF/Excel functionality | P1 | 1 week |
| **PERF-002** | Caching layer (Redis) | P1 | 1 week |
| **DOCS-001** | User guide & tutorials | P0 | 1 week |
| **TEST-001** | End-to-end testing suite | P0 | 1 week |

---

### 3.5 v2.3: Complete Coverage (Apr 21, 2026)

**Duration:** 4 weeks (Mar 24 - Apr 21)  
**Scope:** All 73 barrios + data quality refinement

#### Features

| Feature ID | Description | Priority | Estimate |
|------------|-------------|----------|----------|
| **DATA-004** | Complete 73 barrios coverage | P0 | 2 weeks |
| **DQ-001** | Data quality monitoring dashboard | P1 | 1 week |
| **ETL-005** | Automated data refresh pipeline | P0 | 1 week |
| **VIZ-007** | Comparison tool (multi-barrio) | P1 | 1 week |

---

### 3.6 v3.0: Public API + Scoring (May 26, 2026)

**Duration:** 5 weeks (Apr 21 - May 26)  
**Scope:** REST API + Investment scoring

#### Features

| Feature ID | Description | Priority | Estimate |
|------------|-------------|----------|----------|
| **API-001** | FastAPI REST API implementation | P0 | 2 weeks |
| **API-002** | API authentication (JWT) | P0 | 1 week |
| **API-003** | Rate limiting & monitoring | P1 | 1 week |
| **AN-004** | Investment opportunity scoring | P0 | 2 weeks |
| **DOCS-002** | API documentation (OpenAPI/Swagger) | P0 | 1 week |

---

## 4. Execution Plan (Phases & Sprints)

### 4.1 Agile Framework

```
Framework: Scrum (2-week sprints)
Ceremonies:
  - Sprint Planning: Monday 9:00 AM (2h)
  - Daily Standup: Every day 9:30 AM (15 min, async in Slack)
  - Sprint Review: Alternate Friday 2:00 PM (1h)
  - Sprint Retro: Alternate Friday 3:00 PM (1h)

Team Composition:
  - Product Manager: 1 (roadmap, priorities, stakeholder mgmt)
  - Backend Engineer: 1 (ETL, database, API)
  - Full-Stack Engineer: 1 (dashboard, UX)
  - Data Scientist: 1 (models, analysis)
  - (Part-time) DevOps: 0.5 (CI/CD, monitoring)
```

---

## 5. Integration con GitHub

### 5.1 GitHub Projects Structure

**Crear 2 Projects:**

1. **Project: "Barcelona Housing - Roadmap"** (Board view)
   - Vista: Quarterly releases
   - Tracking: High-level features

2. **Project: "Barcelona Housing - Sprint Board"** (Kanban)
   - Vista: Current sprint work
   - Tracking: Daily execution

---

## 6. Roadmap Visualization

### 6.1 Mermaid Gantt Chart (para README)

Ver sección en README.md

---

## 7. Scripts de Automatización del Roadmap

Ver scripts en `scripts/`:
- `create_milestones.sh` - Crear milestones de releases
- `create_roadmap_issues.sh` - Crear epic issues
- `roadmap_progress.sh` - Reporte de progreso

---

## 8. Conclusión: Roadmap File Structure

```
barcelona-housing-demographics-analyzer/
├── README.md                    # Includes Mermaid Gantt chart
├── ROADMAP.md                   # This document (detailed roadmap)
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── epic.md              # Epic template
│       ├── user-story.md        # User story template
│       └── spike.md             # Spike template (already exists)
├── docs/
│   ├── roadmap/
│   │   ├── v2.0-foundation.md   # Detailed plan for v2.0
│   │   ├── v2.1-analytics.md    # Detailed plan for v2.1
│   │   └── okrs-2026.md         # Quarterly OKRs
│   └── architecture/
│       └── system-design-v2.md  # Technical architecture
├── scripts/
│   ├── create_milestones.sh     # Create release milestones
│   ├── create_roadmap_issues.sh # Create epic issues
│   └── roadmap_progress.sh      # Progress reporting
└── spike-data-validation/       # (Already exists)
```

---

## 9. Next Steps

1. ✅ Crear ROADMAP.md (este archivo)
2. ⏳ Crear milestones en GitHub
3. ⏳ Crear epic issues para v2.0
4. ⏳ Actualizar README con Gantt chart
5. ⏳ Setup GitHub Projects (manual)

