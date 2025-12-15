#!/usr/bin/env python3
"""
Validation script for barrio_structural_attributes.csv.

Performs data quality checks and generates validation report.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_structural_attributes(csv_path: Path) -> pd.DataFrame:
    """Load the structural attributes CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Structural attributes file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} neighborhoods from {csv_path.name}")
    return df


def check_coverage() -> Dict:
    """Check that all 73 neighborhoods are present."""
    expected_count = 73
    csv_path = PROJECT_ROOT / "data" / "raw" / "barrio_structural_attributes.csv"
    
    df = load_structural_attributes(csv_path)
    actual_count = len(df)
    
    passed = actual_count == expected_count
    
    return {
        "name": "Coverage Check",
        "passed": passed,
        "expected": expected_count,
        "actual": actual_count,
        "message": f"{'✓ PASS' if passed else '✗ FAIL'}: {actual_count} neighborhoods (expected {expected_count})"
    }


def check_null_values(df: pd.DataFrame) -> Dict:
    """Check for NULL values in critical columns."""
    critical_cols = [
        "barrio_id",
        "anyo_construccion_promedio",
        "antiguedad_anos",
        "num_edificios"
    ]
    
    null_counts = {}
    for col in critical_cols:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_counts[col] = null_count
    
    total_nulls = sum(null_counts.values())
    passed = total_nulls == 0
    
    return {
        "name": "NULL Value Check",
        "passed": passed,
        "null_counts": null_counts,
        "message": f"{'✓ PASS' if passed else '✗ FAIL'}: {total_nulls} NULL values found in critical columns"
    }


def check_value_ranges(df: pd.DataFrame) -> Dict:
    """Check that values are within reasonable ranges."""
    checks = []
    
    # Construction year should be between 1800 and 2025
    year_col = "anyo_construccion_promedio"
    if year_col in df.columns:
        min_year = df[year_col].min()
        max_year = df[year_col].max()
        year_valid = (min_year >= 1800 and max_year <= 2025)
        checks.append({
            "field": year_col,
            "valid": year_valid,
            "range": f"{min_year:.1f} - {max_year:.1f}",
            "expected": "1800-2025"
        })
    
    # Age should be positive
    age_col = "antiguedad_anos"
    if age_col in df.columns:
        min_age = df[age_col].min()
        max_age = df[age_col].max()
        age_valid = (min_age >= 0 and max_age <= 225)  # Max age ~225 years
        checks.append({
            "field": age_col,
            "valid": age_valid,
            "range": f"{min_age:.1f} - {max_age:.1f}",
            "expected": "0-225 years"
        })
    
    # Number of buildings should be positive
    count_col = "num_edificios"
    if count_col in df.columns:
        min_count = df[count_col].min()
        max_count = df[count_col].max()
        count_valid = (min_count > 0)
        checks.append({
            "field": count_col,
            "valid": count_valid,
            "range": f"{min_count:.0f} - {max_count:.0f}",
            "expected": "> 0"
        })
    
    passed = all(check["valid"] for check in checks)
    
    return {
        "name": "Value Range Check",
        "passed": passed,
        "checks": checks,
        "message": f"{'✓ PASS' if passed else '✗ FAIL'}: All values within expected ranges"
    }


def check_barrio_id_compatibility() -> Dict:
    """Check that barrio_ids match dim_barrios."""
    import sqlite3
    
    csv_path = PROJECT_ROOT / "data" / "raw" / "barrio_structural_attributes.csv"
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    df = load_structural_attributes(csv_path)
    csv_ids = set(df["barrio_id"].unique())
    
    if not db_path.exists():
        return {
            "name": "barrio_id Compatibility",
            "passed": None,
            "message": "⚠ SKIP: Database not found, cannot verify compatibility"
        }
    
    conn = sqlite3.connect(db_path)
    db_ids_df = pd.read_sql_query("SELECT DISTINCT barrio_id FROM dim_barrios", conn)
    conn.close()
    
    db_ids = set(db_ids_df["barrio_id"].unique())
    
    missing_in_csv = db_ids - csv_ids
    extra_in_csv = csv_ids - db_ids
    
    passed = len(missing_in_csv) == 0 and len(extra_in_csv) == 0
    
    details = []
    if missing_in_csv:
        details.append(f"Missing from CSV: {sorted(missing_in_csv)}")
    if extra_in_csv:
        details.append(f"Extra in CSV: {sorted(extra_in_csv)}")
    
    return {
        "name": "barrio_id Compatibility",
        "passed": passed,
        "csv_ids": len(csv_ids),
        "db_ids": len(db_ids),
        "details": details,
        "message": f"{'✓ PASS' if passed else '✗ FAIL'}: barrio_id compatibility with dim_barrios"
    }


def generate_summary_statistics(df: pd.DataFrame) -> Dict:
    """Generate summary statistics for the report."""
    stats = {}
    
    numeric_cols = [
        "anyo_construccion_promedio",
        "antiguedad_anos",
        "num_edificios",
        "pct_edificios_pre1950"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            stats[col] = {
                "mean": df[col].mean(),
                "median": df[col].median(),
                "min": df[col].min(),
                "max": df[col].max(),
                "std": df[col].std()
            }
    
    return stats


def run_all_validations() -> tuple[bool, str]:
    """Run all validations and return (passed, report)."""
    csv_path = PROJECT_ROOT / "data" / "raw" / "barrio_structural_attributes.csv"
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("STRUCTURAL ATTRIBUTES VALIDATION REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    report_lines.append(f"File: {csv_path}")
    report_lines.append("")
    
    # Load data
    try:
        df = load_structural_attributes(csv_path)
    except Exception as e:
        return False, f"ERROR: Could not load file: {e}"
    
    # Run checks
    checks = [
        check_coverage(),
        check_null_values(df),
        check_value_ranges(df),
        check_barrio_id_compatibility(),
    ]
    
    all_passed = all(
        check["passed"] for check in checks if check["passed"] is not None
    )
    
    # Report checks
    report_lines.append("VALIDATION CHECKS")
    report_lines.append("-" * 80)
    
    for check in checks:
        report_lines.append(f"\n{check['name']}")
        report_lines.append(f"  {check['message']}")
        
        if "details" in check and check["details"]:
            for detail in check["details"]:
                report_lines.append(f"    {detail}")
        
        if "checks" in check:
            for subcheck in check["checks"]:
                status = "✓" if subcheck["valid"] else "✗"
                report_lines.append(
                    f"    {status} {subcheck['field']}: {subcheck['range']} (expected: {subcheck['expected']})"
                )
    
    report_lines.append("")
    
    # Summary statistics
    report_lines.append("SUMMARY STATISTICS")
    report_lines.append("-" * 80)
    
    stats = generate_summary_statistics(df)
    for col, values in stats.items():
        report_lines.append(f"\n{col}:")
        report_lines.append(f"  Mean:   {values['mean']:.2f}")
        report_lines.append(f"  Median: {values['median']:.2f}")
        report_lines.append(f"  Range:  {values['min']:.2f} - {values['max']:.2f}")
        report_lines.append(f"  Std Dev:{values['std']:.2f}")
    
    # Top/Bottom neighborhoods
    report_lines.append("")
    report_lines.append("NOTABLE NEIGHBORHOODS")
    report_lines.append("-" * 80)
    
    report_lines.append("\n5 Oldest Neighborhoods (by avg construction year):")
    oldest = df.nsmallest(5, "anyo_construccion_promedio")[["barrio_nombre", "anyo_construccion_promedio", "antiguedad_anos"]]
    for _, row in oldest.iterrows():
        report_lines.append(f"  - {row['barrio_nombre']}: {row['anyo_construccion_promedio']:.1f} ({row['antiguedad_anos']:.1f} years old)")
    
    report_lines.append("\n5 Newest Neighborhoods (by avg construction year):")
    newest = df.nlargest(5, "anyo_construccion_promedio")[["barrio_nombre", "anyo_construccion_promedio", "antiguedad_anos"]]
    for _, row in newest.iterrows():
        report_lines.append(f"  - {row['barrio_nombre']}: {row['anyo_construccion_promedio']:.1f} ({row['antiguedad_anos']:.1f} years old)")
    
    # Final result
    report_lines.append("")
    report_lines.append("=" * 80)
    if all_passed:
        report_lines.append("✓ ALL VALIDATIONS PASSED")
    else:
        report_lines.append("✗ SOME VALIDATIONS FAILED - REVIEW REQUIRED")
    report_lines.append("=" * 80)
    
    return all_passed, "\n".join(report_lines)


def main() -> int:
    """Main entry point."""
    csv_path = PROJECT_ROOT / "data" / "raw" / "barrio_structural_attributes.csv"
    
    print(f"Validating structural attributes: {csv_path}")
    print()
    
    try:
        all_passed, report = run_all_validations()
        
        # Print report
        print(report)
        print()
        
        # Save report
        report_dir = PROJECT_ROOT / "data" / "logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "structural_attributes_validation.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"Report saved to: {report_path}")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
