# Resumen Ejecutivo - EDA Modelo Hedonic MICRO

**Fecha**: 2025-12-19  
**Issue**: #202 - Fase 2  
**Notebook**: `spike-data-validation/notebooks/03_EDA_micro_hedonic.ipynb`

---

## 📊 Resumen de Datos

| Métrica | Valor |
|---------|-------|
| **Observaciones** | 100 |
| **Barrios** | 5 (Gràcia) |
| **Completitud** | 100.0% |
| **Precio/m² medio** | 4,679 €/m² |
| **Rango precio/m²** | 3,302 - 6,361 €/m² |
| **Superficie media** | 77.8 m² |
| **Rango superficie** | 2.9 - 473.0 m² |

---

## 🔍 Hallazgos Clave

### 1. Correlaciones con Precio/m²

| Variable | Correlación | Interpretación |
|----------|-------------|----------------|
| `ano_construccion` | +0.212 | ✅ Positiva (edificios más nuevos → mayor precio) |
| `superficie_m2` | -0.091 | ⚠️ Negativa débil (posible efecto de datos mock) |
| `banos` | -0.181 | ⚠️ Negativa (contraintuitiva, posible efecto mock) |
| `habitaciones` | -0.223 | ⚠️ Negativa (más habitaciones → menor precio/m²) |

**Observación crítica**: Las correlaciones negativas con `superficie_m2`, `banos` y `habitaciones` son **contraintuitivas** y probablemente se deben a que los datos son **mock/simulados**. En el mercado real, estas correlaciones deberían ser positivas o al menos no negativas.

---

### 2. Outliers

- **4 observaciones (4.0%)** con superficie >200 m²
- Rango de outliers: 289-473 m²
- **Precios/m² razonables** (4,271-4,688 €/m²) → Probablemente casos reales (áticos/dúplex) o errores de Catastro

**Recomendación**: Filtrar >200 m² o usar transformación logarítmica.

---

### 3. Interacciones

✅ **Superficie × Barrio**: Diferencias significativas entre categorías de superficie dentro del mismo barrio  
✅ **Año × Barrio**: Efecto del año de construcción varía por barrio  
✅ **Características combinadas**: Ascensor y exterior muestran efectos diferenciados

**Implicación**: Incluir interacciones en el modelo puede mejorar el R².

---

### 4. Transformaciones Logarítmicas

- **Correlación original** (superficie vs precio/m²): -0.091
- **Correlación log-transformada**: Por evaluar en el notebook
- **Recomendación**: Probar transformación log para mejorar relaciones lineales

---

### 5. Análisis Temporal

- **Año de construcción**: Efecto positivo en precio/m² (corr = +0.212)
- **Categorías de antigüedad**: Diferencias significativas entre categorías
- **Tendencia**: Edificios más nuevos tienden a ser más caros

---

## ⚠️ Limitaciones (Datos Mock)

### Problemas Identificados

1. **Correlaciones contraintuitivas**: Variables que deberían correlacionar positivamente con precio muestran correlaciones negativas
2. **Tamaño de muestra pequeño**: 100 observaciones es el mínimo para modelos hedonic
3. **Datos simulados**: Las relaciones pueden no reflejar el mercado real

### Validación Pendiente

- ⏳ **Esperar datos reales** de Idealista API para validar relaciones
- ⏳ **Re-entrenar modelo** con datos reales cuando estén disponibles
- ⏳ **Comparar resultados** mock vs real

---

## ✅ Recomendaciones para el Modelo

### Pre-procesamiento

1. **Transformaciones**:
   - ✅ Aplicar `log(superficie_m2 + 1)` y `log(precio_m2)`
   - ✅ Evaluar si mejora correlaciones

2. **Limpieza de datos**:
   - ✅ Filtrar outliers en superficie (>200 m²) O usar transformación log
   - ✅ Validar consistencia precio = precio_m2 × superficie_m2

3. **Feature Engineering**:
   - ✅ Crear interacciones: `superficie_m2 × barrio_id`
   - ✅ Crear interacciones: `ano_construccion × barrio_id`
   - ✅ Combinar características: `ascensor × exterior`

### Modelo

1. **Algoritmo**:
   - ✅ Empezar con **Linear Regression** (baseline)
   - ✅ Probar **Ridge/Lasso** para regularización
   - ⚠️ Evitar modelos complejos (RF, GBM) con muestra pequeña

2. **Validación**:
   - ✅ Usar **5-fold cross-validation** (en vez de train/test split)
   - ✅ Evaluar métricas: R², RMSE, MAE, Bias

3. **Features a incluir**:
   ```
   Variables base:
   - log(superficie_m2)
   - ano_construccion
   - habitaciones
   - banos
   - barrio_id (dummies)
   - ascensor (boolean)
   - exterior (boolean)
   
   Interacciones:
   - superficie_m2 × barrio_id
   - ano_construccion × barrio_id
   ```

---

## 📋 Próximos Pasos

### Inmediato (Con datos mock)

1. ✅ **Limpiar outliers** o aplicar transformaciones
2. ✅ **Entrenar modelo** con variables transformadas e interacciones
3. ✅ **Comparar** modelo log vs original
4. ✅ **Documentar** resultados (aunque sean con datos mock)

### Cuando lleguen datos reales

1. ⏳ **Extraer datos reales** de Idealista API
2. ⏳ **Re-ejecutar matching** Catastro ↔ Idealista
3. ⏳ **Re-entrenar modelo** con datos reales
4. ⏳ **Comparar** resultados mock vs real
5. ⏳ **Validar** si correlaciones mejoran con datos reales

---

## 📊 Métricas Objetivo

### Criterios GO/NO-GO (con datos reales)

| Métrica | Objetivo | Baseline MACRO |
|---------|----------|----------------|
| **R² test** | ≥ 0.75 | 0.71 |
| **RMSE test** | ≤ 250 €/m² | 323.47 €/m² |
| **Bias test** | ≤ ±100 €/m² | 203.0 €/m² |
| **Mejora vs MACRO** | R² +0.05, RMSE -50 €/m² | - |

---

## 🔗 Archivos Relacionados

- **Notebook EDA**: `spike-data-validation/notebooks/03_EDA_micro_hedonic.ipynb`
- **Script entrenamiento**: `spike-data-validation/scripts/fase2/train_micro_hedonic.py`
- **Datos matched**: `spike-data-validation/data/processed/fase2/catastro_idealista_matched.csv`
- **Análisis modelo**: `spike-data-validation/docs/MICRO_MODEL_ANALYSIS.md`
- **Hallazgos modelo**: `spike-data-validation/docs/MICRO_MODEL_FINDINGS.md`

---

## 📝 Notas Finales

- **Datos actuales**: Mock/simulados → Resultados no representativos del mercado real
- **Pipeline técnico**: ✅ Validado (extracción, matching, análisis funcionan)
- **Rendimiento modelo**: ⏳ Pendiente validación con datos reales
- **Próximo hito**: Obtener credenciales API Idealista y extraer datos reales

---

**Última actualización**: 2025-12-19

