"""
Data loader module for the Barcelona Housing Dashboard.

Provides cached functions to load data from the SQLite database.
Uses Streamlit's cache to avoid reloading data on every interaction.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Optional

import pandas as pd
import streamlit as st

from src.app.config import DB_PATH, VIVIENDA_TIPO_M2
from src.database_setup import validate_table_name


def get_connection() -> sqlite3.Connection:
    """
    Crea una conexión a la base de datos SQLite.
    
    Returns:
        Conexión SQLite con foreign keys habilitadas.
    
    Raises:
        FileNotFoundError: Si la base de datos no existe.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@st.cache_data(ttl=3600)
def load_barrios() -> pd.DataFrame:
    """
    Carga la dimensión de barrios con geometrías.
    
    Returns:
        DataFrame con barrio_id, barrio_nombre, distrito_nombre, geometry_json.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT 
                barrio_id,
                barrio_nombre,
                barrio_nombre_normalizado,
                distrito_id,
                distrito_nombre,
                geometry_json
            FROM dim_barrios
            ORDER BY barrio_id
            """,
            conn,
        )
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_available_years() -> dict:
    """
    Obtiene los años disponibles en cada tabla de hechos.

    Returns:
        Diccionario con años mínimo y máximo por tabla.

    Raises:
        InvalidTableNameError: Si alguna tabla no está en la whitelist.
    """
    conn = get_connection()
    try:
        result = {}
        tables = ["fact_precios", "fact_demografia", "fact_renta"]
        for table in tables:
            # Validar nombre de tabla contra whitelist (seguridad SQL injection)
            validated_table = validate_table_name(table)
            df = pd.read_sql(
                f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {validated_table}",
                conn,
            )
            result[table] = {
                "min": int(df["min_year"].iloc[0]) if pd.notna(df["min_year"].iloc[0]) else None,
                "max": int(df["max_year"].iloc[0]) if pd.notna(df["max_year"].iloc[0]) else None,
            }
    finally:
        conn.close()
    return result


@st.cache_data(ttl=3600)
def load_distritos() -> list[str]:
    """
    Obtiene la lista de distritos únicos.
    
    Returns:
        Lista de nombres de distrito ordenados.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            "SELECT DISTINCT distrito_nombre FROM dim_barrios ORDER BY distrito_nombre",
            conn,
        )
    finally:
        conn.close()
    return df["distrito_nombre"].tolist()


@st.cache_data(ttl=3600)
def load_precios(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Carga precios de vivienda para un año específico.
    
    Args:
        year: Año a consultar.
        distrito: Filtro opcional por distrito.
    
    Returns:
        DataFrame con barrio_id, avg_precio_m2_venta, avg_precio_alquiler.
    """
    conn = get_connection()
    try:
        query = """
        SELECT 
            p.barrio_id,
            b.barrio_nombre,
            b.distrito_nombre,
            b.geometry_json,
            AVG(p.precio_m2_venta) AS avg_precio_m2,
            AVG(p.precio_mes_alquiler) AS avg_alquiler
        FROM fact_precios p
        JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE p.anio = ?
        """
        params = [year]
        
        if distrito:
            query += " AND b.distrito_nombre = ?"
            params.append(distrito)
        
        query += " GROUP BY p.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json"
        
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_renta(year: int = 2022) -> pd.DataFrame:
    """
    Carga datos de renta para un año específico.
    
    Args:
        year: Año a consultar (por defecto 2022, único disponible).
    
    Returns:
        DataFrame con barrio_id y renta_euros.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT barrio_id, renta_euros
            FROM fact_renta
            WHERE anio = ?
            """,
            conn,
            params=[year],
        )
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_demografia(year: int) -> pd.DataFrame:
    """
    Carga datos demográficos para un año específico.
    
    Args:
        year: Año a consultar.
    
    Returns:
        DataFrame con métricas demográficas por barrio, incluyendo
        pct_mayores_65, pct_menores_15 e indice_envejecimiento.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT 
                barrio_id,
                poblacion_total,
                poblacion_hombres,
                poblacion_mujeres,
                hogares_totales,
                edad_media,
                porc_inmigracion,
                densidad_hab_km2,
                pct_mayores_65,
                pct_menores_15,
                indice_envejecimiento
            FROM fact_demografia
            WHERE anio = ?
            """,
            conn,
            params=[year],
        )
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_affordability_data(year: int = 2022) -> pd.DataFrame:
    """
    Carga datos combinados para análisis de esfuerzo de compra.
    
    Args:
        year: Año para precios (renta siempre es 2022).
    
    Returns:
        DataFrame con precio, renta y effort_ratio por barrio.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            f"""
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                b.geometry_json,
                p.avg_precio_m2,
                r.renta_euros,
                (p.avg_precio_m2 * {VIVIENDA_TIPO_M2}) / r.renta_euros AS effort_ratio
            FROM dim_barrios b
            LEFT JOIN (
                SELECT barrio_id, AVG(precio_m2_venta) AS avg_precio_m2
                FROM fact_precios
                WHERE anio = ? AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ) p ON b.barrio_id = p.barrio_id
            LEFT JOIN (
                SELECT barrio_id, renta_euros
                FROM fact_renta WHERE anio = 2022
            ) r ON b.barrio_id = r.barrio_id
            WHERE b.geometry_json IS NOT NULL
              AND p.avg_precio_m2 IS NOT NULL
              AND r.renta_euros IS NOT NULL
            """,
            conn,
            params=[year],
        )
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_temporal_comparison(year_start: int = 2015, year_end: int = 2022) -> pd.DataFrame:
    """
    Carga comparación temporal de precios.
    
    Args:
        year_start: Año inicial.
        year_end: Año final.
    
    Returns:
        DataFrame con variación de precios y esfuerzo.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            f"""
            WITH precios_start AS (
                SELECT barrio_id, AVG(precio_m2_venta) AS precio_start
                FROM fact_precios
                WHERE anio = ? AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ),
            precios_end AS (
                SELECT barrio_id, AVG(precio_m2_venta) AS precio_end
                FROM fact_precios
                WHERE anio = ? AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ),
            renta_actual AS (
                SELECT barrio_id, renta_euros
                FROM fact_renta WHERE anio = 2022
            )
            SELECT
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                b.geometry_json,
                ps.precio_start,
                pe.precio_end,
                r.renta_euros,
                ((pe.precio_end - ps.precio_start) / ps.precio_start) * 100 AS var_precio_pct,
                (ps.precio_start * {VIVIENDA_TIPO_M2}) / r.renta_euros AS effort_start,
                (pe.precio_end * {VIVIENDA_TIPO_M2}) / r.renta_euros AS effort_end
            FROM dim_barrios b
            LEFT JOIN precios_start ps ON b.barrio_id = ps.barrio_id
            LEFT JOIN precios_end pe ON b.barrio_id = pe.barrio_id
            LEFT JOIN renta_actual r ON b.barrio_id = r.barrio_id
            WHERE b.geometry_json IS NOT NULL
              AND ps.precio_start IS NOT NULL
              AND pe.precio_end IS NOT NULL
              AND r.renta_euros IS NOT NULL
            """,
            conn,
            params=[year_start, year_end],
        )
    finally:
        conn.close()
    
    df["effort_change"] = df["effort_end"] - df["effort_start"]
    return df


@st.cache_data(ttl=3600)
def load_correlation_data(year: int = 2022) -> pd.DataFrame:
    """
    Carga datos para análisis de correlación.
    
    Args:
        year: Año a consultar.
    
    Returns:
        DataFrame con precio, renta, densidad y población.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                p.avg_precio_m2,
                r.renta_euros,
                d.densidad_hab_km2,
                d.poblacion_total
            FROM dim_barrios b
            LEFT JOIN (
                SELECT barrio_id, AVG(precio_m2_venta) AS avg_precio_m2
                FROM fact_precios
                WHERE anio = ? AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ) p ON b.barrio_id = p.barrio_id
            LEFT JOIN (
                SELECT barrio_id, renta_euros
                FROM fact_renta WHERE anio = ?
            ) r ON b.barrio_id = r.barrio_id
            LEFT JOIN (
                SELECT barrio_id, densidad_hab_km2, poblacion_total
                FROM fact_demografia WHERE anio = ?
            ) d ON b.barrio_id = d.barrio_id
            WHERE p.avg_precio_m2 IS NOT NULL
              AND r.renta_euros IS NOT NULL
              AND d.densidad_hab_km2 IS NOT NULL
            """,
            conn,
            params=[year, year, year],
        )
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_kpis() -> dict:
    """
    Calcula KPIs globales del proyecto.
    
    Returns:
        Diccionario con métricas clave.
    """
    conn = get_connection()
    try:
        # Total barrios
        barrios = pd.read_sql("SELECT COUNT(*) as n FROM dim_barrios", conn)
        
        # Barrios con geometría
        geom = pd.read_sql(
            "SELECT COUNT(*) as n FROM dim_barrios WHERE geometry_json IS NOT NULL",
            conn,
        )
        
        # Registros de precios
        precios = pd.read_sql("SELECT COUNT(*) as n FROM fact_precios", conn)
        
        # Años cubiertos
        years = pd.read_sql(
            "SELECT MIN(anio) as min_y, MAX(anio) as max_y FROM fact_precios",
            conn,
        )
        
        # Precio medio actual (2022) y anterior (2021)
        precio_medio = pd.read_sql(
            """
            SELECT anio, AVG(precio_m2_venta) as avg_precio
            FROM fact_precios
            WHERE anio IN (2021, 2022) AND precio_m2_venta IS NOT NULL
            GROUP BY anio
            """,
            conn,
        )
        precio_2022 = precio_medio[precio_medio["anio"] == 2022]["avg_precio"].iloc[0] if not precio_medio[precio_medio["anio"] == 2022].empty else 0.0
        precio_2021 = precio_medio[precio_medio["anio"] == 2021]["avg_precio"].iloc[0] if not precio_medio[precio_medio["anio"] == 2021].empty else 0.0
        
        # Alquiler medio (2022)
        alquiler_medio = pd.read_sql(
            """
            SELECT AVG(precio_mes_alquiler) as avg_alquiler
            FROM fact_precios
            WHERE anio = 2022 AND precio_mes_alquiler IS NOT NULL
            """,
            conn,
        )
        
        # Renta media (2022)
        renta_media = pd.read_sql(
            "SELECT AVG(renta_euros) as avg_renta FROM fact_renta WHERE anio = 2022",
            conn,
        )
        
    finally:
        conn.close()
    
    return {
        "total_barrios": int(barrios["n"].iloc[0]),
        "barrios_con_geometria": int(geom["n"].iloc[0]),
        "registros_precios": int(precios["n"].iloc[0]),
        "año_min": int(years["min_y"].iloc[0]),
        "año_max": int(years["max_y"].iloc[0]),
        "precio_medio_2022": float(precio_2022),
        "precio_medio_2021": float(precio_2021),
        "alquiler_medio_2022": float(alquiler_medio["avg_alquiler"].iloc[0]) if pd.notna(alquiler_medio["avg_alquiler"].iloc[0]) else 0.0,
        "renta_media_2022": float(renta_media["avg_renta"].iloc[0]),
    }


def build_geojson(df: pd.DataFrame) -> dict:
    """
    Construye un FeatureCollection GeoJSON desde un DataFrame.
    
    Args:
        df: DataFrame con columnas geometry_json, barrio_id, barrio_nombre, distrito_nombre.
    
    Returns:
        Diccionario GeoJSON FeatureCollection.
    """
    features = []
    for _, row in df.iterrows():
        if pd.isna(row.get("geometry_json")):
            continue
        geometry = json.loads(row["geometry_json"])
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "barrio_id": int(row["barrio_id"]),
                "barrio_nombre": row.get("barrio_nombre", ""),
                "distrito_nombre": row.get("distrito_nombre", ""),
            },
        })
    return {"type": "FeatureCollection", "features": features}

