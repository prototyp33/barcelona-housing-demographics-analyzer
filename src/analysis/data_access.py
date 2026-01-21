"""
Analysis Module - Data Logic & SQL Queries

Consolidates all SQL queries and Pandas transformations for the dashboard.
This module separates data logic from UI components, following the modular architecture.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import pandas as pd
import numpy as np
import streamlit as st
import sqlite3

from src.app.config import DB_PATH, VIVIENDA_TIPO_M2
from src.database import DatabaseManager
from src.database_setup import validate_table_name

logger = logging.getLogger(__name__)

# Global database manager instance
_db_manager = DatabaseManager()


def get_connection() -> sqlite3.Connection:
    """
    Obtiene una conexión a la base de datos SQLite.
    
    Returns:
        Conexión SQLite con foreign keys habilitadas.
    """
    return _db_manager.get_connection()


@st.cache_data(ttl=3600)
def get_neighborhood_data(include_geometry: bool = True) -> pd.DataFrame:
    """
    Carga datos de barrios desde la dimensión dim_barrios.
    
    Args:
        include_geometry: Si True, incluye geometry_json en el resultado.
    
    Returns:
        DataFrame con información de barrios.
    """
    conn = get_connection()
    try:
        geometry_col = ", geometry_json" if include_geometry else ""
        query = f"""
            SELECT 
                barrio_id,
                barrio_nombre,
                barrio_nombre_normalizado,
                distrito_id,
                distrito_nombre,
                municipio,
                ambito,
                codi_districte,
                codi_barri
                {geometry_col}
            FROM dim_barrios
            ORDER BY barrio_id
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def get_available_years() -> dict[str, dict[str, Optional[int]]]:
    """
    Obtiene los años disponibles en cada tabla de hechos.
    
    Returns:
        Diccionario con min/max años por tabla.
    """
    conn = get_connection()
    try:
        result = {}
        tables = [
            "fact_precios", "fact_demografia", "fact_renta", 
            "fact_educacion", "fact_vivienda_publica", "fact_seguridad", "fact_presion_turistica"
        ]
        for table in tables:
            try:
                validated_table = validate_table_name(table)
                df = pd.read_sql(
                    f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {validated_table}",
                    conn,
                )
                if not df.empty and pd.notna(df["min_year"].iloc[0]):
                    result[table] = {
                        "min": int(df["min_year"].iloc[0]),
                        "max": int(df["max_year"].iloc[0]),
                        "years": list(range(int(df["min_year"].iloc[0]), int(df["max_year"].iloc[0]) + 1))
                    }
                else:
                    result[table] = {"min": None, "max": None, "years": []}
            except Exception:
                result[table] = {"min": None, "max": None, "years": []}
    finally:
        conn.close()
    return result


@st.cache_data(ttl=3600)
def get_districts() -> list[str]:
    """
    Obtiene la lista de distritos únicos.
    
    Returns:
        Lista de nombres de distritos ordenados.
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
def get_prices(year: int, distrito: Optional[str] = None, source: Optional[str] = None) -> pd.DataFrame:
    """
    Carga precios de vivienda. Si source es None, consolida fact_precios (real) e Idealista (market).
    
    Args:
        year: Año a consultar.
        distrito: Filtro opcional por distrito.
        source: 'real' (Incasòl), 'market' (Idealista) or None (both).
    
    Returns:
        DataFrame con precios por barrio.
    """
    conn = get_connection()
    try:
        df_real = pd.DataFrame()
        if source in [None, 'real']:
            query_off = """
            SELECT 
                p.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                MAX(p.precio_m2_venta) as precio_m2_venta, 
                MAX(p.precio_mes_alquiler) as precio_mes_alquiler, 
                'real' as source_type
            FROM fact_precios p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.anio = ?
            """
            params = [year]
            if distrito:
                query_off += " AND b.distrito_nombre = ?"
                params.append(distrito)
            query_off += " GROUP BY p.barrio_id"
            df_real = pd.read_sql(query_off, conn, params=params)

        df_market = pd.DataFrame()
        if source in [None, 'market']:
            try:
                query_id = """
                SELECT 
                    f.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                    MAX(CASE WHEN f.operacion = 'sale' THEN f.precio_m2_medio END) as precio_m2_venta,
                    MAX(CASE WHEN f.operacion = 'rent' THEN f.precio_medio END) as precio_mes_alquiler,
                    'market' as source_type
                FROM fact_oferta_idealista f
                JOIN dim_barrios b ON f.barrio_id = b.barrio_id
                WHERE f.anio = ?
                """
                params_id = [year]
                if distrito:
                    query_id += " AND b.distrito_nombre = ?"
                    params_id.append(distrito)
                query_id += " GROUP BY f.barrio_id"
                df_market = pd.read_sql(query_id, conn, params=params_id)
            except Exception:
                pass

        if source == 'real': return df_real
        if source == 'market': return df_market

        # Consolidation (legacy behavior with enhancement)
        dfs = [df for df in [df_real, df_market] if not df.empty]
        if not dfs: return pd.DataFrame()
        
        df = pd.concat(dfs, ignore_index=True).groupby('barrio_id').agg({
            'barrio_nombre': 'first',
            'distrito_nombre': 'first',
            'geometry_json': 'first',
            'precio_m2_venta': 'max',
            'precio_mes_alquiler': 'max'
        }).reset_index()
        
        return df.rename(columns={'precio_m2_venta': 'avg_precio_m2', 'precio_mes_alquiler': 'avg_alquiler'})
    finally:
        conn.close()

@st.cache_data(ttl=3600)
def get_yield_analysis(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Calcula la rentabilidad dual (Real vs Market) por barrio.
    Implementa Metodología C (Dual Comparison).
    """
    df_real = get_prices(year, distrito, source='real')
    df_market = get_prices(year, distrito, source='market')
    
    if df_real.empty and df_market.empty: return pd.DataFrame()
    
    # Merge and calculate
    res = pd.DataFrame()
    if not df_real.empty:
        df_real['yield_real'] = (df_real['precio_mes_alquiler'] * 12) / (df_real['precio_m2_venta'] * VIVIENDA_TIPO_M2) * 100
        res = df_real[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'geometry_json', 'yield_real']]
    
    if not df_market.empty:
        df_market['yield_market'] = (df_market['precio_mes_alquiler'] * 12) / (df_market['precio_m2_venta'] * VIVIENDA_TIPO_M2) * 100
        market_cols = ['barrio_id', 'yield_market']
        if res.empty:
            res = df_market[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'geometry_json', 'yield_market']]
        else:
            res = res.merge(df_market[market_cols], on='barrio_id', how='outer')
            
    if not res.empty:
        if 'yield_real' not in res.columns: res['yield_real'] = np.nan
        if 'yield_market' not in res.columns: res['yield_market'] = np.nan
        if 'yield_gap' not in res.columns:
            res['yield_gap'] = res['yield_market'] - res['yield_real']
        
    return res


@st.cache_data(ttl=3600)
def get_renta(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos de renta para un año específico.
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente disponible.
    
    Returns:
        DataFrame con barrio_id y renta_euros.
    """
    if year is None:
        years_info = get_available_years()
        year = years_info.get("fact_renta", {}).get("max")
        if year is None:
            return pd.DataFrame()

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
def get_demografia(year: int) -> pd.DataFrame:
    """
    Carga datos demográficos para un año específico.
    
    Args:
        year: Año a consultar.
    
    Returns:
        DataFrame con métricas demográficas por barrio.
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
def get_affordability_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos combinados para análisis de esfuerzo de compra.
    
    Args:
        year: Año para precios. Si es None, usa el más reciente.
    
    Returns:
        DataFrame con precio, renta y effort_ratio por barrio.
    """
    years_info = get_available_years()
    if year is None:
        year = years_info.get("fact_precios", {}).get("max") or 2023

    # Cargar precios consolidados
    df_precios = get_prices(year)
    if df_precios.empty:
        return pd.DataFrame()
        
    # Cargar renta (usar el año más reciente disponible)
    income_year = years_info.get("fact_renta", {}).get("max")
    if income_year is None:
        return pd.DataFrame()
        
    df_renta = get_renta(income_year)
    
    # Combinar
    df = df_precios.merge(df_renta, on='barrio_id', how='inner')
    
    # Calcular ratio
    df['effort_ratio'] = (df['avg_precio_m2'] * VIVIENDA_TIPO_M2) / df['renta_euros']
    
    # Filtrar nulos
    df = df[df['effort_ratio'].notna()]
    
    return df


@st.cache_data(ttl=3600)
def get_temporal_comparison(year_start: Optional[int] = None, year_end: Optional[int] = None) -> pd.DataFrame:
    """
    Carga comparación temporal de precios.
    
    Args:
        year_start: Año inicial. Si es None, usa el mínimo disponible.
        year_end: Año final. Si es None, usa el máximo disponible.
    
    Returns:
        DataFrame con comparación de precios entre años.
    """
    years_info = get_available_years()
    if year_start is None:
        year_start = years_info.get("fact_precios", {}).get("min") or 2015
    if year_end is None:
        year_end = years_info.get("fact_precios", {}).get("max") or 2023

    # Cargar precios inicio y fin
    df_start = get_prices(year_start)
    df_end = get_prices(year_end)
    
    if df_start.empty or df_end.empty:
        return pd.DataFrame()
        
    # Renombrar columnas para el merge
    df_start = df_start[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'avg_precio_m2']].rename(columns={'avg_precio_m2': 'precio_start'})
    df_end = df_end[['barrio_id', 'avg_precio_m2']].rename(columns={'avg_precio_m2': 'precio_end'})
    
    # Merge
    df = df_start.merge(df_end, on='barrio_id', how='inner')
    
    # Cargar renta y calcular esfuerzo (usar el año más reciente disponible)
    income_year = years_info.get("fact_renta", {}).get("max")
    if income_year:
        df_renta = get_renta(income_year)
        df = df.merge(df_renta, on='barrio_id', how='inner')
        
        df["effort_start"] = (df["precio_start"] * VIVIENDA_TIPO_M2) / df["renta_euros"]
        df["effort_end"] = (df["precio_end"] * VIVIENDA_TIPO_M2) / df["renta_euros"]
        df["effort_change"] = df["effort_end"] - df["effort_start"]
    else:
        df["effort_start"] = None
        df["effort_end"] = None
        df["effort_change"] = None
    
    df["precio_change_pct"] = ((df["precio_end"] - df["precio_start"]) / df["precio_start"]) * 100
    
    # Alias para compatibilidad con mapa
    df["var_precio_pct"] = df["precio_change_pct"]
    
    return df


@st.cache_data(ttl=3600)
def get_correlation_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos para análisis de correlación.
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente.
    
    Returns:
        DataFrame con precio, renta, densidad y población.
    """
    # Determinar mejores años disponibles para fallback
    years_info = get_available_years()
    if year is None:
        year = years_info.get("fact_precios", {}).get("max") or 2023

    income_years = years_info.get("fact_renta", {})
    income_year = year if income_years.get("min") and income_years.get("max") and income_years["min"] <= year <= income_years["max"] else (income_years.get("max") or 2022)
    
    demo_years = years_info.get("fact_demografia", {})
    demo_year = min(year, demo_years.get("max") or 2025)
    
    conn = get_connection()
    try:
        query = """
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                p.avg_precio_m2,
                COALESCE(r.renta_mediana, r.renta_promedio, r.renta_euros) as renta_euros,
                d.poblacion_total
            FROM dim_barrios b
            INNER JOIN (
                SELECT barrio_id, AVG(precio_m2_venta) AS avg_precio_m2
                FROM fact_precios
                WHERE anio = ? AND precio_m2_venta IS NOT NULL
                GROUP BY barrio_id
            ) p ON b.barrio_id = p.barrio_id
            LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND r.anio = ?
            LEFT JOIN v_demografia_aggregated d ON b.barrio_id = d.barrio_id AND d.anio = ?
        """
        df = pd.read_sql(query, conn, params=[year, income_year, demo_year])
        return df.dropna(subset=['renta_euros', 'poblacion_total'])
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def get_kpis() -> dict:
    """
    Calcula KPIs globales del proyecto.
    """
    conn = get_connection()
    try:
        # Total barrios
        barrios = pd.read_sql("SELECT COUNT(*) as n FROM dim_barrios", conn)
        precios_count = pd.read_sql("SELECT COUNT(*) as n FROM fact_precios", conn)
        
        # Años
        years_df = pd.read_sql("SELECT MIN(anio) as min_y, MAX(anio) as max_y FROM fact_precios", conn)
        max_year = int(years_df["max_y"].iloc[0]) if pd.notna(years_df["max_y"].iloc[0]) else 2023
        
        # Data para Yield
        df_yield = get_yield_analysis(max_year)
        yield_real = df_yield['yield_real'].mean() if not df_yield.empty and 'yield_real' in df_yield.columns else 0.0
        yield_market = df_yield['yield_market'].mean() if not df_yield.empty and 'yield_market' in df_yield.columns else 0.0
        
        # Alquiler medio (Real)
        alquiler_df = pd.read_sql("SELECT AVG(precio_mes_alquiler) as avg FROM fact_precios WHERE anio = ?", conn, params=[max_year])
        alquiler_curr = float(alquiler_df["avg"].iloc[0]) if not alquiler_df.empty and pd.notna(alquiler_df["avg"].iloc[0]) else 0.0
        
        return {
            "total_barrios": int(barrios["n"].iloc[0]),
            "registros_precios": int(precios_count["n"].iloc[0]),
            "año_max": max_year,
            "yield_real_pct": float(yield_real),
            "yield_market_pct": float(yield_market),
            "alquiler_medio_real": alquiler_curr,
            "yield_ciudad_pct": float(yield_real) # Default legacy
        }
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def get_accessibility_metrics(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Carga métricas de accesibilidad (Educación y Vivienda Pública) por barrio.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                e.total_centros_educativos,
                e.num_centros_infantil,
                e.num_centros_primaria,
                e.num_centros_secundaria,
                e.num_centros_universidad,
                v.viviendas_proteccion_oficial as viviendas_publicas
            FROM dim_barrios b
            LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = ?
            LEFT JOIN fact_vivienda_publica v ON b.barrio_id = v.barrio_id AND v.anio = ?
        """
        params = [year, year]
        if distrito:
            query += " WHERE b.distrito_nombre = ?"
            params.append(distrito)
            
        df = pd.read_sql(query, conn, params=params)
        return df.fillna(0)
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def get_safety_and_tourism(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Carga métricas de seguridad y presión turística.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                s.tasa_criminalidad_1000hab,
                s.delitos_patrimonio,
                t.num_listings_airbnb,
                t.pct_entire_home,
                t.precio_noche_promedio
            FROM dim_barrios b
            LEFT JOIN fact_seguridad s ON b.barrio_id = s.barrio_id AND s.anio = ?
            LEFT JOIN fact_presion_turistica t ON b.barrio_id = t.barrio_id AND t.anio = ?
        """
        params = [year, year]
        if distrito:
            query += " WHERE b.distrito_nombre = ?"
            params.append(distrito)
            
        df = pd.read_sql(query, conn, params=params)
        return df.fillna(0)
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def get_price_trends(distritos: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Carga la evolución temporal de precios.
    
    Args:
        distritos: Lista opcional de distritos para filtrar.
    
    Returns:
        DataFrame con tendencias de precios por año.
    """
    years_info = get_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2022
    
    all_data = []
    for year in range(min_year, max_year + 1):
        df_year = get_prices(year)
        if not df_year.empty:
            df_year['anyo'] = year
            all_data.append(df_year)
            
    if not all_data:
        return pd.DataFrame()
        
    # Filter out empty or all-NA DataFrames
    all_data = [d for d in all_data if not d.empty and not d.isna().all().all()]
    
    if not all_data:
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)
    
    if distritos:
        df = df[df['distrito_nombre'].isin(distritos)]
        
    # Agrupar para obtener tendencia
    df_trends = df.groupby(['anyo', 'barrio_nombre', 'distrito_nombre']).agg({
        'avg_precio_m2': 'mean',
        'avg_alquiler': 'mean'
    }).reset_index()
    
    return df_trends.rename(columns={'avg_precio_m2': 'precio_venta_m2', 'avg_alquiler': 'precio_alquiler_m2'})


@st.cache_data(ttl=3600)
def get_geojson() -> dict:
    """
    Construye un objeto GeoJSON a partir de los barrios con geometrías.
    
    Returns:
        Diccionario GeoJSON con FeatureCollection.
    """
    df_barrios = get_neighborhood_data(include_geometry=True)
    features = []
    
    for _, row in df_barrios.iterrows():
        if pd.notna(row.get('geometry_json')):
            try:
                geometry = json.loads(row['geometry_json']) if isinstance(row['geometry_json'], str) else row['geometry_json']
                feature = {
                    "type": "Feature",
                    "properties": {
                        "barrio_id": int(row['barrio_id']),
                        "barrio_nombre": row.get('barrio_nombre', ''),
                        "distrito_nombre": row.get('distrito_nombre', '')
                    },
                    "geometry": geometry
                }
                features.append(feature)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Error parsing geometry for barrio_id {row.get('barrio_id')}: {e}")
                continue
    
    return {
        "type": "FeatureCollection",
        "features": features
    }
