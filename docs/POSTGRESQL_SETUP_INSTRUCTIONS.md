# PostgreSQL Setup Instructions for Looker Integration

## Quick Start Guide

This guide will help you set up PostgreSQL and migrate your SQLite database for Looker integration.

## Prerequisites Check

✅ **PostgreSQL**: Already installed (version 16.8)  
✅ **psycopg2**: Already installed  
⚠️ **python-dotenv**: May need installation

## Step-by-Step Setup

### Step 1: Install Missing Dependencies

```bash
# Install python-dotenv for environment variable management
pip install python-dotenv
```

### Step 2: Create PostgreSQL Database

Run the setup script:

```bash
./scripts/setup_postgresql_database.sh
```

This will:
- Create database `barcelona_housing`
- Enable PostGIS extension (for geospatial data)
- Verify the setup

**Alternative (manual)**:
```bash
createdb barcelona_housing
psql -d barcelona_housing -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Step 3: Configure Environment Variables

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your PostgreSQL credentials:
   ```bash
   # Edit .env file
   nano .env  # or use your preferred editor
   ```

   Update these values:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DATABASE=barcelona_housing
   POSTGRES_USER=your_username        # Usually your macOS username
   POSTGRES_PASSWORD=your_password    # Leave empty to be prompted
   ```

   **Note**: If you don't have a PostgreSQL password set, you can:
   - Leave `POSTGRES_PASSWORD` empty (script will prompt)
   - Or set it to your macOS user password if PostgreSQL uses peer authentication

### Step 4: Run Migration

```bash
python scripts/migrate_sqlite_to_postgresql.py
```

The script will:
- ✅ Check dependencies
- ✅ Connect to both databases
- ✅ Migrate all tables (preserving data)
- ✅ Create indexes for performance
- ✅ Provide summary statistics

**Expected output**:
```
============================================================
🔄 SQLite to PostgreSQL Migration
============================================================
✅ PostgreSQL connection successful
Connecting to SQLite: /path/to/data/processed/database.db
📦 Found 25 tables to migrate:
   dim_barrios, fact_precios, fact_demografia...
✅ Migrated dim_barrios: 73 rows
✅ Migrated fact_precios: 1011 rows
...
📊 MIGRATION SUMMARY
============================================================
✅ Successfully migrated: 25/25 tables
📈 Total rows migrated: 15,234
```

### Step 5: Verify Migration

Connect to PostgreSQL and verify:

```bash
psql -d barcelona_housing

# Check tables
\dt

# Check row counts
SELECT 
    'dim_barrios' as table_name, 
    COUNT(*) as rows 
FROM dim_barrios
UNION ALL
SELECT 'fact_precios', COUNT(*) FROM fact_precios
UNION ALL
SELECT 'fact_demografia', COUNT(*) FROM fact_demografia;

# Test a query
SELECT 
    b.barrio_nombre,
    AVG(p.precio_m2_venta) as avg_price
FROM fact_precios p
JOIN dim_barrios b ON p.barrio_id = b.barrio_id
WHERE p.anio = 2024
GROUP BY b.barrio_nombre
ORDER BY avg_price DESC
LIMIT 10;
```

### Step 6: Configure Looker Connection

1. **In Looker**: Go to Admin → Connections → New Connection

2. **Connection Settings**:
   - **Type**: PostgreSQL
   - **Name**: Barcelona Housing
   - **Host**: `localhost` (or your PostgreSQL server)
   - **Port**: `5432`
   - **Database**: `barcelona_housing`
   - **Username**: Your PostgreSQL username
   - **Password**: Your PostgreSQL password
   - **Schema**: `public` (default)

3. **Test Connection**: Click "Test Connection" to verify

4. **Create LookML Model**: See `docs/LOOKER_CONNECTION_GUIDE.md` for sample LookML

## Troubleshooting

### Issue: "Database does not exist"

**Solution**:
```bash
# Create the database
createdb barcelona_housing
```

### Issue: "Password authentication failed"

**Solutions**:
1. Check your `.env` file has correct password
2. Or leave password empty in `.env` and enter when prompted
3. For macOS, PostgreSQL might use peer authentication (no password needed)

### Issue: "Permission denied" when creating database

**Solution**:
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if not running
brew services start postgresql@16

# Or use your system's PostgreSQL service
```

### Issue: "psycopg2 not installed"

**Solution**:
```bash
pip install psycopg2-binary
```

### Issue: "Module 'dotenv' not found"

**Solution**:
```bash
pip install python-dotenv
```

## Database Schema Overview

After migration, you'll have:

**Dimension Tables**:
- `dim_barrios` (73 neighborhoods)
- `dim_tiempo` (time dimension)

**Fact Tables** (20+):
- `fact_precios` (housing prices)
- `fact_demografia` (demographics)
- `fact_renta` (income)
- `fact_educacion` (education)
- `fact_seguridad` (safety)
- `fact_calidad_aire` (air quality)
- `fact_turismo_intensidad` (tourism)
- ... and more

**Analytical Views**:
- `vw_gentrification_risk`
- `vw_affordability`
- ... and more

## Next Steps

1. ✅ **Migration Complete**: Data is in PostgreSQL
2. 📊 **Connect Looker**: Follow Step 6 above
3. 📝 **Create LookML Models**: See `docs/LOOKER_CONNECTION_GUIDE.md`
4. 🔄 **Keep SQLite Updated**: Run migration script after ETL updates

## Maintenance

### Re-run Migration After ETL Updates

After running your ETL pipeline and updating SQLite:

```bash
# Re-run migration (will replace existing data)
python scripts/migrate_sqlite_to_postgresql.py
```

### Backup PostgreSQL Database

```bash
# Create backup
pg_dump barcelona_housing > backup_$(date +%Y%m%d).sql

# Restore from backup
psql barcelona_housing < backup_20260110.sql
```

## Support

For issues:
1. Check migration logs
2. Verify PostgreSQL is running: `brew services list | grep postgresql`
3. Check database exists: `psql -l | grep barcelona_housing`
4. Review connection settings in `.env`

---

**Last Updated**: 2026-01-10  
**PostgreSQL Version**: 16.8  
**Database Size**: ~4.5 MB (SQLite) → ~5-10 MB (PostgreSQL with indexes)
