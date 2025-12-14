#!/usr/bin/env python3
"""
Validation script for fact_renta table backfill.

This script validates the IDESCAT income data loaded into fact_renta,
checking coverage, completeness, and data quality.
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Connect to the SQLite database."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def get_coverage_by_year(conn: sqlite3.Connection) -> List[Dict]:
    """Get coverage statistics by year as specified in the task requirements."""
    query = """
        SELECT anio, 
               COUNT(DISTINCT barrio_id) as barrios_con_datos,
               ROUND(COUNT(DISTINCT barrio_id) * 100.0 / 73, 1) as cobertura_pct
        FROM fact_renta 
        GROUP BY anio 
        ORDER BY anio;
    """
    cursor = conn.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def get_total_records(conn: sqlite3.Connection) -> int:
    """Get total number of records in fact_renta."""
    cursor = conn.execute("SELECT COUNT(*) as count FROM fact_renta;")
    return cursor.fetchone()["count"]


def check_null_values(conn: sqlite3.Connection) -> Dict[str, int]:
    """Check for NULL values in critical columns."""
    query = """
        SELECT 
            SUM(CASE WHEN barrio_id IS NULL THEN 1 ELSE 0 END) as barrio_id_nulls,
            SUM(CASE WHEN anio IS NULL THEN 1 ELSE 0 END) as anio_nulls,
            SUM(CASE WHEN renta_euros IS NULL THEN 1 ELSE 0 END) as renta_euros_nulls,
            COUNT(*) as total_records
        FROM fact_renta;
    """
    cursor = conn.execute(query)
    return dict(cursor.fetchone())


def check_foreign_key_integrity(conn: sqlite3.Connection) -> Tuple[int, int]:
    """Check foreign key integrity: all barrio_ids should exist in dim_barrios."""
    query = """
        SELECT COUNT(*) as orphaned
        FROM fact_renta fr
        LEFT JOIN dim_barrios db ON fr.barrio_id = db.barrio_id
        WHERE db.barrio_id IS NULL;
    """
    cursor = conn.execute(query)
    orphaned = cursor.fetchone()["orphaned"]
    
    total_query = "SELECT COUNT(*) as total FROM fact_renta;"
    total = conn.execute(total_query).fetchone()["total"]
    
    return orphaned, total


def get_source_distribution(conn: sqlite3.Connection) -> List[Dict]:
    """Get distribution of records by source."""
    query = """
        SELECT source, 
               COUNT(*) as records,
               COUNT(DISTINCT barrio_id) as barrios,
               MIN(anio) as min_year,
               MAX(anio) as max_year
        FROM fact_renta
        GROUP BY source
        ORDER BY source;
    """
    cursor = conn.execute(query)
    return [dict(row) for row in cursor.fetchall()]


def run_validations(db_path: Path) -> Tuple[bool, str]:
    """
    Run all validations and return (success, report).
    
    Returns:
        Tuple of (all_validations_passed, report_text)
    """
    conn = connect_db(db_path)
    report_lines = []
    all_passed = True
    
    # Header
    timestamp = datetime.now().isoformat()
    report_lines.append("=" * 80)
    report_lines.append("FACT_RENTA BACKFILL VALIDATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append(f"Database: {db_path}")
    report_lines.append("")
    
    # Total records
    total_records = get_total_records(conn)
    report_lines.append(f"Total Records in fact_renta: {total_records}")
    report_lines.append("")
    
    # Coverage by year (SQL verification query from task)
    report_lines.append("COVERAGE BY YEAR")
    report_lines.append("-" * 80)
    coverage_data = get_coverage_by_year(conn)
    report_lines.append(f"{'Year':<8} {'Barrios':<15} {'Coverage %':<12}")
    report_lines.append("-" * 80)
    
    for row in coverage_data:
        report_lines.append(
            f"{row['anio']:<8} {row['barrios_con_datos']:<15} {row['cobertura_pct']:<12}"
        )
    report_lines.append("")
    
    # DQC: Completeness for 2018-2022 (≥95% requirement)
    report_lines.append("DATA QUALITY CHECK: Completeness (2018-2022)")
    report_lines.append("-" * 80)
    
    critical_years = {2018, 2019, 2020, 2021, 2022}
    completeness_passed = True
    
    for row in coverage_data:
        year = row["anio"]
        if year in critical_years:
            coverage = row["cobertura_pct"]
            status = "✓ PASS" if coverage >= 95.0 else "✗ FAIL"
            if coverage < 95.0:
                completeness_passed = False
                all_passed = False
            report_lines.append(f"  {year}: {coverage}% - {status}")
    
    if completeness_passed:
        report_lines.append("✓ Completeness Check: PASSED (all years 2018-2022 have ≥95% coverage)")
    else:
        report_lines.append("✗ Completeness Check: FAILED (some years below 95% threshold)")
    report_lines.append("")
    
    # DQC: NULL value checks
    report_lines.append("DATA QUALITY CHECK: NULL Values")
    report_lines.append("-" * 80)
    null_stats = check_null_values(conn)
    
    null_checks_passed = True
    if null_stats["barrio_id_nulls"] > 0:
        report_lines.append(f"✗ FAIL: {null_stats['barrio_id_nulls']} NULL barrio_id values found")
        null_checks_passed = False
        all_passed = False
    else:
        report_lines.append("✓ PASS: No NULL values in barrio_id")
    
    if null_stats["anio_nulls"] > 0:
        report_lines.append(f"✗ FAIL: {null_stats['anio_nulls']} NULL anio values found")
        null_checks_passed = False
        all_passed = False
    else:
        report_lines.append("✓ PASS: No NULL values in anio")
    
    if null_stats["renta_euros_nulls"] > 0:
        report_lines.append(f"✗ FAIL: {null_stats['renta_euros_nulls']} NULL renta_euros values found")
        null_checks_passed = False
        all_passed = False
    else:
        report_lines.append("✓ PASS: No NULL values in renta_euros")
    
    if null_checks_passed:
        report_lines.append("✓ NULL Value Check: PASSED")
    else:
        report_lines.append("✗ NULL Value Check: FAILED")
    report_lines.append("")
    
    # DQC: Foreign key integrity
    report_lines.append("DATA QUALITY CHECK: Foreign Key Integrity")
    report_lines.append("-" * 80)
    orphaned, total = check_foreign_key_integrity(conn)
    
    if orphaned > 0:
        report_lines.append(f"✗ FAIL: {orphaned} out of {total} records have invalid barrio_id")
        all_passed = False
    else:
        report_lines.append(f"✓ PASS: All {total} records have valid barrio_id references")
    report_lines.append("")
    
    # Source distribution
    report_lines.append("SOURCE DISTRIBUTION")
    report_lines.append("-" * 80)
    source_data = get_source_distribution(conn)
    
    for source_row in source_data:
        report_lines.append(
            f"Source: {source_row['source']}\n"
            f"  Records: {source_row['records']}\n"
            f"  Barrios: {source_row['barrios']}\n"
            f"  Year Range: {source_row['min_year']}-{source_row['max_year']}"
        )
    report_lines.append("")
    
    # Summary
    report_lines.append("=" * 80)
    if all_passed:
        report_lines.append("✓ ALL VALIDATIONS PASSED")
    else:
        report_lines.append("✗ SOME VALIDATIONS FAILED - REVIEW REQUIRED")
    report_lines.append("=" * 80)
    
    conn.close()
    
    return all_passed, "\n".join(report_lines)


def main() -> int:
    """Main entry point."""
    # Default database path
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    
    print(f"Validating fact_renta table in: {db_path}")
    print()
    
    try:
        all_passed, report = run_validations(db_path)
        
        # Print report to console
        print(report)
        print()
        
        # Save report to file
        report_dir = PROJECT_ROOT / "data" / "logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "fact_renta_backfill.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Report saved to: {report_path}")
        
        # Exit with appropriate code
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
