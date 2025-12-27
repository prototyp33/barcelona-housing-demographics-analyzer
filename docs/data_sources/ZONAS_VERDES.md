## Fuente: Zonas Verdes y Medio Ambiente - Open Data BCN

### Descripción general

Los datos de **zonas verdes y medio ambiente** son fundamentales para entender la calidad de vida y sostenibilidad ambiental en los barrios de Barcelona. Estos datos provienen del **Open Data BCN** del Ayuntamiento de Barcelona y se utilizan para construir la tabla de hechos `fact_medio_ambiente`, que amplía `fact_ruido` con métricas de zonas verdes.

**URLs**:
- Parques y jardines: https://opendata-ajuntament.barcelona.cat/data/es/dataset/parcs-i-jardins
- Arbolado: https://opendata-ajuntament.barcelona.cat/data/es/dataset/arbres

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Anual (datos actualizados periódicamente).
- **Variables clave**:
  - `superficie_zonas_verdes_m2`: Superficie total de zonas verdes en m²
  - `num_parques_jardines`: Número de parques y jardines
  - `num_arboles`: Número de árboles
  - `m2_zonas_verdes_por_habitante`: m² de zonas verdes por habitante (métrica clave)
  - `nivel_lden_medio`: Nivel sonoro equivalente día-tarde-noche [dB(A)] (de fact_ruido)
  - `nivel_ld_dia`: Nivel sonoro diurno [dB(A)] (de fact_ruido)
  - `nivel_ln_noche`: Nivel sonoro nocturno [dB(A)] (de fact_ruido)
  - `pct_poblacion_expuesta_65db`: % de población expuesta a >65 dB(A) (de fact_ruido)

### Fuentes de datos

#### 1. Parques y Jardines - Open Data BCN

Dataset oficial del Ayuntamiento de Barcelona con todos los parques y jardines de la ciudad.

**Formato**: CSV, JSON (vía API CKAN)

**Datos disponibles**:
- Nombre del parque/jardín
- Superficie (m² o hectáreas)
- Coordenadas geográficas (latitud, longitud)
- Código de distrito/barrio

**IDs de datasets potenciales**:
- `parcs-i-jardins`
- `parques-jardines`
- `parcs-jardins`
- `parques`
- `jardines`
- `zones-verdes`
- `zonas-verdes`

#### 2. Arbolado - Open Data BCN

Dataset oficial del Ayuntamiento de Barcelona con el inventario de árboles de la ciudad.

**Formato**: CSV, JSON (vía API CKAN)

**Datos disponibles**:
- Nombre científico y común del árbol
- Coordenadas geográficas (latitud, longitud)
- Código de distrito/barrio
- Especie y características

**IDs de datasets potenciales**:
- `arbres`
- `arbolado`
- `trees`
- `arboles`
- `arbrat`

### Procesamiento

#### 1. Extracción

El extractor `ZonasVerdesExtractor` busca múltiples datasets en Open Data BCN:

```python
from src.extraction.zonas_verdes_extractor import ZonasVerdesExtractor

extractor = ZonasVerdesExtractor()

# Extraer parques y jardines
df_parques, meta_parques = extractor.extract_parques_jardines()

# Extraer arbolado
df_arbolado, meta_arbolado = extractor.extract_arbolado()

# Extraer todo
df_all, meta_all = extractor.extract_all()
```

**Validación de coordenadas**: El extractor filtra automáticamente registros con coordenadas válidas dentro del rango geográfico de Barcelona:
- Latitud: 41.35 - 41.45
- Longitud: 2.05 - 2.25

#### 2. Geocodificación a barrios

Los datos se geocodifican a barrios usando `dim_barrios.geometry_json`:

```python
# El script process_zonas_verdes_data.py realiza:
# 1. Carga geometrías de barrios desde la BD
# 2. Crea GeoDataFrame de puntos de zonas verdes
# 3. Spatial join (within) para asignar barrios
```

#### 3. Agregación y cálculo de métricas

El script agrega datos por barrio y calcula:

- **Superficie total**: Suma de m² de zonas verdes por barrio
- **Número de parques/jardines**: Conteo de parques y jardines por barrio
- **Número de árboles**: Conteo de árboles por barrio
- **m² por habitante**: `superficie_zonas_verdes_m2 / poblacion_total`

```python
# Ejecutar procesamiento
python scripts/process_zonas_verdes_data.py
```

### Estructura de datos

#### Tabla: `fact_medio_ambiente`

```sql
CREATE TABLE fact_medio_ambiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    -- Ruido (compatibilidad con fact_ruido)
    nivel_lden_medio REAL,
    nivel_ld_dia REAL,
    nivel_ln_noche REAL,
    pct_poblacion_expuesta_65db REAL,
    -- Zonas verdes
    superficie_zonas_verdes_m2 REAL,
    num_parques_jardines INTEGER DEFAULT 0,
    num_arboles INTEGER DEFAULT 0,
    m2_zonas_verdes_por_habitante REAL,
    -- Metadata
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Índices**:
- `idx_fact_medio_ambiente_unique`: (barrio_id, anio)
- `idx_fact_medio_ambiente_barrio_fecha`: (barrio_id, anio)

### Métricas clave

#### m² de zonas verdes por habitante

Esta es la métrica principal para evaluar la calidad ambiental de un barrio:

```
m2_zonas_verdes_por_habitante = superficie_zonas_verdes_m2 / poblacion_total
```

**Interpretación**:
- **>20 m²/hab**: Excelente (recomendación OMS: mínimo 9 m²/hab)
- **10-20 m²/hab**: Bueno
- **5-10 m²/hab**: Aceptable
- **<5 m²/hab**: Insuficiente

### Scripts de procesamiento

#### Extracción
```bash
python -c "from src.extraction.zonas_verdes_extractor import ZonasVerdesExtractor; e = ZonasVerdesExtractor(); e.extract_all()"
```

#### Procesamiento y carga
```bash
python scripts/process_zonas_verdes_data.py
```

### Validaciones

- **Cobertura geográfica**: ≥ 95% barrios (≥69 de 73)
- **Completitud**: ≥ 95% campos obligatorios
- **Integridad referencial**: FK a `dim_barrios` validada
- **Coordenadas válidas**: 100% de registros retornados tienen coordenadas válidas dentro de Barcelona

### Notas importantes

- La tabla `fact_medio_ambiente` amplía `fact_ruido` con datos de zonas verdes
- Los datos de ruido pueden migrarse desde `fact_ruido` a `fact_medio_ambiente` para tener una vista unificada
- La geocodificación requiere que `dim_barrios.geometry_json` esté poblado
- El cálculo de m² por habitante requiere datos de población en `fact_demografia`

### Referencias

- [Open Data BCN - Parques y Jardines](https://opendata-ajuntament.barcelona.cat/data/es/dataset/parcs-i-jardins)
- [Open Data BCN - Arbolado](https://opendata-ajuntament.barcelona.cat/data/es/dataset/arbres)
- [OMS - Espacios verdes urbanos](https://www.who.int/es/news-room/fact-sheets/detail/urban-green-spaces)

