#!/usr/bin/env python3
"""
Database Schema Inspector - Barcelona Housing Demographics Analyzer

Muestra un resumen completo del esquema de la base de datos incluyendo:
- Todas las tablas y vistas
- Columnas con tipos de datos
- Índices y claves foráneas
- Estadísticas de registros
- Cobertura temporal
"""

import sys
from pathlib import Path
import sqlite3
import argparse
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager

def get_table_info(conn: sqlite3.Connection, table_name: str) -> List[Tuple]:
    """Obtiene información de columnas de una tabla."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def get_foreign_keys(conn: sqlite3.Connection, table_name: str) -> List[Tuple]:
    """Obtiene las claves foráneas de una tabla."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return cursor.fetchall()

def get_indexes(conn: sqlite3.Connection, table_name: str) -> List[Tuple]:
    """Obtiene los índices de una tabla."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({table_name})")
    return cursor.fetchall()

def get_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """Obtiene el número de registros en una tabla."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except:
        return 0

def get_year_range(conn: sqlite3.Connection, table_name: str) -> Tuple[int, int]:
    """Obtiene el rango de años en una tabla (si tiene columna 'anio')."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT MIN(anio), MAX(anio) FROM {table_name} WHERE anio IS NOT NULL")
        result = cursor.fetchone()
        return result if result[0] is not None else (None, None)
    except:
        return (None, None)

def get_barrio_coverage(conn: sqlite3.Connection, table_name: str) -> Tuple[int, int]:
    """Obtiene la cobertura de barrios (barrios únicos vs total)."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(DISTINCT barrio_id) FROM {table_name} WHERE barrio_id IS NOT NULL")
        unique_barrios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM dim_barrios")
        total_barrios = cursor.fetchone()[0]
        
        return (unique_barrios, total_barrios)
    except:
        return (0, 73)

def export_markdown(conn: sqlite3.Connection, output_path: str):
    """Genera un reporte del esquema en formato Markdown y lo guarda en un archivo."""
    lines = []
    lines.append("# Reporte de Esquema de Base de Datos")
    lines.append(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, type 
        FROM sqlite_master 
        WHERE type IN ('table', 'view') 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY type DESC, name
    """)
    objects = cursor.fetchall()
    
    tables = [obj for obj in objects if obj[1] == 'table']
    views = [obj for obj in objects if obj[1] == 'view']
    
    lines.append("## 📊 Resumen")
    lines.append(f"- **Tablas:** {len(tables)}")
    lines.append(f"- **Vistas:** {len(views)}")
    lines.append(f"- **Total:** {len(objects)}")
    lines.append("")
    
    lines.append("## 📋 Tablas")
    for table_name, _ in tables:
        lines.append(f"### `{table_name}`")
        
        # Columnas
        columns = get_table_info(conn, table_name)
        lines.append("#### 📌 Columnas")
        lines.append("| # | Nombre | Tipo | Atributos |")
        lines.append("|---|--------|------|-----------|")
        for col in columns:
            col_id, name, dtype, not_null, default, pk = col
            attrs = []
            if pk: attrs.append("🔑 PK")
            if not_null: attrs.append("NOT NULL")
            if default: attrs.append(f"DEFAULT {default}")
            lines.append(f"| {col_id+1} | `{name}` | {dtype} | {', '.join(attrs)} |")
        
        # FKs
        fks = get_foreign_keys(conn, table_name)
        if fks:
            lines.append("#### 🔗 Claves Foráneas")
            for fk in fks:
                _, _, ref_table, from_col, to_col, *_ = fk
                lines.append(f"- `{from_col}` → `{ref_table}({to_col})`")
        
        # Índices
        indexes = get_indexes(conn, table_name)
        if indexes:
            lines.append("#### 📇 Índices")
            for idx in indexes:
                _, idx_name, unique, *_ = idx
                lines.append(f"- `{idx_name}` {'(UNIQUE)' if unique else ''}")
        
        # Estadísticas
        row_count = get_row_count(conn, table_name)
        min_year, max_year = get_year_range(conn, table_name)
        
        lines.append("#### 📈 Estadísticas")
        lines.append(f"- **Registros:** {row_count:,}")
        if min_year:
            lines.append(f"- **Rango años:** {min_year} - {max_year}")
        
        if 'barrio_id' in [col[1] for col in columns]:
            unique, total = get_barrio_coverage(conn, table_name)
            coverage = (unique / total * 100) if total > 0 else 0
            lines.append(f"- **Cobertura barrios:** {unique}/{total} ({coverage:.1f}%)")
        
        lines.append("")

    if views:
        lines.append("## 👁️ Vistas")
        for view_name, _ in views:
            lines.append(f"### `{view_name}`")
            try:
                columns = get_table_info(conn, view_name)
                lines.append("#### 📌 Columnas")
                lines.append("| # | Nombre | Tipo |")
                lines.append("|---|--------|------|")
                for col in columns:
                    col_id, name, dtype, *_ = col
                    lines.append(f"| {col_id+1} | `{name}` | {dtype} |")
                
                row_count = get_row_count(conn, view_name)
                lines.append(f"- **Registros:** {row_count:,}")
            except Exception as e:
                lines.append(f"⚠️ Error al inspeccionar vista: {str(e)}")
            lines.append("")

    lines.append("## 📊 Resumen de Cobertura (Tablas Fact)")
    lines.append("| Tabla | Registros | Años | Barrios |")
    lines.append("|-------|-----------|------|---------|")
    
    fact_tables = [t[0] for t in tables if t[0].startswith('fact_')]
    for table in fact_tables:
        row_count = get_row_count(conn, table)
        min_year, max_year = get_year_range(conn, table)
        year_str = f"{min_year}-{max_year}" if min_year else "N/A"
        
        columns = get_table_info(conn, table)
        has_barrio = 'barrio_id' in [col[1] for col in columns]
        if has_barrio:
            unique, total = get_barrio_coverage(conn, table)
            barrio_str = f"{unique}/{total} ({unique/total*100:.0f}%)"
        else:
            barrio_str = "N/A"
        
        lines.append(f"| `{table}` | {row_count:,} | {year_str} | {barrio_str} |")

    content = "\n".join(lines)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"\n✅ Reporte guardado en: {output_path}")

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Inspecciona el esquema de la base de datos.")
    parser.add_argument("--markdown", type=str, help="Ruta del archivo para exportar en Markdown (ej: docs/SCHEMA.md)")
    args = parser.parse_args()

    print("=" * 80)
    print("DATABASE SCHEMA INSPECTOR - Barcelona Housing Demographics")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    db = DatabaseManager()
    conn = db.get_connection()
    
    try:
        if args.markdown:
            export_markdown(conn, args.markdown)
            return

        # Obtener todas las tablas y vistas
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, type 
            FROM sqlite_master 
            WHERE type IN ('table', 'view') 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY type DESC, name
        """)
        objects = cursor.fetchall()
        
        tables = [obj for obj in objects if obj[1] == 'table']
        views = [obj for obj in objects if obj[1] == 'view']
        
        print(f"📊 RESUMEN")
        print("-" * 80)
        print(f"  Tablas: {len(tables)}")
        print(f"  Vistas: {len(views)}")
        print(f"  Total:  {len(objects)}")
        print()
        
        # ============================================================
        # TABLAS
        # ============================================================
        print("=" * 80)
        print("📋 TABLAS")
        print("=" * 80)
        print()
        
        for table_name, _ in tables:
            print(f"┌─ {table_name}")
            print("│")
            
            # Información de columnas
            columns = get_table_info(conn, table_name)
            print("│  📌 COLUMNAS:")
            for col in columns:
                col_id, name, dtype, not_null, default, pk = col
                pk_mark = " 🔑 PK" if pk else ""
                null_mark = " NOT NULL" if not_null else ""
                default_mark = f" DEFAULT {default}" if default else ""
                print(f"│    {col_id+1:2d}. {name:30s} {dtype:15s}{pk_mark}{null_mark}{default_mark}")
            
            # Claves foráneas
            fks = get_foreign_keys(conn, table_name)
            if fks:
                print("│")
                print("│  🔗 FOREIGN KEYS:")
                for fk in fks:
                    _, _, ref_table, from_col, to_col, *_ = fk
                    print(f"│    {from_col} → {ref_table}({to_col})")
            
            # Índices
            indexes = get_indexes(conn, table_name)
            if indexes:
                print("│")
                print("│  📇 ÍNDICES:")
                for idx in indexes:
                    _, idx_name, unique, *_ = idx
                    unique_mark = " (UNIQUE)" if unique else ""
                    print(f"│    {idx_name}{unique_mark}")
            
            # Estadísticas
            row_count = get_row_count(conn, table_name)
            print("│")
            print("│  📈 ESTADÍSTICAS:")
            print(f"│    Registros: {row_count:,}")
            
            # Rango de años (si aplica)
            min_year, max_year = get_year_range(conn, table_name)
            if min_year is not None:
                print(f"│    Años: {min_year} - {max_year}")
            
            # Cobertura de barrios (si aplica)
            if 'barrio_id' in [col[1] for col in columns]:
                unique, total = get_barrio_coverage(conn, table_name)
                coverage = (unique / total * 100) if total > 0 else 0
                print(f"│    Barrios: {unique}/{total} ({coverage:.1f}%)")
            
            print("└" + "─" * 78)
            print()
        
        # ============================================================
        # VISTAS
        # ============================================================
        if views:
            print("=" * 80)
            print("👁️  VISTAS")
            print("=" * 80)
            print()
            
            for view_name, _ in views:
                print(f"┌─ {view_name}")
                print("│")
                
                try:
                    # Información de columnas
                    columns = get_table_info(conn, view_name)
                    print("│  📌 COLUMNAS:")
                    for col in columns:
                        col_id, name, dtype, *_ = col
                        print(f"│    {col_id+1:2d}. {name:30s} {dtype:15s}")
                    
                    # Estadísticas
                    row_count = get_row_count(conn, view_name)
                    print("│")
                    print("│  📈 ESTADÍSTICAS:")
                    print(f"│    Registros: {row_count:,}")
                    
                    # Rango de años (si aplica)
                    min_year, max_year = get_year_range(conn, view_name)
                    if min_year is not None:
                        print(f"│    Años: {min_year} - {max_year}")
                
                except Exception as e:
                    print(f"│  ⚠️  ERROR: {str(e)}")
                    print("│  (La vista puede tener referencias a columnas que no existen)")
                
                print("└" + "─" * 78)
                print()
        
        # ============================================================
        # RESUMEN DE COBERTURA
        # ============================================================
        print("=" * 80)
        print("📊 RESUMEN DE COBERTURA")
        print("=" * 80)
        print()
        
        fact_tables = [t[0] for t in tables if t[0].startswith('fact_')]
        
        print(f"{'Tabla':<35} {'Registros':>12} {'Años':>15} {'Barrios':>15}")
        print("-" * 80)
        
        for table in fact_tables:
            row_count = get_row_count(conn, table)
            min_year, max_year = get_year_range(conn, table)
            
            year_str = f"{min_year}-{max_year}" if min_year else "N/A"
            
            # Verificar si tiene barrio_id
            columns = get_table_info(conn, table)
            has_barrio = 'barrio_id' in [col[1] for col in columns]
            
            if has_barrio:
                unique, total = get_barrio_coverage(conn, table)
                barrio_str = f"{unique}/{total} ({unique/total*100:.0f}%)"
            else:
                barrio_str = "N/A"
            
            print(f"{table:<35} {row_count:>12,} {year_str:>15} {barrio_str:>15}")
        
        print()
        print("=" * 80)
        print("✅ Inspección completada")
        print("=" * 80)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
