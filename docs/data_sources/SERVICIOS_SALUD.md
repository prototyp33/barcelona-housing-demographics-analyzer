## Fuente: Servicios Sanitarios - Open Data BCN

### Descripción general

Los datos de **servicios sanitarios** son fundamentales para entender la accesibilidad a servicios básicos de salud en los barrios de Barcelona. Estos datos provienen del **Open Data BCN** del Ayuntamiento de Barcelona y se utilizan para construir la tabla de hechos `fact_servicios_salud`.

**URLs**:
- Portal: https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipament-sanitat
- API CKAN: `https://opendata-ajuntament.barcelona.cat/api/3/action/package_show?id=equipament-sanitat`
- Farmacias: https://opendata-ajuntament.barcelona.cat/data/es/dataset/sanitat-farmacies

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Anual (datos actualizados periódicamente).
- **Variables clave**:
  - `num_centros_salud`: Número de centros de salud por barrio
  - `num_hospitales`: Número de hospitales por barrio
  - `num_farmacias`: Número de farmacias por barrio
  - `total_servicios_sanitarios`: Total de servicios sanitarios
  - `densidad_servicios_por_km2`: Densidad de servicios por km²
  - `densidad_servicios_por_1000hab`: Densidad de servicios por 1000 habitantes

### Fuentes de datos

#### 1. Open Data BCN - Equipament Sanitat

Dataset oficial del Ayuntamiento de Barcelona con todos los equipamientos sanitarios de la ciudad (centros de salud y hospitales).

**Formato**: CSV, JSON (vía API CKAN)

**Datos disponibles**:
- Nombre del equipamiento
- Tipo de equipamiento (centro de salud, hospital)
- Dirección completa
- Coordenadas geográficas (latitud, longitud)
- Código de distrito/barrio

**Procesamiento**:
1. Extracción mediante `ServiciosSaludExtractor.extract_centros_salud_hospitales()`
2. **Validación de coordenadas**: Filtrado de registros con coordenadas válidas dentro del rango geográfico de Barcelona
   - Latitud: 41.35 - 41.45
   - Longitud: 2.05 - 2.25
   - Criterio: 100% de registros retornados tienen coordenadas válidas
3. **Filtrado**: Se excluyen farmacias del dataset de centros de salud
4. Geocodificación de coordenadas → barrio usando `dim_barrios.geometry_json` o `codi_barri`

**Criterio de aceptación**: ≥100 centros de salud/hospitales extraídos

#### 2. Open Data BCN - Farmacies

Dataset oficial del Ayuntamiento de Barcelona con todas las farmacias de la ciudad.

**Formato**: CSV, JSON (vía API CKAN)

**Datos disponibles**:
- Nombre de la farmacia
- Dirección completa
- Coordenadas geográficas (latitud, longitud)
- Código de distrito/barrio

**Procesamiento**:
1. Extracción mediante `ServiciosSaludExtractor.extract_farmacias()`
2. **Validación de coordenadas**: Filtrado de registros con coordenadas válidas dentro del rango geográfico de Barcelona
   - Latitud: 41.35 - 41.45
   - Longitud: 2.05 - 2.25
   - Criterio: 100% de registros retornados tienen coordenadas válidas
3. **Filtrado**: Se excluyen centros de salud del dataset de farmacias
4. Geocodificación de coordenadas → barrio usando `dim_barrios.geometry_json` o `codi_barri`

**Criterio de aceptación**: ≥200 farmacias extraídas

### Estructura de datos

#### Tabla `fact_servicios_salud`

```sql
CREATE TABLE fact_servicios_salud (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    num_centros_salud INTEGER DEFAULT 0,
    num_hospitales INTEGER DEFAULT 0,
    num_farmacias INTEGER DEFAULT 0,
    total_servicios_sanitarios INTEGER DEFAULT 0,
    densidad_servicios_por_km2 REAL,
    densidad_servicios_por_1000hab REAL,
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Índices**:
- `idx_fact_servicios_salud_unique`: Único en (barrio_id, anio)
- `idx_fact_servicios_salud_barrio_fecha`: En (barrio_id, anio)

### Métricas calculadas

#### Densidad de servicios sanitarios

1. **Densidad por km²**:
   ```
   densidad_servicios_por_km2 = total_servicios_sanitarios / area_km2
   ```
   - Mide la concentración geográfica de servicios sanitarios
   - Útil para comparar barrios de diferentes tamaños

2. **Densidad por 1000 habitantes**:
   ```
   densidad_servicios_por_1000hab = (total_servicios_sanitarios / poblacion_total) * 1000
   ```
   - Mide la accesibilidad relativa a la población
   - Útil para identificar barrios con mayor necesidad de servicios sanitarios

### Uso del extractor

#### Extracción básica

```python
from src.extraction.servicios_salud_extractor import ServiciosSaludExtractor
from pathlib import Path

# Crear extractor
extractor = ServiciosSaludExtractor(output_dir=Path("data/raw"))

# Extraer centros de salud y hospitales
df_centros, meta_centros = extractor.extract_centros_salud_hospitales()
print(f"Centros extraídos: {meta_centros['centros_with_valid_coords']}")

# Extraer farmacias
df_farmacias, meta_farmacias = extractor.extract_farmacias()
print(f"Farmacias extraídas: {meta_farmacias['farmacias_with_valid_coords']}")

# Extraer todo
df_all, meta_all = extractor.extract_all()
print(f"Total servicios: {len(df_all)}")
```

#### Procesamiento y carga en BD

```python
# Ejecutar script de procesamiento
python scripts/process_servicios_salud_data.py
```

El script:
1. Carga datos raw de `data/raw/servicios_salud/`
2. Geocodifica servicios sanitarios a barrios
3. Calcula densidades por barrio
4. Inserta datos en `fact_servicios_salud`

### Validación de datos

#### Criterios de aceptación

- ✅ **≥100 centros de salud/hospitales extraídos**: Verificado en metadata `centros_with_valid_coords`
- ✅ **≥200 farmacias extraídas**: Verificado en metadata `farmacias_with_valid_coords`
- ✅ **100% registros con coordenadas válidas**: Todos los registros retornados tienen coordenadas dentro del rango de Barcelona
- ✅ **Geocodificación completa**: Todos los servicios sanitarios asignados a un barrio válido

#### Validación post-procesamiento

```sql
-- Verificar cobertura por barrio
SELECT 
    COUNT(DISTINCT barrio_id) as barrios_con_datos,
    SUM(num_centros_salud) as total_centros,
    SUM(num_hospitales) as total_hospitales,
    SUM(num_farmacias) as total_farmacias,
    SUM(total_servicios_sanitarios) as total_servicios
FROM fact_servicios_salud
WHERE anio = 2025;

-- Top 10 barrios con más servicios sanitarios
SELECT 
    db.barrio_nombre,
    fs.num_centros_salud,
    fs.num_hospitales,
    fs.num_farmacias,
    fs.total_servicios_sanitarios,
    fs.densidad_servicios_por_1000hab
FROM fact_servicios_salud fs
JOIN dim_barrios db ON fs.barrio_id = db.barrio_id
WHERE fs.anio = 2025
ORDER BY fs.total_servicios_sanitarios DESC
LIMIT 10;
```

### Notas técnicas

#### Optimización de búsqueda

El extractor utiliza la API CKAN `package_search` para buscar datasets por palabras clave, mejorando significativamente el rendimiento comparado con iterar sobre todos los datasets.

#### Validación de contenido

El extractor incluye métodos `_is_centros_salud_dataset()` y `_is_farmacias_dataset()` que validan el contenido del dataset antes de procesarlo, evitando procesar datasets incorrectos.

#### Geocodificación dual

El procesamiento utiliza dos métodos de geocodificación:
1. **Mapeo directo por `codi_barri`**: Más eficiente cuando el dataset incluye el código de barrio
2. **Geocodificación espacial**: Fallback usando `shapely` y `geopandas` para asignar servicios a barrios basándose en coordenadas

### Referencias

- [Open Data BCN - Equipament Sanitat](https://opendata-ajuntament.barcelona.cat/data/es/dataset/equipament-sanitat)
- [Open Data BCN - Farmacies](https://opendata-ajuntament.barcelona.cat/data/es/dataset/sanitat-farmacies)
- [API CKAN Documentation](https://docs.ckan.org/en/2.9/api/)

