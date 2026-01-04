# Plan de Integración - Calidad del Aire

## Estado Actual

### ✅ Completado

1. **Extractor base creado**: `src/extraction/calidad_aire_extractor.py`
2. **Datasets identificados**:
   - Catálogo de contaminantes (21 tipos)
   - Estaciones de medición (2018-2025, 55 estaciones en 2025)
3. **Límites OMS definidos** en el código

### ⏳ Pendiente

- Encontrar dataset con mediciones reales
- Mapear estaciones a barrios
- Agregar datos por barrio
- Cargar en `fact_calidad_aire`

---

## Datasets Disponibles en Open Data BCN

### 1. Catálogo de Contaminantes

- **ID**: `6960936a-95ed-4cc4-a6ec-e089197ccd8b`
- **Archivo**: `qualitat_aire_contaminants.csv`
- **Registros**: 21 contaminantes
- **Contenido**: Códigos, nombres y unidades

**Contaminantes principales:**

```
1  - SO2 (Dióxido de azufre)
8  - NO2 (Dióxido de nitrógeno)
9  - PM2.5 (Partículas finas)
10 - PM10 (Partículas en suspensión)
14 - O3 (Ozono)
22 - Black Carbon
```

### 2. Estaciones de Medición

- **ID**: `4dff88b1-151b-48db-91c2-45007cd5d07a`
- **Archivos**: Por año (2018-2025)
- **Registros**: 55 estaciones (2025)
- **Columnas**:
  - `Estacio` - Código de estación
  - `nom_cabina` - Nombre de la estación
  - `codi_dtes` - Código de distrito
  - `zqa` - Zona de calidad del aire
  - `codi_eoi` - Código EOI
  - `longitud`, `latitud` - Coordenadas

### 3. Mapas de Inmisión (Air quality immission maps)

- **ID**: `d8f6af6e-e03e-462d-b3c8-d40b64179446`
- **Recursos**: 54 archivos
- **Tipo**: Mapas raster/vectoriales de concentraciones
- **Uso**: Interpolación espacial de contaminantes

### 4. Población Expuesta (Study of population exposed)

- **ID**: `a910281c-a5b0-4ed5-98a7-c7957293ac8c`
- **Recursos**: 6 archivos
- **Contenido**: Análisis de población expuesta por niveles de contaminación

---

## Estrategia de Integración

### Opción A: Usar Mapas de Inmisión (Recomendado)

**Ventaja**: Datos ya agregados espacialmente  
**Proceso**:

1. Descargar mapas raster de NO2, PM10, PM2.5, O3
2. Calcular promedio por barrio usando geometrías
3. Generar índice de calidad compuesto

**Implementación**:

```python
# Usar dataset d8f6af6e-e03e-462d-b3c8-d40b64179446
# Buscar archivos GeoJSON o Shapefile por contaminante
# Intersectar con geometrías de barrios
```

### Opción B: Agregar desde Estaciones

**Ventaja**: Datos más granulares  
**Proceso**:

1. Obtener mediciones horarias/diarias por estación
2. Mapear estaciones a barrios (por coordenadas)
3. Calcular promedios anuales por barrio

**Desafío**: Necesitamos encontrar el dataset de mediciones

### Opción C: Usar Datos de Población Expuesta

**Ventaja**: Ya incluye análisis de impacto  
**Proceso**:

1. Descargar dataset `a910281c-a5b0-4ed5-98a7-c7957293ac8c`
2. Extraer datos por barrio si están disponibles
3. Usar como proxy de calidad del aire

---

## Próximos Pasos Concretos

### Paso 1: Explorar Dataset de Mapas de Inmisión

```bash
python3 -c "
from src.extraction.calidad_aire_extractor import CalidadAireExtractor
extractor = CalidadAireExtractor()
info = extractor.get_dataset_info('d8f6af6e-e03e-462d-b3c8-d40b64179446')

# Listar recursos
for i, resource in enumerate(info['resources'][:10]):
    print(f'{i+1}. {resource[\"name\"]} ({resource.get(\"format\", \"N/A\")})')
"
```

### Paso 2: Identificar Archivos GeoJSON/CSV Útiles

Buscar archivos que contengan:

- Datos por barrio o distrito
- Promedios anuales
- Múltiples contaminantes

### Paso 3: Actualizar Extractor

Añadir método específico para procesar mapas de inmisión:

```python
def extract_mapas_inmision(self, year: int, contaminante: str) -> pd.DataFrame:
    """Extrae datos de mapas de inmisión por barrio."""
    pass
```

### Paso 4: Mapear a Barrios

Si los datos son por coordenadas:

```python
import geopandas as gpd

# Cargar geometrías de barrios
barrios = gpd.read_file('geometrias_barrios.geojson')

# Intersectar con datos de calidad del aire
# Calcular promedio por barrio
```

### Paso 5: Cargar en Base de Datos

```sql
INSERT INTO fact_calidad_aire (
    barrio_id,
    anio,
    no2_promedio_anual,
    pm10_promedio_anual,
    pm25_promedio_anual,
    o3_promedio_anual,
    indice_calidad_aire,
    categoria_calidad,
    etl_loaded_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
```

---

## Estructura de Tabla Objetivo

```sql
CREATE TABLE fact_calidad_aire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,

    -- Contaminantes principales (μg/m³)
    no2_promedio_anual REAL,
    pm10_promedio_anual REAL,
    pm25_promedio_anual REAL,
    o3_promedio_anual REAL,
    so2_promedio_anual REAL,

    -- Índices y categorías
    indice_calidad_aire REAL,  -- 0-100 (100 = excelente)
    categoria_calidad TEXT,     -- Excelente, Buena, Regular, Mala

    -- Comparación con límites OMS
    excede_limite_no2 BOOLEAN,
    excede_limite_pm10 BOOLEAN,
    excede_limite_pm25 BOOLEAN,

    -- Metadatos
    source TEXT DEFAULT 'opendata_bcn_aire',
    dataset_id TEXT,
    etl_loaded_at TEXT,

    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id),
    UNIQUE(barrio_id, anio)
);
```

---

## Alternativa Rápida: Datos Sintéticos para Testing

Si no encontramos datos reales rápidamente, podemos generar datos sintéticos basados en:

1. Distancia al centro (más contaminación en centro)
2. Densidad de tráfico (correlación con NO2)
3. Zonas industriales (PM10)
4. Datos históricos de otras ciudades similares

```python
def generate_synthetic_air_quality(barrios_df: pd.DataFrame) -> pd.DataFrame:
    """Genera datos sintéticos de calidad del aire para testing."""
    # Usar coordenadas del centro de Barcelona
    # Calcular distancia al centro
    # Aplicar modelo de degradación
    pass
```

---

## Recursos Adicionales

### APIs Alternativas

- **Gencat XVPCA**: https://mediambient.gencat.cat/ca/05_ambits_dactuacio/atmosfera/qualitat_de_laire/
- **European Environment Agency**: https://www.eea.europa.eu/data-and-maps
- **AEMET**: Datos meteorológicos correlacionados

### Documentación

- Límites OMS 2021: https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines
- Normativa UE: Directiva 2008/50/CE

---

## Estimación de Esfuerzo

- **Exploración de datasets**: 30 min
- **Desarrollo de extractor**: 1-2 horas
- **Mapeo a barrios**: 1 hora
- **Testing y validación**: 30 min
- **Carga en DB**: 30 min

**Total estimado**: 3-4 horas

---

**Última actualización**: 2026-01-04  
**Estado**: En progreso  
**Prioridad**: Alta
