# Issue #202 - Investigación Completa: Matching y Correlaciones Negativas

**Fecha**: 21 de diciembre de 2025  
**Estado**: ✅ Investigación completada  
**Decisión**: ⚠️ NO-GO para MICRO con modelo lineal, mantener MACRO baseline

---

## 📋 Resumen Ejecutivo

Se implementaron múltiples estrategias de matching (geográfico, por edificio, por cuadrícula) y se investigó a fondo el problema de correlaciones negativas. **Hallazgo principal**: El mercado de Gràcia tiene una curva de demanda no-lineal que no puede ser capturada por modelos lineales OLS. **Recomendación**: Mantener MACRO baseline (R² = 0.71) como solución de producción.

---

## 🔍 Estrategias de Matching Implementadas

### 1. Matching Geográfico (Coordenadas) ✅

**Implementación**:
- Geocoding de 429/505 direcciones Idealista (85%)
- Matching por distancia geográfica (Haversine)
- Combinación con matching heurístico (score ponderado)

**Resultados**:
- Match rate: 62% (254/410 propiedades dentro de rango Gràcia)
- Distancia promedio: 103.6 m
- **Correlación superficie**: -0.239 ❌ (PEOR que heurístico -0.024)
- **Correlación habitaciones**: -0.273 ❌ (PEOR que heurístico -0.166)

**Conclusión**: ⚠️ Matching geográfico preciso no mejora correlaciones, las empeora.

---

### 2. Matching por Edificio ✅

**Implementación**:
- Agrupar Catastro por `referencia_catastral` (edificio completo)
- Agregar características (media de superficie, año, plantas)
- Matching geográfico Idealista → edificio más cercano

**Resultados**:
- Match rate: 99.8% (596/597)
- Distancia promedio: 140.1 m
- **Correlación superficie**: -0.037 ❌ (similar a heurístico)
- **Correlación habitaciones**: -0.183 ❌ (similar a heurístico)

**Conclusión**: ⚠️ Mejora match rate pero no resuelve correlaciones negativas.

---

### 3. Matching por Cuadrícula Geográfica ⚠️

**Implementación**:
- Dividir área en cuadrículas 100m × 100m
- Agregar Idealista y Catastro por cuadrícula
- Matching: cuadrícula Idealista → cuadrícula Catastro

**Resultados**:
- Match rate: 10.3% (3/29 cuadrículas) ❌

**Conclusión**: ❌ No viable (cuadrículas no se alinean bien).

---

## 📊 Comparación de Estrategias

| Estrategia | Match Rate | Correlación superficie | Correlación habitaciones | Viabilidad |
|-----------|------------|------------------------|--------------------------|------------|
| **Heurístico** | 100% | -0.024 | -0.166 | ✅ Baseline |
| **Geográfico Individual** | 62% | -0.239 | -0.273 | ❌ Empeora |
| **Por Edificio** | 99.8% | -0.037 | -0.183 | ⚠️ Similar |
| **Por Cuadrícula** | 10.3% | N/A | N/A | ❌ No viable |
| **MACRO (barrio)** | 100% | N/A | N/A | ✅ R² = 0.71 |

**Conclusión**: Ninguna estrategia de matching individual mejora las correlaciones. MACRO sigue siendo la mejor opción.

---

## 🔬 Investigación de Datos

### Análisis de Precios Idealista ✅

- **Precio/m² mediano**: 5,515 €/m² ✅ (dentro del rango esperado 4,500-6,500 €/m²)
- **Outliers altos**: 8.3% (42 propiedades > 10,017 €/m²)
- **Outliers bajos**: 0.2% (1 propiedad < 1,323 €/m²)

**Conclusión**: Precios son razonables en general.

---

### Análisis de Características Catastro ✅

- **Superficie mediana**: 80.0 m² ✅ (dentro del rango esperado 60-120 m²)
- **Año construcción mediano**: 1972
- **Outliers**: 2.7% en superficie (valores extremos: 1.1 m², 988 m²)

**Conclusión**: Características son razonables en general.

---

### Análisis de Correlaciones por Grupos

**Curva Precio/m² vs Superficie**:

| Superficie | Observaciones | Precio/m² Medio | Interpretación |
|------------|---------------|-----------------|----------------|
| <50 m²     | 76            | 6,508 €/m²      | Estudios/lofts premium |
| 50-70 m²   | 110           | 6,629 €/m²      | Viviendas pequeñas |
| 70-90 m²   | 124           | 5,968 €/m²      | Viviendas estándar |
| 90-110 m²  | 111           | 5,903 €/m²      | Viviendas estándar (economías de escala) |
| 100-150 m² | 111           | 5,903 €/m²      | Viviendas grandes |
| >150 m²    | 84            | 6,846 €/m²      | Viviendas de lujo |

**Hallazgo crítico**: 
- Propiedades **medianas (90-110m²)** tienen precio/m² **más bajo** (5,903 €/m²)
- Propiedades **pequeñas (<50m²)** tienen precio/m² **más alto** (6,508 €/m²)
- Propiedades **grandes (>150m²)** tienen precio/m² **más alto** (6,846 €/m²)

**Esto explica la correlación negativa**: El mercado tiene una **curva de demanda no-lineal** donde las propiedades medianas tienen mejor relación precio/tamaño.

---

### Limpieza de Datos

**Filtros aplicados**:
- Duplicados: 43 eliminados (8.5%)
- No-residenciales: 39 eliminados (8.4%)
- Outliers: 42 eliminados (9.9%)
- Matches baja calidad: 149 eliminados (39.1%)

**Total eliminado**: 273 observaciones (54.1%)

**Resultado**:
- Dataset limpio: 232 observaciones
- **Correlación superficie**: -0.197 ❌ (vs -0.024 original) **Empeora**
- **Correlación habitaciones**: -0.344 ❌ (vs -0.166 original) **Empeora**

**Conclusión**: Aunque se eliminan outliers y propiedades problemáticas, las correlaciones siguen siendo negativas. Esto confirma que el problema es la **estructura fundamental del mercado** (curva no-lineal), no solo datos incorrectos.

---

## 💡 Causa Raíz Identificada

### Curva de Demanda No-Lineal en Gràcia

El mercado de viviendas en Gràcia tiene una estructura de precios donde:

1. **Estudios pequeños** (<50m²): Precio/m² alto (6,508 €/m²)
   - Demanda por ubicación (centro, bien comunicado)
   - No por tamaño
   - Mercado premium para jóvenes profesionales

2. **Viviendas estándar** (70-110m²): Precio/m² medio-bajo (5,903 €/m²)
   - Economías de escala
   - Mercado masivo
   - Mejor relación precio/tamaño

3. **Viviendas de lujo** (>150m²): Precio/m² alto (6,846 €/m²)
   - Mercado premium
   - Características especiales (vistas, terraza, etc.)

**Esta estructura no-lineal no puede ser capturada por un modelo lineal OLS**, lo que explica las correlaciones negativas.

---

## 🎯 Recomendaciones

### Para el Spike (Inmediato)

1. ✅ **Mantener MACRO baseline** (R² = 0.71)
   - Funciona bien a nivel barrio
   - No requiere matching individual
   - Es la mejor opción disponible

2. ⚠️ **NO-GO para MICRO con modelo lineal**
   - Correlaciones negativas persisten incluso con datos limpios
   - Estructura no-lineal requiere modelos no-lineales
   - No cumple criterios de éxito (R² ≥ 0.75)

3. ⏳ **Si se quiere continuar con MICRO** (futuro):
   - Usar transformaciones no-lineales (log, polinomios)
   - O modelos no-lineales (Random Forest, Gradient Boosting)
   - Clasificar por tipo de propiedad (vivienda, estudio, etc.)

### Para Producción (Futuro)

1. **Modelos no-lineales**:
   - Random Forest
   - Gradient Boosting (XGBoost, LightGBM)
   - Neural Networks

2. **Clasificación por tipo**:
   - Entrenar modelos separados por tipo de propiedad
   - Vivienda, estudio, local, etc.

3. **Validación de datos**:
   - Filtrar propiedades no-residenciales
   - Validar rangos razonables
   - Verificar matching de calidad

---

## 📊 Métricas Finales

| Métrica | MACRO Baseline | MICRO (mejor intento) | Target |
|---------|----------------|----------------------|--------|
| **R²** | 0.71 | 0.21 | ≥0.75 |
| **RMSE** | 323.47 €/m² | 2,113 €/m² | ≤250 €/m² |
| **Correlación superficie** | N/A | -0.024 a -0.239 | >0 |
| **Correlación habitaciones** | N/A | -0.166 a -0.344 | >0 |
| **Granularidad** | Barrio×Año | Edificio individual | Edificio |

**Conclusión**: MACRO baseline cumple mejor los objetivos que cualquier intento de MICRO.

---

## 📝 Archivos Generados

### Scripts Implementados
- `match_idealista_catastro_geographic.py` - Matching geográfico
- `match_idealista_catastro_by_building.py` - Matching por edificio
- `match_idealista_catastro_by_grid.py` - Matching por cuadrícula
- `filter_clean_dataset.py` - Limpieza de datos

### Datasets Generados
- `idealista_gracia_comet_with_coords.csv` - Idealista con coordenadas (429 propiedades)
- `idealista_catastro_matched_geographic_final.csv` - Matches geográficos (254 matches)
- `idealista_catastro_matched_by_building.csv` - Matches por edificio (596 matches)
- `dataset_micro_hedonic_cleaned.csv` - Dataset limpio (232 observaciones)

### Documentación
- `MATCHING_GEOGRAFICO_RESULTADOS.md` - Resultados matching geográfico
- `ESTRATEGIAS_MATCHING_NIVEL_DIFERENTE.md` - Comparación de estrategias
- `INVESTIGACION_DATOS_CORRELACIONES_NEGATIVAS.md` - Análisis detallado
- `INVESTIGACION_RESUMEN_FINAL.md` - Resumen ejecutivo

---

## ✅ Conclusión Final

**Problema identificado**: Curva de demanda no-lineal en el mercado de Gràcia que no puede ser capturada por modelos lineales.

**Solución recomendada**: Mantener MACRO baseline (R² = 0.71) como solución de producción.

**Próximos pasos**:
1. Cerrar Issue #202 con decisión NO-GO para MICRO lineal
2. Mantener MACRO como baseline
3. Considerar modelos no-lineales solo si se requiere MICRO en el futuro

---

**Última actualización**: 2025-12-21  
**Estado**: ✅ Investigación completada - Listo para GitHub Issue #202

