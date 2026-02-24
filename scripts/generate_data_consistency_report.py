#!/usr/bin/env python3
"""
Genera un reporte de consistencia de datos de la base de datos.

Analiza:
- Métricas faltantes (valores nulos por columna)
- Inconsistencia de años (gaps temporales, cobertura por año)
- Cobertura de barrios por tabla y año
- Consistencia cruzada entre tablas

Uso:
    python scripts/generate_data_consistency_report.py
    python scripts/generate_data_consistency_report.py --db-path data/processed/database.db --output reports/
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Añadir root del proyecto al path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Abre conexión a SQLite."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_existing_tables(conn: sqlite3.Connection, prefix: str = "fact_") -> List[str]:
    """Obtiene tablas existentes que coinciden con el prefijo."""
    df = pd.read_sql(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE ?
        ORDER BY name
        """,
        conn,
        params=(f"{prefix}%",),
    )
    return df["name"].tolist()


def get_year_column(conn: sqlite3.Connection, table: str) -> Optional[str]:
    """Devuelve el nombre de la columna de año (anio o year) o None."""
    df = pd.read_sql(f"PRAGMA table_info({table})", conn)
    cols = [c for c in df["name"].tolist()]
    return "anio" if "anio" in cols else ("year" if "year" in cols else None)


def table_has_year_column(conn: sqlite3.Connection, table: str) -> bool:
    """Verifica si la tabla tiene columna anio o year."""
    return get_year_column(conn, table) is not None


def table_has_barrio_column(conn: sqlite3.Connection, table: str) -> bool:
    """Verifica si la tabla tiene columna barrio_id."""
    df = pd.read_sql(f"PRAGMA table_info({table})", conn)
    return "barrio_id" in df["name"].tolist()


def analyze_year_coverage(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """Analiza cobertura temporal por tabla."""
    tables = get_existing_tables(conn)
    result = {}

    for table in tables:
        try:
            year_col = get_year_column(conn, table)
            if not year_col:
                continue

            barrio_select = "COUNT(DISTINCT barrio_id) as barrios" if table_has_barrio_column(conn, table) else "COUNT(*) as barrios"

            df = pd.read_sql(
                f"""
                SELECT {year_col}, COUNT(*) as registros, {barrio_select}
                FROM {table}
                WHERE {year_col} IS NOT NULL
                GROUP BY {year_col}
                ORDER BY {year_col}
                """,
                conn,
            )

            if df.empty:
                continue

            min_year = int(df[year_col].min())
            max_year = int(df[year_col].max())
            expected_years = set(range(min_year, max_year + 1))
            actual_years = set(df[year_col].astype(int).tolist())
            missing_years = sorted(expected_years - actual_years)

            # Coeficiente de variación en registros por año
            counts = df["registros"].tolist()
            avg_count = sum(counts) / len(counts) if counts else 0
            var_count = sum((c - avg_count) ** 2 for c in counts) / len(counts) if counts else 0
            std_count = var_count ** 0.5
            cv = (std_count / avg_count * 100) if avg_count > 0 else 0

            result[table] = {
                "min_year": min_year,
                "max_year": max_year,
                "years_span": max_year - min_year + 1,
                "years_with_data": len(actual_years),
                "missing_years": missing_years,
                "total_records": int(df["registros"].sum()),
                "avg_records_per_year": round(avg_count, 1),
                "std_records_per_year": round(std_count, 1),
                "cv_percent": round(cv, 1),
                "barrios_per_year": df.set_index(year_col)["barrios"].to_dict(),
            }
        except Exception as e:
            result[table] = {"error": str(e)}

    return result


def analyze_missing_metrics(conn: sqlite3.Connection) -> Dict[str, Dict[str, Any]]:
    """Analiza valores nulos (métricas faltantes) por tabla y columna."""
    tables = get_existing_tables(conn)
    result = {}

    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            if df.empty:
                result[table] = {"total_rows": 0, "columns": {}}
                continue

            total = len(df)
            null_pct = (df.isnull().sum() / total * 100).round(2)
            null_pct = null_pct[null_pct > 0].sort_values(ascending=False)

            problematic = {col: float(pct) for col, pct in null_pct.items() if pct > 5}
            result[table] = {
                "total_rows": total,
                "columns": problematic,
                "completeness_pct": round(100 - null_pct.mean(), 2) if len(null_pct) > 0 else 100,
            }
        except Exception as e:
            result[table] = {"error": str(e)}

    return result


def analyze_cross_table_consistency(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analiza consistencia entre tablas (barrios presentes en todas)."""
    key_tables = ["fact_precios", "fact_demografia_ampliada", "fact_renta"]
    tables = get_existing_tables(conn)
    available = [t for t in key_tables if t in tables]

    barrio_sets: Dict[str, Set[int]] = {}
    for table in available:
        try:
            df = pd.read_sql(
                f"SELECT DISTINCT barrio_id FROM {table} WHERE barrio_id IS NOT NULL",
                conn,
            )
            barrio_sets[table] = set(df["barrio_id"].astype(int).tolist())
        except Exception:
            barrio_sets[table] = set()

    if not barrio_sets:
        return {"common_barrios": 0, "all_barrios": 0, "consistency_pct": 0, "details": {}}

    common = set.intersection(*barrio_sets.values())
    all_barrios = set.union(*barrio_sets.values())
    consistency = (len(common) / len(all_barrios) * 100) if all_barrios else 0

    details = {"common": len(common), "union": len(all_barrios)}
    for t, s in barrio_sets.items():
        details[t] = len(s)

    return {
        "common_barrios": len(common),
        "all_barrios": len(all_barrios),
        "consistency_pct": round(consistency, 2),
        "details": details,
        "tables_checked": available,
    }


def analyze_year_barrio_matrix(conn: sqlite3.Connection) -> pd.DataFrame:
    """Matriz año-tabla: qué tablas tienen datos para cada año."""
    year_data = analyze_year_coverage(conn)
    if not year_data:
        return pd.DataFrame()

    all_years = set()
    for v in year_data.values():
        if "error" not in v:
            all_years.update(range(v["min_year"], v["max_year"] + 1))

    rows = []
    for year in sorted(all_years):
        row = {"año": year}
        for table, data in year_data.items():
            if "error" in data:
                continue
            if year in range(data["min_year"], data["max_year"] + 1):
                barrios = data.get("barrios_per_year", {})
                n_barrios = barrios.get(year, "?")
                row[table] = n_barrios if n_barrios != "?" else "✓"
            else:
                row[table] = "—"
        rows.append(row)

    return pd.DataFrame(rows)


def generate_markdown_report(
    year_coverage: Dict,
    missing_metrics: Dict,
    cross_consistency: Dict,
    db_path: Path,
    output_path: Path,
) -> str:
    """Genera el reporte en Markdown."""
    lines = [
        "# Reporte de Consistencia de Datos",
        "",
        f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Base de datos**: `{db_path}`",
        "",
        "---",
        "",
        "## 1. Resumen Ejecutivo",
        "",
    ]

    # Resumen
    n_tables = len([t for t in year_coverage if "error" not in year_coverage[t]])
    tables_with_gaps = sum(
        1 for t, d in year_coverage.items() if "error" not in d and d.get("missing_years")
    )
    tables_high_null = sum(
        1
        for t, d in missing_metrics.items()
        if "error" not in d and d.get("completeness_pct", 100) < 90
    )

    lines.extend(
        [
            f"- **Tablas con datos temporales**: {n_tables}",
            f"- **Tablas con gaps de años**: {tables_with_gaps}",
            f"- **Tablas con >10% nulos**: {tables_high_null}",
            f"- **Consistencia cruzada (barrios)**: {cross_consistency.get('consistency_pct', 0)}%",
            "",
            "---",
            "",
            "## 2. Inconsistencia de Años (Gaps Temporales)",
            "",
            "| Tabla | Min | Max | Años con datos | Gaps | CV% |",
            "|-------|-----|-----|----------------|------|-----|",
        ]
    )

    for table in sorted(year_coverage.keys()):
        d = year_coverage[table]
        if "error" in d:
            lines.append(f"| {table} | — | — | Error | {d['error'][:30]}... |")
            continue
        gaps = d.get("missing_years", [])
        gaps_str = ", ".join(map(str, gaps[:5])) + ("..." if len(gaps) > 5 else "") if gaps else "✓"
        lines.append(
            f"| {table} | {d['min_year']} | {d['max_year']} | "
            f"{d['years_with_data']}/{d['years_span']} | {gaps_str} | {d.get('cv_percent', 0)} |"
        )

    lines.extend(
        [
            "",
            "**Leyenda**: CV% = Coeficiente de variación en registros/año (alto = inconsistencia).",
            "",
            "---",
            "",
            "## 3. Métricas Faltantes (Valores Nulos >5%)",
            "",
        ]
    )

    has_missing = False
    for table in sorted(missing_metrics.keys()):
        d = missing_metrics[table]
        if "error" in d:
            lines.append(f"### {table}\n\nError: {d['error']}\n")
            continue
        cols = d.get("columns", {})
        if not cols:
            continue
        has_missing = True
        lines.append(f"### {table} ({d.get('total_rows', 0):,} filas)")
        lines.append("")
        lines.append("| Columna | % Nulos |")
        lines.append("|---------|--------|")
        for col, pct in sorted(cols.items(), key=lambda x: x[1], reverse=True)[:15]:
            lines.append(f"| {col} | {pct:.1f}% |")
        if len(cols) > 15:
            lines.append(f"| ... | {len(cols) - 15} columnas más |")
        lines.append("")

    if not has_missing:
        lines.append("No se detectaron columnas con más de 5% de valores nulos.\n")

    lines.extend(
        [
            "---",
            "",
            "## 4. Consistencia Cruzada (Barrios)",
            "",
            "Mide el solapamiento de barrios entre `fact_precios`, `fact_demografia_ampliada` y `fact_renta`.",
            "",
        ]
    )

    cc = cross_consistency
    lines.append(f"- **Barrios en todas las tablas**: {cc.get('common_barrios', 0)}")
    lines.append(f"- **Barrios en al menos una**: {cc.get('all_barrios', 0)}")
    lines.append(f"- **Consistencia**: {cc.get('consistency_pct', 0)}%")
    lines.append("")
    if cc.get("details"):
        lines.append("| Tabla | Barrios únicos |")
        lines.append("|-------|----------------|")
        for t in cc.get("tables_checked", []):
            lines.append(f"| {t} | {cc['details'].get(t, 0)} |")
    lines.append("")

    # Inconsistencias entre tablas (rangos de años no alineados)
    key_tables_years = {}
    for t in ["fact_precios", "fact_demografia_ampliada", "fact_renta", "fact_demografia"]:
        if t in year_coverage and "error" not in year_coverage[t]:
            key_tables_years[t] = (
                year_coverage[t]["min_year"],
                year_coverage[t]["max_year"],
            )

    if key_tables_years:
        lines.extend(
            [
                "---",
                "",
                "## 5. Inconsistencias de Rango entre Tablas Clave",
                "",
                "Rangos de años disponibles por tabla (para cruces barrio-año):",
                "",
                "| Tabla | Año min | Año max | Años comunes con fact_precios |",
                "|-------|---------|---------|--------------------------------|",
            ]
        )
        precios_range = key_tables_years.get("fact_precios", (None, None))
        precios_years = set(range(precios_range[0], precios_range[1] + 1)) if precios_range[0] else set()
        for t in ["fact_precios", "fact_demografia_ampliada", "fact_renta", "fact_demografia"]:
            if t not in key_tables_years:
                continue
            mn, mx = key_tables_years[t]
            other_years = set(range(mn, mx + 1))
            common = len(precios_years & other_years)
            lines.append(f"| {t} | {mn} | {mx} | {common} |")
        lines.extend(
            [
                "",
                "**Nota**: Para análisis multivariable (precio + renta + demografía), usar solo años presentes en todas las tablas.",
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## 6. Cobertura por Año (Barrios)",
        ]
    )
    lines.extend(
        [
            "",
            "Número de barrios con datos por tabla y año en tablas clave.",
            "",
        ]
    )

    # Tabla resumida por año para tablas principales
    key_tables = ["fact_precios", "fact_demografia_ampliada", "fact_renta"]
    for table in key_tables:
        if table not in year_coverage or "error" in year_coverage[table]:
            continue
        d = year_coverage[table]
        bp = d.get("barrios_per_year", {})
        if not bp:
            continue
        lines.append(f"### {table}")
        lines.append("")
        lines.append("| Año | Barrios |")
        lines.append("|-----|---------|")
        for yr in sorted(bp.keys()):
            lines.append(f"| {yr} | {bp[yr]} |")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 7. Recomendaciones",
            "",
        ]
    )

    recs = []
    if tables_with_gaps > 0:
        recs.append("- Completar años faltantes en las tablas con gaps temporales.")
    if tables_high_null > 0:
        recs.append("- Revisar y documentar columnas con alta proporción de nulos.")
    if cross_consistency.get("consistency_pct", 100) < 100:
        recs.append("- Investigar barrios presentes en unas tablas pero no en otras.")
    # Recomendación por rangos desalineados
    if key_tables_years:
        renta_max = key_tables_years.get("fact_renta", (None, None))[1]
        precios_max = key_tables_years.get("fact_precios", (None, None))[1]
        if renta_max and precios_max and renta_max < precios_max:
            recs.append(
                f"- fact_renta termina en {renta_max} mientras fact_precios llega a {precios_max}. "
                "Actualizar renta para análisis recientes."
            )
        demo_amp = key_tables_years.get("fact_demografia_ampliada", (None, None))
        if demo_amp[0] == demo_amp[1] and demo_amp[0]:
            recs.append(
                f"- fact_demografia_ampliada solo tiene año {demo_amp[0]}. "
                "Considerar poblar años históricos para análisis multivariable."
            )
    if not recs:
        recs.append("- La base de datos presenta buena consistencia general.")
    lines.extend([r + "\n" for r in recs])

    return "\n".join(lines)


def main() -> int:
    """Punto de entrada."""
    parser = argparse.ArgumentParser(description="Genera reporte de consistencia de datos.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--output-name", type=str, default="DATA_CONSISTENCY_REPORT.md")
    args = parser.parse_args()

    if not args.db_path.exists():
        print(f"❌ Base de datos no encontrada: {args.db_path}")
        return 1

    args.output.mkdir(parents=True, exist_ok=True)
    output_file = args.output / args.output_name

    print("📊 Analizando base de datos...")
    conn = get_connection(args.db_path)

    try:
        year_coverage = analyze_year_coverage(conn)
        print(f"   ✓ Cobertura temporal: {len(year_coverage)} tablas")

        missing_metrics = analyze_missing_metrics(conn)
        print(f"   ✓ Métricas faltantes: {len(missing_metrics)} tablas")

        cross_consistency = analyze_cross_table_consistency(conn)
        print(f"   ✓ Consistencia cruzada: {cross_consistency.get('consistency_pct', 0)}%")

        report = generate_markdown_report(
            year_coverage, missing_metrics, cross_consistency, args.db_path, output_file
        )

        output_file.write_text(report, encoding="utf-8")
        print(f"\n✅ Reporte generado: {output_file}")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
