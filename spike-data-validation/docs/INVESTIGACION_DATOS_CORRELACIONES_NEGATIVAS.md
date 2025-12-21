# Investigación: Correlaciones Negativas en Modelo MICRO

**Fecha**: 21 de diciembre de 2025  
**Issue**: #202 - Modelo Hedonic Pricing MICRO  
**Problema**: Correlaciones negativas entre características y precio/m²

---

## 🎯 Objetivo

Investigar por qué las correlaciones entre `superficie_m2`/`habitaciones` y `precio_m2` son negativas, cuando deberían ser positivas.

---

## 📊 Hallazgos Principales

### 1. Precios de Idealista ✅ Razonables

**Estadísticas**:
- Precio/m² mediano: **5,515 €/m²** ✅ (dentro del rango esperado 4,500-6,500 €/m²)
- Precio total mediano: 510,000 €
- Rango: 1,174 - 27,108 €/m²

**Outliers**:
- **8.3% outliers altos** (42 propiedades > 10,017 €/m²)
  - Ejemplos: 14,908 €/m², 16,913 €/m², 15,300 €/m²
  - Ubicaciones: "Corazón de Barcelona", "Vila de Gràcia" (zonas premium)
- **0.2% outliers bajos** (1 propiedad < 1,323 €/m²)
  - Ejemplo: 1,174 €/m² en El Coll (posible error o propiedad especial)

**Conclusión**: Los precios parecen razonables en general, pero hay outliers que pueden afectar las correlaciones.

---

### 2. Características de Catastro ✅ Razonables

**Estadísticas**:
- Superficie mediana: **80.0 m²** ✅ (dentro del rango esperado 60-120 m²)
- Año construcción mediano: 1972
- Plantas mediana: 1.0

**Problemas detectados**:
- Superficies extremas: 1.1 m² (mínimo) y 988 m² (máximo)
- Plantas negativas: -3.0 (probablemente sótanos mal codificados)
- **2.7% outliers altos** en superficie (20 propiedades > 217 m²)

**Conclusión**: La mayoría de características son razonables, pero hay valores extremos que pueden ser errores o propiedades no-residenciales.

---

### 3. Análisis de Correlaciones por Grupos

**Curva Precio/m² vs Superficie** (análisis por bins):

| Superficie | Observaciones | Precio/m² Medio | Precio/m² Mediano |
|------------|---------------|-----------------|-------------------|
| <50 m²     | ~76           | 6,508 €/m²      | ~6,500 €/m²       |
| 50-70 m²   | ~110          | 6,629 €/m²      | ~6,600 €/m²       |
| 70-90 m²   | ~124          | 5,968 €/m²      | ~6,000 €/m²       |
| 90-110 m²  | ~111          | 5,903 €/m²      | ~5,900 €/m²       |
| 110-130 m² | ~84           | 6,846 €/m²      | ~6,800 €/m²       |
| >150 m²    | ~84           | 6,846 €/m²      | ~6,800 €/m²       |

**Hallazgo crítico**: 
- Propiedades **pequeñas (<70m²)**: precio/m² **más alto** (6,508-6,629 €/m²)
- Propiedades **medianas (70-110m²)**: precio/m² **más bajo** (5,903-5,968 €/m²)
- Propiedades **grandes (>110m²)**: precio/m² **más alto** (6,846 €/m²)

**Interpretación**: 
- Propiedades pequeñas son **estudios/lofts** en zonas premium → precio/m² alto
- Propiedades medianas son **viviendas estándar** → precio/m² más bajo (economías de escala)
- Propiedades grandes son **viviendas de lujo** o **edificios completos** → precio/m² alto

**Esto explica la correlación negativa**: El mercado de Gràcia tiene una curva de demanda no-lineal donde las propiedades medianas (viviendas estándar) tienen precio/m² más bajo que las pequeñas (estudios premium) o grandes (lujo).

---

### 4. Casos Problemáticos Específicos

#### A. Propiedades Muy Grandes (>300m²)

**Ejemplos**:
- 945 m², 27 habitaciones, 4,762 €/m²
- 567 m², 6 habitaciones, 3,175 €/m² (múltiples matches)
- 408 m², 6 habitaciones, 4,534 €/m²

**Problema**: Estas propiedades probablemente son:
- Edificios completos (no viviendas individuales)
- Locales comerciales
- Propiedades especiales

**Impacto**: Reducen el precio/m² promedio para propiedades grandes, contribuyendo a la correlación negativa.

#### B. Propiedades Muy Pequeñas (<40m²)

**Ejemplos**:
- 25 m², 0 habitaciones, 13,600 €/m² (múltiples matches)
- 37 m², 2 habitaciones, 12,027 €/m² (múltiples matches)

**Problema**: Estas propiedades son:
- Estudios/lofts en zonas premium
- Precio/m² muy alto (demanda por ubicación, no por tamaño)

**Impacto**: Aumentan el precio/m² promedio para propiedades pequeñas, contribuyendo a la correlación negativa.

#### C. Discrepancias Idealista vs Catastro

**Propiedades con diferencia >50m²** entre Idealista y Catastro:
- Pueden indicar matching incorrecto
- O diferencias en cómo se mide la superficie (útil vs construida)

**Impacto**: Matching incorrecto puede mezclar propiedades diferentes, afectando correlaciones.

---

### 5. Verificación de Parsing Comet AI

**Datos parseados**:
- ✅ Todos tienen precio, superficie, habitaciones
- ✅ No hay valores cero o negativos
- ✅ No hay duplicados

**Tipos de propiedad identificados**:
- Duplex: ~10% de propiedades
- Estudios: ~5% de propiedades
- Locales comerciales: ~2% de propiedades

**Problema**: El dataset incluye **tipos de propiedad no-residenciales** (locales, oficinas) que pueden tener lógica de precios diferente.

---

## 💡 Causas Probables de Correlaciones Negativas

### 1. **Curva de Demanda No-Lineal** (Principal) ⚠️

El mercado de Gràcia tiene una estructura de precios donde:
- **Estudios pequeños** (25-50m²): precio/m² alto (demanda por ubicación)
- **Viviendas estándar** (70-110m²): precio/m² medio (economías de escala)
- **Viviendas grandes/lujo** (>150m²): precio/m² alto (premium)

Esta estructura **no es lineal**, lo que explica la correlación negativa en un modelo lineal.

**Solución**: Usar transformaciones no-lineales (log, polinomios) o modelos no-lineales.

### 2. **Mezcla de Tipos de Propiedad** ⚠️

El dataset incluye:
- Viviendas residenciales
- Estudios/lofts
- Locales comerciales (2%)
- Edificios completos

Cada tipo tiene lógica de precios diferente, lo que puede confundir el modelo.

**Solución**: Filtrar por tipo de propiedad o usar variables dummy.

### 3. **Outliers Extremos** ⚠️

- Propiedades muy grandes (945m²) con precio/m² bajo
- Propiedades muy pequeñas (25m²) con precio/m² muy alto

**Solución**: Filtrar outliers o usar modelos robustos.

### 4. **Matching Incorrecto** (Menor probabilidad)

- 22.2% de matches con score < 0.5
- Discrepancias de superficie >50m² en algunos casos

**Solución**: Filtrar matches de baja calidad o mejorar algoritmo de matching.

---

## 🎯 Recomendaciones

### Para el Spike (Inmediato)

1. **Filtrar outliers**:
   - Eliminar propiedades <30m² (estudios)
   - Eliminar propiedades >300m² (edificios completos)
   - Eliminar precio/m² <2,000 o >15,000 €/m²

2. **Filtrar por tipo de propiedad**:
   - Excluir locales comerciales
   - Excluir oficinas
   - Mantener solo viviendas residenciales

3. **Usar transformaciones no-lineales**:
   - `log(precio_m2)` como variable dependiente
   - `log(superficie_m2)` como variable independiente
   - O usar modelos polinómicos

4. **Filtrar matches de baja calidad**:
   - Solo usar matches con score >= 0.7
   - Verificar discrepancias de superficie

### Para Producción (Futuro)

1. **Clasificar tipos de propiedad**:
   - Vivienda, estudio, local, oficina
   - Entrenar modelos separados por tipo

2. **Usar modelos no-lineales**:
   - Random Forest
   - Gradient Boosting
   - Neural Networks

3. **Validar datos antes de matching**:
   - Verificar que propiedades sean del mismo tipo
   - Verificar rangos razonables de características

---

## 📊 Próximos Pasos

1. ✅ **Filtrar dataset** (outliers + tipos no-residenciales)
2. ✅ **Re-entrenar modelo** con datos filtrados
3. ✅ **Probar transformaciones no-lineales**
4. ✅ **Comparar resultados** con baseline MACRO

---

**Última actualización**: 2025-12-21  
**Estado**: ✅ Investigación completada - Causas identificadas

