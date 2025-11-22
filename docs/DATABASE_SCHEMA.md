# Database Schema Documentation

This document details the database schema for the Barcelona Housing Demographics Analyzer. The database is implemented in SQLite and follows a star schema design with a central dimension table (`dim_barrios`) and multiple fact tables.

## Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    dim_barrios ||--o{ fact_precios : "has prices"
    dim_barrios ||--o{ fact_demografia : "has demographics"
    dim_barrios ||--o{ fact_demografia_ampliada : "has detailed demographics"
    dim_barrios ||--o{ fact_renta : "has income data"
    dim_barrios ||--o{ fact_oferta_idealista : "has real estate offers"

    dim_barrios {
        INTEGER barrio_id PK
        TEXT barrio_nombre
        TEXT barrio_nombre_normalizado
        INTEGER distrito_id
        TEXT distrito_nombre
        TEXT municipio
        TEXT ambito
        TEXT codi_districte
        TEXT codi_barri
        TEXT geometry_json
        TEXT source_dataset
        TEXT etl_created_at
        TEXT etl_updated_at
    }

    fact_precios {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        TEXT periodo
        INTEGER trimestre
        REAL precio_m2_venta
        REAL precio_mes_alquiler
        TEXT dataset_id
        TEXT source
        TEXT etl_loaded_at
    }

    fact_demografia {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        INTEGER poblacion_total
        INTEGER poblacion_hombres
        INTEGER poblacion_mujeres
        INTEGER hogares_totales
        REAL edad_media
        REAL porc_inmigracion
        REAL densidad_hab_km2
        TEXT dataset_id
        TEXT source
        TEXT etl_loaded_at
    }

    fact_demografia_ampliada {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        TEXT sexo
        TEXT grupo_edad
        TEXT nacionalidad
        INTEGER poblacion
        TEXT barrio_nombre_normalizado
        TEXT dataset_id
        TEXT source
        TEXT etl_loaded_at
    }

    fact_renta {
        INTEGER id PK
        INTEGER barrio_id FK
        INTEGER anio
        REAL renta_euros
        REAL renta_promedio
        REAL renta_mediana
        REAL renta_min
        REAL renta_max
        INTEGER num_secciones
        TEXT barrio_nombre_normalizado
        TEXT dataset_id
        TEXT source
        TEXT etl_loaded_at
    }

    fact_oferta_idealista {
        INTEGER id PK
        INTEGER barrio_id FK
        TEXT operacion
        INTEGER anio
        INTEGER mes
        INTEGER num_anuncios
        REAL precio_medio
        REAL precio_mediano
        REAL precio_min
        REAL precio_max
        REAL precio_m2_medio
        REAL precio_m2_mediano
        REAL superficie_media
        REAL superficie_mediana
        REAL habitaciones_media
        TEXT barrio_nombre_normalizado
        TEXT dataset_id
        TEXT source
        TEXT etl_loaded_at
    }

    etl_runs {
        TEXT run_id PK
        TEXT started_at
        TEXT finished_at
        TEXT status
        TEXT parameters
    }
```

## Table Descriptions

### `dim_barrios` (Dimension)
The central dimension table containing the 73 neighborhoods (barrios) of Barcelona. It serves as the primary key for linking all other fact tables.
- **Key Fields**: `barrio_id` (PK), `barrio_nombre`, `distrito_id`.
- **Geospatial**: Contains `geometry_json` for map visualizations.

### `fact_precios` (Fact)
Stores historical housing prices (sale and rent) aggregated by neighborhood and time period.
- **Purpose**: To track the evolution of housing costs over time.
- **Granularity**: One record per barrio, year, quarter (optional), and source dataset.
- **Unique Constraint**: `(barrio_id, anio, trimestre, dataset_id, source)` to allow multiple indicators from different sources to coexist without duplication.

### `fact_demografia` (Fact)
Standard demographic indicators aggregated at the neighborhood level.
- **Purpose**: Provides high-level population statistics like total population, gender breakdown, and density.
- **Granularity**: One record per barrio and year.

### `fact_demografia_ampliada` (Fact)
Detailed demographic breakdowns that allow for more granular analysis than `fact_demografia`.
- **Purpose**: Enables deep dives into population structure, such as analyzing specific age groups (e.g., "18-35 years") or nationality distribution within a neighborhood. This is crucial for correlating housing prices with specific demographic shifts (e.g., gentrification by young professionals).
- **Granularity**: One record per barrio, year, sex, age group, and nationality.

### `fact_renta` (Fact)
Economic indicators related to household income.
- **Purpose**: To analyze the purchasing power of neighborhoods.
- **Granularity**: One record per barrio and year.

### `fact_oferta_idealista` (Fact)
Real-time or near real-time supply data scraped from Idealista.
- **Purpose**: Captures the current market state (number of listings, median prices) which might differ from official statistics that often have a lag.
- **Granularity**: One record per barrio, operation type (sale/rent), year, and month.

### `etl_runs` (Audit)
Logs every execution of the ETL pipeline for auditing and debugging purposes.
