#!/usr/bin/env python3
"""
Export data from PostgreSQL to CSV files for Looker Studio upload.

This script exports all relevant tables and views to organized CSV files
that can be uploaded directly to Looker Studio.

Output structure:
  data/exports/looker_studio/
    ├── 01_dimensions/
    │   ├── dim_barrios.csv
    │   └── dim_tiempo.csv
    ├── 02_market/
    │   ├── fact_precios.csv
    │   └── fact_oferta_idealista.csv
    ├── 03_demographics/
    │   ├── fact_demografia.csv
    │   └── fact_renta.csv
    ├── 04_environment/
    │   ├── fact_calidad_aire.csv
    │   └── fact_ruido.csv
    ├── 05_social/
    │   ├── fact_seguridad.csv
    │   └── fact_educacion.csv
    ├── 06_tourism/
    │   └── fact_turismo_intensidad.csv
    └── 07_analytical_views/
        ├── v_riesgo_gentrificacion.csv
        └── v_affordability_detallado.csv
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

# Output directory structure
EXPORT_BASE = PROJECT_ROOT / "data" / "exports" / "looker_studio"

# Table organization by category
TABLE_CATEGORIES = {
    "01_dimensions": [
        "dim_barrios",
        "dim_barrios_extended",
        "dim_tiempo",
    ],
    "02_market": [
        "fact_precios",
        "fact_oferta_idealista",
        "fact_regulacion",
    ],
    "03_demographics": [
        "fact_demografia_ampliada",  # fact_demografia may not exist, using ampliada
        "fact_renta",
        "fact_renta_avanzada",
        "fact_desempleo",
    ],
    "04_environment": [
        "fact_calidad_aire",
        "fact_ruido",
        "fact_medio_ambiente",
    ],
    "05_social": [
        "fact_seguridad",
        "fact_educacion",
        "fact_servicios_salud",
        "fact_comercio",
        "fact_movilidad",
    ],
    "06_tourism": [
        "fact_turismo_intensidad",
        "fact_presion_turistica",
    ],
    "07_housing": [
        "fact_vivienda_publica",
        "fact_housing_master",
    ],
    "08_advanced": [
        "fact_catastro_avanzado",
        "fact_hogares_avanzado",
        "fact_vivienda_contexto_metropolitano",
    ],
}

# Analytical views to export
ANALYTICAL_VIEWS = [
    "v_riesgo_gentrificacion",
    "v_affordability_detallado",
    "v_precios_evolucion_anual",
    "v_demografia_resumen",
    "v_correlaciones_cruzadas",
    "v_barrio_scorecard",
]


def get_connection():
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def table_exists(conn, table_name: str) -> bool:
    """Check if table exists in database."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return cursor.fetchone()[0]
    except:
        return False


def export_table(conn, table_name: str, output_path: Path) -> int:
    """
    Export a table to CSV.
    
    Returns:
        Number of rows exported.
    """
    # Check if table exists
    if not table_exists(conn, table_name):
        logger.warning(f"  ⚠️  Table {table_name} does not exist, skipping")
        return 0
    
    try:
        query = f'SELECT * FROM "{table_name}"'
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            logger.warning(f"  ⚠️  Table {table_name} is empty")
            return 0
        
        # Clean column names (remove special characters for Looker Studio)
        df.columns = df.columns.str.replace(' ', '_').str.lower()
        
        # Remove BOM and use standard UTF-8 (Looker Studio prefers this)
        # Also ensure no hidden characters
        df.columns = df.columns.str.strip()
        
        # Save to CSV with standard UTF-8 (no BOM) for better Looker Studio compatibility
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
        
        logger.info(f"  ✅ Exported {table_name}: {len(df):,} rows")
        return len(df)
        
    except Exception as e:
        logger.error(f"  ❌ Error exporting {table_name}: {e}")
        return 0


def view_exists(conn, view_name: str) -> bool:
    """Check if view exists in database."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (view_name,))
        return cursor.fetchone()[0]
    except:
        return False


def export_view(conn, view_name: str, output_path: Path) -> int:
    """
    Export a view to CSV.
    
    Returns:
        Number of rows exported.
    """
    # Check if view exists
    if not view_exists(conn, view_name):
        logger.warning(f"  ⚠️  View {view_name} does not exist, skipping")
        return 0
    
    try:
        query = f'SELECT * FROM "{view_name}"'
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            logger.warning(f"  ⚠️  View {view_name} is empty")
            return 0
        
        # Clean column names
        df.columns = df.columns.str.replace(' ', '_').str.lower()
        df.columns = df.columns.str.strip()
        
        # Save to CSV with standard UTF-8 (no BOM) for better Looker Studio compatibility
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
        
        logger.info(f"  ✅ Exported {view_name}: {len(df):,} rows")
        return len(df)
        
    except Exception as e:
        logger.warning(f"  ⚠️  Error exporting {view_name}: {e}")
        return 0


def create_readme(output_dir: Path) -> None:
    """Create README with file descriptions."""
    readme_content = """# Looker Studio Data Exports

This directory contains CSV files exported from the Barcelona Housing database, organized by category for easy upload to Looker Studio.

## Directory Structure

### 01_dimensions/
**Master reference data**
- `dim_barrios.csv` - All 73 neighborhoods with names, districts, codes, and geometry
- `dim_barrios_extended.csv` - Extended neighborhood data with KPIs
- `dim_tiempo.csv` - Time dimension (years, quarters, months)

**Use for**: Joining with fact tables, filtering by neighborhood/district

### 02_market/
**Housing market data**
- `fact_precios.csv` - Housing prices (sale & rental) by neighborhood and year
- `fact_oferta_idealista.csv` - Real estate listings from Idealista
- `fact_regulacion.csv` - Rental regulation data (rental index, stressed zones)

**Use for**: Price analysis, market trends, rental regulation impact

### 03_demographics/
**Demographic and income data**
- `fact_demografia.csv` - Basic demographics (population, age, gender)
- `fact_demografia_ampliada.csv` - Detailed demographics by age group, nationality
- `fact_renta.csv` - Income data (median, average income)
- `fact_renta_avanzada.csv` - Advanced income metrics (Gini coefficient, etc.)
- `fact_desempleo.csv` - Unemployment data

**Use for**: Demographic analysis, income distribution, social indicators

### 04_environment/
**Environmental data**
- `fact_calidad_aire.csv` - Air quality metrics (NO2, PM2.5, etc.)
- `fact_ruido.csv` - Noise levels (Lden, Ld, Ln)
- `fact_medio_ambiente.csv` - Other environmental metrics

**Use for**: Environmental impact analysis, quality of life metrics

### 05_social/
**Social services and infrastructure**
- `fact_seguridad.csv` - Crime/safety data
- `fact_educacion.csv` - Education facilities and metrics
- `fact_servicios_salud.csv` - Health services
- `fact_comercio.csv` - Commercial activity
- `fact_movilidad.csv` - Transportation and mobility

**Use for**: Social infrastructure analysis, accessibility metrics

### 06_tourism/
**Tourism pressure**
- `fact_turismo_intensidad.csv` - Tourism intensity index
- `fact_presion_turistica.csv` - Tourism pressure metrics

**Use for**: Gentrification analysis, tourism impact

### 07_housing/
**Housing data**
- `fact_vivienda_publica.csv` - Public housing data
- `fact_housing_master.csv` - Master housing data

**Use for**: Housing policy analysis

### 08_advanced/
**Advanced metrics**
- `fact_catastro_avanzado.csv` - Advanced cadastral data
- `fact_hogares_avanzado.csv` - Advanced household data
- `fact_vivienda_contexto_metropolitano.csv` - Metropolitan context

**Use for**: Advanced analysis, detailed metrics

### 07_analytical_views/
**Pre-calculated analytical views**
- `v_riesgo_gentrificacion.csv` - Gentrification risk scores
- `v_affordability_detallado.csv` - Detailed affordability metrics
- `v_precios_evolucion_anual.csv` - Annual price evolution
- `v_demografia_resumen.csv` - Demographic summary
- `v_correlaciones_cruzadas.csv` - Cross-correlations
- `v_barrio_scorecard.csv` - Neighborhood scorecards

**Use for**: Ready-to-use metrics, dashboards, quick analysis

## How to Use in Looker Studio

### Option 1: Upload Individual Files
1. In Looker Studio: **Create** → **Data Source**
2. Select **File Upload**
3. Upload the CSV file you need
4. Configure fields and data types

### Option 2: Use Multiple Files with Blending
1. Upload multiple CSV files as separate data sources
2. Use **Data Blending** to join them
3. Join on common keys:
   - `barrio_id` - Neighborhood ID
   - `anio` - Year
   - `barrio_nombre` - Neighborhood name

### Recommended Data Sources for Common Analyses

**Price Analysis Dashboard**:
- `02_market/fact_precios.csv`
- `01_dimensions/dim_barrios.csv` (for joins)

**Demographics Dashboard**:
- `03_demographics/fact_demografia.csv`
- `03_demographics/fact_renta.csv`
- `01_dimensions/dim_barrios.csv`

**Gentrification Analysis**:
- `07_analytical_views/v_riesgo_gentrificacion.csv`
- `06_tourism/fact_turismo_intensidad.csv`
- `02_market/fact_precios.csv`

**Affordability Analysis**:
- `07_analytical_views/v_affordability_detallado.csv`
- `03_demographics/fact_renta.csv`
- `02_market/fact_precios.csv`

**Environmental Dashboard**:
- `04_environment/fact_calidad_aire.csv`
- `04_environment/fact_ruido.csv`
- `01_dimensions/dim_barrios.csv`

## Data Updates

To refresh the data:
```bash
python scripts/export_data_for_looker_studio.py
```

This will regenerate all CSV files with the latest data from PostgreSQL.

## Notes

- All files use UTF-8 encoding with BOM (utf-8-sig) for Excel compatibility
- Column names are normalized (lowercase, underscores)
- Dates are in ISO format (YYYY-MM-DD)
- Empty tables are skipped (you'll see a warning)

---
**Last Updated**: 2026-01-10
**Database**: barcelona_housing (PostgreSQL)
"""
    
    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    logger.info(f"✅ Created README: {readme_path}")


def main() -> int:
    """Main export function."""
    logger.info("=" * 60)
    logger.info("📊 Exporting Data for Looker Studio")
    logger.info("=" * 60)
    
    # Create output directory
    EXPORT_BASE.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    try:
        conn = get_connection()
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect: {e}")
        return 1
    
    total_rows = 0
    total_files = 0
    
    try:
        # Export tables by category
        logger.info("\n📦 Exporting tables by category...")
        for category, tables in TABLE_CATEGORIES.items():
            logger.info(f"\n{category}:")
            category_dir = EXPORT_BASE / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            for table in tables:
                output_path = category_dir / f"{table}.csv"
                rows = export_table(conn, table, output_path)
                if rows > 0:
                    total_rows += rows
                    total_files += 1
        
        # Export analytical views
        logger.info("\n📊 Exporting analytical views...")
        views_dir = EXPORT_BASE / "07_analytical_views"
        views_dir.mkdir(parents=True, exist_ok=True)
        
        for view in ANALYTICAL_VIEWS:
            output_path = views_dir / f"{view}.csv"
            rows = export_view(conn, view, output_path)
            if rows > 0:
                total_rows += rows
                total_files += 1
        
        # Create README
        logger.info("\n📝 Creating README...")
        create_readme(EXPORT_BASE)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ EXPORT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Files exported: {total_files}")
        logger.info(f"Total rows: {total_rows:,}")
        logger.info(f"Output directory: {EXPORT_BASE}")
        logger.info("\nNext steps:")
        logger.info("  1. Review files in: data/exports/looker_studio/")
        logger.info("  2. Upload CSV files to Looker Studio")
        logger.info("  3. Use README.md for guidance on which files to use")
        
        return 0
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
