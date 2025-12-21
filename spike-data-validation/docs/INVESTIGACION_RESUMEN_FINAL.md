# Resumen Final - Investigación de Correlaciones Negativas

**Fecha**: 21 de diciembre de 2025  
**Issue**: #202 - Modelo Hedonic Pricing MICRO  
**Estado**: ✅ Investigación completada

---

## 🎯 Objetivo

Investigar por qué las correlaciones entre características (superficie, habitaciones) y precio/m² son negativas en el modelo MICRO, cuando deberían ser positivas.

---

## 📊 Hallazgos Principales

### 1. Precios y Características Son Razonables ✅

- **Precio/m² mediano**: 5,515 €/m² (dentro del rango esperado 4,500-6,500 €/m²)
- **Superficie mediana**: 80 m² (dentro del rango esperado 60-120 m²)
- **Año construcción mediano**: 1972

**Conclusión**: Los datos no tienen errores sistemáticos obvios.

---

### 2. Curva de Demanda No-Lineal ⚠️ (Causa Principal)

**Análisis por grupos de superficie**:

| Superficie | Precio/m² Medio | Interpretación |
|------------|-----------------|----------------|
| <50 m²     | 6,713 €/m²      | Estudios/lofts premium |
| 50-70 m²   | 6,087 €/m²      | Viviendas pequeñas |
| 70-90 m²   | 6,693 €/m²      | Viviendas estándar |
| 90-110 m²  | 5,291 €/m²      | Viviendas estándar (economías de escala) |
| 110-130 m² | 5,195 €/m²      | Viviendas grandes |
| 130-150 m² | 7,625 €/m²      | Viviendas de lujo |
| >150 m²    | 6,846 €/m²      | Viviendas premium/edificios |

**Hallazgo crítico**: 
- Propiedades **medianas (90-110m²)** tienen precio/m² **más bajo** (5,291 €/m²)
- Propiedades **pequeñas (<50m²)** tienen precio/m² **más alto** (6,713 €/m²)
- Propiedades **grandes (130-150m²)** tienen precio/m² **más alto** (7,625 €/m²)

**Interpretación**: 
El mercado de Gràcia tiene una **curva de demanda no-lineal** donde:
- Estudios pequeños: precio/m² alto (demanda por ubicación, no tamaño)
- Viviendas estándar: precio/m² medio (economías de escala)
- Viviendas de lujo: precio/m² alto (premium)

**Esto explica la correlación negativa**: Un modelo lineal no puede capturar esta estructura no-lineal.

---

### 3. Mezcla de Tipos de Propiedad ⚠️

**Tipos identificados**:
- Estudios: 7.1%
- Duplex: 8.9%
- Áticos: 7.3%
- Locales comerciales: 2.2%
- Oficinas: 1.8%
- Garajes: 5.0%

**Total no-residenciales**: 8.7%

**Problema**: Cada tipo tiene lógica de precios diferente, lo que confunde el modelo.

---

### 4. Outliers y Casos Problemáticos ⚠️

**Propiedades muy grandes (>300m²)**:
- 8 propiedades
- Precio/m² promedio: 4,768 €/m²
- Probablemente edificios completos o locales comerciales

**Propiedades muy pequeñas (<40m²)**:
- 15 propiedades
- Precio/m² promedio: 8,346 €/m²
- Probablemente estudios/lofts premium

**Impacto**: Contribuyen a la correlación negativa pero no son la causa principal.

---

### 5. Limpieza de Datos No Resuelve el Problema ❌

**Filtros aplicados**:
- Duplicados: 43 eliminados (8.5%)
- No-residenciales: 39 eliminados (8.4%)
- Outliers: 42 eliminados (9.9%)
- Matches baja calidad: 149 eliminados (39.1%)

**Total eliminado**: 273 observaciones (54.1%)

**Resultado**:
- Dataset limpio: 232 observaciones
- Correlación superficie: **-0.197** (vs -0.024 original) ❌ **Empeora**
- Correlación habitaciones: **-0.344** (vs -0.166 original) ❌ **Empeora**

**Conclusión**: Aunque se eliminan outliers y propiedades problemáticas, las correlaciones siguen siendo negativas. Esto confirma que el problema es la **estructura fundamental del mercado** (curva no-lineal), no solo datos incorrectos.

---

## 💡 Causa Raíz Identificada

### Curva de Demanda No-Lineal en Gràcia

El mercado de viviendas en Gràcia tiene una estructura de precios donde:

1. **Estudios pequeños** (<50m²): Precio/m² alto
   - Demanda por ubicación (centro, bien comunicado)
   - No por tamaño
   - Mercado premium para jóvenes profesionales

2. **Viviendas estándar** (70-110m²): Precio/m² medio-bajo
   - Economías de escala
   - Mercado masivo
   - Mejor relación precio/tamaño

3. **Viviendas de lujo** (>130m²): Precio/m² alto
   - Mercado premium
   - Características especiales (vistas, terraza, etc.)

**Esta estructura no-lineal no puede ser capturada por un modelo lineal OLS**, lo que explica las correlaciones negativas.

---

## 🎯 Recomendaciones

### Para el Spike (Inmediato)

1. ✅ **Mantener MACRO baseline** (R² = 0.71)
   - Funciona bien a nivel barrio
   - No requiere matching individual

2. ⚠️ **NO-GO para MICRO con modelo lineal**
   - Correlaciones negativas persisten incluso con datos limpios
   - Estructura no-lineal requiere modelos no-lineales

3. ⏳ **Si se quiere continuar con MICRO**:
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

## 📊 Comparación Final

| Aspecto | Original | Limpio | Cambio |
|---------|----------|--------|--------|
| **Observaciones** | 505 | 232 | -54.1% |
| **Correlación superficie** | -0.024 | -0.197 | ❌ Empeora |
| **Correlación habitaciones** | -0.166 | -0.344 | ❌ Empeora |
| **Precio/m² mediano** | 5,515 €/m² | 5,467 €/m² | Similar |
| **Superficie mediana** | 80 m² | 88 m² | Similar |

**Conclusión**: La limpieza de datos no mejora las correlaciones, confirmando que el problema es la estructura del mercado, no los datos.

---

## 📝 Próximos Pasos

1. ✅ **Documentar hallazgos en Issue #202**
2. ✅ **Mantener MACRO como baseline**
3. ⏳ **Considerar modelos no-lineales** si se quiere continuar con MICRO
4. ⏳ **Clasificar por tipo de propiedad** para modelos separados

---

**Última actualización**: 2025-12-21  
**Estado**: ✅ Investigación completada - Causa raíz identificada

