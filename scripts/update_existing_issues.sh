#!/bin/bash
# Script para actualizar issues existentes con descripciones completas
# Barcelona Housing Demographics Analyzer - Q1 2026 Data Expansion

set -e

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Limpiar GITHUB_TOKEN inválido del entorno si existe
unset GITHUB_TOKEN

echo "🔄 Actualizando issues existentes con descripciones completas..."
echo "📦 Repositorio: $REPO"
echo ""

# Issue #245 - Educación
echo "📝 Actualizando Issue #245 (Educación)..."
gh issue edit 245 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #245 actualizada" || echo "⚠️  Error actualizando #245"
echo ""

# Issue #246 - Movilidad
echo "📝 Actualizando Issue #246 (Movilidad)..."
gh issue edit 246 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #246 actualizada" || echo "⚠️  Error actualizando #246"
echo ""

# Issue #247 - Vivienda Pública
echo "📝 Actualizando Issue #247 (Vivienda Pública)..."
gh issue edit 247 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #247 actualizada" || echo "⚠️  Error actualizando #247"
echo ""

# Issue #248 - Zonas Verdes
echo "📝 Actualizando Issue #248 (Zonas Verdes)..."
gh issue edit 248 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #248 actualizada" || echo "⚠️  Error actualizando #248"
echo ""

# Issue #249 - Salud
echo "📝 Actualizando Issue #249 (Salud)..."
gh issue edit 249 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #249 actualizada" || echo "⚠️  Error actualizando #249"
echo ""

# Issue #250 - Contaminación Aire
echo "📝 Actualizando Issue #250 (Contaminación Aire)..."
gh issue edit 250 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #250 actualizada" || echo "⚠️  Error actualizando #250"
echo ""

# Issue #251 - Comercio
echo "📝 Actualizando Issue #251 (Comercio)..."
gh issue edit 251 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #251 actualizada" || echo "⚠️  Error actualizando #251"
echo ""

# Issue #252 - Dashboard Integration
echo "📝 Actualizando Issue #252 (Dashboard Integration)..."
gh issue edit 252 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #252 actualizada" || echo "⚠️  Error actualizando #252"
echo ""

# Issue #253 - ETL Automation
echo "📝 Actualizando Issue #253 (ETL Automation)..."
gh issue edit 253 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #253 actualizada" || echo "⚠️  Error actualizando #253"
echo ""

# Issue #254 - Catastro
echo "📝 Actualizando Issue #254 (Catastro)..."
gh issue edit 254 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #254 actualizada" || echo "⚠️  Error actualizando #254"
echo ""

# Issue #255 - Documentación Final
echo "📝 Actualizando Issue #255 (Documentación Final)..."
gh issue edit 255 \
  --repo "$REPO" \
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
  2>&1 && echo "✅ Issue #255 actualizada" || echo "⚠️  Error actualizando #255"
echo ""

echo "✅ Actualización completada"
echo ""
echo "🔗 Ver issues actualizadas:"
echo "   gh issue list --milestone \"Foundation - New Data Sources\""

