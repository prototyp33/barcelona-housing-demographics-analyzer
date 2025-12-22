## Fuente: Inside Airbnb - Presión Turística

### Descripción general

**Inside Airbnb** es una plataforma independiente que recopila y publica datos públicos de Airbnb para análisis de políticas públicas y académicos. Los datos están disponibles públicamente en formato CSV comprimido desde su repositorio S3.

En este proyecto, estos datos se utilizan para construir la tabla de hechos `fact_presion_turistica`, que mide el impacto del turismo en el mercado de vivienda por barrio (`barrio_id`), año (`anio`) y mes (`mes`).

**URL base**: http://insideairbnb.com/get-the-data.html  
**Repositorio S3**: http://data.insideairbnb.com/spain/catalonia/barcelona/YYYY-MM-DD/data/

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios).
- **Frecuencia temporal**: Mensual (datos históricos desde 2011).
- **Variables clave**:
  - Número de listings activos por barrio
  - Porcentaje de viviendas completas vs. habitaciones compartidas
  - Precio promedio por noche
  - Tasa de ocupación (días ocupados / días disponibles)
  - Número de reviews por mes

### Datasets disponibles

Inside Airbnb proporciona tres tipos de archivos CSV:

1. **listings.csv.gz**: Información de propiedades listadas
   - Columnas principales: `id`, `neighbourhood`, `latitude`, `longitude`, `room_type`, `price`, `last_review`
   - Tamaño típico: ~19,000 registros (2025)

2. **calendar.csv.gz**: Disponibilidad y precios por fecha
   - Columnas principales: `listing_id`, `date`, `available`, `price`
   - Tamaño típico: ~7M registros (2025)

3. **reviews.csv.gz**: Reviews por listing
   - Columnas principales: `listing_id`, `date`
   - Tamaño típico: ~1M registros (2025)

### Esquema `fact_presion_turistica`

Columnas principales:

- `barrio_id` (INTEGER, FK a `dim_barrios.barrio_id`)
- `anio` (INTEGER)
- `mes` (INTEGER, 1-12)
- `num_listings_airbnb` (INTEGER): Número total de listings activos
- `pct_entire_home` (REAL): Porcentaje de listings que son viviendas completas (vs. habitaciones)
- `precio_noche_promedio` (REAL, €): Precio promedio por noche
- `tasa_ocupacion` (REAL, 0-1): Proporción de días ocupados sobre días disponibles
- `num_reviews_mes` (INTEGER): Número de reviews recibidos en el mes

### Procesamiento de datos

#### 1. Extracción

El extractor `AirbnbExtractor` descarga los archivos más recientes desde el repositorio S3 público de Inside Airbnb:

```python
from src.extraction.airbnb_extractor import AirbnbExtractor

extractor = AirbnbExtractor(output_dir=Path("data/raw/airbnb"))
results, metadata = extractor.extract_barcelona_data()
```

#### 2. Geocodificación

Los listings se mapean a barrios usando dos métodos complementarios:

1. **Geocodificación espacial** (preferido): Usa las coordenadas `latitude`/`longitude` de los listings y las geometrías de `dim_barrios.geometry_json` para determinar en qué barrio está cada listing mediante spatial join.

2. **Mapeo por nombre** (fallback): Si la geocodificación falla o no hay coordenadas, se usa el campo `neighbourhood` normalizado para buscar coincidencias con `barrio_nombre_normalizado`.

**Criterio de éxito**: ≥95% de listings mapeados a barrios.

#### 3. Agregación temporal

Los datos se agregan por `(barrio_id, anio, mes)`:

- **num_listings_airbnb**: `COUNT(listings.id)`
- **pct_entire_home**: `SUM(room_type = 'Entire home/apt') / COUNT(*) * 100`
- **precio_noche_promedio**: `AVG(price)` (limpio de símbolos $, €, comas)
- **tasa_ocupacion**: `AVG(available = 'f')` desde calendar.csv (días ocupados / total)
- **num_reviews_mes**: `COUNT(reviews.id)` agrupado por mes

#### 4. Extracción de fecha

La fecha (año/mes) se extrae de:
- `last_review` en listings.csv (preferido)
- `date` en calendar.csv o reviews.csv (si está disponible)
- Fecha actual (fallback si no hay fechas disponibles)

### Validaciones clave

El script `scripts/validate_presion_turistica.py` aplica las siguientes comprobaciones:

- **Cobertura de barrios**: `COUNT(DISTINCT barrio_id) >= 70` (≥95% de los 73 barrios)
- **Cobertura temporal mínima**: Presencia de años 2020 y 2024
- **Completitud**: ≥80% de registros con `num_listings_airbnb > 0`

Si alguna de estas condiciones no se cumple, el script devuelve un código de salida no cero.

### Actualización mensual

El script `scripts/update_airbnb_monthly.py` automatiza la actualización mensual:

1. Descarga los datos más recientes de Inside Airbnb
2. Ejecuta el ETL para procesar y cargar datos
3. Valida los datos cargados

**Ejecución manual**:
```bash
python -m scripts.update_airbnb_monthly
```

**Ejecución automática con cron** (primer día de cada mes a las 2 AM):
```bash
0 2 1 * * cd /path/to/project && python -m scripts.update_airbnb_monthly >> logs/airbnb_update.log 2>&1
```

### Limitaciones conocidas

1. **Tasa de ocupación**: El calendar.csv muestra disponibilidad futura, no ocupación histórica. Para ocupación histórica real, se necesitarían datos de calendar históricos o inferir desde reviews.

2. **Barrios sin datos**: Algunos barrios pueden no tener listings de Airbnb (ej: Vallbona, Baró de Viver). Esto es esperado y no indica un error.

3. **Fechas**: Los datos pueden tener fechas futuras (ej: calendar con fechas hasta 2026). El procesador filtra y agrupa correctamente por año/mes real.

### Referencias

- **Inside Airbnb**: http://insideairbnb.com/
- **Datos de Barcelona**: http://insideairbnb.com/get-the-data.html
- **Metodología**: http://insideairbnb.com/about.html

