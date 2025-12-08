# Estructura de Directorios de Datos

Este documento describe la estructura de directorios utilizada para almacenar datos en el proyecto Barcelona Housing Demographics Analyzer.

## 📂 Estructura de Directorios

```
barcelona-housing-demographics-analyzer/
│
├── data/
│   ├── raw/                              # ← Datos brutos extraídos de fuentes
│   │   ├── ine/
│   │   │   └── ine_demographics_2015_2025_20250115_143022_123456.csv
│   │   ├── opendatabcn/
│   │   │   ├── opendatabcn_demografia-per-barris_2015_2025_20250115_143025_789012.csv
│   │   │   └── opendatabcn_habitatge-per-barris_2015_2025_20250115_143028_345678.csv
│   │   ├── idealista/
│   │   │   └── idealista_report_20250115.pdf
│   │   └── extraction_metadata_20250115_143030.json
│   │
│   ├── processed/                        # ← Datos limpios y normalizados listos para análisis
│   │   ├── database.db                   # ← Esquema dimensional (dim_barrios, fact_* y etl_runs)
│   │   └── backups/                      # ← Copias opcionales o versiones históricas (pendiente)
│   │
│   └── logs/                              # ← Logs de extracción
│       └── extraction_20250115_143030.txt
│
├── logs/                                  # ← Logs del sistema (rotación diaria)
│   └── data_extraction_20250115.log
│
└── scripts/
    └── extract_data.py
```

## 📍 Directorios Principales

### `data/raw/` - Datos Brutos

**Propósito**: Almacena datos extraídos directamente de las fuentes sin procesar.

**Estructura**:
- **Subdirectorios por fuente**: Cada fuente tiene su propio subdirectorio para mejor organización
  - `ine/`: Datos del Instituto Nacional de Estadística
  - `opendatabcn/`: Datos de Open Data Barcelona
  - `idealista/`: Datos de Idealista

**Convención de nombres**:
```
{source}_{dataset}_{year_start}_{year_end}_{YYYYMMDD_HHMMSS_ffffff}.{ext}
```

**Ejemplos**:
- `ine/ine_demographics_2015_2025_20250115_143022_123456.csv`
- `opendatabcn/opendatabcn_demografia-per-barris_2015_2025_20250115_143025_789012.csv`
- `opendatabcn/opendatabcn_habitatge-per-barris_2015_2025_20250115_143028_345678.csv`

**Ventajas de subdirectorios**:
- ✅ Organización clara por fuente
- ✅ Fácil identificación de origen de datos
- ✅ Soporte para múltiples datasets por fuente
- ✅ Evita conflictos de nombres

### `data/processed/` - Datos Procesados

**Propósito**: Almacena los resultados del pipeline ETL listos para análisis y visualización.

**Estado**: ✅ Implementado.

**Contenido actual**:
```
data/processed/
├── database.db          # SQLite con tablas:
│                        #   - dim_barrios (73 barrios con geometrías GeoJSON)
│                        #   - fact_demografia (demografía estándar)
│                        #   - fact_demografia_ampliada (edad quinquenal y nacionalidad)
│                        #   - fact_precios (precios de venta y alquiler)
│                        #   - fact_renta (renta por barrio)
│                        #   - fact_oferta_idealista (oferta inmobiliaria actual)
│                        #   - etl_runs (auditoría de ejecuciones)
└── backups/             # Carpeta opcional para snapshots (crear según necesidad)
```

**Cómo generar/actualizar el esquema**:

```bash
# Ejecuta el ETL (Transformación + Carga)
python scripts/process_and_load.py \
    --raw-dir data/raw \
    --processed-dir data/processed \
    --log-level INFO
```

El script:
- Detecta automáticamente los últimos archivos en `data/raw/opendatabcn/`, `data/raw/geojson/` y `data/raw/idealista/`
- Construye la dimensión de barrios (`dim_barrios`) con geometrías GeoJSON
- Genera las tablas de hechos:
  - `fact_demografia` (demografía estándar) o `fact_demografia_ampliada` (edad quinquenal y nacionalidad)
  - `fact_precios` (precios de venta y alquiler)
  - `fact_renta` (renta familiar disponible por barrio)
  - `fact_oferta_idealista` (oferta inmobiliaria actual de Idealista API)
- Registra la ejecución en `etl_runs`
- Crea/actualiza `data/processed/database.db`

**Notas**:
- `fact_demografia_ampliada` se usa cuando está disponible el dataset `pad_mdb_lloc-naix-continent_edat-q_sexe`
- `fact_renta` contiene renta agregada por barrio desde datos de sección censal
- `fact_oferta_idealista` requiere API credentials de Idealista y se actualiza ejecutando `scripts/extract_idealista.py`
- `dim_barrios` incluye geometrías GeoJSON cuando está disponible el archivo `barrios_geojson_*.json`
- Cada ejecución registra métricas y parámetros en `etl_runs` para trazabilidad.

### `data/logs/` - Logs de Extracción

**Propósito**: Resúmenes legibles de cada ejecución de extracción.

**Formato**: Archivos de texto plano con timestamp único.

**Ejemplo de nombre**:
```
extraction_20250115_143030.txt
```

**Contenido**:
- Fecha y rango de extracción
- Resumen por fuente con validación
- Cobertura temporal
- Estado de fuentes (exitosas/fallidas)
- Advertencias sobre datos sospechosos

### `logs/` - Logs del Sistema

**Propósito**: Logs detallados del sistema con rotación diaria.

**Formato**: Archivos de log con rotación automática.

**Ejemplo de nombre**:
```
data_extraction_20250115.log
```

**Características**:
- Rotación diaria automática
- Retención de 30 días
- Tamaño máximo: 10MB por archivo
- Encoding: UTF-8

## 🔧 Uso del Directorio de Salida

### Directorio por Defecto

Por defecto, los datos se guardan en `data/raw/`:

```bash
# Extracción estándar (guarda en data/raw/)
python scripts/extract_data.py \
    --year-start 2015 \
    --year-end 2025
```

**Archivos generados**:
```
data/raw/ine/ine_demographics_2015_2025_20250115_143022_123456.csv
data/raw/opendatabcn/opendatabcn_demografia-per-barris_2015_2025_20250115_143025_789012.csv
data/raw/opendatabcn/opendatabcn_habitatge-per-barris_2015_2025_20250115_143028_345678.csv
data/logs/extraction_20250115_143030.txt
```

### Directorio Personalizado

Puedes especificar un directorio personalizado con `--output-dir`:

```bash
# Extracción con directorio personalizado
python scripts/extract_data.py \
    --year-start 2015 \
    --year-end 2025 \
    --output-dir /custom/path/data
```

**Archivos generados**:
```
/custom/path/data/ine/ine_demographics_2015_2025_20250115_143022_123456.csv
/custom/path/data/opendatabcn/opendatabcn_demografia-per-barris_2015_2025_20250115_143025_789012.csv
/custom/path/data/logs/extraction_20250115_143030.txt
```

**Nota**: El directorio se crea automáticamente si no existe.

## 📊 Ejemplo de Resumen de Extracción

Después de cada extracción, se genera un resumen en `data/logs/extraction_{timestamp}.txt`:

```
================================================================================
RESUMEN DE EXTRACCIÓN DE DATOS
================================================================================

Fecha de extracción: 2025-01-15T14:30:30
Rango solicitado: 2015 - 2025
Fuentes solicitadas: ine, opendatabcn, idealista

--------------------------------------------------------------------------------
RESUMEN POR FUENTE
--------------------------------------------------------------------------------

✓ ine                                   1,234 registros [VÁLIDO]
✓ opendatabcn_demographics             5,678 registros [VÁLIDO]
✓ opendatabcn_housing                  3,456 registros [VÁLIDO]
✗ idealista                                  0 registros [VACÍO]

Total de registros extraídos: 10,368

--------------------------------------------------------------------------------
COBERTURA TEMPORAL
--------------------------------------------------------------------------------

⚠️  ine                             81.8% - Años faltantes: [2024, 2025]
✓   opendatabcn_demographics      100.0% - Completo
✓   opendatabcn_housing           100.0% - Completo

--------------------------------------------------------------------------------
ESTADO DE FUENTES
--------------------------------------------------------------------------------

✓ Fuentes exitosas: ine, opendatabcn_demographics, opendatabcn_housing
✗ Fuentes fallidas: idealista

--------------------------------------------------------------------------------
VALIDACIÓN DE DATOS
--------------------------------------------------------------------------------

⚠️  ADVERTENCIA: Las siguientes fuentes tienen pocos registros:
   - idealista (0 registros)

================================================================================
Resumen guardado: data/logs/extraction_20250115_143030.txt
================================================================================
```

## 🔄 Flujo de Datos

```
Fuentes Externas (INE, OpenDataBCN, Idealista)
         ↓
    [Extracción]
         ↓
   data/raw/          ← Datos brutos con timestamps únicos
         ↓
   [Procesamiento]     ← Futuro: limpieza y normalización
         ↓
  data/processed/      ← Datos listos para análisis
         ↓
   [Análisis]          ← Notebooks y scripts de análisis
```

## 📝 Convenciones

### Nombres de Archivos

1. **Datos raw**: `{source}_{dataset}_{year_range}_{timestamp}.{ext}`
2. **Metadata**: `extraction_metadata_{timestamp}.json`
3. **Resúmenes**: `extraction_{timestamp}.txt`
4. **Logs del sistema**: `data_extraction_{YYYYMMDD}.log`

### Timestamps

- **Formato**: `YYYYMMDD_HHMMSS_ffffff`
- **Ejemplo**: `20250115_143022_123456`
- **Propósito**: Garantizar unicidad y trazabilidad

### Validación

- **Mínimo de registros**: 10 (configurable via `MIN_RECORDS_WARNING`)
- **Estados**: `VÁLIDO`, `SOSPECHOSO`, `VACÍO`
- **Advertencias**: Automáticas en logs y resúmenes

## ✅ Resumen

- **Output por defecto**: `data/raw/` (con subdirectorios por fuente)
- **Output personalizado**: Especificable con `--output-dir`
- **Logs de extracción**: `data/logs/extraction_{timestamp}.txt`
- **Logs del sistema**: `logs/data_extraction_{YYYYMMDD}.log`
- **Datos procesados**: `data/processed/` (futuro)

Esta estructura mantiene claridad entre datos brutos, procesados y logs, fundamental para un proyecto data-driven profesional y open source.

## 📊 Esquema de Base de Datos

### Tablas de Dimensión

#### `dim_barrios`
Dimensión de barrios con información geográfica y administrativa.

```sql
CREATE TABLE dim_barrios (
    barrio_id INTEGER PRIMARY KEY,
    barrio_nombre TEXT NOT NULL,
    barrio_nombre_normalizado TEXT NOT NULL,
    distrito_id INTEGER,
    distrito_nombre TEXT,
    municipio TEXT,
    ambito TEXT,
    codi_districte TEXT,
    codi_barri TEXT,
    geometry_json TEXT,              -- GeoJSON con geometría del barrio
    source_dataset TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT
);
```

**Notas**:
- `geometry_json`: Contiene geometría en formato GeoJSON (Polygon) cuando está disponible
- `barrio_nombre_normalizado`: Versión normalizada para matching de nombres

### Tablas de Hechos

#### `fact_demografia`
Demografía estándar por barrio y año (población total, por sexo, hogares, etc.).

```sql
CREATE TABLE fact_demografia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    poblacion_total INTEGER,
    poblacion_hombres INTEGER,
    poblacion_mujeres INTEGER,
    hogares_totales INTEGER,
    edad_media REAL,
    porc_inmigracion REAL,
    densidad_hab_km2 REAL,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

#### `fact_demografia_ampliada` ⭐ NUEVO
Demografía detallada con edad quinquenal y nacionalidad por barrio, año, sexo y grupo de edad.

```sql
CREATE TABLE fact_demografia_ampliada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    sexo TEXT,                       -- 'hombre', 'mujer'
    grupo_edad TEXT,                 -- '18-34', '35-49', '50-64', '65+'
    nacionalidad TEXT,                -- 'Europa', 'América', 'África', 'Asia', 'Oceanía', 'No consta'
    poblacion INTEGER,
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Ejemplo de uso**:
```sql
-- Población joven (18-34) por nacionalidad en 2025
SELECT 
    b.barrio_nombre,
    d.nacionalidad,
    SUM(d.poblacion) as poblacion_total
FROM fact_demografia_ampliada d
JOIN dim_barrios b ON d.barrio_id = b.barrio_id
WHERE d.anio = 2025 
  AND d.grupo_edad = '18-34'
GROUP BY b.barrio_nombre, d.nacionalidad
ORDER BY poblacion_total DESC;
```

#### `fact_renta` ⭐ NUEVO
Renta Familiar Disponible (RFD) agregada por barrio y año.

```sql
CREATE TABLE fact_renta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    renta_euros REAL,                -- Métrica principal (promedio o mediana según configuración)
    renta_promedio REAL,
    renta_mediana REAL,
    renta_min REAL,
    renta_max REAL,
    num_secciones INTEGER,            -- Número de secciones censales agregadas
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Ejemplo de uso**:
```sql
-- Renta por barrio en 2022 con información del distrito
SELECT 
    b.barrio_nombre,
    b.distrito_nombre,
    r.renta_euros,
    r.renta_mediana,
    r.num_secciones
FROM fact_renta r
JOIN dim_barrios b ON r.barrio_id = b.barrio_id
WHERE r.anio = 2022
ORDER BY r.renta_euros DESC;
```

#### `fact_oferta_idealista` ⭐ NUEVO
Oferta inmobiliaria actual de Idealista API agregada por barrio, operación (venta/alquiler), año y mes.

```sql
CREATE TABLE fact_oferta_idealista (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    operacion TEXT NOT NULL,              -- 'sale' o 'rent'
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    num_anuncios INTEGER,                 -- Número de anuncios activos
    precio_medio REAL,
    precio_mediano REAL,
    precio_min REAL,
    precio_max REAL,
    precio_m2_medio REAL,
    precio_m2_mediano REAL,
    superficie_media REAL,
    superficie_mediana REAL,
    habitaciones_media REAL,
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    is_mock INTEGER DEFAULT 0,           -- 1 = datos mock, 0 = datos reales de API
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Ejemplo de uso**:
```sql
-- Oferta de venta por barrio en el último mes disponible (solo datos reales)
SELECT 
    b.barrio_nombre,
    b.distrito_nombre,
    o.anio,
    o.mes,
    o.num_anuncios,
    o.precio_medio,
    o.precio_m2_medio,
    o.superficie_media,
    o.is_mock
FROM fact_oferta_idealista o
JOIN dim_barrios b ON o.barrio_id = b.barrio_id
WHERE o.operacion = 'sale'
  AND o.is_mock = 0  -- Solo datos reales
  AND (o.anio, o.mes) = (
      SELECT MAX(anio), MAX(mes) 
      FROM fact_oferta_idealista 
      WHERE operacion = 'sale' AND is_mock = 0
  )
ORDER BY o.precio_m2_medio DESC;
```

#### `fact_precios`
Precios de vivienda (venta y alquiler) por barrio, año y período.

```sql
CREATE TABLE fact_precios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    periodo TEXT,
    trimestre INTEGER,
    precio_m2_venta REAL,
    precio_mes_alquiler REAL,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

### Tabla de Auditoría

#### `etl_runs`
Registro de ejecuciones del pipeline ETL para trazabilidad.

```sql
CREATE TABLE etl_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL,
    parameters TEXT                  -- JSON con parámetros y métricas de la ejecución
);
```

