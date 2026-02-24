#!/usr/bin/env python3
"""
Pobla fact_demografia_ampliada con años históricos desde fact_demografia.

fact_demografia_ampliada solo tiene 2025 (datos desagregados de Open Data BCN).
fact_demografia tiene 2015-2025 (agregados).

Este script crea registros "agregados" en fact_demografia_ampliada para años
que solo existen en fact_demografia, permitiendo análisis multivariable
con cobertura temporal completa.

Cada registro histórico tiene:
- sexo='desconocido', grupo_edad=None, nacionalidad=None
- poblacion=poblacion_total (de fact_demografia)
- source='backfill_from_fact_demografia'

Uso:
    python scripts/backfill_fact_demografia_ampliada.py
    python scripts/backfill_fact_demografia_ampliada.py --dry-run
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


def get_ampliada_years(conn: sqlite3.Connection) -> set[int]:
    """Obtiene años ya presentes en fact_demografia_ampliada."""
    df = pd.read_sql("SELECT DISTINCT anio FROM fact_demografia_ampliada", conn)
    return set(df["anio"].dropna().astype(int).tolist())


def get_demografia_years(conn: sqlite3.Connection) -> set[int]:
    """Obtiene años en fact_demografia."""
    df = pd.read_sql("SELECT DISTINCT anio FROM fact_demografia WHERE anio IS NOT NULL", conn)
    return set(df["anio"].dropna().astype(int).tolist())


def backfill(conn: sqlite3.Connection, dry_run: bool) -> int:
    """
    Inserta en fact_demografia_ampliada registros agregados desde fact_demografia
    para años que no están en ampliada.
    """
    years_ampliada = get_ampliada_years(conn)
    years_demografia = get_demografia_years(conn)
    years_to_add = years_demografia - years_ampliada

    if not years_to_add:
        return 0

    placeholders = ",".join("?" * len(years_to_add))
    df_dem = pd.read_sql(
        f"""
        SELECT d.barrio_id, d.anio, d.poblacion_total,
               b.barrio_nombre_normalizado
        FROM fact_demografia d
        JOIN dim_barrios b ON d.barrio_id = b.barrio_id
        WHERE d.anio IN ({placeholders})
        AND d.poblacion_total IS NOT NULL AND d.poblacion_total > 0
        """,
        conn,
        params=list(years_to_add),
    )

    if df_dem.empty:
        return 0

    ref_time = datetime.now(timezone.utc).isoformat()
    records = []

    for _, row in df_dem.iterrows():
        records.append({
            "barrio_id": int(row["barrio_id"]),
            "anio": int(row["anio"]),
            "sexo": "desconocido",
            "grupo_edad": None,
            "nacionalidad": None,
            "poblacion": int(row["poblacion_total"]),
            "barrio_nombre_normalizado": row["barrio_nombre_normalizado"],
            "dataset_id": "backfill_fact_demografia",
            "source": "backfill_from_fact_demografia",
            "etl_loaded_at": ref_time,
        })

    if dry_run:
        return len(records)

    df_insert = pd.DataFrame(records)
    df_insert.to_sql(
        "fact_demografia_ampliada",
        conn,
        if_exists="append",
        index=False,
    )
    conn.commit()
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill fact_demografia_ampliada desde fact_demografia"
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.db_path.exists():
        print(f"❌ Base de datos no encontrada: {args.db_path}")
        return 1

    conn = get_connection(args.db_path)

    years_ampliada = get_ampliada_years(conn)
    years_demografia = get_demografia_years(conn)
    years_to_add = sorted(years_demografia - years_ampliada)

    if not years_to_add:
        print("✅ fact_demografia_ampliada ya tiene todos los años de fact_demografia.")
        conn.close()
        return 0

    print(f"📊 fact_demografia_ampliada: años {sorted(years_ampliada)}")
    print(f"   fact_demografia: años {sorted(years_demografia)}")
    print(f"   Años a backfill: {years_to_add}")
    print()

    inserted = backfill(conn, args.dry_run)
    conn.close()

    if args.dry_run:
        print(f"[DRY-RUN] Se insertarían {inserted} registros")
    else:
        print(f"✓ Insertados {inserted} registros en fact_demografia_ampliada")
        print()
        print("⚠️  Los registros históricos tienen sexo='desconocido' y sin desagregación")
        print("   por edad/nacionalidad. Solo poblacion_total está disponible.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
