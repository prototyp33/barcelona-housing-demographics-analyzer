# Estrategias de Matching a Nivel Diferente

**Fecha**: 21 de diciembre de 2025  
**Issue**: #202 - Mejora de matching  
**Contexto**: Matching individual (edificio-a-edificio) tiene correlaciones negativas

---

## 🎯 Objetivo

Explorar estrategias de matching a diferentes niveles de agregación para resolver el problema de correlaciones negativas en el modelo MICRO.

---

## 📊 Estrategias Implementadas

### 1. Matching Individual (Heurístico) ✅ Baseline

**Nivel**: Vivienda individual ↔ Registro Catastro individual

**Características**:
- Match rate: 100% (505/505)
- Correlación `superficie_m2` - `precio_m2`: **-0.024** ❌
- Correlación `habitaciones` - `precio_m2`: **-0.166** ❌

**Problema**: Correlaciones negativas sugieren matching incorrecto o datos erróneos.

---

### 2. Matching Geográfico Individual ✅ Implementado

**Nivel**: Vivienda individual ↔ Edificio Catastro (por coordenadas)

**Características**:
- Match rate: 62% (254/410) - solo propiedades dentro de rango Gràcia
- Distancia promedio: 103.6 m
- Correlación `superficie_m2` - `precio_m2`: **-0.239** ❌❌ (PEOR)
- Correlación `habitaciones` - `precio_m2`: **-0.273** ❌❌ (PEOR)

**Problema**: Aunque el matching geográfico es preciso, las correlaciones empeoran.

**Conclusión**: ⚠️ Matching geográfico no resuelve el problema.

---

### 3. Matching por Edificio ✅ Implementado

**Nivel**: Vivienda Idealista ↔ Edificio Catastro completo (agregado)

**Estrategia**:
- Agrupar Catastro por `referencia_catastral` (edificio completo)
- Agregar características: media de superficie, año construcción, plantas
- Matching geográfico: Idealista → edificio más cercano (< 300m)
- Fallback: Matching por barrio si no hay coordenadas

**Resultados**:
- Match rate: **99.8%** (596/597) ✅
- Distancia promedio: 140.1 m (81.9% con distancia válida)
- Correlación `superficie_m2` - `precio_m2`: **-0.037** ❌
- Correlación `habitaciones` - `precio_m2`: **-0.183** ❌

**Comparación con heurístico**:
- Match rate: Mejor (99.8% vs 100%, pero más realista)
- Correlaciones: Similar o ligeramente peor (-0.037 vs -0.024)

**Ventajas**:
- ✅ Un edificio puede tener múltiples viviendas (más realista)
- ✅ Reduce problema de granularidad edificio-vs-vivienda
- ✅ Mantiene variación geográfica (no solo barrio)
- ✅ Match rate muy alto

**Desventajas**:
- ❌ Correlaciones siguen siendo negativas
- ❌ Agregación puede perder variación individual

**Conclusión**: ⚠️ Mejora match rate pero no resuelve correlaciones negativas.

---

### 4. Matching por Cuadrícula Geográfica ⚠️ Implementado (bajo match rate)

**Nivel**: Cuadrícula geográfica (100m × 100m)

**Estrategia**:
- Dividir área en cuadrículas de 100m × 100m
- Agregar Idealista por cuadrícula
- Agregar Catastro por cuadrícula
- Matching: cuadrícula Idealista → cuadrícula Catastro

**Resultados**:
- Cuadrículas Idealista: 29
- Cuadrículas Catastro: 56
- Match rate: **10.3%** (3/29) ❌

**Problema**: Las cuadrículas no se alinean bien (diferentes distribuciones espaciales).

**Conclusión**: ❌ No viable con tamaño de cuadrícula actual.

---

## 📊 Comparación de Estrategias

| Estrategia | Match Rate | Correlación superficie | Correlación habitaciones | Distancia | Viabilidad |
|-----------|------------|------------------------|--------------------------|-----------|------------|
| **Heurístico** | 100% | -0.024 | -0.166 | N/A | ✅ Baseline |
| **Geográfico Individual** | 62% | -0.239 | -0.273 | 103.6 m | ⚠️ Empeora |
| **Por Edificio** | 99.8% | -0.037 | -0.183 | 140.1 m | ⚠️ Similar |
| **Por Cuadrícula** | 10.3% | N/A | N/A | N/A | ❌ No viable |
| **MACRO (barrio)** | 100% | N/A | N/A | N/A | ✅ R² = 0.71 |

---

## 💡 Hallazgos Clave

### 1. El Problema No Es el Matching ⚠️

- Matching geográfico preciso (103.6 m promedio) → correlaciones empeoran
- Matching por edificio (más realista) → correlaciones similares
- **Conclusión**: El problema parece ser los datos mismos, no el matching.

### 2. MACRO Funciona Mejor ✅

- MACRO baseline (nivel barrio): R² = 0.71
- MICRO (nivel individual): R² = 0.21
- **Conclusión**: Agregación a nivel barrio funciona mejor que matching individual.

### 3. Posibles Causas de Correlaciones Negativas

1. **Datos de Idealista incorrectos**:
   - Precios pueden no corresponder a propiedades
   - Parsing de Comet AI puede tener errores
   - Precios pueden estar desactualizados o incorrectos

2. **Datos de Catastro incorrectos**:
   - Características pueden no corresponder a edificios
   - Agregación por edificio puede mezclar viviendas diferentes

3. **Problema de granularidad**:
   - Un edificio tiene múltiples viviendas con diferentes características
   - Matching edificio-a-vivienda puede no ser apropiado

4. **Problema de escala**:
   - Variación individual puede tener mucho ruido
   - Agregación reduce ruido (por eso MACRO funciona mejor)

---

## 🎯 Recomendaciones

### Para el Spike (Inmediato)

1. ✅ **Mantener MACRO baseline** (R² = 0.71)
   - Es la mejor opción disponible
   - Funciona bien a nivel barrio

2. ⏳ **Investigar datos de Idealista** (prioridad alta)
   - Verificar manualmente una muestra de precios
   - Comparar con precios esperados para Gràcia
   - Revisar parsing de Comet AI

3. ⏳ **Investigar datos de Catastro** (prioridad alta)
   - Verificar que características corresponden a edificios correctos
   - Revisar si hay errores en extracción

4. ⏳ **Considerar matching a nivel barrio** (como MACRO)
   - Ya funciona bien (R² = 0.71)
   - Puede ser suficiente para el spike

### Para Producción (Futuro)

1. **Validar datos antes de matching**:
   - Verificar precios de Idealista
   - Verificar características de Catastro
   - Implementar validaciones de calidad

2. **Considerar modelo híbrido**:
   - MACRO para predicciones a nivel barrio
   - MICRO solo si se resuelven problemas de datos

3. **Explorar otras fuentes de datos**:
   - APIs oficiales de precios
   - Datos de transacciones reales
   - Validación cruzada con múltiples fuentes

---

## 📝 Próximos Pasos

1. **Documentar hallazgos en Issue #202**
   - Matching geográfico no mejora correlaciones
   - Matching por edificio similar a heurístico
   - MACRO sigue siendo mejor opción

2. **Investigar datos de Idealista**
   - Verificar precios manualmente
   - Comparar con fuentes externas

3. **Investigar datos de Catastro**
   - Verificar características
   - Revisar extracción

4. **Decisión Go/No-Go para MICRO**
   - Basado en resultados: **NO-GO** para matching individual
   - **GO** para MACRO (ya funciona)

---

## 🔗 Archivos Generados

- **Matching por edificio**: `idealista_catastro_matched_by_building.csv` (596 matches)
- **Matching por cuadrícula**: `idealista_catastro_matched_by_grid.csv` (3 matches)
- **Métricas**: Archivos `*_metrics.json` correspondientes

---

**Última actualización**: 2025-12-21  
**Estado**: ✅ Estrategias implementadas y evaluadas - MACRO sigue siendo mejor opción

