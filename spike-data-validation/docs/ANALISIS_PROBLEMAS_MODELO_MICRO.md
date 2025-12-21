# Análisis de Problemas - Modelo Hedónico MICRO

**Fecha**: 20 de diciembre de 2025  
**Issue**: #202 - Fase 2  
**Estado**: ⚠️ Modelo con rendimiento muy bajo

---

## 🔍 Hallazgos Críticos

### 1. Correlaciones Muy Bajas/Negativas

**Correlaciones con `precio_m2`**:
- `superficie_m2`: **-0.006** ❌ (prácticamente cero, debería ser positiva ~0.3-0.5)
- `habitaciones`: **-0.199** ❌ (negativa, contraintuitivo)
- `ano_construccion`: **-0.079** ❌ (negativa, contraintuitivo)
- `plantas`: **-0.038** ❌ (negativa, contraintuitivo)

**Interpretación**: Las variables predictoras **NO están relacionadas** con el precio en este dataset. Esto explica por qué el modelo tiene R² negativo/cero.

---

### 2. Outliers Extremos

**Precio/m²**:
- **Mínimo**: 1,174 €/m² (muy bajo para Gràcia)
- **Máximo**: **27,108 €/m²** ⚠️ (extremadamente alto)
- **Media**: 6,357 €/m²
- **Mediana**: 5,515 €/m²
- **Outliers**: 32 observaciones (8.1%) fuera de rango IQR

**Outliers más extremos**:
- Propiedad con **27,108 €/m²**: 166 m², 2 habitaciones, precio total 4,500,000 €
- Propiedad con **20,588 €/m²**: 170 m², 2 habitaciones, precio total 3,500,000 €
- Propiedad con **1,174 €/m²**: 120 m², 0 habitaciones, precio total 140,900 €

**Superficie**:
- **Mínimo**: 23 m² (muy pequeño, posible error)
- **Máximo**: 945 m² (muy grande, posible local comercial)
- Propiedades < 30 m²: 1
- Propiedades > 200 m²: 5

---

### 3. Resultados del Modelo

**Modelo Lineal**:
- R² test: **-0.66** ❌ (peor que baseline aleatorio)
- RMSE test: **2,136 €/m²** ❌ (objetivo: ≤250 €/m²)
- R² train: 0.18 (muy bajo)

**Modelo Log**:
- R² test: **0.0046** ❌ (casi cero)
- RMSE test: **1,654 €/m²** ❌ (mejor que lineal pero aún muy alto)
- R² train: 0.13 (muy bajo)

**Comparación con MACRO**:
- MACRO: R² = 0.71, RMSE = 323 €/m²
- MICRO: R² = -0.66, RMSE = 2,136 €/m²
- **Delta**: MICRO es **MUCHO PEOR** que MACRO

---

## 🔎 Causas Probables

### Causa 1: Calidad del Matching ⚠️ **MÁS PROBABLE**

**Hipótesis**: El matching entre Idealista y Catastro puede estar asociando propiedades incorrectas.

**Evidencia**:
- Correlaciones prácticamente cero sugieren que las características físicas (Catastro) no corresponden a los precios (Idealista)
- Match rate: 77.8% (393/505) es alto, pero la **calidad** del match puede ser baja
- Match score promedio no revisado

**Verificación necesaria**:
- Revisar matches con score bajo (< 0.6)
- Verificar si direcciones coinciden realmente
- Revisar si referencias catastrales son correctas

---

### Causa 2: Datos de Idealista Incorrectos ⚠️ **PROBABLE**

**Hipótesis**: Los precios extraídos de Idealista pueden tener errores.

**Evidencia**:
- Precio máximo: 27,108 €/m² es extremadamente alto (posible error de scraping)
- Precio mínimo: 1,174 €/m² es muy bajo (posible error o propiedad especial)
- Variabilidad muy alta (std = 3,067 €/m²)

**Verificación necesaria**:
- Revisar si los precios son por m² o precio total
- Verificar si hay errores en el parsing de Comet AI
- Comparar con precios esperados para Gràcia (rango típico: 4,000-8,000 €/m²)

---

### Causa 3: Variables Predictoras Insuficientes ⚠️ **POSIBLE**

**Hipótesis**: Las variables disponibles no capturan la variabilidad del precio.

**Variables actuales**:
- `superficie_m2` (correlación: -0.006)
- `habitaciones` (correlación: -0.199)
- `ano_construccion` (correlación: -0.079)
- `plantas` (correlación: -0.038)
- `barrio_id` (dummies)

**Variables faltantes** (que podrían ayudar):
- Estado de conservación
- Orientación
- Ascensor
- Terraza/Balcon
- Reformado/No reformado
- Tipo de propiedad (piso/ático/estudio)

---

### Causa 4: Outliers Extremos ⚠️ **POSIBLE**

**Hipótesis**: Los outliers extremos están distorsionando el modelo.

**Evidencia**:
- 32 outliers (8.1%) fuera de rango IQR
- Precio máximo (27,108 €/m²) es 4.3x la mediana
- Precio mínimo (1,174 €/m²) es 0.2x la mediana

**Impacto**: Los outliers pueden estar "jalando" el modelo hacia valores extremos.

---

## 💡 Recomendaciones Inmediatas

### Prioridad 1: Investigar Calidad del Matching 🔴 **URGENTE**

**Acciones**:
1. Revisar matches con score bajo (< 0.6)
2. Verificar manualmente una muestra de matches:
   - ¿Las direcciones coinciden?
   - ¿Las superficies son similares?
   - ¿Los precios son razonables para la ubicación?
3. Analizar distribución de match scores
4. Considerar filtrar matches con score < umbral (ej: 0.7)

**Script sugerido**:
```python
# Revisar calidad de matches
df_matched = pd.read_csv('idealista_catastro_matched_improved.csv')
low_score = df_matched[df_matched['match_score'] < 0.6]
print(f"Matches con score < 0.6: {len(low_score)} ({len(low_score)/len(df_matched)*100:.1f}%)")
```

---

### Prioridad 2: Limpiar Outliers Extremos 🔴 **URGENTE**

**Acciones**:
1. Filtrar propiedades con precio/m² fuera de rango razonable:
   - Rango esperado para Gràcia: 3,000 - 12,000 €/m²
   - Filtrar < 2,000 €/m² y > 15,000 €/m²
2. Filtrar propiedades con superficie muy pequeña/grande:
   - Filtrar < 30 m² (posibles errores)
   - Filtrar > 300 m² (posibles locales comerciales)
3. Re-entrenar modelo con datos limpios

**Código sugerido**:
```python
# Filtrar outliers
df_clean = df[
    (df['precio_m2'] >= 2000) & 
    (df['precio_m2'] <= 15000) &
    (df['superficie_m2'] >= 30) & 
    (df['superficie_m2'] <= 300)
].copy()
print(f"Observaciones después de filtrar: {len(df_clean)} ({len(df_clean)/len(df)*100:.1f}%)")
```

---

### Prioridad 3: Verificar Datos de Idealista 🟡 **IMPORTANTE**

**Acciones**:
1. Revisar parsing de Comet AI:
   - ¿Los precios son correctos?
   - ¿Hay errores en la extracción?
2. Comparar con precios esperados:
   - Buscar fuentes externas de precios en Gràcia
   - Verificar si los precios son razonables
3. Revisar si hay propiedades especiales:
   - Locales comerciales
   - Garajes
   - Trasteros
   - Obras nuevas

---

### Prioridad 4: Mejorar Variables Predictoras 🟡 **IMPORTANTE**

**Acciones**:
1. Extraer más features de Idealista:
   - Estado de conservación
   - Ascensor
   - Terraza/Balcon
   - Reformado
2. Agregar interacciones:
   - `superficie_m2 × barrio_id`
   - `habitaciones × superficie_m2`
3. Considerar transformaciones:
   - `log(superficie_m2)`
   - `superficie_m2²` (efectos no lineales)

---

## 📊 Próximos Pasos Sugeridos

### Paso 1: Limpieza de Datos (Hoy)
- [ ] Filtrar outliers extremos (precio/m² y superficie)
- [ ] Re-entrenar modelo con datos limpios
- [ ] Comparar métricas antes/después

### Paso 2: Análisis de Matching (Hoy)
- [ ] Revisar distribución de match scores
- [ ] Filtrar matches con score bajo (< 0.6 o 0.7)
- [ ] Re-entrenar modelo con matches de alta calidad
- [ ] Comparar métricas

### Paso 3: Verificación de Datos (Mañana)
- [ ] Revisar parsing de Comet AI
- [ ] Verificar precios con fuentes externas
- [ ] Identificar propiedades especiales

### Paso 4: Mejoras al Modelo (Si es necesario)
- [ ] Agregar más features
- [ ] Probar transformaciones
- [ ] Considerar modelos no lineales (Random Forest, GBM)

---

## 🎯 Criterios de Éxito

**Después de limpieza, el modelo debería**:
- ✅ R² test ≥ 0.30 (mínimo aceptable)
- ✅ RMSE test ≤ 1,000 €/m² (mejora significativa)
- ✅ Correlaciones positivas con `superficie_m2` y `habitaciones`

**Si después de limpieza aún no cumple**:
- Revisar calidad del matching (causa más probable)
- Considerar que los datos pueden no ser suficientes
- Documentar limitaciones y mantener MACRO v0.1

---

## 📝 Notas Finales

- **El problema principal parece ser la calidad del matching**, no el modelo en sí
- Las correlaciones prácticamente cero sugieren que Idealista y Catastro no están correctamente asociados
- Los outliers extremos también están contribuyendo al mal rendimiento
- **Recomendación**: Empezar por limpiar outliers y revisar calidad de matches antes de hacer cambios más complejos

---

**Última actualización**: 2025-12-20  
**Próxima acción**: Limpiar outliers y revisar calidad de matches

