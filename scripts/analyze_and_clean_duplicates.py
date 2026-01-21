#!/usr/bin/env python3
"""
Analyze and optionally clean duplicates in fact_precios.

This script:
1. Analyzes duplicate patterns in fact_precios
2. Shows statistics and examples
3. Optionally removes duplicates (with backup)
"""

import argparse
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def analyze_duplicates(conn: sqlite3.Connection) -> dict:
    """
    Analiza los duplicados en fact_precios.
    
    Returns:
        Diccionario con estadísticas de duplicados.
    """
    print("🔍 Analyzing duplicates in fact_precios...\n")
    
    # Total records
    total = pd.read_sql("SELECT COUNT(*) as n FROM fact_precios", conn)["n"].iloc[0]
    
    # Duplicate groups (barrio_id + anio)
    dup_groups = pd.read_sql("""
        SELECT 
            barrio_id,
            anio,
            COUNT(*) as dup_count,
            COUNT(DISTINCT dataset_id) as unique_datasets,
            COUNT(DISTINCT source) as unique_sources,
            COUNT(DISTINCT trimestre) as unique_trimestres
        FROM fact_precios
        GROUP BY barrio_id, anio
        HAVING COUNT(*) > 1
    """, conn)
    
    total_dup_groups = len(dup_groups)
    total_dup_records = dup_groups["dup_count"].sum() - total_dup_groups  # Records to delete
    
    # Duplicates with different prices (critical issue)
    price_dups = pd.read_sql("""
        WITH price_duplicates AS (
            SELECT 
                barrio_id,
                anio,
                COUNT(*) as dup_count,
                COUNT(DISTINCT precio_m2_venta) as unique_venta_prices,
                COUNT(DISTINCT precio_mes_alquiler) as unique_alquiler_prices
            FROM fact_precios
            WHERE precio_m2_venta IS NOT NULL OR precio_mes_alquiler IS NOT NULL
            GROUP BY barrio_id, anio
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) as count
        FROM price_duplicates
        WHERE unique_venta_prices > 1 OR unique_alquiler_prices > 1
    """, conn)["count"].iloc[0]
    
    # Source/dataset breakdown
    source_breakdown = pd.read_sql("""
        SELECT 
            source,
            dataset_id,
            COUNT(*) as total_records
        FROM fact_precios
        GROUP BY source, dataset_id
        ORDER BY total_records DESC
    """, conn)
    
    stats = {
        "total_records": total,
        "total_dup_groups": total_dup_groups,
        "total_dup_records": total_dup_records,
        "price_conflicts": price_dups,
        "source_breakdown": source_breakdown,
        "dup_groups": dup_groups,
    }
    
    return stats


def print_analysis(stats: dict) -> None:
    """Imprime el análisis de duplicados."""
    print("=" * 60)
    print("📊 DUPLICATE ANALYSIS RESULTS")
    print("=" * 60)
    print(f"\nTotal records in fact_precios: {stats['total_records']:,}")
    print(f"Duplicate groups (barrio_id + anio): {stats['total_dup_groups']:,}")
    print(f"Duplicate records to remove: {stats['total_dup_records']:,}")
    print(f"⚠️  Groups with conflicting prices: {stats['price_conflicts']:,}")
    
    if stats['total_dup_groups'] > 0:
        print(f"\n📈 Duplicate Statistics:")
        print(f"   Average duplicates per group: {stats['dup_groups']['dup_count'].mean():.2f}")
        print(f"   Max duplicates in single group: {stats['dup_groups']['dup_count'].max()}")
        
        print(f"\n📋 Top 10 Duplicate Groups:")
        top_dups = stats['dup_groups'].head(10)
        for _, row in top_dups.iterrows():
            print(f"   Barrio {row['barrio_id']}, Año {row['anio']}: {row['dup_count']} records "
                  f"(datasets: {row['unique_datasets']}, sources: {row['unique_sources']})")
    
    print(f"\n📦 Source/Dataset Breakdown:")
    for _, row in stats['source_breakdown'].head(10).iterrows():
        print(f"   {row['source']} / {row['dataset_id']}: {row['total_records']:,} records")
    
    print("\n" + "=" * 60)


def preview_deletions(conn: sqlite3.Connection, limit: int = 20) -> pd.DataFrame:
    """
    Muestra un preview de los registros que se eliminarían.
    
    Args:
        conn: Conexión a la base de datos.
        limit: Número de ejemplos a mostrar.
    
    Returns:
        DataFrame con registros a eliminar.
    """
    query = """
    WITH ranked_duplicates AS (
        SELECT 
            p.id,
            p.barrio_id,
            b.barrio_nombre,
            p.anio,
            p.trimestre,
            p.precio_m2_venta,
            p.precio_mes_alquiler,
            p.dataset_id,
            p.source,
            p.etl_loaded_at,
            ROW_NUMBER() OVER (
                PARTITION BY p.barrio_id, p.anio 
                ORDER BY p.etl_loaded_at DESC, p.id DESC
            ) as keep_rank
        FROM fact_precios p
        JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE EXISTS (
            SELECT 1 
            FROM fact_precios p2 
            WHERE p2.barrio_id = p.barrio_id 
              AND p2.anio = p.anio 
              AND p2.id != p.id
        )
    )
    SELECT 
        id,
        barrio_id,
        barrio_nombre,
        anio,
        trimestre,
        precio_m2_venta,
        precio_mes_alquiler,
        dataset_id,
        source,
        etl_loaded_at,
        CASE 
            WHEN keep_rank = 1 THEN 'KEEP'
            ELSE 'DELETE'
        END as action
    FROM ranked_duplicates
    WHERE keep_rank > 1
    ORDER BY barrio_id, anio, keep_rank
    LIMIT ?
    """
    
    return pd.read_sql(query, conn, params=[limit])


def clean_duplicates(conn: sqlite3.Connection, dry_run: bool = True) -> int:
    """
    Elimina duplicados de fact_precios.
    
    Args:
        conn: Conexión a la base de datos.
        dry_run: Si True, solo muestra lo que se haría sin eliminar.
    
    Returns:
        Número de registros eliminados (o que se eliminarían).
    """
    if dry_run:
        print("\n🔍 DRY RUN MODE - No records will be deleted\n")
    else:
        print("\n⚠️  DELETION MODE - Records will be permanently deleted\n")
    
    # Count records to delete
    count_query = """
    WITH ranked_duplicates AS (
        SELECT 
            id,
            ROW_NUMBER() OVER (
                PARTITION BY barrio_id, anio 
                ORDER BY etl_loaded_at DESC, id DESC
            ) as keep_rank
        FROM fact_precios
        WHERE EXISTS (
            SELECT 1 
            FROM fact_precios p2 
            WHERE p2.barrio_id = fact_precios.barrio_id 
              AND p2.anio = fact_precios.anio 
              AND p2.id != fact_precios.id
        )
    )
    SELECT COUNT(*) as count
    FROM ranked_duplicates
    WHERE keep_rank > 1
    """
    
    count = pd.read_sql(count_query, conn)["count"].iloc[0]
    
    if count == 0:
        print("✅ No duplicates found. Database is clean!")
        return 0
    
    print(f"📊 Would delete {count:,} duplicate records")
    
    if not dry_run:
        # Create backup
        backup_table = f"fact_precios_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💾 Creating backup table: {backup_table}")
        conn.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM fact_precios")
        conn.commit()
        print(f"✅ Backup created with {pd.read_sql(f'SELECT COUNT(*) as n FROM {backup_table}', conn)['n'].iloc[0]:,} records")
        
        # Delete duplicates
        delete_query = """
        DELETE FROM fact_precios
        WHERE id IN (
            WITH ranked_duplicates AS (
                SELECT 
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY barrio_id, anio 
                        ORDER BY etl_loaded_at DESC, id DESC
                    ) as keep_rank
                FROM fact_precios
                WHERE EXISTS (
                    SELECT 1 
                    FROM fact_precios p2 
                    WHERE p2.barrio_id = fact_precios.barrio_id 
                      AND p2.anio = fact_precios.anio 
                      AND p2.id != fact_precios.id
                )
            )
            SELECT id FROM ranked_duplicates WHERE keep_rank > 1
        )
        """
        
        cursor = conn.execute(delete_query)
        conn.commit()
        deleted = cursor.rowcount
        print(f"✅ Deleted {deleted:,} duplicate records")
        
        # Verify
        remaining_dups = pd.read_sql("""
            SELECT barrio_id, anio, COUNT(*) as count
            FROM fact_precios
            GROUP BY barrio_id, anio
            HAVING COUNT(*) > 1
        """, conn)
        
        if len(remaining_dups) == 0:
            print("✅ Verification: No duplicates remain")
        else:
            print(f"⚠️  Warning: {len(remaining_dups)} duplicate groups still exist")
        
        return deleted
    else:
        return count


def main() -> int:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Analyze and clean duplicates in fact_precios"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Actually delete duplicates (creates backup first)"
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=20,
        help="Number of deletion examples to preview (default: 20)"
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
        # Analyze
        stats = analyze_duplicates(conn)
        print_analysis(stats)
        
        # Preview deletions
        if stats['total_dup_records'] > 0:
            print(f"\n📋 Preview of records to delete (showing {args.preview}):")
            print("-" * 60)
            preview = preview_deletions(conn, limit=args.preview)
            print(preview.to_string(index=False))
            print("-" * 60)
        
        # Clean if requested
        if args.clean:
            if stats['total_dup_records'] == 0:
                print("\n✅ No duplicates to clean")
                return 0
            
            response = input(f"\n⚠️  Are you sure you want to delete {stats['total_dup_records']:,} duplicate records? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Cancelled")
                return 1
            
            deleted = clean_duplicates(conn, dry_run=False)
            print(f"\n✅ Cleanup complete: {deleted:,} records deleted")
        else:
            print(f"\n💡 To actually delete duplicates, run with --clean flag")
            print(f"   python3 scripts/analyze_and_clean_duplicates.py --clean")
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
