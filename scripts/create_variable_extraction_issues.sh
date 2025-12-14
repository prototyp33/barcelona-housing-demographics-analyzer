#!/bin/bash
# Create GitHub Issues for Variable Extraction (Architecture v2.0 Expansion)
# Based on mapeo_variables_extractores.csv

set -e

echo "📋 Creating issues for Architecture v2.0 Variable Extraction"
echo ""

# Milestone para la expansión de arquitectura
MILESTONE="v2.1 Enhanced Analytics"  # O crear nuevo milestone "Architecture Expansion"

# Leer CSV y crear issues para variables pendientes
# Nota: Este script crea issues para extractores nuevos (no existentes)

# FASE 2: Extractores Críticos (Semanas 3-6)

echo "## Creating Fase 2: Critical Extractors"
echo ""

# 1. DesempleoExtractor
gh issue create \
  --title "[EPIC] DesempleoExtractor - Tasa de Desempleo por Barrio" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Extraer tasas de desempleo por barrio desde SEPE (Servicio Público de Empleo Estatal).

## 🎯 Criterios de Aceptación
- [ ] Extractor implementado en `src/extraction/economic/desempleo_extractor.py`
- [ ] Datos extraídos: tasa_desempleo, numero_parados, poblacion_activa
- [ ] Cobertura temporal: 2008-2025
- [ ] Datos cargados en `fact_socioeconomic`
- [ ] Tests unitarios con coverage ≥80%

## 📊 Fuente
- SEPE: https://www.sepe.es/HomeSepe/que-es-el-sepe/estadisticas
- Granularidad: Requiere mapeo territorio → barrio

## ⏱️ Estimación
40 horas

## 📅 Timeline
**Start Date:** 2026-01-27  
**Target Date:** 2026-02-09

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Tabla: fact_socioeconomic (NUEVA)
- Variable: Tasa de desempleo (Muy Alta prioridad)
EOF
)" \
  --label "epic,data-extraction,v2.1,p0-critical" \
  --milestone "$MILESTONE"

# 2. EducacionExtractor
gh issue create \
  --title "[EPIC] EducacionExtractor - Nivel Educativo por Barrio" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Extraer distribución de nivel educativo por barrio desde Open Data BCN.

## 🎯 Criterios de Aceptación
- [ ] Extractor implementado en `src/extraction/economic/educacion_extractor.py`
- [ ] Datos extraídos: nivel_educativo, porcentaje_nivel
- [ ] Categorías: Sin estudios, Primaria, ESO, Bachillerato, FP, Universidad
- [ ] Cobertura temporal: 2015-2025
- [ ] Datos cargados en `fact_socioeconomic`

## 📊 Fuente
- Open Data BCN: Dataset "nivell-destudis"
- CKAN API: https://opendata-ajuntament.barcelona.cat/data/api/3

## ⏱️ Estimación
40 horas

## 📅 Timeline
**Start Date:** 2026-02-10  
**Target Date:** 2026-02-23

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Tabla: fact_socioeconomic (NUEVA)
- Variable: Nivel educativo (Muy Alta prioridad)
EOF
)" \
  --label "epic,data-extraction,v2.1,p0-critical" \
  --milestone "$MILESTONE"

# 3. HUTExtractor
gh issue create \
  --title "[EPIC] HUTExtractor - Viviendas Uso Turístico" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Extraer registro de Habitatges d'ús Turístic (HUT) desde Ajuntament Barcelona.

## 🎯 Criterios de Aceptación
- [ ] Extractor implementado en `src/extraction/tourism/hut_extractor.py`
- [ ] Datos extraídos: huts_registradas, huts_operativas, plazas_totales
- [ ] Agregación espacial: puntos HUT → barrios (spatial join)
- [ ] Cobertura temporal: 2016-2025
- [ ] Datos cargados en `fact_turismo`

## 📊 Fuente
- Portal Dades BCN: Dataset "habitatges-us-turistic"
- Ajuntament Barcelona API

## ⏱️ Estimación
35 horas

## 📅 Timeline
**Start Date:** 2026-02-24  
**Target Date:** 2026-03-09

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Tabla: fact_turismo (NUEVA)
- Variable: Viviendas turísticas (Muy Alta prioridad)
EOF
)" \
  --label "epic,data-extraction,v2.1,p0-critical" \
  --milestone "$MILESTONE"

# 4. AirbnbExtractor
gh issue create \
  --title "[EPIC] AirbnbExtractor - Listados y Ocupación Airbnb" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Extraer datos de Airbnb desde Inside Airbnb (datos públicos agregados).

## 🎯 Criterios de Aceptación
- [ ] Extractor implementado en `src/extraction/tourism/airbnb_extractor.py`
- [ ] Datos extraídos: airbnb_listadas, airbnb_disponibles, ocupacion_media
- [ ] Snapshots mensuales/trimestrales: 2015-2025
- [ ] Agregación espacial: listados → barrios
- [ ] Datos cargados en `fact_turismo`

## 📊 Fuente
- Inside Airbnb: http://insideairbnb.com/get-data/
- Datos públicos agregados (CSV descargables)

## ⏱️ Estimación
35 horas

## 📅 Timeline
**Start Date:** 2026-02-24  
**Target Date:** 2026-03-09

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Tabla: fact_turismo (NUEVA)
- Variable: Airbnb listados (Muy Alta prioridad)
EOF
)" \
  --label "epic,data-extraction,v2.1,p0-critical" \
  --milestone "$MILESTONE"

echo ""
echo "✅ Fase 2 issues created (4 extractores críticos)"
echo ""

# FASE 3: Extractores Complementarios (Semanas 7-10)

echo "## Creating Fase 3: Complementary Extractors"
echo ""

# 5. VisadosExtractor
gh issue create \
  --title "[EPIC] VisadosExtractor - Visados de Obra Nueva" \
  --body "$(cat <<'EOF'
## 📋 Objetivo
Extraer visados de obra nueva desde Colegio Oficial de Arquitectos.

## 🎯 Criterios de Aceptación
- [ ] Extractor implementado en `src/extraction/supply/visados_extractor.py`
- [ ] Datos extraídos: visados_vivienda, nuevas_viviendas
- [ ] Cobertura temporal: 2015-2025
- [ ] Datos cargados en `fact_construccion`

## 📊 Fuente
- Colegio Oficial de Arquitectos de Catalunya
- Requiere web scraping o acuerdo de acceso

## ⏱️ Estimación
50 horas

## 📅 Timeline
**Start Date:** 2026-03-10  
**Target Date:** 2026-03-23

## 🔗 Relacionado
- Epic: Architecture v2.0 Expansion
- Tabla: fact_construccion (NUEVA)
- Variable: Nuevas construcciones (Alta prioridad)
EOF
)" \
  --label "epic,data-extraction,v2.2,p1-high" \
  --milestone "v2.2 Dashboard Polish"

# Continuar con más extractores según necesidad...

echo ""
echo "✅ Issues created successfully!"
echo ""
echo "View all issues: gh issue list --label epic"

