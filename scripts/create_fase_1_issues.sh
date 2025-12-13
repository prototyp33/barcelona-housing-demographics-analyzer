#!/bin/bash

# create_fase_1_issues.sh (VERSIÓN CORREGIDA)

set -e

echo "🚀 Creando issues de Fase 1..."
echo ""

# Step 1: Crear epic
echo "1️⃣ Creando Epic de Fase 1..."

EPIC_URL=$(gh issue create \
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

- [ ] [DATA-101] Create 8 fact tables

- [ ] [DATA-102] Create 2 dimension tables

- [ ] [DATA-103] Create indexes & FK constraints

- [ ] [DATA-104] Update schema.sql

- [ ] [INFRA-101] Setup testing database

- [ ] [DOCS-101] Document schema v2.0

## Acceptance Criteria

- All tables created in PostgreSQL

- Migrations run without errors

- Test DB mirrors production schema

- Docs reflect new schema

## Dependencies

None (first phase)

## Risks

- Schema changes during Fase 2 (mitigate: keep flexible)

---

## Custom Fields (configurar en UI después de crear)

- **Status:** Backlog

- **Priority:** P0

- **Size:** XL

- **Estimate:** 49

- **Epic:** DATA ← Categoría técnica

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-06

- **Target Date:** 2026-01-17

- **Quarter:** Q1 2026

- **Effort (weeks):** 1.2

- **Outcome:** PostgreSQL schema v2.0 operational with 8 fact + 2 dim tables" \
  --label "epic,type-infra,priority-critical" \
  --milestone "Fase 1: Database Infrastructure")

# Extraer número del issue
EPIC_NUMBER=$(echo $EPIC_URL | grep -oE '[0-9]+$')

echo "   ✅ Epic creado: #${EPIC_NUMBER}"
echo "   URL: ${EPIC_URL}"
echo ""

# Step 2: Crear sub-issues
echo "2️⃣ Creando sub-issues de Fase 1..."

# Sub-issue 1: Create 8 fact tables
gh issue create \
  --title "[DATA-101] Create 8 fact tables in PostgreSQL" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Create fact tables para:

1. **fact_desempleo** - SEPE unemployment data by barrio-month

2. **fact_educacion** - Education centers metrics by barrio-year

3. **fact_hut** - Tourist apartment registrations by barrio-month

4. **fact_airbnb** - Airbnb listings by barrio-month

5. **fact_visados** - Visa applications by barrio-month

6. **fact_control_alquiler** - Rent control data by barrio-quarter

7. **fact_centralidad** - Centrality metrics by barrio (static)

8. **fact_accesibilidad** - Accessibility scores by barrio (static)

## Tasks

- [ ] Design schema para cada table (granularidad: barrio-month vs barrio-year)

- [ ] Create SQL DDL statements

- [ ] Add primary keys (composite PK: barrio_id + fecha donde aplique)

- [ ] Add foreign keys to dim_barrios_extended

- [ ] Test CREATE TABLE statements en test DB

- [ ] Document schema en docs/architecture/DATABASE_SCHEMA_V2.md

## Acceptance Criteria

- [ ] All 8 tables created without errors

- [ ] PKs and FKs validated

- [ ] Test data insertable (validate constraints)

- [ ] Schema documented with column descriptions

## SQL Example

\`\`\`sql
CREATE TABLE fact_desempleo (
  desempleo_id SERIAL PRIMARY KEY,
  barrio_id INT NOT NULL REFERENCES dim_barrios_extended(barrio_id),
  fecha DATE NOT NULL,
  total_desempleados INT,
  tasa_desempleo DECIMAL(5,2),
  desempleo_jovenes INT,
  desempleo_mayores_45 INT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(barrio_id, fecha)
);

CREATE INDEX idx_desempleo_barrio ON fact_desempleo(barrio_id);
CREATE INDEX idx_desempleo_fecha ON fact_desempleo(fecha);
\`\`\`

## Dependencies

- Requires dim_barrios_extended to exist first (#${EPIC_NUMBER})

## Estimated Hours

8h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P0

- **Size:** L

- **Estimate:** 8

- **Epic:** DATA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-06

- **Target Date:** 2026-01-08" \
  --label "user-story,database,priority-critical" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 1: DATA-101 (8 fact tables) - 8h"

# Sub-issue 2: Create 2 dimension tables
gh issue create \
  --title "[DATA-102] Create 2 dimension tables" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Create dimension tables:

1. **dim_barrios_extended** - Extended barrio information
   - Existing columns from dim_barrios
   - + distrito, distrito_id
   - + geometry (PostGIS)
   - + metadata (population_2024, area_km2, etc.)

2. **dim_time** - Time dimension for temporal queries
   - fecha (primary key)
   - year, quarter, month, week, day_of_week
   - is_holiday, is_weekend
   - fiscal_quarter, fiscal_year

## Tasks

- [ ] Design dim_barrios_extended schema (backward compatible with existing dim_barrios)

- [ ] Design dim_time schema

- [ ] Create SQL DDL statements

- [ ] Add constraints (PKs, unique keys)

- [ ] Populate dim_time with dates (2015-01-01 to 2030-12-31)

- [ ] Test dimension tables

- [ ] Document dimension usage

## Acceptance Criteria

- [ ] Both dimension tables created

- [ ] dim_time populated with full date range (5,844 rows for 16 years)

- [ ] PKs and unique constraints validated

- [ ] Documentation updated with dimension descriptions

## SQL Example

\`\`\`sql
CREATE TABLE dim_barrios_extended (
  barrio_id INT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  distrito VARCHAR(100),
  distrito_id INT,
  geometry GEOMETRY(POLYGON, 4326),
  area_km2 DECIMAL(10,4),
  population_2024 INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dim_time (
  date_id SERIAL PRIMARY KEY,
  fecha DATE UNIQUE NOT NULL,
  year INT NOT NULL,
  quarter INT CHECK (quarter BETWEEN 1 AND 4),
  month INT CHECK (month BETWEEN 1 AND 12),
  week INT CHECK (week BETWEEN 1 AND 53),
  day_of_week INT CHECK (day_of_week BETWEEN 0 AND 6),
  is_weekend BOOLEAN,
  is_holiday BOOLEAN DEFAULT FALSE
);

-- Populate dim_time
INSERT INTO dim_time (fecha, year, quarter, month, week, day_of_week, is_weekend)
SELECT 
  d::date,
  EXTRACT(YEAR FROM d),
  EXTRACT(QUARTER FROM d),
  EXTRACT(MONTH FROM d),
  EXTRACT(WEEK FROM d),
  EXTRACT(DOW FROM d),
  EXTRACT(DOW FROM d) IN (0, 6)
FROM generate_series('2015-01-01'::date, '2030-12-31'::date, '1 day'::interval) d;
\`\`\`

## Dependencies

None (foundation tables)

## Estimated Hours

6h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P0

- **Size:** L

- **Estimate:** 6

- **Epic:** DATA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-06

- **Target Date:** 2026-01-08" \
  --label "user-story,database,priority-critical" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 2: DATA-102 (2 dimension tables) - 6h"

# Sub-issue 3: Create indexes & constraints
gh issue create \
  --title "[DATA-103] Create indexes and foreign key constraints" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Add performance indexes and data integrity constraints to all tables.

## Tasks

- [ ] Add spatial indexes to geometry columns (dim_barrios_extended)

- [ ] Add indexes to all foreign keys (barrio_id, fecha)

- [ ] Add composite indexes for common query patterns (barrio_id + fecha)

- [ ] Validate foreign key constraints

- [ ] Test query performance with indexes

- [ ] Document index strategy

## Index Strategy

\`\`\`sql
-- Spatial indexes
CREATE INDEX idx_barrios_geom ON dim_barrios_extended USING GIST(geometry);

-- Foreign key indexes (for each fact table)
CREATE INDEX idx_fact_desempleo_barrio ON fact_desempleo(barrio_id);
CREATE INDEX idx_fact_desempleo_fecha ON fact_desempleo(fecha);
CREATE INDEX idx_fact_desempleo_barrio_fecha ON fact_desempleo(barrio_id, fecha);

-- Repeat for all 8 fact tables...
\`\`\`

## Acceptance Criteria

- [ ] All foreign keys have indexes

- [ ] Spatial indexes on geometry columns

- [ ] Composite indexes for common joins

- [ ] Query performance acceptable (<100ms for typical queries)

- [ ] No constraint violations

- [ ] EXPLAIN ANALYZE shows index usage

## Performance Targets

- Barrio lookup: <10ms

- Temporal range query (1 year): <50ms

- Spatial query (within polygon): <100ms

## Estimated Hours

4h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P0

- **Size:** M

- **Estimate:** 4

- **Epic:** DATA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-09

- **Target Date:** 2026-01-09" \
  --label "user-story,database,priority-critical" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 3: DATA-103 (indexes & constraints) - 4h"

# Sub-issue 4: Update schema.sql
gh issue create \
  --title "[DATA-104] Update schema.sql with v2.0 changes" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Consolidate all DDL statements into master schema.sql file.

## Tasks

- [ ] Merge all CREATE TABLE statements into schema.sql

- [ ] Add DROP TABLE IF EXISTS statements (for idempotency)

- [ ] Create migration script (schema_v1_to_v2.sql)

- [ ] Add seed data scripts (optional)

- [ ] Test schema.sql from scratch on empty DB

- [ ] Document breaking changes from v1.0

- [ ] Version control (tag as schema_v2.0.sql)

## Files to Update

\`\`\`
src/database/
├── schema.sql ← Master schema (v2.0)
├── migrations/
│   └── v1_to_v2_migration.sql ← Migration script
└── seeds/
    ├── dim_barrios_extended.sql
    └── dim_time.sql
\`\`\`

## Acceptance Criteria

- [ ] schema.sql runs without errors on empty DB

- [ ] Migration script tested on v1.0 database (no data loss)

- [ ] Version tagged in git (v2.0.0-schema)

- [ ] Documentation updated with migration guide

- [ ] Rollback script created (v2_to_v1_rollback.sql)

## Migration Strategy

\`\`\`sql
-- v1_to_v2_migration.sql
BEGIN;

-- Backup existing data
CREATE TABLE fact_precios_backup AS SELECT * FROM fact_precios;

-- Create new tables
-- ... (all v2.0 tables)

-- Migrate data (if applicable)
-- ... (insert into new tables from old)

-- Validation
SELECT 'Validation: fact_precios row count' AS check,
       (SELECT COUNT(*) FROM fact_precios) AS new_count,
       (SELECT COUNT(*) FROM fact_precios_backup) AS old_count;

COMMIT;
\`\`\`

## Estimated Hours

4h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P0

- **Size:** M

- **Estimate:** 4

- **Epic:** DATA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-10

- **Target Date:** 2026-01-10" \
  --label "user-story,database,priority-critical" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 4: DATA-104 (schema.sql update) - 4h"

# Sub-issue 5: Setup testing database
gh issue create \
  --title "[INFRA-101] Setup PostgreSQL testing database on Render" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Provision PostgreSQL + PostGIS instance on Render for testing schema v2.0.

## Tasks

- [ ] Create Render account (if not exists)

- [ ] Provision PostgreSQL instance (Free tier for testing)

- [ ] Enable PostGIS extension

- [ ] Configure connection string

- [ ] Test connectivity from local machine

- [ ] Run schema.sql on test DB

- [ ] Document credentials in .env.example (NOT in .env)

- [ ] Configure backup strategy (Render auto-backups)

## Configuration

\`\`\`bash
# Render PostgreSQL settings
Instance type: Free (limited to 1GB storage, 1 connection)
Region: Frankfurt (EU - closest to Barcelona)
PostgreSQL version: 16
Extensions: PostGIS 3.4

# Connection string format
DATABASE_URL=postgresql://user:password@dpg-xxxxx.frankfurt-postgres.render.com/dbname
\`\`\`

## Acceptance Criteria

- [ ] PostgreSQL accessible remotely

- [ ] PostGIS extension enabled and working

- [ ] Connection string documented in .env.example

- [ ] Security configured (SSL required)

- [ ] Test query successful (SELECT PostGIS_version();)

- [ ] schema.sql runs successfully

## Security Checklist

- [ ] SSL/TLS enabled

- [ ] Strong password generated

- [ ] IP whitelist configured (if needed)

- [ ] Credentials NOT committed to git

## Test Query

\`\`\`sql
-- Verify PostGIS
SELECT PostGIS_version();
-- Expected: 3.4.x

-- Verify schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
-- Expected: 10 tables (8 fact + 2 dim)
\`\`\`

## Estimated Hours

3h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P0

- **Size:** M

- **Estimate:** 3

- **Epic:** INFRA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-01-10

- **Target Date:** 2026-01-10" \
  --label "user-story,type-infra,priority-critical" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 5: INFRA-101 (test database on Render) - 3h"

# Sub-issue 6: Document schema v2.0
gh issue create \
  --title "[DOCS-101] Document schema v2.0 in architecture docs" \
  --body "## Parent Epic
#${EPIC_NUMBER}

## Descripción

Update architecture documentation with comprehensive schema v2.0 details.

## Tasks

- [ ] Create/update docs/architecture/DATABASE_SCHEMA_V2.md

- [ ] Create ER diagram (mermaid or dbdiagram.io)

- [ ] Document each table (purpose, columns, relationships, granularity)

- [ ] Document migration path from v1.0

- [ ] Add examples of common queries

- [ ] Document data quality requirements (completeness, validity)

## Document Structure

\`\`\`markdown
# Database Schema v2.0

## Overview
[High-level description]

## ER Diagram
[Mermaid diagram showing all tables and relationships]

## Tables

### Dimension Tables

#### dim_barrios_extended
- **Purpose:** ...
- **Granularity:** 1 row per barrio (73 total)
- **Columns:** ...
- **Relationships:** ...

#### dim_time
- **Purpose:** ...
- **Granularity:** 1 row per day
- **Columns:** ...

### Fact Tables

#### fact_desempleo
- **Purpose:** ...
- **Granularity:** barrio-month
- **Source:** SEPE API
- **Columns:** ...
- **Expected Rows:** ~35,000 (73 barrios × 60 months × 8 years)

[Repeat for all 8 fact tables]

## Common Queries
[SQL examples with EXPLAIN ANALYZE results]

## Migration Guide
[Step-by-step v1.0 → v2.0 migration]

## Data Quality
[Requirements and validation queries]
\`\`\`

## ER Diagram Example (Mermaid)

\`\`\`mermaid
erDiagram
    dim_barrios_extended ||--o{ fact_desempleo : has
    dim_barrios_extended ||--o{ fact_educacion : has
    dim_time ||--o{ fact_desempleo : has
\`\`\`

## Acceptance Criteria

- [ ] DATABASE_SCHEMA_V2.md complete and accurate

- [ ] ER diagram visual and clear

- [ ] All tables documented with examples

- [ ] Migration guide tested and verified

- [ ] Common query examples tested

## Estimated Hours

2h

---

## Custom Fields (configurar en UI)

- **Status:** Backlog

- **Priority:** P1

- **Size:** S

- **Estimate:** 2

- **Epic:** DOCS

- **Release:** v2.0 Foundation

- **Phase:** Documentation

- **Start Date:** 2026-01-13

- **Target Date:** 2026-01-13" \
  --label "user-story,documentation,priority-high" \
  --milestone "Fase 1: Database Infrastructure" > /dev/null

echo "   ✅ Sub-issue 6: DOCS-101 (schema documentation) - 2h"

echo ""
echo "========================================="
echo "✅ FASE 1 ISSUES CREADOS"
echo "========================================="
echo ""
echo "Epic: #${EPIC_NUMBER} [EPIC] Fase 1: Database Infrastructure"
echo "Sub-issues: 6 issues"
echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│ Issue         │ Título                │ Hours  │"
echo "├─────────────────────────────────────────────────┤"
echo "│ DATA-101      │ 8 fact tables         │   8h   │"
echo "│ DATA-102      │ 2 dimension tables   │   6h   │"
echo "│ DATA-103      │ Indexes & constraints │   4h   │"
echo "│ DATA-104      │ Update schema.sql     │   4h   │"
echo "│ INFRA-101     │ Test DB on Render     │   3h   │"
echo "│ DOCS-101      │ Documentation         │   2h   │"
echo "├─────────────────────────────────────────────────┤"
echo "│ TOTAL         │                       │  27h   │"
echo "└─────────────────────────────────────────────────┘"
echo ""
echo "⚠️  NEXT STEPS:"
echo ""
echo "1. Verificar issues creados:"
echo "   ./scripts/verify_fase1_fields.sh"
echo ""
echo "2. Configurar custom fields en GitHub Projects UI:"
echo "   - Referencia completa: docs/FASE1_CUSTOM_FIELDS_REFERENCE.md"
echo "   - CSV source: data/reference/fase1_custom_fields.csv"
echo ""
echo "3. Epic #${EPIC_NUMBER} - Configurar:"
echo "   - Epic: DATA, Priority: P0, Size: XL, Estimate: 49"
echo "   - Start: 2026-01-06, Target: 2026-01-17"
echo ""
echo "4. Sub-issues (6 total) - Ver tabla completa en:"
echo "   docs/FASE1_CUSTOM_FIELDS_REFERENCE.md"
echo ""
echo "Script completado! 🎉"

