#!/bin/bash
# Create Issues for Fase 1: Database Infrastructure
# Basado en ARQUITECTURA_DATOS_VARIABLES.md

set -e

echo "📋 Creating Fase 1: Database Infrastructure Issues"
echo ""

MILESTONE="Fase 1: Database Infrastructure"

# Issue 1: Create 8 Fact Tables
gh issue create \
  --title "[FASE 1] Create 8 New Fact Tables" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Crear las 8 nuevas tablas fact para la expansión de arquitectura v2.0.

## 🎯 Criterios de Aceptación
- [ ] fact_hogares creada con constraints FK
- [ ] fact_socioeconomic creada con constraints FK
- [ ] fact_construccion creada con constraints FK
- [ ] fact_movilidad creada con constraints FK
- [ ] fact_turismo creada con constraints FK
- [ ] fact_regulacion creada con constraints FK
- [ ] fact_eficiencia creada con constraints FK
- [ ] fact_financiera creada con constraints FK
- [ ] Todas las tablas con índices únicos apropiados
- [ ] Schema.sql actualizado

## 📊 Tablas a Crear

### fact_hogares
- Campos: barrioid, anio, tamanio_hogar, numero_hogares, porcentaje_total
- FK: barrioid → dim_barrios

### fact_socioeconomic
- Campos: barrioid, anio, tasa_desempleo, numero_parados, salario_medio, nivel_educativo
- FK: barrioid → dim_barrios

### fact_construccion
- Campos: barrioid, anio, visados_vivienda, nuevas_viviendas, rehabilitaciones
- FK: barrioid → dim_barrios

### fact_movilidad
- Campos: barrioid_origen, barrioid_destino, anio, numero_traslados, razon_movimiento
- FK: barrioid_origen → dim_barrios, barrioid_destino → dim_barrios

### fact_turismo
- Campos: barrioid, anio, mes, huts_registradas, airbnb_listadas, ocupacion_media
- FK: barrioid → dim_barrios

### fact_regulacion
- Campos: barrioid, anio, zona_tensionada, suelo_protegido_m2, stock_vivienda_publica
- FK: barrioid → dim_barrios

### fact_eficiencia
- Campos: barrioid, anio, viviendas_clase_a-g (%), prima_energetica
- FK: barrioid → dim_barrios

### fact_financiera
- Campos: barrioid, anio, mes, euribor_12m, tipos_hipotecarios, hipotecas_nuevas
- FK: barrioid → dim_barrios

## ⏱️ Estimación
8 horas

## 📅 Timeline
**Start Date:** 2026-01-06  
**Target Date:** 2026-01-09

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Documento: docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md (Sección 3.1)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE"

# Issue 2: Create 2 Dimension Tables
gh issue create \
  --title "[FASE 1] Create 2 New Dimension Tables" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Crear las 2 nuevas tablas dimension para métricas espaciales y ambientales.

## 🎯 Criterios de Aceptación
- [ ] dim_barrios_metricas creada con constraints FK
- [ ] dim_barrios_ambiente creada con constraints FK
- [ ] Índices espaciales configurados (PostGIS si aplica)
- [ ] Campos calculados documentados
- [ ] Schema.sql actualizado

## 📊 Tablas a Crear

### dim_barrios_metricas
- Campos: barrioid, distancia_plaza_catalunya_km, tiempo_metro, estaciones_metro, numero_equipamientos
- FK: barrioid → dim_barrios (UNIQUE)

### dim_barrios_ambiente
- Campos: barrioid, indice_calidad_aire, no2_medio, pm10_medio, area_verde_m2
- FK: barrioid → dim_barrios (UNIQUE)

## ⏱️ Estimación
6 horas

## 📅 Timeline
**Start Date:** 2026-01-09  
**Target Date:** 2026-01-10

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Documento: docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md (Sección 3.2)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE"

# Issue 3: Indexes and Constraints
gh issue create \
  --title "[FASE 1] Setup Indexes, Constraints & Migrations" \
  --body "$(cat <<'EOF'
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
- [ ] fact_hogares: UNIQUE(barrioid, anio, tamanio_hogar)
- [ ] fact_socioeconomic: UNIQUE(barrioid, anio, nivel_educativo)
- [ ] fact_construccion: UNIQUE(barrioid, anio)
- [ ] fact_movilidad: UNIQUE(barrioid_origen, barrioid_destino, anio)
- [ ] fact_turismo: UNIQUE(barrioid, anio, mes)
- [ ] fact_regulacion: UNIQUE(barrioid, anio)
- [ ] fact_eficiencia: UNIQUE(barrioid, anio)
- [ ] fact_financiera: UNIQUE(barrioid, anio, mes)
- [ ] dim_barrios_metricas: UNIQUE(barrioid)
- [ ] dim_barrios_ambiente: UNIQUE(barrioid)

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
- Epic: Architecture v2.0 Expansion
- Depende de: Issues anteriores (tablas creadas)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical" \
  --milestone "$MILESTONE"

# Issue 4: Validation & Testing
gh issue create \
  --title "[FASE 1] Validate Database Infrastructure" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Validar que toda la infraestructura de base de datos está correcta y lista para Fase 2.

## 🎯 Criterios de Aceptación
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
- Epic: Architecture v2.0 Expansion
- Depende de: Todas las issues anteriores de Fase 1

## ✅ Definition of Done
- [ ] Todas las tablas creadas
- [ ] Constraints verificados
- [ ] Tests pasando
- [ ] Documentación actualizada
- [ ] Listo para Fase 2 (extractores)
EOF
)" \
  --label "database,architecture-expansion,fase-1,p0-critical,testing" \
  --milestone "$MILESTONE"

echo ""
echo "✅ Fase 1 issues created successfully!"
echo ""
echo "📊 View issues: gh issue list --milestone 'Fase 1: Database Infrastructure'"

