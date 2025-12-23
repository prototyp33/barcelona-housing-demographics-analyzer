#!/usr/bin/env python3
"""
Script para procesar datos de Inside Airbnb y poblar fact_presion_turistica.

Fuente: Inside Airbnb (http://insideairbnb.com/barcelona)
Datos descargados: listings.csv, reviews.csv

Este script:
1. Lee el archivo listings de Inside Airbnb
2. Mapea listings a barrios de Barcelona usando el campo 'neighbourhood'
3. Calcula métricas agregadas por barrio
4. Inserta/actualiza datos en fact_presion_turistica

Uso:
    python scripts/process_airbnb_data.py
"""

import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional
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

# Mapeo de nombres de barrios de Airbnb a nombres oficiales
AIRBNB_TO_OFICIAL = {
    "el Raval": "el Raval",
    "el Barri Gòtic": "el Barri Gòtic",
    "la Barceloneta": "la Barceloneta",
    "Sant Pere, Santa Caterina i la Ribera": "Sant Pere, Santa Caterina i la Ribera",
    "el Fort Pienc": "el Fort Pienc",
    "la Sagrada Família": "la Sagrada Família",
    "la Dreta de l'Eixample": "la Dreta de l'Eixample",
    "l'Antiga Esquerra de l'Eixample": "l'Antiga Esquerra de l'Eixample",
    "la Nova Esquerra de l'Eixample": "la Nova Esquerra de l'Eixample",
    "Sant Antoni": "Sant Antoni",
    "el Poble Sec - AEI Parc Montjuïc": "el Poble-sec",
    "el Poble-sec": "el Poble-sec",
    "la Marina del Prat Vermell - AEI Zona Franca": "la Marina del Prat Vermell",
    "la Marina del Prat Vermell": "la Marina del Prat Vermell",
    "la Marina de Port": "la Marina de Port",
    "la Font de la Guatlla": "la Font de la Guatlla",
    "Hostafrancs": "Hostafrancs",
    "la Bordeta": "la Bordeta",
    "Sants - Badal": "Sants - Badal",
    "Sants": "Sants",
    "les Corts": "les Corts",
    "la Maternitat i Sant Ramon": "la Maternitat i Sant Ramon",
    "Pedralbes": "Pedralbes",
    "Vallvidrera, el Tibidabo i les Planes": "Vallvidrera, el Tibidabo i les Planes",
    "Sarrià": "Sarrià",
    "les Tres Torres": "les Tres Torres",
    "Sant Gervasi - la Bonanova": "Sant Gervasi - la Bonanova",
    "Sant Gervasi - Galvany": "Sant Gervasi - Galvany",
    "el Putxet i el Farró": "el Putxet i el Farró",
    "Vallcarca i els Penitents": "Vallcarca i els Penitents",
    "el Coll": "el Coll",
    "la Salut": "la Salut",
    "la Vila de Gràcia": "la Vila de Gràcia",
    "el Camp d'en Grassot i Gràcia Nova": "el Camp d'en Grassot i Gràcia Nova",
    "el Baix Guinardó": "el Baix Guinardó",
    "Can Baró": "Can Baró",
    "el Guinardó": "el Guinardó",
    "la Font d'en Fargues": "la Font d'en Fargues",
    "el Carmel": "el Carmel",
    "la Teixonera": "la Teixonera",
    "Sant Genís dels Agudells": "Sant Genís dels Agudells",
    "Montbau": "Montbau",
    "la Vall d'Hebron": "la Vall d'Hebron",
    "la Clota": "la Clota",
    "Horta": "Horta",
    "Vilapicina i la Torre Llobeta": "Vilapicina i la Torre Llobeta",
    "Porta": "Porta",
    "el Turó de la Peira": "el Turó de la Peira",
    "Can Peguera": "Can Peguera",
    "la Guineueta": "la Guineueta",
    "Canyelles": "Canyelles",
    "les Roquetes": "les Roquetes",
    "Verdun": "Verdun",
    "la Prosperitat": "la Prosperitat",
    "la Trinitat Nova": "la Trinitat Nova",
    "Torre Baró": "Torre Baró",
    "Ciutat Meridiana": "Ciutat Meridiana",
    "Vallbona": "Vallbona",
    "la Trinitat Vella": "la Trinitat Vella",
    "Baró de Viver": "Baró de Viver",
    "el Bon Pastor": "el Bon Pastor",
    "Sant Andreu": "Sant Andreu",
    "la Sagrera": "la Sagrera",
    "el Congrés i els Indians": "el Congrés i els Indians",
    "Navas": "Navas",
    "el Camp de l'Arpa del Clot": "el Camp de l'Arpa del Clot",
    "el Clot": "el Clot",
    "el Parc i la Llacuna del Poblenou": "el Parc i la Llacuna del Poblenou",
    "la Vila Olímpica del Poblenou": "la Vila Olímpica del Poblenou",
    "el Poblenou": "el Poblenou",
    "Diagonal Mar i el Front Marítim del Poblenou": "Diagonal Mar i el Front Marítim del Poblenou",
    "el Besòs i el Maresme": "el Besòs i el Maresme",
    "Provençals del Poblenou": "Provençals del Poblenou",
    "Sant Martí de Provençals": "Sant Martí de Provençals",
    "la Verneda i la Pau": "la Verneda i la Pau",
}


def load_listings_csv(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de listings de Inside Airbnb.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los listings.
    """
    logger.info(f"Cargando listings: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Listings cargados: {len(df)}")
    logger.info(f"Columnas: {df.columns.tolist()}")
    return df


def get_barrio_mapping(conn: sqlite3.Connection) -> Dict[str, int]:
    """
    Obtiene el mapeo de nombre de barrio a barrio_id.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        Diccionario {nombre_barrio: barrio_id}.
    """
    query = "SELECT barrio_id, barrio_nombre FROM dim_barrios"
    df = pd.read_sql_query(query, conn)
    return dict(zip(df["barrio_nombre"], df["barrio_id"]))


def normalize_neighbourhood(name: str) -> Optional[str]:
    """
    Normaliza el nombre del barrio de Airbnb al nombre oficial.
    
    Args:
        name: Nombre del barrio según Airbnb.
    
    Returns:
        Nombre oficial del barrio o None si no se encuentra.
    """
    if pd.isna(name):
        return None
    
    # Buscar en el mapeo
    if name in AIRBNB_TO_OFICIAL:
        return AIRBNB_TO_OFICIAL[name]
    
    # Intentar coincidencia parcial
    name_lower = name.lower().strip()
    for airbnb_name, oficial_name in AIRBNB_TO_OFICIAL.items():
        if airbnb_name.lower() in name_lower or name_lower in airbnb_name.lower():
            return oficial_name
    
    return name  # Devolver original si no hay match


def process_listings(df: pd.DataFrame, barrio_mapping: Dict[str, int]) -> pd.DataFrame:
    """
    Procesa los listings y calcula métricas por barrio.
    
    Args:
        df: DataFrame con los listings.
        barrio_mapping: Mapeo de nombres a IDs.
    
    Returns:
        DataFrame con métricas agregadas por barrio.
    """
    logger.info("Procesando listings...")
    
    # Normalizar nombres de barrios
    df["barrio_normalizado"] = df["neighbourhood"].apply(normalize_neighbourhood)
    
    # Mapear a barrio_id
    df["barrio_id"] = df["barrio_normalizado"].map(barrio_mapping)
    
    # Filtrar listings sin barrio válido
    df_valid = df[df["barrio_id"].notna()].copy()
    logger.info(f"Listings con barrio válido: {len(df_valid)} de {len(df)}")
    
    # Convertir precio (quitar $ y comas)
    if "price" in df_valid.columns:
        df_valid["price_clean"] = df_valid["price"].astype(str).str.replace(r'[\$,]', '', regex=True)
        df_valid["price_clean"] = pd.to_numeric(df_valid["price_clean"], errors="coerce")
    
    # Calcular métricas por barrio
    agg_funcs = {
        "id": "count",  # num_listings
        "price_clean": "mean",  # precio promedio
        "reviews_per_month": "mean",  # reviews promedio
        "availability_365": "mean",  # disponibilidad promedio
        "number_of_reviews_ltm": "sum",  # total reviews último año
    }
    
    # Filtrar por room_type
    df_entire = df_valid[df_valid["room_type"] == "Entire home/apt"]
    
    df_agg = df_valid.groupby("barrio_id").agg(agg_funcs).reset_index()
    df_agg.columns = ["barrio_id", "num_listings", "precio_noche_promedio", 
                      "reviews_per_month_avg", "availability_avg", "num_reviews_ltm"]
    
    # Calcular porcentaje de entire home
    df_entire_count = df_entire.groupby("barrio_id")["id"].count().reset_index()
    df_entire_count.columns = ["barrio_id", "num_entire_home"]
    
    df_agg = df_agg.merge(df_entire_count, on="barrio_id", how="left")
    df_agg["num_entire_home"] = df_agg["num_entire_home"].fillna(0)
    df_agg["pct_entire_home"] = (df_agg["num_entire_home"] / df_agg["num_listings"] * 100).round(2)
    
    # Calcular tasa de ocupación estimada (basada en reviews)
    # Fórmula: ocupación ≈ reviews_per_month * 50% / 30 días * 100
    df_agg["tasa_ocupacion"] = (df_agg["reviews_per_month_avg"] * 0.5 / 30 * 100 * 30).clip(0, 100).round(2)
    
    # Añadir año actual
    df_agg["anio"] = datetime.now().year
    
    logger.info(f"Métricas calculadas para {len(df_agg)} barrios")
    return df_agg


def insert_into_fact_presion_turistica(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame
) -> int:
    """
    Inserta los datos en fact_presion_turistica.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame con métricas agregadas.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_presion_turistica...")
    
    cursor = conn.cursor()
    inserted = 0
    anio = datetime.now().year
    
    # Primero eliminar datos del año actual para evitar duplicados
    cursor.execute("DELETE FROM fact_presion_turistica WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT INTO fact_presion_turistica
                (barrio_id, anio, num_listings_airbnb, pct_entire_home, 
                 precio_noche_promedio, tasa_ocupacion, num_reviews_mes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    anio,
                    int(row["num_listings"]),
                    row["pct_entire_home"],
                    row["precio_noche_promedio"],
                    row["tasa_ocupacion"],
                    row["reviews_per_month_avg"],
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
        b.distrito_nombre,
        COUNT(*) as barrios,
        SUM(pt.num_listings_airbnb) as total_listings,
        AVG(pt.precio_noche_promedio) as avg_precio,
        AVG(pt.pct_entire_home) as avg_entire_home
    FROM fact_presion_turistica pt
    JOIN dim_barrios b ON pt.barrio_id = b.barrio_id
    WHERE pt.anio = ?
    GROUP BY b.distrito_nombre
    ORDER BY total_listings DESC
    """
    df = pd.read_sql_query(query, conn, params=[anio])
    
    logger.info(f"\nResumen por distrito ({anio}):")
    for _, row in df.iterrows():
        logger.info(f"  {row['distrito_nombre']}: {int(row['total_listings'])} listings, "
                   f"€{row['avg_precio']:.0f}/noche, {row['avg_entire_home']:.1f}% entire home")
    
    # Total
    total = df['total_listings'].sum()
    logger.info(f"\n📊 Total listings en Barcelona: {int(total)}")


def main() -> int:
    """Función principal."""
    # Buscar archivo de listings
    airbnb_dir = PROJECT_ROOT / "data" / "raw" / "airbnb" / "insideairbnb"
    listings_files = list(airbnb_dir.glob("*listings*.csv"))
    
    if not listings_files:
        logger.error(f"No se encontraron archivos de listings en {airbnb_dir}")
        return 1
    
    listings_path = listings_files[0]
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar listings
        df = load_listings_csv(listings_path)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener mapeo de barrios
        barrio_mapping = get_barrio_mapping(conn)
        logger.info(f"Barrios en BD: {len(barrio_mapping)}")
        
        # Procesar listings
        df_agg = process_listings(df, barrio_mapping)
        
        # Insertar en BD
        inserted = insert_into_fact_presion_turistica(conn, df_agg)
        
        # Validar
        validate_data(conn, datetime.now().year)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} barrios actualizados")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

