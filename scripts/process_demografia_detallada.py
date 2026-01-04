#!/usr/bin/env python3
"""
Script para procesar demografía detallada de IDESCAT y enriquecer fact_demografia.

Fuentes:
- IDESCAT: Datos a nivel municipal (Barcelona) distribuidos proporcionalmente.

Este script:
1. Lee datos demográficos municipales de IDESCAT EMEX.
2. Distribuye valores por barrio usando la población total existente como peso.
3. Actualiza o inserta en fact_demografia.
"""

import logging
import sqlite3
import sys
import re
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

import pandas as pd
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def get_connection() -> sqlite3.Connection:
    """Crea una conexión a la base de datos."""
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def get_barrios_weights(conn: sqlite3.Connection) -> pd.DataFrame:
    """Obtiene pesos de barrios usando población total disponible."""
    # Intentar obtener de v_demografia_aggregated
    try:
        query = """
        SELECT barrio_id, MAX(poblacion_total) as peso
        FROM v_demografia_aggregated
        GROUP BY barrio_id
        HAVING peso > 0
        """
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            return df
    except Exception:
        pass
        
    # Fallback a dim_barrios si no hay datos demográficos
    query = "SELECT barrio_id, 1.0 as peso FROM dim_barrios"
    return pd.read_sql_query(query, conn)


def main():
    try:
        from src.extraction.idescat import IDESCATExtractor
        e = IDESCATExtractor()
        
        conn = get_connection()
        barrios_df = get_barrios_weights(conn)
        
        raw_dir = PROJECT_ROOT / "data" / "raw" / "idescat"
        if not raw_dir.exists():
            logger.error("Directorio de datos raw de idescat no existe")
            return 1
            
        # Buscar archivos de demografía detallada
        files = list(raw_dir.glob("*demografia_detallada*.csv"))
        if not files:
            logger.error("No se encontraron archivos de demografía detallada")
            logger.info("Ejecutar: python -c 'from src.extraction.idescat import IDESCATExtractor; e = IDESCATExtractor(); e.get_demographics_emex(2024)'")
            return 1
            
        latest_file = max(files, key=lambda p: p.stat().st_mtime)
        df_raw = pd.read_csv(latest_file)
        if df_raw.empty:
            return 1
            
        row = df_raw.iloc[0]
        anio = int(row.get("anio", 2024))
        
        total_peso = barrios_df["peso"].sum()
        
        # Columnas a distribuir
        cols_to_distribute = {
            "pob_hombres": "poblacion_hombres",
            "pob_mujeres": "poblacion_mujeres",
            "pob_total": "poblacion_total",
        }
        
        inserted = 0
        cursor = conn.cursor()
        
        for _, b_row in barrios_df.iterrows():
            bid = int(b_row["barrio_id"])
            prop = b_row["peso"] / total_peso if total_peso > 0 else 1.0/len(barrios_df)
            
            # Cálculos adicionales
            pob_total = row.get("pob_total", 0) * prop
            pob_hombres = row.get("pob_hombres", 0) * prop
            pob_mujeres = row.get("pob_mujeres", 0) * prop
            
            # Grupos edad
            pob_0_14 = row.get("pob_0_14", 0) * prop
            pob_65_plus = (row.get("pob_65_84", 0) + row.get("pob_85_mas", 0)) * prop
            
            pct_menores_15 = (pob_0_14 / pob_total * 100) if pob_total > 0 else 0
            pct_mayores_65 = (pob_65_plus / pob_total * 100) if pob_total > 0 else 0
            
            # Inmigración (nacidos extranjero)
            nac_ext = row.get("nac_extranjero", 0) * prop
            porc_inmigracion = (nac_ext / pob_total * 100) if pob_total > 0 else 0
            
            cursor.execute("""
                INSERT INTO fact_demografia 
                (barrio_id, anio, poblacion_total, poblacion_hombres, poblacion_mujeres,
                 pct_menores_15, pct_mayores_65, porc_inmigracion, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(barrio_id, anio) DO UPDATE SET
                    poblacion_total = excluded.poblacion_total,
                    poblacion_hombres = excluded.poblacion_hombres,
                    poblacion_mujeres = excluded.poblacion_mujeres,
                    pct_menores_15 = excluded.pct_menores_15,
                    pct_mayores_65 = excluded.pct_mayores_65,
                    porc_inmigracion = excluded.porc_inmigracion,
                    source = excluded.source,
                    etl_loaded_at = excluded.etl_loaded_at
            """, (
                bid, anio, int(pob_total), int(pob_hombres), int(pob_mujeres),
                round(pct_menores_15, 2), round(pct_mayores_65, 2), round(porc_inmigracion, 2),
                "idescat_emex_distribuido", datetime.now().isoformat()
            ))
            
            # Hogares Avanzado
            h_unipersonal = row.get("hogares_unipersonal", 0) * prop
            h_total = row.get("hogares_total", 0) * prop # Necesitamos total hogares
            
            # Fallback si no hay total hogares explícito
            if not h_total:
                # Sumar por dimensión
                h_total = (row.get("hogares_1_pers", 0) + row.get("hogares_2_pers", 0) + 
                           row.get("hogares_3_pers", 0) + row.get("hogares_4_pers", 0) + 
                           row.get("hogares_5_mas", 0)) * prop
            
            pct_unipersonal = (h_unipersonal / h_total * 100) if h_total > 0 else 0
            promedio_personas = (pob_total / h_total) if h_total > 0 else 0
            
            cursor.execute("""
                INSERT INTO fact_hogares_avanzado
                (barrio_id, anio, promedio_personas_por_hogar, pct_hogares_unipersonales, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(barrio_id, anio) DO UPDATE SET
                    promedio_personas_por_hogar = excluded.promedio_personas_por_hogar,
                    pct_hogares_unipersonales = excluded.pct_hogares_unipersonales,
                    source = excluded.source,
                    etl_loaded_at = excluded.etl_loaded_at
            """, (
                bid, anio, round(promedio_personas, 2), round(pct_unipersonal, 2),
                "idescat_emex_distribuido", datetime.now().isoformat()
            ))
            
            inserted += 1
            
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Éxito: {inserted} registros actualizados en fact_demografia")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()

