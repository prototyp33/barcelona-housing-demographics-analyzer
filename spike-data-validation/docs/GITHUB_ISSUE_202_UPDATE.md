# Comentario para GitHub Issue #202

## 📊 Resultados Finales - Modelo Hedónico MICRO

**Fecha**: 20 de diciembre de 2025  
**Estado**: ❌ **NO-GO** - Modelo no cumple criterios de éxito

---

### Resumen Ejecutivo

Después de entrenar múltiples variantes del modelo MICRO con datos reales (393 observaciones Idealista ↔ Catastro), **el modelo no cumple los criterios de éxito** y es **significativamente peor** que el baseline MACRO v0.1.

**Decisión**: ❌ **NO-GO** - Mantener MACRO v0.1 como baseline operativo.

---

### Resultados del Mejor Modelo

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **R² Test** | 0.21 | ≥ 0.75 | ❌ |
| **RMSE Test** | 2,113 €/m² | ≤ 250 €/m² | ❌ |
| **Comparación MACRO** | Peor | Mejor que MACRO | ❌ |

**Mejor modelo**: Matches de alta calidad (score ≥ 0.7) con 118 observaciones.

---

### Comparación de Modelos Probados

| Modelo | N obs | Test R² | Test RMSE | Estado |
|--------|-------|---------|-----------|--------|
| Original (todos) | 393 | -0.66 | 2,136 €/m² | ❌ R² negativo |
| Filtrado (outliers) | 374 | 0.12 | 1,945 €/m² | ⚠️ R² bajo |
| **Alta calidad (score≥0.7)** | **118** | **0.21** | **2,113 €/m²** | ✅ Mejor |
| Log (transformación) | 393 | 0.005 | 1,654 €/m² | ⚠️ R² muy bajo |

---

### Comparación con Baseline MACRO

| Métrica | MACRO v0.1 | MICRO (mejor) | Delta | Estado |
|---------|------------|---------------|-------|--------|
| **R²** | 0.71 | 0.21 | -0.50 | ❌ Peor |
| **RMSE** | 323 €/m² | 2,113 €/m² | +1,790 €/m² | ❌ Peor |
| **Granularidad** | Barrio×Año | Edificio | - | ✅ Mejor |

**Conclusión**: El modelo MICRO es **3.4x peor en R²** y **6.5x peor en RMSE** que el baseline MACRO.

---

### 🔍 Hallazgos Críticos

#### 1. Correlaciones Negativas Persistentes ⚠️ **CRÍTICO**

**Incluso con matches de alta calidad (score ≥ 0.7)**:
- `superficie_m2` - `precio_m2`: **-0.186** ❌ (debería ser positiva ~0.3-0.5)
- `habitaciones` - `precio_m2`: **-0.202** ❌ (debería ser positiva ~0.2-0.4)

**Interpretación**: Las variables predictoras **NO están relacionadas** con el precio, incluso después de filtrar por calidad de matching.

#### 2. Calidad del Matching ⚠️ **PROBLEMA**

- **40% de matches tienen score < 0.6** (baja calidad)
- Muchos matches tienen `catastro_barrio_nombre` = NaN
- Correlaciones negativas incluso con matches de alta calidad

#### 3. Outliers Extremos ⚠️ **PROBLEMA**

- Precio/m² máximo: **27,108 €/m²** (extremadamente alto)
- Precio/m² mínimo: 1,174 €/m² (muy bajo)
- 32 outliers (8.1%) fuera de rango razonable

**Mejora después de filtrar**: R² mejora de -0.66 a 0.12, pero sigue siendo muy bajo.

---

### 💡 Causas Probables del Fracaso

#### Causa 1: Matching Incorrecto 🔴 **MÁS PROBABLE**

**Evidencia**:
- Correlaciones negativas incluso con matches de alta calidad
- 40% de matches de baja calidad
- Muchos `catastro_barrio_nombre` = NaN

**Hipótesis**: El algoritmo de matching está asociando propiedades incorrectas de Idealista con datos de Catastro.

#### Causa 2: Datos de Idealista Incorrectos 🔴 **PROBABLE**

**Evidencia**:
- Precios extremos (27,108 €/m² es inusual para Gràcia)
- Correlaciones negativas sugieren que precios no corresponden a características

**Hipótesis**: Los datos extraídos de Idealista (vía Comet AI) pueden tener errores en precios o superficies.

#### Causa 3: Variables Predictoras Insuficientes 🟡 **POSIBLE**

Variables faltantes que podrían ayudar:
- Estado de conservación
- Ascensor
- Terraza/Balcon
- Reformado/No reformado
- Orientación

---

### 📋 Recomendaciones

#### Para el Spike (Inmediato)

1. ✅ **Documentar hallazgos** (completado)
2. ⏳ **Revisar algoritmo de matching**:
   - Verificar manualmente una muestra de matches
   - Analizar por qué las correlaciones son negativas
   - Considerar matching geográfico (coordenadas)
3. ⏳ **Verificar datos de Idealista**:
   - Revisar parsing de Comet AI
   - Comparar con precios esperados para Gràcia
   - Identificar errores en extracción
4. ⏳ **Actualizar Issue #202** con resultados (este comentario)

#### Para Producción (Futuro)

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

### 🎯 Decisión Final

#### ❌ NO-GO para Modelo MICRO

**Razones**:
1. R² = 0.21 << objetivo de 0.75
2. RMSE = 2,113 €/m² >> objetivo de 250 €/m²
3. **Peor que baseline MACRO** (R² = 0.71, RMSE = 323 €/m²)
4. Correlaciones negativas sugieren problema fundamental en datos/matching

**Recomendación**: 
- **Mantener baseline MACRO v0.1** como modelo operativo
- **Investigar causas** antes de intentar nuevamente
- **Documentar limitaciones** para futuras iteraciones

---

### 📊 Artefactos Generados

- **Notebook de entrenamiento**: `notebooks/06_train_micro_hedonic_model.ipynb`
- **Análisis de problemas**: `docs/ANALISIS_PROBLEMAS_MODELO_MICRO.md`
- **Resultados finales**: `docs/MODELO_MICRO_RESULTADOS_FINALES.md`
- **Dataset filtrado**: `data/processed/fase2/dataset_micro_hedonic_filtered.csv`
- **Resultados JSON**: `data/processed/fase2/modelo_micro_results.json`

---

### 📝 Próximos Pasos

1. **Revisar algoritmo de matching** (prioridad alta)
2. **Verificar datos de Idealista** (prioridad alta)
3. **Considerar mejoras al matching** (matching geográfico)
4. **Re-evaluar modelo MICRO** cuando se resuelvan problemas fundamentales

---

**Estado del Issue**: ⏳ **Bloqueado** - Requiere investigación de causas antes de continuar  
**Baseline recomendado**: ✅ **MACRO v0.1** (R² = 0.71, RMSE = 323 €/m²)

