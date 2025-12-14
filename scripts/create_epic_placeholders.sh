#!/bin/bash
# Create Epic Placeholders for Fase 2, 3, 4
# These are placeholder epics that will be refined post-spike

set -e

echo "🚀 Creando Epic Placeholders para Fase 2-4..."
echo ""

# Epic Fase 2: Critical Extractors
echo "1️⃣ Creando Epic Fase 2: Critical Extractors..."

EPIC_2_URL=$(gh issue create \
  --title "[EPIC PLACEHOLDER] Fase 2: Critical Extractors" \
  --body "## Objetivo

Desarrollar 4 extractores críticos para alimentar fact tables.

## Scope (Pendiente refinamiento post-spike)

**Extractors a desarrollar:**

1. **DesempleoExtractor** - SEPE unemployment data → fact_desempleo

2. **EducacionExtractor** - Education centers → fact_educacion

3. **HUTExtractor** - Tourist apartments registry → fact_hut

4. **AirbnbExtractor** - Airbnb listings → fact_airbnb

**Tests & Infrastructure:**

- Unit tests (>80% coverage)

- Integration tests

- CI/CD setup

- Documentation

## Dependencies

- ✅ Fase 1 completada (schema v2.0 disponible)

- ⚠️ **Pending Spike validation** (Dec 16-20, 2025)

  - Confirmar acceso a APIs

  - Validar data quality

  - Verificar linking barrio_id

## Next Actions

- [ ] **Dec 20:** Review spike findings

- [ ] **Dec 21:** Decompose into user stories (si GO decision)

- [ ] **Jan 6:** Kickoff development (si aprobado)

## Estimated Effort

~170h (to be refined post-spike)

**Breakdown (preliminary):**

- Extractors: 4 × 40h = 160h

- Tests: 4 × 15h = 60h

- CI/CD: 8h

- Docs: 8h

- Integration: 20h

Total: ~256h (refinable)

## Risks

- APIs may be rate-limited or unavailable

- Data quality may be insufficient for analytics

- Linking barrio_id may fail for some sources

---

## Custom Fields (configurar después de crear)

- **Status:** Backlog

- **Priority:** P0

- **Size:** XL

- **Estimate:** 256 (preliminary)

- **Epic:** ETL

- **Release:** v2.0 Foundation

- **Phase:** Extraction

- **Start Date:** 2026-01-20

- **Target Date:** 2026-02-14

- **Quarter:** Q1 2026

- **Effort (weeks):** 6.4

- **Outcome:** 4 critical extractors operational with >80% test coverage" \
  --label "epic,v2.0,etl,priority-critical" \
  --milestone "Fase 2: Critical Extractors")

EPIC_2_NUMBER=$(echo "$EPIC_2_URL" | grep -oE '[0-9]+$')
echo "   ✅ Epic Fase 2 creado: #$EPIC_2_NUMBER"
echo "   URL: $EPIC_2_URL"
echo ""

# Epic Fase 3: Complementary Extractors
echo "2️⃣ Creando Epic Fase 3: Complementary Extractors..."

EPIC_3_URL=$(gh issue create \
  --title "[EPIC PLACEHOLDER] Fase 3: Complementary Extractors" \
  --body "## Objetivo

Desarrollar extractores complementarios para variables adicionales.

## Scope (Pendiente refinamiento post-Fase 2)

**Extractors a desarrollar:**

1. **VisadosExtractor** - Visa applications → fact_visados

2. **ControlAlquilerExtractor** - Rent control data → fact_control_alquiler

3. **CentralidadExtractor** - Centrality metrics → fact_centralidad

4. **AccesibilidadExtractor** - Accessibility scores → fact_accesibilidad

5. **EficienciaEnergeticaExtractor** - Energy efficiency → fact_eficiencia

6. **AmbienteExtractor** - Environmental data → fact_ambiente

## Dependencies

- ✅ Fase 1 completada (schema supports new tables)

- ✅ Fase 2 completada (extractor pattern established)

- ⚠️ **Pending v2.0 stability validation**

## Next Actions

- [ ] **Feb 15:** Refine scope based on Fase 2 learnings

- [ ] **Feb 17:** Decompose into user stories

- [ ] **Feb 24:** Kickoff development

## Estimated Effort

~628h (highly preliminary)

## Risks

- Data sources may not exist for all variables

- May require web scraping (higher complexity)

- Some metrics may need to be calculated vs extracted

---

## Custom Fields (configurar después de crear)

- **Status:** Backlog

- **Priority:** P1

- **Size:** XL

- **Estimate:** 628 (very preliminary)

- **Epic:** ETL

- **Release:** v2.1 Enhanced Analytics

- **Phase:** Extraction

- **Start Date:** 2026-02-24

- **Target Date:** 2026-03-21

- **Quarter:** Q1 2026

- **Effort (weeks):** 15.7

- **Outcome:** 6 complementary extractors operational" \
  --label "epic,v2.1,etl,priority-high" \
  --milestone "Fase 3: Complementary Extractors")

EPIC_3_NUMBER=$(echo "$EPIC_3_URL" | grep -oE '[0-9]+$')
echo "   ✅ Epic Fase 3 creado: #$EPIC_3_NUMBER"
echo "   URL: $EPIC_3_URL"
echo ""

# Epic Fase 4: Integration & Production
echo "3️⃣ Creando Epic Fase 4: Integration & Production..."

EPIC_4_URL=$(gh issue create \
  --title "[EPIC PLACEHOLDER] Fase 4: Integration & Production" \
  --body "## Objetivo

Integrar todos los extractores en pipeline ETL v3.0 y desplegar a producción.

## Scope (Pendiente refinamiento post-Fase 3)

**Tasks:**

1. **Pipeline Integration**

   - Orchestrate 18 extractors

   - Automatic scheduling (daily/weekly/monthly)

   - Error handling & retry logic

   - Notification system

2. **Validation & Testing**

   - Global multivariate validation

   - Performance testing (load, stress)

   - Data quality monitoring

   - End-to-end tests

3. **Production Deployment**

   - Deploy to production environment

   - Setup monitoring & alerts

   - Backup & disaster recovery

   - Runbooks & documentation

## Dependencies

- ✅ Fase 1, 2, 3 completadas (all extractors ready)

- ⚠️ **Pending production infrastructure**

## Next Actions

- [ ] **Mar 22:** Refine deployment strategy

- [ ] **Mar 24:** Decompose into user stories

- [ ] **Mar 28:** Kickoff integration

## Estimated Effort

~220h

## Risks

- Integration issues between extractors

- Performance bottlenecks at scale

- Production environment not ready

---

## Custom Fields (configurar después de crear)

- **Status:** Backlog

- **Priority:** P0

- **Size:** XL

- **Estimate:** 220

- **Epic:** INFRA

- **Release:** v2.0 Foundation

- **Phase:** Infrastructure

- **Start Date:** 2026-03-28

- **Target Date:** 2026-04-11

- **Quarter:** Q2 2026

- **Effort (weeks):** 5.5

- **Outcome:** ETL v3.0 pipeline operational in production" \
  --label "epic,v2.0,type-infra,priority-critical" \
  --milestone "Fase 4: Integration & Production")

EPIC_4_NUMBER=$(echo "$EPIC_4_URL" | grep -oE '[0-9]+$')
echo "   ✅ Epic Fase 4 creado: #$EPIC_4_NUMBER"
echo "   URL: $EPIC_4_URL"
echo ""

echo "========================================="
echo "✅ EPIC PLACEHOLDERS CREADOS"
echo "========================================="
echo ""
echo "Epic Fase 2: #$EPIC_2_NUMBER"
echo "Epic Fase 3: #$EPIC_3_NUMBER"
echo "Epic Fase 4: #$EPIC_4_NUMBER"
echo ""
echo "⚠️  NEXT STEPS:"
echo ""
echo "1. Agregar epics al proyecto GitHub:"
echo "   ./scripts/add_epics_to_project.sh (crear si no existe)"
echo ""
echo "2. Configurar custom fields en GitHub Projects UI"
echo "   Ver valores en el body de cada epic"
echo ""
echo "Script completado! 🎉"

