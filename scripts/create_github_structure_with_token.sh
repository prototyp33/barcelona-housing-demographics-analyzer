#!/bin/bash
# Script para crear estructura GitHub usando token de entorno
# Uso: GITHUB_TOKEN=tu_token bash scripts/create_github_structure_with_token.sh

set -e

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Verificar que hay token
if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Error: GITHUB_TOKEN no está configurado"
  echo "Uso: GITHUB_TOKEN=tu_token bash $0"
  exit 1
fi

# Configurar token para gh CLI
export GH_TOKEN="$GITHUB_TOKEN"

echo "🚀 Creando estructura de GitHub para Q1 2026 Data Expansion..."
echo "📦 Repositorio: $REPO"
echo ""

# =============================================================================
# 1. CREAR MILESTONE
# =============================================================================
echo "📅 Creando Milestone..."
MILESTONE_RESPONSE=$(gh api repos/$REPO/milestones \
  -f title="Foundation - New Data Sources" \
  -f description="Integrar 9 nuevas fuentes de datos para enriquecer análisis de vivienda.

KPIs: 9 tablas fact, 95% cobertura, ETL automatizado, Dashboard actualizado

Sprints:
- Sprint 1 (7-24 ene): Educación y Movilidad
- Sprint 2 (27 ene - 14 feb): Vivienda Pública y Zonas Verdes
- Sprint 3 (17 feb - 7 mar): Comercio, Salud y Dashboard
- Sprint 4 (10-31 mar): Catastro y Documentación" \
  -f due_on="2026-03-31T23:59:59Z" \
  --jq '.number' 2>/dev/null || echo "")

if [ -z "$MILESTONE_RESPONSE" ]; then
  echo "⚠️  Milestone ya existe o error. Obteniendo número existente..."
  MILESTONE_RESPONSE=$(gh api repos/$REPO/milestones --jq '.[] | select(.title=="Foundation - New Data Sources") | .number' 2>/dev/null || echo "1")
fi

MILESTONE_NUM=${MILESTONE_RESPONSE:-1}
echo "✅ Milestone: #$MILESTONE_NUM"
echo ""

# =============================================================================
# 2. CREAR LABELS
# =============================================================================
echo "🏷️  Creando Labels..."

create_label() {
  gh label create "$1" --color "$2" --description "$3" --force 2>/dev/null && echo "  ✅ $1" || echo "  ⚠️  $1 (ya existe)"
}

# Por Tipo
create_label "feature" "0E8A16" "Nueva funcionalidad"
create_label "etl" "7057FF" "Pipeline ETL"
create_label "data-extraction" "F9D0C4" "Extracción de datos"
create_label "database" "BFD4F2" "Esquema DB y migraciones"
create_label "documentation" "0075CA" "Documentación"

# Por Prioridad
create_label "priority-high" "B60205" "Alta prioridad"
create_label "priority-medium" "FFA500" "Media prioridad"
create_label "priority-low" "CCCCCC" "Baja prioridad"

# Por Sprint
create_label "sprint-1" "1D76DB" "Sprint 1: Educación y Movilidad"
create_label "sprint-2" "0366D6" "Sprint 2: Vivienda Pública"
create_label "sprint-3" "0052CC" "Sprint 3: Comercio y Salud"
create_label "sprint-4" "003D99" "Sprint 4: Catastro"

# Por Fuente
create_label "opendata-bcn" "006B75" "Open Data Barcelona"
create_label "atm" "D93F0B" "ATM Transport"
create_label "amb" "D93F0B" "AMB Open Data"
create_label "idescat" "5319E7" "IDESCAT"
create_label "bicing" "1D76DB" "Bicing API"

# Por Dominio
create_label "education" "C2E0C6" "Equipamientos educativos"
create_label "mobility" "BFD4F2" "Transporte y movilidad"
create_label "housing" "FBCA04" "Vivienda"
create_label "environment" "7FD8BE" "Medio ambiente"
create_label "health" "F9D0C4" "Salud"
create_label "commerce" "FFE4B5" "Comercio"

echo "✅ Labels procesados"
echo ""

# =============================================================================
# 3. OBTENER ÚLTIMO NÚMERO DE ISSUE
# =============================================================================
echo "🔍 Obteniendo último número de issue..."
LAST_ISSUE=$(gh issue list --repo "$REPO" --limit 1 --json number --jq '.[0].number' 2>/dev/null || echo "238")
START_ISSUE=$((LAST_ISSUE + 1))
echo "✅ Última issue: #$LAST_ISSUE, empezando desde #$START_ISSUE"
echo ""

# =============================================================================
# 4. CREAR ISSUES
# =============================================================================
echo "📝 Creando Issues..."

ISSUE_NUM=$START_ISSUE

create_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"
  
  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    --milestone "$MILESTONE_NUM" \
    --label "$labels" \
    2>/dev/null && echo "  ✅ Issue #$ISSUE_NUM creada" || echo "  ⚠️  Issue #$ISSUE_NUM (error)"
  
  ISSUE_NUM=$((ISSUE_NUM + 1))
}

# Sprint 1
create_issue \
  "[S1-E1] 🎓 Implementar extractor de equipamientos educativos (Open Data BCN)" \
  "## Descripción
Crear extractor para datos de equipamientos educativos de Open Data BCN.

## Objetivos
1. Extraer listado completo de equipamientos educativos
2. Geocodificar y mapear a 73 barrios
3. Clasificar por tipología (infantil, primaria, secundaria, FP, universidad)
4. Tests unitarios con cobertura ≥80%

## Criterios de Aceptación
- ✅ ≥500 equipamientos extraídos
- ✅ 100% registros con coordenadas válidas
- ✅ Tests pasan
- ✅ Documentación completa en docs/data_sources/EDUCACION.md

**Story Points:** 5
**Due Date:** 14 enero 2026" \
  "sprint-1,feature,data-extraction,opendata-bcn,priority-high,education"

create_issue \
  "[S1-E2] 🚇 Implementar extractor de movilidad (Bicing + AMB)" \
  "## Descripción
Crear extractores para datos de movilidad: Bicing (GBFS API) y AMB Open Data.

## Objetivos
1. Extraer estaciones Bicing (GBFS API)
2. Extraer infraestructuras de transporte de AMB Open Data
3. Geocodificar y mapear a 73 barrios
4. Calcular tiempo medio al centro

## Criterios de Aceptación
- ✅ ≥200 estaciones Bicing extraídas
- ✅ Infraestructuras AMB procesadas
- ✅ Tests pasan
- ✅ Documentación completa

**Story Points:** 8
**Due Date:** 21 enero 2026" \
  "sprint-1,feature,data-extraction,bicing,amb,priority-high,mobility"

create_issue \
  "[S1-E3] 🏘️ Implementar extractor de vivienda pública (IDESCAT)" \
  "## Descripción
Crear extractor para datos de vivienda pública de IDESCAT con distribución proporcional.

## Objetivos
1. Extraer datos municipales de IDESCAT
2. Distribuir proporcionalmente por barrio (usando población/renta)
3. Documentar claramente que son estimaciones
4. Tests unitarios

## Criterios de Aceptación
- ✅ Datos municipales extraídos
- ✅ Distribución proporcional implementada
- ✅ Documentación con advertencias sobre estimaciones
- ✅ Tests pasan

**Story Points:** 5
**Due Date:** 24 enero 2026" \
  "sprint-1,feature,data-extraction,idescat,priority-high,housing"

# Sprint 2
create_issue \
  "[S2-E1] 🌳 Integrar datos de zonas verdes y medio ambiente" \
  "## Descripción
Ampliar fact_ruido con datos de zonas verdes y árboles de Open Data BCN.

## Objetivos
1. Extraer datos de parques y jardines
2. Extraer datos de arbolado
3. Calcular m² zonas verdes por habitante
4. Ampliar tabla fact_ruido → fact_medio_ambiente

**Story Points:** 3
**Due Date:** 7 febrero 2026" \
  "sprint-2,feature,data-extraction,opendata-bcn,priority-medium,environment"

create_issue \
  "[S2-E2] 🏥 Integrar datos de salud y servicios sanitarios" \
  "## Descripción
Crear fact_servicios_salud con datos de centros de salud, hospitales y farmacias.

**Story Points:** 3
**Due Date:** 10 febrero 2026" \
  "sprint-2,feature,data-extraction,opendata-bcn,priority-medium,health"

create_issue \
  "[S2-E3] 🌫️ Integrar datos de contaminación del aire (ASPB)" \
  "## Descripción
Extraer datos de NO₂, PM10, PM2.5 por estación de la Red de Calidad del Aire.

**Story Points:** 5
**Due Date:** 14 febrero 2026" \
  "sprint-2,feature,data-extraction,priority-medium,environment"

# Sprint 3
create_issue \
  "[S3-E1] 🏪 Integrar datos de comercio y actividad económica" \
  "## Descripción
Crear fact_comercio con datos de locales comerciales, terrazas y tasa de ocupación.

**Story Points:** 5
**Due Date:** 28 febrero 2026" \
  "sprint-3,feature,data-extraction,opendata-bcn,priority-medium,commerce"

create_issue \
  "[S3-E2] 📊 Integrar nuevas fuentes en Dashboard Streamlit" \
  "## Descripción
Actualizar dashboard para mostrar datos de las nuevas fuentes (educación, movilidad, vivienda pública).

**Story Points:** 8
**Due Date:** 3 marzo 2026" \
  "sprint-3,feature,documentation,priority-high"

create_issue \
  "[S3-E3] 🔄 Automatizar pipeline ETL completo" \
  "## Descripción
Crear script de orquestación ETL y GitHub Actions para ejecución automática.

**Story Points:** 5
**Due Date:** 7 marzo 2026" \
  "sprint-3,feature,etl,priority-high"

# Sprint 4
create_issue \
  "[S4-E1] 🏛️ Integrar datos de Catastro (opcional - alta complejidad)" \
  "## Descripción
Evaluar e implementar integración con API de Catastro para datos detallados de inmuebles.

**Nota:** Requiere evaluación de API comercial vs. web scraping.

**Story Points:** 13
**Due Date:** 24 marzo 2026" \
  "sprint-4,feature,data-extraction,priority-low"

create_issue \
  "[S4-E2] 📚 Documentación completa y guía de usuario" \
  "## Descripción
Completar documentación técnica y crear guía de usuario para el dashboard.

**Story Points:** 5
**Due Date:** 31 marzo 2026" \
  "sprint-4,feature,documentation,priority-medium"

LAST_CREATED=$((ISSUE_NUM - 1))
echo ""
echo "📊 Resumen:"
echo "  - Milestone: #$MILESTONE_NUM"
echo "  - Labels: 26 procesados"
echo "  - Issues creadas: #$START_ISSUE - #$LAST_CREATED (11 issues)"
echo ""
echo "🔗 Ver issues:"
echo "   gh issue list --milestone \"Foundation - New Data Sources\""

