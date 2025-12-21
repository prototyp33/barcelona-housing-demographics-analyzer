# Resultados Entrenamiento Modelo Hedonic MICRO

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Script**: `spike-data-validation/scripts/fase2/train_micro_hedonic.py`

---

## 📊 Resumen Ejecutivo

### **Estado General**: ❌ NO-GO

El modelo MICRO con datos mock **no cumple los criterios** de rendimiento. Los resultados confirman que los datos mock tienen relaciones artificiales que no permiten un modelo útil.

---

## 🔍 Resultados por Configuración

### **Configuración 1: Log Transform + Interacciones + CV**

```
Observaciones: 61 (después de limpiar outliers)
Features: ~20 (con interacciones)
Transformación: log(precio_m2), log(superficie_m2)
Interacciones: superficie×barrio, año×barrio

Métricas:
  R² test:  -0.1983  ❌ (objetivo: ≥0.75)
  RMSE test: 724.50 €/m²  ❌ (objetivo: ≤250)
  Bias test: 140.64 €/m²  ❌ (objetivo: ≤±100)
  
Cross-validation (5-fold):
  R² (original): -10.91 ± 17.47  ❌❌ (muy negativo, alta varianza)
  RMSE (original): 1573.09 ± 1165.09 €/m²  ❌❌ (muy alto)

Criterios cumplidos: 0/5
```

**Interpretación**: 
- R² negativo indica que el modelo es **peor que predecir la media**
- Alta varianza en CV indica **inestabilidad extrema**
- Conclusión: **Datos mock no son adecuados para modelo**

---

### **Configuración 2: Sin Log Transform + Sin Interacciones**

```
Observaciones: 61
Features: ~11 (sin interacciones)
Transformación: ninguna
Interacciones: ninguna

Métricas esperadas: (por ejecutar)
```

---

### **Configuración 3: Log Transform + Sin Interacciones**

```
Observaciones: 61
Features: ~11 (sin interacciones)
Transformación: log(precio_m2), log(superficie_m2)
Interacciones: ninguna

Métricas esperadas: (por ejecutar)
```

---

## 📈 Comparación con Baseline MACRO

| Métrica | MACRO Baseline | MICRO (Log+Inter) | Delta | Status |
|---------|---------------|-------------------|-------|--------|
| **R² test** | 0.710 | -0.198 | -0.908 | ❌ Peor |
| **RMSE test** | 323.47 €/m² | 724.50 €/m² | +401.03 | ❌ Peor |
| **Bias test** | 203.0 €/m² | 140.64 €/m² | -62.36 | ✅ Mejor |

**Conclusión**: El modelo MICRO es **significativamente peor** que el baseline MACRO en R² y RMSE.

---

## 🔍 Análisis de Problemas

### **Problema 1: R² Negativo**

**Causa**: 
- Datos mock tienen correlaciones muy bajas/negativas
- Modelo no puede aprender patrones reales
- Con transformación log + interacciones, hay demasiadas features para pocos datos

**Evidencia**:
- Correlaciones observadas: -0.091 a +0.212 (muy bajas)
- R² negativo en test y CV

---

### **Problema 2: Alta Varianza en Cross-Validation**

**Causa**:
- Muestra pequeña (61 observaciones)
- Muchas features (~20 con interacciones)
- Ratio observaciones/features: ~3:1 (recomendado: ≥10:1)

**Evidencia**:
- CV R²: -10.91 ± 17.47 (desviación estándar enorme)
- CV RMSE: 1573.09 ± 1165.09 €/m² (desviación estándar enorme)

---

### **Problema 3: Overfitting**

**Causa**:
- R² train (0.39) > R² test (-0.20) → Overfitting
- Modelo memoriza training set pero no generaliza

---

## 💡 Conclusiones

### **Para Datos Mock**

1. ✅ **Pipeline técnico funciona**: El script se ejecuta sin errores
2. ❌ **Rendimiento inadecuado**: R² negativo, RMSE muy alto
3. ⚠️ **Datos mock limitan modelo**: Correlaciones artificiales no permiten aprendizaje

### **Recomendaciones**

1. **Inmediato**:
   - ✅ Documentar que resultados son con datos mock
   - ✅ Validar que pipeline funciona técnicamente
   - ⏳ Esperar datos reales de Idealista API

2. **Con Datos Reales**:
   - Re-ejecutar EDA para validar correlaciones
   - Re-entrenar modelo con datos reales
   - Comparar resultados mock vs real
   - Validar si mejoran métricas

---

## 📋 Próximos Pasos

1. ✅ **Entrenamiento completado** (con datos mock)
2. ✅ **Resultados documentados**
3. ⏳ **Esperar datos reales** de Idealista API
4. ⏳ **Re-entrenar** con datos reales cuando estén disponibles

---

## 🔗 Archivos Relacionados

- **Script entrenamiento**: `spike-data-validation/scripts/fase2/train_micro_hedonic.py`
- **Resultados JSON**: `spike-data-validation/data/processed/fase2/micro_hedonic_linear_results.json`
- **EDA**: `spike-data-validation/notebooks/03_EDA_micro_hedonic.ipynb`
- **Análisis modelo**: `spike-data-validation/docs/MICRO_MODEL_ANALYSIS.md`

---

**Última actualización**: 2025-12-19  
**Nota**: Estos resultados son con datos mock. Rendimiento real se evaluará con datos de Idealista API.

