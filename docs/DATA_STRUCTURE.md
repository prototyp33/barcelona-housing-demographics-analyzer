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
├── database.db          # SQLite con tablas dim_barrios, fact_precios, fact_demografia y etl_runs
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
- Detecta automáticamente los últimos archivos en `data/raw/opendatabcn/`
- Construye la dimensión de barrios (`dim_barrios`)
- Genera las tablas de hechos `fact_demografia` y `fact_precios`
- Registra la ejecución en `etl_runs`
- Crea/actualiza `data/processed/database.db`

**Notas**:
- Actualmente `fact_precios` solo contiene precios de venta (`habitatges-2na-ma`). Los precios de alquiler quedan en `NULL` hasta encontrar un dataset válido.
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

