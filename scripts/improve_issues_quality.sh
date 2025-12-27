#!/bin/bash
# Script para mejorar la calidad de las issues según mejores prácticas
# Barcelona Housing Demographics Analyzer - Q1 2026 Data Expansion

set -e

REPO="prototyp33/barcelona-housing-demographics-analyzer"

# Limpiar GITHUB_TOKEN inválido del entorno si existe
unset GITHUB_TOKEN

echo "✨ Mejorando calidad de issues según mejores prácticas..."
echo "📦 Repositorio: $REPO"
echo ""

# Issue #245 - Educación
echo "📝 Mejorando Issue #245 (Educación)..."
gh issue edit 245 \
  --repo "$REPO" \
  --title "[FEATURE] [S1-E1] 🎓 Implementar extractor de equipamientos educativos (Open Data BCN)" \
  --body "## Descripción del Problema
Actualmente no tenemos datos de equipamientos educativos por barrio, lo cual es crítico para analizar la relación entre calidad educativa y precio de vivienda.

## Descripción
Crear extractor para datos de equipamientos educativos de Open Data BCN.

## Objetivos
1. Extraer listado completo de equipamientos educativos
2. Geocodificar y mapear a 73 barrios
3. Clasificar por tipología (infantil, primaria, secundaria, FP, universidad)
4. Tests unitarios con cobertura ≥80%

## Criterios de Aceptación
- [ ] ≥500 equipamientos extraídos
- [ ] 100% registros con coordenadas válidas
- [ ] Tests pasan con cobertura ≥80%
- [ ] Documentación completa en docs/data_sources/EDUCACION.md
- [ ] Tabla fact_educacion poblada con datos de 73 barrios

## Estimación de Tiempo
- **Desarrollo:** 20 horas (2.5 días)
- **Testing:** 3 horas
- **Documentación:** 1 hora
- **Total:** 24 horas (3 días)

**Story Points:** 5
**Due Date:** 14 enero 2026" \
  2>&1 && echo "✅ Issue #245 mejorada" || echo "⚠️  Error mejorando #245"
echo ""

# Issue #246 - Movilidad
echo "📝 Mejorando Issue #246 (Movilidad)..."
gh issue edit 246 \
  --repo "$REPO" \
  --title "[FEATURE] [S1-E2] 🚇 Implementar extractor de movilidad (Bicing + AMB)" \
  --body "## Descripción del Problema
Falta información sobre accesibilidad y movilidad por barrio, necesaria para calcular tiempo al centro y evaluar calidad de transporte público.

## Descripción
Crear extractores para datos de movilidad: Bicing (GBFS API) y AMB Open Data.

## Objetivos
1. Extraer estaciones Bicing (GBFS API)
2. Extraer infraestructuras de transporte de AMB Open Data
3. Geocodificar y mapear a 73 barrios
4. Calcular tiempo medio al centro

## Criterios de Aceptación
- [ ] ≥200 estaciones Bicing extraídas
- [ ] Infraestructuras AMB procesadas (metro, bus, FGC)
- [ ] Tests pasan
- [ ] Documentación completa
- [ ] Tabla fact_movilidad poblada con datos de 73 barrios

## Estimación de Tiempo
- **Desarrollo:** 32 horas (4 días)
- **Testing:** 5 horas
- **Documentación:** 3 horas
- **Total:** 40 horas (5 días)

**Story Points:** 8
**Due Date:** 21 enero 2026" \
  2>&1 && echo "✅ Issue #246 mejorada" || echo "⚠️  Error mejorando #246"
echo ""

# Issue #247 - Vivienda Pública
echo "📝 Mejorando Issue #247 (Vivienda Pública)..."
gh issue edit 247 \
  --repo "$REPO" \
  --title "[FEATURE] [S1-E3] 🏘️ Implementar extractor de vivienda pública (IDESCAT)" \
  --body "## Descripción del Problema
Los datos de vivienda pública solo están disponibles a nivel municipal, necesitamos distribuirlos proporcionalmente por barrio para análisis granular.

## Descripción
Crear extractor para datos de vivienda pública de IDESCAT con distribución proporcional.

## Objetivos
1. Extraer datos municipales de IDESCAT
2. Distribuir proporcionalmente por barrio (usando población/renta)
3. Documentar claramente que son estimaciones
4. Tests unitarios

## Criterios de Aceptación
- [ ] Datos municipales extraídos
- [ ] Distribución proporcional implementada
- [ ] Documentación con advertencias sobre estimaciones
- [ ] Tests pasan
- [ ] Tabla fact_vivienda_publica poblada

## Estimación de Tiempo
- **Desarrollo:** 18 horas (2.25 días)
- **Testing:** 4 horas
- **Documentación:** 2 horas
- **Total:** 24 horas (3 días)

**Story Points:** 5
**Due Date:** 24 enero 2026" \
  2>&1 && echo "✅ Issue #247 mejorada" || echo "⚠️  Error mejorando #247"
echo ""

# Issue #248 - Zonas Verdes
echo "📝 Mejorando Issue #248 (Zonas Verdes)..."
gh issue edit 248 \
  --repo "$REPO" \
  --title "[FEATURE] [S2-E1] 🌳 Integrar datos de zonas verdes y medio ambiente" \
  --body "## Descripción del Problema
Necesitamos ampliar la tabla fact_ruido con datos de zonas verdes para análisis de calidad de vida y sostenibilidad ambiental.

## Descripción
Ampliar fact_ruido con datos de zonas verdes y árboles de Open Data BCN.

## Objetivos
1. Extraer datos de parques y jardines
2. Extraer datos de arbolado
3. Calcular m² zonas verdes por habitante
4. Ampliar tabla fact_ruido → fact_medio_ambiente

## Criterios de Aceptación
- [ ] Datos de zonas verdes extraídos de Open Data BCN
- [ ] Cálculo de m² por habitante por barrio
- [ ] Tabla fact_medio_ambiente creada o ampliada
- [ ] Tests pasan
- [ ] Documentación completa

## Estimación de Tiempo
- **Desarrollo:** 12 horas (1.5 días)
- **Testing:** 2 horas
- **Documentación:** 2 horas
- **Total:** 16 horas (2 días)

**Story Points:** 3
**Due Date:** 7 febrero 2026" \
  2>&1 && echo "✅ Issue #248 mejorada" || echo "⚠️  Error mejorando #248"
echo ""

# Issue #249 - Salud
echo "📝 Mejorando Issue #249 (Salud)..."
gh issue edit 249 \
  --repo "$REPO" \
  --title "[FEATURE] [S2-E2] 🏥 Integrar datos de salud y servicios sanitarios" \
  --body "## Descripción del Problema
Faltan datos de servicios sanitarios por barrio para análisis de calidad de vida y accesibilidad a servicios básicos.

## Descripción
Crear fact_servicios_salud con datos de centros de salud, hospitales y farmacias.

## Objetivos
1. Extraer datos de centros de salud y hospitales
2. Extraer datos de farmacias
3. Geocodificar y mapear a 73 barrios
4. Calcular densidad de servicios sanitarios por barrio

## Criterios de Aceptación
- [ ] Tabla fact_servicios_salud creada
- [ ] ≥100 centros de salud/hospitales extraídos
- [ ] ≥200 farmacias extraídas
- [ ] 100% registros con coordenadas válidas
- [ ] Tests pasan
- [ ] Documentación completa

## Estimación de Tiempo
- **Desarrollo:** 12 horas (1.5 días)
- **Testing:** 2 horas
- **Documentación:** 2 horas
- **Total:** 16 horas (2 días)

**Story Points:** 3
**Due Date:** 10 febrero 2026" \
  2>&1 && echo "✅ Issue #249 mejorada" || echo "⚠️  Error mejorando #249"
echo ""

# Issue #250 - Contaminación Aire
echo "📝 Mejorando Issue #250 (Contaminación Aire)..."
gh issue edit 250 \
  --repo "$REPO" \
  --title "[FEATURE] [S2-E3] 🌫️ Integrar datos de contaminación del aire (ASPB)" \
  --body "## Descripción del Problema
La calidad del aire es un factor crítico para calidad de vida pero no está integrada en nuestro análisis actual.

## Descripción
Extraer datos de NO₂, PM10, PM2.5 por estación de la Red de Calidad del Aire.

## Objetivos
1. Extraer datos históricos de calidad del aire
2. Mapear estaciones a barrios más cercanos
3. Calcular promedios anuales por barrio
4. Crear tabla fact_contaminacion_aire

## Criterios de Aceptación
- [ ] Datos de ≥5 estaciones de calidad del aire
- [ ] Cobertura temporal ≥2020-2024
- [ ] Mapeo correcto estaciones → barrios
- [ ] Tests pasan
- [ ] Documentación completa

## Estimación de Tiempo
- **Desarrollo:** 32 horas (4 días)
- **Testing:** 4 horas
- **Documentación:** 4 horas
- **Total:** 40 horas (5 días)

**Story Points:** 5
**Due Date:** 14 febrero 2026" \
  2>&1 && echo "✅ Issue #250 mejorada" || echo "⚠️  Error mejorando #250"
echo ""

# Issue #251 - Comercio
echo "📝 Mejorando Issue #251 (Comercio)..."
gh issue edit 251 \
  --repo "$REPO" \
  --title "[FEATURE] [S3-E1] 🏪 Integrar datos de comercio y actividad económica" \
  --body "## Descripción del Problema
La actividad comercial es un indicador importante de dinamismo económico del barrio pero no está integrada.

## Descripción
Crear fact_comercio con datos de locales comerciales, terrazas y tasa de ocupación.

## Objetivos
1. Extraer datos de locales comerciales
2. Extraer datos de terrazas y licencias
3. Calcular densidad comercial por barrio
4. Calcular tasa de ocupación de locales

## Criterios de Aceptación
- [ ] Tabla fact_comercio creada
- [ ] ≥1000 locales comerciales extraídos
- [ ] Datos de terrazas y licencias procesados
- [ ] Tests pasan
- [ ] Documentación completa

## Estimación de Tiempo
- **Desarrollo:** 16 horas (2 días)
- **Testing:** 2 horas
- **Documentación:** 2 horas
- **Total:** 20 horas (2.5 días)

**Story Points:** 5
**Due Date:** 28 febrero 2026" \
  2>&1 && echo "✅ Issue #251 mejorada" || echo "⚠️  Error mejorando #251"
echo ""

# Issue #252 - Dashboard Integration
echo "📝 Mejorando Issue #252 (Dashboard Integration)..."
gh issue edit 252 \
  --repo "$REPO" \
  --title "[FEATURE] [S3-E2] 📊 Integrar nuevas fuentes en Dashboard Streamlit" \
  --body "## Descripción del Problema
El dashboard actual no muestra las nuevas fuentes de datos (educación, movilidad, vivienda pública), limitando la capacidad de análisis de usuarios.

## Descripción
Actualizar dashboard para mostrar datos de las nuevas fuentes (educación, movilidad, vivienda pública).

## Objetivos
1. Añadir visualizaciones para educación (centros por barrio)
2. Añadir visualizaciones para movilidad (estaciones, tiempo al centro)
3. Añadir visualizaciones para vivienda pública
4. Actualizar filtros y búsquedas

## Criterios de Aceptación
- [ ] Dashboard muestra datos de educación
- [ ] Dashboard muestra datos de movilidad
- [ ] Dashboard muestra datos de vivienda pública
- [ ] Filtros funcionan correctamente
- [ ] Tests de UI pasan
- [ ] Documentación actualizada

## Estimación de Tiempo
- **Desarrollo:** 32 horas (4 días)
- **Testing:** 5 horas
- **Documentación:** 3 horas
- **Total:** 40 horas (5 días)

**Story Points:** 8
**Due Date:** 3 marzo 2026" \
  2>&1 && echo "✅ Issue #252 mejorada" || echo "⚠️  Error mejorando #252"
echo ""

# Issue #253 - ETL Automation
echo "📝 Mejorando Issue #253 (ETL Automation)..."
gh issue edit 253 \
  --repo "$REPO" \
  --title "[FEATURE] [S3-E3] 🔄 Automatizar pipeline ETL completo" \
  --body "## Descripción del Problema
El pipeline ETL actual requiere ejecución manual, lo cual es propenso a errores y no escala para producción.

## Descripción
Crear script de orquestación ETL y GitHub Actions para ejecución automática.

## Objetivos
1. Crear script maestro de orquestación ETL
2. Configurar GitHub Actions para ejecución semanal
3. Implementar notificaciones de errores
4. Documentar proceso de automatización

## Criterios de Aceptación
- [ ] Script de orquestación funcional
- [ ] GitHub Actions configurado y funcionando
- [ ] Notificaciones de errores implementadas
- [ ] Logs estructurados y accesibles
- [ ] Documentación completa

## Estimación de Tiempo
- **Desarrollo:** 32 horas (4 días)
- **Testing:** 4 horas
- **Documentación:** 4 horas
- **Total:** 40 horas (5 días)

**Story Points:** 5
**Due Date:** 7 marzo 2026" \
  2>&1 && echo "✅ Issue #253 mejorada" || echo "⚠️  Error mejorando #253"
echo ""

# Issue #254 - Catastro
echo "📝 Mejorando Issue #254 (Catastro)..."
gh issue edit 254 \
  --repo "$REPO" \
  --title "[FEATURE] [S4-E1] 🏛️ Integrar datos de Catastro (opcional - alta complejidad)" \
  --body "## Descripción del Problema
Los datos de Catastro proporcionarían información detallada sobre características físicas de inmuebles, pero el acceso requiere evaluación de opciones técnicas y legales.

## Descripción
Evaluar e implementar integración con API de Catastro para datos detallados de inmuebles.

## Objetivos
1. Evaluar opciones de acceso a datos de Catastro
2. Decidir entre API comercial vs. web scraping
3. Implementar extractor según decisión
4. Crear tabla fact_catastro con datos básicos

## Criterios de Aceptación
- [ ] Evaluación de opciones documentada
- [ ] Extractor implementado (si viable)
- [ ] Tabla fact_catastro creada (si viable)
- [ ] Tests pasan
- [ ] Documentación completa con limitaciones

**Nota:** Requiere evaluación de API comercial vs. web scraping. Puede ser descartada si no es viable.

## Estimación de Tiempo
- **Investigación:** 16 horas (2 días)
- **Desarrollo:** 40 horas (5 días)
- **Testing:** 4 horas
- **Documentación:** 4 horas
- **Total:** 64 horas (8 días)

**Story Points:** 13
**Due Date:** 24 marzo 2026" \
  2>&1 && echo "✅ Issue #254 mejorada" || echo "⚠️  Error mejorando #254"
echo ""

# Issue #255 - Documentación Final
echo "📝 Mejorando Issue #255 (Documentación Final)..."
gh issue edit 255 \
  --repo "$REPO" \
  --title "[FEATURE] [S4-E2] 📚 Documentación completa y guía de usuario" \
  --body "## Descripción del Problema
La documentación actual está incompleta y no hay guía de usuario para el dashboard, limitando la adopción y mantenibilidad del proyecto.

## Descripción
Completar documentación técnica y crear guía de usuario para el dashboard.

## Objetivos
1. Completar documentación técnica de todas las fuentes
2. Crear guía de usuario para el dashboard
3. Documentar proceso de instalación y configuración
4. Crear ejemplos de uso y casos de estudio

## Criterios de Aceptación
- [ ] Documentación técnica completa (todas las fuentes)
- [ ] Guía de usuario del dashboard creada
- [ ] README actualizado con instrucciones claras
- [ ] Ejemplos de uso documentados
- [ ] Documentación revisada y validada

## Estimación de Tiempo
- **Documentación técnica:** 16 horas (2 días)
- **Guía de usuario:** 6 horas
- **Revisión y edición:** 2 horas
- **Total:** 24 horas (3 días)

**Story Points:** 5
**Due Date:** 31 marzo 2026" \
  2>&1 && echo "✅ Issue #255 mejorada" || echo "⚠️  Error mejorando #255"
echo ""

echo "✅ Mejora de calidad completada"
echo ""
echo "🔍 Verificar issues mejoradas:"
echo "   gh issue list --milestone \"Foundation - New Data Sources\""

