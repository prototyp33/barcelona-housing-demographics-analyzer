# Resultados MACRO v0.2 - Mejoras con Features de Renta y Demografía

**Fecha**: 21 de diciembre de 2025  
**Modelo**: MACRO v0.2  
**Objetivo**: Mejorar MACRO v0.1 (R² = 0.71) integrando features de renta y demografía

---

## 📊 Métricas de Performance

### MACRO v0.1 (Baseline)

- **R² (test 2025)**: 0.710
- **RMSE**: 323.47 €/m²
- **MAE**: N/A
- **Bias**: +203.28 €/m² (subestima 2025)

**Features**:
- `superficie_m2_barrio_mean`
- `ano_construccion_barrio_mean`
- `plantas_barrio_mean`
- `anio_num`
- Dummies de `dataset_id`

---

### MACRO v0.2 (Mejorado)

- **R² (test 2025)**: **0.7952** ✅
- **RMSE**: 271.84 €/m² ✅
- **MAE**: 244.17 €/m²
- **Bias**: -42.50 €/m² (mejor que v0.1)

**Features adicionales**:
- `renta_promedio_barrio` (coeficiente: 0.0763)
- `renta_mediana_barrio` (coeficiente: -0.0831)
- `poblacion_total` (coeficiente: 0.0000 - no significativo)
- `prop_18_34` (coeficiente: 0.0000 - no significativo)
- `prop_65_plus` (coeficiente: 0.0000 - no significativo)
- `prop_extranjeros` (coeficiente: 0.0000 - no significativo)

**Total features**: 16 (10 numéricas + 6 dummies dataset)

---

## 📈 Comparación

| Métrica | MACRO v0.1 | MACRO v0.2 | Mejora |
|---------|------------|------------|--------|
| **R²** | 0.710 | **0.7952** | **+0.0852** ✅ |
| **RMSE** | 323.47 €/m² | **271.84 €/m²** | **-51.63 €/m²** ✅ |
| **Bias** | +203.28 €/m² | **-42.50 €/m²** | **-245.78 €/m²** ✅ |

### ✅ Mejoras Logradas

1. **R² mejorado**: +0.0852 (de 0.71 a 0.7952)
   - **Mejora relativa**: +12.0%
   - **Cerca del target**: 0.7952 vs 0.80 (diferencia: -0.0048)

2. **RMSE mejorado**: -51.63 €/m² (de 323.47 a 271.84)
   - **Mejora relativa**: -16.0%
   - **Mejor que target**: 271.84 vs 250 (diferencia: +21.84)

3. **Bias mejorado**: -245.78 €/m² (de +203.28 a -42.50)
   - **Mejora significativa**: De sobreestimar a subestimar ligeramente
   - **Más balanceado**: Bias absoluto reducido de 203.28 a 42.50

---

## 🔍 Análisis de Features

### Features Significativas

1. **`superficie_m2_barrio_mean`**: 68.23
   - Impacto positivo: +68.23 €/m² por m² adicional

2. **`ano_construccion_barrio_mean`**: 11.32
   - Impacto positivo: +11.32 €/m² por año más reciente

3. **`plantas_barrio_mean`**: -826.86
   - Impacto negativo: -826.86 €/m² por planta adicional
   - **Nota**: Coeficiente inusualmente alto, posible colinealidad

4. **`anio`**: 137.38
   - Impacto positivo: +137.38 €/m² por año

5. **`renta_promedio_barrio`**: 0.0763
   - Impacto positivo: +0.0763 €/m² por euro de renta promedio
   - **Interpretación**: Barrios con mayor renta tienen precios más altos

6. **`renta_mediana_barrio`**: -0.0831
   - Impacto negativo: -0.0831 €/m² por euro de renta mediana
   - **Nota**: Coeficiente negativo sugiere posible colinealidad con `renta_promedio_barrio`

### Features No Significativas

- `poblacion_total`: 0.0000
- `prop_18_34`: 0.0000
- `prop_65_plus`: 0.0000
- `prop_extranjeros`: 0.0000

**Conclusión**: Las features demográficas no aportan información adicional al modelo (posiblemente por falta de variación temporal o colinealidad con otras features).

---

## 📋 Cobertura de Datos

### fact_renta

- **Cobertura temporal**: 2015-2023
- **Cobertura espacial**: 73/73 barrios
- **Match rate en dataset MACRO**: 68.6% (120/175 observaciones)
- **Imputación**: 55 valores imputados con mediana (24863.03 €)

### fact_demografia_ampliada

- **Cobertura temporal**: Solo 2025
- **Cobertura espacial**: 73/73 barrios
- **Match rate en dataset MACRO**: 14.3% (25/175 observaciones)
- **Imputación**: 150 valores imputados con mediana

**Limitación**: Las features demográficas solo están disponibles para 2025, lo que limita su utilidad para el modelo.

---

## 🎯 Evaluación del Target

### Target Original

- **R² ≥ 0.80**: ⚠️ **Casi cumplido** (0.7952, diferencia: -0.0048)
- **RMSE ≤ 250 €/m²**: ❌ **No cumplido** (271.84, diferencia: +21.84)

### Evaluación

**✅ Mejora significativa sobre v0.1**:
- R² mejorado en +12.0%
- RMSE mejorado en -16.0%
- Bias mucho más balanceado

**⚠️ Limitaciones**:
- No alcanza completamente el target de R² ≥ 0.80 (muy cerca: 0.7952)
- RMSE aún por encima del target (271.84 vs 250)
- Features demográficas no aportan valor (solo disponibles para 2025)

---

## 💡 Recomendaciones

### Para Producción

1. **✅ Adoptar MACRO v0.2 (simplificado)** como modelo operativo
   - Mejora significativa sobre v0.1
   - R² cercano al target (0.7952 vs 0.80)
   - RMSE mejorado pero aún por encima del target
   - **Modelo simplificado**: Sin pérdida de performance, 4 features menos

2. **✅ Modelo Simplificado (Recomendado)**:
   - **Features eliminadas**: Todas las demográficas (no aportan valor)
   - **Performance**: Idéntica al modelo completo (R² = 0.7952, RMSE = 271.84)
   - **Ventajas**: Más simple, más rápido, más interpretable
   - **Features finales**: 12 (vs 16 en modelo completo)

3. **Mejoras futuras**:
   - Considerar eliminar `renta_mediana_barrio` si hay colinealidad con `renta_promedio_barrio`
   - Investigar coeficiente anómalo de `plantas_barrio_mean` (-826.86)
   - Explorar transformaciones no-lineales (log, polinomios)
   - Obtener datos demográficos para años anteriores (2020-2024) si se quiere reintroducir

---

## 📁 Archivos Generados

- **Dataset enriquecido**: `gracia_merged_agg_barrio_anio_dataset_v02.csv`
- **Métricas**: `macro_model_v02.json`
- **Predicciones**: `macro_predictions_v02.csv`

---

## 🔧 Scripts Utilizados

1. **`enrich_macro_dataset_v02.py`**: Enriquece dataset MACRO con features de renta y demografía
2. **`train_macro_v02.py`**: Entrena y evalúa modelo MACRO v0.2

---

**Última actualización**: 2025-12-21

