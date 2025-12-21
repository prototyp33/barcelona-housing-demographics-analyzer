# Análisis Modelo Hedonic MICRO v1.0

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Estado**: ⚠️ Modelo con bajo rendimiento

---

## 📊 Resultados Modelos Probados

### Modelo 1: Linear Regression

```
R² train:  0.2444
R² test:   0.2055  ❌ (objetivo: ≥0.75)
RMSE test: 496.76 €/m²  ❌ (objetivo: ≤250)
Bias test: 75.03 €/m²  ✅ (objetivo: ≤±100)
```

**Criterios cumplidos**: 1/5

---

### Modelo 2: Random Forest

```
R² train:  0.8271  (overfitting)
R² test:   -0.1014  ❌❌ (peor que baseline)
RMSE test: 584.88 €/m²  ❌
Bias test: 70.90 €/m²  ✅
```

**Criterios cumplidos**: 1/5

---

### Modelo 3: Gradient Boosting

```
R² train:  0.9938  (overfitting extremo)
R² test:   -0.5540  ❌❌ (muy negativo)
RMSE test: 694.74 €/m²  ❌
Bias test: 78.15 €/m²  ✅
```

**Criterios cumplidos**: 1/5

---

## 🔍 Diagnóstico de Problemas

### Problema 1: Correlaciones Muy Bajas

```
Correlaciones con precio_m2:
  superficie_m2:     -0.091  (esperado: +0.3 a +0.5)
  ano_construccion:  +0.212  (esperado: +0.2 a +0.4)
  plantas:          -0.053  (esperado: ±0.1)
  habitaciones:    -0.223  (esperado: +0.2 a +0.4)
  banos:           -0.181  (esperado: +0.1 a +0.3)
```

**Interpretación**: Las correlaciones son muy bajas o negativas, lo que sugiere:
- ❌ Datos mock pueden tener relaciones artificiales
- ❌ Variables no capturan la variabilidad real del precio
- ❌ Puede haber outliers afectando las correlaciones

---

### Problema 2: Outliers en Superficie

```
Superficie estadísticas:
  Min:  2.92 m²   ⚠️ (muy pequeño, posible error)
  Max: 473.00 m²  ⚠️ (muy grande, posible error)
  Q1:  69.0 m²
  Q3:  89.0 m²
  IQR: 20.0 m²
```

**Outliers detectados**: ~15% de observaciones fuera de rango normal (20-200 m²)

**Impacto**: Los outliers pueden estar distorsionando el modelo.

---

### Problema 3: Tamaño de Muestra Pequeño

```
Observaciones totales: 100
Train set:             80
Test set:              20  ⚠️ (muy pequeño para evaluación confiable)
Features:              11
```

**Ratio observaciones/features**: ~9:1 (recomendado: ≥10:1)

**Problema**: Con solo 20 observaciones en test, las métricas pueden ser muy volátiles.

---

### Problema 4: Overfitting en Modelos No-Lineales

- **Random Forest**: R² train 0.83 vs R² test -0.10 (diferencia enorme)
- **GBM**: R² train 0.99 vs R² test -0.55 (overfitting extremo)

**Causa**: Modelos complejos con pocos datos → memorizan el training set.

---

## 💡 Soluciones Propuestas

### Solución 1: Limpiar Outliers (Inmediato)

```python
# Filtrar observaciones con superficie fuera de rango razonable
df_clean = df[(df['superficie_m2'] >= 30) & (df['superficie_m2'] <= 200)].copy()
# Esto debería eliminar ~10-15 observaciones extremas
```

**Impacto esperado**: Mejorar correlaciones y estabilidad del modelo.

---

### Solución 2: Usar Log-Transformaciones

```python
# Transformar variables con distribución sesgada
df['log_superficie'] = np.log(df['superficie_m2'])
df['log_precio_m2'] = np.log(df['precio_m2'])
```

**Impacto esperado**: Normalizar distribuciones y mejorar relaciones lineales.

---

### Solución 3: Reducir Features (Regularización)

```python
# Usar solo features más importantes
features_minimal = ['superficie_m2', 'ano_construccion', 'barrio_id']
# O usar Lasso/Ridge para regularización automática
```

**Impacto esperado**: Reducir overfitting, mejorar generalización.

---

### Solución 4: Cross-Validation en vez de Train/Test Split

```python
# Con 100 observaciones, usar 5-fold CV en vez de 80/20 split
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5, scoring='r2')
```

**Impacto esperado**: Evaluación más robusta con datos limitados.

---

### Solución 5: Usar Datos Reales de Idealista (Cuando Lleguen)

**Problema actual**: Datos mock pueden tener relaciones artificiales.

**Solución**: Cuando lleguen credenciales API, re-entrenar con datos reales.

---

## 🎯 Recomendación Inmediata

**Para el spike (validación rápida)**:

1. ✅ **Documentar hallazgos** (este documento)
2. ✅ **Limpiar outliers** y re-entrenar
3. ✅ **Probar modelo simplificado** (solo features principales)
4. ✅ **Usar cross-validation** para evaluación más robusta

**Para producción**:

1. ⏳ Esperar datos reales de Idealista API
2. ⏳ Aumentar tamaño de muestra (≥200 observaciones)
3. ⏳ Validar con datos reales

---

## 📋 Próximos Pasos

1. **Implementar limpieza de outliers** en `train_micro_hedonic.py`
2. **Probar modelo simplificado** (solo superficie, año, barrio)
3. **Usar cross-validation** para evaluación
4. **Documentar** que resultados actuales son con datos mock

---

**Última actualización**: 2025-12-19

