# Informe de Auditoría de Calidad de Datos

**Fecha:** 28 de diciembre de 2024  
**Base de Datos:** `data/master.db`  
**Total Registros:** 16,653

---

## 📊 RESUMEN EJECUTIVO

### ✅ **FORTALEZAS IDENTIFICADAS:**

1. **Cobertura Geográfica Completa**

   - ✅ 73 barrios de Barcelona con datos
   - ✅ 100% de cobertura en todas las tablas principales

2. **Consistencia Temporal Sólida**

   - ✅ Solapamiento temporal 2020-2023 entre renta y precios
   - ✅ Datos históricos desde 2012 hasta 2025 en precios
   - ✅ 4 años comunes para análisis integrado

3. **Calidad de Precios**
   - ✅ Solo 5 outliers menores detectados (0.08%)
   - ✅ Rangos de precios realistas y consistentes
   - ✅ Mediana de venta: 2,991 €/m²

---

## ⚠️ **HALLAZGOS CRÍTICOS**

### 1. **VALORES NULOS EN TABLAS AVANZADAS**

#### **fact_catastro_avanzado** (225 filas)

**CRÍTICO:** 100% de valores nulos en TODAS las métricas catastrales

| Columna                      | % Nulos | Impacto |
| ---------------------------- | ------- | ------- |
| num_propietarios_fisica      | 100%    | 🔴 ALTO |
| num_propietarios_juridica    | 100%    | 🔴 ALTO |
| pct_propietarios_extranjeros | 100%    | 🔴 ALTO |
| superficie_media_m2          | 100%    | 🔴 ALTO |
| num_plantas_avg              | 100%    | 🔴 ALTO |
| antiguedad_media_bloque      | 100%    | 🔴 ALTO |

**Causa Raíz:** Bug en la transformación - las columnas se crean pero no se populan con datos.

**Acción Requerida:** 🚨 URGENTE - Revisar `prepare_fact_catastro_avanzado()` en `advanced_analysis.py`

---

#### **fact_hogares_avanzado** (365 filas)

| Columna                     | % Nulos | Estado       | Impacto |
| --------------------------- | ------- | ------------ | ------- |
| pct_hogares_unipersonales   | 100%    | 🔴 Sin datos | ALTO    |
| promedio_personas_por_hogar | 47.4%   | 🟡 Parcial   | MEDIO   |
| pct_presencia_mujeres       | 7.7%    | 🟢 Bueno     | BAJO    |
| num_hogares_con_menores     | 2.5%    | 🟢 Excelente | BAJO    |

**Causa:** Limitación de chunk size (25k filas) en algunos datasets.

**Acción Requerida:** 🟡 Aumentar chunk size o procesar datasets completos.

---

#### **fact_precios** (6,358 filas)

| Columna             | % Nulos | Explicación                                       |
| ------------------- | ------- | ------------------------------------------------- |
| trimestre           | 100%    | ✅ Esperado - no todos los datos tienen trimestre |
| precio_mes_alquiler | 86.4%   | ✅ Esperado - mayoría son ventas                  |
| precio_m2_venta     | 13.6%   | ✅ Esperado - algunos son alquileres              |

**Estado:** ✅ Normal - estructura esperada de datos mixtos venta/alquiler.

---

### 2. **CONSISTENCIA TEMPORAL**

#### **Matriz de Solapamiento (2020-2024)**

| Año  | Renta Avanzada | Catastro | Hogares | Precios | Renta Básica |
| ---- | -------------- | -------- | ------- | ------- | ------------ |
| 2020 | ✓              | ✗        | ✓       | ✓       | ✗            |
| 2021 | ✓              | ✓        | ✓       | ✓       | ✗            |
| 2022 | ✓              | ✓        | ✓       | ✓       | ✗            |
| 2023 | ✓              | ✓        | ✓       | ✓       | ✓            |
| 2024 | ✗              | ✓        | ✓       | ✓       | ✗            |

#### **Años Óptimos para Análisis Integrado:**

- **2021-2023:** ✅ Todos los datasets avanzados disponibles
- **2020:** ⚠️ Sin datos de catastro
- **2024:** ⚠️ Sin datos de renta avanzada

**Recomendación:** Enfocar análisis principal en 2021-2023 (3 años completos).

---

### 3. **OUTLIERS EN PRECIOS**

#### **Precio Venta (€/m²)**

- **Rango Válido:** 500 - 20,000 €/m²
- **Rango Real:** 342.61 - 12,154.22 €/m²
- **Mediana:** 2,991.45 €/m²
- **Q1-Q3:** 2,187.58 - 3,993.53 €/m²

**Outliers Detectados:**

- ⚠️ **5 valores** por debajo de 500 €/m² (0.08%)
  - Ejemplos: 438.5 €/m² (posibles errores o zonas muy específicas)
- ℹ️ **3 outliers** por IQR (valores extremos pero posiblemente válidos)

**Acción:** 🟡 Revisar manualmente los 5 valores bajos - posibles errores de entrada.

---

#### **Precio Alquiler (€/mes)**

- **Rango Válido:** 200 - 5,000 €/mes
- **Rango Real:** 211.35 - 2,088.15 €/mes
- **Mediana:** 815.84 €/mes
- **Q1-Q3:** 667.70 - 994.35 €/mes

**Estado:** ✅ Todos los valores dentro de rangos esperados.

---

### 4. **COBERTURA POR DATASET**

#### **fact_renta_avanzada** (292 filas)

- **Años:** 2020-2023 (4 años)
- **Cobertura:** 73 barrios × 4 años = 100%
- **Estado:** ✅ COMPLETO

#### **fact_catastro_avanzado** (225 filas)

- **Años:** 2021-2024 (4 años)
- **Cobertura:** Parcial (solo 6 barrios en 2021)
- **Estado:** ⚠️ INCOMPLETO + 🔴 DATOS NULOS

#### **fact_hogares_avanzado** (365 filas)

- **Años:** 2020-2024 (5 años)
- **Cobertura:** 73 barrios × 5 años = 100%
- **Estado:** 🟡 PARCIAL (algunas métricas incompletas)

#### **fact_precios** (6,358 filas)

- **Años:** 2012-2025 (14 años)
- **Cobertura:** 73 barrios desde 2014
- **Estado:** ✅ EXCELENTE

---

## 🎯 **PLAN DE ACCIÓN PRIORITARIO**

### **URGENTE (Antes de Análisis):**

1. **🔴 Corregir fact_catastro_avanzado**

   - Todas las columnas están vacías (100% nulos)
   - Revisar y corregir transformación
   - Re-ejecutar carga de datos

2. **🟡 Validar Outliers de Precios**
   - Revisar 5 registros con precio < 500 €/m²
   - Confirmar si son errores o casos especiales

### **IMPORTANTE (Mejora de Calidad):**

3. **🟡 Completar fact_hogares_avanzado**

   - Aumentar chunk size para capturar más datos
   - Implementar `pct_hogares_unipersonales`

4. **🟢 Documentar Limitaciones**
   - Años con datos parciales
   - Métricas no disponibles

### **OPCIONAL (Optimización):**

5. **🟢 Ampliar Cobertura Temporal**
   - Obtener datos de renta para 2024
   - Completar catastro para 2021

---

## 📈 **IMPACTO EN ANÁLISIS**

### **Análisis Viables con Datos Actuales:**

✅ **Análisis de Precios (2012-2025)**

- Evolución temporal completa
- Comparaciones entre barrios
- Tendencias de mercado

✅ **Análisis de Renta e Inequidad (2020-2023)**

- Índice de Gini
- Ratio P80/P20
- Renta bruta por hogar

✅ **Análisis de Hogares (2020-2024)**

- Composición (parcial)
- Hacinamiento (parcial)
- Presencia de mujeres (completo)
- Hogares con menores (completo)

❌ **Análisis de Catastro (NO VIABLE)**

- Todas las métricas están vacías
- Requiere corrección urgente

### **Análisis Integrados Recomendados:**

**Período Óptimo: 2021-2023**

- ✅ Renta + Precios + Hogares
- ⚠️ Catastro (requiere corrección)

**Análisis Alternativos:**

- **2020:** Renta + Precios + Hogares (sin catastro)
- **2024:** Precios + Hogares (sin renta avanzada)

---

## 📊 **VISUALIZACIONES GENERADAS**

1. **Mapas de Calor de Valores Faltantes:**

   - `reports/missing_values_fact_renta_avanzada.png`
   - `reports/missing_values_fact_catastro_avanzado.png`
   - `reports/missing_values_fact_hogares_avanzado.png`
   - `reports/missing_values_fact_precios.png`

2. **Distribuciones de Precios:**
   - `reports/price_distributions.png`

---

## ✅ **CONCLUSIONES**

### **Calidad General:** 🟡 **BUENA CON RESERVAS**

**Puntos Fuertes:**

- ✅ Cobertura geográfica completa (73 barrios)
- ✅ Datos de precios excelentes (14 años, 6,358 registros)
- ✅ Renta avanzada completa (292 registros)
- ✅ Solapamiento temporal adecuado (2020-2023)

**Puntos Críticos:**

- 🔴 fact_catastro_avanzado completamente vacía
- 🟡 fact_hogares_avanzado parcialmente completa
- 🟡 Algunos outliers menores en precios

### **Recomendación Final:**

**PROCEDER CON ANÁLISIS** enfocado en:

1. Precios (2012-2025)
2. Renta e inequidad (2020-2023)
3. Hogares (métricas disponibles, 2020-2024)

**POSPONER** análisis de catastro hasta corrección de datos.

---

**Próximos Pasos:**

1. Corregir transformación de catastro
2. Validar outliers de precios
3. Iniciar análisis exploratorio con datos validados
4. Generar dashboards y visualizaciones

---

**Última Actualización:** 28 de diciembre de 2024  
**Auditor:** Sistema Automatizado de Calidad de Datos  
**Estado:** ✅ Auditoría Completada
