# Análisis de Datos Faltantes

**Fecha de análisis**: 17 de noviembre de 2025

---

## 📊 Resumen Ejecutivo

### Datos Disponibles ✅

| Tabla | Registros | Cobertura Temporal | Cobertura Geográfica | Estado |
|-------|-----------|-------------------|---------------------|--------|
| `dim_barrios` | 73 | N/A | 73/73 barrios (100%) | ✅ Completo |
| `fact_demografia` | 657 | 2015-2023 (9 años) | 73/73 barrios (100%) | ✅ Completo |
| `fact_demografia_ampliada` | 2,256 | 2015-2023 (9 años) | 73/73 barrios (100%) | ✅ Completo |
| `fact_precios` | 9,927 | 2012-2025 (14 años) | 73/73 barrios (100%) | ⚠️ Parcial |
| `fact_renta` | 73 | 1 año | 73/73 barrios (100%) | ⚠️ Limitado |
| `fact_oferta_idealista` | 0 | N/A | 0/73 barrios (0%) | ❌ Vacío |

### Geometrías ✅

- **Geometrías en `dim_barrios`**: 73/73 (100%) ✅
- Todas las geometrías GeoJSON están cargadas correctamente.

---

## ⚠️ Datos Faltantes o Incompletos

### 1. **fact_oferta_idealista** ❌ CRÍTICO

**Estado**: Tabla existe pero está completamente vacía (0 registros).

**Impacto**: 
- No tenemos datos de oferta inmobiliaria actual del mercado privado
- Falta información sobre precios de mercado en tiempo real
- No podemos analizar tendencias de oferta (número de anuncios, tiempo en mercado)

**Acción requerida**:
1. Ejecutar `scripts/build_idealista_location_ids.py` para crear el mapeo `barrio_location_ids.csv`
2. Ejecutar `scripts/extract_idealista.py` para extraer oferta de venta y alquiler
3. Ejecutar el pipeline ETL para cargar los datos en `fact_oferta_idealista`

**Limitaciones**:
- Límite de 150 peticiones/mes en RapidAPI (Plan Basic)
- Discovery + extracción completa consume ~146 peticiones
- Solo puede ejecutarse una vez al mes

---

### 2. **fact_renta** ⚠️ COBERTURA TEMPORAL LIMITADA

**Estado**: Solo 73 registros (1 año de datos).

**Análisis**:
- Cobertura geográfica: ✅ 73/73 barrios (100%)
- Cobertura temporal: ❌ Solo 1 año (probablemente 2023 o el año más reciente disponible)

**Impacto**:
- No podemos analizar tendencias temporales de renta
- No podemos correlacionar cambios de renta con cambios de precios a lo largo del tiempo
- Análisis de renta vs precios limitado a un solo año

**Acción requerida**:
1. Verificar qué años están disponibles en los datasets de renta de Open Data BCN
2. Extraer datos históricos de renta si están disponibles
3. Re-ejecutar el pipeline ETL para cargar múltiples años

**Fuentes potenciales**:
- Open Data BCN: `renda-disponible-llars-bcn`, `atles-renda-bruta-per-llar`, `atles-renda-bruta-per-persona`
- Portal de Dades: Buscar indicadores de renta familiar disponible

---

### 3. **fact_precios** ⚠️ DATOS DE ALQUILER INCOMPLETOS

**Estado**: 9,927 registros totales, pero:
- `precio_m2_venta`: 8,197 registros con datos (82.6%)
- `precio_mes_alquiler`: 1,730 registros con datos (17.4%) ❌

**Análisis**:
- **Venta**: Cobertura razonable (82.6% de registros tienen datos)
- **Alquiler**: Solo 17.4% de registros tienen datos de alquiler

**Impacto**:
- Análisis de precios de alquiler limitado
- No podemos comparar adecuadamente venta vs alquiler en muchos barrios/años
- Tendencias de alquiler incompletas

**Causa probable**:
- Los datasets de Portal de Dades pueden tener más indicadores de venta que de alquiler
- Open Data BCN tiene datos de alquiler pero sin métrica de precio identificable (según documentación)

**Acción requerida**:
1. Revisar qué datasets de Portal de Dades contienen datos de alquiler
2. Verificar si hay más indicadores de alquiler disponibles
3. Considerar integrar datos de alquiler de otras fuentes (si están disponibles)

---

### 4. **fact_demografia** ⚠️ CAMPOS NULL MENORES

**Estado**: 657 registros, pero:
- `porc_inmigracion`: 20 registros con NULL (3.0%)

**Análisis**:
- La mayoría de campos están completos
- Solo `porc_inmigracion` tiene algunos NULLs (20 de 657 = 3.0%)

**Impacto**: Bajo - solo afecta a 20 registros específicos

**Acción requerida**: 
- Verificar si estos 20 registros corresponden a barrios/años específicos
- Buscar fuentes alternativas para completar estos datos si es crítico

---

### 5. **Datos de INE** ⏳ PENDIENTE

**Estado**: Estructura base preparada, pero no implementada completamente.

**Impacto**:
- Falta fuente importante de datos demográficos nacionales
- No tenemos datos históricos de precios del INE

**Acción requerida**:
1. Implementar `ine_extractor.py` completamente
2. Extraer datos demográficos y de precios históricos del INE
3. Integrar en el pipeline ETL

---

## 📈 Cobertura Temporal por Tabla

| Tabla | Años Disponibles | Gaps Identificados |
|-------|------------------|-------------------|
| `fact_demografia` | 2015-2023 | ✅ Sin gaps aparentes |
| `fact_demografia_ampliada` | 2015-2023 | ✅ Sin gaps aparentes |
| `fact_precios` | 2012-2025 | ⚠️ Datos de alquiler muy limitados |
| `fact_renta` | 1 año | ❌ Solo un año disponible |
| `fact_oferta_idealista` | N/A | ❌ Sin datos |

---

## 🎯 Prioridades para Completar Datos

### Prioridad Alta 🔴

1. **Completar `fact_oferta_idealista`**
   - Ejecutar discovery script para mapear `locationId`s
   - Extraer oferta de Idealista (venta + alquiler)
   - Cargar en base de datos
   - **Tiempo estimado**: 2-3 horas
   - **Impacto**: Alto - datos de mercado actual

2. **Ampliar cobertura temporal de `fact_renta`**
   - Verificar años disponibles en Open Data BCN
   - Extraer datos históricos
   - **Tiempo estimado**: 1-2 horas
   - **Impacto**: Medio - permite análisis temporal

### Prioridad Media 🟡

3. **Mejorar cobertura de alquiler en `fact_precios`**
   - Revisar datasets de Portal de Dades
   - Identificar indicadores de alquiler adicionales
   - **Tiempo estimado**: 2-3 horas
   - **Impacto**: Medio - mejora análisis comparativo

4. **Completar `porc_inmigracion` NULLs**
   - Identificar barrios/años afectados
   - Buscar fuentes alternativas
   - **Tiempo estimado**: 1 hora
   - **Impacto**: Bajo - solo 20 registros

### Prioridad Baja 🟢

5. **Implementar extractor INE completo**
   - Completar `ine_extractor.py`
   - Integrar en pipeline
   - **Tiempo estimado**: 4-6 horas
   - **Impacto**: Medio - fuente adicional de datos

---

## 📝 Notas Adicionales

### Datos que SÍ tenemos y son suficientes para EDA:

✅ **Demografía básica y ampliada**: Cobertura completa 2015-2023
✅ **Precios de venta**: Cobertura razonable 2012-2025
✅ **Geometrías**: Todas las geometrías de barrios disponibles
✅ **Renta**: Un año completo (útil para análisis cross-sectional)

### Datos que limitan el análisis:

❌ **Oferta actual**: Sin datos de mercado actual
⚠️ **Renta histórica**: Solo un año limita análisis temporal
⚠️ **Alquiler**: Cobertura muy limitada

---

## 🚀 Próximos Pasos Recomendados

1. **Inmediato**: Proceder con EDA usando los datos disponibles
   - Los datos actuales son suficientes para análisis exploratorio
   - Identificar patrones y relaciones básicas
   - Visualizaciones geográficas (geometrías disponibles)

2. **Corto plazo**: Completar `fact_oferta_idealista`
   - Ejecutar discovery + extracción
   - Cargar en base de datos
   - Actualizar EDA con datos de oferta

3. **Medio plazo**: Ampliar cobertura temporal de renta
   - Extraer años históricos
   - Análisis de tendencias renta vs precios

---

*Última actualización: 2025-11-17*

