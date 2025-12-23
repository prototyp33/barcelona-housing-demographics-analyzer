#!/usr/bin/env python3
"""
Script para calcular datos de regulación de alquileres para fact_regulacion.

Criterios para zona tensionada (Ley 11/2020 de Cataluña):
1. Precio medio de alquiler > 30% de la renta media del barrio
2. Incremento de precios > 3% anual sostenido
3. Alta presión turística (>5% viviendas en Airbnb)

Este script calcula el índice de referencia basado en:
- Precios de alquiler reales del barrio
- Renta mediana de los hogares
- Presión turística (Airbnb)

Uso:
    python scripts/calculate_regulacion_data.py
"""

import logging
import sqlite3
import sys
from pathlib import Path
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


def get_precios_alquiler(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene precios de alquiler por barrio y año.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con precios de alquiler.
    """
    query = """
    SELECT 
        barrio_id,
        anio,
        AVG(precio_mes_alquiler) as precio_alquiler
    FROM fact_precios
    WHERE precio_mes_alquiler IS NOT NULL
    GROUP BY barrio_id, anio
    """
    return pd.read_sql_query(query, conn)


def get_renta_barrios(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene renta mediana por barrio y año.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con renta mediana.
    """
    query = """
    SELECT 
        barrio_id,
        anio,
        renta_mediana
    FROM fact_renta
    WHERE renta_mediana IS NOT NULL
    """
    return pd.read_sql_query(query, conn)


def get_presion_turistica(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene presión turística por barrio.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con datos de Airbnb.
    """
    query = """
    SELECT 
        barrio_id,
        anio,
        num_listings_airbnb,
        pct_entire_home
    FROM fact_presion_turistica
    """
    return pd.read_sql_query(query, conn)


def get_poblacion_barrios(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene población y hogares por barrio.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con datos demográficos.
    """
    query = """
    SELECT 
        barrio_id,
        anio,
        hogares_totales,
        poblacion_total
    FROM fact_demografia
    WHERE hogares_totales IS NOT NULL
    """
    return pd.read_sql_query(query, conn)


def calculate_zona_tensionada(
    precio_alquiler: float,
    renta_mensual: float,
    pct_airbnb: float,
    incremento_precio: float
) -> tuple[bool, str]:
    """
    Determina si un barrio es zona tensionada.
    
    Criterios:
    1. Carga de alquiler > 30% de la renta
    2. Incremento de precios > 3% anual
    3. Alta presión turística (>5% viviendas Airbnb)
    
    Args:
        precio_alquiler: Precio mensual de alquiler.
        renta_mensual: Renta mensual del hogar.
        pct_airbnb: Porcentaje de viviendas en Airbnb.
        incremento_precio: Incremento anual de precio (%).
    
    Returns:
        Tupla (es_tensionada, nivel_tension).
    """
    if renta_mensual <= 0:
        return False, "sin_datos"
    
    carga_alquiler = (precio_alquiler / renta_mensual) * 100
    
    # Contar criterios cumplidos
    criterios = 0
    
    if carga_alquiler > 30:
        criterios += 1
    if incremento_precio > 3:
        criterios += 1
    if pct_airbnb > 5:
        criterios += 1
    
    # Determinar nivel de tensión
    if criterios >= 2:
        return True, "alta"
    elif criterios == 1:
        if carga_alquiler > 25:
            return True, "media"
        return False, "baja"
    else:
        return False, "baja"


def calculate_indice_referencia(
    precio_alquiler: float,
    renta_mensual: float,
    zona_tensionada: bool
) -> float:
    """
    Calcula el índice de referencia de alquiler.
    
    El índice representa el precio recomendado €/m² basado en:
    - Precio actual del mercado
    - Capacidad de pago (30% renta)
    - Si es zona tensionada (se aplica reducción)
    
    Args:
        precio_alquiler: Precio mensual de alquiler.
        renta_mensual: Renta mensual del hogar.
        zona_tensionada: Si el barrio es zona tensionada.
    
    Returns:
        Índice de referencia (€/m²).
    """
    if renta_mensual <= 0:
        return precio_alquiler / 70  # Asumir 70m² promedio
    
    # Precio máximo recomendado (30% de renta mensual)
    precio_max_recomendado = renta_mensual * 0.30
    
    # Si es zona tensionada, el índice es el menor entre mercado y recomendado
    if zona_tensionada:
        indice = min(precio_alquiler, precio_max_recomendado) / 70
    else:
        # Media ponderada
        indice = (precio_alquiler * 0.7 + precio_max_recomendado * 0.3) / 70
    
    return round(indice, 2)


def process_regulacion(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Procesa y calcula todos los indicadores de regulación.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con datos de regulación por barrio y año.
    """
    logger.info("Cargando datos...")
    
    # Cargar datos
    df_precios = get_precios_alquiler(conn)
    df_renta = get_renta_barrios(conn)
    df_turismo = get_presion_turistica(conn)
    df_demo = get_poblacion_barrios(conn)
    
    logger.info(f"Precios: {len(df_precios)}, Renta: {len(df_renta)}, "
               f"Turismo: {len(df_turismo)}, Demo: {len(df_demo)}")
    
    # Obtener todos los barrios y años
    query = "SELECT DISTINCT barrio_id FROM dim_barrios"
    barrios = pd.read_sql_query(query, conn)["barrio_id"].tolist()
    
    # Años a procesar (últimos 5 años)
    anio_actual = datetime.now().year
    anios = list(range(anio_actual - 4, anio_actual + 1))
    
    results = []
    
    for barrio_id in barrios:
        for anio in anios:
            # Obtener precio de alquiler
            precio_row = df_precios[
                (df_precios["barrio_id"] == barrio_id) & 
                (df_precios["anio"] == anio)
            ]
            precio_alquiler = precio_row["precio_alquiler"].values[0] if len(precio_row) > 0 else None
            
            # Obtener renta
            renta_row = df_renta[
                (df_renta["barrio_id"] == barrio_id) & 
                (df_renta["anio"] == anio)
            ]
            renta_anual = renta_row["renta_mediana"].values[0] if len(renta_row) > 0 else None
            renta_mensual = renta_anual / 12 if renta_anual else None
            
            # Obtener turismo
            turismo_row = df_turismo[
                (df_turismo["barrio_id"] == barrio_id) & 
                (df_turismo["anio"] == anio)
            ]
            if len(turismo_row) == 0:
                # Usar año más reciente
                turismo_row = df_turismo[df_turismo["barrio_id"] == barrio_id]
            pct_airbnb = turismo_row["pct_entire_home"].values[0] if len(turismo_row) > 0 else 0
            num_listings = turismo_row["num_listings_airbnb"].values[0] if len(turismo_row) > 0 else 0
            
            # Calcular incremento de precio (comparar con año anterior)
            precio_anterior_row = df_precios[
                (df_precios["barrio_id"] == barrio_id) & 
                (df_precios["anio"] == anio - 1)
            ]
            if len(precio_anterior_row) > 0 and precio_alquiler:
                precio_anterior = precio_anterior_row["precio_alquiler"].values[0]
                incremento = ((precio_alquiler - precio_anterior) / precio_anterior) * 100 if precio_anterior > 0 else 0
            else:
                incremento = 0
            
            # Si no hay precio de alquiler, saltar
            if precio_alquiler is None or pd.isna(precio_alquiler):
                continue
            
            # Calcular zona tensionada
            zona_tensionada, nivel_tension = calculate_zona_tensionada(
                precio_alquiler,
                renta_mensual if renta_mensual else precio_alquiler * 3,  # Fallback
                pct_airbnb,
                incremento
            )
            
            # Calcular índice de referencia
            indice = calculate_indice_referencia(
                precio_alquiler,
                renta_mensual if renta_mensual else precio_alquiler * 3,
                zona_tensionada
            )
            
            results.append({
                "barrio_id": barrio_id,
                "anio": anio,
                "indice_referencia_alquiler": indice,
                "zona_tensionada": 1 if zona_tensionada else 0,
                "nivel_tension": nivel_tension,
                "num_licencias_vut": int(num_listings) if num_listings else 0,
                "derecho_tanteo": 1 if zona_tensionada and nivel_tension == "alta" else 0,
            })
    
    df_result = pd.DataFrame(results)
    logger.info(f"Registros calculados: {len(df_result)}")
    return df_result


def insert_into_fact_regulacion(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """
    Inserta los datos en fact_regulacion.
    
    Args:
        conn: Conexión a la base de datos.
        df: DataFrame con datos de regulación.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_regulacion...")
    
    cursor = conn.cursor()
    
    # Eliminar datos existentes para recalcular
    cursor.execute("DELETE FROM fact_regulacion")
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute(
                """
                INSERT INTO fact_regulacion
                (barrio_id, anio, indice_referencia_alquiler, zona_tensionada, 
                 nivel_tension, num_licencias_vut, derecho_tanteo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    row["indice_referencia_alquiler"],
                    int(row["zona_tensionada"]),
                    row["nivel_tension"],
                    int(row["num_licencias_vut"]),
                    int(row["derecho_tanteo"]),
                )
            )
            inserted += 1
        except sqlite3.Error as e:
            logger.error(f"Error insertando: {e}")
    
    conn.commit()
    logger.info(f"Registros insertados: {inserted}")
    return inserted


def validate_data(conn: sqlite3.Connection) -> None:
    """
    Valida los datos insertados.
    
    Args:
        conn: Conexión a la base de datos.
    """
    logger.info("Validando datos...")
    
    query = """
    SELECT 
        anio,
        COUNT(*) as barrios,
        SUM(zona_tensionada) as zonas_tensionadas,
        AVG(indice_referencia_alquiler) as avg_indice,
        SUM(num_licencias_vut) as total_vut
    FROM fact_regulacion
    GROUP BY anio
    ORDER BY anio DESC
    """
    df = pd.read_sql_query(query, conn)
    
    logger.info("\nResumen por año:")
    for _, row in df.iterrows():
        logger.info(f"  {int(row['anio'])}: {int(row['barrios'])} barrios, "
                   f"{int(row['zonas_tensionadas'])} tensionadas, "
                   f"índice avg: {row['avg_indice']:.2f} €/m²")
    
    # Resumen por nivel de tensión
    query = """
    SELECT 
        nivel_tension,
        COUNT(DISTINCT barrio_id) as barrios
    FROM fact_regulacion
    WHERE anio = (SELECT MAX(anio) FROM fact_regulacion)
    GROUP BY nivel_tension
    """
    df_nivel = pd.read_sql_query(query, conn)
    
    logger.info("\nNivel de tensión (último año):")
    for _, row in df_nivel.iterrows():
        logger.info(f"  {row['nivel_tension']}: {row['barrios']} barrios")


def main() -> int:
    """Función principal."""
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Procesar datos
        df_regulacion = process_regulacion(conn)
        
        # Insertar en BD
        inserted = insert_into_fact_regulacion(conn, df_regulacion)
        
        # Validar
        validate_data(conn)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} registros")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

