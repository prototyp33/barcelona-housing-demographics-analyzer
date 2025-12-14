#!/bin/bash
# Create Milestones for Architecture v2.0 Expansion (Fase 1-4)
# Basado en el plan de implementación de 12 semanas

set -e

echo "📅 Creating Architecture Expansion Milestones"
echo ""

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Milestone 1: Spike Validation
echo "## Creating Milestone: Spike Validation"
gh api -X POST "repos/${REPO}/milestones" \
  -f title="Spike Validation (Dec 16-20)" \
  -f description="Data validation spike for hedonic pricing model viability" \
  -f due_on="2025-12-20T23:59:59Z" \
  --jq '.title' || echo "⚠️  Milestone may already exist"

echo ""

# Milestone 2: Fase 1 - Database Infrastructure
echo "## Creating Milestone: Fase 1 - Database Infrastructure"
gh api -X POST "repos/${REPO}/milestones" \
  -f title="Fase 1: Database Infrastructure" \
  -f description="Crear 8 tablas fact nuevas + 2 tablas dimension. Índices, constraints, migraciones. (Semanas 1-2, 22h)" \
  -f due_on="2026-01-10T23:59:59Z" \
  --jq '.title' || echo "⚠️  Milestone may already exist"

echo ""

# Milestone 3: Fase 2 - Critical Extractors
echo "## Creating Milestone: Fase 2 - Critical Extractors"
gh api -X POST "repos/${REPO}/milestones" \
  -f title="Fase 2: Critical Extractors" \
  -f description="DesempleoExtractor, EducacionExtractor, HUTExtractor, AirbnbExtractor. (Semanas 3-6, 170h)" \
  -f due_on="2026-02-07T23:59:59Z" \
  --jq '.title' || echo "⚠️  Milestone may already exist"

echo ""

# Milestone 4: Fase 3 - Complementary Extractors
echo "## Creating Milestone: Fase 3 - Complementary Extractors"
gh api -X POST "repos/${REPO}/milestones" \
  -f title="Fase 3: Complementary Extractors" \
  -f description="VisadosExtractor, ControlAlquilerExtractor, CentralidadExtractor, AccesibilidadExtractor, EficienciaEnergeticaExtractor, AmbienteExtractor. (Semanas 7-10, 170h)" \
  -f due_on="2026-03-14T23:59:59Z" \
  --jq '.title' || echo "⚠️  Milestone may already exist"

echo ""

# Milestone 5: Fase 4 - Integration & Production
echo "## Creating Milestone: Fase 4 - Integration & Production"
gh api -X POST "repos/${REPO}/milestones" \
  -f title="Fase 4: Integration & Production" \
  -f description="Pipeline ETL v3.0, validación multivariante, performance testing, documentación. (Semanas 11-12, 84h)" \
  -f due_on="2026-03-28T23:59:59Z" \
  --jq '.title' || echo "⚠️  Milestone may already exist"

echo ""
echo "✅ Milestones creation process completed!"
echo ""
echo "📊 Verifying milestones:"
gh api "repos/${REPO}/milestones?state=all" --jq '.[] | select(.title | contains("Spike") or contains("Fase")) | "\(.title) - Due: \(.due_on // "No due date") - \(.state)"'

