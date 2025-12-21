# MACRO v0.2 Simplificado - Modelo Final Recomendado

**Fecha**: 21 de diciembre de 2025  
**Modelo**: MACRO v0.2 (simplificado)  
**Estado**: ✅ **Modelo operativo recomendado**

---

## 📊 Resumen Ejecutivo

El modelo MACRO v0.2 se ha simplificado eliminando features demográficas que no aportan valor. El modelo simplificado mantiene **exactamente el mismo rendimiento** que el modelo completo, pero con **4 features menos** (12 vs 16).

**Decisión**: ✅ **Adoptar modelo simplificado como modelo operativo**

---

## 📈 Métricas de Performance

### MACRO v0.2 Simplificado

- **R² (test 2025)**: **0.7952** ✅
- **RMSE**: **271.84 €/m²** ✅
- **MAE**: 244.17 €/m²
- **Bias**: -42.50 €/m²
- **Features**: 12 (vs 16 en modelo completo)

### Comparación con Modelo Completo

| Métrica | Con Demografía | Simplificado | Diferencia |
|---------|----------------|--------------|------------|
| **R²** | 0.7952 | **0.7952** | **0.0000** ✅ |
| **RMSE** | 271.84 €/m² | **271.84 €/m²** | **0.00 €/m²** ✅ |
| **MAE** | 244.17 €/m² | **244.17 €/m²** | **0.00 €/m²** ✅ |
| **Features** | 16 | **12** | **-4** ✅ |

**Conclusión**: ✅ **Modelo simplificado es equivalente sin pérdida de performance**

---

## 🔍 Features del Modelo Simplificado

### Features Estructurales (3)

1. **`superficie_m2_barrio_mean`**: 68.23
   - Impacto: +68.23 €/m² por m² adicional

2. **`ano_construccion_barrio_mean`**: 11.32
   - Impacto: +11.32 €/m² por año más reciente

3. **`plantas_barrio_mean`**: -826.86
   - Impacto: -826.86 €/m² por planta adicional
   - **⚠️ Nota**: Coeficiente inusualmente alto, posible colinealidad

### Features de Renta (2)

4. **`renta_promedio_barrio`**: 0.0763
   - Impacto: +0.0763 €/m² por euro de renta promedio
   - **Interpretación**: Barrios con mayor renta tienen precios más altos

5. **`renta_mediana_barrio`**: -0.0831
   - Impacto: -0.0831 €/m² por euro de renta mediana
   - **⚠️ Nota**: Coeficiente negativo sugiere posible colinealidad con `renta_promedio_barrio`

### Features Temporales (1)

6. **`anio`**: 137.38
   - Impacto: +137.38 €/m² por año

### Dummies de Dataset (6)

- `dataset_bxtvnxvukh`: -468.08
- `dataset_cq4causxvu`: 95.87
- `dataset_idjhkx1ruj`: -394.70
- `dataset_mrslyp5pcq`: -516.84
- `dataset_u25rr7oxh6`: 125.42
- (Una dummy omitida como referencia)

### Features Eliminadas (4)

- ❌ `poblacion_total` (coeficiente: 0.0000)
- ❌ `prop_18_34` (coeficiente: 0.0000)
- ❌ `prop_65_plus` (coeficiente: 0.0000)
- ❌ `prop_extranjeros` (coeficiente: 0.0000)

**Razón**: Todas tenían coeficientes ≈ 0, no aportan información al modelo.

---

## 📋 Comparación con Versiones Anteriores

| Versión | R² | RMSE | Features | Estado |
|---------|----|------|----------|--------|
| **MACRO v0.1** | 0.710 | 323.47 €/m² | 9 | Baseline |
| **MACRO v0.2 (completo)** | 0.7952 | 271.84 €/m² | 16 | Mejorado |
| **MACRO v0.2 (simplificado)** | **0.7952** | **271.84 €/m²** | **12** | ✅ **Recomendado** |

### Mejora sobre v0.1

- **R²**: +0.0852 (+12.0%)
- **RMSE**: -51.63 €/m² (-16.0%)
- **Bias**: -245.78 €/m² (mucho más balanceado)

---

## ⚠️ Actualización: Modelo Optimizado Disponible

**Nota**: Después de los diagnósticos, se creó un **modelo optimizado** que elimina `renta_mediana_barrio` por alta colinealidad (VIF = 1,245, r = 0.9995).

**Ver**: `MACRO_V02_DIAGNOSTICOS_RESULTADOS.md` para detalles completos.

**Modelo recomendado**: **MACRO v0.2 Optimizado** (R² = 0.7944, RMSE = 272.34 €/m², 11 features)

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
- Modelo más simple y eficiente

**⚠️ Limitaciones**:
- No alcanza completamente el target de R² ≥ 0.80 (muy cerca: 0.7952)
- RMSE aún por encima del target (271.84 vs 250)

---

## 💡 Ventajas del Modelo Simplificado

1. **✅ Mismo rendimiento**: Sin pérdida de performance
2. **✅ Más simple**: 4 features menos (25% reducción)
3. **✅ Más rápido**: Menos cálculos en inferencia
4. **✅ Más interpretable**: Menos variables para analizar
5. **✅ Menos dependencias**: No requiere datos demográficos (solo disponibles para 2025)

---

## 🔧 Uso del Modelo

### Script de Entrenamiento

```bash
# Modelo simplificado (recomendado, por defecto)
python3 spike-data-validation/scripts/train_macro_v02.py \
    --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv \
    --report spike-data-validation/data/logs/macro_model_v02_simplified.json

# Modelo completo (con demografía, si se necesita)
python3 spike-data-validation/scripts/train_macro_v02.py \
    --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv \
    --report spike-data-validation/data/logs/macro_model_v02.json \
    --with-demo
```

### Archivos Generados

- **Métricas**: `macro_model_v02_simplified.json`
- **Predicciones**: `macro_predictions_v02_simplified.csv`

---

## 📁 Archivos Relacionados

- **Script de enriquecimiento**: `enrich_macro_dataset_v02.py`
- **Script de entrenamiento**: `train_macro_v02.py`
- **Dataset enriquecido**: `gracia_merged_agg_barrio_anio_dataset_v02.csv`
- **Documentación completa**: `MACRO_V02_RESULTADOS.md`

---

## 🚀 Próximos Pasos

1. **✅ Adoptar modelo simplificado** como modelo operativo
2. **Validar colinealidad**: Revisar `renta_promedio_barrio` vs `renta_mediana_barrio`
3. **Investigar coeficiente anómalo**: `plantas_barrio_mean` = -826.86
4. **Explorar mejoras**: Transformaciones no-lineales, más features de renta

---

**Última actualización**: 2025-12-21

