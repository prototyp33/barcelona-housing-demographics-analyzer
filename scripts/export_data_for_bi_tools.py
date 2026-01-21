#!/usr/bin/env python3
"""
Exporta CSVs "BI-ready" desde SQLite para Power BI / Looker / Tableau.

Objetivo:
    - Evitar que Power BI/Looker/Tableau tengan que hacer joins complejos o SQL pesado.
    - Exportar vistas estables (grano anual y mensual) + dimensiones.

Salida por defecto:
    data/exports/bi/
      ├── 01_dimensions/
      ├── 02_housing_yearly/
      ├── 03_housing_monthly/
      ├── 04_economy_yearly/
      └── README.md

Uso:
    ./myenv/bin/python scripts/export_data_for_bi_tools.py
    ./myenv/bin/python scripts/export_data_for_bi_tools.py --db-path data/processed/database.db --out-dir data/exports/bi
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


logger = logging.getLogger(__name__)


DEFAULT_DB_PATH = Path("data") / "processed" / "database.db"
DEFAULT_OUT_DIR = Path("data") / "exports" / "bi"


TABLE_CATEGORIES: Dict[str, List[str]] = {
    # Modelo estrella estricto (recomendado para Power BI / Tableau / Looker)
    "00_star_schema": [
        "v_dim_barrios_star",
        "v_dim_tiempo_star",
        "v_fact_housing_anual_star",
        "v_fact_alquiler_mensual_star",
    ],
    "01_dimensions": [
        "dim_barrios",
        "dim_tiempo",
    ],
    # Hechos/vistas anuales "ready-to-use" (recomendado para la mayoría de dashboards)
    "02_housing_yearly": [
        "v_metricas_housing",
        "v_precios_anual",
        "v_alquiler_anual",
    ],
    # Series mensuales (para time-series y análisis de estacionalidad)
    "03_housing_monthly": [
        "v_alquiler_mensual",
    ],
    # Capa económica consolidada (correlaciones / análisis multivariable)
    "04_economy_yearly": [
        "v_economia_consolidada",
        "v_correlaciones_cruzadas",
    ],
}


def setup_logging(level: str) -> None:
    """Configura logging."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def connect_sqlite(db_path: Path) -> sqlite3.Connection:
    """
    Abre conexión a SQLite con pragmas razonables para lecturas.

    Args:
        db_path: Ruta a la base de datos.

    Returns:
        Conexión sqlite3.
    """
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def object_exists(conn: sqlite3.Connection, name: str) -> bool:
    """
    Verifica si existe tabla o vista en SQLite.

    Args:
        conn: Conexión sqlite3.
        name: Nombre de tabla/vista.

    Returns:
        True si existe, False si no.
    """
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE (type = 'table' OR type = 'view') AND name = ? LIMIT 1;",
        (name,),
    )
    return cur.fetchone() is not None


def export_query_to_csv(
    conn: sqlite3.Connection,
    name: str,
    output_path: Path,
    encoding: str,
) -> int:
    """
    Exporta una tabla/vista completa a CSV.

    Args:
        conn: Conexión sqlite3.
        name: Tabla o vista.
        output_path: Ruta de salida.
        encoding: Encoding para CSV (recomendado: utf-8-sig para Power BI/Excel).

    Returns:
        Número de filas exportadas.
    """
    if not object_exists(conn, name):
        logger.warning("⚠️  No existe '%s' en SQLite, se omite", name)
        return 0

    query = f'SELECT * FROM "{name}"'
    df = pd.read_sql_query(query, conn)

    if df.empty:
        logger.warning("⚠️  '%s' está vacío, se omite", name)
        return 0

    # Limpieza ligera de nombres de columnas (sin cambiar semántica)
    df.columns = [str(c).strip() for c in df.columns]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding=encoding, lineterminator="\n")
    logger.info("✅ Exportado %s: %s filas -> %s", name, len(df), output_path)
    return int(len(df))


def create_readme(output_dir: Path, exported: Iterable[Tuple[str, str, int]]) -> None:
    """
    Crea README con guía de uso en Power BI/Looker/Tableau.

    Args:
        output_dir: Directorio base de export.
        exported: Iterable de (categoria, nombre, filas).
    """
    lines: List[str] = []
    lines.append("# BI exports (Power BI / Looker / Tableau)")
    lines.append("")
    lines.append("CSVs generados desde la base SQLite `data/processed/database.db`.")
    lines.append("")
    lines.append("## Archivos exportados")
    lines.append("")
    current_cat: Optional[str] = None
    for category, name, rows in exported:
        if category != current_cat:
            current_cat = category
            lines.append(f"### {category}/")
        lines.append(f"- `{name}.csv` ({rows:,} filas)")
    lines.append("")
    lines.append("## Recomendación de modelo (Power BI / Tableau)")
    lines.append("")
    lines.append("### Opción A (recomendada): modelo estrella estricto")
    lines.append("- **Dimensiones**: `00_star_schema/v_dim_barrios_star.csv`, `00_star_schema/v_dim_tiempo_star.csv`")
    lines.append(
        "- **Hechos anual (barrio-año)**: `00_star_schema/v_fact_housing_anual_star.csv`"
    )
    lines.append(
        "- **Hechos mensual (barrio-mes)**: `00_star_schema/v_fact_alquiler_mensual_star.csv`"
    )
    lines.append("")
    lines.append("**Relaciones**:")
    lines.append("- `v_fact_*_star.barrio_id` → `v_dim_barrios_star.barrio_id`")
    lines.append("- `v_fact_*_star.time_id` → `v_dim_tiempo_star.time_id`")
    lines.append("")
    lines.append("### Opción B: vistas “ready-to-use” (menos joins, más columnas repetidas)")
    lines.append("- **Dimensiones**: `01_dimensions/dim_barrios.csv`, `01_dimensions/dim_tiempo.csv`")
    lines.append("- **Anual**: `02_housing_yearly/v_metricas_housing.csv` (principal)")
    lines.append("- **Mensual**: `03_housing_monthly/v_alquiler_mensual.csv`")
    lines.append("")
    lines.append("## Notas de compatibilidad")
    lines.append("- Encoding: `utf-8-sig` (mejor para Power BI/Excel).")
    lines.append("- Fechas en ISO cuando existan (YYYY-MM-DD).")
    lines.append("")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """CLI principal."""
    parser = argparse.ArgumentParser(description="Export CSVs BI-ready desde SQLite.")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH))
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--encoding",
        type=str,
        default="utf-8-sig",
        help="Encoding para CSV (utf-8-sig recomendado para Power BI/Excel).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    args = parser.parse_args()
    setup_logging(args.log_level)

    db_path = Path(args.db_path)
    out_dir = Path(args.out_dir)

    if not db_path.exists():
        logger.error("No existe la base de datos: %s", db_path)
        return 2

    exported: List[Tuple[str, str, int]] = []
    total_rows = 0
    total_files = 0

    conn = connect_sqlite(db_path)
    try:
        logger.info("📦 Exportando CSVs BI-ready desde: %s", db_path)
        for category, objects in TABLE_CATEGORIES.items():
            logger.info("== %s ==", category)
            for name in objects:
                output_path = out_dir / category / f"{name}.csv"
                rows = export_query_to_csv(conn, name=name, output_path=output_path, encoding=args.encoding)
                if rows > 0:
                    exported.append((category, name, rows))
                    total_rows += rows
                    total_files += 1

        create_readme(out_dir, exported)
        logger.info("📝 README generado en: %s", out_dir / "README.md")
        logger.info("✅ Export finalizado: %s archivos, %s filas totales", total_files, total_rows)
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

