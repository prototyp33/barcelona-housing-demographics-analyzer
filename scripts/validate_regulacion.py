from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from src.database_setup import (
    create_connection,
    create_database_schema,
    ensure_database_path,
)

logger = logging.getLogger(__name__)


def _get_db_path() -> Path:
    """
    Obtiene la ruta por defecto de la base de datos procesada.

    Returns:
        Ruta al archivo SQLite en ``data/processed/database.db``.
    """
    processed_dir = Path("data") / "processed"
    return ensure_database_path(None, processed_dir)


def validate_regulacion(conn: sqlite3.Connection) -> bool:
    """
    Valida la tabla ``fact_regulacion`` según los criterios del sprint.

    Criterios:
        - 73 barrios con datos (COUNT DISTINCT barrio_id).
        - Cobertura temporal mínima: incluye años 2024 y 2025.
        - Al menos el 95% de los registros tienen
          ``indice_referencia_alquiler`` no nulo.

    Args:
        conn: Conexión SQLite activa.

    Returns:
        True si se cumplen todos los criterios, False en caso contrario.
    """
    cursor = conn.cursor()

    # 1. Número de barrios
    cursor.execute("SELECT COUNT(DISTINCT barrio_id) FROM fact_regulacion;")
    distinct_barrios = cursor.fetchone()[0] or 0
    
    # Identificar barrios faltantes
    cursor.execute("SELECT DISTINCT barrio_id FROM fact_regulacion;")
    present_barrios = {r[0] for r in cursor.fetchall() if r[0] is not None}
    
    cursor.execute("SELECT barrio_id, barrio_nombre FROM dim_barrios ORDER BY barrio_id;")
    all_barrios = {r[0]: r[1] for r in cursor.fetchall()}
    
    missing_barrios = set(all_barrios.keys()) - present_barrios
    missing_details = [(bid, all_barrios[bid]) for bid in sorted(missing_barrios)]

    # 2. Cobertura temporal
    cursor.execute("SELECT MIN(anio), MAX(anio) FROM fact_regulacion;")
    row = cursor.fetchone()
    min_year, max_year = row if row else (None, None)

    cursor.execute("SELECT DISTINCT anio FROM fact_regulacion;")
    years = {r[0] for r in cursor.fetchall() if r[0] is not None}

    has_2024 = 2024 in years
    has_2025 = 2025 in years

    # 3. Completitud del índice de referencia
    cursor.execute("SELECT COUNT(*) FROM fact_regulacion;")
    total_rows = cursor.fetchone()[0] or 0

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM fact_regulacion
        WHERE indice_referencia_alquiler IS NOT NULL;
        """
    )
    non_null_rows = cursor.fetchone()[0] or 0

    completeness = (non_null_rows / total_rows * 100.0) if total_rows else 0.0

    print("=== Validación fact_regulacion ===")
    print(f"- Barrios distintos: {distinct_barrios}/73")
    if missing_details:
        print(f"- Barrios faltantes ({len(missing_details)}):")
        for barrio_id, barrio_nombre in missing_details:
            print(f"  * {barrio_id}: {barrio_nombre}")
    print(f"- Rango de años: {min_year} - {max_year}")
    print(f"- Años presentes: {sorted(years)}")
    print(
        f"- Registros con indice_referencia_alquiler no nulo: "
        f"{non_null_rows}/{total_rows} ({completeness:.2f}%)"
    )

    ok_barrios = distinct_barrios == 73
    ok_years = has_2024 and has_2025
    ok_completeness = completeness >= 95.0

    print()
    print("Criterios:")
    print(f"* 73 barrios con datos: {'OK' if ok_barrios else 'FALLO'}")
    print(
        "* Cobertura 2024-2025: "
        f"{'OK' if ok_years else 'FALLO'} (2024={has_2024}, 2025={has_2025})"
    )
    print(
        f"* ≥95% completitud en indice_referencia_alquiler: "
        f"{'OK' if ok_completeness else 'FALLO'}"
    )

    return bool(ok_barrios and ok_years and ok_completeness)


def main() -> None:
    """
    Punto de entrada CLI para validar ``fact_regulacion``.

    Conecta a la base de datos por defecto y ejecuta las comprobaciones
    definidas en :func:`validate_regulacion`.
    """
    db_path = _get_db_path()
    print(f"Usando base de datos: {db_path}")

    conn = create_connection(db_path)
    try:
        # Asegurar que el esquema (incluyendo fact_regulacion) existe
        create_database_schema(conn)
        success = validate_regulacion(conn)
    finally:
        conn.close()

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()


