# Resultados - Matching Geográfico

**Fecha**: 21 de diciembre de 2025  
**Issue**: #202 - Mejora de matching  
**Estado**: ⚠️ Implementado pero correlaciones empeoran

---

## 📊 Resumen Ejecutivo

Se implementó matching geográfico basado en coordenadas (lat/lon) y se combinó con matching heurístico. Sin embargo, **las correlaciones empeoran** en lugar de mejorar.

**Decisión**: ⚠️ Matching geográfico no mejora el problema de correlaciones negativas.

---

## 🔧 Implementación Completada

### Scripts Creados

1. **`match_idealista_catastro_geographic.py`** ✅
   - Geocoding de direcciones Idealista (Nominatim/OpenStreetMap)
   - Cálculo de distancia geográfica (Haversine)
   - Matching geográfico + heurístico combinado
   - Score ponderado configurable

2. **`test_geographic_matching.py`** ✅
   - Script de prueba rápida

3. **`match_idealista_catastro_geographic_relaxed.py`** ✅
   - Wrapper con parámetros relajados

### Geocoding Completado

- **429/505 direcciones geocodificadas** (85.0%)
- **Tiempo**: ~8 horas (debido a rate limits de Nominatim)
- **Archivo**: `idealista_gracia_comet_with_coords.csv`

---

## 📊 Resultados del Matching

### Parámetros Finales

- **Distancia máxima**: 300m
- **Peso geográfico**: 0.5 (50% geográfico, 50% heurístico)
- **Score mínimo**: 0.4
- **Filtrado geográfico**: Solo propiedades dentro del rango de Gràcia

### Métricas

| Métrica | Heurístico | Geográfico | Cambio |
|---------|------------|------------|--------|
| **Match Rate** | 100% (505/505) | 62.0% (254/410) | ⬇️ -38% |
| **Observaciones** | 505 | 254 | ⬇️ -251 |
| **Distancia promedio** | N/A | 103.6 m | ✅ Válida |
| **Matches geográficos** | 0% | 100% | ✅ Mejora |

---

## 🔍 Correlaciones (Crítico)

### Matching Heurístico (505 obs)

- `superficie_m2` - `precio_m2`: **-0.024** ❌
- `habitaciones` - `precio_m2`: **-0.166** ❌

### Matching Geográfico (254 obs)

- `superficie_m2` - `precio_m2`: **-0.239** ❌❌ (PEOR)
- `habitaciones` - `precio_m2`: **-0.273** ❌❌ (PEOR)

### Análisis

**Las correlaciones empeoran** con matching geográfico:
- `superficie_m2`: -0.216 peor (de -0.024 a -0.239)
- `habitaciones`: -0.108 peor (de -0.166 a -0.273)

**Interpretación**: El matching geográfico no resuelve el problema de correlaciones negativas. Esto sugiere que:
1. El problema no es el matching, sino los datos mismos
2. Los precios de Idealista pueden no corresponder a las características de Catastro
3. Puede haber errores sistemáticos en los datos

---

## 📊 Distancias Geográficas

**Todos los matches tienen distancia válida** (100%):
- **Media**: 103.6 m
- **Mediana**: 56.5 m
- **Min**: 24.9 m
- **Max**: 267.0 m

**Interpretación**: Las distancias son razonables (todas < 300m), lo que sugiere que el matching geográfico funciona correctamente desde el punto de vista técnico.

---

## 💡 Hallazgos

### 1. Matching Geográfico Funciona Técnicamente ✅

- Geocoding exitoso: 85% de direcciones
- Distancias calculadas correctamente
- Todos los matches dentro de 300m
- 100% de matches usan matching geográfico

### 2. Pero No Mejora Correlaciones ❌

- Correlaciones empeoran significativamente
- Match rate se reduce (62% vs 100%)
- Menos observaciones para entrenar modelo

### 3. Problema Más Fundamental ⚠️

Las correlaciones negativas persisten incluso con matching geográfico preciso, lo que sugiere:
- **Datos de Idealista incorrectos**: Precios pueden no corresponder a propiedades
- **Datos de Catastro incorrectos**: Características pueden no corresponder a edificios
- **Problema de granularidad**: Matching edificio-a-edificio puede no ser apropiado (un edificio tiene múltiples viviendas)

---

## 🎯 Recomendaciones

### Para el Spike (Inmediato)

1. ✅ **Matching geográfico implementado** (completado)
2. ⏳ **Investigar datos de Idealista**:
   - Verificar manualmente una muestra de precios
   - Comparar con precios esperados para Gràcia
   - Revisar parsing de Comet AI
3. ⏳ **Investigar datos de Catastro**:
   - Verificar que características corresponden a edificios correctos
   - Revisar si hay errores en extracción
4. ⏳ **Considerar problema de granularidad**:
   - Un edificio Catastro puede tener múltiples viviendas
   - Matching edificio-a-vivienda puede no ser apropiado

### Para Producción (Futuro)

1. **Validar datos antes de matching**:
   - Verificar precios de Idealista
   - Verificar características de Catastro
   - Implementar validaciones de calidad
2. **Considerar matching a nivel de vivienda**:
   - Si Catastro tiene datos por vivienda (no solo edificio)
   - O matching a nivel de barrio (como MACRO)
3. **Mantener baseline MACRO**:
   - MACRO v0.1 sigue siendo mejor opción
   - R² = 0.71 vs MICRO = 0.21

---

## 📊 Comparación de Métodos

| Aspecto | Heurístico | Geográfico | Mejor |
|---------|------------|------------|-------|
| **Match Rate** | 100% | 62% | Heurístico |
| **Correlación superficie** | -0.024 | -0.239 | Heurístico |
| **Correlación habitaciones** | -0.166 | -0.273 | Heurístico |
| **Distancia válida** | No | Sí (100%) | Geográfico |
| **Precisión geográfica** | Baja | Alta | Geográfico |
| **Observaciones** | 505 | 254 | Heurístico |

**Conclusión**: Matching heurístico es mejor para este caso, a pesar de no usar coordenadas.

---

## 📝 Próximos Pasos

1. **Investigar datos de Idealista** (prioridad alta)
   - Verificar precios manualmente
   - Comparar con fuentes externas
2. **Investigar datos de Catastro** (prioridad alta)
   - Verificar características
   - Revisar extracción
3. **Considerar matching a nivel diferente**
   - Nivel barrio (como MACRO)
   - O nivel vivienda si está disponible
4. **Documentar limitaciones**
   - Matching geográfico no resuelve el problema
   - Problema parece ser más fundamental

---

## 🔗 Archivos Generados

- **Idealista con coordenadas**: `idealista_gracia_comet_with_coords.csv` (429 propiedades)
- **Idealista filtrado geográfico**: `idealista_gracia_filtered_geographic.csv` (410 propiedades)
- **Matches geográficos**: `idealista_catastro_matched_geographic_final.csv` (254 matches)
- **Dataset para modelo**: `dataset_micro_hedonic_geographic.csv` (254 observaciones)
- **Métricas**: `idealista_catastro_matched_geographic_final_metrics.json`

---

**Última actualización**: 2025-12-21  
**Estado**: ⚠️ Implementado pero no mejora correlaciones - requiere investigación adicional

