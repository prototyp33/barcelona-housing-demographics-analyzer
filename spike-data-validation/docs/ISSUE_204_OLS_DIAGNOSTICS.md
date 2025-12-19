# Issue #204 - Diagnósticos OLS baseline MACRO v0.1 (Structural-only)

## 🎯 Objetivo

Validar los supuestos clásicos de OLS sobre el baseline macro v0.1 (modelo **Structural-only**) para el spike de Gràcia.

Target de la issue: **≥4/5 tests OLS pasan**.

## 📦 Dataset y modelo analizado

- Dataset: `spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv`
- Nivel: `barrio_id × anio × dataset_id` (175 observaciones)
- Modelo:
  - Estructurales: `superficie_m2_barrio_mean`, `ano_construccion_barrio_mean`, `plantas_barrio_mean`
  - Tendencia temporal: `anio_num`
  - Dummies dataset: `ds_*` (con `drop_first=True`)
  - Target: `precio_m2_mean`

## 📊 Resultados globales del modelo

- Observaciones: **175**
- **R² = 0.871**
- **RMSE ≈ 229.0 €/m²**

Fuente: `spike-data-validation/data/logs/ols_diagnostics_macro_204.json`  
Script: `spike-data-validation/scripts/ols_diagnostics_macro_204.py`

## ✅ / ❌ Tests OLS ejecutados

### 1. Normalidad (Shapiro–Wilk) ✅

- Statistic \(W\) = **0.987**
- **p-value = 0.1003 > 0.05**
- **Conclusión**: No se rechaza normalidad de los residuos (aceptable para OLS).

### 2. Homocedasticidad (Breusch–Pagan) ❌

- LM statistic = **24.96**
- **p-value = 0.0030 < 0.05**
- **Conclusión**: Evidencia de heterocedasticidad (varianza de residuos no constante).

### 3. Multicolinealidad (VIF) ✅

- VIF máximo (sin intercept) ≈ **2.54** (`ano_construccion_barrio_mean`)
- Resto de VIFs entre ~1 y ~2.
- Umbral: max VIF < 10.
- **Conclusión**: No hay problema serio de multicolinealidad entre features.

### 4. Autocorrelación (Durbin–Watson) ❌

- **DW = 1.48** (umbral aceptable ~[1.5, 2.5])
- **Conclusión**: Autocorrelación positiva en los residuos (típico en series temporales).

### 5. Outliers / Influencia (Cook’s distance) ❌

- Umbral: \(4/n ≈ 0.0229\)
- Observaciones con Cook’s D > 4/n: **13**
- **Conclusión**: Hay varios puntos altamente influyentes.

## 📌 Resumen criterio Issue #204

- Tests OK: **2/5**
- Criterio objetivo: **≥4/5 tests pasan**
- `criterion_met = False`

**Conclusión**: El baseline OLS MACRO v0.1 es útil a nivel exploratorio, pero **NO cumple** los supuestos OLS de forma suficiente como para usarlo como modelo OLS “canónico” sin correcciones.

## 🧭 Implicaciones y recomendaciones

- Para análisis exploratorio y como baseline de performance, el modelo es **aceptable** si se documentan estas limitaciones.
- Para usos de producción / inferencia estadística:
  - Usar **errores estándar robustos** (HC3) para los coeficientes.
  - Considerar modelos robustos (RLM/Huber) o limpieza de outliers basados en Cook’s D.
  - Explorar modelos que tengan en cuenta autocorrelación temporal (GLS o estructura en los residuos).

## 🧪 Artefactos generados

- JSON resumen diagnósticos:  
  `spike-data-validation/data/logs/ols_diagnostics_macro_204.json`
- Q–Q plot residuos:  
  `spike-data-validation/data/logs/ols_qqplot_residuals_204.png`
- Residuos vs Fitted:  
  `spike-data-validation/data/logs/ols_resid_vs_fitted_204.png`


