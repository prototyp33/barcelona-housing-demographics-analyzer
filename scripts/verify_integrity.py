"""
Script de validación de integridad de datos.

Verifica la integridad referencial, duplicados y completitud de datos.
Puede ejecutarse desde línea de comandos o importarse como módulo.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


db_path = Path("data/processed/database.db")


def verify_integrity(return_json: bool = False) -> Optional[Dict]:
    """
    Verifica la integridad de la base de datos.
    
    Args:
        return_json: Si es True, retorna diccionario en lugar de imprimir.
    
    Returns:
        Diccionario con resultados si return_json=True, None en caso contrario.
    """
    if not db_path.exists():
        error_msg = "Database not found."
        if return_json:
            return {"error": error_msg, "status": "error"}
        print(error_msg)
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {
        "status": "success",
        "checks": [],
        "warnings": [],
        "errors": []
    }
    
    # Check 1: Duplicados fragmentados en fact_precios
    cursor.execute("""
        SELECT barrio_id, anio, trimestre, COUNT(*) 
        FROM fact_precios 
        GROUP BY barrio_id, anio, trimestre 
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        warning_msg = f"WARNING: {len(duplicates)} fragmented records found. Analytics will be difficult."
        results["warnings"].append({
            "type": "duplicates",
            "message": warning_msg,
            "count": len(duplicates),
            "samples": [
                {"barrio_id": dup[0], "anio": dup[1], "trimestre": dup[2], "count": dup[3]}
                for dup in duplicates[:5]
            ]
        })
        if not return_json:
            print(warning_msg)
            for dup in duplicates[:5]:
                print(f"  - Barrio {dup[0]}, Year {dup[1]}, Q{dup[2]}: {dup[3]} rows")
    else:
        success_msg = "✅ No fragmented records found in fact_precios."
        results["checks"].append({
            "type": "duplicates",
            "status": "pass",
            "message": success_msg
        })
        if not return_json:
            print(success_msg)
    
    # Check 2: Completitud demográfica
    cursor.execute("""
        SELECT COUNT(*) FROM fact_demografia 
        WHERE edad_media IS NULL OR densidad_hab_km2 IS NULL
    """)
    nulls = cursor.fetchone()[0]
    
    if nulls > 0:
        warning_msg = f"WARNING: {nulls} demographic records with NULL values in critical fields."
        results["warnings"].append({
            "type": "nulls",
            "message": warning_msg,
            "count": nulls
        })
    else:
        success_msg = "✅ No NULL values in critical demographic fields."
        results["checks"].append({
            "type": "nulls",
            "status": "pass",
            "message": success_msg
        })
    
    if not return_json:
        print(f"Demographic Nulls: {nulls}")
    
    # Check 3: Verificar fuentes combinadas
    cursor.execute("""
        SELECT dataset_id, source FROM fact_precios 
        WHERE dataset_id LIKE '%|%' OR source LIKE '%|%'
        LIMIT 5
    """)
    merged_rows = cursor.fetchall()
    
    if merged_rows:
        info_msg = f"✅ Found {len(merged_rows)} sample rows with merged sources (indicating successful upsert)."
        results["checks"].append({
            "type": "merged_sources",
            "status": "info",
            "message": info_msg,
            "count": len(merged_rows),
            "samples": [
                {"dataset_id": row[0], "source": row[1]}
                for row in merged_rows
            ]
        })
        if not return_json:
            print(info_msg)
            for row in merged_rows:
                print(f"  - Dataset IDs: {row[0]}")
    else:
        info_msg = "ℹ️ No merged source rows found (might be expected if no overlap occurred)."
        results["checks"].append({
            "type": "merged_sources",
            "status": "info",
            "message": info_msg
        })
        if not return_json:
            print(info_msg)
    
    # Check 4: Integridad referencial
    cursor.execute("""
        SELECT COUNT(*) FROM fact_precios p
        LEFT JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE b.barrio_id IS NULL
    """)
    orphan_precios = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM fact_demografia d
        LEFT JOIN dim_barrios b ON d.barrio_id = b.barrio_id
        WHERE b.barrio_id IS NULL
    """)
    orphan_demo = cursor.fetchone()[0]
    
    if orphan_precios > 0 or orphan_demo > 0:
        error_msg = f"ERROR: Found {orphan_precios + orphan_demo} orphan records (violates referential integrity)."
        results["errors"].append({
            "type": "referential_integrity",
            "message": error_msg,
            "orphan_precios": orphan_precios,
            "orphan_demo": orphan_demo
        })
        if not return_json:
            print(error_msg)
    else:
        success_msg = "✅ Referential integrity check passed."
        results["checks"].append({
            "type": "referential_integrity",
            "status": "pass",
            "message": success_msg
        })
        if not return_json:
            print(success_msg)
    
    conn.close()
    
    # Determinar estado general
    if results["errors"]:
        results["status"] = "error"
    elif results["warnings"]:
        results["status"] = "warning"
    else:
        results["status"] = "success"
    
    if return_json:
        return results
    
    return None


if __name__ == "__main__":
    verify_integrity(return_json=False)
