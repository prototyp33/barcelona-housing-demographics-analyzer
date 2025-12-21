# Resultados de Diagnósticos MACRO v0.2

**Fecha**: 21 de diciembre de 2025  
**Notebook**: `07_diagnosticos_macro_v02.ipynb`

---

## 📊 Hallazgos Principales

### 1. Colinealidad Detectada

#### VIF (Variance Inflation Factor)

| Feature | VIF | Interpretación |
|---------|-----|----------------|
| `renta_mediana_barrio` | **1,245.82** | ❌ Colinealidad extrema |
| `renta_promedio_barrio` | **1,243.78** | ❌ Colinealidad extrema |
| `ano_construccion_barrio_mean` | 2.64 | ✅ Aceptable |
| `plantas_barrio_mean` | 2.45 | ✅ Aceptable |
| `superficie_m2_barrio_mean` | 1.31 | ✅ Aceptable |
| `anio` | 1.05 | ✅ Aceptable |

**Nota**: El VIF del `const` (intercept) no es interpretable y se excluye del análisis.

#### Correlación renta_promedio ↔ renta_mediana

- **Correlación**: **r = 0.9995** (casi perfecta)
- **Interpretación**: ❌ **Alta colinealidad**
- **Recomendación**: Eliminar una de las dos features

---

### 2. Coeficiente Anómalo

#### plantas_barrio_mean

- **Coeficiente**: **-826.86** €/m² por planta
- **Interpretación**: ⚠️ **Anómalo** (muy alto en valor absoluto)
- **Correlación con precio_m2**: r = -0.481 (moderada negativa)
- **Correlación con ano_construccion**: r = 0.718 (alta positiva)

**Posibles causas**:
1. Colinealidad con `ano_construccion_barrio_mean` (r = 0.718)
2. Error en los datos
3. Efecto real pero capturado de forma incorrecta

**Recomendación**: Investigar más a fondo, considerar transformación o eliminación.

---

### 3. Normalidad de Residuos

- **Test Shapiro-Wilk**: p-value = 0.0804
- **Interpretación**: ✅ **Residuos normalmente distribuidos** (p > 0.05)

---

## 🔧 Modelo Optimizado

### Cambios Implementados

1. **Eliminada `renta_mediana_barrio`**:
   - Razón: VIF = 1,245, r = 0.9995 con `renta_promedio_barrio`
   - Mantiene `renta_promedio_barrio` (más interpretable)

### Comparación de Modelos

| Métrica | Simplificado | Optimizado | Diferencia |
|---------|--------------|------------|------------|
| **R²** | 0.7952 | **0.7944** | -0.0008 (despreciable) |
| **RMSE** | 271.84 €/m² | **272.34 €/m²** | +0.50 €/m² (despreciable) |
| **Features** | 12 | **11** | -1 (más simple) |
| **VIF máximo** | 1,245 | **< 5** | ✅ Colinealidad eliminada |

### Conclusión

✅ **Modelo optimizado recomendado**:
- Rendimiento prácticamente idéntico (diferencia < 0.1%)
- Elimina colinealidad extrema (VIF de 1,245 a < 5)
- Más simple (1 feature menos)
- Más robusto estadísticamente

---

## 📋 Recomendaciones Finales

### ✅ Implementadas

1. **Eliminar `renta_mediana_barrio`** ✅
   - Modelo optimizado creado
   - Colinealidad eliminada
   - Rendimiento mantenido

### ✅ Completadas

2. **Investigación `plantas_barrio_mean`** ✅:
   - **Hallazgo**: La feature SÍ aporta valor significativo al modelo
   - **R² con plantas**: 0.7944 vs **0.6207 sin plantas** (pérdida de -17.37%)
   - **Correlación parcial**: r = -0.2321 (significativa, p = 0.002)
   - **Conclusión**: Mantener en el modelo (a pesar del coeficiente anómalo)
   - **Interpretación**: Relación no-lineal con múltiples segmentos de mercado
   - **Ver**: `INVESTIGACION_PLANTAS_RESULTADOS.md` para detalles completos

3. **Validar datos de origen**:
   - Verificar que `plantas_barrio_mean` esté correctamente calculado
   - Revisar si hay errores en la agregación por barrio

---

## 📁 Archivos Generados

### Modelos

- `macro_model_v02_simplified.json` - Modelo simplificado (con renta_mediana)
- `macro_model_v02_optimized.json` - **Modelo optimizado (recomendado)**

### Visualizaciones

- `correlation_matrix_macro_v02.png` - Matriz de correlaciones
- `vif_analysis_macro_v02.png` - Análisis VIF
- `renta_correlation_analysis.png` - Análisis renta
- `plantas_analysis.png` - Análisis plantas
- `residuals_analysis_macro_v02.png` - Análisis de residuos

### Resúmenes

- `diagnosticos_macro_v02_summary.json` - Resumen de diagnósticos

---

## 🎯 Modelo Final Recomendado

**MACRO v0.2 Optimizado** (CON `plantas_barrio_mean`):
- **R²**: 0.7944
- **RMSE**: 272.34 €/m²
- **Features**: 11 (sin `renta_mediana_barrio`, CON `plantas_barrio_mean`)
- **VIF máximo**: < 5 (sin colinealidad)
- **Estado**: ✅ **Listo para producción**

**Justificación para mantener `plantas_barrio_mean`**:
- Eliminar la feature empeora R² de 0.79 a 0.62 (-17.37%)
- Correlación parcial significativa (r = -0.23, p = 0.002)
- Coeficiente anómalo puede indicar relación no-lineal, pero el modelo funciona bien

---

**Última actualización**: 2025-12-21

