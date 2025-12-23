#!/usr/bin/env python3
"""
Script para procesar datos de ruido de Open Data BCN y poblar fact_ruido.

Este script:
1. Lee el CSV de población expuesta a ruido por barrios (2022)
2. Calcula métricas agregadas por barrio
3. Inserta los datos en la tabla fact_ruido

Uso:
    python scripts/process_ruido_data.py
"""

import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def load_ruido_csv(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de ruido por barrios.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los datos de ruido.
    """
    logger.info(f"Cargando CSV: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Registros cargados: {len(df)}")
    logger.info(f"Columnas: {df.columns.tolist()}")
    return df


def get_barrio_mapping(conn: sqlite3.Connection) -> Dict[int, int]:
    """
    Obtiene el mapeo de código de barrio a barrio_id.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        Diccionario {codi_barri_int: barrio_id}.
    """
    query = "SELECT barrio_id, codi_barri FROM dim_barrios"
    df = pd.read_sql_query(query, conn)
    # Convertir codi_barri de string ("01", "02") a int (1, 2)
    return {int(row["codi_barri"]): row["barrio_id"] for _, row in df.iterrows()}


def calculate_noise_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula métricas de ruido agregadas por barrio.
    
    Métricas calculadas:
    - nivel_lden_medio: Promedio ponderado del Lden (día-tarde-noche)
    - nivel_ld_dia: Promedio ponderado del ruido diurno
    - nivel_ln_noche: Promedio ponderado del ruido nocturno
    - pct_poblacion_expuesta_65db: % de población expuesta a >=65 dB
    
    Args:
        df: DataFrame con datos crudos de ruido.
    
    Returns:
        DataFrame con métricas por barrio.
    """
    logger.info("Calculando métricas de ruido por barrio...")
    
    # Diccionario para convertir rangos de ruido a valores numéricos (punto medio)
    noise_ranges = {
        "<35 dB(A)": 32.5,
        "35-40 dB(A)": 37.5,
        "40-45 dB(A)": 42.5,
        "45-50 dB(A)": 47.5,
        "50-55 dB(A)": 52.5,
        "55-60 dB(A)": 57.5,
        "60-65 dB(A)": 62.5,
        "65-70 dB(A)": 67.5,
        "70-75 dB(A)": 72.5,
        "75-80 dB(A)": 77.5,
        ">=80 dB(A)": 82.5,
    }
    
    # Añadir valor numérico del rango
    df = df.copy()
    df["noise_value"] = df["rang"].map(noise_ranges)
    
    # Filtrar solo fuentes de ruido "Total" o tráfico viario (fuente principal)
    # Usamos "Trànsit viari" como proxy de ruido total urbano
    df_traffic = df[df["font_soroll"] == "Trànsit viari"].copy()
    
    results = []
    
    for barri_code, barri_group in df_traffic.groupby("barri"):
        barri_name = barri_group["nom_barri"].iloc[0]
        
        # Calcular promedio ponderado para cada período
        # Día
        df_dia = barri_group[barri_group["periode_horari"] == "Dia"]
        if not df_dia.empty:
            nivel_ld = (df_dia["noise_value"] * df_dia["percentatge_poblacio_exposada"]).sum()
        else:
            nivel_ld = None
        
        # Noche
        df_nit = barri_group[barri_group["periode_horari"] == "Nit"]
        if not df_nit.empty:
            nivel_ln = (df_nit["noise_value"] * df_nit["percentatge_poblacio_exposada"]).sum()
        else:
            nivel_ln = None
        
        # Lden (calculado como promedio ponderado de los tres períodos)
        # Usamos el período "Vespre" (tarde) como aproximación
        df_vespre = barri_group[barri_group["periode_horari"] == "Vespre"]
        if not df_vespre.empty:
            nivel_le = (df_vespre["noise_value"] * df_vespre["percentatge_poblacio_exposada"]).sum()
        else:
            nivel_le = nivel_ld if nivel_ld else 0
        
        # Fórmula simplificada de Lden (penaliza tarde y noche)
        if nivel_ld is not None and nivel_ln is not None:
            nivel_lden = nivel_ld  # Simplificación: usamos Ld como base
        else:
            nivel_lden = None
        
        # Población expuesta a >=65 dB (rangos 65-70, 70-75, 75-80, >=80)
        high_noise_ranges = ["65-70 dB(A)", "70-75 dB(A)", "75-80 dB(A)", ">=80 dB(A)"]
        df_high_noise = df_dia[df_dia["rang"].isin(high_noise_ranges)]
        pct_65db = df_high_noise["percentatge_poblacio_exposada"].sum() if not df_high_noise.empty else 0
        
        results.append({
            "barri": barri_code,
            "nom_barri": barri_name,
            "nivel_lden_medio": round(nivel_lden, 2) if nivel_lden else None,
            "nivel_ld_dia": round(nivel_ld, 2) if nivel_ld else None,
            "nivel_ln_noche": round(nivel_ln, 2) if nivel_ln else None,
            "pct_poblacion_expuesta_65db": round(pct_65db * 100, 2),  # Convertir a porcentaje
        })
    
    df_metrics = pd.DataFrame(results)
    logger.info(f"Métricas calculadas para {len(df_metrics)} barrios")
    return df_metrics


def insert_into_fact_ruido(
    conn: sqlite3.Connection,
    df_metrics: pd.DataFrame,
    barrio_mapping: Dict[str, int],
    anio: int = 2022
) -> int:
    """
    Inserta los datos de ruido en la tabla fact_ruido.
    
    Args:
        conn: Conexión a la base de datos.
        df_metrics: DataFrame con métricas de ruido por barrio.
        barrio_mapping: Diccionario de mapeo codi_barri -> barrio_id.
        anio: Año de los datos.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_ruido...")
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for _, row in df_metrics.iterrows():
        barri_code = int(row["barri"])
        barrio_id = barrio_mapping.get(barri_code)
        
        if barrio_id is None:
            logger.warning(f"Barrio no encontrado: {barri_code} ({row['nom_barri']})")
            skipped += 1
            continue
        
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_ruido
                (barrio_id, anio, nivel_lden_medio, nivel_ld_dia, nivel_ln_noche, pct_poblacion_expuesta_65db)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    barrio_id,
                    anio,
                    row["nivel_lden_medio"],
                    row["nivel_ld_dia"],
                    row["nivel_ln_noche"],
                    row["pct_poblacion_expuesta_65db"],
                )
            )
            inserted += 1
        except sqlite3.Error as e:
            logger.error(f"Error insertando barrio {barri_code}: {e}")
            skipped += 1
    
    conn.commit()
    logger.info(f"Insertados: {inserted}, Omitidos: {skipped}")
    return inserted


def validate_data(conn: sqlite3.Connection, anio: int = 2022) -> None:
    """
    Valida los datos insertados en fact_ruido.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de los datos.
    """
    logger.info("Validando datos insertados...")
    
    # Contar registros
    query = "SELECT COUNT(*) as count FROM fact_ruido WHERE anio = ?"
    df = pd.read_sql_query(query, conn, params=[anio])
    count = df["count"].iloc[0]
    logger.info(f"Registros en fact_ruido para {anio}: {count}")
    
    # Estadísticas descriptivas
    query = """
    SELECT 
        MIN(nivel_lden_medio) as min_lden,
        MAX(nivel_lden_medio) as max_lden,
        AVG(nivel_lden_medio) as avg_lden,
        MIN(pct_poblacion_expuesta_65db) as min_pct_65,
        MAX(pct_poblacion_expuesta_65db) as max_pct_65,
        AVG(pct_poblacion_expuesta_65db) as avg_pct_65
    FROM fact_ruido
    WHERE anio = ?
    """
    df = pd.read_sql_query(query, conn, params=[anio])
    
    logger.info("Estadísticas de ruido:")
    logger.info(f"  Lden: min={df['min_lden'].iloc[0]:.1f}, max={df['max_lden'].iloc[0]:.1f}, avg={df['avg_lden'].iloc[0]:.1f}")
    logger.info(f"  % Expuesta >65dB: min={df['min_pct_65'].iloc[0]:.1f}%, max={df['max_pct_65'].iloc[0]:.1f}%, avg={df['avg_pct_65'].iloc[0]:.1f}%")
    
    # Top 5 barrios más ruidosos
    query = """
    SELECT 
        b.barrio_nombre,
        r.nivel_lden_medio,
        r.pct_poblacion_expuesta_65db
    FROM fact_ruido r
    JOIN dim_barrios b ON r.barrio_id = b.barrio_id
    WHERE r.anio = ?
    ORDER BY r.pct_poblacion_expuesta_65db DESC
    LIMIT 5
    """
    df = pd.read_sql_query(query, conn, params=[anio])
    logger.info("\nTop 5 barrios con más población expuesta a ruido alto:")
    for _, row in df.iterrows():
        logger.info(f"  - {row['barrio_nombre']}: {row['pct_poblacion_expuesta_65db']:.1f}% expuesta a >65dB")


def main() -> int:
    """Función principal."""
    # Rutas
    csv_path = PROJECT_ROOT / "data" / "raw" / "ruido" / "2022_poblacio_exposada_barris.csv"
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not csv_path.exists():
        logger.error(f"CSV no encontrado: {csv_path}")
        return 1
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar CSV
        df = load_ruido_csv(csv_path)
        
        # Calcular métricas
        df_metrics = calculate_noise_metrics(df)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener mapeo de barrios
        barrio_mapping = get_barrio_mapping(conn)
        logger.info(f"Mapeo de barrios cargado: {len(barrio_mapping)} barrios")
        
        # Insertar datos
        inserted = insert_into_fact_ruido(conn, df_metrics, barrio_mapping, anio=2022)
        
        # Validar
        validate_data(conn, anio=2022)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} registros insertados")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

