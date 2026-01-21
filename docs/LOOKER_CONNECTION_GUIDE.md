# Looker Connection Guide - Barcelona Housing Demographics Analyzer

## Current Database System

**Database**: SQLite  
**Location**: `data/processed/database.db`  
**Schema**: Star Schema (Dimensional Model)  
**Tables**: 
- 1 dimension table: `dim_barrios`
- 20+ fact tables: `fact_precios`, `fact_demografia`, `fact_renta`, etc.
- Multiple analytical views: `vw_gentrification_risk`, etc.

## Challenge: SQLite + Looker

**⚠️ Important**: Looker does **not natively support SQLite** connections. Looker supports:
- PostgreSQL ✅
- MySQL ✅
- BigQuery ✅
- Snowflake ✅
- Redshift ✅
- SQL Server ✅
- **SQLite ❌** (Not supported)

## Solution Options

### Option 1: Migrate to PostgreSQL (Recommended for Production)

**Best for**: Production deployments, team collaboration, advanced analytics

**Steps**:

1. **Set up PostgreSQL database**:
   ```bash
   # Install PostgreSQL (if not already installed)
   brew install postgresql@14  # macOS
   # or
   sudo apt-get install postgresql-14  # Linux
   
   # Create database
   createdb barcelona_housing
   ```

2. **Install PostGIS extension** (for geospatial data):
   ```sql
   CREATE EXTENSION postgis;
   ```

3. **Migrate data from SQLite to PostgreSQL**:
   - Use `pgloader` or custom Python script
   - See migration script below

4. **Connect Looker to PostgreSQL**:
   - In Looker: Admin → Connections → New Connection
   - Type: PostgreSQL
   - Host: Your PostgreSQL server
   - Database: `barcelona_housing`
   - Port: 5432
   - Username/Password: Your credentials

**Migration Script** (`scripts/migrate_sqlite_to_postgresql.py`):
```python
#!/usr/bin/env python3
"""
Migrate SQLite database to PostgreSQL for Looker integration.
"""
import sqlite3
import psycopg2
from pathlib import Path
import pandas as pd

SQLITE_DB = Path("data/processed/database.db")
POSTGRES_CONFIG = {
    "host": "localhost",
    "database": "barcelona_housing",
    "user": "your_user",
    "password": "your_password",
    "port": 5432
}

def migrate_table(table_name: str, sqlite_conn, pg_conn):
    """Migrate a single table from SQLite to PostgreSQL."""
    # Read from SQLite
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    
    if df.empty:
        print(f"⚠️  Table {table_name} is empty, skipping...")
        return
    
    # Write to PostgreSQL
    df.to_sql(table_name, pg_conn, if_exists='replace', index=False, method='multi')
    print(f"✅ Migrated {table_name}: {len(df)} rows")

def main():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
    
    # Get list of tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        sqlite_conn
    )['name'].tolist()
    
    # Exclude system tables
    tables = [t for t in tables if not t.startswith('sqlite_')]
    
    print(f"📦 Migrating {len(tables)} tables...")
    
    for table in tables:
        try:
            migrate_table(table, sqlite_conn, pg_conn)
        except Exception as e:
            print(f"❌ Error migrating {table}: {e}")
    
    sqlite_conn.close()
    pg_conn.close()
    print("✅ Migration complete!")

if __name__ == "__main__":
    main()
```

**Estimated Time**: 4-6 hours (including PostgreSQL setup)

---

### Option 2: SQLite to PostgreSQL Sync Tool

**Best for**: Quick migration without code changes

**Tools**:
- **pgloader**: Command-line tool for database migration
  ```bash
  # Install pgloader
  brew install pgloader  # macOS
  # or
  sudo apt-get install pgloader  # Linux
  
  # Migrate
  pgloader data/processed/database.db \
    postgresql://user:password@localhost/barcelona_housing
  ```

- **DB Browser for SQLite** → Export → PostgreSQL script

**Estimated Time**: 1-2 hours

---

### Option 3: Export to CSV/Parquet + Looker File Connection

**Best for**: Quick prototyping, one-time analysis, small datasets

**Steps**:

1. **Export tables to CSV/Parquet**:
   ```python
   # scripts/export_for_looker.py
   import pandas as pd
   import sqlite3
   from pathlib import Path
   
   conn = sqlite3.connect("data/processed/database.db")
   output_dir = Path("data/exports/looker")
   output_dir.mkdir(parents=True, exist_ok=True)
   
   tables = ["dim_barrios", "fact_precios", "fact_demografia", ...]
   
   for table in tables:
       df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
       # Export as CSV
       df.to_csv(output_dir / f"{table}.csv", index=False)
       # Or as Parquet (better for large files)
       df.to_parquet(output_dir / f"{table}.parquet", index=False)
   ```

2. **Upload to cloud storage** (S3, GCS, etc.)

3. **Connect Looker to file source**:
   - Looker supports file-based connections via:
     - Google Cloud Storage
     - Amazon S3
     - Azure Blob Storage
   - Or use Looker's "Upload File" feature (limited to smaller datasets)

**Limitations**:
- ❌ No real-time updates (manual refresh required)
- ❌ Limited to smaller datasets
- ❌ No complex joins across files

**Estimated Time**: 1 hour

---

### Option 4: SQLite ODBC Bridge (Advanced)

**Best for**: Temporary solution, testing

**Steps**:

1. **Install SQLite ODBC driver**:
   - macOS: `brew install sqlite-odbc`
   - Linux: `sudo apt-get install unixodbc unixodbc-dev libsqliteodbc`

2. **Configure ODBC DSN**:
   ```ini
   # /etc/odbc.ini
   [BarcelonaHousing]
   Driver=SQLite3
   Database=/path/to/data/processed/database.db
   ```

3. **Use PostgreSQL Foreign Data Wrapper** (if you have PostgreSQL):
   ```sql
   -- In PostgreSQL
   CREATE EXTENSION postgres_fdw;
   CREATE SERVER sqlite_server FOREIGN DATA WRAPPER odbc_fdw;
   ```

**Limitations**:
- ⚠️ Complex setup
- ⚠️ Performance may be slower
- ⚠️ Not officially supported by Looker

**Estimated Time**: 4-6 hours (complex setup)

---

## Recommended Approach

### For Production Use: **Option 1 (PostgreSQL Migration)**

**Why**:
- ✅ Native Looker support
- ✅ Better performance for analytics
- ✅ PostGIS for advanced geospatial queries
- ✅ Concurrent access for team collaboration
- ✅ Scalable for future growth

**Migration Checklist**:
- [ ] Set up PostgreSQL server
- [ ] Install PostGIS extension
- [ ] Run migration script
- [ ] Verify data integrity
- [ ] Update application code (optional, can keep SQLite for local dev)
- [ ] Configure Looker connection
- [ ] Test queries in Looker

### For Quick Testing: **Option 3 (CSV Export)**

**Why**:
- ✅ Fastest to implement
- ✅ No infrastructure changes
- ✅ Good for proof-of-concept

---

## Database Schema Reference

### Key Tables for Looker

**Dimension Tables**:
- `dim_barrios` - Neighborhood master data (73 barrios)
- `dim_tiempo` - Time dimension (years, quarters)

**Fact Tables**:
- `fact_precios` - Housing prices (sale & rental)
- `fact_demografia` - Demographics
- `fact_renta` - Income data
- `fact_educacion` - Education metrics
- `fact_seguridad` - Safety/crime data
- `fact_calidad_aire` - Air quality
- `fact_turismo_intensidad` - Tourism pressure
- `fact_regulacion` - Rental regulation data
- ... (20+ fact tables)

**Analytical Views**:
- `vw_gentrification_risk` - Gentrification risk scores
- `vw_affordability` - Affordability metrics
- ... (multiple views)

### Sample Looker Model (LookML)

Once connected to PostgreSQL, you can create a LookML model:

```lookml
connection: barcelona_housing_postgres {
  host: "your-postgres-host"
  database: "barcelona_housing"
  user: "your_user"
  password: "your_password"
  port: 5432
}

datagroup: barcelona_housing_default_datagroup {
  sql_trigger: SELECT MAX(etl_loaded_at) FROM etl_runs ;;
}

model: barcelona_housing {
  connection: barcelona_housing_postgres
  
  explore: fact_precios {
    label: "Housing Prices"
    join: dim_barrios {
      sql_on: ${fact_precios.barrio_id} = ${dim_barrios.barrio_id} ;;
      relationship: many_to_one
    }
  }
  
  explore: fact_demografia {
    label: "Demographics"
    join: dim_barrios {
      sql_on: ${fact_demografia.barrio_id} = ${dim_barrios.barrio_id} ;;
      relationship: many_to_one
    }
  }
}
```

---

## Next Steps

1. **Choose your approach** based on your needs
2. **Set up PostgreSQL** (if choosing Option 1)
3. **Run migration** using provided scripts
4. **Configure Looker connection**
5. **Create LookML models** for your analytics

## Support

For questions or issues:
- Check PostgreSQL migration logs
- Verify database connectivity
- Review Looker connection documentation: https://docs.looker.com/

---

**Last Updated**: 2026-01-10  
**Database Version**: SQLite 3.x → PostgreSQL 14+ (recommended)
