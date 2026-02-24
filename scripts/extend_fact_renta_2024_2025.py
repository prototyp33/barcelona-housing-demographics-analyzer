#!/usr/bin/env python3
"""
Extiende fact_renta con años 2024 y 2025.

Estrategia:
1. Intenta extraer datos oficiales de IDESCAT/Open Data BCN para 2024-2025.
2. Si no hay datos oficiales, inserta estimaciones por forward-fill (copia 2023)
   con source='estimated_forward_fill' para transparencia.

Uso:
    python scripts/extend_fact_renta_2024_2025.py
    python scripts/extend_fact_renta_2024_2025.py --dry-run
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Abre conexión a SQLite."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_max_renta_year(conn: sqlite3.Connection) -> int | None:
    """Obtiene el año máximo en fact_renta."""
    df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_renta", conn)
    val = df["max_year"].iloc[0]
    return int(val) if pd.notna(val) else None


def try_extract_and_load(
    conn: sqlite3.Connection,
    year_start: int,
    year_end: int,
    dry_run: bool,
) -> bool:
    """
    Intenta extraer datos oficiales e insertarlos.
    Returns True si se insertó algo, False si hay que usar forward-fill.
    """
    try:
        from src.extraction.idescat import IDESCATExtractor
        from src.etl.transformations.market import load_idescat_income, prepare_renta_barrio

        extractor = IDESCATExtractor(rate_limit_delay=1.0)
        df, metadata = extractor.get_renta_by_barrio(year_start=year_start, year_end=year_end)
        if not metadata.get("success") or df.empty:
            return False

        # IDESCAT puede devolver Codi_Barri/anio o Any/Codi_Barri según estrategia
        if "anio" not in df.columns and "Any" in df.columns:
            df = df.rename(columns={"Any": "anio"})
        if "anio" not in df.columns:
            return False

        years_in_df = [int(y) for y in df["anio"].dropna().unique() if y in (2024, 2025)]
        if not years_in_df:
            return False

        dim_barrios = pd.read_sql("SELECT * FROM dim_barrios", conn)
        ref_time = datetime.now(timezone.utc)

        # Probar load_idescat_income (formato IDESCAT) o prepare_renta_barrio (Open Data BCN)
        fact_new = None
        if "Codi_Barri" in df.columns:
            try:
                fact_new = load_idescat_income(
                    df, dim_barrios, "idescat_extended", ref_time, "opendatabcn"
                )
            except Exception:
                pass
        if fact_new is None and "Any" in df.columns:
            try:
                fact_new = prepare_renta_barrio(
                    df, dim_barrios, "idescat_extended", ref_time, "opendatabcn", "mean"
                )
            except Exception:
                pass

        if fact_new is None or fact_new.empty:
            return False

        fact_new = fact_new[fact_new["anio"].isin(years_in_df)]
        if fact_new.empty:
            return False

        if not dry_run:
            fact_new.to_sql("fact_renta", conn, if_exists="append", index=False)
            conn.commit()
        print(f"   ✓ Datos oficiales: {len(fact_new)} registros para años {years_in_df}")
        return True
    except Exception as e:
        print(f"   ⚠️  Extracción/carga falló: {e}")
        return False


def copy_2023_to_new_years(conn: sqlite3.Connection, years: list[int]) -> int:
    """Copia registros de 2023 a los años indicados con source=estimated_forward_fill."""
    dim_barrios = pd.read_sql("SELECT barrio_id FROM dim_barrios", conn)
    barrio_ids = dim_barrios["barrio_id"].tolist()

    df_2023 = pd.read_sql(
        """
        SELECT barrio_id, renta_euros, renta_promedio, renta_mediana, renta_min, renta_max,
               num_secciones, barrio_nombre_normalizado, dataset_id
        FROM fact_renta WHERE anio = 2023
        """,
        conn,
    )

    if df_2023.empty:
        print("   ❌ No hay datos de 2023 para copiar")
        return 0

    ref_time = datetime.now(timezone.utc).isoformat()
    cursor = conn.cursor()
    inserted = 0

    for year in years:
        for _, row in df_2023.iterrows():
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_renta
                (barrio_id, anio, renta_euros, renta_promedio, renta_mediana, renta_min, renta_max,
                 num_secciones, barrio_nombre_normalizado, dataset_id, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'estimated_forward_fill', ?)
                """,
                (
                    int(row["barrio_id"]),
                    year,
                    row["renta_euros"],
                    row["renta_promedio"],
                    row["renta_mediana"],
                    row["renta_min"],
                    row["renta_max"],
                    row["num_secciones"],
                    row["barrio_nombre_normalizado"],
                    row["dataset_id"] or "forward_fill_2023",
                    ref_time,
                ),
            )
            inserted += 1

    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Extiende fact_renta con 2024-2025")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría")
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Omitir extracción IDESCAT y usar directamente forward-fill (útil sin red)",
    )
    args = parser.parse_args()

    if not args.db_path.exists():
        print(f"❌ Base de datos no encontrada: {args.db_path}")
        return 1

    conn = get_connection(args.db_path)
    max_year = get_max_renta_year(conn)

    if max_year is None:
        print("❌ fact_renta está vacía. Ejecuta el ETL primero.")
        conn.close()
        return 1

    years_to_add = [y for y in [2024, 2025] if y > max_year]
    if not years_to_add:
        print(f"✅ fact_renta ya tiene datos hasta {max_year}. No hay nada que extender.")
        conn.close()
        return 0

    print(f"📊 fact_renta actual: hasta {max_year}")
    print(f"   Años a añadir: {years_to_add}")
    print()

    # 1. Intentar extracción oficial (salvo --skip-extraction)
    if not args.skip_extraction:
        print("1. Intentando extracción oficial (IDESCAT/Open Data BCN)...")
        if try_extract_and_load(conn, min(years_to_add), max(years_to_add), args.dry_run):
            conn.close()
            return 0
        print("   ⚠️  No hay datos oficiales. Usando forward-fill desde 2023.")
    else:
        print("1. Omitiendo extracción (--skip-extraction). Usando forward-fill desde 2023.")
    print()

    # 2. Forward-fill desde 2023
    print("2. Insertando estimaciones (copia de 2023, source=estimated_forward_fill)...")
    if args.dry_run:
        count_2023 = pd.read_sql("SELECT COUNT(*) as c FROM fact_renta WHERE anio=2023", conn)["c"].iloc[0]
        print(f"   [DRY-RUN] Se insertarían {count_2023 * len(years_to_add)} registros")
        conn.close()
        return 0

    inserted = copy_2023_to_new_years(conn, years_to_add)
    conn.commit()
    conn.close()

    print(f"   ✓ Insertados {inserted} registros")
    print()
    print("⚠️  Los datos de 2024-2025 son estimaciones (forward-fill de 2023).")
    print("   Actualiza cuando IDESCAT publique datos oficiales.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
