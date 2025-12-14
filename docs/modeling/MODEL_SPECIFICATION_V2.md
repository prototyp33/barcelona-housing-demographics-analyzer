# Modelo Hedónico v2.0 - Especificación Técnica

**Versión:** 2.0  
**Última actualización:** Diciembre 2025  
**Barrio Piloto:** Gràcia (Spike)

---

## Resumen Ejecutivo

El modelo hedónico de precios de vivienda estima el valor de una propiedad basándose en sus características intrínsecas y de ubicación. Esta especificación define la ecuación del modelo, variables incluidas, y criterios de validación para v2.0 y releases futuros.

**Target R²:** ≥0.55 (v2.0), ≥0.65 (v2.1+)

---

## Especificación Base (v2.0)

### Ecuación del Modelo

```
ln(precio) = β₀ + β₁·ln(superficie) + β₂·antiguedad + β₃·plantas + β₄·ascensor + β₅·distancia_centro + β₆·barrio_id + ε
```

### Variables Incluidas

| Variable | Tipo | Transformación | Fuente | Disponibilidad |
|----------|------|----------------|--------|----------------|
| `precio` | Dependiente | ln() | `fact_precios` | ✅ |
| `superficie` | Independiente | ln() | Catastro/INE | ✅ |
| `antiguedad` | Independiente | Lineal | `fact_demografia.ano_construccion` | ✅ |
| `plantas` | Independiente | Lineal | Catastro | ⚠️ Parcial |
| `ascensor` | Independiente | Binaria (0/1) | Catastro | ⚠️ Parcial |
| `distancia_centro` | Independiente | Lineal | Calculada desde `dim_barrios.geometry` | ✅ |
| `barrio_id` | Independiente | Categórica (dummy) | `dim_barrios` | ✅ |

### Justificación de Transformaciones

**Log-log para precio y superficie:**
- Permite interpretar coeficientes como elasticidades
- Reduce heterocedasticidad
- Mejora normalidad de residuos

**Antigüedad lineal:**
- Efecto constante por año (no exponencial)
- Más interpretable económicamente

**Distancia al centro:**
- Calculada como distancia euclidiana desde centroide del barrio a Plaza Catalunya
- Usando PostGIS: `ST_Distance(geometry, ST_SetSRID(ST_MakePoint(2.1734, 41.3851), 4326))`

---

## Variables Expandidas (v2.1+)

### v2.1 Enhanced Analytics

**Variables adicionales:**

```
ln(precio) = β₀ + β₁·ln(superficie) + β₂·antiguedad + β₃·plantas + β₄·ascensor + 
             β₅·distancia_centro + β₆·barrio_id + 
             β₇·ln(renta_disponible) + β₈·tasa_desempleo + β₉·euribor + ε
```

| Variable | Tipo | Transformación | Fuente | Prioridad |
|----------|------|----------------|--------|-----------|
| `renta_disponible` | Independiente | ln() | `fact_renta_historica` | Muy Alta |
| `tasa_desempleo` | Independiente | Lineal | Open Data BCN | Alta |
| `euribor` | Independiente | Lineal | Banco de España | Muy Alta |

### v2.2+ Advanced Features

**Variables adicionales:**

- `eficiencia_energetica` (categórica: A-G)
- `num_hut` (número de viviendas uso turístico)
- `proximidad_servicios` (índice calculado)
- `calidad_aire` (índice)

---

## Criterios de Validación

### Criterios de Éxito (Go/No-Go)

| Criterio | Target v2.0 | Target v2.1+ | Método de Validación |
|----------|-------------|--------------|----------------------|
| R² Ajustado | ≥0.55 | ≥0.65 | `statsmodels.OLS().fit().rsquared_adj` |
| Match Rate | ≥70% | ≥70% | `matched_records / total_records` |
| Sample Size | ≥100 | ≥200 | `len(df)` |
| OLS Assumptions | ≥4/5 | ≥4/5 | Tests diagnósticos |
| Coeficientes Plausibles | Sí | Sí | Revisión manual de signos |

### Tests de Supuestos OLS

1. **Normalidad de Residuos**
   - Test: Shapiro-Wilk
   - Criterio: p-value > 0.05
   - Visualización: Q-Q plot

2. **Homocedasticidad**
   - Test: Breusch-Pagan
   - Criterio: p-value > 0.05
   - Visualización: Residuals vs Fitted plot
   - Mitigación: Robust standard errors (HC3) si falla

3. **No Multicolinealidad**
   - Test: Variance Inflation Factor (VIF)
   - Criterio: VIF < 5 para todas las variables
   - Mitigación: Eliminar variable con mayor VIF

4. **No Autocorrelación**
   - Test: Durbin-Watson
   - Criterio: 1.5 < DW < 2.5
   - Nota: Menos crítico para datos cross-sectional

5. **Outliers e Influential Points**
   - Test: Cook's Distance
   - Criterio: Cook's D < 1
   - Visualización: Leverage plot

---

## Interpretación de Coeficientes

### Coeficientes Log-Log (Elasticidades)

**Ejemplo:** `β₁ = 0.85` para `ln(superficie)`

**Interpretación:**
- Un aumento del 1% en superficie aumenta el precio en 0.85%
- Elasticidad precio-superficie: 0.85 (inelástica)

### Coeficientes Lineales

**Ejemplo:** `β₂ = -500` para `antiguedad`

**Interpretación:**
- Cada año adicional de antigüedad reduce el precio en 500€
- Efecto marginal constante

### Coeficientes Binarios

**Ejemplo:** `β₄ = 15,000` para `ascensor`

**Interpretación:**
- Tener ascensor aumenta el precio en 15,000€
- Efecto fijo (no proporcional)

---

## Implementación Técnica

### Librería

**statsmodels** (Python)

```python
import statsmodels.api as sm

# Preparar datos
X = df[['ln_superficie', 'antiguedad', 'plantas', 'ascensor', 'distancia_centro']]
X = sm.add_constant(X)  # Agregar intercept
y = df['ln_precio']

# Estimar modelo
model = sm.OLS(y, X).fit()

# Resultados
print(model.summary())
print(f"R² Ajustado: {model.rsquared_adj:.3f}")
```

### Validación de Supuestos

```python
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.outliers_influence import variance_inflation_factor

# 1. Normalidad
stat, p_value = stats.shapiro(model.resid)
print(f"Shapiro-Wilk: p={p_value:.4f}")

# 2. Homocedasticidad
bp_stat, bp_pvalue, _, _ = het_breuschpagan(model.resid, X)
print(f"Breusch-Pagan: p={bp_pvalue:.4f}")

# 3. VIF
vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif_data)

# 4. Durbin-Watson
dw_stat = durbin_watson(model.resid)
print(f"Durbin-Watson: {dw_stat:.3f}")
```

---

## Modelos Alternativos Considerados

### Robust Linear Model (RLM)

**Cuándo usar:** Si homocedasticidad falla

```python
from statsmodels.robust.robust_linear_model import RLM

model_rlm = RLM(y, X).fit()
```

### Random Forest (v2.2+)

**Cuándo usar:** Si relaciones no lineales son importantes

```python
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(n_estimators=100, max_depth=10)
rf.fit(X, y)
```

**Trade-off:** Mejor R² pero menos interpretable

---

## Limitaciones Conocidas

### v2.0

1. **Match Rate:** Si <70%, modelo a nivel barrio-mes (no transacción)
2. **Variables Faltantes:** Renta, Euribor no incluidos inicialmente
3. **Temporalidad:** Modelo estático (no considera tendencias temporales)

### Mitigaciones Planificadas

- v2.1: Agregar variables económicas críticas
- v2.2: Modelo con efectos temporales (panel data)
- v3.0: Modelo de machine learning como alternativa

---

## Referencias

- **Variables Catalog:** `docs/modeling/HEDONIC_VARIABLES.md`
- **Spike Notebook:** `spike-data-validation/notebooks/01-gracia-hedonic-model.ipynb`
- **Database Schema:** `docs/architecture/DATABASE_SCHEMA_V2.md`

---

**Última actualización:** Diciembre 2025

