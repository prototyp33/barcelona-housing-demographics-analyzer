#!/bin/bash
# Create Sub-Issues for Fase 1: Database Infrastructure Epic
# Estos sub-issues se vinculan al epic principal

set -e

echo "📋 Creating Fase 1 Sub-Issues"
echo ""

# Obtener número del epic de Fase 1
EPIC_NUMBER=$(gh issue list --label epic --milestone "Fase 1: Database Infrastructure" --json number --jq '.[0].number')

if [ -z "$EPIC_NUMBER" ]; then
    echo "❌ Error: Epic de Fase 1 no encontrado"
    echo "   Crear el epic primero con: gh issue create --title '[EPIC] Fase 1: Database Infrastructure'"
    exit 1
fi

echo "Epic encontrado: #$EPIC_NUMBER"
echo ""

MILESTONE="Fase 1: Database Infrastructure"

# Sub-issue 1: Create 8 Fact Tables
ISSUE_1=$(gh issue create \
  --title "[FASE 1.1] Create 8 New Fact Tables" \
  --body "$(cat <<EOF
## 📋 Objetivo
Crear las 8 nuevas tablas fact para la expansión de arquitectura v2.0.

## 🎯 Criterios de Aceptación
- [ ] fact_desempleo creada con constraints FK
- [ ] fact_educacion creada con constraints FK
- [ ] fact_hut creada con constraints FK
- [ ] fact_airbnb creada con constraints FK
- [ ] fact_visados creada con constraints FK
- [ ] fact_control_alquiler creada con constraints FK
- [ ] fact_centralidad creada con constraints FK
- [ ] fact_accesibilidad creada con constraints FK
- [ ] Todas las tablas con índices únicos apropiados
- [ ] Schema.sql actualizado

## 📊 Tablas a Crear

Ver documentación completa en: \`docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md\` (Sección 3.1)

## ⏱️ Estimación
8 horas

## 📅 Timeline
**Start Date:** 2026-01-06  
**Target Date:** 2026-01-09

## 🔗 Relacionado
Part of #$EPIC_NUMBER

**Documento:** docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md

## Project Fields
**Epic:** DATA (categoría técnica)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE" \
  --json number --jq '.number')

echo "✅ Created sub-issue #$ISSUE_1: Create 8 Fact Tables"

# Sub-issue 2: Create 2 Dimension Tables
ISSUE_2=$(gh issue create \
  --title "[FASE 1.2] Create 2 New Dimension Tables" \
  --body "$(cat <<EOF
## 📋 Objetivo
Crear las 2 nuevas tablas dimension para métricas espaciales y temporales.

## 🎯 Criterios de Aceptación
- [ ] dim_barrios_extended creada con constraints FK
- [ ] dim_time creada (si aplica)
- [ ] Índices espaciales configurados (PostGIS si aplica)
- [ ] Campos calculados documentados
- [ ] Schema.sql actualizado

## 📊 Tablas a Crear

### dim_barrios_extended
- Campos: barrioid, distancia_plaza_catalunya_km, tiempo_metro, estaciones_metro, numero_equipamientos
- FK: barrioid → dim_barrios (UNIQUE)

### dim_time (si aplica)
- Campos para dimensiones temporales si se requiere

## ⏱️ Estimación
6 horas

## 📅 Timeline
**Start Date:** 2026-01-09  
**Target Date:** 2026-01-10

## 🔗 Relacionado
Part of #$EPIC_NUMBER

**Documento:** docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md (Sección 3.2)

## Project Fields
**Epic:** DATA (categoría técnica)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE" \
  --json number --jq '.number')

echo "✅ Created sub-issue #$ISSUE_2: Create 2 Dimension Tables"

# Sub-issue 3: Setup Indexes & Constraints
ISSUE_3=$(gh issue create \
  --title "[FASE 1.3] Setup Indexes, Constraints & Migrations" \
  --body "$(cat <<EOF
## 📋 Objetivo
Establecer índices únicos, constraints FK, y crear migraciones reversibles.

## 🎯 Criterios de Aceptación
- [ ] Índices únicos creados para todas las tablas
- [ ] Foreign key constraints verificados
- [ ] Migraciones reversibles documentadas
- [ ] Schema versionado (v2.0)
- [ ] Tests de integridad referencial pasando

## 📊 Tareas

### Índices Únicos
- [ ] Verificar UNIQUE constraints en todas las tablas
- [ ] Índices compuestos para queries frecuentes
- [ ] Índices espaciales (PostGIS) si aplica

### Constraints FK
- [ ] Todas las tablas con FK a dim_barrios verificadas
- [ ] ON DELETE CASCADE configurado apropiadamente

### Migraciones
- [ ] Script de migración desde SQLite (si aplica)
- [ ] Script de rollback documentado
- [ ] Versionado de schema

## ⏱️ Estimación
4 horas

## 📅 Timeline
**Start Date:** 2026-01-10  
**Target Date:** 2026-01-10

## 🔗 Relacionado
Part of #$EPIC_NUMBER

**Depends on:** #$ISSUE_1, #$ISSUE_2

## Project Fields
**Epic:** DATA (categoría técnica)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE" \
  --json number --jq '.number')

echo "✅ Created sub-issue #$ISSUE_3: Setup Indexes & Constraints"

# Sub-issue 4: Testing Infrastructure
ISSUE_4=$(gh issue create \
  --title "[FASE 1.4] Setup Testing Infrastructure & Validation" \
  --body "$(cat <<EOF
## 📋 Objetivo
Validar que toda la infraestructura de base de datos está correcta y lista para Fase 2.

## 🎯 Criterios de Aceptación
- [ ] Testing database operational en Render
- [ ] Todas las 10 tablas creadas y accesibles
- [ ] Constraints FK verificados (tests pasando)
- [ ] Índices funcionando correctamente
- [ ] Migraciones reversibles testeadas
- [ ] Schema.sql actualizado y versionado
- [ ] Documentación completa

## 📊 Tests a Ejecutar

### Integridad Referencial
- [ ] Test: Insertar registro con barrioid inexistente → debe fallar
- [ ] Test: Eliminar barrio con registros → debe cascadear correctamente
- [ ] Test: UNIQUE constraints funcionando

### Performance
- [ ] Test: Queries con JOINs <500ms
- [ ] Test: Índices siendo usados (EXPLAIN ANALYZE)

### Migraciones
- [ ] Test: Migración forward funciona
- [ ] Test: Migración rollback funciona
- [ ] Test: Datos preservados correctamente

## ⏱️ Estimación
4 horas

## 📅 Timeline
**Start Date:** 2026-01-10  
**Target Date:** 2026-01-10

## 🔗 Relacionado
Part of #$EPIC_NUMBER

**Depends on:** #$ISSUE_1, #$ISSUE_2, #$ISSUE_3

## Project Fields
**Epic:** DATA (categoría técnica)

## ✅ Definition of Done
- [ ] Todas las tablas creadas
- [ ] Constraints verificados
- [ ] Tests pasando
- [ ] Documentación actualizada
- [ ] Listo para Fase 2 (extractores)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical,testing" \
  --milestone "$MILESTONE" \
  --json number --jq '.number')

echo "✅ Created sub-issue #$ISSUE_4: Testing Infrastructure"

# Actualizar epic con referencias a sub-issues
echo ""
echo "## Updating Epic #$EPIC_NUMBER with sub-issue references"
echo ""

gh issue comment "$EPIC_NUMBER" --body "$(cat <<EOF
## Sub-Issues Created

- #$ISSUE_1: Create 8 New Fact Tables
- #$ISSUE_2: Create 2 New Dimension Tables
- #$ISSUE_3: Setup Indexes, Constraints & Migrations
- #$ISSUE_4: Setup Testing Infrastructure & Validation

**Total:** 4 sub-issues para Fase 1

## Dependencies

\`\`\`
#$ISSUE_1 (Create tables)
    ↓
#$ISSUE_2 (Create dimensions)
    ↓
#$ISSUE_3 (Indexes & Constraints) → Depends on: #$ISSUE_1, #$ISSUE_2
    ↓
#$ISSUE_4 (Testing) → Depends on: #$ISSUE_1, #$ISSUE_2, #$ISSUE_3
\`\`\`
EOF
)"

echo ""
echo "✅ Fase 1 sub-issues created and linked to Epic #$EPIC_NUMBER"
echo ""
echo "📊 View all Fase 1 issues:"
echo "   gh issue list --milestone 'Fase 1: Database Infrastructure'"

