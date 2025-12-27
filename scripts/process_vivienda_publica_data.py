#!/usr/bin/env python3
"""
Script para procesar datos de vivienda pública y poblar fact_vivienda_publica.

Fuentes:
- IDESCAT: Datos a nivel municipal (Barcelona)
- Open Data BCN: Datos de habitatge

Este script:
1. Lee datos municipales de IDESCAT
2. Distribuye proporcionalmente por barrio usando población o renta como peso
3. Complementa con datos de Open Data BCN si disponibles
4. Inserta datos en fact_vivienda_publica

IMPORTANTE: Los datos de IDESCAT son estimaciones distribuidas proporcionalmente.
Documentar claramente en la BD que son estimaciones, no datos reales por barrio.

Uso:
    python scripts/process_vivienda_publica_data.py
"""

import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional
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


def load_idescat_data(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de datos IDESCAT.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los datos municipales.
    """
    logger.info(f"Cargando datos IDESCAT: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Registros cargados: {len(df)}")
    return df


def get_barrios_with_weights(conn: sqlite3.Connection, weight_type: str = "poblacion") -> pd.DataFrame:
    """
    Obtiene los barrios con sus pesos para distribución proporcional.
    
    Args:
        conn: Conexión a la base de datos.
        weight_type: Tipo de peso ('poblacion' o 'renta').
    
    Returns:
        DataFrame con barrio_id, barrio_nombre, peso.
    """
    if weight_type == "poblacion":
        # Usar población total del último año disponible
        query = """
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            COALESCE(MAX(d.poblacion_total), 0) as peso
        FROM dim_barrios db
        LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id
        GROUP BY db.barrio_id, db.barrio_nombre
        HAVING peso > 0
        ORDER BY db.barrio_id
        """
    else:  # renta
        # Usar renta mediana del último año disponible
        query = """
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            COALESCE(MAX(r.renta_mediana), 0) as peso
        FROM dim_barrios db
        LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id
        GROUP BY db.barrio_id, db.barrio_nombre
        HAVING peso > 0
        ORDER BY db.barrio_id
        """
    
    df = pd.read_sql_query(query, conn)
    logger.info(f"Barrios con pesos ({weight_type}): {len(df)}")
    logger.info(f"Peso total: {df['peso'].sum()}")
    return df


def distribute_municipal_to_barrios(
    municipal_value: float,
    barrios_df: pd.DataFrame,
    weight_column: str = "peso"
) -> pd.Series:
    """
    Distribuye un valor municipal proporcionalmente por barrios.
    
    Args:
        municipal_value: Valor total a nivel municipal.
        barrios_df: DataFrame con barrios y pesos.
        weight_column: Nombre de la columna con pesos.
    
    Returns:
        Series con valores distribuidos por barrio.
    """
    if barrios_df.empty:
        logger.warning("DataFrame de barrios vacío")
        return pd.Series(dtype=float)
    
    total_weight = barrios_df[weight_column].sum()
    
    if total_weight == 0:
        logger.warning("Peso total es 0, distribuyendo uniformemente")
        # Distribución uniforme como fallback
        n_barrios = len(barrios_df)
        return pd.Series([municipal_value / n_barrios] * n_barrios, index=barrios_df.index)
    
    # Distribución proporcional
    proportions = barrios_df[weight_column] / total_weight
    distributed = municipal_value * proportions
    
    return distributed


def process_idescat_data(
    df_idescat: pd.DataFrame,
    barrios_df: pd.DataFrame,
    anio: int
) -> pd.DataFrame:
    """
    Procesa datos IDESCAT y los distribuye por barrios.
    
    Args:
        df_idescat: DataFrame con datos municipales de IDESCAT.
        barrios_df: DataFrame con barrios y pesos.
        anio: Año de los datos.
    
    Returns:
        DataFrame con datos distribuidos por barrio.
    """
    logger.info("Procesando datos IDESCAT y distribuyendo por barrios...")
    
    results = []
    
    # Buscar columnas relevantes en los datos IDESCAT
    # Estas pueden variar según la estructura de la API
    renta_col = None
    contratos_col = None
    fianzas_col = None
    
    for col in df_idescat.columns:
        col_lower = col.lower()
        if "renta" in col_lower or "alquiler" in col_lower:
            renta_col = col
        elif "contrato" in col_lower:
            contratos_col = col
        elif "fianza" in col_lower:
            fianzas_col = col
    
    # Extraer valores municipales
    if df_idescat.empty:
        logger.warning("DataFrame IDESCAT vacío")
        return pd.DataFrame()
    
    # Asumir que hay un solo registro municipal (Barcelona)
    row = df_idescat.iloc[0]
    
    renta_media = row[renta_col] if renta_col and renta_col in row.index else None
    contratos = row[contratos_col] if contratos_col and contratos_col in row.index else None
    fianzas = row[fianzas_col] if fianzas_col and fianzas_col in row.index else None
    
    # Distribuir por barrios
    for _, barrio_row in barrios_df.iterrows():
        barrio_id = int(barrio_row["barrio_id"])
        peso = barrio_row["peso"]
        
        # Calcular proporción
        total_peso = barrios_df["peso"].sum()
        if total_peso > 0:
            proporcion = peso / total_peso
        else:
            proporcion = 1.0 / len(barrios_df)
        
        results.append({
            "barrio_id": barrio_id,
            "anio": anio,
            "renta_media_mensual_alquiler": round(renta_media * proporcion, 2) if renta_media else None,
            "contratos_alquiler_nuevos": int(contratos * proporcion) if contratos else None,
            "fianzas_depositadas_euros": round(fianzas * proporcion, 2) if fianzas else None,
            "viviendas_proteccion_oficial": None,  # TODO: añadir si hay datos
        })
    
    df_result = pd.DataFrame(results)
    logger.info(f"Datos distribuidos para {len(df_result)} barrios")
    logger.warning("⚠️  IMPORTANTE: Estos son valores estimados por distribución proporcional, no datos reales por barrio")
    
    return df_result


def insert_into_fact_vivienda_publica(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame
) -> int:
    """
    Inserta los datos en fact_vivienda_publica.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame con datos por barrio.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_vivienda_publica...")
    
    cursor = conn.cursor()
    inserted = 0
    
    # Eliminar datos del año actual para evitar duplicados
    anio = df_agg["anio"].iloc[0] if not df_agg.empty else datetime.now().year
    
    cursor.execute("DELETE FROM fact_vivienda_publica WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_vivienda_publica
                (barrio_id, anio, contratos_alquiler_nuevos, fianzas_depositadas_euros,
                 renta_media_mensual_alquiler, viviendas_proteccion_oficial, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    row["contratos_alquiler_nuevos"],
                    row["fianzas_depositadas_euros"],
                    row["renta_media_mensual_alquiler"],
                    row["viviendas_proteccion_oficial"],
                    "idescat_distribuido",  # Marcar como distribuido
                    datetime.now().isoformat(),
                )
            )
            inserted += 1
        except sqlite3.Error as e:
            logger.error(f"Error insertando barrio {row['barrio_id']}: {e}")
    
    conn.commit()
    logger.info(f"Registros insertados: {inserted}")
    return inserted


def validate_data(conn: sqlite3.Connection, anio: int) -> None:
    """
    Valida los datos insertados.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de los datos.
    """
    logger.info("Validando datos insertados...")
    
    query = """
    SELECT 
        COUNT(*) as barrios,
        SUM(contratos_alquiler_nuevos) as total_contratos,
        AVG(renta_media_mensual_alquiler) as avg_renta
    FROM fact_vivienda_publica
    WHERE anio = ?
    """
    result = pd.read_sql_query(query, conn, params=[anio])
    
    if not result.empty:
        row = result.iloc[0]
        logger.info(f"\nResumen ({anio}):")
        logger.info(f"  Barrios con datos: {int(row['barrios'])}")
        if row['total_contratos']:
            logger.info(f"  Total contratos (estimado): {int(row['total_contratos'])}")
        if row['avg_renta']:
            logger.info(f"  Renta media (estimada): {row['avg_renta']:.2f} €")
        logger.warning("⚠️  Recordar: Estos son valores estimados por distribución proporcional")


def main() -> int:
    """Función principal."""
    # Buscar archivo CSV más reciente de IDESCAT
    vivienda_dir = PROJECT_ROOT / "data" / "raw" / "viviendapublica"
    csv_files = list(vivienda_dir.glob("*idescat*.csv")) if vivienda_dir.exists() else []
    
    if not csv_files:
        logger.error(f"No se encontraron archivos CSV en {vivienda_dir}")
        logger.info("Ejecutar primero: python -c 'from src.extraction.vivienda_publica_extractor import ViviendaPublicaExtractor; e = ViviendaPublicaExtractor(); e.extract_all(2024)'")
        return 1
    
    csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar datos
        df_idescat = load_idescat_data(csv_path)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener barrios con pesos (usar población como default)
        barrios_df = get_barrios_with_weights(conn, weight_type="poblacion")
        
        if barrios_df.empty:
            logger.error("No hay barrios con pesos en la BD")
            conn.close()
            return 1
        
        # Procesar y distribuir
        anio = datetime.now().year
        df_agg = process_idescat_data(df_idescat, barrios_df, anio)
        
        if df_agg.empty:
            logger.error("No se generaron datos agregados")
            conn.close()
            return 1
        
        # Insertar en BD
        inserted = insert_into_fact_vivienda_publica(conn, df_agg)
        
        # Validar
        validate_data(conn, anio)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} barrios actualizados")
        logger.warning("⚠️  IMPORTANTE: Los datos son estimaciones por distribución proporcional")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

