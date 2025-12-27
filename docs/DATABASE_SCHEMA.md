# Esquema de Base de Datos - Barcelona Housing Demographics Analyzer

## Arquitectura General

La base de datos sigue un modelo **dimensional (star schema)** con:

- **2 tablas de dimensión**: `dim_barrios` y `dim_barrios_extended` (Maestra ampliada con KPIs)
- **1 tabla de dimensión temporal**: `dim_tiempo` (períodos anuales y trimestrales)
- **8/24 tablas de hechos/vistas** (`fact_*`): Estructura v2.0 Foundation con retrocompatibilidad
- **1 tabla de auditoría**: `etl_runs` (registro de ejecuciones ETL)

## Diagrama ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    dim_barrios ||--|| dim_barrios_extended : "extended by"
    dim_barrios ||--o{ fact_precios : "has"
    dim_barrios ||--o{ fact_demografia : "has"
    dim_barrios ||--o{ fact_renta : "has"
    dim_barrios ||--o{ fact_educacion : "has"
    dim_barrios ||--o{ fact_presion_turistica : "has"
    dim_barrios ||--o{ fact_hut : "has"
    dim_barrios ||--o{ fact_visados : "has"
    dim_barrios ||--o{ fact_desempleo : "has"
    dim_barrios ||--o{ fact_movilidad : "has"
    dim_barrios ||--o{ fact_regulacion : "has"
    dim_barrios ||--o{ fact_comercio : "has"
    dim_barrios ||--o{ fact_servicios_salud : "has"
    dim_barrios ||--o{ fact_seguridad : "has"
    dim_barrios ||--o{ fact_medio_ambiente : "has"

    fact_airbnb ..> fact_presion_turistica : "view"
    fact_control_alquiler ..> fact_regulacion : "view"
    fact_accesibilidad ..> fact_movilidad : "view"
    fact_centralidad ..> fact_comercio : "view"

    dim_barrios {
        INTEGER barrio_id PK
        TEXT barrio_nombre
        TEXT barrio_nombre_normalizado UK
        TEXT codi_barri
        TEXT geometry_json
        INTEGER distrito_id
        TEXT distrito_nombre
    }

    dim_barrios_extended {
        INTEGER barrio_id PK
        TEXT barrio_nombre
        TEXT distrito_nombre
        REAL indice_gentrificacion_relativo
        REAL indice_vulnerabilidad_socioeconomica
        TEXT clase_social_predominante
        TEXT perfil_demografico_resumen
        REAL precio_m2_venta_actual
        REAL variacion_precio_12m
        REAL densidad_comercial_kpi
        TEXT etl_updated_at
    }

    dim_tiempo {
        INTEGER time_id PK
        INTEGER anio
        INTEGER trimestre
        INTEGER mes
        TEXT periodo UK
    }

    fact_precios {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        TEXT periodo
        INTEGER trimestre
        REAL precio_m2_venta
        REAL precio_mes_alquiler
    }

    fact_demografia {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        INTEGER poblacion_total
        INTEGER poblacion_hombres
        INTEGER poblacion_mujeres
        REAL edad_media
        REAL densidad_hab_km2
    }

    fact_renta {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        REAL renta_euros
        REAL renta_promedio
        REAL renta_mediana
    }

    fact_educacion {
        INTEGER barrio_id FK
        INTEGER anio
        REAL pct_sin_estudios
        REAL pct_primaria
        REAL pct_secundaria
        REAL pct_universitarios
        INTEGER poblacion_16plus
    }

    fact_movilidad {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        INTEGER mes
        INTEGER estaciones_metro
        INTEGER estaciones_bicing
        REAL tiempo_medio_centro_minutos
    }

    fact_servicios_salud {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        INTEGER num_centros_salud
        INTEGER num_farmacias
        REAL densidad_servicios_por_1000hab
    }

    fact_comercio {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        INTEGER num_locales_comerciales
        INTEGER num_terrazas
        REAL densidad_comercial_por_1000hab
    }

    fact_calidad_aire {
        INTEGER barrio_id FK
        INTEGER anio
        REAL no2_mean
        REAL pm25_mean
        REAL pm10_mean
        REAL o3_mean
    }

    fact_soroll {
        INTEGER barrio_id FK
        INTEGER anio
        REAL lden_mean
        REAL pct_exposed_65db
    }
```

## Tablas de Dimensión

### 1. `dim_barrios` (Dimensión Principal)

**Descripción**: Tabla maestra con información de los 73 barrios de Barcelona.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS dim_barrios (
    barrio_id INTEGER PRIMARY KEY,
    barrio_nombre TEXT NOT NULL,
    barrio_nombre_normalizado TEXT NOT NULL,
    distrito_id INTEGER,
    distrito_nombre TEXT,
    municipio TEXT,
    ambito TEXT,
    codi_districte TEXT,
    codi_barri TEXT,
    geometry_json TEXT,
    source_dataset TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_barrios_nombre
ON dim_barrios (barrio_nombre_normalizado);
```

**Campos principales**:

- `barrio_id` (PK): Identificador único del barrio
- `barrio_nombre`: Nombre del barrio
- `barrio_nombre_normalizado`: Nombre normalizado para búsquedas
- `codi_barri`: Código oficial del barrio (usado para geocodificación)
- `geometry_json`: Geometría GeoJSON del barrio (para análisis espacial)
- `distrito_id`, `distrito_nombre`: Información del distrito
- `municipio`, `ambito`: Información administrativa

**Índices**:

- `idx_dim_barrios_nombre`: Único en `barrio_nombre_normalizado`

**Relaciones**:

- Todas las tablas `fact_*` tienen `FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)`

### 2. `dim_tiempo` (Dimensión Temporal)

**Descripción**: Tabla de períodos temporales (años y trimestres).

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS dim_tiempo (
    time_id INTEGER PRIMARY KEY AUTOINCREMENT,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    mes INTEGER,
    periodo TEXT NOT NULL,
    year_quarter TEXT,
    year_month TEXT,
    es_fin_de_semana INTEGER,
    es_verano INTEGER,
    estacion TEXT,
    dia_semana TEXT,
    fecha_inicio TEXT,
    fecha_fin TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_tiempo_periodo
ON dim_tiempo (periodo);

CREATE INDEX IF NOT EXISTS idx_dim_tiempo_anio_trimestre
ON dim_tiempo (anio, trimestre);
```

**Campos principales**:

- `time_id` (PK): Identificador único
- `anio`: Año (2015-2024)
- `trimestre`: Trimestre (1-4) o NULL para períodos anuales
- `mes`: Mes (1-12) o NULL
- `periodo`: Texto del período (ej: "2023", "2023-Q1")
- `fecha_inicio`, `fecha_fin`: Rango de fechas del período
- `estacion`: Estación del año (primavera, verano, otoño, invierno)
- `es_verano`: Flag para verano (1) o no (0)

**Índices**:

- `idx_dim_tiempo_periodo`: Único en `periodo`
- `idx_dim_tiempo_anio_trimestre`: En `(anio, trimestre)`

**Nota**: Esta tabla existe y está poblada automáticamente con períodos anuales y trimestrales.

## Tablas de Hechos (Fact Tables)

Todas las tablas `fact_*` comparten la siguiente estructura base:

- `id` (PK): Auto-incremento
- `barrio_id` (FK): Referencia a `dim_barrios`
- `anio`: Año de los datos
- Campos de métricas específicas
- `dataset_id`, `source`: Metadata de origen
- `etl_loaded_at`: Timestamp de carga

### 1. `fact_precios`

**Descripción**: Precios de vivienda (venta y alquiler) por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_precios (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_precios_unique
ON fact_precios (
    barrio_id,
    anio,
    COALESCE(trimestre, -1),
    COALESCE(dataset_id, ''),
    COALESCE(source, '')
);
```

**Campos clave**:

- `precio_m2_venta`: Precio por m² en venta
- `precio_mes_alquiler`: Precio mensual de alquiler
- `periodo`, `trimestre`: Granularidad temporal

**Índice único**: `(barrio_id, anio, trimestre, dataset_id, source)`

**Fuentes**: Portal de Dades, Idealista

### 2. `fact_demografia`

**Descripción**: Datos demográficos básicos por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_demografia (
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
    pct_mayores_65 REAL,
    pct_menores_15 REAL,
    indice_envejecimiento REAL,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_demografia_unique
ON fact_demografia (barrio_id, anio);
```

**Campos clave**:

- `poblacion_total`, `poblacion_hombres`, `poblacion_mujeres`
- `hogares_totales`
- `edad_media`
- `porc_inmigracion`
- `densidad_hab_km2`
- `pct_mayores_65`, `pct_menores_15`
- `indice_envejecimiento`

**Índice único**: `(barrio_id, anio)`

**Fuentes**: IDESCAT, Open Data BCN

### 3. `fact_demografia_ampliada`

**Descripción**: Datos demográficos desagregados por sexo, edad y nacionalidad.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_demografia_ampliada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    sexo TEXT,
    grupo_edad TEXT,
    nacionalidad TEXT,
    poblacion INTEGER,
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_demografia_ampliada_barrio_anio
ON fact_demografia_ampliada (barrio_id, anio);
```

**Campos clave**:

- `sexo`: H/M
- `grupo_edad`: Rango de edad
- `nacionalidad`: Española/Extranjera
- `poblacion`: Contador

**Índice**: `(barrio_id, anio)`

**Fuentes**: IDESCAT

### 4. `fact_renta`

**Descripción**: Datos de renta disponible por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_renta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    renta_euros REAL,
    renta_promedio REAL,
    renta_mediana REAL,
    renta_min REAL,
    renta_max REAL,
    num_secciones INTEGER,
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_renta_unique
ON fact_renta (barrio_id, anio);
```

**Campos clave**:

- `renta_euros`: Renta promedio
- `renta_promedio`, `renta_mediana`
- `renta_min`, `renta_max`
- `num_secciones`: Número de secciones censales

**Índice único**: `(barrio_id, anio)`

**Fuentes**: IDESCAT, ICGC

### 5. `fact_oferta_idealista`

**Descripción**: Datos de oferta inmobiliaria de Idealista por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_oferta_idealista (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    operacion TEXT NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    num_anuncios INTEGER,
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
    is_mock INTEGER DEFAULT 0,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_oferta_idealista_unique
ON fact_oferta_idealista (barrio_id, operacion, anio, mes);

CREATE INDEX IF NOT EXISTS idx_fact_oferta_idealista_barrio_fecha
ON fact_oferta_idealista (barrio_id, anio, mes);
```

**Campos clave**:

- `operacion`: "venta" o "alquiler"
- `mes`: Mes del año
- `num_anuncios`: Número de anuncios
- `precio_medio`, `precio_mediano`
- `precio_m2_medio`, `precio_m2_mediano`
- `superficie_media`, `habitaciones_media`
- `is_mock`: Flag para datos simulados

**Índice único**: `(barrio_id, operacion, anio, mes)`

**Fuentes**: Idealista (RapidAPI), Mock Generator

### 6. `fact_regulacion`

**Descripción**: Datos de regulación de vivienda (zonas tensionadas, licencias VUT).

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_regulacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    zona_tensionada INTEGER,
    nivel_tension TEXT,
    indice_referencia_alquiler REAL,
    num_licencias_vut INTEGER,
    derecho_tanteo INTEGER,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_regulacion_unique
ON fact_regulacion (barrio_id, anio);
```

**Campos clave**:

- `zona_tensionada`: 1 si es zona tensionada, 0 si no
- `nivel_tension`: Nivel de tensión
- `indice_referencia_alquiler`: Índice de referencia para alquiler
- `num_licencias_vut`: Número de licencias VUT
- `derecho_tanteo`: 1 si aplica derecho de tanteo

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Portal de Dades, Generalitat

### 7. `fact_presion_turistica`

**Descripción**: Datos de presión turística (Airbnb) por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_presion_turistica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    num_listings_airbnb INTEGER,
    pct_entire_home REAL,
    precio_noche_promedio REAL,
    tasa_ocupacion REAL,
    num_reviews_mes INTEGER,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_presion_turistica_unique
ON fact_presion_turistica (barrio_id, anio, mes);

CREATE INDEX IF NOT EXISTS idx_fact_presion_turistica_barrio_fecha
ON fact_presion_turistica (barrio_id, anio, mes);
```

**Campos clave**:

- `mes`: Mes del año
- `num_listings_airbnb`: Número de anuncios Airbnb
- `pct_entire_home`: Porcentaje de viviendas completas
- `precio_noche_promedio`: Precio promedio por noche
- `tasa_ocupacion`: Tasa de ocupación
- `num_reviews_mes`: Número de reviews del mes

**Índice único**: `(barrio_id, anio, mes)`

**Fuentes**: Airbnb (scraping), Inside Airbnb

### 8. `fact_seguridad`

**Descripción**: Datos de seguridad y delitos por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_seguridad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    delitos_patrimonio INTEGER,
    delitos_seguridad_personal INTEGER,
    tasa_criminalidad_1000hab REAL,
    percepcion_inseguridad REAL,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_seguridad_unique
ON fact_seguridad (barrio_id, anio, trimestre);

CREATE INDEX IF NOT EXISTS idx_fact_seguridad_barrio_fecha
ON fact_seguridad (barrio_id, anio, trimestre);
```

**Campos clave**:

- `trimestre`: Trimestre del año
- `delitos_patrimonio`: Delitos contra el patrimonio
- `delitos_seguridad_personal`: Delitos contra la seguridad personal
- `tasa_criminalidad_1000hab`: Tasa de criminalidad por 1000 habitantes
- `percepcion_inseguridad`: Percepción de inseguridad (0-10)

**Índice único**: `(barrio_id, anio, trimestre)`

**Fuentes**: Open Data BCN, Encuestas

### 9. `fact_ruido`

**Descripción**: Datos de ruido ambiental por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_ruido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    nivel_lden_medio REAL,
    nivel_ld_dia REAL,
    nivel_ln_noche REAL,
    pct_poblacion_expuesta_65db REAL,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_ruido_unique
ON fact_ruido (barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_ruido_barrio_fecha
ON fact_ruido (barrio_id, anio);
```

**Campos clave**:

- `nivel_lden_medio`: Nivel de ruido día-tarde-noche promedio
- `nivel_ld_dia`: Nivel de ruido diurno
- `nivel_ln_noche`: Nivel de ruido nocturno
- `pct_poblacion_expuesta_65db`: Porcentaje de población expuesta a >65dB

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Open Data BCN

**Nota**: Esta tabla está siendo migrada a `fact_medio_ambiente` (ver abajo).

### 10. `fact_medio_ambiente`

**Descripción**: Datos ambientales (ruido + zonas verdes) por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_medio_ambiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    -- Ruido (mantener compatibilidad con fact_ruido)
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_medio_ambiente_unique
ON fact_medio_ambiente (barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_medio_ambiente_barrio_fecha
ON fact_medio_ambiente (barrio_id, anio);
```

**Campos clave**:

- **Ruido** (compatibilidad con `fact_ruido`):
  - `nivel_lden_medio`, `nivel_ld_dia`, `nivel_ln_noche`
  - `pct_poblacion_expuesta_65db`
- **Zonas verdes**:
  - `superficie_zonas_verdes_m2`: Superficie total de zonas verdes en m²
  - `num_parques_jardines`: Número de parques y jardines
  - `num_arboles`: Número de árboles
  - `m2_zonas_verdes_por_habitante`: m² de zonas verdes por habitante

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Open Data BCN

### 11. `fact_educacion`

**Descripción**: Niveles de educación y equipamientos educativos por barrio. Esta tabla sirve como proxy principal para análisis de gentrificación.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_educacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    -- Niveles de educación (Proxy de Gentrificación)
    pct_sin_estudios REAL,
    pct_primaria REAL,
    pct_secundaria REAL,
    pct_universitarios REAL,
    poblacion_16plus INTEGER,
    -- Equipamientos (Mantener compatibilidad)
    num_centros_infantil INTEGER DEFAULT 0,
    num_centros_primaria INTEGER DEFAULT 0,
    num_centros_secundaria INTEGER DEFAULT 0,
    num_centros_fp INTEGER DEFAULT 0,
    num_centros_universidad INTEGER DEFAULT 0,
    total_centros_educativos INTEGER DEFAULT 0,
    -- Metadata
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn_educacion',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_educacion_unique
ON fact_educacion (barrio_id, anio);
```

**Campos clave**:

- `pct_universitarios`: Porcentaje de población con estudios universitarios (indicador clave de gentrificación)
- `pct_secundaria`, `pct_primaria`, `pct_sin_estudios`: Distribución de niveles educativos
- `poblacion_16plus`: Población total de 16 años o más considerada en las estadísticas
- `total_centros_educativos`: Total de centros de enseñanza en el barrio

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Padró Municipal d'Habitants, Open Data BCN

### 12. `fact_calidad_aire`

**Descripción**: Calidad del aire por barrio (interpolada mediante IDW de 11 estaciones ASPB).

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_calidad_aire (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    no2_mean REAL,
    pm25_mean REAL,
    pm10_mean REAL,
    o3_mean REAL,
    stations_nearby INTEGER,
    max_distance_m REAL,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_calidad_aire_unique
ON fact_calidad_aire (barrio_id, anio);
```

**Campos clave**:

- `no2_mean`: Media anual de Dióxido de Nitrógeno (µg/m³)
- `pm25_mean`: Media anual de Partículas < 2.5 µm (Crítico para salud y precios)
- `pm10_mean`: Media anual de Partículas < 10 µm
- `stations_nearby`: Número de estaciones usadas para la interpolación
- `max_distance_m`: Distancia a la estación más lejana (métrica de calidad IDW)

**Fuentes**: ASPB (Agència Salut Pública Bcn), Open Data BCN

### 13. `fact_soroll`

**Descripción**: Niveles de ruido ambiental por barrio bajados del Mapa Estratégico de Soroll (quinquenal).

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_soroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    lden_mean REAL,
    pct_exposed_65db REAL,
    area_covered_m2 REAL,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_soroll_unique
ON fact_soroll (barrio_id, anio);
```

**Campos clave**:

- `lden_mean`: Nivel de ruido día-tarde-noche promedio en dB(A)
- `pct_exposed_65db`: % de población expuesta a niveles > 65dB
- `area_covered_m2`: Superficie total cubierta por la medición en el barrio

**Fuentes**: Mapa Estratègic de Soroll de Barcelona

### 14. `fact_desempleo` [NUEVO v2.0]

**Descripción**: Datos de desempleo por barrio.

**Campos clave**:

- `num_desempleados`: Número total de personas desempleadas.
- `tasa_desempleo_estimada`: Tasa de desempleo calculada sobre la población activa estimada.

### 15. `fact_hut` [NUEVO v2.0]

**Descripción**: Viviendas de Uso Turístico con licencia oficial.

**Campos clave**:

- `num_licencias_vut`: Número total de licencias HUT activas.
- `densidad_vut_por_100_viviendas`: Ratio de presión turística oficial.

### 16. `fact_visados` [NUEVO v2.0]

**Descripción**: Visados de obra nueva y rehabilitación mayor.

**Campos clave**:

- `num_visados_obra_nueva`: Número de proyectos aprobados.
- `num_viviendas_proyectadas`: Total de unidades de vivienda nuevas.
- `presupuesto_total_euros`: Inversión estimada en construcción.

## Vistas de Capa de Fundación (v2.0 Foundation)

Para asegurar la retrocompatibilidad y simplificar el análisis, se han creado las siguientes vistas:

### `fact_airbnb`

- **Origen**: `fact_presion_turistica`
- **Propósito**: Estandarizar el acceso a métricas de Inside Airbnb.

### `fact_control_alquiler`

- **Origen**: `fact_regulacion`
- **Propósito**: Alias para análisis de políticas de vivienda.

### `fact_accesibilidad`

- **Origen**: `fact_movilidad`
- **Propósito**: Enfoque en transporte y tiempos de desplazamiento.

### `fact_centralidad`

- **Origen**: Agregación de `fact_comercio` + `fact_servicios_salud`
- **Propósito**: Medir la densidad de servicios y centralidad del barrio.

**Descripción**: Infraestructuras de transporte y movilidad por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_movilidad (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_movilidad_unique
ON fact_movilidad (barrio_id, anio, mes);

CREATE INDEX IF NOT EXISTS idx_fact_movilidad_barrio_fecha
ON fact_movilidad (barrio_id, anio, mes);
```

**Campos clave**:

- `mes`: Mes del año (opcional)
- `estaciones_metro`: Número de estaciones de metro
- `estaciones_fgc`: Número de estaciones de FGC
- `paradas_bus`: Número de paradas de bus
- `estaciones_bicing`: Número de estaciones Bicing
- `capacidad_bicing`: Capacidad total de Bicing
- `uso_bicing_promedio`: Uso promedio de Bicing
- `tiempo_medio_centro_minutos`: Tiempo medio al centro en minutos

**Índice único**: `(barrio_id, anio, mes)`

**Fuentes**: ATM Open Data, Bicing GBFS API

### 15. `fact_vivienda_publica`

**Descripción**: Datos de vivienda pública y protección oficial por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_vivienda_publica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    contratos_alquiler_nuevos INTEGER,
    fianzas_depositadas_euros REAL,
    renta_media_mensual_alquiler REAL,
    viviendas_proteccion_oficial INTEGER,
    dataset_id TEXT,
    source TEXT DEFAULT 'incasol_idescat',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_vivienda_publica_unique
ON fact_vivienda_publica (barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_vivienda_publica_barrio_fecha
ON fact_vivienda_publica (barrio_id, anio);
```

**Campos clave**:

- `contratos_alquiler_nuevos`: Contratos de alquiler nuevos
- `fianzas_depositadas_euros`: Fianzas depositadas en euros
- `renta_media_mensual_alquiler`: Renta media mensual de alquiler
- `viviendas_proteccion_oficial`: Número de viviendas de protección oficial

**Índice único**: `(barrio_id, anio)`

**Fuentes**: IDESCAT, INCASOL

**Nota**: Los datos son estimaciones distribuidas proporcionalmente desde nivel municipal.

### 16. `fact_servicios_salud`

**Descripción**: Servicios sanitarios por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_servicios_salud (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_servicios_salud_unique
ON fact_servicios_salud (barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_servicios_salud_barrio_fecha
ON fact_servicios_salud (barrio_id, anio);
```

**Campos clave**:

- `num_centros_salud`: Número de centros de salud
- `num_hospitales`: Número de hospitales
- `num_farmacias`: Número de farmacias
- `total_servicios_sanitarios`: Total de servicios sanitarios
- `densidad_servicios_por_km2`: Densidad de servicios por km²
- `densidad_servicios_por_1000hab`: Densidad de servicios por 1000 habitantes

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Open Data BCN

### 17. `fact_comercio`

**Descripción**: Actividad comercial por barrio.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS fact_comercio (
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

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_comercio_unique
ON fact_comercio (barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_comercio_barrio_fecha
ON fact_comercio (barrio_id, anio);
```

**Campos clave**:

- `num_locales_comerciales`: Número de locales comerciales
- `num_terrazas`: Número de terrazas
- `num_licencias`: Número de licencias
- `total_establecimientos`: Total de establecimientos comerciales
- `densidad_comercial_por_km2`: Densidad comercial por km²
- `densidad_comercial_por_1000hab`: Densidad comercial por 1000 habitantes
- `tasa_ocupacion_locales`: Tasa de ocupación de locales (0-1)
- `pct_locales_ocupados`: Porcentaje de locales ocupados

**Índice único**: `(barrio_id, anio)`

**Fuentes**: Open Data BCN

### 18. `fact_housing_master`

**Descripción**: Tabla maestra consolidada con métricas agregadas de vivienda y renta.

**Esquema SQL**:

```sql
-- Nota: Esta tabla se crea mediante scripts de transformación/agregación
-- No está definida en database_setup.py como las demás tablas fact_*
-- Estructura aproximada basada en los campos encontrados en la BD:

CREATE TABLE IF NOT EXISTS fact_housing_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    barrio_nombre TEXT,
    year INTEGER NOT NULL,
    quarter TEXT,
    period TEXT,
    -- Precios
    preu_lloguer_mensual REAL,
    preu_lloguer_m2 REAL,
    preu_venda_total REAL,
    preu_venda_m2 REAL,
    source_rental TEXT,
    source_sales TEXT,
    -- Renta
    renta_annual REAL,
    renta_min REAL,
    renta_max REAL,
    -- Métricas de asequibilidad
    price_to_income_ratio REAL,
    rent_burden_pct REAL,
    affordability_index REAL,
    affordability_ratio REAL,
    -- Características del edificio
    anyo_construccion_promedio REAL,
    antiguedad_anos REAL,
    num_edificios REAL,
    pct_edificios_pre1950 REAL,
    superficie_m2 REAL,
    pct_edificios_con_ascensor_proxy REAL,
    -- Transformaciones
    log_price_sales REAL,
    log_price_rental REAL,
    building_age_dynamic REAL,
    -- Temporal
    year_quarter TEXT,
    time_index INTEGER,
    source TEXT,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
```

**Campos clave**:

- **Precios**:
  - `preu_lloguer_mensual`: Precio mensual de alquiler
  - `preu_lloguer_m2`: Precio por m² de alquiler
  - `preu_venda_total`: Precio total de venta
  - `preu_venda_m2`: Precio por m² de venta
- **Renta**:
  - `renta_annual`: Renta anual
  - `renta_min`, `renta_max`: Rango de renta
- **Métricas de asequibilidad**:
  - `price_to_income_ratio`: Ratio precio/renta
  - `rent_burden_pct`: Porcentaje de carga de alquiler
  - `affordability_index`: Índice de asequibilidad
  - `affordability_ratio`: Ratio de asequibilidad
- **Características del edificio**:
  - `anyo_construccion_promedio`: Año promedio de construcción
  - `antiguedad_anos`: Antigüedad en años
  - `num_edificios`: Número de edificios
  - `pct_edificios_pre1950`: Porcentaje de edificios anteriores a 1950
  - `superficie_m2`: Superficie promedio
  - `pct_edificios_con_ascensor_proxy`: Porcentaje con ascensor (proxy)
- **Transformaciones**:
  - `log_price_sales`: Logaritmo del precio de venta
  - `log_price_rental`: Logaritmo del precio de alquiler
  - `building_age_dynamic`: Edad dinámica del edificio
- **Temporal**:
  - `year`, `quarter`, `period`: Períodos temporales
  - `year_quarter`: Año-trimestre combinado
  - `time_index`: Índice temporal

**Nota**: Esta tabla parece ser una tabla de agregación o vista materializada que combina y calcula métricas derivadas de otras tablas `fact_*` (precios, renta, demografía).

**Fuentes**: Agregación de múltiples fuentes (fact_precios, fact_renta, etc.)

## Vistas (Views)

### `vw_gentrification_risk`

**Descripción**: Vista para el análisis cruzado de riesgo de gentrificación y calidad de vida. Combina educación, precios de venta, calidad del aire y ruido.

**Esquema SQL**:

```sql
CREATE VIEW IF NOT EXISTS vw_gentrification_risk AS
SELECT
    b.barrio_nombre AS nom_barri,
    e.anio AS year,
    e.pct_universitarios,
    p.precio_m2_venta AS precio_venta_medio_m2,
    a.pm25_mean,
    s.pct_exposed_65db
FROM dim_barrios b
LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND e.anio = p.anio
LEFT JOIN fact_calidad_aire a ON b.barrio_id = a.barrio_id AND e.anio = a.anio
LEFT JOIN fact_soroll s ON b.barrio_id = s.barrio_id AND e.anio = s.anio;
```

**Utilidad**:

- Identificar barrios con alto crecimiento de población universitaria y precios al alza.
- Correlacionar la calidad ambiental (aire/ruido) con la valoración inmobiliaria.
- Facilitar el consumo de datos para el dashboard de "Gentrification Cockpit".

## Tabla de Auditoría

### `etl_runs`

**Descripción**: Registro de ejecuciones del pipeline ETL.

**Esquema SQL**:

```sql
CREATE TABLE IF NOT EXISTS etl_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    status TEXT NOT NULL,
    parameters TEXT
);
```

**Campos**:

- `run_id` (PK): Identificador único de la ejecución
- `started_at`: Timestamp de inicio
- `finished_at`: Timestamp de finalización
- `status`: Estado de la ejecución
- `parameters`: Parámetros de la ejecución (JSON)

## Relaciones Clave

### Relación Principal: `dim_barrios` → `fact_*`

Todas las tablas de hechos tienen una relación **many-to-one** con `dim_barrios`:

```sql
FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
```

Esto garantiza:

- **Integridad referencial**: No se pueden insertar datos de barrios inexistentes
- **Consistencia**: Todos los datos están vinculados a los 73 barrios oficiales
- **Geocodificación**: El `codi_barri` permite mapeo directo sin geocodificación espacial

### Relación Temporal: `dim_tiempo` → `fact_*`

Aunque no hay foreign keys explícitas, las tablas `fact_*` usan:

- `anio`: Año de los datos
- `trimestre`, `mes`: Granularidad temporal (cuando aplica)

Esto permite:

- **Análisis temporal**: Comparar métricas entre períodos
- **Agregación**: Agrupar datos por año, trimestre o mes
- **Series temporales**: Analizar tendencias a lo largo del tiempo

## Índices y Optimización

### Índices Únicos

Todas las tablas `fact_*` tienen índices únicos que previenen duplicados:

- **Patrón común**: `(barrio_id, anio)` o `(barrio_id, anio, periodo)`
- **Propósito**: Garantizar un solo registro por barrio/período/fuente

### Índices de Búsqueda

Todas las tablas `fact_*` tienen índices adicionales para optimizar consultas:

- **Patrón común**: `(barrio_id, anio)` o `(barrio_id, anio, mes)`
- **Propósito**: Acelerar filtros por barrio y fecha

## Convenciones de Nomenclatura

### Tablas

- **`dim_*`**: Tablas de dimensión (dimension tables)
- **`fact_*`**: Tablas de hechos (fact tables)
- **`etl_*`**: Tablas de auditoría/metadata

### Campos

- **`barrio_id`**: Foreign key a `dim_barrios`
- **`anio`**: Año (siempre presente en fact tables)
- **`*_id`**: Identificadores únicos
- **`num_*`**: Contadores
- **`pct_*`**: Porcentajes (0-100)
- **`tasa_*`**: Tasas (0-1)
- **`densidad_*`**: Densidades (por km² o por 1000hab)
- **`dataset_id`**, `source`: Metadata de origen
- **`etl_loaded_at`**: Timestamp de carga

## Integridad Referencial

SQLite tiene **foreign keys habilitadas** mediante:

```sql
PRAGMA foreign_keys = ON;
```

Esto garantiza:

- No se pueden eliminar barrios con datos asociados
- No se pueden insertar datos de barrios inexistentes
- Las operaciones de truncado requieren desactivar temporalmente foreign keys

## Validación de Tablas

El sistema incluye una **whitelist de tablas válidas** (`VALID_TABLES`) para prevenir SQL injection:

```python
VALID_TABLES = {
    "dim_barrios",
    "fact_precios",
    "fact_demografia",
    # ... todas las tablas válidas
}
```

Todas las operaciones dinámicas validan contra esta whitelist antes de ejecutar SQL.

## Estadísticas Actuales

- **Barrios**: 73 barrios oficiales de Barcelona
- **Tablas de hechos**: 16 tablas (incluyendo `fact_housing_master`)
- **Período temporal**: 2015-2024 (años y trimestres)
- **Fuentes de datos**: 10+ fuentes diferentes (Open Data BCN, IDESCAT, Idealista, etc.)

## Consultas SQL Comunes

### 1. Obtener todas las métricas de un barrio específico

```sql
SELECT
    db.barrio_nombre,
    dp.poblacion_total,
    dr.renta_euros,
    fp.precio_m2_venta,
    fp.precio_mes_alquiler,
    fe.total_centros_educativos,
    fs.total_servicios_sanitarios,
    fc.total_establecimientos,
    fm.m2_zonas_verdes_por_habitante
FROM dim_barrios db
LEFT JOIN fact_demografia dp ON db.barrio_id = dp.barrio_id AND dp.anio = 2023
LEFT JOIN fact_renta dr ON db.barrio_id = dr.barrio_id AND dr.anio = 2023
LEFT JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = 2023
LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = 2023
LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = 2023
LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = 2023
LEFT JOIN fact_medio_ambiente fm ON db.barrio_id = fm.barrio_id AND fm.anio = 2023
WHERE db.barrio_id = 1;
```

### 2. Comparar barrios por densidad comercial

```sql
SELECT
    db.barrio_nombre,
    fc.densidad_comercial_por_1000hab,
    fc.num_locales_comerciales,
    fc.num_terrazas,
    fc.total_establecimientos
FROM fact_comercio fc
JOIN dim_barrios db ON fc.barrio_id = db.barrio_id
WHERE fc.anio = 2025
ORDER BY fc.densidad_comercial_por_1000hab DESC
LIMIT 10;
```

### 3. Análisis de asequibilidad: precio vs renta

```sql
SELECT
    db.barrio_nombre,
    fp.precio_m2_venta,
    fp.precio_mes_alquiler,
    dr.renta_euros,
    ROUND((fp.precio_mes_alquiler * 12) / dr.renta_euros * 100, 2) AS rent_burden_pct,
    ROUND(fp.precio_m2_venta / (dr.renta_euros / 12), 2) AS price_to_income_ratio
FROM fact_precios fp
JOIN dim_barrios db ON fp.barrio_id = db.barrio_id
JOIN fact_renta dr ON fp.barrio_id = dr.barrio_id AND fp.anio = dr.anio
WHERE fp.anio = 2023
    AND fp.precio_m2_venta IS NOT NULL
    AND dr.renta_euros IS NOT NULL
ORDER BY rent_burden_pct DESC;
```

### 4. Barrios con mejor calidad de vida (múltiples métricas)

```sql
SELECT
    db.barrio_nombre,
    fe.total_centros_educativos,
    fs.total_servicios_sanitarios,
    fc.total_establecimientos,
    fm.m2_zonas_verdes_por_habitante,
    fm.nivel_lden_medio,
    (fe.total_centros_educativos + fs.total_servicios_sanitarios +
     fc.total_establecimientos) AS indice_calidad_vida
FROM dim_barrios db
LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = 2023
LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = 2023
LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = 2023
LEFT JOIN fact_medio_ambiente fm ON db.barrio_id = fm.barrio_id AND fm.anio = 2023
WHERE fe.total_centros_educativos IS NOT NULL
ORDER BY indice_calidad_vida DESC
LIMIT 10;
```

### 5. Evolución temporal de precios por barrio

```sql
SELECT
    db.barrio_nombre,
    fp.anio,
    fp.trimestre,
    fp.precio_m2_venta,
    fp.precio_mes_alquiler,
    LAG(fp.precio_m2_venta) OVER (
        PARTITION BY fp.barrio_id
        ORDER BY fp.anio, fp.trimestre
    ) AS precio_m2_venta_anterior,
    ROUND(
        ((fp.precio_m2_venta - LAG(fp.precio_m2_venta) OVER (
            PARTITION BY fp.barrio_id
            ORDER BY fp.anio, fp.trimestre
        )) / LAG(fp.precio_m2_venta) OVER (
            PARTITION BY fp.barrio_id
            ORDER BY fp.anio, fp.trimestre
        )) * 100, 2
    ) AS variacion_pct
FROM fact_precios fp
JOIN dim_barrios db ON fp.barrio_id = db.barrio_id
WHERE fp.barrio_id = 1
    AND fp.precio_m2_venta IS NOT NULL
ORDER BY fp.anio, fp.trimestre;
```

### 6. Comparar movilidad entre barrios

```sql
SELECT
    db.barrio_nombre,
    fm.estaciones_metro,
    fm.estaciones_fgc,
    fm.paradas_bus,
    fm.estaciones_bicing,
    fm.tiempo_medio_centro_minutos,
    (fm.estaciones_metro + fm.estaciones_fgc + fm.paradas_bus) AS total_infraestructura
FROM fact_movilidad fm
JOIN dim_barrios db ON fm.barrio_id = db.barrio_id
WHERE fm.anio = 2024
    AND fm.mes IS NULL  -- Datos anuales
ORDER BY total_infraestructura DESC;
```

### 7. Análisis de presión turística vs precios

```sql
SELECT
    db.barrio_nombre,
    AVG(pt.num_listings_airbnb) AS avg_listings_airbnb,
    AVG(pt.pct_entire_home) AS avg_pct_entire_home,
    AVG(fp.precio_mes_alquiler) AS avg_precio_alquiler,
    AVG(fp.precio_m2_venta) AS avg_precio_venta
FROM fact_presion_turistica pt
JOIN dim_barrios db ON pt.barrio_id = db.barrio_id
LEFT JOIN fact_precios fp ON pt.barrio_id = fp.barrio_id
    AND pt.anio = fp.anio
WHERE pt.anio = 2023
GROUP BY db.barrio_id, db.barrio_nombre
HAVING avg_listings_airbnb > 100
ORDER BY avg_precio_alquiler DESC;
```

### 8. Barrios con mejor relación servicios/población

```sql
SELECT
    db.barrio_nombre,
    dp.poblacion_total,
    fs.total_servicios_sanitarios,
    fe.total_centros_educativos,
    fs.densidad_servicios_por_1000hab,
    ROUND(
        CAST((fe.total_centros_educativos + fs.total_servicios_sanitarios) AS REAL) /
        NULLIF(dp.poblacion_total, 0) * 1000, 2
    ) AS servicios_por_1000hab
FROM dim_barrios db
JOIN fact_demografia dp ON db.barrio_id = dp.barrio_id AND dp.anio = 2023
LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = 2023
LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = 2023
WHERE dp.poblacion_total > 0
ORDER BY servicios_por_1000hab DESC
LIMIT 10;
```

### 9. Análisis de seguridad por distrito

```sql
SELECT
    db.distrito_nombre,
    COUNT(DISTINCT fs.barrio_id) AS num_barrios,
    AVG(fs.tasa_criminalidad_1000hab) AS avg_tasa_criminalidad,
    AVG(fs.percepcion_inseguridad) AS avg_percepcion_inseguridad,
    SUM(fs.delitos_patrimonio) AS total_delitos_patrimonio,
    SUM(fs.delitos_seguridad_personal) AS total_delitos_personal
FROM fact_seguridad fs
JOIN dim_barrios db ON fs.barrio_id = db.barrio_id
WHERE fs.anio = 2023
GROUP BY db.distrito_nombre
ORDER BY avg_tasa_criminalidad DESC;
```

### 10. Ranking de barrios por múltiples factores

```sql
WITH barrio_scores AS (
    SELECT
        db.barrio_id,
        db.barrio_nombre,
        -- Normalizar métricas (0-100)
        ROW_NUMBER() OVER (ORDER BY fc.densidad_comercial_por_1000hab DESC) * 100.0 /
            COUNT(*) OVER () AS score_comercio,
        ROW_NUMBER() OVER (ORDER BY fs.densidad_servicios_por_1000hab DESC) * 100.0 /
            COUNT(*) OVER () AS score_salud,
        ROW_NUMBER() OVER (ORDER BY fe.total_centros_educativos DESC) * 100.0 /
            COUNT(*) OVER () AS score_educacion,
        ROW_NUMBER() OVER (ORDER BY fm.m2_zonas_verdes_por_habitante DESC) * 100.0 /
            COUNT(*) OVER () AS score_medio_ambiente
    FROM dim_barrios db
    LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = 2023
    LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = 2023
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = 2023
    LEFT JOIN fact_medio_ambiente fm ON db.barrio_id = fm.barrio_id AND fm.anio = 2023
)
SELECT
    barrio_nombre,
    score_comercio,
    score_salud,
    score_educacion,
    score_medio_ambiente,
    ROUND((score_comercio + score_salud + score_educacion + score_medio_ambiente) / 4, 2) AS score_total
FROM barrio_scores
ORDER BY score_total DESC
LIMIT 10;
```

### 11. Comparar oferta Idealista vs precios oficiales

```sql
SELECT
    db.barrio_nombre,
    AVG(oi.precio_m2_medio) AS precio_m2_idealista,
    AVG(fp.precio_m2_venta) AS precio_m2_oficial,
    AVG(oi.precio_m2_medio) - AVG(fp.precio_m2_venta) AS diferencia,
    ROUND(
        ((AVG(oi.precio_m2_medio) - AVG(fp.precio_m2_venta)) /
         NULLIF(AVG(fp.precio_m2_venta), 0)) * 100, 2
    ) AS diferencia_pct
FROM fact_oferta_idealista oi
JOIN dim_barrios db ON oi.barrio_id = db.barrio_id
LEFT JOIN fact_precios fp ON oi.barrio_id = fp.barrio_id
    AND oi.anio = fp.anio
WHERE oi.operacion = 'venta'
    AND oi.anio = 2023
    AND oi.is_mock = 0
GROUP BY db.barrio_id, db.barrio_nombre
HAVING AVG(fp.precio_m2_venta) IS NOT NULL
ORDER BY ABS(diferencia_pct) DESC;
```

### 12. Análisis de zonas verdes y calidad ambiental

```sql
SELECT
    db.barrio_nombre,
    dp.poblacion_total,
    fm.superficie_zonas_verdes_m2,
    fm.num_parques_jardines,
    fm.num_arboles,
    fm.m2_zonas_verdes_por_habitante,
    fm.nivel_lden_medio,
    CASE
        WHEN fm.m2_zonas_verdes_por_habitante >= 9 THEN 'Excelente'
        WHEN fm.m2_zonas_verdes_por_habitante >= 5 THEN 'Bueno'
        WHEN fm.m2_zonas_verdes_por_habitante >= 2 THEN 'Aceptable'
        ELSE 'Insuficiente'
    END AS calidad_zonas_verdes
FROM fact_medio_ambiente fm
JOIN dim_barrios db ON fm.barrio_id = db.barrio_id
LEFT JOIN fact_demografia dp ON fm.barrio_id = dp.barrio_id AND fm.anio = dp.anio
WHERE fm.anio = 2023
ORDER BY fm.m2_zonas_verdes_por_habitante DESC;
```

## Referencias

- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html)
- [Star Schema Design](https://en.wikipedia.org/wiki/Star_schema)
- [Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
