"""
Funciones optimizadas de data_loader que usan las nuevas vistas de la base de datos.

Estas funciones proporcionan mejor rendimiento usando:
- vw_kpis_por_barrio_anio: Para KPIs agregados
- vw_resumen_por_distrito: Para resúmenes por distrito
- *_recent views: Para datos recientes (últimos 3 años)

Mantiene compatibilidad hacia atrás: si las vistas no existen, hace fallback
a las funciones originales.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Optional

import pandas as pd
import streamlit as st

from src.app.data_loader import get_connection, table_exists
from src.database import DatabaseManager

_db_manager = DatabaseManager()
logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)
def load_distritos_optimized() -> list[str]:
    """
    Obtiene la lista de distritos únicos usando la vista optimizada.
    
    Returns:
        Lista de nombres de distritos ordenados.
    """
    # Intentar usar vista optimizada
    if table_exists("vw_resumen_por_distrito"):
        conn = get_connection()
        try:
            df = pd.read_sql(
                "SELECT DISTINCT distrito_nombre FROM vw_resumen_por_distrito ORDER BY distrito_nombre",
                conn,
            )
            return df["distrito_nombre"].tolist()
        except Exception as e:
            logger.warning(f"Error usando vw_resumen_por_distrito, usando fallback: {e}")
        finally:
            conn.close()
    
    # Fallback a método original
    from src.app.data_loader import load_distritos
    return load_distritos()


@st.cache_data(ttl=3600)
def load_kpis_by_barrio_optimized(year: int, barrio_id: Optional[int] = None) -> pd.DataFrame:
    """
    Carga KPIs por barrio y año usando la vista optimizada vw_kpis_por_barrio_anio.
    
    Args:
        year: Año a consultar.
        barrio_id: ID del barrio (opcional). Si es None, retorna todos los barrios.
    
    Returns:
        DataFrame con KPIs agregados por barrio y año.
    """
    if not table_exists("vw_kpis_por_barrio_anio"):
        logger.warning("Vista vw_kpis_por_barrio_anio no existe, usando método original")
        # Fallback: construir manualmente
        return _load_kpis_fallback(year, barrio_id)
    
    conn = get_connection()
    try:
        if barrio_id:
            query = """
                SELECT * FROM vw_kpis_por_barrio_anio
                WHERE anio = ? AND barrio_id = ?
            """
            df = pd.read_sql(query, conn, params=[year, barrio_id])
        else:
            query = """
                SELECT * FROM vw_kpis_por_barrio_anio
                WHERE anio = ?
            """
            df = pd.read_sql(query, conn, params=[year])
        
        return df
    except Exception as e:
        logger.error(f"Error cargando KPIs optimizados: {e}")
        return _load_kpis_fallback(year, barrio_id)
    finally:
        conn.close()


def _load_kpis_fallback(year: int, barrio_id: Optional[int] = None) -> pd.DataFrame:
    """
    Fallback: Construye KPIs manualmente si la vista no está disponible.
    """
    conn = get_connection()
    try:
        barrio_filter = " AND b.barrio_id = ?" if barrio_id else ""
        params = [year]
        if barrio_id:
            params.append(barrio_id)
        
        query = f"""
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                b.distrito_nombre,
                p.anio,
                p.precio_m2_venta,
                p.precio_mes_alquiler,
                d.poblacion_total,
                d.hogares_totales,
                d.densidad_hab_km2,
                r.renta_promedio,
                e.total_centros_educativos,
                c.densidad_comercial_por_1000hab,
                s.densidad_servicios_por_1000hab
            FROM dim_barrios b
            LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND p.anio = ?
            LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND d.anio = ?
            LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND r.anio = ?
            LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = ?
            LEFT JOIN fact_comercio c ON b.barrio_id = c.barrio_id AND c.anio = ?
            LEFT JOIN fact_servicios_salud s ON b.barrio_id = s.barrio_id AND s.anio = ?
            WHERE 1=1 {barrio_filter}
        """.replace("WHERE 1=1 ", "WHERE " if not barrio_filter else "")
        
        df = pd.read_sql(query, conn, params=params * 6 + ([barrio_id] if barrio_id else []))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_precios_recent_optimized(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Carga precios recientes usando la vista fact_precios_recent.
    Consolida múltiples registros por barrio igual que la función original.
    
    Args:
        year: Año a consultar (debe ser >= año máximo - 2 para usar vista recent).
        distrito: Nombre del distrito para filtrar (opcional).
    
    Returns:
        DataFrame con precios de vivienda consolidados (un registro por barrio).
    """
    # Verificar si el año es reciente (últimos 3 años)
    conn = get_connection()
    try:
        # Obtener año máximo
        max_year_df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_precios", conn)
        max_year = int(max_year_df["max_year"].iloc[0]) if not max_year_df.empty else year
        
        # Usar vista recent si el año está en el rango reciente
        use_recent_view = year >= (max_year - 2) and table_exists("fact_precios_recent")
        
        if use_recent_view:
            query = """
                SELECT 
                    p.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                    p.precio_m2_venta, p.precio_mes_alquiler
                FROM fact_precios_recent p
                JOIN dim_barrios b ON p.barrio_id = b.barrio_id
                WHERE p.anio = ?
            """
            params = [year]
            
            if distrito:
                query += " AND b.distrito_nombre = ?"
                params.append(distrito)
            
            df = pd.read_sql(query, conn, params=params)
            
            # Consolidar múltiples registros por barrio (igual que función original)
            if not df.empty:
                df = df.groupby('barrio_id').agg({
                    'barrio_nombre': 'first',
                    'distrito_nombre': 'first',
                    'geometry_json': 'first',
                    'precio_m2_venta': 'max',  # Usar máximo para consolidar
                    'precio_mes_alquiler': 'max'
                }).reset_index()
                
                # Renombrar para compatibilidad
                df = df.rename(columns={
                    'precio_m2_venta': 'avg_precio_m2',
                    'precio_mes_alquiler': 'avg_alquiler'
                })
                
                # Deduplicar final por seguridad
                df = df.drop_duplicates(subset=['barrio_id'])
            
            return df
        else:
            # Fallback a método original
            from src.app.data_loader import load_precios
            return load_precios(year, distrito)
            
    except Exception as e:
        logger.warning(f"Error usando vista recent, usando fallback: {e}")
        from src.app.data_loader import load_precios
        return load_precios(year, distrito)
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_distrito_summary_optimized() -> pd.DataFrame:
    """
    Carga resumen por distrito usando la vista optimizada.
    
    Returns:
        DataFrame con resumen agregado por distrito.
    """
    if not table_exists("vw_resumen_por_distrito"):
        logger.warning("Vista vw_resumen_por_distrito no existe")
        return pd.DataFrame()
    
    conn = get_connection()
    try:
        df = pd.read_sql(
            "SELECT * FROM vw_resumen_por_distrito ORDER BY distrito_nombre",
            conn
        )
        return df
    except Exception as e:
        logger.error(f"Error cargando resumen de distritos: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def is_recent_year(year: int) -> bool:
    """
    Verifica si un año está en el rango "reciente" (últimos 3 años).
    
    Args:
        year: Año a verificar.
    
    Returns:
        True si el año es reciente, False en caso contrario.
    """
    conn = get_connection()
    try:
        max_year_df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_precios", conn)
        max_year = int(max_year_df["max_year"].iloc[0]) if not max_year_df.empty else year
        return year >= (max_year - 2)
    finally:
        conn.close()
