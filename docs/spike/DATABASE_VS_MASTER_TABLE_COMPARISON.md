# Comparativa: Base de Datos vs Master Table CSV

**Fecha de análisis**: 2025-12-13  
**Base de datos**: `data/processed/database.db`  
**Master Table**: `data/processed/barcelona_housing_master_table.csv`

---

## 📊 Resumen Ejecutivo

| Aspecto | Base de Datos (Existente) | Master Table CSV (Nuevo) | Beneficio |
|---------|---------------------------|--------------------------|-----------|
| **Granularidad temporal** | Anual (inconsistente) | Quarterly (consistente) | ✅ Alineación temporal |
| **Features** | 2-3 por tabla | 31 unificadas | ✅ Ready for ML |
| **Calidad de datos** | Mixta, sin validación DQ | Validada y limpia | ✅ Confiabilidad |
| **Affordability metrics** | ❌ No existe | ✅ Calculados | ✅ Análisis avanzado |
| **Atributos estructurales** | ❌ No existe | ✅ 6 features | ✅ Contexto urbano |

---

## 🔍 Análisis Detallado por Tabla

### 1. Precios de Vivienda

#### `fact_precios` (Base de Datos)
```
Registros:        6,358
Barrios:          73/73 (100%)
Período:          2012-2025
Granularidad:     ANUAL (trimestre = NULL en todos)
Fuentes:          - portaldades: 6,299 registros
                  - opendatabcn_idealista: 59 registros
Features:         2 (precio_m2_venta, precio_mes_alquiler)
Periodo:          Formato "YYYY" (ej: "2015")
```

**Problemas identificados:**
- ❌ `trimestre` es NULL en **todos** los registros (6,358/6,358)
- ❌ Granularidad inconsistente: datos deberían ser quarterly pero están como anuales
- ❌ Múltiples registros por barrio-año (posible duplicación por fuente)
- ❌ Sin validación de calidad de datos

#### `barcelona_housing_master_table.csv` (Nuevo)
```
Registros:        2,742
Barrios:          71/73 (97%)
Período:          2015-2024
Granularidad:     QUARTERLY (Q1, Q2, Q3, Q4)
Fuentes:          - incasol_portaldades (alquiler)
                  - generalitat_portaldades (venta)
Features:         4 (preu_lloguer_mensual, preu_lloguer_m2, 
                     preu_venda_total, preu_venda_m2)
Periodo:          Formato "YYYY-QN" (ej: "2015-Q1")
```

**Ventajas:**
- ✅ Granularidad quarterly consistente
- ✅ Validación DQ aplicada
- ✅ Sin duplicados
- ✅ Fuentes oficiales (INCASÒL + Generalitat)

**Gap de cobertura:**
- ⚠️ 2 barrios faltantes (71 vs 73):
  - ID 11: el Poble-sec
  - ID 12: la Marina del Prat Vermell
- ⚠️ Período más corto (2015-2024 vs 2012-2025)

---

### 2. Renta

#### `fact_renta` (Base de Datos)
```
Registros:        657
Barrios:          73/73 (100%)
Período:          2015-2023
Granularidad:     ANUAL
Features:         1 (renta_mediana)
Source:           idescat
```

**Limitaciones:**
- ❌ Solo granularidad anual
- ❌ No alineado con precios quarterly
- ❌ Sin métricas de affordability

#### Master Table CSV - Renta
```
Registros:        2,742 (interpolado quarterly)
Barrios:          71/73 (97%)
Período:          2015-2024
Granularidad:     QUARTERLY (interpolado forward-fill)
Features:         3 (renta_annual, renta_min, renta_max)
Source:           idescat (interpolado)
```

**Ventajas:**
- ✅ Alineado con precios (mismo período y granularidad)
- ✅ Interpolación forward-fill para quarterly
- ✅ Múltiples métricas de renta

---

### 3. Atributos Estructurales

#### Base de Datos
```
❌ NO EXISTE en ninguna tabla
```

#### Master Table CSV
```
Features:         6 atributos estructurales
  - anyo_construccion_promedio
  - antiguedad_anos
  - num_edificios
  - pct_edificios_pre1950
  - superficie_m2
  - pct_edificios_con_ascensor_proxy

Cobertura:        73/73 barrios (100%)
Granularidad:     Estática (no temporal)
Source:           Open Data BCN (edificios)
```

**Ventajas:**
- ✅ Contexto urbano completo
- ✅ Proxy para calidad de vivienda
- ✅ Variables para análisis de gentrificación

---

### 4. Affordability Metrics

#### Base de Datos
```
❌ NO EXISTE en ninguna tabla
```

#### Master Table CSV
```
Features:         4 métricas de affordability
  - price_to_income_ratio
  - rent_burden_pct
  - affordability_index
  - affordability_ratio

Cálculo:          Basado en renta + precios
Granularidad:     Quarterly (2015-2024)
```

**Ventajas:**
- ✅ Métricas listas para análisis
- ✅ Comparabilidad temporal
- ✅ Indicadores de presión inmobiliaria

---

## 📈 Comparación de Cobertura

### Cobertura Temporal

| Período | fact_precios (DB) | Master Table CSV | Gap |
|---------|-------------------|------------------|-----|
| 2012-2014 | ✅ 1,014 registros | ❌ No disponible | -1,014 |
| 2015-2024 | ✅ 4,344 registros | ✅ 2,742 registros | -1,602 |
| 2025 | ✅ 430 registros | ❌ No disponible | -430 |

**Observación**: Master Table tiene menos registros pero mayor calidad y granularidad quarterly.

### Cobertura Espacial

| Aspecto | fact_precios (DB) | Master Table CSV |
|---------|-------------------|------------------|
| Barrios totales | 73/73 (100%) | 71/73 (97%) |
| Barrios con datos 2015-2024 | 73/73 | 71/73 |

**Gap**: 2 barrios faltantes en Master Table:
- ID 11: el Poble-sec
- ID 12: la Marina del Prat Vermell

**Posible causa**: Datos no disponibles en fuentes oficiales (INCASÒL/Generalitat) para estos barrios en el período 2015-2024.

---

## 🔄 Análisis de Solapamiento

### Datos Comunes

**Período común**: 2015-2024

- `fact_precios` (DB): ~4,344 registros anuales
- Master Table CSV: 2,742 registros quarterly

**Relación esperada**: 
- 1 registro anual → 4 registros quarterly
- 4,344 anuales × 4 = ~17,376 quarterly (teórico)
- Master Table tiene 2,742 quarterly = ~686 barrio-años equivalentes

**Conclusión**: Master Table es un **subset limpio y validado** de los datos de portaldades, con:
- ✅ Granularidad quarterly real (no interpolada)
- ✅ Validación de calidad
- ✅ Sin duplicados
- ✅ Fuentes oficiales verificadas

---

## ✅ Beneficios del Master Table CSV

### 1. **Granularidad Consistente**
- **Problema DB**: `fact_precios` tiene `trimestre = NULL` en todos los registros
- **Solución Master Table**: Quarterly real (Q1-Q4) para análisis temporal preciso

### 2. **Features Unificadas**
- **Problema DB**: Datos dispersos en múltiples tablas (`fact_precios`, `fact_renta`, sin estructurales)
- **Solución Master Table**: 31 features en un solo lugar, ready for ML

### 3. **Affordability Metrics**
- **Problema DB**: No existen métricas de affordability
- **Solución Master Table**: 4 métricas calculadas (price_to_income, rent_burden, etc.)

### 4. **Atributos Estructurales**
- **Problema DB**: No existe información sobre edificios
- **Solución Master Table**: 6 features estructurales (edad, superficie, ascensor proxy)

### 5. **Calidad de Datos**
- **Problema DB**: Sin validación DQ, posibles duplicados
- **Solución Master Table**: Validación aplicada, sin duplicados, fuentes verificadas

### 6. **Alineación Temporal**
- **Problema DB**: Renta anual vs precios (teóricamente quarterly pero NULL)
- **Solución Master Table**: Todo alineado quarterly (renta interpolada)

---

## ⚠️ Limitaciones del Master Table CSV

### 1. **Cobertura Temporal Reducida**
- ❌ No incluye 2012-2014 (solo 2015-2024)
- ❌ No incluye 2025

### 2. **Cobertura Espacial**
- ⚠️ 2 barrios faltantes (71 vs 73)

### 3. **Renta Interpolada**
- ⚠️ Renta quarterly es interpolación forward-fill (no datos reales quarterly)
- ⚠️ Puede introducir sesgo en análisis de corto plazo

---

## 🎯 Recomendaciones

### Opción 1: Usar Master Table para Análisis ML
**Ventajas:**
- ✅ Features unificadas y listas
- ✅ Granularidad consistente
- ✅ Calidad validada

**Cuándo usar:**
- Modelos de machine learning
- Análisis de affordability
- Análisis temporal quarterly

### Opción 2: Mantener Base de Datos para Cobertura Completa
**Ventajas:**
- ✅ Cobertura temporal completa (2012-2025)
- ✅ Todos los barrios (73/73)
- ✅ Datos históricos preservados

**Cuándo usar:**
- Análisis histórico largo plazo
- Dashboard con todos los barrios
- Análisis anual (no quarterly)

### Opción 3: Híbrido (Recomendado)
**Estrategia:**
1. **Master Table** para análisis ML y quarterly
2. **Base de Datos** para cobertura completa y histórico
3. **Integración**: Cargar Master Table a DB como nueva tabla `fact_housing_master`

**Beneficios:**
- ✅ Lo mejor de ambos mundos
- ✅ Backward compatibility
- ✅ Flexibilidad de análisis

---

## 📝 Próximos Pasos Sugeridos

1. ✅ **Investigar barrios faltantes** en Master Table → ID 11 (Poble-sec) y ID 12 (Marina del Prat Vermell)
2. **Crear tabla `fact_housing_master`** en DB con datos del CSV
3. **Documentar proceso de interpolación** de renta
4. **Validar cobertura** de 2015-2024 entre ambas fuentes
5. **Decidir estrategia** de uso (Master Table vs DB vs Híbrido)
6. **Investigar por qué faltan datos** para Poble-sec y Marina del Prat Vermell en fuentes oficiales

---

## 📚 Referencias

- Esquema DB: `src/database_setup.py`
- Master Table: `data/processed/barcelona_housing_master_table.csv`
- Verificación DB: `scripts/verify_database_state.py`

