#!/usr/bin/env python3
"""
Fix script for vw_gentrification_risk view.

Drops and recreates the view to ensure it only uses columns that exist
in the actual database tables.
"""

import sys
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def verify_table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Get list of columns in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]


def fix_view(conn: sqlite3.Connection, dry_run: bool = False) -> bool:
    """
    Fix the vw_gentrification_risk view.
    
    Args:
        conn: Database connection.
        dry_run: If True, only shows what would be done.
    
    Returns:
        True if successful, False otherwise.
    """
    print("🔍 Checking table structures...")
    
    # Verify columns exist
    educacion_cols = verify_table_columns(conn, "fact_educacion")
    precios_cols = verify_table_columns(conn, "fact_precios")
    calidad_aire_cols = verify_table_columns(conn, "fact_calidad_aire")
    ruido_cols = verify_table_columns(conn, "fact_ruido")
    
    print(f"   fact_educacion columns: {', '.join(educacion_cols[:5])}...")
    print(f"   fact_precios columns: {', '.join(precios_cols[:5])}...")
    
    # Check if problematic column exists
    if "pct_universitarios" in educacion_cols:
        print("   ⚠️  pct_universitarios exists in fact_educacion")
    else:
        print("   ✅ pct_universitarios does NOT exist (expected)")
    
    # Verify required columns exist
    required_cols = {
        "fact_educacion": ["total_centros_educativos", "num_centros_universidad"],
        "fact_precios": ["precio_m2_venta"],
        "fact_calidad_aire": ["pm25_mean"],
        "fact_ruido": ["pct_poblacion_expuesta_65db"],
    }
    
    missing = []
    for table, cols in required_cols.items():
        table_cols = verify_table_columns(conn, table)
        for col in cols:
            if col not in table_cols:
                missing.append(f"{table}.{col}")
    
    if missing:
        print(f"   ❌ Missing required columns: {missing}")
        return False
    
    print("   ✅ All required columns exist")
    
    # Drop and recreate view
    print("\n🔧 Fixing view...")
    
    drop_sql = "DROP VIEW IF EXISTS vw_gentrification_risk;"
    create_sql = """
    CREATE VIEW vw_gentrification_risk AS
    SELECT 
        b.barrio_nombre AS nom_barri,
        b.barrio_id,
        e.anio AS year,
        e.total_centros_educativos AS num_centros_educativos,
        e.num_centros_universidad AS num_universidades,
        p.precio_m2_venta AS precio_venta_medio_m2,
        a.pm25_mean,
        r.pct_poblacion_expuesta_65db AS pct_exposed_65db
    FROM dim_barrios b
    LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
    LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND e.anio = p.anio
    LEFT JOIN fact_calidad_aire a ON b.barrio_id = a.barrio_id AND e.anio = a.anio
    LEFT JOIN fact_ruido r ON b.barrio_id = r.barrio_id AND e.anio = r.anio;
    """
    
    if dry_run:
        print("   [DRY RUN] Would execute:")
        print(f"   {drop_sql}")
        print(f"   {create_sql.strip()}")
        return True
    
    try:
        conn.execute(drop_sql)
        conn.execute(create_sql)
        conn.commit()
        print("   ✅ View dropped and recreated")
    except sqlite3.Error as e:
        print(f"   ❌ Error: {e}")
        conn.rollback()
        return False
    
    # Verify view works
    print("\n✅ Verifying view...")
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM vw_gentrification_risk")
        count = cursor.fetchone()[0]
        print(f"   ✅ View returns {count} records")
        
        # Test a sample query
        cursor = conn.execute("""
            SELECT 
                nom_barri,
                num_centros_educativos,
                precio_venta_medio_m2
            FROM vw_gentrification_risk
            WHERE precio_venta_medio_m2 IS NOT NULL
            LIMIT 5
        """)
        sample = cursor.fetchall()
        if sample:
            print("   ✅ Sample query successful")
            print("   Sample records:")
            for row in sample:
                print(f"      {row[0]}: {row[1]} centros, €{row[2]:,.0f}/m²")
        
        return True
    except sqlite3.Error as e:
        print(f"   ❌ View verification failed: {e}")
        return False


def main() -> int:
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix vw_gentrification_risk view")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help=f"Path to database (default: {DB_PATH})"
    )
    
    args = parser.parse_args()
    
    if not args.db_path.exists():
        print(f"❌ Database not found at {args.db_path}", file=sys.stderr)
        return 1
    
    conn = sqlite3.connect(args.db_path)
    
    try:
        success = fix_view(conn, dry_run=args.dry_run)
        if success:
            print("\n🎉 View fix completed successfully!")
            return 0
        else:
            print("\n❌ View fix failed")
            return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
