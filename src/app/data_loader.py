from __future__ import annotations

"""
Data loader module for the Barcelona Housing Dashboard.

Provides cached functions to load data from the SQLite database.
Uses Streamlit's cache to avoid reloading data on every interaction.
Updated for Market Cockpit.
"""

import json
import logging
import sqlite3
import time
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Callable, Any

import pandas as pd
import streamlit as st

from src.app.config import DB_PATH, MASTER_TABLE_CSV_PATH, VIVIENDA_TIPO_M2, PROJECT_ROOT
from src.database_setup import validate_table_name
from src.app.api_client import get_api_client
from src.database import DatabaseManager

_db_manager = DatabaseManager()
logger = logging.getLogger(__name__)

# Configurar nivel de logging según variable de entorno o secrets
LOG_LEVEL = logging.INFO
try:
    # Intentar acceder a secrets solo si estamos en contexto de Streamlit
    if hasattr(st, 'secrets'):
        try:
            log_config = st.secrets.get("logging", {})
            if isinstance(log_config, dict) and log_config.get("level", "").upper() == "DEBUG":
                LOG_LEVEL = logging.DEBUG
        except Exception:
            # st.secrets no disponible o no configurado, usar defaults
            pass
except (AttributeError, RuntimeError, KeyError):
    # st no disponible fuera del contexto de Streamlit
    pass

# También verificar variable de entorno
import os
if os.environ.get("STREAMLIT_LOGGING_LEVEL", "").upper() == "DEBUG":
    LOG_LEVEL = logging.DEBUG

logger.setLevel(LOG_LEVEL)


def log_performance(func: Callable) -> Callable:
    """
    Decorator para loggear tiempo de ejecución y métricas de funciones de carga de datos.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Log métricas según tipo de resultado
            if isinstance(result, pd.DataFrame):
                rows = len(result)
                cols = len(result.columns) if not result.empty else 0
                logger.info(
                    f"PERF | {func_name} | {elapsed_ms:.1f}ms | "
                    f"Rows: {rows} | Cols: {cols} | Args: {args} | Kwargs: {kwargs}"
                )
            elif isinstance(result, dict):
                keys = len(result)
                logger.info(
                    f"PERF | {func_name} | {elapsed_ms:.1f}ms | "
                    f"Keys: {keys} | Args: {args} | Kwargs: {kwargs}"
                )
            elif isinstance(result, list):
                items = len(result)
                logger.info(
                    f"PERF | {func_name} | {elapsed_ms:.1f}ms | "
                    f"Items: {items} | Args: {args} | Kwargs: {kwargs}"
                )
            else:
                logger.info(
                    f"PERF | {func_name} | {elapsed_ms:.1f}ms | "
                    f"Args: {args} | Kwargs: {kwargs}"
                )
            
            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(
                f"ERROR | {func_name} | {elapsed_ms:.1f}ms | "
                f"Exception: {type(e).__name__}: {str(e)} | Args: {args} | Kwargs: {kwargs}",
                exc_info=True
            )
            raise
    
    return wrapper


@contextmanager
def log_query(query_name: str, params: Optional[tuple] = None):
    """
    Context manager para loggear consultas SQL con tiempo de ejecución.
    
    Args:
        query_name: Nombre descriptivo de la consulta
        params: Parámetros de la consulta (opcional)
    """
    start_time = time.time()
    logger.debug(f"QUERY_START | {query_name} | Params: {params}")
    
    try:
        yield
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(f"QUERY_END | {query_name} | {elapsed_ms:.1f}ms | Success")
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(
            f"QUERY_ERROR | {query_name} | {elapsed_ms:.1f}ms | "
            f"Exception: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        raise


@st.cache_resource
def get_geojson() -> dict:
    """
    Carga el GeoJSON de los barrios desde un archivo estático o lo genera desde la BD (v1.1 SSOT).
    
    Returns:
        Diccionario GeoJSON FeatureCollection.
    """
    geojson_path = PROJECT_ROOT / "data" / "processed" / "barrios_geo.json"
    
    # 1. Intentar cargar desde archivo estático
    if geojson_path.exists():
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error al leer GeoJSON estático: {e}")

    # 2. Si no existe, cargar desde BD y guardar
    df_barrios = load_barrios()
    geojson = build_geojson(df_barrios)
    
    # Guardar para futuras cargas si es posible
    try:
        geojson_path.parent.mkdir(parents=True, exist_ok=True)
        with open(geojson_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"No se pudo guardar el GeoJSON estático: {e}")
        
    return geojson

def get_connection(retries: int = 3, delay: float = 0.5) -> sqlite3.Connection:
    """
    Crea una conexión a la base de datos SQLite con manejo de reintentos (v1.1 SSOT).
    Optimizado para mejor rendimiento en Streamlit con múltiples usuarios concurrentes.
    
    Args:
        retries: Número de reintentos en caso de bloqueo.
        delay: Tiempo de espera entre reintentos en segundos.
        
    Returns:
        Conexión SQLite con foreign keys habilitadas y optimizaciones PRAGMA.
        
    Nota:
        WAL mode tiene un overhead del 17-43% en escrituras con 1-2 conexiones,
        pero mejora significativamente con más usuarios concurrentes.
    """
    logger.debug("CONNECTION | get_connection | Opening new connection")
    
    for attempt in range(retries):
        try:
            conn = _db_manager.get_connection()
            # Optimizaciones PRAGMA para mejor rendimiento y concurrencia
            conn.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging para mejor concurrencia
            conn.execute("PRAGMA synchronous = NORMAL;")  # Balance entre seguridad y velocidad
            conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache (ajustable según memoria disponible)
            conn.execute("PRAGMA temp_store = MEMORY;")  # Usar memoria para temporales
            conn.execute("PRAGMA busy_timeout = 5000;")  # 5s timeout - previene lock errors en multi-usuario
            conn.execute("PRAGMA wal_autocheckpoint = 1000;")  # +12% rendimiento en inserts según benchmarks 2026
            
            # Verificar y loggear modo WAL
            wal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            logger.debug(f"CONNECTION | get_connection | WAL mode: {wal_mode}")
            
            return conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                logger.warning(f"CONNECTION | get_connection | DB locked, retry {attempt + 1}/{retries}")
                time.sleep(delay)
                continue
            logger.error(f"CONNECTION | get_connection | Failed after {retries} attempts: {e}")
            raise
    return _db_manager.get_connection()


@st.cache_data(ttl=3600)
def get_dynamic_metric_metadata() -> dict:
    """
    Enriquece los metadatos de las métricas con los años reales de la base de datos (v1.2 MVP).
    Evita valores hardcoded de años en el dashboard.
    
    Returns:
        Diccionario METRIC_METADATA actualizado.
    """
    from src.app.config import METRIC_METADATA, COLOR_SCALES
    
    # 1. Obtener años reales de la BD
    years_info = load_available_years()
    
    # 2. Clonar metadatos base
    dynamic_meta = METRIC_METADATA.copy()
    
    # 3. Actualizar "Precio Venta"
    precios_years = years_info.get("fact_precios", {})
    if precios_years.get("max"):
        dynamic_meta["Precio Venta"]["max_year"] = precios_years["max"]
        dynamic_meta["Precio Venta"]["min_year"] = precios_years["min"]
        
    # 4. Actualizar "Renta Mensual"
    renta_years = years_info.get("fact_renta", {})
    if renta_years.get("max"):
        dynamic_meta["Renta Mensual"]["max_year"] = renta_years["max"]
        dynamic_meta["Renta Mensual"]["min_year"] = renta_years["min"]
        if renta_years["min"] == renta_years["max"]:
             dynamic_meta["Renta Mensual"]["info"] = f"Datos de renta disponibles para {renta_years['max']}"
    
    # 5. Actualizar "Esfuerzo Compra" (depende de Precios y Renta)
    # Usamos el año de renta como base si es único
    if renta_years.get("max"):
        dynamic_meta["Esfuerzo Compra"]["max_year"] = renta_years["max"]
        dynamic_meta["Esfuerzo Compra"]["min_year"] = renta_years["min"]
        dynamic_meta["Esfuerzo Compra"]["info"] = f"Basado en Renta {renta_years['max']}"

    # 6. Actualizar "Demografía"
    demo_years = years_info.get("fact_demografia", {})
    if demo_years.get("max"):
        dynamic_meta["Demografía"]["max_year"] = demo_years["max"]
        dynamic_meta["Demografía"]["min_year"] = demo_years["min"]
        
    return dynamic_meta


def log_user_query(distrito: Optional[str], metric: str, year: int) -> None:
    """
    Registra la consulta del usuario para análisis estratégico (v1.1 SSOT).
    """
    logger.info(
        f"USER_QUERY | Distrito: {distrito or 'Global'} | Métrica: {metric} | Año: {year}"
    )


@st.cache_data(ttl=3600)
def load_master_table_csv() -> pd.DataFrame:
    """
    Carga la tabla maestra consolidada para BI (CSV) como fuente SSOT de métricas avanzadas.

    Esta tabla incluye métricas de:
    - Gap de negociación (asking vs transaction)
    - Riesgo de gentrificación (renta/gini + alquiler)

    Returns:
        DataFrame con una fila por barrio y año.
    """
    if not MASTER_TABLE_CSV_PATH.exists():
        logger.warning(f"No se encontró el CSV maestro en: {MASTER_TABLE_CSV_PATH}")
        return pd.DataFrame()

    df = pd.read_csv(MASTER_TABLE_CSV_PATH)

    # Normalizar tipos para evitar inconsistencias en filtros/plots
    if "anio" in df.columns:
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")

    bool_like_cols = [
        "negotiation_low_volume",
        "negotiation_extreme_gap",
        "precio_venta_faltante",
        "precio_alquiler_faltante",
        "demografia_faltante",
        "turismo_faltante",
        "seguridad_faltante",
        "calidad_baja",
        "tiene_anomalias",
    ]
    for col in bool_like_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


# Cache de verificación de tablas para evitar consultas repetidas
_table_exists_cache: dict[str, bool] = {}

def table_exists(table_name: str, conn: Optional[sqlite3.Connection] = None) -> bool:
    """
    Verifica si una tabla existe en la base de datos.
    Optimizado con cache para evitar consultas repetidas en la misma sesión.
    
    Args:
        table_name: Nombre de la tabla a verificar.
        conn: Conexión opcional a la base de datos. Si no se proporciona, crea una nueva.
        
    Returns:
        True si la tabla existe, False en caso contrario.
    """
    # Verificar cache primero
    if table_name in _table_exists_cache:
        return _table_exists_cache[table_name]
    
    _conn = conn
    close_conn = False
    
    if _conn is None:
        _conn = get_connection()
        close_conn = True
        
    try:
        cursor = _conn.execute(
            "SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name=?", (table_name,)
        )
        exists = cursor.fetchone() is not None
        # Guardar en cache
        _table_exists_cache[table_name] = exists
        return exists
    finally:
        if close_conn:
            _conn.close()


def build_geojson(df: pd.DataFrame) -> dict:
    """
    Construye un objeto GeoJSON a partir de un DataFrame con geometrías.
    
    Args:
        df: DataFrame con columnas 'barrio_id' y 'geometry_json'.
    
    Returns:
        Diccionario GeoJSON con FeatureCollection.
    """
    features = []
    
    for _, row in df.iterrows():
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
                logging.warning(f"Error parsing geometry for barrio_id {row.get('barrio_id')}: {e}")
                continue
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@st.cache_data(ttl=3600)
def load_barrios() -> pd.DataFrame:
    """
    Carga la dimensión de barrios con geometrías.
    Usa la API si está disponible, con fallback a DB local.
    """
    # 1. Intentar via API
    try:
        client = get_api_client()
        barrios_data = client.get_barrios(include_geometry=True)
        if barrios_data:
            df = pd.DataFrame(barrios_data)
            return df.sort_values("barrio_id")
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_barrios | API fallback: {e}")

    # 2. Fallback local (DB)
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT DISTINCT
                barrio_id,
                barrio_nombre,
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
    Optimizado con consulta combinada.
    """
    # 1. API (solo intentar si no sabemos que está caída)
    try:
        client = get_api_client()
        years = client.get_years()
        if years: 
            logger.debug("DATA_LOAD | load_available_years | Source: API")
            return years
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_available_years | API fallback: {e}")
        pass

    # 2. Fallback local - Optimizado con consulta combinada
    conn = get_connection()
    try:
        # Consulta combinada para obtener años de múltiples tablas en una sola query
        query = """
            SELECT 
                'fact_precios' as table_name,
                MIN(anio) as min_year,
                MAX(anio) as max_year
            FROM fact_precios
            UNION ALL
            SELECT 
                'fact_demografia' as table_name,
                MIN(anio) as min_year,
                MAX(anio) as max_year
            FROM fact_demografia
            WHERE anio IS NOT NULL
            UNION ALL
            SELECT 
                'fact_renta' as table_name,
                MIN(anio) as min_year,
                MAX(anio) as max_year
            FROM fact_renta
            WHERE anio IS NOT NULL
        """
        df = pd.read_sql(query, conn)
        
        result = {}
        for _, row in df.iterrows():
            table_name = row["table_name"]
            result[table_name] = {
                "min": int(row["min_year"]) if pd.notna(row["min_year"]) else None,
                "max": int(row["max_year"]) if pd.notna(row["max_year"]) else None,
            }
    finally:
        conn.close()
    return result


@st.cache_data(ttl=3600)
@log_performance
def load_distritos() -> list[str]:
    """
    Obtiene la lista de distritos únicos.
    Usa vista optimizada vw_resumen_por_distrito si está disponible.
    """
    logger.debug("DATA_LOAD | load_distritos | Starting")
    
    # 1. API
    try:
        client = get_api_client()
        distritos = client.get_distritos()
        if distritos:
            logger.info(f"DATA_LOAD | load_distritos | Source: API | Count: {len(distritos)}")
            return distritos
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_distritos | API fallback: {e}")

    # 2. Intentar usar vista optimizada
    if table_exists("vw_resumen_por_distrito"):
        logger.debug("DATA_LOAD | load_distritos | Using optimized view: vw_resumen_por_distrito")
        conn = get_connection()
        try:
            df = pd.read_sql(
                "SELECT DISTINCT distrito_nombre FROM vw_resumen_por_distrito ORDER BY distrito_nombre",
                conn,
            )
            result = df["distrito_nombre"].tolist()
            logger.info(f"DATA_LOAD | load_distritos | Source: Optimized view | Count: {len(result)}")
            return result
        except Exception as e:
            logger.debug(f"DATA_LOAD | load_distritos | Optimized view error, using fallback: {e}")
        finally:
            conn.close()

    # 3. Fallback original
    logger.debug("DATA_LOAD | load_distritos | Using fallback: dim_barrios")
    conn = get_connection()
    try:
        df = pd.read_sql(
            "SELECT DISTINCT distrito_nombre FROM dim_barrios ORDER BY distrito_nombre",
            conn,
        )
        result = df["distrito_nombre"].tolist()
        logger.info(f"DATA_LOAD | load_distritos | Source: Fallback | Count: {len(result)}")
        return result
    finally:
        conn.close()


@st.cache_data(ttl=3600)
@log_performance
def load_precios(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """
    Carga precios de vivienda consolidados (fact_precios + Idealista).
    """
    logger.info(f"DATA_LOAD | load_precios | Year: {year} | Distrito: {distrito or 'All'}")
    
    # 1. API
    try:
        client = get_api_client()
        data = client.get_precios(year=year, distrito=distrito, include_geometry=True)
        if data:
            df = pd.DataFrame(data)
            logger.info(f"DATA_LOAD | load_precios | Source: API | Rows: {len(df)}")
            # Match the dashboard's column expectations
            if 'avg_precio_m2' in df.columns:
                return df
            return df
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_precios | API fallback: {e}")

    # 2. Fallback local
    logger.info("DATA_LOAD | load_precios | Source: Local DB")
    conn = get_connection()
    try:
        # Verificar si podemos usar vista recent (años recientes)
        max_year_df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_precios", conn)
        max_year = int(max_year_df["max_year"].iloc[0]) if not max_year_df.empty else year
        use_recent_view = year >= (max_year - 2) and table_exists("fact_precios_recent", conn)
        
        if use_recent_view:
            logger.debug(f"DATA_LOAD | load_precios | Using optimized view: fact_precios_recent")
        
        # 1. Cargar fact_precios (usar vista recent si aplica)
        if use_recent_view:
            query_off = """
            SELECT 
                p.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
                p.precio_m2_venta, p.precio_mes_alquiler
            FROM fact_precios_recent p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.anio = ?
            """
        else:
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

        # 3. Consolidar - filter out empty or all-NA DataFrames
        dfs = [df for df in [df_off, df_id] if not df.empty and not df.isna().all().all()]
        if not dfs:
            return pd.DataFrame()
            
        df = pd.concat(dfs, ignore_index=True).groupby('barrio_id').agg({
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
        
        logger.info(
            f"DATA_LOAD | load_precios | Complete | "
            f"Rows: {len(df)} | "
            f"Barrios: {df['barrio_id'].nunique() if not df.empty else 0} | "
            f"Avg precio: {df['avg_precio_m2'].mean():.2f}€/m²" if not df.empty and 'avg_precio_m2' in df.columns else ""
        )
        
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_renta(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos de renta para un año específico.
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente disponible.
    
    Returns:
        DataFrame con barrio_id y renta_euros.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_renta", {}).get("max")
        if year is None:
            return pd.DataFrame()

    # 1. API
    try:
        client = get_api_client()
        data = client.get_renta(year=year)
        if data:
            df = pd.DataFrame(data)
            # Standardize column name if coming from fact_renta_avanzada
            if 'renta_bruta_llar' in df.columns:
                df = df.rename(columns={'renta_bruta_llar': 'renta_euros'})
            return df
    except Exception:
        pass

    # 2. Local Fallback
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


@st.cache_data(ttl=21600)  # 6 horas - datos demográficos cambian lentamente
def load_demografia(year: int) -> pd.DataFrame:
    """
    Carga datos demográficos para un año específico.
    Optimizado para usar fact_demografia_ampliada cuando fact_demografia está vacía.
    
    Args:
        year: Año a consultar.
    
    Returns:
        DataFrame con métricas demográficas por barrio, incluyendo
        pct_mayores_65, pct_menores_15 e indice_envejecimiento.
    """
    conn = get_connection()
    try:
        # Intentar primero fact_demografia
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
        
        # Si está vacía, intentar fact_demografia_ampliada y agregar
        if df.empty and table_exists("fact_demografia_ampliada", conn):
            df_ampliada = pd.read_sql(
                """
                SELECT 
                    barrio_id,
                    SUM(CASE WHEN sexo = 'Total' AND grupo_edad = 'Total' THEN poblacion ELSE 0 END) as poblacion_total,
                    SUM(CASE WHEN sexo = 'Hombres' AND grupo_edad = 'Total' THEN poblacion ELSE 0 END) as poblacion_hombres,
                    SUM(CASE WHEN sexo = 'Mujeres' AND grupo_edad = 'Total' THEN poblacion ELSE 0 END) as poblacion_mujeres,
                    NULL as hogares_totales,
                    NULL as edad_media,
                    NULL as porc_inmigracion,
                    NULL as densidad_hab_km2,
                    NULL as pct_mayores_65,
                    NULL as pct_menores_15,
                    NULL as indice_envejecimiento
                FROM fact_demografia_ampliada
                WHERE anio = ?
                GROUP BY barrio_id
                """,
                conn,
                params=[year],
            )
            if not df_ampliada.empty:
                df = df_ampliada
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_affordability_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos combinados para análisis de esfuerzo de compra usando precios consolidados.
    
    Args:
        year: Año para precios. Si es None, usa el más reciente.
    
    Returns:
        DataFrame con precio, renta y effort_ratio por barrio.
    """
    years_info = load_available_years()
    if year is None:
        year = years_info.get("fact_precios", {}).get("max") or 2023

    # 1. Cargar precios consolidados
    df_precios = load_precios(year)
    if df_precios.empty:
        return pd.DataFrame()
        
    # 2. Cargar renta (usar el año más reciente disponible)
    income_year = years_info.get("fact_renta", {}).get("max")
    if income_year is None:
        return pd.DataFrame()
        
    df_renta = load_renta(income_year)
    
    # 3. Combinar
    df = df_precios.merge(df_renta, on='barrio_id', how='inner')
    
    # 4. Calcular ratio
    df['effort_ratio'] = (df['avg_precio_m2'] * VIVIENDA_TIPO_M2) / df['renta_euros']
    
    # Filtrar nulos
    df = df[df['effort_ratio'].notna()]
    
    return df


@st.cache_data(ttl=3600)
def load_temporal_comparison(year_start: Optional[int] = None, year_end: Optional[int] = None) -> pd.DataFrame:
    """
    Carga comparación temporal de precios usando precios consolidados.
    """
    years_info = load_available_years()
    if year_start is None:
        year_start = years_info.get("fact_precios", {}).get("min") or 2015
    if year_end is None:
        year_end = years_info.get("fact_precios", {}).get("max") or 2023

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
    
    # 4. Cargar renta y calcular esfuerzo (usar el año más reciente disponible)
    income_year = years_info.get("fact_renta", {}).get("max")
    if income_year:
        df_renta = load_renta(income_year)
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
def load_correlation_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos para análisis de correlación.
    Optimizado para usar vistas cuando es apropiado.
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente.
    
    Returns:
        DataFrame con precio, renta, densidad y población.
    """
    # Determinar mejores años disponibles para fallback
    years_info = load_available_years()
    if year is None:
        year = years_info.get("fact_precios", {}).get("max") or 2023

    income_years = years_info.get("fact_renta", {})
    income_year = year if income_years.get("min") and income_years.get("max") and income_years["min"] <= year <= income_years["max"] else (income_years.get("max") or 2022)
    
    demo_years = years_info.get("fact_demografia", {})
    demo_year = min(year, demo_years.get("max") or 2025)
    
    conn = get_connection()
    try:
        # Usar vista recent para precios si el año es reciente
        max_year = years_info.get("fact_precios", {}).get("max") or year
        use_recent_view = year >= (max_year - 2) and table_exists("fact_precios_recent", conn)
        
        precios_table = "fact_precios_recent" if use_recent_view else "fact_precios"
        
        query = f"""
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
                FROM {precios_table}
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
@log_performance
def load_kpis() -> dict:
    """
    Calcula KPIs globales del proyecto.
    Optimizado para usar una sola consulta combinada cuando es posible.
    
    Returns:
        Diccionario con métricas clave.
    """
    logger.info("DATA_LOAD | load_kpis | Starting")
    
    # 1. API
    try:
        client = get_api_client()
        kpis = client.get_api_kpis()
        if kpis:
            logger.info("DATA_LOAD | load_kpis | Source: API")
            return kpis
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_kpis | API fallback: {e}")

    # 2. Local Fallback - Optimizado con consulta combinada
    logger.info("DATA_LOAD | load_kpis | Source: Local DB")
    conn = get_connection()
    try:
        # Consulta combinada para obtener múltiples métricas en una sola query
        # Esto reduce el número de round-trips a la BD
        query = """
            WITH stats AS (
                SELECT 
                    (SELECT COUNT(*) FROM dim_barrios) as total_barrios,
                    (SELECT COUNT(*) FROM dim_barrios WHERE geometry_json IS NOT NULL) as barrios_con_geometria,
                    (SELECT COUNT(*) FROM fact_precios) as registros_precios,
                    (SELECT MIN(anio) FROM fact_precios) as min_year,
                    (SELECT MAX(anio) FROM fact_precios) as max_year
            ),
            precios_stats AS (
                SELECT 
                    anio,
                    AVG(precio_m2_venta) as avg_precio,
                    AVG(precio_mes_alquiler) as avg_alquiler
                FROM fact_precios
                WHERE anio IN (
                    (SELECT MAX(anio) FROM fact_precios),
                    (SELECT MAX(anio) - 1 FROM fact_precios)
                )
                AND precio_m2_venta IS NOT NULL
                GROUP BY anio
            )
            SELECT 
                s.*,
                p_curr.avg_precio as precio_curr,
                p_prev.avg_precio as precio_prev,
                p_curr.avg_alquiler as alquiler_curr
            FROM stats s
            LEFT JOIN precios_stats p_curr ON p_curr.anio = s.max_year
            LEFT JOIN precios_stats p_prev ON p_prev.anio = s.max_year - 1
        """
        
        df = pd.read_sql(query, conn)
        
        if df.empty:
            return {
                "total_barrios": 0,
                "barrios_con_geometria": 0,
                "registros_precios": 0,
                "año_min": None,
                "año_max": None,
                "precio_medio_actual": 0.0,
                "precio_medio_anterior": 0.0,
                "alquiler_medio_actual": 0.0,
                "renta_media_actual": 0.0,
                "yield_ciudad_pct": 0.0,
                "variacion_anual_pct": 0.0
            }
        
        row = df.iloc[0]
        max_year = int(row["max_year"]) if pd.notna(row["max_year"]) else 2022
        precio_curr = float(row["precio_curr"]) if pd.notna(row["precio_curr"]) else 0.0
        precio_prev = float(row["precio_prev"]) if pd.notna(row["precio_prev"]) else 0.0
        alquiler_curr = float(row["alquiler_curr"]) if pd.notna(row["alquiler_curr"]) else 0.0
        
        # Renta media (consulta separada si es necesario)
        income_years = load_available_years().get("fact_renta", {})
        max_income_year = income_years.get("max")
        renta_curr = 0.0
        
        if max_income_year:
            renta_query = """
                SELECT COALESCE(AVG(renta_mediana), AVG(renta_euros)) as avg_renta
                FROM fact_renta 
                WHERE anio = ?
            """
            renta_df = pd.read_sql(renta_query, conn, params=[max_income_year])
            if not renta_df.empty and pd.notna(renta_df["avg_renta"].iloc[0]):
                renta_curr = float(renta_df["avg_renta"].iloc[0])

        # Cálculos de Inteligencia de Negocio
        yield_pct = 0.0
        if precio_curr > 0 and alquiler_curr > 0:
            yield_pct = (alquiler_curr * 12) / (precio_curr * VIVIENDA_TIPO_M2) * 100

        yoy_growth_pct = 0.0
        if precio_prev > 0:
            yoy_growth_pct = ((precio_curr - precio_prev) / precio_prev) * 100

        result = {
            "total_barrios": int(row["total_barrios"]),
            "barrios_con_geometria": int(row["barrios_con_geometria"]),
            "registros_precios": int(row["registros_precios"]),
            "año_min": int(row["min_year"]) if pd.notna(row["min_year"]) else None,
            "año_max": max_year,
            "precio_medio_actual": precio_curr,
            "precio_medio_anterior": precio_prev,
            "alquiler_medio_actual": alquiler_curr,
            "renta_media_actual": renta_curr,
            "yield_ciudad_pct": yield_pct,
            "variacion_anual_pct": yoy_growth_pct
        }
        logger.info(
            f"DATA_LOAD | load_kpis | Complete | "
            f"Barrios: {result['total_barrios']} | "
            f"Precio medio: {precio_curr:.2f}€/m² | "
            f"Yield: {yield_pct:.2f}%"
        )
        return result
    finally:
        conn.close()


@st.cache_data(ttl=1800)  # TTL más corto para datos que pueden cambiar más frecuentemente
def load_critical_kpis(year: int = 2024, barrio_id: Optional[int] = None) -> dict:
    """
    Carga KPIs críticos para el Market Cockpit con búsqueda inteligente de datos recientes.
    Optimizado para usar vistas recent cuando es apropiado.
    Permite filtrar por barrio_id específico.
    """
    conn = get_connection()
    try:
        # Determinar si podemos usar vistas recent
        max_year_df = pd.read_sql("SELECT MAX(anio) as max_year FROM fact_precios", conn)
        max_year = int(max_year_df["max_year"].iloc[0]) if not max_year_df.empty else year
        use_recent_views = year >= (max_year - 2)
        result = {
            "precio_vs_indice": {"value": None, "trend": None},
            "presion_turistica": {"value": None, "trend": None},
            "criminalidad": {"value": None, "trend": None},
            "ruido": {"value": None, "trend": None},
        }

        # Cláusula de filtrado por barrio (v1.2 MVP - Seguro contra SQLi)
        barrio_filter = " AND p.barrio_id = ?" if barrio_id else ""
        barrio_filter_simple = " AND barrio_id = ?" if barrio_id else ""
        
        params_base = [year]
        if barrio_id:
            params_base.append(barrio_id)

        # 1. Precio vs Índice (Fallback inteligente)
        if table_exists("fact_precios", conn) and table_exists("fact_regulacion", conn):
            try:
                # Buscamos el año con datos más cercano al seleccionado (hacia atrás)
                query_target = f"""
                    SELECT 
                        AVG(p.precio_mes_alquiler) as avg_rent,
                        AVG(r.indice_referencia_alquiler) as avg_idx,
                        p.anio
                    FROM fact_precios p
                    JOIN fact_regulacion r ON p.barrio_id = r.barrio_id AND p.anio = r.anio
                    WHERE p.anio <= ? AND p.precio_mes_alquiler > 0 AND r.indice_referencia_alquiler > 0
                    {barrio_filter}
                    GROUP BY p.anio
                    ORDER BY p.anio DESC
                    LIMIT 1
                """
                df = pd.read_sql_query(query_target, conn, params=params_base)
                if not df.empty:
                    current_val = ((df['avg_rent'].iloc[0] / (df['avg_idx'].iloc[0] * VIVIENDA_TIPO_M2)) - 1) * 100
                    result["precio_vs_indice"]["value"] = current_val
                    
                    # Tendencia (vs año anterior del encontrado)
                    target_year = int(df['anio'].iloc[0])
                    params_prev = [target_year - 1]
                    if barrio_id:
                        params_prev.append(barrio_id)
                        
                    df_prev = pd.read_sql_query(query_target, conn, params=params_prev)
                    if not df_prev.empty:
                        prev_val = ((df_prev['avg_rent'].iloc[0] / (df_prev['avg_idx'].iloc[0] * VIVIENDA_TIPO_M2)) - 1) * 100
                        result["precio_vs_indice"]["trend"] = current_val - prev_val
            except Exception as e:
                logger.warning(f"Error KPI Precio/Índice: {e}")

        # 2. Presión Turística (usar vista recent si aplica)
        if table_exists("fact_presion_turistica", conn):
            try:
                # Usar vista recent si el año es reciente
                table_name = "fact_presion_turistica_recent" if (use_recent_views and table_exists("fact_presion_turistica_recent", conn)) else "fact_presion_turistica"
                query_air = f"SELECT SUM(num_listings_airbnb) as total, anio FROM {table_name} WHERE anio <= ? {barrio_filter_simple} GROUP BY anio HAVING total > 0 ORDER BY anio DESC LIMIT 1"
                df_air = pd.read_sql_query(query_air, conn, params=params_base)
                
                # población
                demo_table = "v_demografia_aggregated" if table_exists("v_demografia_aggregated", conn) else "fact_demografia"
                if barrio_id:
                    query_pop = f"SELECT poblacion_total as total FROM {demo_table} WHERE barrio_id = ? AND anio = (SELECT MAX(anio) FROM {demo_table} WHERE barrio_id = ?)"
                    df_pop = pd.read_sql_query(query_pop, conn, params=[barrio_id, barrio_id])
                else:
                    query_pop = f"SELECT SUM(poblacion_total) as total FROM {demo_table} WHERE anio = (SELECT MAX(anio) FROM {demo_table})"
                    df_pop = pd.read_sql_query(query_pop, conn)
                
                total_pop = df_pop['total'].iloc[0] if not df_pop.empty else (1600000 if not barrio_id else 20000)
                
                if not df_air.empty and total_pop > 0:
                    val = (df_air['total'].iloc[0] / total_pop) * 100
                    result["presion_turistica"]["value"] = val
                    
                    # Tendencia
                    target_year = int(df_air['anio'].iloc[0])
                    params_air_prev = [target_year - 1]
                    if barrio_id:
                        params_air_prev.append(barrio_id)
                    df_air_prev = pd.read_sql_query(query_air, conn, params=params_air_prev)
                    if not df_air_prev.empty:
                        prev_val = (df_air_prev['total'].iloc[0] / total_pop) * 100
                        result["presion_turistica"]["trend"] = val - prev_val
            except Exception as e:
                logger.warning(f"Error KPI Turismo: {e}")

        # 3. Criminalidad
        if table_exists("fact_seguridad", conn):
            try:
                # Intentamos obtener la tasa real, si es 0 usamos delitos/población
                query_crime = f"""
                    SELECT 
                        AVG(CASE WHEN tasa_criminalidad_1000hab > 0 THEN tasa_criminalidad_1000hab ELSE (delitos_patrimonio * 1000.0 / 20000.0) END) as rate,
                        anio
                    FROM fact_seguridad 
                    WHERE anio <= ? {barrio_filter_simple}
                    GROUP BY anio
                    ORDER BY anio DESC
                    LIMIT 1
                """
                df = pd.read_sql_query(query_crime, conn, params=params_base)
                if not df.empty and df['rate'].iloc[0] > 0:
                    val = df['rate'].iloc[0]
                    result["criminalidad"]["value"] = val
                    target_year = int(df['anio'].iloc[0])
                    
                    params_crime_prev = [target_year - 1]
                    if barrio_id:
                        params_crime_prev.append(barrio_id)
                    df_prev = pd.read_sql_query(query_crime, conn, params=params_crime_prev)
                    if not df_prev.empty:
                        result["criminalidad"]["trend"] = val - df_prev['rate'].iloc[0]
            except Exception as e:
                logger.warning(f"Error KPI Crimen: {e}")

        # 4. Ruido
        if table_exists("fact_ruido", conn):
            try:
                if barrio_id:
                    sql = "SELECT nivel_lden_medio FROM fact_ruido WHERE anio <= ? AND barrio_id = ? AND nivel_lden_medio > 0 ORDER BY anio DESC LIMIT 1"
                    df_noise = pd.read_sql_query(sql, conn, params=[year, barrio_id])
                else:
                    sql = "SELECT AVG(nivel_lden_medio) as nivel_lden_medio FROM fact_ruido WHERE anio = (SELECT MAX(anio) FROM fact_ruido WHERE anio <= ?)"
                    df_noise = pd.read_sql_query(sql, conn, params=[year])
                
                if not df_noise.empty and df_noise['nivel_lden_medio'].iloc[0] is not None:
                    result["ruido"]["value"] = float(df_noise['nivel_lden_medio'].iloc[0])
            except Exception as e:
                logger.warning(f"Error KPI Ruido: {e}")

        return result
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_top_vulnerable_barrios(year: Optional[int] = None, top_n: int = 5) -> pd.DataFrame:
    """
    Carga los barrios más vulnerables según score de riesgo de gentrificación.
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente.
        top_n: Número de barrios a retornar.
    
    Returns:
        DataFrame con barrios ordenados por score de vulnerabilidad.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

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
def load_regulation_summary(year: Optional[int] = None) -> dict:
    """
    Carga resumen de regulación (zonas tensionadas, licencias VUT) (v1.2 MVP).
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente.
    
    Returns:
        Diccionario con métricas de regulación.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    conn = get_connection()
    try:
        if not table_exists("fact_regulacion", conn):
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
def load_affordability_summary(year: Optional[int] = None) -> dict:
    """
    Carga resumen de asequibilidad (ratio precio/renta) (v1.2 MVP).
    
    Args:
        year: Año a consultar. Si es None, usa el más reciente.
    
    Returns:
        Diccionario con métricas de asequibilidad.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    conn = get_connection()
    try:
        if not table_exists("fact_precios", conn) or not table_exists("fact_renta", conn):
            return {"ratio_precio_renta_anios": None}

        query = """
            SELECT 
                AVG(p.precio_m2_venta) as precio_medio,
                AVG(COALESCE(r.renta_mediana, r.renta_promedio, r.renta_euros)) as renta_euros
            FROM fact_precios p
            LEFT JOIN fact_renta r ON p.barrio_id = r.barrio_id AND p.anio = ?
            WHERE p.anio = ? AND p.precio_m2_venta IS NOT NULL AND (r.renta_mediana IS NOT NULL OR r.renta_promedio IS NOT NULL OR r.renta_euros IS NOT NULL)
        """
        df = pd.read_sql_query(query, conn, params=[year, year])
        
        if df.empty or pd.isna(df["renta_euros"].iloc[0]):
            income_years = load_available_years().get("fact_renta", {})
            max_income_year = income_years.get("max")
            if max_income_year:
                df = pd.read_sql_query(query, conn, params=[max_income_year, year])
        
        ratio_anios = None
        if not df.empty and df["renta_euros"].iloc[0] is not None and df["renta_euros"].iloc[0] > 0:
            precio_medio = df["precio_medio"].iloc[0]
            renta_euros = df["renta_euros"].iloc[0]
            
            # Ratio: (Precio_m2 * 70) / Renta_anual
            ratio_anios = (precio_medio * VIVIENDA_TIPO_M2) / renta_euros
            
        return {
            "ratio_precio_renta_anios": float(ratio_anios) if ratio_anios else None,
        }
    finally:
        conn.close()


@st.cache_data(ttl=3600)
def load_quality_of_life_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos de calidad de vida (ruido y zonas verdes) para el mapa (v1.2 MVP).
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    conn = get_connection()
    try:
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.geometry_json,
            COALESCE(r.nivel_lden_medio, 0) as nivel_ruido,
            COALESCE(m.superficie_zonas_verdes_m2, 0) as m2_zonas_verdes,
            COALESCE(m.num_arboles, 0) as num_arboles
        FROM dim_barrios b
        LEFT JOIN fact_ruido r ON b.barrio_id = r.barrio_id AND r.anio = (SELECT MAX(anio) FROM fact_ruido WHERE anio <= ?)
        LEFT JOIN fact_medio_ambiente m ON b.barrio_id = m.barrio_id AND m.anio = (SELECT MAX(anio) FROM fact_medio_ambiente WHERE anio <= ?)
        """
        df = pd.read_sql(query, conn, params=[year, year])
        
        # Proxy para zonas verdes (vectorizado) si m2_zonas_verdes es 0
        df['m2_zonas_verdes'] = df['m2_zonas_verdes'].where(df['m2_zonas_verdes'] > 0, df['num_arboles'] * 15)
        
        # Deduplicar
        df = df.drop_duplicates(subset=['barrio_id'])
        
    finally:
        conn.close()
    return df


@st.cache_data(ttl=3600)
def load_gentrification_risk_metrics(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga métricas de riesgo de gentrificación (estudios universitarios, variación de precios) (v1.2 MVP).
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    conn = get_connection()
    try:
        # Use v_demografia_aggregated and calculate proxies
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre,
            COALESCE(e.num_centros_universidad, 0) as num_universidades,
            COALESCE(d.porc_inmigracion, 0) as porc_inmigracion,
            COALESCE(d.poblacion_total, 0) as poblacion_total
        FROM dim_barrios b
        LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = (SELECT MAX(anio) FROM fact_educacion WHERE anio <= ?)
        LEFT JOIN v_demografia_aggregated d ON b.barrio_id = d.barrio_id AND d.anio = (SELECT MAX(anio) FROM v_demografia_aggregated WHERE anio <= ?)
        """
        df_risk = pd.read_sql(query, conn, params=[year, year])
        
        # Calculate education proxy: universities per 10k population
        df_risk['pct_universitarios'] = 0.0
        mask = df_risk['poblacion_total'] > 0
        df_risk.loc[mask, 'pct_universitarios'] = (
            df_risk.loc[mask, 'num_universidades'] / df_risk.loc[mask, 'poblacion_total'] * 10000
        )
        
        # Calcular variación de precios a 3 años (Lead Indicator de gentrificación)
        query_prices = """
        SELECT barrio_id, anio, AVG(precio_m2_venta) as precio_m2_venta
        FROM fact_precios
        WHERE anio IN (?, ?) AND precio_m2_venta IS NOT NULL
        GROUP BY barrio_id, anio
        """
        df_p = pd.read_sql(query_prices, conn, params=[year, year-3])
        if not df_p.empty and year in df_p['anio'].values:
            # Extra safety: drop duplicates if any (shouldn't happen with GROUP BY)
            df_p = df_p.drop_duplicates(subset=['barrio_id', 'anio'])
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
def load_investment_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga datos para análisis de inversión con alineación estratégica (v1.2 MVP):
    - X: Venta: Precio Oferta (bhl3ulphi5)
    - Y: Alquiler: Mensual (b37xv8wcjh - Incasòl)
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    df = pd.DataFrame()
    
    # 1. Intentar via API Specialized Endpoint
    try:
        client = get_api_client()
        data = client.get_investment_stats(year=year)
        if data:
            df = pd.DataFrame(data)
    except Exception as e:
        logger.debug(f"DATA_LOAD | load_investment_data | API fallback: {e}")

    # 2. Fallback Local Direct SQL (Specialized Query)
    if df.empty:
        conn = get_connection()
        try:
            query = """
            WITH offer_prices AS (
                SELECT barrio_id, AVG(precio_m2_venta) as entry_cost
                FROM fact_precios
                WHERE anio = ? AND dataset_id = 'bhl3ulphi5'
                GROUP BY barrio_id
            ),
            contract_rents AS (
                SELECT barrio_id, AVG(precio_mes_alquiler) as rental_income
                FROM fact_precios
                WHERE anio = ? AND dataset_id = 'b37xv8wcjh'
                GROUP BY barrio_id
            )
            SELECT 
                b.barrio_id, b.barrio_nombre, b.distrito_nombre,
                o.entry_cost as avg_precio_m2,
                c.rental_income as avg_alquiler
            FROM dim_barrios b
            JOIN offer_prices o ON b.barrio_id = o.barrio_id
            JOIN contract_rents c ON b.barrio_id = c.barrio_id
            """
            df = pd.read_sql(query, conn, params=[year, year])
        except Exception as e:
            logger.error(f"Error en fallback local de inversión: {e}")
        finally:
            conn.close()

    if df.empty:
        return pd.DataFrame()
    
    # Calcular Yield Bruto Anual basado en métricas alineadas
    # Formula: (Mes_Alquiler_Contrato * 12) / (Precio_M2_Oferta * 70)
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
def load_full_correlation_data(year: Optional[int] = None) -> pd.DataFrame:
    """
    Carga un dataset completo para análisis de correlación avanzado (v1.2 MVP).
    Incluye: Precios, Renta, Densidad, Gentrificación y Ruido.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

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


@st.cache_data(ttl=3600)
def load_price_trends(distritos: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Carga la evolución temporal de precios usando precios consolidados.
    Optimizado para usar una sola consulta SQL en lugar de múltiples llamadas.
    """
    years_info = load_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2022
    
    # Optimización: usar consulta SQL directa en lugar de múltiples llamadas a load_precios
    conn = get_connection()
    try:
        # Construir filtro de distritos si aplica
        distrito_filter = ""
        params = [min_year, max_year]
        if distritos:
            placeholders = ",".join(["?"] * len(distritos))
            distrito_filter = f" AND b.distrito_nombre IN ({placeholders})"
            params.extend(distritos)
        
        query = f"""
            SELECT 
                p.anio as anyo,
                b.barrio_nombre,
                b.distrito_nombre,
                AVG(p.precio_m2_venta) as precio_venta_m2,
                AVG(p.precio_mes_alquiler) as precio_alquiler_m2
            FROM fact_precios p
            JOIN dim_barrios b ON p.barrio_id = b.barrio_id
            WHERE p.anio BETWEEN ? AND ?
            AND p.precio_m2_venta IS NOT NULL
            {distrito_filter}
            GROUP BY p.anio, b.barrio_id, b.barrio_nombre, b.distrito_nombre
            ORDER BY p.anio, b.barrio_nombre
        """
        
        df = pd.read_sql(query, conn, params=params)
        
        if df.empty:
            return pd.DataFrame()
        
        return df
    finally:
        conn.close()


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
            FROM v_demografia_aggregated d
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
        if not table_exists("fact_oferta_idealista", conn):
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
@st.cache_data(ttl=3600)
@log_performance
def load_accessibility_metrics(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """Load social infrastructure accessibility metrics."""
    # 1. API
    try:
        client = get_api_client()
        data = client.get_accessibility_metrics(year=year, distrito=distrito)
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass

    # 2. Local Fallback
    conn = get_connection()
    try:
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre, b.distrito_nombre,
            e.total_centros_educativos, e.num_centros_infantil,
            e.num_centros_primaria, e.num_centros_secundaria,
            e.num_centros_universidad,
            v.viviendas_publicas
        FROM dim_barrios b
        LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND e.anio = ?
        LEFT JOIN fact_vivienda_publica v ON b.barrio_id = v.barrio_id AND v.anio = ?
        """
        params = [year, year]
        if distrito:
            query += " WHERE b.distrito_nombre = ?"
            params.append(distrito)
        
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

@st.cache_data(ttl=3600)
@log_performance
def load_safety_metrics(year: int, distrito: Optional[str] = None) -> pd.DataFrame:
    """Load safety and tourism pressure metrics."""
    # 1. API
    try:
        client = get_api_client()
        data = client.get_safety_metrics(year=year, distrito=distrito)
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass

    # 2. Local Fallback
    conn = get_connection()
    try:
        query = """
        SELECT 
            b.barrio_id, b.barrio_nombre, b.distrito_nombre,
            s.tasa_criminalidad, s.num_delitos,
            t.num_listings, t.pct_entire_homes, t.avg_price_night, t.occupancy_rate
        FROM dim_barrios b
        LEFT JOIN fact_seguridad s ON b.barrio_id = s.barrio_id AND s.anio = ?
        LEFT JOIN fact_presion_turistica t ON b.barrio_id = t.barrio_id AND t.anio = ?
        """
        params = [year, year]
        if distrito:
            query += " WHERE b.distrito_nombre = ?"
            params.append(distrito)
            
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

@st.cache_data(ttl=3600)
@log_performance
def load_equity_metrics() -> pd.DataFrame:
    """Load model fairness and equity metrics."""
    # 1. API
    try:
        client = get_api_client()
        data = client.get_equity_metrics()
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass

    # 2. Local Fallback
    conn = get_connection()
    try:
        if not table_exists("fact_model_fairness", conn):
            # Fallback hardcoded values if table doesn't exist yet (Phase 3 results)
            return pd.DataFrame([{
                "model_version": "V2-Optimized (Baseline)",
                "mae": 409.40,
                "r2": 0.7591,
                "ges": 0.4266,
                "ipr": 1.0027,
                "etl_loaded_at": "Fallback"
            }])
            
        return pd.read_sql("SELECT * FROM fact_model_fairness ORDER BY etl_loaded_at DESC", conn)
    finally:
        conn.close()
