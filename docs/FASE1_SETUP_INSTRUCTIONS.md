# Fase 1: Database Infrastructure - Setup Instructions

**Fecha:** Diciembre 2025  
**Duración:** 1.2 semanas (Jan 6-17, 2026)  
**Esfuerzo:** 49 horas

---

## Paso 1: Crear Epic y Sub-Issues de Fase 1

### ⭐ Script Recomendado (Todo en uno)

```bash
chmod +x scripts/create_fase_1_issues.sh
./scripts/create_fase_1_issues.sh
```

Este script crea:
- ✅ Epic de Fase 1
- ✅ 6 sub-issues (DATA-101 a DATA-104, INFRA-101, DOCS-101)
- ✅ Referencias correctas al parent epic
- ✅ Custom fields documentados en cada issue

### Opción B: Scripts Separados (Legacy)

Si prefieres crear por separado:

```bash
chmod +x scripts/create_fase1_epic.sh
./scripts/create_fase1_epic.sh
```

### Opción B: Comando manual

```bash
gh issue create \
  --title "[EPIC] Fase 1: Database Infrastructure" \
  --body "$(cat <<'EOF'
## Objetivo

Establecer schema v2.0 en PostgreSQL con 8 fact tables + 2 dimension tables.

## Scope

- **8 Fact Tables:** fact_desempleo, fact_educacion, fact_hut, fact_airbnb, fact_visados, fact_control_alquiler, fact_centralidad, fact_accesibilidad

- **2 Dimension Tables:** dim_barrios_extended, dim_time

- **Indexes & Constraints:** PKs, FKs, spatial indexes

- **Testing Setup:** Test DB en Render

- **Documentation:** Schema v2.0 docs

## Entregables

- [ ] Schema SQL completo
- [ ] Testing database operational
- [ ] Migration plan from v1.0
- [ ] Documentation updated

## Acceptance Criteria

- All tables created in PostgreSQL
- Migrations run without errors
- Test DB mirrors production schema
- Docs reflect new schema

## Dependencies

None (first phase)

## Risks

- Schema changes during Fase 2 (mitigate: keep flexible, avoid premature optimization)

---

## Project Fields

**Start Date:** 2026-01-06
**Target Date:** 2026-01-17
**Epic:** DATA
**Release:** v2.0 Foundation
**Quarter:** Q1 2026
**Phase:** Infrastructure
**Priority:** P0
**Size:** XL
**Estimate:** 49
**Effort (weeks):** 1.2
**Outcome:** PostgreSQL schema v2.0 operational with 8 fact + 2 dim tables

**Estimate:** 49h  
**Duration:** 1.2 weeks  
**Team:** Dev1 (lead), DBA (support)
EOF
)" \
  --milestone "Fase 1: Database Infrastructure" \
  --label "epic,v2.0,phase-infrastructure,p0-critical"
```

---

## Paso 2: Configurar Custom Fields en GitHub Projects UI

Una vez creado el epic, configurar los siguientes campos en GitHub Projects:

### Campos a Configurar

| Campo | Valor |
|------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | XL |
| **Estimate** | 49 |
| **Epic** | DATA (categoría técnica, NO el número del epic) |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-06 |
| **Target Date** | 2026-01-17 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 1.2 |
| **Outcome** | PostgreSQL schema v2.0 operational with 8 fact + 2 dim tables |

### Instrucciones

1. Ir a **GitHub Projects** → "Barcelona Housing - Roadmap"
2. Buscar el issue del epic recién creado
3. Click en el issue para abrir el panel lateral
4. Configurar cada campo manualmente según la tabla arriba

**⚠️ IMPORTANTE:** 
- El campo **Epic** es para categoría técnica (DATA, ETL, AN, etc.), NO para el número del epic parent
- Para referenciar el parent epic, usar `Part of #NUMBER` en el body del issue (ver `docs/EPIC_FIELD_USAGE.md`)

---

## Paso 3: Crear Sub-Issues

### Opción A: Usando el script

```bash
chmod +x scripts/create_fase1_subissues.sh
./scripts/create_fase1_subissues.sh
```

### Opción B: Crear manualmente

El script creará 4 sub-issues:

1. **[FASE 1.1] Create 8 New Fact Tables** (8h)
2. **[FASE 1.2] Create 2 New Dimension Tables** (6h)
3. **[FASE 1.3] Setup Indexes, Constraints & Migrations** (4h)
4. **[FASE 1.4] Setup Testing Infrastructure & Validation** (4h)

**Total:** 22 horas (resto del tiempo es overhead, documentación, etc.)

---

## Paso 4: Verificar Setup

```bash
# Verificar epic creado
gh issue list --label epic --milestone "Fase 1: Database Infrastructure"

# Verificar sub-issues
gh issue list --milestone "Fase 1: Database Infrastructure"

# Verificar milestone
gh api "repos/prototyp33/barcelona-housing-demographics-analyzer/milestones?state=all" \
  --jq '.[] | select(.title | contains("Fase 1")) | "\(.title) - Due: \(.due_on)"'
```

---

## Estructura de Dependencias

```
[EPIC] Fase 1: Database Infrastructure
    │
    ├── [FASE 1.1] Create 8 New Fact Tables
    │       └── Start: 2026-01-06
    │       └── Target: 2026-01-09
    │
    ├── [FASE 1.2] Create 2 New Dimension Tables
    │       └── Start: 2026-01-09
    │       └── Target: 2026-01-10
    │       └── Depends on: FASE 1.1
    │
    ├── [FASE 1.3] Setup Indexes, Constraints & Migrations
    │       └── Start: 2026-01-10
    │       └── Target: 2026-01-10
    │       └── Depends on: FASE 1.1, FASE 1.2
    │
    └── [FASE 1.4] Setup Testing Infrastructure & Validation
            └── Start: 2026-01-10
            └── Target: 2026-01-10
            └── Depends on: FASE 1.1, FASE 1.2, FASE 1.3
```

---

## Referencias

- **Arquitectura Completa:** `docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md`
- **Plan de Implementación:** `docs/ARCHITECTURE_IMPLEMENTATION_PLAN.md`
- **Milestone:** "Fase 1: Database Infrastructure" (Due: 2026-01-10)

---

**Última actualización:** Diciembre 2025

