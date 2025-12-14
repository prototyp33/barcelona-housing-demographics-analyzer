# Database Schema v2.0 - PostgreSQL + PostGIS

**Versión:** 2.0  
**Database:** PostgreSQL 14+ con extensión PostGIS  
**Última actualización:** Diciembre 2025  
**Migración desde:** SQLite (v1.0)

---

## Resumen Ejecutivo

El schema v2.0 migra de SQLite a PostgreSQL con PostGIS para soportar:
- Consultas geospaciales avanzadas
- Mejor rendimiento con índices
- Escalabilidad para 73 barrios + datos históricos
- Integridad referencial mejorada

---

## Arquitectura General

### Star Schema Design

```
dim_barrios (Dimension Table)
    ├── fact_precios (Fact Table)
    ├── fact_demografia (Fact Table)
    ├── fact_demografia_ampliada (Fact Table)
    ├── fact_renta (Fact Table)
    └── fact_renta_historica (NEW - v2.1)
```

---

## Tablas Principales

### dim_barrios (Dimension Table)

**Propósito:** Tabla maestra de barrios con geometría geospacial

```sql
CREATE TABLE dim_barrios (
    barrio_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nombre_normalizado VARCHAR(100),
    distrito_id INTEGER,
    distrito_nombre VARCHAR(100),
    municipio VARCHAR(50) DEFAULT 'Barcelona',
    codi_districte VARCHAR(10),
    codi_barri VARCHAR(10) UNIQUE NOT NULL,  -- Código oficial Ajuntament
    geometry GEOMETRY(POLYGON, 4326),  -- PostGIS geometry
    geometry_json JSONB,  -- GeoJSON backup
    centroide GEOMETRY(POINT, 4326),  -- Calculado automáticamente
    area_km2 REAL,
    source_dataset VARCHAR(100),
    etl_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    etl_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_barrios_codi_barri ON dim_barrios(codi_barri);
CREATE INDEX idx_barrios_geometry ON dim_barrios USING GIST(geometry);
CREATE INDEX idx_barrios_centroide ON dim_barrios USING GIST(centroide);

-- Trigger para actualizar centroide
CREATE OR REPLACE FUNCTION update_barrio_centroide()
RETURNS TRIGGER AS $$
BEGIN
    NEW.centroide = ST_Centroid(NEW.geometry);
    NEW.etl_updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_centroide
    BEFORE INSERT OR UPDATE ON dim_barrios
    FOR EACH ROW
    EXECUTE FUNCTION update_barrio_centroide();
```

**Campos clave:**
- `codi_barri`: Identificador oficial (usado para matching)
- `geometry`: Polígono del barrio en PostGIS
- `centroide`: Punto central (para cálculos de distancia)

---

### fact_precios (Fact Table)

**Propósito:** Precios de transacciones y alquileres por barrio y período

```sql
CREATE TABLE fact_precios (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    mes INTEGER,
    precio_venta REAL,  -- Precio total (EUR)
    precio_m2_venta REAL,  -- Precio por m² (EUR/m²)
    precio_alquiler_mes REAL,  -- Alquiler mensual (EUR/mes)
    precio_alquiler_m2 REAL,  -- Alquiler por m² (EUR/m²/mes)
    num_transacciones INTEGER,
    superficie_media REAL,  -- m² promedio
    tipo_vivienda VARCHAR(50),  -- 'piso', 'casa', 'atico', etc.
    dataset_id VARCHAR(100),
    source VARCHAR(50),  -- 'INE', 'PortalDades', 'Catastro'
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_precio_positivo CHECK (precio_m2_venta > 0 OR precio_alquiler_m2 > 0),
    CONSTRAINT chk_fecha_valida CHECK (fecha >= '2015-01-01' AND fecha <= CURRENT_DATE)
);

-- Índices
CREATE INDEX idx_precios_barrio_fecha ON fact_precios(barrio_id, fecha);
CREATE INDEX idx_precios_anio ON fact_precios(anio);
CREATE INDEX idx_precios_source ON fact_precios(source);
```

**Notas:**
- Precios en EUR (no normalizados)
- Soporta múltiples fuentes (INE, Portal de Dades)
- Validación de rangos razonables (100k - 2M EUR para vivienda típica)

---

### fact_demografia (Fact Table)

**Propósito:** Datos demográficos agregados por barrio y año

```sql
CREATE TABLE fact_demografia (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,
    poblacion_total INTEGER,
    poblacion_hombres INTEGER,
    poblacion_mujeres INTEGER,
    hogares_totales INTEGER,
    hogares_unipersonales INTEGER,
    edad_media REAL,
    edad_mediana INTEGER,
    porc_inmigracion REAL,  -- % población extranjera
    densidad_hab_km2 REAL,
    dataset_id VARCHAR(100),
    source VARCHAR(50),
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(barrio_id, anio, source)
);

-- Índices
CREATE INDEX idx_demografia_barrio_anio ON fact_demografia(barrio_id, anio);
```

---

### fact_demografia_ampliada (Fact Table)

**Propósito:** Datos demográficos desagregados por sexo, edad, nacionalidad

```sql
CREATE TABLE fact_demografia_ampliada (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,
    sexo VARCHAR(10),  -- 'Hombres', 'Mujeres', 'Total'
    grupo_edad VARCHAR(20),  -- '0-14', '15-29', '30-44', etc.
    nacionalidad VARCHAR(50),  -- 'Española', 'Extranjera', país específico
    poblacion INTEGER,
    dataset_id VARCHAR(100),
    source VARCHAR(50),
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_demografia_ampliada_barrio ON fact_demografia_ampliada(barrio_id, anio);
```

---

### fact_renta (Fact Table)

**Propósito:** Datos de renta disponible por barrio

```sql
CREATE TABLE fact_renta (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id) ON DELETE CASCADE,
    anio INTEGER NOT NULL,
    renta_media REAL,  -- Renta media anual (EUR)
    renta_mediana REAL,  -- Renta mediana anual (EUR)
    renta_min REAL,
    renta_max REAL,
    num_secciones INTEGER,  -- Número de secciones censales incluidas
    dataset_id VARCHAR(100),
    source VARCHAR(50),  -- 'INE', 'PortalDades'
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(barrio_id, anio, source)
);

-- Índices
CREATE INDEX idx_renta_barrio_anio ON fact_renta(barrio_id, anio);
```

---

## Nuevas Tablas (v2.1+)

### fact_renta_historica (NEW - v2.1)

**Propósito:** Histórico completo de renta (2015-2025)

```sql
CREATE TABLE fact_renta_historica (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id),
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    renta_media REAL,
    renta_mediana REAL,
    fuente VARCHAR(50),
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(barrio_id, anio, trimestre, fuente)
);
```

### fact_euribor (NEW - v2.1)

**Propósito:** Tipos de interés históricos

```sql
CREATE TABLE fact_euribor (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    euribor_3m REAL,
    euribor_12m REAL,
    fuente VARCHAR(50) DEFAULT 'BancoEspana',
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_euribor_fecha ON fact_euribor(fecha);
```

### fact_construccion (NEW - v2.1)

**Propósito:** Visados y nuevas construcciones

```sql
CREATE TABLE fact_construccion (
    id SERIAL PRIMARY KEY,
    barrio_id INTEGER NOT NULL REFERENCES dim_barrios(barrio_id),
    anio INTEGER NOT NULL,
    visados_vivienda INTEGER,
    viviendas_construidas INTEGER,
    superficie_construida_m2 REAL,
    fuente VARCHAR(50),
    etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(barrio_id, anio, fuente)
);
```

---

## Vistas Útiles

### Vista: Precios con Demografía

```sql
CREATE VIEW v_precios_demografia AS
SELECT 
    p.barrio_id,
    b.nombre AS barrio_nombre,
    p.fecha,
    p.anio,
    p.precio_m2_venta,
    p.precio_alquiler_m2,
    d.poblacion_total,
    d.edad_media,
    d.porc_inmigracion,
    d.densidad_hab_km2
FROM fact_precios p
JOIN dim_barrios b ON p.barrio_id = b.barrio_id
LEFT JOIN fact_demografia d ON p.barrio_id = d.barrio_id AND p.anio = d.anio;
```

### Vista: Barrios con Geometría para Mapas

```sql
CREATE VIEW v_barrios_geojson AS
SELECT 
    barrio_id,
    nombre,
    distrito_nombre,
    ST_AsGeoJSON(geometry) AS geometry_json,
    ST_X(centroide) AS lon,
    ST_Y(centroide) AS lat,
    area_km2
FROM dim_barrios;
```

---

## Funciones PostGIS Útiles

### Calcular Distancia al Centro

```sql
CREATE OR REPLACE FUNCTION distancia_centro(barrio_id_param INTEGER)
RETURNS REAL AS $$
DECLARE
    centro_plaza_catalunya GEOMETRY(POINT, 4326);
    barrio_centroide GEOMETRY(POINT, 4326);
BEGIN
    -- Plaza Catalunya: 2.1734, 41.3851
    centro_plaza_catalunya := ST_SetSRID(ST_MakePoint(2.1734, 41.3851), 4326);
    
    SELECT centroide INTO barrio_centroide
    FROM dim_barrios
    WHERE barrio_id = barrio_id_param;
    
    -- Retornar distancia en km
    RETURN ST_Distance(
        ST_Transform(centro_plaza_catalunya, 3857),
        ST_Transform(barrio_centroide, 3857)
    ) / 1000;
END;
$$ LANGUAGE plpgsql;
```

---

## Migración desde SQLite

### Script de Migración

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2
from pathlib import Path

def migrate():
    # Conectar a SQLite
    sqlite_conn = sqlite3.connect('data/processed/database.db')
    sqlite_cur = sqlite_conn.cursor()
    
    # Conectar a PostgreSQL
    pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    pg_cur = pg_conn.cursor()
    
    # Migrar dim_barrios
    sqlite_cur.execute("SELECT * FROM dim_barrios")
    for row in sqlite_cur.fetchall():
        # Convertir geometry_json a PostGIS geometry
        # Insertar en PostgreSQL
        pass
    
    # Migrar fact tables
    # ...
    
    pg_conn.commit()
```

---

## Índices y Performance

### Índices Críticos

```sql
-- Búsquedas por barrio y fecha
CREATE INDEX idx_precios_barrio_fecha ON fact_precios(barrio_id, fecha DESC);

-- Agregaciones temporales
CREATE INDEX idx_precios_anio_trimestre ON fact_precios(anio, trimestre);

-- Joins frecuentes
CREATE INDEX idx_demografia_barrio_anio ON fact_demografia(barrio_id, anio);
```

### Query Optimization

**Ejemplo: Precio medio por barrio y año**

```sql
-- Optimizado con índice
EXPLAIN ANALYZE
SELECT 
    b.nombre,
    p.anio,
    AVG(p.precio_m2_venta) AS precio_medio
FROM fact_precios p
JOIN dim_barrios b ON p.barrio_id = b.barrio_id
WHERE p.anio >= 2020
GROUP BY b.nombre, p.anio
ORDER BY p.anio DESC, precio_medio DESC;
```

---

## Referencias

- **Schema v1.0 (SQLite):** `docs/DATABASE_SCHEMA.md`
- **PostGIS Documentation:** https://postgis.net/documentation/
- **Migration Guide:** `scripts/migrate_sqlite_to_postgres.py`

---

**Última actualización:** Diciembre 2025

