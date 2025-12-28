# Base de Datos Consolidada - master.db

**Fecha de Consolidación:** 28 de diciembre de 2024  
**Tamaño:** 2.81 MB  
**Ubicación:** `data/master.db`

## 📊 Resumen de Datos

### **Total: 16,653 registros**

---

## 🗂️ Estructura de Datos

### **DIMENSIONES** (196 registros)

| Tabla                  | Registros | Descripción                      |
| ---------------------- | --------- | -------------------------------- |
| `dim_barrios`          | 73        | Barrios de Barcelona             |
| `dim_tiempo`           | 50        | Dimensión temporal (2015-2024)   |
| `dim_barrios_extended` | 73        | Información extendida de barrios |

### **DATOS AVANZADOS** (882 registros)

| Tabla                    | Registros | Años      | Descripción                             |
| ------------------------ | --------- | --------- | --------------------------------------- |
| `fact_renta_avanzada`    | 292       | 2020-2023 | Renta bruta, Gini, P80/P20              |
| `fact_catastro_avanzado` | 225       | 2021-2024 | Propietarios, antigüedad, superficie    |
| `fact_hogares_avanzado`  | 365       | 2020-2024 | Composición, hacinamiento, nacionalidad |

### **DATOS BÁSICOS** (9,173 registros)

| Tabla                 | Registros | Descripción                  |
| --------------------- | --------- | ---------------------------- |
| `fact_precios`        | 6,358     | Precios de venta de vivienda |
| `fact_housing_master` | 2,742     | Tabla maestra consolidada    |
| `fact_renta`          | 73        | Renta básica por barrio      |

### **OTROS DATASETS** (6,402 registros)

| Tabla                      | Registros | Descripción              |
| -------------------------- | --------- | ------------------------ |
| `fact_demografia_ampliada` | 2,256     | Demografía detallada     |
| `fact_presion_turistica`   | 2,093     | Presión turística        |
| `fact_oferta_idealista`    | 1,898     | Ofertas de Idealista     |
| `fact_seguridad`           | 1,460     | Datos de seguridad       |
| `fact_regulacion`          | 894       | Regulación de alquileres |
| `fact_educacion`           | 73        | Centros educativos       |
| `fact_ruido`               | 73        | Contaminación acústica   |
| `fact_medio_ambiente`      | 70        | Calidad ambiental        |
| `fact_comercio`            | 70        | Actividad comercial      |
| `fact_servicios_salud`     | 69        | Servicios de salud       |
| `fact_movilidad`           | 3         | Movilidad urbana         |

---

## 🔄 Proceso de Consolidación

### Fuentes Consolidadas:

1. **`data/database.db`**

   - Datos avanzados de scripts especializados
   - fact_hogares_avanzado (365 filas)
   - fact_renta_avanzada (292 filas)
   - fact_catastro_avanzado (225 filas)

2. **`data/processed/database.db`**
   - Datos del ETL completo
   - fact_precios (6,358 filas)
   - fact_housing_master (2,742 filas)
   - fact_renta (73 filas)
   - Otros datasets (6,402 filas)

### Estrategias de Consolidación:

- **Reemplazo:** Tablas de datos básicos (precios, renta)
- **Merge:** Tablas avanzadas (sin duplicados)
- **Copia:** Tablas nuevas o vacías en master
- **Recreación:** Tablas con schema mismatch

### Tablas Recreadas por Schema Mismatch:

- `fact_educacion`
- `fact_regulacion`
- `fact_presion_turistica`
- `fact_seguridad`

---

## 📈 Cobertura de Datos

### Temporal:

- **Rango:** 2015-2024 (10 años)
- **Datos avanzados:** 2020-2024 (5 años)
- **Datos básicos:** Variable por dataset

### Geográfica:

- **73 barrios** de Barcelona
- **10 distritos**
- Cobertura completa de la ciudad

### Métricas Principales:

**Vivienda:**

- Precios de venta (6,358 registros)
- Ofertas de alquiler (1,898 registros)
- Características catastrales (225 registros)

**Sociodemografía:**

- Renta e inequidad (292 registros)
- Composición de hogares (365 registros)
- Demografía ampliada (2,256 registros)

**Contexto Urbano:**

- Presión turística (2,093 registros)
- Seguridad (1,460 registros)
- Regulación (894 registros)
- Educación, salud, comercio, movilidad

---

## 🎯 Calidad de Datos

### ✅ Datos Completos y Verificados:

- **fact_renta_avanzada:** 292 filas
  - Renta media: 49k€ (2020) → 59k€ (2023)
  - Gini medio: 32.0 → 31.2
- **fact_hogares_avanzado:** 365 filas
  - Personas/hogar: 70.65 (2022) → 71.48 (2024)
- **fact_catastro_avanzado:** 225 filas

  - 73 barrios × ~3 años con datos

- **fact_precios:** 6,358 filas
  - Datos de venta de vivienda

### ⚠️ Limitaciones Conocidas:

1. **Chunks limitados:** Algunos datasets cargados con 25k filas/chunk
2. **Datos de hogares:** % extranjeros = 0% (datos limitados)
3. **fact_demografia:** Vacía (requiere investigación)
4. **Turismo:** Dataset alternativo usado

---

## 🔧 Scripts de Consolidación

### Consolidar Bases de Datos:

```bash
python3 -m scripts.consolidate_databases
```

### Cargar Datasets Avanzados:

```bash
python3 -m scripts.load_advanced_only
python3 -m scripts.load_single_dataset catastro
python3 -m scripts.load_single_dataset hogares
```

### ETL Completo:

```bash
python3 -m src.etl.pipeline
```

---

## 📝 Próximos Pasos

### Fase de Análisis:

1. **Análisis Exploratorio:**

   - Distribuciones de precios por barrio
   - Correlaciones renta-precio
   - Evolución temporal de inequidad

2. **Modelado Predictivo:**

   - Predicción de precios
   - Identificación de barrios en riesgo
   - Segmentación de mercado

3. **Visualización:**

   - Dashboards interactivos
   - Mapas de calor
   - Series temporales

4. **Reporting:**
   - Informes por barrio
   - Análisis de tendencias
   - Recomendaciones de política pública

---

## 🗄️ Backup y Versionado

**Backup Automático:** Se crea automáticamente al ejecutar consolidación  
**Ubicación:** `data/master_backup_<timestamp>.db`

**Bases de Datos Originales:**

- `data/database.db` (preservada)
- `data/processed/database.db` (preservada)

---

**Última Actualización:** 28 de diciembre de 2024  
**Versión:** 1.0  
**Estado:** ✅ Listo para Análisis
