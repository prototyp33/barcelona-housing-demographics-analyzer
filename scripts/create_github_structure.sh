#!/bin/bash
# Script para crear Milestones, Labels e Issues en GitHub
# Barcelona Housing Demographics Analyzer - Q1 2026 Data Expansion

# No usar set -e para permitir continuar aunque haya errores en issues individuales

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Limpiar GITHUB_TOKEN inválido del entorno si existe
unset GITHUB_TOKEN

echo "🚀 Creando estructura de GitHub para Q1 2026 Data Expansion..."
echo "📦 Repositorio: $REPO"
echo ""

# =============================================================================
# 1. CREAR MILESTONE
# =============================================================================
echo "📅 Creando Milestone..."
MILESTONE_TITLE="Foundation - New Data Sources"

# Primero verificar si el milestone ya existe
echo "🔍 Verificando si el milestone ya existe..."
EXISTING_MILESTONE=$(gh api repos/$REPO/milestones --jq ".[] | select(.title==\"$MILESTONE_TITLE\") | .number" 2>/dev/null | head -1 | grep -E '^[0-9]+$' || echo "")

if [ -n "$EXISTING_MILESTONE" ] && [ "$EXISTING_MILESTONE" -gt 0 ] 2>/dev/null; then
  echo "✅ Milestone ya existe: #$EXISTING_MILESTONE"
  MILESTONE_NUM=$EXISTING_MILESTONE
else
  echo "📝 Creando nuevo milestone..."
  MILESTONE_RESPONSE=$(gh api repos/$REPO/milestones \
    -X POST \
    -f title="$MILESTONE_TITLE" \
    -f description="Integrar 9 nuevas fuentes de datos para enriquecer análisis de vivienda.

KPIs: 9 tablas fact, 95% cobertura, ETL automatizado, Dashboard actualizado

Sprints:
- Sprint 1 (7-24 ene): Educación y Movilidad
- Sprint 2 (27 ene - 14 feb): Vivienda Pública y Zonas Verdes
- Sprint 3 (17 feb - 7 mar): Comercio, Salud y Dashboard
- Sprint 4 (10-31 mar): Catastro y Documentación" \
    -f due_on="2026-03-31T23:59:59Z" \
    --jq '.number' 2>/dev/null || echo "")
  
  if [ -z "$MILESTONE_RESPONSE" ] || ! echo "$MILESTONE_RESPONSE" | grep -qE '^[0-9]+$'; then
    echo "⚠️  Error creando milestone. Verificando si se creó..."
    MILESTONE_RESPONSE=$(gh api repos/$REPO/milestones --jq ".[] | select(.title==\"$MILESTONE_TITLE\") | .number" 2>/dev/null | head -1 | grep -E '^[0-9]+$' || echo "")
  fi
  
  if [ -n "$MILESTONE_RESPONSE" ] && echo "$MILESTONE_RESPONSE" | grep -qE '^[0-9]+$'; then
    MILESTONE_NUM=$MILESTONE_RESPONSE
    echo "✅ Milestone creado: #$MILESTONE_NUM"
  else
    echo "❌ Error: No se pudo crear ni encontrar el milestone"
    echo "💡 Verifica autenticación: gh auth status"
    exit 1
  fi
fi
echo ""

# =============================================================================
# 2. CREAR LABELS
# =============================================================================
echo "🏷️  Creando Labels..."

# Por Tipo
gh label create "feature" --color 0E8A16 --description "Nueva funcionalidad" --force 2>/dev/null || echo "  Label 'feature' ya existe"
gh label create "etl" --color 7057FF --description "Pipeline ETL" --force 2>/dev/null || echo "  Label 'etl' ya existe"
gh label create "data-extraction" --color F9D0C4 --description "Extracción de datos" --force 2>/dev/null || echo "  Label 'data-extraction' ya existe"
gh label create "database" --color BFD4F2 --description "Esquema DB y migraciones" --force 2>/dev/null || echo "  Label 'database' ya existe"
gh label create "documentation" --color 0075CA --description "Documentación" --force 2>/dev/null || echo "  Label 'documentation' ya existe"

# Por Prioridad
gh label create "priority-high" --color B60205 --description "Alta prioridad" --force 2>/dev/null || echo "  Label 'priority-high' ya existe"
gh label create "priority-medium" --color FFA500 --description "Media prioridad" --force 2>/dev/null || echo "  Label 'priority-medium' ya existe"
gh label create "priority-low" --color CCCCCC --description "Baja prioridad" --force 2>/dev/null || echo "  Label 'priority-low' ya existe"

# Por Sprint
gh label create "sprint-1" --color 1D76DB --description "Sprint 1: Educación y Movilidad" --force 2>/dev/null || echo "  Label 'sprint-1' ya existe"
gh label create "sprint-2" --color 0366D6 --description "Sprint 2: Vivienda Pública" --force 2>/dev/null || echo "  Label 'sprint-2' ya existe"
gh label create "sprint-3" --color 0052CC --description "Sprint 3: Comercio y Salud" --force 2>/dev/null || echo "  Label 'sprint-3' ya existe"
gh label create "sprint-4" --color 003D99 --description "Sprint 4: Catastro" --force 2>/dev/null || echo "  Label 'sprint-4' ya existe"

# Por Fuente
gh label create "opendata-bcn" --color 006B75 --description "Open Data Barcelona" --force 2>/dev/null || echo "  Label 'opendata-bcn' ya existe"
gh label create "atm" --color D93F0B --description "ATM Transport" --force 2>/dev/null || echo "  Label 'atm' ya existe"
gh label create "amb" --color D93F0B --description "AMB Open Data" --force 2>/dev/null || echo "  Label 'amb' ya existe"
gh label create "idescat" --color 5319E7 --description "IDESCAT" --force 2>/dev/null || echo "  Label 'idescat' ya existe"
gh label create "bicing" --color 1D76DB --description "Bicing API" --force 2>/dev/null || echo "  Label 'bicing' ya existe"

# Por Dominio
gh label create "education" --color C2E0C6 --description "Equipamientos educativos" --force 2>/dev/null || echo "  Label 'education' ya existe"
gh label create "mobility" --color BFD4F2 --description "Transporte y movilidad" --force 2>/dev/null || echo "  Label 'mobility' ya existe"
gh label create "housing" --color FBCA04 --description "Vivienda" --force 2>/dev/null || echo "  Label 'housing' ya existe"
gh label create "environment" --color 7FD8BE --description "Medio ambiente" --force 2>/dev/null || echo "  Label 'environment' ya existe"
gh label create "health" --color F9D0C4 --description "Salud" --force 2>/dev/null || echo "  Label 'health' ya existe"
gh label create "commerce" --color FFE4B5 --description "Comercio" --force 2>/dev/null || echo "  Label 'commerce' ya existe"

echo "✅ Labels creados"
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
# 4. CREAR ISSUES - SPRINT 1
# =============================================================================
echo "📝 Creando Issues - Sprint 1..."

# Issue Educación
ISSUE_NUM=$START_ISSUE
ISSUE_OUTPUT=$(gh issue create \
  --repo "$REPO" \
  --title "[S1-E1] 🎓 Implementar extractor de equipamientos educativos (Open Data BCN)" \
  --body "## Descripción
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
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-1,feature,data-extraction,opendata-bcn,priority-high,education" \
  2>&1)

if echo "$ISSUE_OUTPUT" | grep -q "https://github.com"; then
  echo "✅ Issue #$ISSUE_NUM creada"
else
  echo "⚠️  Issue #$ISSUE_NUM (error): $(echo "$ISSUE_OUTPUT" | head -1)"
fi

# Issue Movilidad Bicing
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S1-E2] 🚇 Implementar extractor de movilidad (Bicing + AMB)" \
  --body "## Descripción
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
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-1,feature,data-extraction,bicing,amb,priority-high,mobility" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue Vivienda Pública
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S1-E3] 🏘️ Implementar extractor de vivienda pública (IDESCAT)" \
  --body "## Descripción
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
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-1,feature,data-extraction,idescat,priority-high,housing" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

echo ""

# =============================================================================
# 5. CREAR ISSUES - SPRINT 2
# =============================================================================
echo "📝 Creando Issues - Sprint 2..."

# Issue Zonas Verdes
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S2-E1] 🌳 Integrar datos de zonas verdes y medio ambiente" \
  --body "## Descripción
Ampliar fact_ruido con datos de zonas verdes y árboles de Open Data BCN.

## Objetivos
1. Extraer datos de parques y jardines
2. Extraer datos de arbolado
3. Calcular m² zonas verdes por habitante
4. Ampliar tabla fact_ruido → fact_medio_ambiente

## Criterios de Aceptación
- ✅ Datos de zonas verdes extraídos de Open Data BCN
- ✅ Cálculo de m² por habitante por barrio
- ✅ Tabla fact_medio_ambiente creada o ampliada
- ✅ Tests pasan
- ✅ Documentación completa

**Story Points:** 3
**Due Date:** 7 febrero 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-2,feature,data-extraction,opendata-bcn,priority-medium,environment" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue Salud
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S2-E2] 🏥 Integrar datos de salud y servicios sanitarios" \
  --body "## Descripción
Crear fact_servicios_salud con datos de centros de salud, hospitales y farmacias.

## Objetivos
1. Extraer datos de centros de salud y hospitales
2. Extraer datos de farmacias
3. Geocodificar y mapear a 73 barrios
4. Calcular densidad de servicios sanitarios por barrio

## Criterios de Aceptación
- ✅ Tabla fact_servicios_salud creada
- ✅ ≥100 centros de salud/hospitales extraídos
- ✅ ≥200 farmacias extraídas
- ✅ 100% registros con coordenadas válidas
- ✅ Tests pasan
- ✅ Documentación completa

**Story Points:** 3
**Due Date:** 10 febrero 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-2,feature,data-extraction,opendata-bcn,priority-medium,health" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue Contaminación Aire
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S2-E3] 🌫️ Integrar datos de contaminación del aire (ASPB)" \
  --body "## Descripción
Extraer datos de NO₂, PM10, PM2.5 por estación de la Red de Calidad del Aire.

## Objetivos
1. Extraer datos históricos de calidad del aire
2. Mapear estaciones a barrios más cercanos
3. Calcular promedios anuales por barrio
4. Crear tabla fact_contaminacion_aire

## Criterios de Aceptación
- ✅ Datos de ≥5 estaciones de calidad del aire
- ✅ Cobertura temporal ≥2020-2024
- ✅ Mapeo correcto estaciones → barrios
- ✅ Tests pasan
- ✅ Documentación completa

**Story Points:** 5
**Due Date:** 14 febrero 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-2,feature,data-extraction,priority-medium,environment" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

echo ""

# =============================================================================
# 6. CREAR ISSUES - SPRINT 3
# =============================================================================
echo "📝 Creando Issues - Sprint 3..."

# Issue Comercio
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S3-E1] 🏪 Integrar datos de comercio y actividad económica" \
  --body "## Descripción
Crear fact_comercio con datos de locales comerciales, terrazas y tasa de ocupación.

## Objetivos
1. Extraer datos de locales comerciales
2. Extraer datos de terrazas y licencias
3. Calcular densidad comercial por barrio
4. Calcular tasa de ocupación de locales

## Criterios de Aceptación
- ✅ Tabla fact_comercio creada
- ✅ ≥1000 locales comerciales extraídos
- ✅ Datos de terrazas y licencias procesados
- ✅ Tests pasan
- ✅ Documentación completa

**Story Points:** 5
**Due Date:** 28 febrero 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-3,feature,data-extraction,opendata-bcn,priority-medium,commerce" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue Dashboard Integration
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S3-E2] 📊 Integrar nuevas fuentes en Dashboard Streamlit" \
  --body "## Descripción
Actualizar dashboard para mostrar datos de las nuevas fuentes (educación, movilidad, vivienda pública).

## Objetivos
1. Añadir visualizaciones para educación (centros por barrio)
2. Añadir visualizaciones para movilidad (estaciones, tiempo al centro)
3. Añadir visualizaciones para vivienda pública
4. Actualizar filtros y búsquedas

## Criterios de Aceptación
- ✅ Dashboard muestra datos de educación
- ✅ Dashboard muestra datos de movilidad
- ✅ Dashboard muestra datos de vivienda pública
- ✅ Filtros funcionan correctamente
- ✅ Tests de UI pasan
- ✅ Documentación actualizada

**Story Points:** 8
**Due Date:** 3 marzo 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-3,feature,documentation,priority-high" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue ETL Automation
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S3-E3] 🔄 Automatizar pipeline ETL completo" \
  --body "## Descripción
Crear script de orquestación ETL y GitHub Actions para ejecución automática.

## Objetivos
1. Crear script maestro de orquestación ETL
2. Configurar GitHub Actions para ejecución semanal
3. Implementar notificaciones de errores
4. Documentar proceso de automatización

## Criterios de Aceptación
- ✅ Script de orquestación funcional
- ✅ GitHub Actions configurado y funcionando
- ✅ Notificaciones de errores implementadas
- ✅ Logs estructurados y accesibles
- ✅ Documentación completa

**Story Points:** 5
**Due Date:** 7 marzo 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-3,feature,etl,priority-high" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

echo ""

# =============================================================================
# 7. CREAR ISSUES - SPRINT 4
# =============================================================================
echo "📝 Creando Issues - Sprint 4..."

# Issue Catastro
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S4-E1] 🏛️ Integrar datos de Catastro (opcional - alta complejidad)" \
  --body "## Descripción
Evaluar e implementar integración con API de Catastro para datos detallados de inmuebles.

## Objetivos
1. Evaluar opciones de acceso a datos de Catastro
2. Decidir entre API comercial vs. web scraping
3. Implementar extractor según decisión
4. Crear tabla fact_catastro con datos básicos

## Criterios de Aceptación
- ✅ Evaluación de opciones documentada
- ✅ Extractor implementado (si viable)
- ✅ Tabla fact_catastro creada (si viable)
- ✅ Tests pasan
- ✅ Documentación completa con limitaciones

**Nota:** Requiere evaluación de API comercial vs. web scraping. Puede ser descartada si no es viable.

**Story Points:** 13
**Due Date:** 24 marzo 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-4,feature,data-extraction,priority-low" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

# Issue Documentación Final
ISSUE_NUM=$((ISSUE_NUM + 1))
gh issue create \
  --repo "$REPO" \
  --title "[S4-E2] 📚 Documentación completa y guía de usuario" \
  --body "## Descripción
Completar documentación técnica y crear guía de usuario para el dashboard.

## Objetivos
1. Completar documentación técnica de todas las fuentes
2. Crear guía de usuario para el dashboard
3. Documentar proceso de instalación y configuración
4. Crear ejemplos de uso y casos de estudio

## Criterios de Aceptación
- ✅ Documentación técnica completa (todas las fuentes)
- ✅ Guía de usuario del dashboard creada
- ✅ README actualizado con instrucciones claras
- ✅ Ejemplos de uso documentados
- ✅ Documentación revisada y validada

**Story Points:** 5
**Due Date:** 31 marzo 2026" \
  --milestone "$MILESTONE_TITLE" \
  --label "sprint-4,feature,documentation,priority-medium" \
  2>/dev/null && echo "✅ Issue #$ISSUE_NUM creada" || echo "⚠️  Issue #$ISSUE_NUM (error)"

LAST_CREATED=$ISSUE_NUM
echo ""
echo "📊 Resumen:"
echo "  - Milestone: #$MILESTONE_NUM"
echo "  - Labels: 26 creados"
echo "  - Issues creadas: #$START_ISSUE - #$LAST_CREATED"
echo ""
echo "🔗 Ver issues en GitHub:"
echo "   gh issue list --milestone \"Foundation - New Data Sources\""

