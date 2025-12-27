## Fuente: Movilidad y Transporte - Bicing y ATM

### Descripción general

Los datos de **movilidad y transporte** son fundamentales para entender la conectividad y accesibilidad de los barrios de Barcelona. Estos datos provienen de dos fuentes principales:
1. **Bicing**: Sistema de bicicletas públicas (API GBFS, sin autenticación)
2. **ATM**: Autoritat del Transport Metropolità (API requiere key, opcional)

Estos datos se utilizan para construir la tabla de hechos `fact_movilidad`.

**URLs**:
- Bicing GBFS: https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/
- ATM Open Data: https://www.ambmobilitat.cat/principales/Opendata.aspx

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo).
- **Frecuencia temporal**: Mensual/Anual (Bicing: tiempo real, ATM: según disponibilidad).
- **Variables clave**:
  - `estaciones_metro`: Número de estaciones de metro
  - `estaciones_fgc`: Número de estaciones de FGC
  - `paradas_bus`: Número de paradas de bus
  - `estaciones_bicing`: Número de estaciones Bicing
  - `capacidad_bicing`: Capacidad total de bicicletas
  - `uso_bicing_promedio`: Uso promedio de estaciones Bicing
  - `tiempo_medio_centro_minutos`: Tiempo estimado al centro (Plaza Catalunya)

### Fuentes de datos

#### 1. Bicing - API GBFS

Sistema de bicicletas públicas de Barcelona. API pública sin autenticación usando el estándar GBFS (General Bikeshare Feed Specification).

**Endpoints**:
- `station_information`: Información de estaciones (ubicación, capacidad)
- `station_status`: Estado actual (bicis disponibles, estaciones activas)

**Formato**: JSON (GBFS standard)

**Procesamiento**:
1. Extracción mediante `BicingExtractor`
2. Geocodificación de coordenadas → barrio usando `dim_barrios.geometry_json`
3. Agregación por barrio: número de estaciones, capacidad, uso promedio
4. Cálculo de tiempo medio al centro usando distancias geográficas

**Rate Limits**:
- **Bicing API**: 60 peticiones/minuto
- **Rate limit delay recomendado**: 1.0 segundo entre peticiones

#### 2. AMB Open Data Portal - Infraestructuras y Equipamientos

Portal público de Open Data de la Àrea Metropolitana de Barcelona (http://opendata.amb.cat) con datos de infraestructuras y equipamientos de transporte.

**Colecciones relevantes**:
- `infraestructures`: Infraestructuras de transporte
- `equipaments`: Equipamientos (puede incluir estaciones de transporte)
- `estudis_mobilitat`: Estudios de movilidad

**Formato**: JSON (también disponible CSV, XML, KML)

**Procesamiento**:
1. Extracción mediante `ATMExtractor` (usa portal Open Data AMB)
2. Búsqueda de estaciones de metro/bus en infraestructuras y equipamientos
3. Geocodificación de coordenadas → barrio
4. Agregación por barrio

**Rate Limits**: No especificado, usar delay de 2.0 segundos entre peticiones

**Nota**: Este portal es público y no requiere autenticación, a diferencia de la API oficial de ATM.

### Scripts de procesamiento

#### Extracción Bicing
```bash
python -c "from src.extraction.movilidad_extractor import BicingExtractor; e = BicingExtractor(); e.extract_all()"
```

#### Extracción AMB Open Data
```bash
python -c "from src.extraction.movilidad_extractor import ATMExtractor; e = ATMExtractor(); e.extract_all()"
```

#### Procesamiento y carga
```bash
python scripts/process_movilidad_data.py
```

### Estructura de datos

#### Tabla: `fact_movilidad`

```sql
CREATE TABLE fact_movilidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER,
    estaciones_metro INTEGER DEFAULT 0,
    estaciones_fgc INTEGER DEFAULT 0,
    paradas_bus INTEGER DEFAULT 0,
    estaciones_bicing INTEGER DEFAULT 0,
    capacidad_bicing INTEGER DEFAULT 0,
    uso_bicing_promedio REAL,
    tiempo_medio_centro_minutos REAL,
    dataset_id TEXT,
    source TEXT DEFAULT 'atm_opendata',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

### Validaciones

- **Cobertura de estaciones Bicing**: ≥200 estaciones extraídas con coordenadas válidas
- **Validación de coordenadas**: 100% de registros retornados tienen coordenadas válidas dentro del rango de Barcelona
- **Cobertura geográfica**: ≥ 95% barrios (≥69 de 73)
- **Completitud**: ≥ 95% campos obligatorios
- **Integridad referencial**: FK a `dim_barrios` validada
- **Tests unitarios**: Cobertura ≥80%

### Notas importantes

- **Bicing**: Datos en tiempo real, actualizar periódicamente (mensual recomendado)
- **AMB Open Data**: Portal público sin autenticación. Usar para infraestructuras y equipamientos de transporte.
- **Validación automática**: Los extractores validan automáticamente que todas las coordenadas estén dentro del rango geográfico de Barcelona antes de retornar los datos
- El cálculo de tiempo al centro usa velocidad promedio de 20 km/h (transporte público)
- La geocodificación requiere que `dim_barrios` tenga `geometry_json` poblado
- Los datos de AMB pueden requerir filtrado para identificar específicamente estaciones de metro/bus
- Los extractores manejan correctamente errores 503 (Service Unavailable) de la API de Bicing

### Criterios de Aceptación

- ✅ ≥200 estaciones Bicing extraídas (validación automática)
- ✅ Infraestructuras AMB procesadas (metro, bus, FGC)
- ✅ Tests pasan con cobertura ≥80% (86% actual)
- ✅ Documentación completa
- ✅ Tabla `fact_movilidad` poblada con datos de 73 barrios

### Dependencias

```bash
pip install geopy  # Para cálculo de distancias geográficas
pip install shapely geopandas  # Para geocodificación
```

### Referencias

- [Bicing GBFS API](https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/)
- [AMB Open Data Portal](http://opendata.amb.cat)
- [AMB Open Data API Documentation](http://opendata.amb.cat) (ver colecciones: infraestructures, equipaments)
- [GBFS Specification](https://github.com/MobilityData/gbfs)

