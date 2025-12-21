# Resultados de Investigación: plantas_barrio_mean

**Fecha**: 21 de diciembre de 2025  
**Notebook**: `07_diagnosticos_macro_v02.ipynb` (Sección 10)

---

## 📊 Hallazgos Principales

### 1. Correlaciones

| Tipo | Valor | p-value | Interpretación |
|------|-------|---------|----------------|
| **Simple** | r = -0.4811 | p < 0.0001 | ✅ Negativa y significativa |
| **Parcial** (controlando año construcción) | r = -0.2321 | p = 0.0020 | ✅ Negativa y significativa |

**Conclusión**: 
- La correlación se reduce al controlar por año construcción (de -0.48 a -0.23)
- **Pero sigue siendo significativa** → Indica que hay un efecto directo, no solo espurio
- El efecto está parcialmente mediado por año construcción, pero no completamente

---

### 2. Comparación de Modelos

| Métrica | Con plantas | Sin plantas | Diferencia |
|---------|-------------|------------|------------|
| **R²** | 0.7944 | **0.6207** | **-0.1737** ❌ |
| **RMSE** | 272.34 €/m² | **369.92 €/m²** | **+97.58 €/m²** ❌ |

**Conclusión**: 
- ❌ **Eliminar `plantas_barrio_mean` empeora significativamente el modelo**
- Pérdida de R²: -17.37% (de 0.79 a 0.62)
- Aumento de RMSE: +97.58 €/m² (+35.8%)
- **La feature SÍ aporta valor al modelo**, a pesar del coeficiente anómalo

---

## 🔍 Interpretación del Coeficiente Anómalo

### Coeficiente: -826.86 €/m² por planta

**Análisis**:
1. **Signo negativo**: Más plantas → menor precio/m²
2. **Magnitud alta**: -826.86 €/m² es un efecto fuerte
3. **Pero el modelo es mejor con esta feature**: R² = 0.79 vs 0.62 sin ella

**Hipótesis**:
- El coeficiente puede estar capturando un **efecto no-lineal** de forma incorrecta
- La relación plantas-precio puede tener **múltiples segmentos de mercado**
- El modelo lineal puede estar promediando efectos opuestos en diferentes segmentos

---

## 💡 Interpretación Económica: Segmentos de Mercado

### Hipótesis: Dos Segmentos de Mercado

#### Segmento 1: Edificios Tradicionales (4.4-4.8 plantas)
- **Características**: Sin ascensor, barrios consolidados, arquitectura clásica
- **Target**: Familias, inversores en alquileres
- **Precio/m²**: **ALTO** (4,322 €/m²)

#### Segmento 2: Edificios de Transición (4.8-5.2 plantas)
- **Características**: Época de transición, posible degradación
- **Target**: Mercado mixto
- **Precio/m²**: **MEDIO-BAJO** (3,933 €/m²)

#### Segmento 3: Edificios Modernos Medianos (5.2-5.4 plantas)
- **Características**: Con ascensor, renovados, barrios en mejora
- **Target**: Profesionales jóvenes
- **Precio/m²**: **ALTO** (4,373 €/m²) ← Anomalía interesante

#### Segmento 4: Torres Altas (5.4-5.6 plantas)
- **Características**: Alta densidad, zonas periféricas, construidos en masa
- **Target**: Mercado masivo
- **Precio/m²**: **MÁS BAJO** (3,179 €/m²)

**Conclusión**: La relación plantas-precio es **no-lineal** y tiene múltiples segmentos.

---

## 🎯 Recomendaciones

### ✅ Mantener `plantas_barrio_mean` en el modelo

**Razones**:
1. **Aporta valor significativo**: R² mejora de 0.62 a 0.79 (+27.4%)
2. **Efecto directo confirmado**: Correlación parcial significativa (r = -0.23, p = 0.002)
3. **No es completamente espurio**: Aunque parcialmente mediado por año construcción, hay efecto directo

### ⚠️ Considerar Mejoras Futuras

1. **Transformación no-lineal**:
   - Polinomio: `plantas²` o `plantas³`
   - Splines cúbicos
   - Segmentación por rango de plantas

2. **Interacciones**:
   - `plantas × ano_construccion`: Capturar efecto diferencial por época
   - `plantas × barrio_id`: Efecto diferencial por barrio

3. **Modelos no-lineales**:
   - Random Forest (captura automáticamente no-linealidades)
   - Gradient Boosting
   - Regresión polinómica

---

## 📋 Decisión Final

### Modelo Recomendado: MACRO v0.2 Optimizado (CON plantas_barrio_mean)

**Justificación**:
- ✅ Mejor rendimiento (R² = 0.7944 vs 0.6207 sin plantas)
- ✅ Feature aporta valor significativo
- ✅ Coeficiente anómalo puede indicar relación no-lineal, pero el modelo funciona bien

**Mejoras futuras**:
- Explorar transformaciones no-lineales de `plantas_barrio_mean`
- Considerar interacciones con otras features
- Validar con modelos no-lineales (Random Forest, XGBoost)

---

## 📁 Archivos Generados

- `investigacion_plantas_summary.json` - Resumen de investigación
- `plantas_vs_precio_bivariado.png` - Análisis bivariado
- `correlacion_parcial_plantas.png` - Correlación parcial
- `plantas_precio_por_epoca.png` - Análisis por época

---

## 🔍 Fase 3: Análisis de Interacción Plantas × Ascensor

### Resultados

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Correlación plantas ↔ ascensor** | r = 0.7659 | ✅ **Alta correlación** |

**Conclusión**: 
- ✅ Edificios con más plantas tienden a tener más ascensor
- El efecto negativo de plantas puede estar parcialmente relacionado con la falta de ascensor en edificios antiguos
- **Plantas está correlacionado con ascensor** (r = 0.77)

---

## 🔍 Fase 4: Análisis de Densidad como Mediador

### Resultados

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Correlación plantas ↔ densidad** | r = 0.0797 | ❌ **Baja correlación** |
| **Correlación parcial** (controlando densidad) | r = -0.5741 | ⚠️ **Más negativa que la simple** |
| **Reducción vs correlación simple** | -19.3% | ⚠️ **Aumenta, no disminuye** |

**Conclusión**: 
- ❌ **Plantas NO es un proxy de densidad urbana** (r = 0.08, muy bajo)
- ⚠️ **Densidad NO media el efecto de plantas** (la correlación parcial es MÁS negativa que la simple)
- Al controlar por densidad, el efecto negativo de plantas se hace **más fuerte** (r = -0.57 vs -0.48)
- Esto sugiere que la densidad puede estar "ocultando" parte del efecto negativo real de plantas

**Interpretación**:
- El efecto negativo de plantas es **real y directo**, no mediado por densidad
- La densidad puede estar actuando como una variable de confusión que atenúa el efecto negativo

---

## 🎯 Conclusiones Finales sobre Mediadores

### Ascensor (Fase 3)
- ✅ **Alta correlación** (r = 0.77): Más plantas → más ascensor
- **Implicación**: El efecto negativo de plantas puede estar relacionado con la falta de ascensor en edificios antiguos altos

### Densidad (Fase 4)
- ❌ **Baja correlación** (r = 0.08): Plantas NO es proxy de densidad
- ⚠️ **No media el efecto**: La correlación parcial es más negativa que la simple
- **Implicación**: El efecto negativo de plantas es directo, no mediado por densidad

---

**Última actualización**: 2025-12-21

