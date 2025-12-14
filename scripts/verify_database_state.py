#!/usr/bin/env python3
"""
Script para verificar el estado actual de la base de datos.
Consulta el esquema, índices, conteos y calidad de datos.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection, VALID_TABLES

DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def get_table_info(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Obtiene información del esquema de una tabla."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "pk": row[5],
        })
    return columns


def get_indexes(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Obtiene información de índices de una tabla."""
    cursor = conn.execute(f"PRAGMA index_list({table_name})")
    indexes = []
    for row in cursor.fetchall():
        idx_name = row[1]
        is_unique = row[2]
        # Obtener columnas del índice
        idx_info = conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
        columns = [col[2] for col in idx_info if col[2] is not None]
        # Si no hay columnas, intentar obtener la expresión del índice
        if not columns:
            try:
                # Para índices con expresiones (como COALESCE), obtener la definición SQL
                sql_cursor = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='index' AND name=?",
                    (idx_name,)
                )
                sql_row = sql_cursor.fetchone()
                if sql_row and sql_row[0]:
                    # Extraer columnas de la definición SQL
                    sql_def = sql_row[0]
                    if "(" in sql_def and ")" in sql_def:
                        cols_part = sql_def.split("(")[1].split(")")[0]
                        columns = [c.strip() for c in cols_part.split(",")]
            except Exception:
                pass
        indexes.append({
            "name": idx_name,
            "unique": bool(is_unique),
            "columns": columns,
        })
    return indexes


def get_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Obtiene el número de filas en una tabla."""
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def get_null_counts(conn: sqlite3.Connection, table_name: str) -> dict[str, int]:
    """Obtiene conteos de valores nulos por columna."""
    columns = get_table_info(conn, table_name)
    null_counts = {}
    for col in columns:
        col_name = col["name"]
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL"
        )
        null_counts[col_name] = cursor.fetchone()[0]
    return null_counts


def check_foreign_keys(conn: sqlite3.Connection) -> dict:
    """Verifica la integridad de las foreign keys."""
    results = {}
    for table in VALID_TABLES:
        if table == "dim_barrios" or table == "etl_runs":
            continue
        
        # Obtener foreign keys de la tabla
        cursor = conn.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        
        if not fks:
            continue
        
        for fk in fks:
            fk_table = fk[2]  # Tabla referenciada
            fk_from = fk[3]   # Columna en tabla actual
            fk_to = fk[4]     # Columna en tabla referenciada
            
            # Verificar registros huérfanos
            query = f"""
                SELECT COUNT(*) 
                FROM {table} t
                LEFT JOIN {fk_table} d ON t.{fk_from} = d.{fk_to}
                WHERE d.{fk_to} IS NULL
            """
            cursor = conn.execute(query)
            orphan_count = cursor.fetchone()[0]
            
            key = f"{table}.{fk_from} -> {fk_table}.{fk_to}"
            results[key] = {
                "orphan_count": orphan_count,
                "valid": orphan_count == 0,
            }
    
    return results


def main():
    """Ejecuta la verificación completa de la base de datos."""
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada: {DB_PATH}")
        return 1
    
    print(f"📊 Verificando base de datos: {DB_PATH}\n")
    print("=" * 80)
    
    conn = create_connection(DB_PATH)
    
    try:
        # 1. Listar todas las tablas
        print("\n## 1. TABLAS EXISTENTES")
        print("-" * 80)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        all_tables = [row[0] for row in cursor.fetchall()]
        for table in all_tables:
            status = "✓" if table in VALID_TABLES else "⚠"
            print(f"{status} {table}")
        
        # 2. Verificar esquema de cada tabla válida
        print("\n## 2. ESQUEMA DE TABLAS")
        print("=" * 80)
        
        for table in sorted(VALID_TABLES):
            if table not in all_tables:
                print(f"\n⚠ {table}: NO EXISTE")
                continue
            
            print(f"\n### {table}")
            print("-" * 80)
            
            # Columnas
            columns = get_table_info(conn, table)
            print("\nColumnas:")
            for col in columns:
                pk = " [PK]" if col["pk"] else ""
                nn = " NOT NULL" if col["notnull"] else ""
                default = f" DEFAULT {col['default']}" if col["default"] else ""
                print(f"  - {col['name']}: {col['type']}{pk}{nn}{default}")
            
            # Índices
            indexes = get_indexes(conn, table)
            if indexes:
                print("\nÍndices:")
                for idx in indexes:
                    unique = "UNIQUE " if idx["unique"] else ""
                    cols = ", ".join(idx["columns"])
                    print(f"  - {unique}{idx['name']}: ({cols})")
            
            # Conteo de filas
            row_count = get_row_count(conn, table)
            print(f"\nRegistros: {row_count:,}")
            
            # Valores nulos en columnas clave
            null_counts = get_null_counts(conn, table)
            important_nulls = {
                k: v for k, v in null_counts.items()
                if v > 0 and k not in ["id", "etl_loaded_at", "etl_created_at", "etl_updated_at"]
            }
            if important_nulls:
                print("\nValores nulos (columnas importantes):")
                for col, count in sorted(important_nulls.items(), key=lambda x: x[1], reverse=True):
                    pct = (count / row_count * 100) if row_count > 0 else 0
                    print(f"  - {col}: {count:,} ({pct:.1f}%)")
        
        # 3. Verificar integridad referencial
        print("\n## 3. INTEGRIDAD REFERENCIAL")
        print("=" * 80)
        fk_results = check_foreign_keys(conn)
        if fk_results:
            for fk, result in fk_results.items():
                status = "✓" if result["valid"] else "❌"
                print(f"{status} {fk}: {result['orphan_count']} registros huérfanos")
        else:
            print("No se encontraron foreign keys para verificar")
        
        # 4. Estadísticas generales
        print("\n## 4. ESTADÍSTICAS GENERALES")
        print("=" * 80)
        
        total_rows = sum(get_row_count(conn, table) for table in VALID_TABLES if table in all_tables)
        print(f"Total de registros en todas las tablas: {total_rows:,}")
        
        # Verificar barrios
        if "dim_barrios" in all_tables:
            barrio_count = get_row_count(conn, "dim_barrios")
            print(f"\nBarrios en dim_barrios: {barrio_count}/73")
            
            # Verificar geometry_json
            cursor = conn.execute(
                "SELECT COUNT(*) FROM dim_barrios WHERE geometry_json IS NOT NULL AND geometry_json != ''"
            )
            geojson_count = cursor.fetchone()[0]
            print(f"Barrios con geometry_json: {geojson_count}/73 ({geojson_count/73*100:.1f}%)")
        
        # Verificar fact_precios
        if "fact_precios" in all_tables:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT barrio_id) FROM fact_precios"
            )
            barrios_con_precios = cursor.fetchone()[0]
            print(f"\nBarrios con datos de precios: {barrios_con_precios}")
            
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT source) FROM fact_precios"
            )
            sources = cursor.fetchone()[0]
            print(f"Fuentes de datos en fact_precios: {sources}")
        
        # Verificar fact_demografia
        if "fact_demografia" in all_tables:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT barrio_id) FROM fact_demografia"
            )
            barrios_con_demo = cursor.fetchone()[0]
            print(f"\nBarrios con datos demográficos: {barrios_con_demo}")
        
        print("\n" + "=" * 80)
        print("✅ Verificación completada")
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

