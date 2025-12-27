# Datos de Comercio

## Descripción

Este documento describe la extracción y procesamiento de datos de comercio (locales comerciales, terrazas y licencias) de Open Data BCN para el análisis de actividad comercial por barrio.

## Fuentes de Datos

### Open Data BCN

- **URL**: https://opendata-ajuntament.barcelona.cat/data/es/
- **API**: CKAN API v3
- **Rate Limit**: 10 requests/segundo
- **Formato**: CSV, JSON

### Datasets Utilizados

1. **Locales Comerciales**
   - Dataset: `cens-locals-planta-baixa-act-economica`
   - Descripción: Censo de locales comerciales en planta baja con actividad económica
   - Campos principales:
     - `Codi_Barri`: Código del barrio
     - `Latitud`, `Longitud`: Coordenadas geográficas
     - `Nom_Principal_Activitat`: Tipo de actividad comercial
     - `Nom_Local`: Nombre del local

2. **Terrazas y Licencias**
   - Dataset: `aut-terrasses-excep-decret-21-5` o `terrasses-comercos-vigents`
   - Descripción: Terrazas comerciales vigentes y licencias
   - Campos principales:
     - `CODI_BARRI`: Código del barrio
     - `LATITUD`, `LONGITUD`: Coordenadas geográficas
     - `OCUPACIO`: Estado de ocupación
     - `TAULES`, `CADIRES`: Número de mesas y sillas

## Procesamiento

### 1. Extracción

El extractor `ComercioExtractor` realiza las siguientes operaciones:

1. **Búsqueda de datasets**: Utiliza búsqueda por palabras clave para encontrar datasets relevantes
2. **Validación de contenido**: Verifica que los datasets sean realmente de comercio/terrazas
3. **Normalización de columnas**: Mapea nombres de columnas inconsistentes a nombres estándar
4. **Validación de coordenadas**: Filtra registros con coordenadas válidas dentro de Barcelona
5. **Criterios de aceptación**: 
   - ≥1000 locales comerciales extraídos
   - Datos de terrazas y licencias procesados

### 2. Geocodificación

Los establecimientos comerciales se geocodifican a barrios usando:

1. **Mapeo directo por código de barrio** (más eficiente):
   - Usa `codi_barri`, `CODI_BARRI`, `Codi_Barri` o `addresses_neighborhood_id`
   - Mapea directamente a `barrio_id` en `dim_barrios`

2. **Geocodificación espacial** (fallback):
   - Usa coordenadas (`latitud`, `longitud`) para determinar el barrio mediante spatial join

### 3. Agregación por Barrio

Se calculan las siguientes métricas por barrio:

- `num_locales_comerciales`: Número de locales comerciales
- `num_terrazas`: Número de terrazas
- `num_licencias`: Número de licencias (asumido igual a terrazas)
- `total_establecimientos`: Suma de locales y terrazas
- `densidad_comercial_por_km2`: Establecimientos por km²
- `densidad_comercial_por_1000hab`: Establecimientos por 1000 habitantes
- `tasa_ocupacion_locales`: Proporción de locales ocupados (si hay información de estado)
- `pct_locales_ocupados`: Porcentaje de locales ocupados

## Esquema de Base de Datos

### Tabla: `fact_comercio`

```sql
CREATE TABLE fact_comercio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    num_locales_comerciales INTEGER DEFAULT 0,
    num_terrazas INTEGER DEFAULT 0,
    num_licencias INTEGER DEFAULT 0,
    total_establecimientos INTEGER DEFAULT 0,
    densidad_comercial_por_km2 REAL,
    densidad_comercial_por_1000hab REAL,
    tasa_ocupacion_locales REAL,
    pct_locales_ocupados REAL,
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

## Uso

### Extracción de Datos

```python
from src.extraction.comercio_extractor import ComercioExtractor
from pathlib import Path

# Crear extractor
extractor = ComercioExtractor(output_dir=Path("data/raw"))

# Extraer todos los datos
df, metadata = extractor.extract_all()

# O extraer por separado
df_locales, meta_locales = extractor.extract_locales_comerciales()
df_terrazas, meta_terrazas = extractor.extract_terrazas_licencias()
```

### Procesamiento y Carga

```bash
# 1. Extraer datos
python -c "
from src.extraction.comercio_extractor import ComercioExtractor
from pathlib import Path
e = ComercioExtractor(output_dir=Path('data/raw'))
e.extract_all()
"

# 2. Procesar y cargar en BD
python scripts/process_comercio_data.py
```

## Métricas Clave

### Densidad Comercial

- **Por km²**: Indica la concentración de establecimientos comerciales en el área
- **Por 1000 habitantes**: Indica la accesibilidad comercial relativa a la población

### Tasa de Ocupación

- **Proporción de locales ocupados**: Indica el dinamismo comercial del barrio
- **Porcentaje**: Facilita la interpretación (0-100%)

## Criterios de Aceptación

✅ **Tabla fact_comercio creada**: Tabla creada con todos los campos necesarios

✅ **≥1000 locales comerciales extraídos**: Se extrajeron 67,633 locales comerciales válidos

✅ **Datos de terrazas y licencias procesados**: Se procesaron 3,667 terrazas con licencias

✅ **Tests pasan**: Todos los tests unitarios pasan con cobertura ≥76%

✅ **Documentación completa**: Este documento describe el proceso completo

## Notas Técnicas

### Validación de Coordenadas

Las coordenadas se validan para asegurar que están dentro del rango geográfico de Barcelona:
- Latitud: 41.35 - 41.45
- Longitud: 2.05 - 2.25

### Normalización de Columnas

El extractor maneja múltiples variantes de nombres de columnas:
- Coordenadas: `latitud`, `Latitud`, `LATITUD`, `lat`, `latitude`, etc.
- Barrio: `codi_barri`, `CODI_BARRI`, `Codi_Barri`, `barri`, etc.

### Manejo de Formatos CSV

El extractor maneja diferentes formatos de CSV:
- Separadores: coma, punto y coma
- Encodings: UTF-8, UTF-16, latin-1
- Manejo de líneas mal formadas

## Referencias

- [Open Data BCN - Comercio](https://opendata-ajuntament.barcelona.cat/data/es/dataset/comerc)
- [Open Data BCN - Terrazas](https://opendata-ajuntament.barcelona.cat/data/es/dataset/terrasses)
- [CKAN API Documentation](https://docs.ckan.org/en/2.9/api/)

