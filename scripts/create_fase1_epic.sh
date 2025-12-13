#!/bin/bash
# Create Epic for Fase 1: Database Infrastructure
# Ejecutar manualmente si hay problemas de permisos

set -e

echo "📋 Creating Fase 1 Epic"
echo ""

gh issue create \
  --title "[EPIC] Fase 1: Database Infrastructure" \
  --body "## Objetivo

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

## Sub-issues

- #TBD: Create 8 fact tables

- #TBD: Create 2 dimension tables

- #TBD: Setup indexes

- #TBD: Testing infrastructure

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
**Team:** Dev1 (lead), DBA (support)" \
  --milestone "Fase 1: Database Infrastructure" \
  --label "epic,v2.0,phase-infrastructure,p0-critical"

echo ""
echo "✅ Epic created successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Configurar custom fields en GitHub Projects UI"
echo "   2. Ejecutar: ./scripts/create_fase1_subissues.sh"

