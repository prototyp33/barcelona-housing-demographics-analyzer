"""
Componente de monitoreo de rendimiento para el dashboard Streamlit.

Muestra métricas de rendimiento y logging en tiempo real.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import streamlit as st

from src.app.config import PROJECT_ROOT


def setup_logging_to_file(log_level: int = logging.INFO) -> logging.Handler:
    """
    Configura logging a archivo para monitoreo persistente.
    
    Args:
        log_level: Nivel de logging (INFO, DEBUG, etc.)
    
    Returns:
        Handler de archivo configurado
    """
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "dashboard.log"
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Agregar handler al logger raíz
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)
    
    return file_handler


def render_performance_metrics(show_details: bool = False):
    """
    Renderiza métricas de rendimiento en el sidebar o en una sección dedicada.
    
    Args:
        show_details: Si True, muestra detalles adicionales de rendimiento
    """
    if not show_details:
        return
    
    with st.expander("📊 Métricas de Rendimiento", expanded=False):
        st.caption("Monitoreo en tiempo real del dashboard")
        
        # Métricas básicas
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cache Hits", "N/A", help="Hits del cache de Streamlit")
            st.metric("DB Connections", "N/A", help="Conexiones activas a la BD")
        
        with col2:
            st.metric("Avg Load Time", "N/A", help="Tiempo promedio de carga")
            st.metric("Last Update", "N/A", help="Última actualización")
        
        # Logs recientes (últimas 10 líneas)
        st.subheader("Logs Recientes")
        log_file = PROJECT_ROOT / "data" / "logs" / "dashboard.log"
        
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    
                    for line in recent_lines:
                        st.code(line.strip(), language=None)
            except Exception as e:
                st.error(f"Error leyendo logs: {e}")
        else:
            st.info("No hay logs disponibles aún")


def log_cache_info(func_name: str, cache_hit: bool, elapsed_ms: float):
    """
    Loggea información sobre uso de cache.
    
    Args:
        func_name: Nombre de la función
        cache_hit: Si fue un cache hit
        elapsed_ms: Tiempo transcurrido en ms
    """
    logger = logging.getLogger(__name__)
    cache_status = "HIT" if cache_hit else "MISS"
    logger.debug(f"CACHE | {func_name} | {cache_status} | {elapsed_ms:.1f}ms")


@st.cache_data(ttl=60)  # Cache corto para métricas de rendimiento
def get_performance_summary() -> dict:
    """
    Obtiene resumen de métricas de rendimiento.
    
    Returns:
        Diccionario con métricas clave
    """
    log_file = PROJECT_ROOT / "data" / "logs" / "dashboard.log"
    
    if not log_file.exists():
        return {
            "total_logs": 0,
            "errors": 0,
            "warnings": 0,
            "avg_query_time": 0.0
        }
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_logs = len(lines)
        errors = sum(1 for line in lines if "ERROR" in line)
        warnings = sum(1 for line in lines if "WARNING" in line)
        
        # Extraer tiempos de queries
        query_times = []
        for line in lines:
            if "PERF |" in line or "QUERY_END |" in line:
                # Buscar patrón de tiempo (ej: "52.0ms" o "52.0 ms")
                import re
                match = re.search(r'(\d+\.?\d*)\s*ms', line)
                if match:
                    query_times.append(float(match.group(1)))
        
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0.0
        
        return {
            "total_logs": total_logs,
            "errors": errors,
            "warnings": warnings,
            "avg_query_time": avg_query_time,
            "last_log_time": lines[-1].split(" | ")[0] if lines else "N/A"
        }
    except Exception as e:
        logging.getLogger(__name__).error(f"Error reading performance summary: {e}")
        return {
            "total_logs": 0,
            "errors": 0,
            "warnings": 0,
            "avg_query_time": 0.0
        }
