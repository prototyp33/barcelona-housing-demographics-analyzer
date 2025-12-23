## Fuente: Contaminación Acústica (Ruido) - Open Data BCN

### Descripción general

Los datos de **contaminación acústica** (ruido ambiental) son fundamentales para entender la calidad de vida en los barrios de Barcelona. Estos datos provienen principalmente del **Mapa Estratégico de Ruido (MER)** y la **Red de Monitorización de Ruido Ambiental** del Ayuntamiento de Barcelona.

En este proyecto, estos datos se utilizan para construir la tabla de hechos `fact_ruido`, que mide los niveles de ruido por barrio (`barrio_id`) y año (`anio`).

**URLs**:
- Mapa de ruido: https://opendata-ajuntament.barcelona.cat/data/es/dataset/mapa-ruido
- Red monitorización: https://opendata-ajuntament.barcelona.cat/data/es/dataset/xarxasoroll-equipsmonitor-dades

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Anual (objetivo: 2022, último Mapa Estratégico de Ruido disponible).
- **Variables clave**:
  - `nivel_lden_medio`: Nivel sonoro equivalente día-tarde-noche [dB(A)]
  - `nivel_ld_dia`: Nivel sonoro diurno (7-21h) [dB(A)]
  - `nivel_ln_noche`: Nivel sonoro nocturno (23-7h) [dB(A)]
  - `pct_poblacion_expuesta_65db`: Porcentaje de población expuesta a >65 dB(A)

### Fuentes de datos

#### 1. Mapas Estratégicos de Ruido (MER)

Los MER son mapas ráster (GeoTIFF) que representan los niveles de ruido en toda la ciudad. Se actualizan periódicamente (último disponible: 2022).

**Formato**: Ráster GeoTIFF con valores en dB(A)

**Procesamiento**: Requiere herramientas GIS (rasterio, geopandas) para:
- Extraer valores del ráster dentro de cada geometría de barrio
- Calcular estadísticas (media, máximo, mínimo) por barrio

#### 2. Red de Monitorización

La red de sensores proporciona datos horarios de niveles de ruido en puntos específicos de la ciudad.

**Formato**: CSV con datos horarios por sensor

**Procesamiento**: Agregación temporal (horario → mensual → anual) y espacial (sensor → barrio)

#### 3. Datasets CSV agregados (Preferido)

Si hay datasets CSV ya agregados por barrio en Open Data BCN, estos son los más fáciles de procesar.

**IDs potenciales**:
- `mapa-ruido`
- `mapa-ruido-barcelona`
- `mapa-estrategic-soroll`
- `rasters-mapa-estrategic-soroll`
- `xarxasoroll-equipsmonitor-dades`

### Esquema `fact_ruido`

Columnas principales:

- `barrio_id` (INTEGER, FK a `dim_barrios.barrio_id`)
- `anio` (INTEGER)
- `nivel_lden_medio` (REAL): Nivel sonoro equivalente día-tarde-noche [dB(A)]
- `nivel_ld_dia` (REAL): Nivel sonoro diurno (7-21h) [dB(A)]
- `nivel_ln_noche` (REAL): Nivel sonoro nocturno (23-7h) [dB(A)]
- `pct_poblacion_expuesta_65db` (REAL): Porcentaje de población expuesta a >65 dB(A)

### Procesamiento de datos

#### 1. Extracción

El extractor `RuidoExtractor` intenta múltiples métodos en orden:

```python
from src.extraction.ruido_extractor import RuidoExtractor

extractor = RuidoExtractor(output_dir=Path("data/raw/ruido"))

# Extraer datos agregados por barrio
df, metadata = extractor.extract_ruido_barrio(anio=2022)

# O extraer mapas ráster
raster_path, metadata = extractor.extract_mapas_ruido(anio=2022)

# O extraer datos de sensores
df_sensors, metadata = extractor.extract_red_monitorizacion(anio=2022, mes=None)
```

#### 2. Procesamiento GIS (si hay rásteres)

Si se descargan mapas ráster, el procesador puede calcular estadísticas por barrio:

```python
# Requiere: rasterio, geopandas, shapely
from src.processing.prepare_ruido import prepare_ruido

result = prepare_ruido(
    raw_data_path=Path("data/raw/ruido"),
    barrios_df=dim_barrios,  # Debe incluir geometry_json
    poblacion_df=poblacion_df,  # Para calcular exposición
)
```

El procesador:
1. Carga el ráster con `rasterio`
2. Crea un GeoDataFrame de barrios con `geopandas`
3. Extrae valores del ráster dentro de cada geometría de barrio
4. Calcula estadísticas (media, máximo, mínimo)

#### 3. Mapeo de barrios

Los datos se mapean a `barrio_id` usando:
- Nombre de barrio normalizado (si está disponible)
- `codi_barri` (si está disponible)

#### 4. Cálculo de exposición

El porcentaje de población expuesta a >65 dB(A) se calcula usando:
- Nivel Lden medio del barrio
- Datos de población desde `fact_demografia`

**Simplificación actual**: Si `nivel_lden_medio > 65`, se asume 100% de población expuesta. En la realidad, esto requeriría datos más detallados de distribución espacial dentro del barrio.

#### 5. Agregación temporal

Los datos se agregan por `(barrio_id, anio)`:
- `nivel_lden_medio`: `AVG(nivel_lden)`
- `nivel_ld_dia`: `AVG(nivel_ld)`
- `nivel_ln_noche`: `AVG(nivel_ln)`
- `pct_poblacion_expuesta_65db`: `AVG(pct_exposicion)`

### Validaciones clave

El script `scripts/validate_ruido.py` aplica las siguientes comprobaciones:

- **Cobertura de barrios**: `COUNT(DISTINCT barrio_id) = 73`
- **Cobertura temporal mínima**: Presencia del año 2022
- **Completitud**: ≥80% de registros con `nivel_lden_medio > 0`
- **Rangos válidos**: Niveles entre 40-80 dB(A) (rango típico para zonas urbanas)

Si alguna de estas condiciones no se cumple, el script devuelve un código de salida no cero.

### Limitaciones conocidas

1. **Dependencias GIS**: El procesamiento de mapas ráster requiere:
   - `rasterio`: Para leer archivos GeoTIFF
   - `geopandas`: Para operaciones espaciales
   - `shapely`: Para geometrías
   
   Si no están disponibles, el procesador usa datos CSV como fallback.

2. **Cobertura temporal**: Los Mapas Estratégicos de Ruido se actualizan periódicamente (no anualmente). El último disponible suele ser de 2022.

3. **Cálculo de exposición**: La estimación actual del porcentaje de población expuesta es simplificada. Una implementación más precisa requeriría:
   - Datos de distribución espacial de población dentro del barrio
   - Superposición detallada de mapas de ruido con datos demográficos

4. **Agregación de sensores**: Si se usan datos de sensores, la agregación espacial (sensor → barrio) requiere:
   - Mapeo de ubicaciones de sensores a barrios
   - Interpolación o asignación proporcional si un sensor está cerca de múltiples barrios

### Preparación de datos manuales

Si necesitas preparar archivos CSV manualmente:

1. Crear directorio: `data/raw/ruido/`
2. Preparar CSV con columnas mínimas:
   - `barrio` o `barrio_id` o `codi_barri`
   - `anio` o `any`
   - `nivel_lden` o `nivel_lden_medio` (opcional: `nivel_ld`, `nivel_ln`)
3. Nombrar el archivo con patrón: `ruido_*.csv` o `*ruido*.csv`
4. Ejecutar el ETL: `python -m src.etl.pipeline`

**Ejemplo de formato CSV**:
```csv
barrio,anio,nivel_lden,nivel_ld,nivel_ln
Barrio 1,2022,65.5,68.0,55.0
Barrio 2,2022,58.2,60.0,50.0
```

### Referencias

- **Open Data BCN - Mapa de Ruido**: https://opendata-ajuntament.barcelona.cat/data/es/dataset/mapa-ruido
- **Open Data BCN - Red Monitorización**: https://opendata-ajuntament.barcelona.cat/data/es/dataset/xarxasoroll-equipsmonitor-dades
- **Directiva Europea 2002/49/CE**: Sobre evaluación y gestión del ruido ambiental
- **Real Decreto 1367/2007**: Desarrollo de la directiva europea en España

