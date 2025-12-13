# Issue Relationships & Custom Fields - Complete Reference

**Fecha:** Diciembre 2025  
**Propósito:** Mapa completo de relaciones y custom fields para todas las issues del spike y fases

---

## 🔷 EPICS PLACEHOLDERS (Fase 2-4)

### Issue #194: [EPIC PLACEHOLDER] Fase 2: Critical Extractors

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 256
Epic: ETL
Release: v2.0 Foundation
Phase: Extraction
Start date: 2026-01-20
Target date: 2026-02-14
Quarter: Q1 2026
Effort (weeks): 6.4
Outcome: 4 critical extractors operational with >80% test coverage
```

**Relationships:**
- **Depends on:** #187 (Fase 1: Database Infrastructure) - BLOCKER, #198 (Spike Epic) - GO decision required
- **Blocks:** #195 (Fase 3: Complementary Extractors), #196 (Fase 4: Integration & Production)
- **Related to:** #188 (Create 8 fact tables), #189 (Create 2 dimension tables)
- **Milestone:** Fase 2: Critical Extractors

---

### Issue #195: [EPIC PLACEHOLDER] Fase 3: Complementary Extractors

**Custom Fields:**
```yaml
Status: Backlog
Priority: P1
Size: XL
Estimate: 628
Epic: ETL
Release: v2.1 Enhanced Analytics
Phase: Extraction
Start date: 2026-02-24
Target date: 2026-03-21
Quarter: Q1 2026
Effort (weeks): 15.7
Outcome: 6 complementary extractors operational
```

**Relationships:**
- **Depends on:** #187 (Fase 1: Database Infrastructure), #194 (Fase 2: Critical Extractors) - BLOCKER
- **Blocks:** None (can run in parallel with #196 partially)
- **Related to:** #188 (Create 8 fact tables), #194 (Fase 2)
- **Milestone:** Fase 3: Complementary Extractors

---

### Issue #196: [EPIC PLACEHOLDER] Fase 4: Integration & Production

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 220
Epic: INFRA
Release: v2.0 Foundation
Phase: Infrastructure
Start date: 2026-03-28
Target date: 2026-04-11
Quarter: Q2 2026
Effort (weeks): 5.5
Outcome: ETL v3.0 pipeline operational in production
```

**Relationships:**
- **Depends on:** #187 (Fase 1: Database Infrastructure) - BLOCKER, #194 (Fase 2: Critical Extractors) - BLOCKER, #195 (Fase 3: Complementary Extractors) - SOFT BLOCKER
- **Blocks:** Production launch, v2.0 release
- **Related to:** #192 (Setup PostgreSQL test DB), All extractor issues
- **Milestone:** Fase 4: Integration & Production

---

## 🔬 SPIKE ISSUES (Dec 16-20)

### Issue #198: [SPIKE] Data Validation & Model Feasibility (Epic)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: XL
Estimate: 40
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 1
Outcome: GO/NO-GO decision for v2.0 with validated data sources and model
```

**Relationships:**
- **Depends on:** None (kickoff issue)
- **Blocks:** #187 (Fase 1), #194 (Fase 2), #195 (Fase 3), #196 (Fase 4)
- **Related to:** All spike sub-issues (#199-#207, #208, #209)
- **Milestone:** Spike Validation (Dec 16-20)
- **Critical Decision Point:** Friday Dec 20, 3:00 PM

---

### Issue #199: [SPIKE-EQUIPO-A] Validar acceso Portal de Dades (Demográficos)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
Outcome: Portal de Dades accessibility validated, coverage >95% barrios
```

**Relationships:**
- **Depends on:** None (can start immediately Monday)
- **Blocks:** #205 (barrio_id linking), #207 (Data quality), #204 (PostgreSQL schema), #208 (Hedonic model)
- **Related to:** #200 (INE API), #201 (Catastro), #208 (Hedonic model)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Tuesday EOD (Dec 17): Deliver sample CSV to Equipo B

---

### Issue #200: [SPIKE-EQUIPO-A] Validar acceso INE API (Económicos)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
Outcome: INE API accessibility validated, coverage >80% barrios
```

**Relationships:**
- **Depends on:** None (can start immediately Monday)
- **Blocks:** #205 (barrio_id linking), #207 (Data quality), #204 (PostgreSQL schema), #208 (Hedonic model)
- **Related to:** #199 (Portal Dades), #201 (Catastro), #208 (Hedonic model)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Tuesday EOD (Dec 17): Deliver sample CSV to Equipo B

---

### Issue #201: [SPIKE-EQUIPO-A] Validar acceso Catastro (Geográficos)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
Outcome: Catastro data accessibility validated for 73 barrios
```

**Relationships:**
- **Depends on:** None (can start immediately Monday)
- **Blocks:** #205 (barrio_id linking), #207 (Data quality), #204 (PostgreSQL schema)
- **Related to:** #199 (Portal Dades), #200 (INE API)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Tuesday EOD (Dec 17): Confirm geometries available

---

### Issue #208: [SPIKE-EQUIPO-B] Implementar hedonic pricing model (Gràcia)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: L
Estimate: 12
Epic: AN
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.3
Outcome: Hedonic model with R² ≥0.55 for Gràcia district
```

**Relationships:**
- **Depends on:** #199 (Portal Dades) - SOFT BLOCKER, #200 (INE API) - SOFT BLOCKER
- **Blocks:** #198 (Spike Epic) - GO decision depends on model performance
- **Related to:** #209 (DiD viability), #206 (Validation framework)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo B (Analytics & Modeling)
- **Sync Points:** Tuesday EOD (Dec 17): Receive sample data, Thursday PM (Dec 19): Present model performance
- **Critical Success Criteria:** GO if R² ≥ 0.55, ≥5 significant variables, expected coefficient signs

---

### Issue #209: [SPIKE-EQUIPO-B] Evaluar viabilidad Difference-in-Differences

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: AN
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
Outcome: DiD viability assessed with control group identification
```

**Relationships:**
- **Depends on:** #208 (Hedonic model) - SOFT, #199 (Portal Dades) - Needs temporal data
- **Blocks:** #198 (Spike Epic) - Informs alternative model strategy
- **Related to:** #208 (Hedonic model) - Alternative/complementary approach
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo B (Analytics & Modeling)
- **Sync Points:** Thursday PM (Dec 19): Present DiD viability assessment

---

### Issue #204: [SPIKE-EQUIPO-A] Diseñar schema PostgreSQL v2.0

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: L
Estimate: 10
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.25
Outcome: PostgreSQL schema v2.0 designed for 8 fact + 2 dim tables
```

**Relationships:**
- **Depends on:** #199 (Portal Dades), #200 (INE API), #201 (Catastro), #205 (barrio_id linking), #208 (Hedonic model)
- **Blocks:** #188 (Create 8 fact tables), #189 (Create 2 dimension tables), #187 (Fase 1 Epic)
- **Related to:** #205 (barrio_id linking), #187 (Fase 1 Epic)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Wednesday PM (Dec 18): Present preliminary schema, Thursday PM (Dec 19): Incorporate feedback

---

### Issue #205: [SPIKE-EQUIPO-A] Linking barrio_id cross-source

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 8
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.2
Outcome: barrio_id linking success rate >90% across all sources
```

**Relationships:**
- **Depends on:** #199 (Portal Dades) - BLOCKER, #200 (INE API) - BLOCKER, #201 (Catastro) - BLOCKER
- **Blocks:** #204 (PostgreSQL schema), #207 (Data quality), All future extractors
- **Related to:** #189 (Create dim_barrios_extended)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Wednesday PM (Dec 18): Present linking results
- **Critical Success Criteria:** GO if >90% linking success rate, deterministic logic

---

### Issue #206: [SPIKE-EQUIPO-A] Validation framework (model testing)

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 6
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.15
Outcome: Statistical validation framework implemented with train/test split
```

**Relationships:**
- **Depends on:** None (can start immediately)
- **Blocks:** #208 (Hedonic model) - SOFT, #209 (DiD viability) - SOFT
- **Related to:** #207 (Data quality)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure) + Equipo B (Analytics)
- **Sync Points:** Tuesday AM (Dec 17): Framework ready for Equipo B

---

### Issue #207: [SPIKE-EQUIPO-A] Data quality assessment

**Custom Fields:**
```yaml
Status: Backlog
Priority: P0
Size: M
Estimate: 6
Epic: DATA
Release: Spike
Phase: Planning
Start date: 2025-12-16
Target date: 2025-12-20
Quarter: Q4 2025
Effort (weeks): 0.15
Outcome: Data quality scorecard completed (completeness >95%, validity >98%)
```

**Relationships:**
- **Depends on:** #199 (Portal Dades), #200 (INE API), #201 (Catastro)
- **Blocks:** #198 (Spike Epic) - Quality assessment informs GO decision
- **Related to:** #205 (barrio_id linking), #206 (Validation framework)
- **Parent:** #198 (Spike Epic)
- **Team:** Equipo A (Data Infrastructure)
- **Sync Points:** Thursday PM (Dec 19): Present data quality scorecard
- **Critical Success Criteria:** GO if Completeness >95%, Validity >98%, Consistency >90%

---

## 📊 RELATIONSHIP DIAGRAMS

Ver secciones de diagramas Mermaid más abajo.

---

## 🎯 CONFIGURACIÓN EN GITHUB PROJECTS

### Cómo Agregar Relationships

**Opción 1: En el Body del Issue (Ya incluido)** ✅

**Opción 2: Usar Tasklists (GitHub Native)** - Ver script `scripts/update_epic_198_tasklist.sh`

**Opción 3: Custom Field "Depends On" (Manual)** - Solo en GitHub Projects PAID plan

---

**Última actualización:** Diciembre 2025

