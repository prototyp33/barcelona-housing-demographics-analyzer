#!/usr/bin/env python3
"""
Script para procesar datos de criminalidad de Mossos d'Esquadra y poblar fact_seguridad.

Fuente: Portal de Dades de Barcelona / Dades Obertes Catalunya
URL: https://analisi.transparenciacatalunya.cat/Seguretat/Fets-penals-coneguts-fets-coneguts-resolts-i-deten/qnyt-emjc

Los datos están a nivel de Área Básica Policial (ABP), que corresponden
a los distritos de Barcelona. Este script:
1. Filtra datos de distritos de Barcelona
2. Agrega por distrito y año
3. Calcula tasas de criminalidad por 1000 habitantes
4. Inserta datos en fact_seguridad distribuyéndolos entre barrios

Uso:
    python scripts/process_seguridad_data.py
"""

import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

# Mapeo de ABP (Área Básica Policial) a código de distrito
ABP_TO_DISTRITO = {
    "ABP Ciutat Vella": 1,
    "ABP Eixample": 2,
    "ABP Sants-Montjuïc": 3,
    "ABP Les Corts": 4,
    "ABP Sarrià-Sant Gervasi": 5,
    "ABP Gràcia": 6,
    "ABP Horta-Guinardó": 7,
    "ABP Nou Barris": 8,
    "ABP Sant Andreu": 9,
    "ABP Sant Martí": 10,
}

# Categorías de delitos según el código penal
DELITOS_PATRIMONIO = [
    "Delictes contra el patrimoni i contra l'ordre socioeconòmic",
    "Furt",
    "Robatori amb força",
    "Robatori amb violència i/o intimidació",
    "Estafes",
    "Danys",
]

DELITOS_SEGURIDAD_PERSONAL = [
    "De les lesions",
    "De l'homicidi i les seves formes",
    "Delictes contra la llibertat",
    "Delictes contra la llibertat i la indemnitat sexuals",
    "De les tortures i altres delictes contra la integritat moral",
]


def load_criminalidad_csv(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de criminalidad de Mossos.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los datos de criminalidad.
    """
    logger.info(f"Cargando CSV: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Registros cargados: {len(df)}")
    logger.info(f"Columnas: {df.columns.tolist()}")
    return df


def filter_barcelona_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra solo datos de los distritos de Barcelona.
    
    Args:
        df: DataFrame con todos los datos de criminalidad.
    
    Returns:
        DataFrame filtrado solo con distritos de Barcelona.
    """
    abp_list = list(ABP_TO_DISTRITO.keys())
    df_bcn = df[df["rea_b_sica_policial_abp"].isin(abp_list)].copy()
    logger.info(f"Registros filtrados para Barcelona: {len(df_bcn)}")
    return df_bcn


def aggregate_by_distrito_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega datos por distrito y año.
    
    Calcula:
    - Total de delitos conocidos
    - Delitos contra el patrimonio
    - Delitos contra la seguridad personal
    
    Args:
        df: DataFrame filtrado con datos de Barcelona.
    
    Returns:
        DataFrame agregado por distrito y año.
    """
    logger.info("Agregando datos por distrito y año...")
    
    results = []
    
    for abp, distrito_code in ABP_TO_DISTRITO.items():
        df_abp = df[df["rea_b_sica_policial_abp"] == abp]
        
        for any_val in df_abp["any"].unique():
            df_year = df_abp[df_abp["any"] == any_val]
            
            # Total delitos
            total_delitos = df_year["coneguts"].sum()
            
            # Delitos contra el patrimonio
            df_patrimonio = df_year[
                df_year["t_tol_codi_penal"].isin(DELITOS_PATRIMONIO) |
                df_year["tipus_de_fet"].isin(DELITOS_PATRIMONIO)
            ]
            delitos_patrimonio = df_patrimonio["coneguts"].sum()
            
            # Delitos contra seguridad personal
            df_seguridad = df_year[
                df_year["t_tol_codi_penal"].isin(DELITOS_SEGURIDAD_PERSONAL)
            ]
            delitos_seguridad = df_seguridad["coneguts"].sum()
            
            results.append({
                "distrito_code": distrito_code,
                "distrito_nombre": abp.replace("ABP ", ""),
                "anio": int(any_val),
                "total_delitos": int(total_delitos),
                "delitos_patrimonio": int(delitos_patrimonio),
                "delitos_seguridad_personal": int(delitos_seguridad),
            })
    
    df_agg = pd.DataFrame(results)
    logger.info(f"Registros agregados: {len(df_agg)}")
    return df_agg


def get_poblacion_distrito(conn: sqlite3.Connection, anio: int) -> Dict[int, int]:
    """
    Obtiene la población por distrito para un año.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año para el que obtener población.
    
    Returns:
        Diccionario {distrito_code: poblacion}.
    """
    # Mapeo de nombre de distrito a código
    DISTRITO_TO_CODE = {
        "Ciutat Vella": 1,
        "Eixample": 2,
        "Sants-Montjuïc": 3,
        "Les Corts": 4,
        "Sarrià-Sant Gervasi": 5,
        "Gràcia": 6,
        "Horta-Guinardó": 7,
        "Nou Barris": 8,
        "Sant Andreu": 9,
        "Sant Martí": 10,
    }
    
    # Intentar con fact_demografia
    query = """
    SELECT 
        b.distrito_nombre,
        SUM(d.poblacion_total) as poblacion
    FROM fact_demografia d
    JOIN dim_barrios b ON d.barrio_id = b.barrio_id
    WHERE d.anio = ?
    GROUP BY b.distrito_nombre
    """
    try:
        df = pd.read_sql_query(query, conn, params=[anio])
        if not df.empty:
            result = {}
            for _, row in df.iterrows():
                code = DISTRITO_TO_CODE.get(row["distrito_nombre"])
                if code:
                    result[code] = int(row["poblacion"])
            if result:
                return result
    except Exception as e:
        logger.warning(f"Error obteniendo población del año {anio}: {e}")
    
    # Fallback: usar población más reciente disponible
    query = """
    SELECT 
        b.distrito_nombre,
        SUM(d.poblacion_total) as poblacion
    FROM fact_demografia d
    JOIN dim_barrios b ON d.barrio_id = b.barrio_id
    WHERE d.anio = (SELECT MAX(anio) FROM fact_demografia)
    GROUP BY b.distrito_nombre
    """
    try:
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            result = {}
            for _, row in df.iterrows():
                code = DISTRITO_TO_CODE.get(row["distrito_nombre"])
                if code:
                    result[code] = int(row["poblacion"])
            if result:
                return result
    except Exception as e:
        logger.warning(f"Error obteniendo población: {e}")
    
    # Fallback con valores aproximados de población por distrito
    return {
        1: 100000,   # Ciutat Vella
        2: 265000,   # Eixample
        3: 180000,   # Sants-Montjuïc
        4: 82000,    # Les Corts
        5: 145000,   # Sarrià-Sant Gervasi
        6: 122000,   # Gràcia
        7: 170000,   # Horta-Guinardó
        8: 168000,   # Nou Barris
        9: 148000,   # Sant Andreu
        10: 235000,  # Sant Martí
    }


def get_barrios_por_distrito(conn: sqlite3.Connection) -> Dict[int, List[int]]:
    """
    Obtiene los barrios de cada distrito.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        Diccionario {distrito_code: [barrio_id, ...]}.
    """
    # Mapeo de nombre de distrito a código
    DISTRITO_TO_CODE = {
        "Ciutat Vella": 1,
        "Eixample": 2,
        "Sants-Montjuïc": 3,
        "Les Corts": 4,
        "Sarrià-Sant Gervasi": 5,
        "Gràcia": 6,
        "Horta-Guinardó": 7,
        "Nou Barris": 8,
        "Sant Andreu": 9,
        "Sant Martí": 10,
    }
    
    query = "SELECT barrio_id, distrito_nombre FROM dim_barrios"
    df = pd.read_sql_query(query, conn)
    
    result = {i: [] for i in range(1, 11)}
    for _, row in df.iterrows():
        distrito_code = DISTRITO_TO_CODE.get(row["distrito_nombre"])
        if distrito_code:
            result[distrito_code].append(row["barrio_id"])
    
    return result


def insert_into_fact_seguridad(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame,
    barrios_por_distrito: Dict[int, List[int]]
) -> int:
    """
    Inserta los datos de seguridad en la tabla fact_seguridad.
    
    Los datos están a nivel de distrito, pero los distribuimos proporcionalmente
    entre los barrios del distrito.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame agregado por distrito y año.
        barrios_por_distrito: Mapeo de distritos a barrios.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_seguridad...")
    
    cursor = conn.cursor()
    inserted = 0
    
    for _, row in df_agg.iterrows():
        distrito = row["distrito_code"]
        anio = row["anio"]
        barrios = barrios_por_distrito.get(distrito, [])
        
        if not barrios:
            logger.warning(f"No hay barrios para distrito {distrito}")
            continue
        
        # Obtener población del distrito para calcular tasas
        pob_distrito = get_poblacion_distrito(conn, anio)
        poblacion = pob_distrito.get(distrito, 100000)
        
        # Calcular tasa por 1000 habitantes
        tasa_criminalidad = (row["total_delitos"] / poblacion) * 1000 if poblacion > 0 else None
        
        # Distribuir entre barrios (proporcionalmente, asumiendo distribución uniforme)
        num_barrios = len(barrios)
        delitos_patrimonio_barrio = row["delitos_patrimonio"] // num_barrios
        delitos_seguridad_barrio = row["delitos_seguridad_personal"] // num_barrios
        
        for barrio_id in barrios:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO fact_seguridad
                    (barrio_id, anio, trimestre, delitos_patrimonio, delitos_seguridad_personal, 
                     tasa_criminalidad_1000hab)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        barrio_id,
                        anio,
                        0,  # 0 indica datos anuales (no trimestrales)
                        delitos_patrimonio_barrio,
                        delitos_seguridad_barrio,
                        round(tasa_criminalidad, 2) if tasa_criminalidad else None,
                    )
                )
                inserted += 1
            except sqlite3.Error as e:
                logger.error(f"Error insertando barrio {barrio_id}: {e}")
    
    conn.commit()
    logger.info(f"Registros insertados: {inserted}")
    return inserted


def validate_data(conn: sqlite3.Connection) -> None:
    """
    Valida los datos insertados en fact_seguridad.
    
    Args:
        conn: Conexión a la base de datos.
    """
    logger.info("Validando datos insertados...")
    
    # Contar registros por año
    query = """
    SELECT anio, COUNT(*) as count, AVG(tasa_criminalidad_1000hab) as avg_tasa
    FROM fact_seguridad
    GROUP BY anio
    ORDER BY anio DESC
    LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    
    logger.info("\nRegistros por año (últimos 10):")
    for _, row in df.iterrows():
        logger.info(f"  {int(row['anio'])}: {row['count']} registros, tasa promedio: {row['avg_tasa']:.1f}‰")
    
    # Distritos con más criminalidad
    query = """
    SELECT 
        b.distrito_nombre,
        SUM(s.delitos_patrimonio + s.delitos_seguridad_personal) as total_delitos,
        AVG(s.tasa_criminalidad_1000hab) as avg_tasa
    FROM fact_seguridad s
    JOIN dim_barrios b ON s.barrio_id = b.barrio_id
    WHERE s.anio = 2024
    GROUP BY b.distrito_nombre
    ORDER BY total_delitos DESC
    """
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        logger.info("\nCriminalidad por distrito (2024):")
        for _, row in df.iterrows():
            logger.info(f"  - {row['distrito_nombre']}: {row['total_delitos']} delitos, tasa: {row['avg_tasa']:.1f}‰")


def main() -> int:
    """Función principal."""
    # Rutas
    csv_path = PROJECT_ROOT / "data" / "raw" / "seguridad" / "criminalidad_mossos.csv"
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not csv_path.exists():
        logger.error(f"CSV no encontrado: {csv_path}")
        return 1
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar CSV
        df = load_criminalidad_csv(csv_path)
        
        # Filtrar solo Barcelona
        df_bcn = filter_barcelona_data(df)
        
        # Agregar por distrito y año
        df_agg = aggregate_by_distrito_year(df_bcn)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener mapeo de barrios por distrito
        barrios_por_distrito = get_barrios_por_distrito(conn)
        logger.info(f"Barrios por distrito: {sum(len(b) for b in barrios_por_distrito.values())} total")
        
        # Insertar datos
        inserted = insert_into_fact_seguridad(conn, df_agg, barrios_por_distrito)
        
        # Validar
        validate_data(conn)
        
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

