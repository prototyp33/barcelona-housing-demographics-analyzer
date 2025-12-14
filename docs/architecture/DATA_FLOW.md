# Data Flow Architecture

**Versión:** 2.0  
**Última actualización:** Diciembre 2025

---

## Resumen

Este documento describe el flujo completo de datos desde las fuentes externas hasta el dashboard final, incluyendo extracción, transformación, carga y visualización.

---

## Diagrama de Flujo General

```mermaid
graph TB
    subgraph "Fuentes Externas"
        INE[INE<br/>Estadística Registral]
        Portal[Portal de Dades BCN<br/>CKAN API]
        Catastro[Catastro<br/>Sede Electrónica]
        Idealista[Idealista<br/>RapidAPI]
    end
    
    subgraph "Capa de Extracción"
        ETL1[Extractor INE]
        ETL2[Extractor Portal Dades]
        ETL3[Extractor Catastro]
        ETL4[Extractor Idealista]
    end
    
    subgraph "Almacenamiento Raw"
        Raw[data/raw/<br/>CSV/JSON files]
    end
    
    subgraph "Capa de Transformación"
        Clean[Data Cleaning<br/>Normalization]
        Validate[Data Validation<br/>Quality Checks]
        Merge[Data Linking<br/>Matching]
    end
    
    subgraph "Base de Datos"
        PostgreSQL[(PostgreSQL<br/>+ PostGIS)]
        Schema[dim_barrios<br/>fact_precios<br/>fact_demografia]
    end
    
    subgraph "Capa de Análisis"
        Model[Hedonic Model<br/>statsmodels]
        Notebooks[Jupyter Notebooks<br/>EDA & Analysis]
    end
    
    subgraph "Visualización"
        Dashboard[Streamlit Dashboard<br/>Market Cockpit]
        API[FastAPI<br/>REST API]
    end
    
    INE --> ETL1
    Portal --> ETL2
    Catastro --> ETL3
    Idealista --> ETL4
    
    ETL1 --> Raw
    ETL2 --> Raw
    ETL3 --> Raw
    ETL4 --> Raw
    
    Raw --> Clean
    Clean --> Validate
    Validate --> Merge
    Merge --> PostgreSQL
    
    PostgreSQL --> Schema
    Schema --> Model
    Schema --> Notebooks
    
    Model --> Dashboard
    Notebooks --> Dashboard
    Schema --> API
    API --> Dashboard
```

---

## Flujo Detallado por Fuente

### 1. INE - Precios de Transacciones

```mermaid
sequenceDiagram
    participant Scheduler as Scheduler<br/>(Daily 6 AM)
    participant Extractor as INE Extractor
    participant API as INE API
    participant Raw as data/raw/
    participant Cleaner as Data Cleaner
    participant DB as PostgreSQL
    
    Scheduler->>Extractor: Trigger extraction
    Extractor->>API: Request data (barrios, 2020-2025)
    API-->>Extractor: CSV/JSON response
    Extractor->>Raw: Save ine_precios_YYYYMMDD.csv
    Extractor->>Cleaner: Trigger cleaning
    Cleaner->>Cleaner: Normalize prices (EUR)
    Cleaner->>Cleaner: Validate ranges (100k-2M)
    Cleaner->>Cleaner: Match barrios (codi_barri)
    Cleaner->>DB: INSERT INTO fact_precios
    DB-->>Cleaner: Success
    Cleaner->>Scheduler: Log completion
```

**Datos extraídos:**
- Precio por m² de venta
- Precio de alquiler mensual
- Número de transacciones
- Período: Trimestral/Anual

---

### 2. Portal de Dades - Demografía

```mermaid
sequenceDiagram
    participant Scheduler as Scheduler<br/>(Quarterly)
    participant Extractor as Portal Dades Extractor
    participant CKAN as CKAN API
    participant Raw as data/raw/
    participant Cleaner as Data Cleaner
    participant DB as PostgreSQL
    
    Scheduler->>Extractor: Trigger extraction
    Extractor->>CKAN: Search datasets<br/>("població", "demografia")
    CKAN-->>Extractor: Dataset list
    Extractor->>CKAN: Download resources
    CKAN-->>Extractor: CSV/GeoJSON files
    Extractor->>Raw: Save portal_demografia_YYYYMMDD.csv
    Extractor->>Cleaner: Trigger cleaning
    Cleaner->>Cleaner: Normalize barrio names
    Cleaner->>Cleaner: Aggregate by barrio/year
    Cleaner->>Cleaner: Calculate derived metrics
    Cleaner->>DB: INSERT INTO fact_demografia
    DB-->>Cleaner: Success
```

**Datos extraídos:**
- Población total por barrio
- Estructura de edad
- Composición de hogares
- Población extranjera
- Densidad poblacional

---

### 3. Catastro - Características de Viviendas

```mermaid
sequenceDiagram
    participant Extractor as Catastro Extractor
    participant Catastro as Sede Catastro
    participant Raw as data/raw/
    participant Cleaner as Data Cleaner
    participant DB as PostgreSQL
    
    Extractor->>Catastro: Request building data<br/>(Gràcia barrio)
    Catastro-->>Extractor: Building attributes CSV
    Extractor->>Raw: Save catastro_gracia_YYYYMMDD.csv
    Extractor->>Cleaner: Trigger cleaning
    Cleaner->>Cleaner: Extract superficie_m2
    Cleaner->>Cleaner: Extract ano_construccion
    Cleaner->>Cleaner: Extract plantas, ascensor
    Cleaner->>Cleaner: Match by ref_catastral
    Cleaner->>DB: UPDATE fact_precios<br/>(add attributes)
```

**Datos extraídos:**
- Superficie (m²)
- Año de construcción
- Número de plantas
- Presencia de ascensor
- Referencia catastral (para matching)

---

## Pipeline ETL Completo

### Fase 1: Extracción (Extract)

**Objetivo:** Obtener datos de fuentes externas sin modificar

**Proceso:**
1. Identificar fuente y endpoint
2. Autenticación (si requiere)
3. Request de datos con parámetros
4. Descarga de archivos (CSV/JSON/GeoJSON)
5. Guardado en `data/raw/` con timestamp
6. Logging de extracción

**Características:**
- Idempotente (puede ejecutarse múltiples veces)
- Manejo de errores y retry logic
- Rate limiting (respetar límites de APIs)
- Validación básica (archivo no vacío, formato correcto)

---

### Fase 2: Transformación (Transform)

**Objetivo:** Limpiar, normalizar y enriquecer datos

**Procesos:**

1. **Data Cleaning**
   - Eliminar duplicados
   - Manejar valores nulos
   - Normalizar formatos (fechas, precios, nombres)
   - Validar rangos (precios razonables, fechas válidas)

2. **Data Normalization**
   - Normalizar nombres de barrios
   - Estandarizar códigos (codi_barri)
   - Unificar unidades (EUR, m², fechas ISO)

3. **Data Enrichment**
   - Calcular métricas derivadas (densidad, tasas)
   - Agregar geocodificación (si falta)
   - Calcular distancias (al centro, a servicios)

4. **Data Validation**
   - Validar integridad referencial (barrio_id existe)
   - Validar completitud (≥95% campos requeridos)
   - Validar consistencia (rangos, tipos)

---

### Fase 3: Carga (Load)

**Objetivo:** Insertar datos limpios en PostgreSQL

**Proceso:**
1. Conectar a PostgreSQL
2. Validar schema (tablas existen)
3. Iniciar transacción
4. INSERT/UPDATE datos
5. Validar constraints
6. Commit o Rollback
7. Logging de carga

**Características:**
- Transaccional (todo o nada)
- Upsert logic (INSERT ... ON CONFLICT UPDATE)
- Batch inserts para performance
- Validación post-carga (conteo de registros)

---

## Flujo de Datos para Modelo Hedónico

```mermaid
graph LR
    subgraph "Data Sources"
        P[fact_precios]
        D[fact_demografia]
        B[dim_barrios]
    end
    
    subgraph "Feature Engineering"
        FE1[ln_precio<br/>ln_superficie]
        FE2[antiguedad<br/>distancia_centro]
        FE3[barrio_dummies]
    end
    
    subgraph "Model Input"
        X[Feature Matrix]
        Y[Target: ln_precio]
    end
    
    subgraph "Model Training"
        OLS[OLS Regression<br/>statsmodels]
    end
    
    subgraph "Outputs"
        Coef[Coefficients<br/>R² Metrics]
        Pred[Predictions]
        Diag[Diagnostics]
    end
    
    P --> FE1
    D --> FE2
    B --> FE3
    
    FE1 --> X
    FE2 --> X
    FE3 --> X
    P --> Y
    
    X --> OLS
    Y --> OLS
    
    OLS --> Coef
    OLS --> Pred
    OLS --> Diag
```

---

## Flujo de Datos para Dashboard

```mermaid
graph TB
    subgraph "Backend"
        DB[(PostgreSQL)]
        Model[Saved Model<br/>pickle/joblib]
    end
    
    subgraph "Streamlit App"
        Page1[Market Cockpit]
        Page2[Barrio Deep Dive]
        Page3[Regulatory Impact]
    end
    
    subgraph "User Actions"
        Select[Select Barrio]
        Filter[Filter by Year]
        Export[Export Data]
    end
    
    DB -->|Query prices| Page1
    DB -->|Query demographics| Page2
    Model -->|Predict prices| Page2
    DB -->|Query DiD results| Page3
    
    Select --> Page1
    Filter --> Page2
    Export --> Page1
    Export --> Page2
```

---

## Flujo de Datos para API

```mermaid
sequenceDiagram
    participant Client as API Client
    participant FastAPI as FastAPI Server
    participant Auth as JWT Auth
    participant DB as PostgreSQL
    participant Model as Hedonic Model
    participant Cache as Redis Cache
    
    Client->>FastAPI: GET /api/v1/barrios
    FastAPI->>Auth: Validate JWT token
    Auth-->>FastAPI: Token valid
    FastAPI->>Cache: Check cache
    alt Cache Hit
        Cache-->>FastAPI: Return cached data
    else Cache Miss
        FastAPI->>DB: Query barrios
        DB-->>FastAPI: Barrio data
        FastAPI->>Cache: Store in cache
    end
    FastAPI-->>Client: JSON response
    
    Client->>FastAPI: POST /api/v1/predict
    FastAPI->>Auth: Validate token
    FastAPI->>Model: Load model
    FastAPI->>Model: Predict price
    Model-->>FastAPI: Prediction result
    FastAPI-->>Client: JSON response
```

---

## Referencias

- **ETL Pipeline:** `docs/architecture/ETL_PIPELINE.md`
- **Database Schema:** `docs/architecture/DATABASE_SCHEMA_V2.md`
- **Model Specification:** `docs/modeling/MODEL_SPECIFICATION_V2.md`

---

**Última actualización:** Diciembre 2025

