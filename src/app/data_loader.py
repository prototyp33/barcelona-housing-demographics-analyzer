"""
Data loader module for the Barcelona Housing Dashboard.

Provides cached functions to load data from the SQLite database.
Uses Streamlit's cache to avoid reloading data on every interaction.
Updated for Market Cockpit.
"""

from __future__ import annotations

import json
import logging
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
            SELECT DISTINCT
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
        df = df.drop_duplicates(subset=['barrio_id'])
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
    Carga precios de vivienda consolidados (fact_precios + Idealista).
    
    Args:
        year: Año a consultar.
        distrito: Filtro opcional por distrito.
    
    Returns:
        DataFrame consolidado y deduplicado.
    """
    conn = get_connection()
    try:
        # 1. Cargar fact_precios
        query_off = """
        SELECT 
            p.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
            p.precio_m2_venta, p.precio_mes_alquiler
        FROM fact_precios p
        JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE p.anio = ?
        """
        df_off = pd.read_sql(query_off, conn, params=[year])
        
        # 2. Cargar fact_oferta_idealista (si existe)
        df_id = pd.DataFrame()
        try:
            query_id = """
            SELECT 
                f.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                CASE WHEN f.operacion = 'sale' THEN f.precio_m2_medio END as precio_m2_venta,
                CASE WHEN f.operacion = 'rent' THEN f.precio_medio END as precio_mes_alquiler
            FROM fact_oferta_idealista f
            JOIN dim_barrios b ON f.barrio_id = b.barrio_id
            WHERE f.anio = ?
            """
            df_id = pd.read_sql(query_id, conn, params=[year])
        except Exception:
            pass

        # 3. Consolidar
        dfs = [df for df in [df_off, df_id] if not df.empty]
        if not dfs:
            return pd.DataFrame()
            
        df = pd.concat(dfs).groupby('barrio_id').agg({
            'barrio_nombre': 'first',
            'distrito_nombre': 'first',
            'geometry_json': 'first',
            'precio_m2_venta': 'max',
            'precio_mes_alquiler': 'max'
        }).reset_index()
        
        # Renombrar para compatibilidad con vistas existentes
        df = df.rename(columns={
            'precio_m2_venta': 'avg_precio_m2',
            'precio_mes_alquiler': 'avg_alquiler'
        })
        
        # 4. Filtrar por distrito si aplica
        if distrito:
            df = df[df['distrito_nombre'] == distrito]
            
        # 5. Deduplicar final por seguridad
        df = df.drop_duplicates(subset=['barrio_id'])
        
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
    Carga datos combinados para análisis de esfuerzo de compra usando precios consolidados.
    
    Args:
        year: Año para precios (renta siempre es 2022).
    
    Returns:
        DataFrame con precio, renta y effort_ratio por barrio.
    """
    # 1. Cargar precios consolidados
    df_precios = load_precios(year)
    if df_precios.empty:
        return pd.DataFrame()
        
    # 2. Cargar renta
    df_renta = load_renta(2022)
    
    # 3. Combinar
    df = df_precios.merge(df_renta, on='barrio_id', how='inner')
    
    # 4. Calcular ratio
    df['effort_ratio'] = (df['avg_precio_m2'] * VIVIENDA_TIPO_M2) / df['renta_euros']
    
    # Filtrar nulos
    df = df[df['effort_ratio'].notna()]
    
    return df


@st.cache_data(ttl=3600)
def load_temporal_comparison(year_start: int = 2015, year_end: int = 2022) -> pd.DataFrame:
    """
    Carga comparación temporal de precios usando precios consolidados.
    """
    # 1. Cargar precios inicio y fin
    df_start = load_precios(year_start)
    df_end = load_precios(year_end)
    
    if df_start.empty or df_end.empty:
        return pd.DataFrame()
        
    # 2. Renombrar columnas para el merge
    df_start = df_start[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'avg_precio_m2']].rename(columns={'avg_precio_m2': 'precio_start'})
    df_end = df_end[['barrio_id', 'avg_precio_m2']].rename(columns={'avg_precio_m2': 'precio_end'})
    
    # 3. Merge
    df = df_start.merge(df_end, on='barrio_id', how='inner')
    
    # 4. Cargar renta y calcular esfuerzo
    df_renta = load_renta(2022)
    df = df.merge(df_renta, on='barrio_id', how='inner')
    
    df["effort_start"] = (df["precio_start"] * VIVIENDA_TIPO_M2) / df["renta_euros"]
    df["effort_end"] = (df["precio_end"] * VIVIENDA_TIPO_M2) / df["renta_euros"]
    
    df["precio_change_pct"] = ((df["precio_end"] - df["precio_start"]) / df["precio_start"]) * 100
    df["effort_change"] = df["effort_end"] - df["effort_start"]
    
    # Alias para compatibilidad con mapa
    df["var_precio_pct"] = df["precio_change_pct"]
    
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
        "año_min": int(years["min_y"].iloc[0]) if pd.notna(years["min_y"].iloc[0]) else None,
        "año_max": int(years["max_y"].iloc[0]) if pd.notna(years["max_y"].iloc[0]) else None,
        "precio_medio_2022": float(precio_2022),
        "precio_medio_2021": float(precio_2021),
        "alquiler_medio_2022": float(alquiler_medio["avg_alquiler"].iloc[0]) if not alquiler_medio.empty and pd.notna(alquiler_medio["avg_alquiler"].iloc[0]) else 0.0,
        "renta_media_2022": float(renta_media["avg_renta"].iloc[0]) if not renta_media.empty and pd.notna(renta_media["avg_renta"].iloc[0]) else 0.0,
    }


@st.cache_data(ttl=3600)
def load_critical_kpis(year: int = 2024) -> dict:
    """
    Carga KPIs críticos para el Market Cockpit según Wireframe 1.
    
    Returns:
        Diccionario con:
        - precio_vs_indice: % diferencia precio vs índice referencia
        - presion_turistica: % viviendas Airbnb
        - criminalidad: tasa por 1000 hab
        - ruido: % población expuesta >65dB
    """
    conn = get_connection()
    try:
        # Inicializar resultados vacíos
        result = {
            "precio_vs_indice": {"value": None, "trend": None},
            "presion_turistica": {"value": None, "trend": None},
            "criminalidad": {"value": None, "trend": None},
            "ruido": {"value": None, "trend": None},
        }

        # Auxiliar para verificar si una tabla existe
        def table_exists(table_name: str) -> bool:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            )
            return cursor.fetchone() is not None

        # 1. Precio vs Índice Referencia
        if table_exists("fact_precios") and table_exists("fact_regulacion"):
            precio_indice_query = """
                SELECT 
                    AVG(p.precio_mes_alquiler) as precio_medio_alquiler,
                    AVG(r.indice_referencia_alquiler) as indice_referencia_promedio
                FROM fact_precios p
                LEFT JOIN fact_regulacion r ON p.barrio_id = r.barrio_id AND p.anio = r.anio
                WHERE p.anio = ? AND p.precio_mes_alquiler IS NOT NULL
            """
            try:
                precio_indice = pd.read_sql_query(precio_indice_query, conn, params=[year])
                if not precio_indice.empty and precio_indice["indice_referencia_promedio"].iloc[0] is not None:
                    precio_medio = precio_indice["precio_medio_alquiler"].iloc[0]
                    indice_ref = precio_indice["indice_referencia_promedio"].iloc[0]
                    if indice_ref > 0:
                        val = ((precio_medio - indice_ref) / indice_ref) * 100
                        result["precio_vs_indice"]["value"] = val
                        
                        precio_indice_prev = pd.read_sql_query(precio_indice_query, conn, params=[year - 1])
                        if not precio_indice_prev.empty and precio_indice_prev["indice_referencia_promedio"].iloc[0] is not None:
                            indice_prev = precio_indice_prev["indice_referencia_promedio"].iloc[0]
                            if indice_prev > 0:
                                prev_val = ((precio_indice_prev["precio_medio_alquiler"].iloc[0] - indice_prev) / indice_prev) * 100
                                result["precio_vs_indice"]["trend"] = val - prev_val
            except Exception as e:
                logger.warning(f"Error al cargar KPIs de precio vs índice: {e}")

        # 2. Presión Turística
        if table_exists("fact_presion_turistica") and table_exists("fact_demografia"):
            turismo_query = """
                SELECT 
                    SUM(pt.num_listings_airbnb) as total_listings,
                    AVG(d.hogares_totales) as avg_hogares
                FROM fact_presion_turistica pt
                LEFT JOIN fact_demografia d ON pt.barrio_id = d.barrio_id AND pt.anio = d.anio
                WHERE pt.anio = ? AND pt.num_listings_airbnb IS NOT NULL
            """
            try:
                turismo = pd.read_sql_query(turismo_query, conn, params=[year])
                if not turismo.empty and turismo["avg_hogares"].iloc[0] is not None and turismo["avg_hogares"].iloc[0] > 0:
                    total_hogares = turismo["avg_hogares"].iloc[0] * 73
                    total_listings = turismo["total_listings"].iloc[0] or 0
                    val = (total_listings / total_hogares) * 100
                    result["presion_turistica"]["value"] = val
                    
                    turismo_prev = pd.read_sql_query(turismo_query, conn, params=[year - 1])
                    if not turismo_prev.empty and turismo_prev["avg_hogares"].iloc[0] is not None and turismo_prev["avg_hogares"].iloc[0] > 0:
                        prev_val = (turismo_prev["total_listings"].iloc[0] or 0) / (turismo_prev["avg_hogares"].iloc[0] * 73) * 100
                        result["presion_turistica"]["trend"] = val - prev_val
            except Exception as e:
                logger.warning(f"Error al cargar KPIs de turismo: {e}")

        # 3. Criminalidad
        if table_exists("fact_seguridad"):
            seguridad_query = """
                SELECT AVG(s.tasa_criminalidad_1000hab) as avg_tasa_criminalidad
                FROM fact_seguridad s
                WHERE s.anio = ? AND s.tasa_criminalidad_1000hab IS NOT NULL
            """
            try:
                seguridad = pd.read_sql_query(seguridad_query, conn, params=[year])
                if not seguridad.empty and seguridad["avg_tasa_criminalidad"].iloc[0] is not None:
                    val = seguridad["avg_tasa_criminalidad"].iloc[0]
                    result["criminalidad"]["value"] = val
                    
                    seguridad_prev = pd.read_sql_query(seguridad_query, conn, params=[year - 1])
                    if not seguridad_prev.empty and seguridad_prev["avg_tasa_criminalidad"].iloc[0] is not None:
                        result["criminalidad"]["trend"] = val - seguridad_prev["avg_tasa_criminalidad"].iloc[0]
            except Exception as e:
                logger.warning(f"Error al cargar KPIs de seguridad: {e}")

        # 4. Ruido
        if table_exists("fact_ruido"):
            ruido_query = """
                SELECT AVG(r.pct_poblacion_expuesta_65db) as avg_pct_expuesta
                FROM fact_ruido r
                WHERE r.anio = ? AND r.pct_poblacion_expuesta_65db IS NOT NULL
            """
            try:
                ruido = pd.read_sql_query(ruido_query, conn, params=[year])
                if not ruido.empty and ruido["avg_pct_expuesta"].iloc[0] is not None:
                    val = ruido["avg_pct_expuesta"].iloc[0]
                    result["ruido"]["value"] = val
                    
                    ruido_prev = pd.read_sql_query(ruido_query, conn, params=[year - 1])
                    if not ruido_prev.empty and ruido_prev["avg_pct_expuesta"].iloc[0] is not None:
                        result["ruido"]["trend"] = val - ruido_prev["avg_pct_expuesta"].iloc[0]
            except Exception as e:
                logger.warning(f"Error al cargar KPIs de ruido: {e}")

        return result
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_top_vulnerable_barrios(year: int = 2024, top_n: int = 5) -> pd.DataFrame:
    """
    Carga los barrios más vulnerables según score de riesgo de gentrificación.
    
    Args:
        year: Año a consultar.
        top_n: Número de barrios a retornar.
    
    Returns:
        DataFrame con barrios ordenados por score de vulnerabilidad.
    """
    conn = get_connection()
    try:
        # Auxiliar para verificar si una tabla o vista existe
        def exists(name: str) -> bool:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE name=?", (name,)
            )
            return cursor.fetchone() is not None

        # Usar vista de riesgo de gentrificación si está disponible
        if exists("v_riesgo_gentrificacion"):
            query = """
                SELECT 
                    barrio_id,
                    barrio_nombre,
                    score_riesgo_gentrificacion,
                    categoria_riesgo,
                    pct_cambio_precio_5_anios,
                    precio_actual,
                    precio_5_anios_atras
                FROM v_riesgo_gentrificacion
                WHERE score_riesgo_gentrificacion IS NOT NULL
                ORDER BY score_riesgo_gentrificacion DESC
                LIMIT ?
            """
            try:
                df = pd.read_sql_query(query, conn, params=[top_n])
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Error al cargar v_riesgo_gentrificacion: {e}")
        
        # Fallback: calcular desde datos disponibles
        if exists("fact_precios"):
            query_fallback = """
                SELECT 
                    b.barrio_id,
                    b.barrio_nombre,
                    AVG(p.precio_m2_venta) as precio_actual
                FROM dim_barrios b
                LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND p.anio = ?
                WHERE p.precio_m2_venta IS NOT NULL
                GROUP BY b.barrio_id, b.barrio_nombre
                ORDER BY precio_actual DESC
                LIMIT ?
            """
            try:
                df = pd.read_sql_query(query_fallback, conn, params=[year, top_n])
                df["score_riesgo_gentrificacion"] = 50.0  # Valor por defecto
                df["categoria_riesgo"] = "Medio"
                return df
            except Exception as e:
                logger.warning(f"Error en fallback de barrios vulnerables: {e}")
        
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_regulation_summary(year: int = 2024) -> dict:
    """
    Carga resumen de regulación (zonas tensionadas, licencias VUT).
    
    Args:
        year: Año a consultar.
    
    Returns:
        Diccionario con métricas de regulación.
    """
    conn = get_connection()
    try:
        # Auxiliar para verificar si una tabla existe
        def table_exists(table_name: str) -> bool:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            )
            return cursor.fetchone() is not None

        if not table_exists("fact_regulacion"):
            return {"zonas_tensionadas": 0, "total_licencias_vut": 0}

        query = """
            SELECT 
                COUNT(DISTINCT barrio_id) as zonas_tensionadas,
                SUM(num_licencias_vut) as total_licencias_vut
            FROM fact_regulacion
            WHERE anio = ? AND zona_tensionada = 1
        """
        df = pd.read_sql_query(query, conn, params=[year])
        
        zonas_tensionadas = int(df["zonas_tensionadas"].iloc[0]) if not df.empty else 0
        total_licencias = int(df["total_licencias_vut"].iloc[0]) if not df.empty and pd.notna(df["total_licencias_vut"].iloc[0]) else 0
        
        return {
            "zonas_tensionadas": zonas_tensionadas,
            "total_licencias_vut": total_licencias,
        }
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_affordability_summary(year: int = 2024) -> dict:
    """
    Carga resumen de asequibilidad (ratio precio/renta).
    
    Args:
        year: Año a consultar.
    
    Returns:
        Diccionario con métricas de asequibilidad.
    """
    conn = get_connection()
    try:
        # Auxiliar para verificar si una tabla existe
        def table_exists(table_name: str) -> bool:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            )
            return cursor.fetchone() is not None

        if not table_exists("fact_precios") or not table_exists("fact_renta"):
            return {"ratio_precio_renta_anios": None}

        query = """
            SELECT 
                AVG(p.precio_m2_venta) as precio_medio,
                AVG(r.renta_mediana) as renta_mediana
            FROM fact_precios p
            LEFT JOIN fact_renta r ON p.barrio_id = r.barrio_id AND p.anio = r.anio
            WHERE p.anio = ? AND p.precio_m2_venta IS NOT NULL AND r.renta_mediana IS NOT NULL
        """
        df = pd.read_sql_query(query, conn, params=[year])
        
        ratio_anios = None
        if not df.empty and df["renta_mediana"].iloc[0] is not None and df["renta_mediana"].iloc[0] > 0:
            precio_medio = df["precio_medio"].iloc[0]
            renta_mediana = df["renta_mediana"].iloc[0]
            # Calcular años de renta necesarios para comprar vivienda tipo (70m²)
            precio_total = precio_medio * VIVIENDA_TIPO_M2
            ratio_anios = precio_total / renta_mediana
        
        return {
            "ratio_precio_renta_anios": ratio_anios,
        }
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_quality_of_life_data(year: int = 2022) -> pd.DataFrame:
    """
    Carga datos de calidad de vida (ruido y zonas verdes) para el mapa.
    """
    conn = get_connection()
    try:
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
            COALESCE(r.nivel_lden_medio, 0) as nivel_ruido,
            COALESCE(m.superficie_zonas_verdes_m2, 0) as m2_zonas_verdes,
            COALESCE(m.num_arboles, 0) as num_arboles
        FROM dim_barrios b
        LEFT JOIN fact_ruido r ON b.barrio_id = r.barrio_id AND r.anio = (SELECT MAX(anio) FROM fact_ruido)
        LEFT JOIN fact_medio_ambiente m ON b.barrio_id = m.barrio_id AND m.anio = (SELECT MAX(anio) FROM fact_medio_ambiente)
        """
        df = pd.read_sql(query, conn)
        
        # Proxy para zonas verdes (vectorizado) si m2_zonas_verdes es 0
        df['m2_zonas_verdes'] = df['m2_zonas_verdes'].where(df['m2_zonas_verdes'] > 0, df['num_arboles'] * 15)
        
        # Deduplicar
        df = df.drop_duplicates(subset=['barrio_id'])
        
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_gentrification_risk_metrics(year: int = 2023) -> pd.DataFrame:
    """
    Carga métricas de riesgo de gentrificación (estudios universitarios, variación de precios).
    """
    conn = get_connection()
    try:
        # Intentar cargar desde vista avanzada si existe
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre,
            COALESCE(e.pct_universitarios, 0) as pct_universitarios,
            COALESCE(d.porc_inmigracion, 0) as porc_inmigracion,
            COALESCE(d.densidad_hab_km2, 0) as densidad
        FROM dim_barrios b
        LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.year = (SELECT MAX(year) FROM fact_educacion)
        LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND d.anio = (SELECT MAX(anio) FROM fact_demografia)
        """
        df_risk = pd.read_sql(query, conn)
        
        # Calcular variación de precios a 3 años (Lead Indicator de gentrificación)
        query_prices = f"""
        SELECT barrio_id, anio, precio_m2_venta
        FROM fact_precios
        WHERE anio IN ({year}, {year-3})
        """
        df_p = pd.read_sql(query_prices, conn)
        if not df_p.empty and year in df_p['anio'].values:
            df_pivot = df_p.pivot(index='barrio_id', columns='anio', values='precio_m2_venta')
            if year-3 in df_pivot.columns:
                df_pivot['var_precio_3a'] = ((df_pivot[year] - df_pivot[year-3]) / df_pivot[year-3]) * 100
                df_risk = df_risk.merge(df_pivot[['var_precio_3a']], on='barrio_id', how='left')
        
        if 'var_precio_3a' not in df_risk.columns:
            df_risk['var_precio_3a'] = 0.0

        # Score Compuesto de Gentrificación (0-100)
        def normalize(s):
            return (s - s.min()) / (s.max() - s.min()) * 100 if (s.max() - s.min()) > 0 else 0

        df_risk['score_gentrificacion'] = (
            normalize(df_risk['pct_universitarios']) * 0.4 +
            normalize(df_risk['var_precio_3a']) * 0.4 +
            normalize(df_risk['porc_inmigracion']) * 0.2
        )
        
        return df_risk[['barrio_id', 'score_gentrificacion', 'pct_universitarios', 'var_precio_3a']]
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_investment_data(year: int = 2023) -> pd.DataFrame:
    """
    Carga datos para análisis de inversión integrando riesgo de gentrificación.
    """
    df = load_precios(year)
    if df.empty:
        return pd.DataFrame()
    
    # Calcular Yield Bruto Anual
    df['yield_bruto_pct'] = (df['avg_alquiler'] * 12 / (df['avg_precio_m2'] * VIVIENDA_TIPO_M2)) * 100
    
    # Simular Score de Liquidez
    df['score_liquidez'] = 5.0
    
    # Integrar Riesgo de Gentrificación
    df_risk = load_gentrification_risk_metrics(year)
    df = df.merge(df_risk, on='barrio_id', how='left')
    
    # Filtrar barrios sin datos de yield
    df = df[df['yield_bruto_pct'].notna() & (df['yield_bruto_pct'] > 0)]
    
    return df


@st.cache_data(ttl=3600)
def load_full_correlation_data(year: int = 2023) -> pd.DataFrame:
    """
    Carga un dataset completo para análisis de correlación avanzado.
    Incluye: Precios, Renta, Densidad, Gentrificación y Ruido.
    """
    # 1. Precios y Renta (Base)
    df = load_correlation_data(year)
    if df.empty:
        return pd.DataFrame()
        
    # 2. Gentrificación
    df_risk = load_gentrification_risk_metrics(year)
    df = df.merge(df_risk[['barrio_id', 'score_gentrificacion', 'pct_universitarios']], on='barrio_id', how='left')
    
    # 3. Calidad de Vida (Ruido)
    df_qol = load_quality_of_life_data(year)
    df = df.merge(df_qol[['barrio_id', 'nivel_ruido', 'm2_zonas_verdes']], on='barrio_id', how='left')
    
    # Rellenar nulos con medianas para no romper correlación
    df = df.fillna(df.median(numeric_only=True))
    
    return df
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
        try:
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
        except (json.JSONDecodeError, TypeError):
            continue
    return {"type": "FeatureCollection", "features": features}


@st.cache_data(ttl=3600)
def load_price_trends(distritos: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Carga la evolución temporal de precios usando precios consolidados.
    """
    years_info = load_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2022
    
    all_data = []
    for year in range(min_year, max_year + 1):
        df_year = load_precios(year)
        if not df_year.empty:
            df_year['anyo'] = year
            all_data.append(df_year)
            
    if not all_data:
        return pd.DataFrame()
        
    df = pd.concat(all_data)
    
    if distritos:
        df = df[df['distrito_nombre'].isin(distritos)]
        
    # Agrupar para obtener tendencia
    df_trends = df.groupby(['anyo', 'barrio_nombre', 'distrito_nombre']).agg({
        'avg_precio_m2': 'mean',
        'avg_alquiler': 'mean'
    }).reset_index()
    
    return df_trends.rename(columns={'avg_precio_m2': 'precio_venta_m2', 'avg_alquiler': 'precio_alquiler_m2'})


@st.cache_data(ttl=3600)
def load_demographics_by_barrio(year: int) -> pd.DataFrame:
    """
    Carga datos demográficos detallados por barrio para un año.
    
    Args:
        year: Año a consultar.
        
    Returns:
        DataFrame con métricas demográficas y nombres de barrio.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT 
                b.barrio_nombre,
                b.distrito_nombre,
                d.*
            FROM fact_demografia d
            JOIN dim_barrios b ON d.barrio_id = b.barrio_id
            WHERE d.anio = ?
            """,
            conn,
            params=[year],
        )
    finally:
            conn.close()
    return df


@st.cache_data(ttl=3600)
def load_idealista_supply(distritos: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Carga la oferta inmobiliaria actual (Idealista/Mock).
    
    Args:
        distritos: Lista opcional de distritos para filtrar.
        
    Returns:
        DataFrame con datos de oferta.
    """
    conn = get_connection()
    try:
        if not table_exists("fact_oferta_idealista"):
            return pd.DataFrame()
            
        query = """
        SELECT 
            f.*,
            b.barrio_nombre,
            b.distrito_nombre
        FROM fact_oferta_idealista f
        JOIN dim_barrios b ON f.barrio_id = b.barrio_id
        WHERE 1=1
        """
        params = []
        if distritos:
            placeholders = ",".join(["?"] * len(distritos))
            query += f" AND b.distrito_nombre IN ({placeholders})"
            params.extend(distritos)
            
        # Ordenar por el mes más reciente
        query += " ORDER BY f.anio DESC, f.mes DESC"
        
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df
