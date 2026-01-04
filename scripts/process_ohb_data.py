#!/usr/bin/env python3
"""
Script para procesar datos del OHB y poblar fact_vivienda_contexto_metropolitano.

Este script:
1. Usa OHBExtractor para obtener y limpiar datos.
2. Inserta los datos en la tabla fact_vivienda_contexto_metropolitano.
"""

import logging
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

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

def main():
    try:
        from src.extraction.ohb_extractor import OHBExtractor
        extractor = OHBExtractor()
        
        # 1. Régimen de tenencia
        logger.info("Procesando Régimen de Tenencia...")
        df_tenencia = extractor.extract_regimen_tenencia()
        
        # 2. Concentración de propiedad (Tipo y Tamaño)
        logger.info("Procesando Concentración de Propiedad...")
        df_tipo = extractor.extract_tipo_propietario()
        df_tamano = extractor.extract_tamano_propietario()
        
        # Consolidar todos los datos por ámbito y año
        # Empezamos con tenencia
        final_df = df_tenencia if not df_tenencia.empty else pd.DataFrame(columns=['ambito', 'anio_inicio', 'anio_fin'])
        
        # Merge con Tipo Propietario
        if not df_tipo.empty:
            if final_df.empty:
                final_df = df_tipo
            else:
                # Asegurar que las columnas de unión existen
                cols_to_check = ['ambito', 'anio_inicio', 'anio_fin']
                if all(c in df_tipo.columns for c in cols_to_check) and all(c in final_df.columns for c in cols_to_check):
                    final_df = final_df.merge(df_tipo, on=cols_to_check, how='outer')
                else:
                    logger.warning(f"Columnas de unión faltantes en df_tipo: {df_tipo.columns.tolist()}")
                    # Fallback: concatenar si no se puede mergear
                    final_df = pd.concat([final_df, df_tipo], ignore_index=True)
                
        # Merge con Tamaño Propietario
        if not df_tamano.empty:
            if final_df.empty:
                final_df = df_tamano
            else:
                cols_to_check = ['ambito', 'anio_inicio', 'anio_fin']
                if all(c in df_tamano.columns for c in cols_to_check) and all(c in final_df.columns for c in cols_to_check):
                    final_df = final_df.merge(df_tamano, on=cols_to_check, how='outer')
                else:
                    logger.warning(f"Columnas de unión faltantes en df_tamano: {df_tamano.columns.tolist()}")
                    final_df = pd.concat([final_df, df_tamano], ignore_index=True)
        
        if final_df.empty:
            logger.warning("No se pudieron obtener datos del OHB")
            return 1
            
        conn = get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        for _, row in final_df.iterrows():
            ambito = str(row['ambito']).strip()
            if pd.isna(row['anio_inicio']):
                continue
                
            cursor.execute("""
                INSERT INTO fact_vivienda_contexto_metropolitano
                (ambito, anio_inicio, anio_fin, 
                 propiedad_total, propiedad_pagada, propiedad_pendiente, 
                 alquiler_total, alquiler_mercado, alquiler_social, cesion_gratuita,
                 pct_persona_fisica, pct_persona_juridica, pct_grandes_tenedores,
                 source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ambito, anio_inicio, anio_fin) DO UPDATE SET
                    propiedad_total = COALESCE(excluded.propiedad_total, propiedad_total),
                    propiedad_pagada = COALESCE(excluded.propiedad_pagada, propiedad_pagada),
                    propiedad_pendiente = COALESCE(excluded.propiedad_pendiente, propiedad_pendiente),
                    alquiler_total = COALESCE(excluded.alquiler_total, alquiler_total),
                    alquiler_mercado = COALESCE(excluded.alquiler_mercado, alquiler_mercado),
                    alquiler_social = COALESCE(excluded.alquiler_social, alquiler_social),
                    cesion_gratuita = COALESCE(excluded.cesion_gratuita, cesion_gratuita),
                    pct_persona_fisica = COALESCE(excluded.pct_persona_fisica, pct_persona_fisica),
                    pct_persona_juridica = COALESCE(excluded.pct_persona_juridica, pct_persona_juridica),
                    pct_grandes_tenedores = COALESCE(excluded.pct_grandes_tenedores, pct_grandes_tenedores),
                    source = excluded.source,
                    etl_loaded_at = excluded.etl_loaded_at
            """, (
                ambito, int(row['anio_inicio']), int(row['anio_fin']),
                row.get('propiedad_total'), row.get('propiedad_pagada'),
                row.get('propiedad_pendiente'), row.get('alquiler_total'),
                row.get('alquiler_mercado'), row.get('alquiler_social'),
                row.get('cesion_gratuita'),
                row.get('pct_persona_fisica'), row.get('pct_persona_juridica'),
                row.get('pct_grandes_tenedores'),
                "OHB_Excel_Consolidated", datetime.now().isoformat()
            ))
            inserted += 1
            
        conn.commit()
        conn.close()
        logger.info(f"✅ Éxito: {inserted} registros cargados/actualizados en fact_vivienda_contexto_metropolitano")
        return 0
        
    except Exception as e:
        logger.error(f"Error en el procesamiento de OHB: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()

