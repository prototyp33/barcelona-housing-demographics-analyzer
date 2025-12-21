# Resultados Finales - Modelo Hedónico MICRO

**Fecha**: 20 de diciembre de 2025  
**Issue**: #202 - Fase 2  
**Estado**: ❌ **NO-GO** - Modelo no cumple criterios de éxito

---

## 📊 Resumen Ejecutivo

### Resultados del Mejor Modelo

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **R² Test** | 0.21 | ≥ 0.75 | ❌ |
| **RMSE Test** | 2,113 €/m² | ≤ 250 €/m² | ❌ |
| **Comparación MACRO** | Peor | Mejor que MACRO | ❌ |

**Decisión**: ❌ **NO-GO** - El modelo MICRO no cumple los criterios de éxito y es **peor** que el baseline MACRO v0.1.

---

## 🔍 Comparación de Modelos Probados

| Modelo | N obs | Test R² | Test RMSE | Estado |
|--------|-------|---------|-----------|--------|
| **1. Original (todos)** | 393 | -0.66 | 2,136 €/m² | ❌ R² negativo |
| **2. Filtrado (outliers)** | 374 | 0.12 | 1,945 €/m² | ⚠️ R² bajo |
| **3. Alta calidad (score≥0.7)** | 118 | **0.21** | 2,113 €/m² | ✅ Mejor |
| **4. Log (transformación)** | 393 | 0.005 | 1,654 €/m² | ⚠️ R² muy bajo |

**Mejor modelo**: Alta calidad (score ≥ 0.7) con R² = 0.21

---

## 📊 Comparación con Baseline MACRO

| Métrica | MACRO v0.1 | MICRO (mejor) | Delta | Estado |
|---------|------------|---------------|-------|--------|
| **R²** | 0.71 | 0.21 | -0.50 | ❌ Peor |
| **RMSE** | 323 €/m² | 2,113 €/m² | +1,790 €/m² | ❌ Peor |
| **Granularidad** | Barrio×Año | Edificio | - | ✅ Mejor |

**Conclusión**: El modelo MICRO es **significativamente peor** que el baseline MACRO, a pesar de tener mayor granularidad.

---

## 🔎 Hallazgos Críticos

### 1. Correlaciones Negativas Persistentes ⚠️ **CRÍTICO**

**Incluso con matches de alta calidad (score ≥ 0.7)**:
- `superficie_m2` - `precio_m2`: **-0.186** ❌ (debería ser positiva ~0.3-0.5)
- `habitaciones` - `precio_m2`: **-0.202** ❌ (debería ser positiva ~0.2-0.4)

**Interpretación**: Las variables predictoras **NO están relacionadas** con el precio en este dataset, incluso después de filtrar por calidad de matching.

**Causa probable**: 
- Matching incorrecto entre Idealista y Catastro
- Datos de Idealista con errores (precios incorrectos)
- Variables de Catastro no corresponden a propiedades de Idealista

---

### 2. Calidad del Matching ⚠️ **PROBLEMA**

**Distribución de match scores**:
- Score < 0.5: 112 observaciones (22.2%)
- Score 0.5-0.6: 90 observaciones (17.8%)
- Score 0.6-0.7: 181 observaciones (35.8%)
- Score ≥ 0.7: 122 observaciones (24.2%)

**40% de matches tienen score < 0.6** (baja calidad)

**Problemas identificados**:
- Muchos matches tienen `catastro_barrio_nombre` = NaN
- Correlaciones negativas incluso con matches de alta calidad
- Superficies y características no corresponden a precios

---

### 3. Outliers Extremos ⚠️ **PROBLEMA**

**Antes de filtrar**:
- Precio/m² mínimo: 1,174 €/m² (muy bajo)
- Precio/m² máximo: **27,108 €/m²** (extremadamente alto)
- 32 outliers (8.1%) fuera de rango razonable

**Después de filtrar** (2,000-15,000 €/m²):
- 19 observaciones eliminadas (4.8%)
- Mejora significativa: R² de -0.66 a 0.12

---

### 4. Mejoras Observadas ✅

**Filtrar outliers**:
- R² mejora de -0.66 a 0.12 (+0.78)
- RMSE mejora de 2,136 a 1,945 €/m² (-191 €/m²)

**Filtrar por match score alto**:
- R² mejora de 0.12 a 0.21 (+0.09)
- Pero muestra se reduce a 118 observaciones (30% del original)

**Limitación**: Aunque mejoran, los resultados siguen siendo **muy inferiores** al baseline MACRO.

---

## 💡 Causas Probables del Fracaso

### Causa 1: Matching Incorrecto 🔴 **MÁS PROBABLE**

**Evidencia**:
- Correlaciones negativas incluso con matches de alta calidad
- 40% de matches de baja calidad
- Muchos `catastro_barrio_nombre` = NaN

**Hipótesis**: El algoritmo de matching está asociando propiedades incorrectas de Idealista con datos de Catastro.

**Solución sugerida**:
- Revisar algoritmo de matching manualmente
- Verificar si direcciones coinciden realmente
- Considerar usar coordenadas geográficas para matching más preciso

---

### Causa 2: Datos de Idealista Incorrectos 🔴 **PROBABLE**

**Evidencia**:
- Precios extremos (27,108 €/m² es inusual para Gràcia)
- Correlaciones negativas sugieren que precios no corresponden a características

**Hipótesis**: Los datos extraídos de Idealista (vía Comet AI) pueden tener errores:
- Precios incorrectos
- Superficies incorrectas
- Propiedades mal categorizadas

**Solución sugerida**:
- Verificar manualmente una muestra de datos de Idealista
- Comparar con precios esperados para Gràcia
- Revisar parsing de Comet AI

---

### Causa 3: Variables Predictoras Insuficientes 🟡 **POSIBLE**

**Variables actuales**:
- `superficie_m2` (correlación: -0.186)
- `habitaciones` (correlación: -0.202)
- `ano_construccion` (no significativo)
- `plantas` (no significativo)
- `barrio_id` (dummies)

**Variables faltantes** (que podrían ayudar):
- Estado de conservación
- Ascensor
- Terraza/Balcon
- Reformado/No reformado
- Orientación
- Tipo de propiedad (piso/ático/estudio)

**Solución sugerida**: Extraer más features de Idealista si están disponibles.

---

## 📋 Recomendaciones

### Para el Spike (Inmediato)

1. ✅ **Documentar hallazgos** (este documento)
2. ⏳ **Revisar algoritmo de matching**:
   - Verificar manualmente una muestra de matches
   - Analizar por qué las correlaciones son negativas
   - Considerar mejorar algoritmo o usar matching geográfico
3. ⏳ **Verificar datos de Idealista**:
   - Revisar parsing de Comet AI
   - Comparar con precios esperados
   - Identificar errores en extracción
4. ⏳ **Actualizar Issue #202** con resultados y decisión NO-GO

---

### Para Producción (Futuro)

1. **Mejorar matching**:
   - Implementar matching geográfico (coordenadas)
   - Mejorar normalización de direcciones
   - Aumentar umbral de match score mínimo (ej: 0.7)
2. **Mejorar extracción de datos**:
   - Validar datos de Idealista antes de usar
   - Extraer más features (ascensor, terraza, etc.)
   - Implementar validaciones de calidad
3. **Considerar alternativas**:
   - Usar API oficial de Idealista (si disponible)
   - Combinar múltiples fuentes de precios
   - Mantener baseline MACRO hasta resolver problemas

---

## 🎯 Decisión Final

### ❌ NO-GO para Modelo MICRO

**Razones**:
1. R² = 0.21 << objetivo de 0.75
2. RMSE = 2,113 €/m² >> objetivo de 250 €/m²
3. **Peor que baseline MACRO** (R² = 0.71, RMSE = 323 €/m²)
4. Correlaciones negativas sugieren problema fundamental en datos/matching

**Recomendación**: 
- **Mantener baseline MACRO v0.1** como modelo operativo
- **Documentar limitaciones** del modelo MICRO
- **Investigar causas** antes de intentar nuevamente

---

## 📊 Métricas de Comparación

| Aspecto | MACRO v0.1 | MICRO (mejor) | Conclusión |
|---------|------------|---------------|------------|
| **R²** | 0.71 | 0.21 | MACRO es 3.4x mejor |
| **RMSE** | 323 €/m² | 2,113 €/m² | MACRO es 6.5x mejor |
| **Granularidad** | Barrio×Año | Edificio | MICRO tiene mejor granularidad |
| **Cumplimiento criterios** | Parcial | No | Ninguno cumple completamente |
| **Recomendación** | ✅ Usar | ❌ No usar | MACRO es mejor opción |

---

## 📝 Próximos Pasos Sugeridos

### Corto Plazo (Esta semana)

1. ✅ Documentar resultados (completado)
2. ⏳ Actualizar Issue #202 con decisión NO-GO
3. ⏳ Revisar algoritmo de matching manualmente
4. ⏳ Verificar datos de Idealista

### Medio Plazo (Próximas semanas)

1. Mejorar algoritmo de matching
2. Re-extraer datos de Idealista si es necesario
3. Considerar alternativas (API oficial, otras fuentes)

### Largo Plazo (Futuro)

1. Re-evaluar modelo MICRO cuando se resuelvan problemas
2. Considerar modelo híbrido (MACRO + MICRO selectivo)
3. Implementar validaciones de calidad automáticas

---

## 📚 Documentación Relacionada

- **Análisis de problemas**: `docs/ANALISIS_PROBLEMAS_MODELO_MICRO.md`
- **Próximos pasos**: `docs/PROXIMOS_PASOS_MODELO_MICRO.md`
- **Plan Fase 2**: `docs/ISSUE_202_FASE2_PLAN.md`
- **Notebook de entrenamiento**: `notebooks/06_train_micro_hedonic_model.ipynb`

---

**Última actualización**: 2025-12-20  
**Estado**: ❌ NO-GO - Mantener MACRO v0.1 como baseline operativo

