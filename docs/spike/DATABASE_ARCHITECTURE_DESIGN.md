# Arquitectura de Base de Datos - Diseño Completo

**Versión**: 2.0  
**Fecha**: 2025-12-14  
**Estado**: Propuesta de Arquitectura Mejorada  
**Base Actual**: SQLite con Star Schema  
**Referencia**: Resumen de Implementación + Mejoras Propuestas

---

## 📋 Resumen Ejecutivo

Esta arquitectura propone una evolución del esquema actual hacia un diseño más completo que integre:

- ✅ **Estado Actual**: Star Schema básico con `dim_barrios` y 5 tablas de hechos
- 🆕 **Mejoras Propuestas**: Dimensiones adicionales, tablas de hechos especializadas, vistas analíticas
- 🎯 **Objetivo**: Soporte para análisis complejos, ML, y dashboards interactivos

### Características Clave

| Aspecto | Detalle |
|---------|---------|
| **Tipo de BD** | SQLite (actual) → PostgreSQL + PostGIS (futuro) |
| **Patrón** | Star Schema + Dimensiones Normalizadas |
| **Dimensiones** | 5 principales + 2 auxiliares |
| **Hechos** | 9 tablas especializadas |
| **Vistas** | 10+ vistas analíticas |
| **Cobertura** | 73 barrios, 2015-2024+ |
| **Registros** | ~50k-100k anuales |

---

## 🏗️ Arquitectura General

### Diagrama de Estrella (Star Schema)

```
                    dim_barrios (Centro)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   dim_tiempo      dim_servicios    dim_fuentes_datos
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   fact_precios    fact_renta      fact_demografia
        │                │                │
   fact_housing_   fact_catastro   fact_proximidad
   master          fact_oferta_    fact_demografia_
                   idealista       ampliada
```

---

## 📊 Tablas de Dimensiones

### 1. `dim_barrios` (Existente - Mejorada)

**Propósito**: Tabla maestra de los 73 barrios de Barcelona con información geográfica y administrativa.

```sql
CREATE TABLE dim_barrios (
    barrio_id INTEGER PRIMARY KEY,
    barrio_nombre TEXT NOT NULL,
    barrio_nombre_normalizado TEXT NOT NULL,
    
    -- Jerarquía administrativa
    distrito_id INTEGER,
    distrito_nombre TEXT,
    municipio TEXT DEFAULT 'Barcelona',
    ambito TEXT,
    
    -- Códigos oficiales
    codi_districte TEXT,
    codi_barri TEXT UNIQUE NOT NULL,  -- Código oficial Ajuntament
    codigo_ine TEXT,                  -- 🆕 Código INE para matching
    
    -- Geografía
    geometry_json TEXT,               -- GeoJSON (Polygon)
    centroide_lat REAL,               -- 🆕 Latitud centroide
    centroide_lon REAL,               -- 🆕 Longitud centroide
    area_km2 REAL,                    -- 🆕 Área en km²
    
    -- Metadatos
    source_dataset TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT
);

-- Índices
CREATE UNIQUE INDEX idx_dim_barrios_nombre ON dim_barrios(barrio_nombre_normalizado);
CREATE UNIQUE INDEX idx_dim_barrios_codi_barri ON dim_barrios(codi_barri);
CREATE INDEX idx_dim_barrios_distrito ON dim_barrios(distrito_id);
```

**Mejoras Propuestas**:
- ✅ Añadir `codigo_ine` para matching con datos INE
- ✅ Añadir `centroide_lat/lon` para cálculos de proximidad
- ✅ Añadir `area_km2` para normalizaciones

---

### 2. `dim_tiempo` (Nueva)

**Propósito**: Tabla de tiempo para análisis temporal y agregaciones.

```sql
CREATE TABLE dim_tiempo (
    time_id INTEGER PRIMARY KEY,
    anio INTEGER NOT NULL,
    trimestre INTEGER,                -- 1-4 o NULL
    mes INTEGER,                      -- 1-12 o NULL
    periodo TEXT,                     -- "2015-Q1", "2015-01", etc.
    year_quarter TEXT,                -- "2015-Q1"
    year_month TEXT,                  -- "2015-01"
    
    -- Atributos temporales
    es_fin_de_semana INTEGER,         -- 0 o 1
    es_verano INTEGER,                -- 0 o 1 (jun-sep)
    estacion TEXT,                    -- primavera, verano, otoño, invierno
    dia_semana TEXT,                  -- lunes, martes, etc.
    
    -- Metadatos
    fecha_inicio TEXT,                -- ISO date
    fecha_fin TEXT                    -- ISO date
);

-- Índices
CREATE UNIQUE INDEX idx_dim_tiempo_periodo ON dim_tiempo(periodo);
CREATE INDEX idx_dim_tiempo_anio_trimestre ON dim_tiempo(anio, trimestre);
```

**Uso**: Permite análisis temporal sin duplicar datos en cada fact table.

---

### 3. `dim_servicios` (Nueva)

**Propósito**: Catálogo de servicios y puntos de interés (POIs) para análisis de proximidad.

```sql
CREATE TABLE dim_servicios (
    servicio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,          -- hospital, colegio, supermercado, transporte
    tipo TEXT,                        -- público, privado, etc.
    direccion TEXT,
    latitud REAL,
    longitud REAL,
    geometry_json TEXT,               -- GeoJSON Point
    
    -- Metadatos
    source TEXT,                      -- google_maps, osm, manual
    fecha_actualizacion TEXT,
    etl_loaded_at TEXT
);

-- Índices
CREATE INDEX idx_dim_servicios_categoria ON dim_servicios(categoria);
CREATE INDEX idx_dim_servicios_tipo ON dim_servicios(tipo);
```

**Categorías**:
- `hospital`: Hospitales y centros de salud
- `colegio`: Escuelas y centros educativos
- `supermercado`: Supermercados y tiendas
- `transporte`: Estaciones de metro/bus, paradas
- `parque`: Parques y zonas verdes
- `cultura`: Museos, bibliotecas, centros culturales

---

### 4. `dim_distritos` (Nueva - Opcional)

**Propósito**: Tabla de distritos para agregaciones a nivel distrito.

```sql
CREATE TABLE dim_distritos (
    distrito_id INTEGER PRIMARY KEY,
    distrito_nombre TEXT NOT NULL,
    codi_districte TEXT UNIQUE,
    municipio TEXT DEFAULT 'Barcelona',
    geometry_json TEXT,               -- GeoJSON del distrito
    area_km2 REAL,
    num_barrios INTEGER,              -- Número de barrios en el distrito
    etl_created_at TEXT
);
```

**Nota**: Puede derivarse de `dim_barrios` si no se necesita información adicional.

---

### 5. `dim_fuentes_datos` (Nueva)

**Propósito**: Catálogo de fuentes de datos para trazabilidad y calidad.

```sql
CREATE TABLE dim_fuentes_datos (
    fuente_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,      -- "opendatabcn", "idescat", etc.
    tipo TEXT,                        -- api, csv, web_scraping
    descripcion TEXT,
    url_base TEXT,
    frecuencia_actualizacion TEXT,    -- "diaria", "semanal", "mensual", "anual"
    calidad_estimada TEXT,            -- "alta", "media", "baja"
    fecha_ultima_actualizacion TEXT,
    contacto TEXT,
    etl_loaded_at TEXT
);
```

**Fuentes Principales**:
- `opendatabcn`: Open Data Barcelona
- `idescat`: Instituto de Estadística de Catalunya
- `ine`: Instituto Nacional de Estadística
- `portaldades`: Portal de Dades Obertes
- `idealista`: Idealista API
- `incasol`: INCASÒL (alquiler)
- `generalitat`: Generalitat de Catalunya (venta)

---

## 📈 Tablas de Hechos

### 1. `fact_precios` (Existente - Mejorada)

**Propósito**: Precios de vivienda (venta y alquiler) por barrio, año y período.

```sql
CREATE TABLE fact_precios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,                -- 1-4 o NULL
    periodo TEXT,                     -- "2015-Q1" o "2015"
    
    -- Precios
    precio_m2_venta REAL,
    precio_mes_alquiler REAL,
    precio_total_venta REAL,          -- 🆕 Precio total (no solo m²)
    
    -- Metadatos
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_precios_unique ON fact_precios (
    barrio_id, anio, COALESCE(trimestre, -1), 
    COALESCE(dataset_id, ''), COALESCE(source, '')
);
CREATE INDEX idx_fact_precios_barrio_anio ON fact_precios(barrio_id, anio);
```

---

### 2. `fact_renta` (Existente)

**Propósito**: Datos de renta familiar disponible por barrio y año.

```sql
CREATE TABLE fact_renta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- Métricas de renta
    renta_euros REAL,
    renta_promedio REAL,
    renta_mediana REAL,
    renta_min REAL,
    renta_max REAL,
    num_secciones INTEGER,
    
    -- Metadatos
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_renta_unique ON fact_renta(barrio_id, anio);
```

---

### 3. `fact_demografia` (Existente - Mejorada)

**Propósito**: Demografía básica por barrio y año.

```sql
CREATE TABLE fact_demografia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- Población
    poblacion_total INTEGER,
    poblacion_hombres INTEGER,
    poblacion_mujeres INTEGER,
    hogares_totales INTEGER,
    
    -- Métricas demográficas
    edad_media REAL,
    porc_inmigracion REAL,
    densidad_hab_km2 REAL,
    
    -- 🆕 Métricas adicionales
    pct_mayores_65 REAL,              -- % población > 65 años
    pct_menores_15 REAL,              -- % población < 15 años
    indice_envejecimiento REAL,       -- Ratio mayores_65 / menores_15
    
    -- Metadatos
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_demografia_unique ON fact_demografia(barrio_id, anio);
```

**Nota**: Las columnas `pct_mayores_65`, `pct_menores_15`, `indice_envejecimiento` ya existen en la BD actual.

---

### 4. `fact_demografia_ampliada` (Existente)

**Propósito**: Demografía desagregada por sexo, grupo de edad y nacionalidad.

```sql
CREATE TABLE fact_demografia_ampliada (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    sexo TEXT,                        -- "H", "M", NULL
    grupo_edad TEXT,                  -- "0-4", "5-9", etc.
    nacionalidad TEXT,                -- "Española", "Extranjera", etc.
    poblacion INTEGER,
    
    -- Metadatos
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE INDEX idx_fact_demografia_ampliada_barrio_anio 
    ON fact_demografia_ampliada(barrio_id, anio);
```

---

### 5. `fact_oferta_idealista` (Existente)

**Propósito**: Datos de oferta inmobiliaria de Idealista por barrio, operación, año y mes.

```sql
CREATE TABLE fact_oferta_idealista (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    operacion TEXT NOT NULL,          -- "venta", "alquiler"
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    
    -- Métricas de oferta
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
    
    -- Metadatos
    barrio_nombre_normalizado TEXT,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    is_mock INTEGER DEFAULT 0,       -- 1 si es dato simulado
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_oferta_idealista_unique 
    ON fact_oferta_idealista(barrio_id, operacion, anio, mes);
CREATE INDEX idx_fact_oferta_idealista_barrio_fecha 
    ON fact_oferta_idealista(barrio_id, anio, mes);
```

---

### 6. `fact_housing_master` (Nueva - Implementada)

**Propósito**: Tabla maestra unificada con 31 features listas para ML y análisis avanzados.

```sql
CREATE TABLE fact_housing_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    barrio_nombre TEXT,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,            -- "Q1", "Q2", "Q3", "Q4"
    period TEXT,                      -- "2015Q1"
    
    -- Precios (4 features)
    preu_lloguer_mensual REAL,
    preu_lloguer_m2 REAL,
    preu_venda_total REAL,
    preu_venda_m2 REAL,
    source_rental TEXT,
    source_sales TEXT,
    
    -- Renta (3 features)
    renta_annual REAL,
    renta_min REAL,
    renta_max REAL,
    
    -- Affordability metrics (4 features)
    price_to_income_ratio REAL,
    rent_burden_pct REAL,
    affordability_index REAL,
    affordability_ratio REAL,
    
    -- Atributos estructurales (6 features)
    anyo_construccion_promedio REAL,
    antiguedad_anos REAL,
    num_edificios REAL,
    pct_edificios_pre1950 REAL,
    superficie_m2 REAL,
    pct_edificios_con_ascensor_proxy REAL,
    
    -- Features transformadas (3 features)
    log_price_sales REAL,
    log_price_rental REAL,
    building_age_dynamic REAL,
    
    -- Metadatos
    source TEXT,
    year_quarter TEXT,                -- "2015-Q1"
    time_index INTEGER,               -- Índice temporal (1, 2, 3...)
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_housing_master_unique 
    ON fact_housing_master(barrio_id, year, quarter);
CREATE INDEX idx_fact_housing_master_year_quarter 
    ON fact_housing_master(year, quarter);
CREATE INDEX idx_fact_housing_master_barrio_year 
    ON fact_housing_master(barrio_id, year);
```

**Características**:
- ✅ 31 features unificadas
- ✅ Granularidad quarterly consistente
- ✅ Ready for ML
- ✅ Métricas de affordability calculadas

---

### 7. `fact_catastro` (Nueva - Propuesta)

**Propósito**: Datos del Catastro (edificios, viviendas, uso del suelo).

```sql
CREATE TABLE fact_catastro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- Edificios
    num_edificios INTEGER,
    num_viviendas INTEGER,
    num_viviendas_vacias INTEGER,
    num_viviendas_habitadas INTEGER,
    
    -- Uso del suelo
    superficie_construida_m2 REAL,
    superficie_rustica_m2 REAL,
    superficie_urbana_m2 REAL,
    
    -- Tipología
    pct_vivienda_residencial REAL,
    pct_vivienda_no_residencial REAL,
    pct_uso_comercial REAL,
    pct_uso_industrial REAL,
    
    -- Metadatos
    source TEXT DEFAULT 'catastro',
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_catastro_unique ON fact_catastro(barrio_id, anio);
```

**Fuente**: API del Catastro (futuro).

---

### 8. `fact_proximidad` (Nueva - Propuesta)

**Propósito**: Métricas de proximidad a servicios y puntos de interés.

```sql
CREATE TABLE fact_proximidad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- Conteos de servicios por distancia
    num_hospitales_1km INTEGER,
    num_hospitales_2km INTEGER,
    num_colegios_500m INTEGER,
    num_colegios_1km INTEGER,
    num_supermercados_500m INTEGER,
    num_supermercados_1km INTEGER,
    num_estaciones_transporte_500m INTEGER,
    num_estaciones_transporte_1km INTEGER,
    num_parques_500m INTEGER,
    num_parques_1km INTEGER,
    
    -- Índices de accesibilidad
    indice_accesibilidad_servicios REAL,  -- Índice compuesto 0-100
    distancia_media_hospital REAL,        -- km
    distancia_media_colegio REAL,         -- km
    distancia_media_supermercado REAL,    -- km
    distancia_media_transporte REAL,      -- km
    
    -- Metadatos
    source TEXT DEFAULT 'google_maps|osm',
    etl_loaded_at TEXT,
    
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Índices
CREATE UNIQUE INDEX idx_fact_proximidad_unique ON fact_proximidad(barrio_id, anio);
CREATE INDEX idx_fact_proximidad_accesibilidad 
    ON fact_proximidad(indice_accesibilidad_servicios);
```

**Cálculo**: Agregación desde `dim_servicios` usando geometrías.

---

## 🔍 Vistas Analíticas

### 1. `v_affordability_quarterly`

**Propósito**: Vista de affordability por barrio y trimestre.

```sql
CREATE VIEW v_affordability_quarterly AS
SELECT 
    fhm.barrio_id,
    db.barrio_nombre,
    fhm.year,
    fhm.quarter,
    fhm.preu_venda_m2,
    fhm.renta_annual,
    fhm.price_to_income_ratio,
    fhm.rent_burden_pct,
    fhm.affordability_index,
    CASE 
        WHEN fhm.affordability_index < 3 THEN 'Muy Baja'
        WHEN fhm.affordability_index < 5 THEN 'Baja'
        WHEN fhm.affordability_index < 7 THEN 'Media'
        WHEN fhm.affordability_index < 9 THEN 'Alta'
        ELSE 'Muy Alta'
    END as categoria_affordability
FROM fact_housing_master fhm
JOIN dim_barrios db ON fhm.barrio_id = db.barrio_id
WHERE fhm.renta_annual IS NOT NULL
  AND fhm.preu_venda_m2 IS NOT NULL;
```

---

### 2. `v_gentrificacion_tendencias`

**Propósito**: Detectar tendencias de gentrificación por barrio.

```sql
CREATE VIEW v_gentrificacion_tendencias AS
SELECT 
    db.barrio_id,
    db.barrio_nombre,
    p15.precio_m2_venta as precio_2015,
    p24.precio_m2_venta as precio_2024,
    ((p24.precio_m2_venta - p15.precio_m2_venta) / p15.precio_m2_venta * 100) as pct_cambio_precio,
    r15.renta_mediana as renta_2015,
    r24.renta_mediana as renta_2024,
    ((r24.renta_mediana - r15.renta_mediana) / r15.renta_mediana * 100) as pct_cambio_renta,
    d15.poblacion_total as poblacion_2015,
    d24.poblacion_total as poblacion_2024
FROM dim_barrios db
LEFT JOIN fact_precios p15 ON db.barrio_id = p15.barrio_id AND p15.anio = 2015
LEFT JOIN fact_precios p24 ON db.barrio_id = p24.barrio_id AND p24.anio = 2024
LEFT JOIN fact_renta r15 ON db.barrio_id = r15.barrio_id AND r15.anio = 2015
LEFT JOIN fact_renta r24 ON db.barrio_id = r24.barrio_id AND r24.anio = 2024
LEFT JOIN fact_demografia d15 ON db.barrio_id = d15.barrio_id AND d15.anio = 2015
LEFT JOIN fact_demografia d24 ON db.barrio_id = d24.barrio_id AND d24.anio = 2024
WHERE p15.precio_m2_venta IS NOT NULL 
  AND p24.precio_m2_venta IS NOT NULL;
```

---

### 3. `v_barrios_mejor_conectados`

**Propósito**: Barrios con mejor accesibilidad a servicios.

```sql
CREATE VIEW v_barrios_mejor_conectados AS
SELECT 
    db.barrio_id,
    db.barrio_nombre,
    fp.indice_accesibilidad_servicios,
    fp.num_hospitales_1km,
    fp.num_colegios_1km,
    fp.num_supermercados_500m,
    fp.num_estaciones_transporte_1km,
    fhm.preu_venda_m2,
    fhm.renta_annual
FROM fact_proximidad fp
JOIN dim_barrios db ON fp.barrio_id = db.barrio_id
LEFT JOIN fact_housing_master fhm ON fp.barrio_id = fhm.barrio_id 
    AND fp.anio = fhm.year
WHERE fp.anio = 2024
ORDER BY fp.indice_accesibilidad_servicios DESC;
```

---

### 4. `v_precios_evolucion_anual`

**Propósito**: Evolución anual de precios por barrio.

```sql
CREATE VIEW v_precios_evolucion_anual AS
SELECT 
    barrio_id,
    anio,
    AVG(precio_m2_venta) as precio_m2_venta_promedio,
    AVG(precio_mes_alquiler) as precio_mes_alquiler_promedio,
    COUNT(*) as num_registros
FROM fact_precios
WHERE precio_m2_venta IS NOT NULL OR precio_mes_alquiler IS NOT NULL
GROUP BY barrio_id, anio
ORDER BY barrio_id, anio;
```

---

### 5. `v_demografia_resumen`

**Propósito**: Resumen demográfico por barrio y año.

```sql
CREATE VIEW v_demografia_resumen AS
SELECT 
    d.barrio_id,
    db.barrio_nombre,
    d.anio,
    d.poblacion_total,
    d.poblacion_hombres,
    d.poblacion_mujeres,
    d.hogares_totales,
    d.edad_media,
    d.porc_inmigracion,
    d.densidad_hab_km2,
    d.pct_mayores_65,
    d.pct_menores_15,
    d.indice_envejecimiento
FROM fact_demografia d
JOIN dim_barrios db ON d.barrio_id = db.barrio_id
ORDER BY d.barrio_id, d.anio;
```

---

## 🔄 Pipeline ETL Mejorado

### Flujo ETL Integrado

```
EXTRACCIÓN (Extract)
├── Catastro API → fact_catastro
├── Open Data BCN → fact_precios, fact_renta, fact_demografia
├── INE API → fact_demografia (validación)
├── Google Maps API → dim_servicios
├── Overpass OSM → dim_servicios
├── Idealista API → fact_oferta_idealista
└── Portal de Dades → fact_precios (validación)
    ↓
TRANSFORMACIÓN (Transform)
├── Normalizar barrios (dim_barrios matching)
├── Consolidar precios (múltiples fuentes)
├── Interpolar renta (forward-fill para quarterly)
├── Calcular métricas affordability
├── Agregar servicios (dim_servicios → fact_proximidad)
├── Calcular índices de accesibilidad
├── Validar integridad referencial
└── Data quality checks (completitud, validez)
    ↓
CARGA (Load)
├── Insertar dim_barrios (si no existen)
├── Insertar dim_tiempo
├── Insertar dim_servicios
├── Insertar fact_catastro
├── Insertar fact_precios
├── Insertar fact_renta
├── Insertar fact_demografia
├── Insertar fact_oferta_idealista
├── Calcular fact_proximidad (vista materializada)
├── Calcular fact_housing_master (tabla integrada) ✅
├── Actualizar dim_fuentes_datos (metadata)
├── Registrar en etl_runs (auditoría)
└── Generar reporte de calidad
    ↓
VALIDACIÓN (Post-Load)
├── Verificar count registros
├── Validar integridad referencial
├── Calcular completitud por campo
├── Detectar outliers
└── Generar data quality score
```

---

## 📊 Control de Calidad de Datos

### Framework de DQ

```python
class DataQualityChecker:
    """Framework para validación de calidad de datos."""
    
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.results = {}
    
    def check_completeness(self, table: str, column: str) -> float:
        """Calcula % de valores no NULL."""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN {column} IS NOT NULL THEN 1 ELSE 0 END) as no_null
            FROM {table}
        """)
        total, no_null = cursor.fetchone()
        return (no_null / total * 100) if total > 0 else 0
    
    def check_validity(self, table: str, column: str, check_func) -> float:
        """Calcula % de valores válidos según check_func."""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT {column} FROM {table}")
        values = [row[0] for row in cursor.fetchall() if row[0] is not None]
        valid = sum(1 for v in values if check_func(v))
        return (valid / len(values) * 100) if values else 0
    
    def check_uniqueness(self, table: str, columns: list) -> int:
        """Detecta duplicados según columnas."""
        cols_str = ", ".join(columns)
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT {cols_str}, COUNT(*) as cnt
            FROM {table}
            GROUP BY {cols_str}
            HAVING cnt > 1
        """)
        duplicates = cursor.fetchall()
        return len(duplicates)
    
    def generate_quality_report(self, table: str) -> dict:
        """Genera reporte de calidad para una tabla."""
        report = {
            'tabla': table,
            'completitud': {},
            'validez': {},
            'uniqueness': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Ejemplo para dim_barrios
        if table == 'dim_barrios':
            report['completitud'] = {
                'codigo_ine': self.check_completeness('dim_barrios', 'codigo_ine'),
                'geometry': self.check_completeness('dim_barrios', 'geometry_json'),
            }
            report['validez'] = {
                'area_km2': self.check_validity(
                    'dim_barrios', 'area_km2', 
                    lambda x: x > 0 and x < 50  # Área razonable para un barrio
                ),
            }
            report['uniqueness'] = {
                'duplicados': self.check_uniqueness('dim_barrios', ['codigo_ine'])
            }
        
        return report
```

---

## 🔐 Configuración de Auditoría y Respaldo

### Tabla de Auditoría

```sql
CREATE TABLE audit_housing_changes (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    housing_master_id INTEGER,
    columna_modificada TEXT,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha_cambio TEXT,
    usuario TEXT,
    razon_cambio TEXT
);

-- Trigger para capturar cambios en fact_housing_master
CREATE TRIGGER audit_housing_master_update
AFTER UPDATE ON fact_housing_master
BEGIN
    INSERT INTO audit_housing_changes
    (housing_master_id, columna_modificada, valor_anterior, valor_nuevo, fecha_cambio)
    VALUES
    (NEW.id, 'preu_venda_m2', OLD.preu_venda_m2, NEW.preu_venda_m2, datetime('now'));
END;
```

### Tabla de Respaldo

```sql
-- Crear tabla de respaldo con timestamp
CREATE TABLE fact_housing_master_backup AS
SELECT *, datetime('now') as backup_date
FROM fact_housing_master
WHERE year >= 2024;
```

---

## 📈 Índices y Optimización

### Índices Recomendados

```sql
-- Índices para búsquedas frecuentes
CREATE INDEX idx_fact_precios_barrio_anio ON fact_precios(barrio_id, anio);
CREATE INDEX idx_fact_renta_barrio_anio ON fact_renta(barrio_id, anio);
CREATE INDEX idx_fact_demografia_barrio_anio ON fact_demografia(barrio_id, anio);

-- Índices para análisis temporal
CREATE INDEX idx_fact_housing_master_year ON fact_housing_master(year);
CREATE INDEX idx_fact_housing_master_quarter ON fact_housing_master(quarter);

-- Índices para joins
CREATE INDEX idx_dim_barrios_distrito ON dim_barrios(distrito_id);
CREATE INDEX idx_dim_servicios_categoria ON dim_servicios(categoria);
```

---

## 🎯 Resumen de Implementación

### Estado Actual ✅

- ✅ `dim_barrios` (73 barrios)
- ✅ `fact_precios` (6,358 registros)
- ✅ `fact_renta` (657 registros)
- ✅ `fact_demografia` (657 registros)
- ✅ `fact_demografia_ampliada` (2,256 registros)
- ✅ `fact_oferta_idealista` (1,898 registros)
- ✅ `fact_housing_master` (2,742 registros) 🆕
- ✅ `etl_runs` (auditoría)

### Propuestas Futuras 🆕

- 🆕 `dim_tiempo` (tabla de tiempo)
- 🆕 `dim_servicios` (POIs y servicios)
- 🆕 `dim_distritos` (agregación distrito)
- 🆕 `dim_fuentes_datos` (catálogo de fuentes)
- 🆕 `fact_catastro` (datos del Catastro)
- 🆕 `fact_proximidad` (métricas de accesibilidad)
- 🆕 Vistas analíticas (10+ vistas)

---

## 📚 Referencias

- **Estado Actual**: `src/database_setup.py`
- **Master Table**: `docs/spike/IMPLEMENTATION_SUMMARY.md`
- **Comparativa**: `docs/spike/DATABASE_VS_MASTER_TABLE_COMPARISON.md`
- **ETL Automation**: `docs/spike/ETL_AUTOMATION_MASTER_TABLE.md`

---

## 📅 Próximos Pasos

1. **Corto Plazo**:
   - Implementar `dim_tiempo` y actualizar fact tables
   - Crear vistas analíticas básicas
   - Mejorar `dim_barrios` con campos adicionales

2. **Medio Plazo**:
   - Integrar `dim_servicios` y `fact_proximidad`
   - Implementar framework de DQ
   - Crear sistema de auditoría

3. **Largo Plazo**:
   - Migración a PostgreSQL + PostGIS (si se requiere)
   - Integración con Catastro API
   - Sistema de respaldo automatizado

---

**Estado**: ✅ Arquitectura diseñada y documentada  
**Siguiente**: Implementación incremental según prioridades del proyecto

