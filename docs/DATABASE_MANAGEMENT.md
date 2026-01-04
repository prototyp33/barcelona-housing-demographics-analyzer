# Database Management Guide

## Overview

The Barcelona Housing Demographics Analyzer uses a centralized `DatabaseManager` class to handle all database connections and operations. This ensures consistency, proper connection management, and integrated data quality monitoring.

## Quick Start

### 1. Verify Database Connection

Run the verification script to check your database setup:

```bash
python3 scripts/verify_database.py
```

Expected output:

```
============================================================
Barcelona Housing Demographics - Database Verification
============================================================

✓ Database connection successful

📊 Checking key tables:
  ✓ dim_barrios
  ✓ fact_precios
  ✓ fact_renta
  ✓ v_demografia_aggregated

📈 Data counts:
  • Barrios: 73
  • Barrios con geometría: 73
  • Registros de precios: 6,358
  • Registros de renta: 73
  • Registros demográficos: 73

📅 Year coverage:
  • Precios: 2012 - 2025
  • Renta: 2023 - 2023
  • Demografía: 2025 - 2025

🎯 Data Quality Metrics:
  • Completeness: 100.0%
  • Validity: 84.2%
  • Consistency: 0.0%
  • Timeliness: 4 days since last update
```

### 2. Run the Dashboard

```bash
./run_dashboard.sh
```

Or manually:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
streamlit run src/app/main.py
```

### 3. Run the API

```bash
./run_api.sh
```

Or manually:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.api.main:app --reload --port 8000
```

## DatabaseManager Usage

### Basic Connection

```python
from src.database import DatabaseManager

# Initialize (uses default path: data/processed/database.db)
db = DatabaseManager()

# Get a connection
conn = db.get_connection()
try:
    # Your database operations
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dim_barrios LIMIT 5")
    results = cursor.fetchall()
finally:
    conn.close()
```

### Execute Queries

```python
# Execute a query and get results as DataFrame
df = db.execute_query(
    "SELECT barrio_nombre, distrito_nombre FROM dim_barrios WHERE distrito_nombre = ?",
    params=("Eixample",)
)
print(df)
```

### Check Table/View Existence

```python
# Check if a table or view exists
if db.table_exists("v_demografia_aggregated"):
    print("Demographics view is available")
```

### Get Data Quality Metrics

```python
# Get comprehensive quality metrics
metrics = db.get_quality_metrics()
print(f"Completeness: {metrics['completeness']}%")
print(f"Validity: {metrics['validity']}%")
print(f"Consistency: {metrics['consistency']}%")
print(f"Timeliness: {metrics['timeliness']} days")
```

## Data Quality Monitoring

The system automatically tracks four key quality dimensions:

### 1. **Completeness** (Target: ≥95%)

Percentage of non-null values in critical fields across all fact tables.

### 2. **Validity** (Target: ≥98%)

Percentage of values that pass validation rules:

- Prices > 0
- Coordinates within Barcelona bounds
- Years between 2000-2030

### 3. **Consistency** (Target: 100%)

Ensures all barrio_ids in fact tables exist in dim_barrios.

### 4. **Timeliness**

Days since the most recent data update (ETL timestamp).

## Database Schema

### Core Tables

- **`dim_barrios`**: 73 Barcelona neighborhoods with geometries
- **`fact_precios`**: Housing prices (2012-2025)
- **`fact_renta`**: Household income (2023)
- **`fact_demografia_ampliada`**: Detailed demographics by age/gender/nationality

### Key Views

- **`v_demografia_aggregated`**: Aggregated demographics per neighborhood/year
- **`v_precios_evolucion_anual`**: Annual price evolution
- **`v_correlaciones_cruzadas`**: Cross-metric correlations

## Troubleshooting

### Database Not Found

```python
FileNotFoundError: Base de datos no encontrada: data/processed/database.db
```

**Solution**: Initialize the database schema:

```bash
python3 src/database_setup.py
```

### Missing Data

If tables exist but are empty, run the ETL pipeline:

```bash
python3 src/etl/extract_opendata_bcn.py
python3 src/etl/extract_portal_dades.py
```

### View Not Found

If `v_demografia_aggregated` doesn't exist:

```bash
python3 src/database_views.py
```

### Low Data Quality Scores

Check the Data Quality dashboard view in Streamlit to see specific issues and affected neighborhoods.

## Best Practices

1. **Always use DatabaseManager** instead of creating raw sqlite3 connections
2. **Close connections** in finally blocks or use context managers
3. **Monitor quality metrics** regularly via the dashboard
4. **Run verification** after any ETL updates
5. **Keep views updated** when schema changes

## Advanced Usage

### Custom Database Path

```python
from pathlib import Path
from src.database import DatabaseManager

# Use a different database
db = DatabaseManager(db_path=Path("data/backup/database.db"))
```

### Transaction Management

```python
db = DatabaseManager()
conn = db.get_connection()
try:
    conn.execute("BEGIN TRANSACTION")
    # Multiple operations
    conn.execute("INSERT INTO ...")
    conn.execute("UPDATE ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

### Batch Operations

```python
import pandas as pd

# Load large dataset
df = pd.read_csv("new_data.csv")

# Write to database
conn = db.get_connection()
try:
    df.to_sql("fact_new_data", conn, if_exists="append", index=False)
finally:
    conn.close()
```

## Related Documentation

- [Database Schema](DATABASE_SCHEMA.md)
- [ETL Pipeline](ETL_PIPELINE.md)
- [Data Quality Standards](DATA_QUALITY.md)
- [API Documentation](API.md)
