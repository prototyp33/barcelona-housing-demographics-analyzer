# Próximos Pasos - Modelo Hedónico MICRO

**Fecha**: 20 de diciembre de 2025  
**Estado**: ✅ Modelo entrenado con datos reales (393 observaciones)  
**Issue**: #202 - Fase 2

---

## ✅ Completado Recientemente

1. **Entrenamiento Modelo MICRO con Datos Reales**
   - Dataset: 393 observaciones (Idealista ↔ Catastro matched)
   - Modelo Lineal entrenado ✅
   - Diagnósticos OLS implementados ✅
   - Resultados guardados en `modelo_micro_results.json` ✅

2. **Correcciones Técnicas**
   - ✅ VIF corregido (solo variables predictoras, sin `const`)
   - ✅ Serialización JSON corregida (conversión numpy → Python nativo)
   - ✅ Modelo log agregado al notebook (pendiente ejecución)

## ⚠️ HALLAZGOS CRÍTICOS (ACTUALIZADO)

**Resultados Finales del Mejor Modelo (matches de alta calidad)**:
- ❌ **R² test: 0.21** (objetivo: ≥0.75)
- ❌ **RMSE test: 2,113 €/m²** (objetivo: ≤250 €/m²)
- ❌ **Peor que MACRO**: R² = 0.21 vs MACRO R² = 0.71
- ⚠️ **Correlaciones negativas**: Incluso con matches de alta calidad (-0.186, -0.202)

**Decisión**: ❌ **NO-GO** - Modelo no cumple criterios y es peor que baseline MACRO

**Comparación con Baseline MACRO**:
- MACRO: R² = 0.71, RMSE = 323 €/m²
- MICRO: R² = -0.66, RMSE = 2,136 €/m²
- **Delta**: MICRO es **MUCHO PEOR** que MACRO

**Diagnósticos OLS**:
- ❌ Normalidad: NO pasa (p=0.008)
- ❌ Homocedasticidad: NO pasa (p=0.033)
- ✅ Autocorrelación: Pasa (DW=1.88)
- ❌ Multicolinealidad: NO pasa (VIF max=12.68)

**Coeficientes Significativos**:
- ✅ `superficie_m2`: +21.08 €/m² (positivo, esperado)
- ⚠️ `habitaciones`: -1,019 €/m² (NEGATIVO - contraintuitivo)
- ✅ `barrio_31.0`: +1,643 €/m² (diferencias entre barrios)

**Problemas Identificados**:
1. **R² negativo**: Indica que el modelo es peor que predecir la media
2. **RMSE extremadamente alto**: 2,136 €/m² vs objetivo 250 €/m²
3. **Coeficiente negativo de habitaciones**: Contraintuitivo (más habitaciones = menos precio?)
4. **Modelo log no ejecutado**: Pendiente probar transformación logarítmica

---

## 📋 Próximos Pasos Inmediatos

### 1. Investigación de Problemas Críticos ⏳ **URGENTE**

**Objetivo**: Entender por qué el modelo tiene R² negativo y RMSE tan alto

**Tareas**:
- [ ] **Verificar datos de entrada**:
  - Revisar `dataset_micro_hedonic_improved.csv` para outliers extremos
  - Verificar que `precio_m2` tiene valores razonables (rango esperado)
  - Verificar que no hay errores en el matching (precios incorrectos)
- [ ] **Ejecutar modelo log** (celda 10 del notebook):
  - Probar transformación logarítmica de `precio_m2`
  - Comparar métricas con modelo lineal
  - Verificar si mejora normalidad y homocedasticidad
- [ ] **Análisis de outliers**:
  - Identificar propiedades con precios extremos
  - Revisar si hay errores en datos (ej: precio total vs precio/m²)
  - Considerar filtrado de outliers extremos
- [ ] **Verificar split train/test**:
  - Revisar si el split es representativo
  - Verificar distribución de variables en train vs test

**Criterios de Evaluación** (Issue #202):
- ✅ R² ≥ 0.75
- ✅ RMSE ≤ 250 €/m²
- ✅ |mean_residual| < 100 €/m²

**Artefactos esperados**:
- Comparación visual de modelos
- Tabla comparativa de métricas
- Decisión: ¿Cuál modelo usar?

---

### 2. Comparación con Baseline MACRO ⏳ **PRIORITARIO**

**Objetivo**: Evaluar si el modelo MICRO mejora sobre el baseline MACRO

**Baseline MACRO v0.1** (Issue #203):
- R² (test 2025): **0.710**
- RMSE: **323.47 €/m²**
- Sesgo: **+203.28 €/m²**

**Comparación esperada**:
- [ ] Calcular ΔR² (MICRO - MACRO)
- [ ] Calcular ΔRMSE (MICRO - MACRO)
- [ ] Calcular ΔSesgo (MICRO - MACRO)
- [ ] Evaluar si cumple criterios Go/No-Go:
  - ΔR² ≥ +0.04
  - ΔRMSE ≤ −70 €/m²

**Artefactos esperados**:
- Tabla comparativa MACRO vs MICRO
- Visualización de mejoras
- Decisión Go/No-Go

---

### 3. Interpretación de Coeficientes ⏳ **IMPORTANTE**

**Objetivo**: Entender qué variables explican mejor el precio

**Análisis**:
- [ ] Revisar coeficientes significativos (p < 0.05)
- [ ] Interpretar efectos de:
  - `superficie_m2`: ¿Efecto positivo esperado?
  - `habitaciones`: ¿Efecto negativo (ya visto)?
  - `ano_construccion`: ¿Efecto positivo (más nuevo = más caro)?
  - `plantas`: ¿Efecto significativo?
  - `barrio_XX`: ¿Diferencias entre barrios?
- [ ] Comparar con expectativas del mercado real
- [ ] Identificar coeficientes contraintuitivos

**Artefactos esperados**:
- Tabla de coeficientes con interpretación
- Visualización de efectos principales
- Notas sobre hallazgos inesperados

---

### 4. Diagnósticos OLS Completos ⏳ **IMPORTANTE**

**Objetivo**: Validar que el modelo cumple supuestos OLS

**Tests a revisar**:
- [ ] **Normalidad** (Shapiro-Wilk): ¿Mejora con modelo log?
- [ ] **Homocedasticidad** (Breusch-Pagan): ¿Mejora con modelo log?
- [ ] **Autocorrelación** (Durbin-Watson): Ya pasa (1.8752)
- [ ] **Multicolinealidad** (VIF): Revisar VIF corregido
- [ ] **Outliers** (Cook's D): Identificar observaciones influyentes

**Criterio Issue #204**: ≥4/5 tests deben pasar

**Artefactos esperados**:
- Resumen de diagnósticos (similar a Issue #204)
- Visualizaciones de residuales
- Recomendaciones si no pasa todos los tests

---

### 5. Visualizaciones Finales ⏳ **RECOMENDADO**

**Objetivo**: Crear visualizaciones para documentación y presentación

**Visualizaciones**:
- [ ] Predicciones vs Valores Reales (scatter plot)
- [ ] Residuales vs Predicciones (homocedasticidad)
- [ ] Q-Q plot de residuales (normalidad)
- [ ] Distribución de residuales (histograma)
- [ ] Comparación MACRO vs MICRO (side-by-side)
- [ ] Coeficientes por importancia (bar chart)

**Artefactos esperados**:
- PNG de alta calidad para cada visualización
- Guardar en `data/processed/fase2/`

---

### 6. Documentación de Hallazgos ⏳ **OBLIGATORIO**

**Objetivo**: Documentar resultados y decisiones para Issue #202

**Documentos a crear/actualizar**:
- [ ] `docs/MODELO_MICRO_RESULTADOS_FINALES.md`
  - Resumen ejecutivo
  - Métricas comparativas (MACRO vs MICRO)
  - Diagnósticos OLS
  - Interpretación de coeficientes
  - Decisión Go/No-Go
- [ ] Actualizar `docs/README.md` con estado actualizado
- [ ] Actualizar `docs/ISSUE_202_FASE2_PLAN.md` con resultados

**Contenido mínimo**:
- Métricas finales del modelo seleccionado
- Comparación con baseline MACRO
- Cumplimiento de criterios Go/No-Go
- Limitaciones identificadas
- Recomendaciones para producción

---

### 7. Actualización GitHub Issue #202 ⏳ **OBLIGATORIO**

**Objetivo**: Sincronizar documentación local con GitHub

**Tareas**:
- [ ] Crear comentario en Issue #202 con:
  - Resumen ejecutivo de resultados
  - Métricas clave (R², RMSE, sesgo)
  - Comparación con MACRO
  - Decisión Go/No-Go
  - Próximos pasos
- [ ] Actualizar estado del issue si corresponde
- [ ] Agregar labels apropiados

**Formato**: Usar `docs/GITHUB_UPDATE_SNIPPETS.md` como referencia

---

### 8. Decisión Go/No-Go ✅ **COMPLETADO**

**Objetivo**: Decidir si el modelo MICRO es viable para producción

**Estado Actual**: ❌ **NO-GO** (decisión final tomada)

**Criterios Issue #202** (al menos 2 de 3):
1. ❌ R² ≥ 0.75 (actual: -0.66)
2. ❌ RMSE ≤ 250 €/m² (actual: 2,136 €/m²)
3. ⏳ |mean_residual| < 100 €/m² (pendiente calcular)

**Criterios adicionales**:
- ❌ ΔR² ≥ +0.04 (actual: -1.37 vs MACRO)
- ❌ ΔRMSE ≤ −70 €/m² (actual: +1,813 €/m² vs MACRO)
- ❌ ≥4/5 diagnósticos OLS pasan (actual: 1/4)

**Decisiones posibles**:
- ✅ **GO**: Modelo cumple criterios → Proceder a producción
- ⚠️ **GO CONDICIONAL**: Modelo cumple parcialmente → Mejoras necesarias
- ❌ **NO-GO**: Modelo no cumple criterios → Mantener MACRO v0.1 ⬅️ **ESTADO ACTUAL**

**Decisión Final**: ❌ **NO-GO**

**Razones**:
1. R² = 0.21 << objetivo de 0.75
2. RMSE = 2,113 €/m² >> objetivo de 250 €/m²
3. **Peor que baseline MACRO** (R² = 0.71, RMSE = 323 €/m²)
4. Correlaciones negativas sugieren problema fundamental

**Acciones completadas**:
1. ✅ Investigación de causas (correlaciones negativas, matching)
2. ✅ Prueba de modelo log (R² = 0.005, no mejora)
3. ✅ Revisión de calidad de datos (outliers filtrados)
4. ✅ Análisis de matching (40% de baja calidad)
5. ✅ Documentación de limitaciones (ver `MODELO_MICRO_RESULTADOS_FINALES.md`)

**Recomendación**: Mantener MACRO v0.1 como baseline operativo hasta resolver problemas fundamentales

**Artefactos esperados**:
- Documento de decisión con justificación
- Recomendaciones para próximos pasos

---

## 📊 Métricas Clave a Revisar

| Métrica | Baseline MACRO | Target MICRO | Modelo Actual |
|---------|----------------|--------------|---------------|
| **R²** | 0.710 | ≥0.75 | ⏳ Pendiente |
| **RMSE** | 323.47 €/m² | ≤250 €/m² | ⏳ Pendiente |
| **Sesgo** | +203.28 €/m² | <±100 €/m² | ⏳ Pendiente |
| **Granularidad** | Barrio×Año | Edificio | ✅ Individual |

---

## 🔄 Flujo de Trabajo Recomendado

1. **Ejecutar análisis** (Pasos 1-4)
   - Comparar modelos lineal vs log
   - Comparar con MACRO
   - Revisar diagnósticos

2. **Documentar** (Pasos 5-6)
   - Crear visualizaciones
   - Escribir documentación

3. **Comunicar** (Pasos 7-8)
   - Actualizar GitHub Issue #202
   - Decisión Go/No-Go

---

## 📝 Notas Importantes

- **Datos reales**: Este es el primer modelo entrenado con datos reales (no mock)
- **Tamaño muestra**: 393 observaciones es adecuado para modelos hedónicos
- **Match rate**: 77.8% (393/505) es excelente para matching heurístico
- **Comparación**: Es crítico comparar con MACRO para validar mejoras

---

**Última actualización**: 2025-12-20  
**Próxima revisión**: Después de ejecutar análisis de resultados

