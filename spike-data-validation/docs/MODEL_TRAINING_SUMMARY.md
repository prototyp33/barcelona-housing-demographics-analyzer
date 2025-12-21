# Resumen Entrenamiento Modelo Hedonic MICRO

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2

---

## ✅ Entrenamiento Completado

El modelo se ha entrenado con las recomendaciones del EDA:
- ✅ Transformación logarítmica
- ✅ Interacciones (superficie×barrio, año×barrio)
- ✅ Cross-validation (5-fold)
- ✅ Limpieza de outliers

---

## 📊 Resultados Principales

### **Configuración: Log Transform + Interacciones + CV**

```
Observaciones: 61 (después de limpiar outliers de 100)
Features: 16 (con interacciones)
Transformación: log(precio_m2), log(superficie_m2)

Métricas Test:
  R²:  -0.1983  ❌ (objetivo: ≥0.75)
  RMSE: 724.50 €/m²  ❌ (objetivo: ≤250)
  Bias: 140.64 €/m²  ❌ (objetivo: ≤±100)

Cross-Validation (5-fold):
  R²: -10.91 ± 17.47  ❌❌ (muy negativo, alta varianza)
  RMSE: 1573.09 ± 1165.09 €/m²  ❌❌ (muy alto)

Criterios cumplidos: 0/5
Decisión: ❌ NO-GO
```

---

## 🔍 Análisis de Resultados

### **Problema Principal: R² Negativo**

**Interpretación**:
- R² negativo significa que el modelo es **peor que predecir la media**
- Esto indica que los datos mock **no tienen relaciones aprendibles**
- Las correlaciones observadas (-0.091 a +0.212) son demasiado bajas

### **Problema Secundario: Alta Varianza en CV**

**Interpretación**:
- Desviación estándar enorme (17.47 en R²) indica **inestabilidad extrema**
- Con solo 48 observaciones en train y 16 features, hay **overfitting**
- Ratio observaciones/features: 3:1 (recomendado: ≥10:1)

---

## 📈 Comparación con Baseline MACRO

| Métrica | MACRO | MICRO | Delta | Status |
|---------|-------|--------|-------|--------|
| R² test | 0.710 | -0.198 | -0.908 | ❌ Peor |
| RMSE test | 323.47 | 724.50 | +401.03 | ❌ Peor |
| Bias test | 203.0 | 140.64 | -62.36 | ✅ Mejor |

**Conclusión**: El modelo MICRO es **significativamente peor** que MACRO en R² y RMSE.

---

## 💡 Conclusión para Spike

### **Pipeline Técnico**: ✅ VALIDADO

- ✅ Script de entrenamiento funciona correctamente
- ✅ Transformaciones log implementadas
- ✅ Interacciones implementadas
- ✅ Cross-validation implementada
- ✅ Métricas calculadas correctamente

### **Rendimiento del Modelo**: ❌ INADECUADO (Datos Mock)

- ❌ R² negativo (modelo inútil)
- ❌ RMSE muy alto (724 vs 250 objetivo)
- ⚠️ Resultados confirman que **datos mock no son adecuados**

---

## 🎯 Próximos Pasos

### **Inmediato**

1. ✅ Entrenamiento completado y documentado
2. ✅ Resultados guardados en JSON
3. ⏳ Actualizar Issue #202 con hallazgos

### **Cuando Lleguen Datos Reales**

1. ⏳ Extraer datos reales de Idealista API
2. ⏳ Re-ejecutar EDA para validar correlaciones
3. ⏳ Re-entrenar modelo con datos reales
4. ⏳ Comparar resultados mock vs real
5. ⏳ Validar si mejoran métricas significativamente

---

## 📝 Nota Final

**Estos resultados son esperados** dado que:
- Los datos son mock/simulados
- Las correlaciones observadas son muy bajas/negativas
- El objetivo del spike es **validar viabilidad técnica**, no optimizar métricas

**El pipeline está listo** para cuando lleguen datos reales.

---

**Última actualización**: 2025-12-19

