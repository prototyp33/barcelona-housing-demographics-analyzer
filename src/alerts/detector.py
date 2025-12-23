"""
Detector de cambios significativos en métricas clave.

Detecta:
- Cambios >10% en precios (trimestre a trimestre)
- Aumento >20% en presión turística
- Cambios en niveles de seguridad
- Nuevas regulaciones aplicadas
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import sqlite3

from ..database_setup import DEFAULT_DB_NAME
from .notifier import Alert, AlertPriority, create_alert

logger = logging.getLogger(__name__)


def _get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Obtiene conexión a la base de datos.
    
    Args:
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Conexión SQLite.
    """
    if db_path is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data" / "processed" / DEFAULT_DB_NAME
    
    return sqlite3.connect(str(db_path))


def detect_changes(
    barrio_id: int,
    metric: str,
    threshold: float = 10.0,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta cambios significativos en una métrica para un barrio.
    
    Args:
        barrio_id: ID del barrio.
        metric: Nombre de la métrica a monitorear.
        threshold: Umbral de cambio porcentual para considerar significativo.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de alertas detectadas.
    """
    from ...analysis.descriptive import calculate_trends
    
    alerts = []
    
    try:
        # Obtener tendencias
        from ...analysis.descriptive import calculate_trends
        
        trend = calculate_trends(barrio_id, metric, db_path=db_path)
        
        if not trend["values"] or len(trend["values"]) < 2:
            return alerts
        
        # Detectar cambios significativos
        for change in trend.get("significant_changes", []):
            change_pct = change["change_pct"]
            
            if abs(change_pct) > threshold:
                # Determinar prioridad
                if abs(change_pct) > 30:
                    priority = AlertPriority.CRITICAL
                elif abs(change_pct) > 20:
                    priority = AlertPriority.HIGH
                elif abs(change_pct) > threshold:
                    priority = AlertPriority.MEDIUM
                else:
                    priority = AlertPriority.LOW
                
                # Determinar dirección
                direction = "aumento" if change_pct > 0 else "disminución"
                
                alert = create_alert(
                    alert_type=f"cambio_{metric}",
                    barrio_id=barrio_id,
                    priority=priority,
                    title=f"Cambio significativo en {metric.replace('_', ' ').title()}",
                    message=(
                        f"{direction.capitalize()} del {abs(change_pct):.1f}% "
                        f"en {metric.replace('_', ' ').title()} "
                        f"({change['previous_year']} → {change['year']})"
                    ),
                    details={
                        "metric": metric,
                        "change_pct": change_pct,
                        "previous_value": change["previous_value"],
                        "new_value": change["new_value"],
                        "previous_year": change["previous_year"],
                        "year": change["year"],
                    },
                )
                
                alerts.append(alert)
        
        # Detectar puntos de inflexión
        for inflection_year in trend.get("inflection_points", []):
            alert = create_alert(
                alert_type=f"inflexion_{metric}",
                barrio_id=barrio_id,
                priority=AlertPriority.MEDIUM,
                title=f"Punto de inflexión en {metric.replace('_', ' ').title()}",
                message=(
                    f"Cambio de tendencia detectado en {metric.replace('_', ' ').title()} "
                    f"en el año {inflection_year}"
                ),
                details={
                    "metric": metric,
                    "inflection_year": inflection_year,
                },
            )
            
            alerts.append(alert)
    
    except Exception as e:
        logger.error("Error detectando cambios para barrio_id=%s, metric=%s: %s", barrio_id, metric, e)
    
    return alerts


def detect_price_changes(
    barrio_id: int,
    threshold: float = 10.0,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta cambios significativos en precios.
    
    Args:
        barrio_id: ID del barrio.
        threshold: Umbral de cambio porcentual (default: 10%).
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de alertas de precios.
    """
    return detect_changes(barrio_id, "precio_m2_venta", threshold, db_path)


def detect_tourism_pressure_changes(
    barrio_id: int,
    threshold: float = 20.0,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta cambios significativos en presión turística.
    
    Args:
        barrio_id: ID del barrio.
        threshold: Umbral de cambio porcentual (default: 20%).
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de alertas de presión turística.
    """
    conn = _get_db_connection(db_path)
    
    alerts = []
    
    try:
        # Obtener datos de presión turística
        query = """
            SELECT 
                barrio_id,
                anio,
                mes,
                num_listings_airbnb,
                pct_entire_home,
                tasa_ocupacion
            FROM fact_presion_turistica
            WHERE barrio_id = ?
            ORDER BY anio DESC, mes DESC
            LIMIT 12
        """
        
        df = pd.read_sql_query(query, conn, params=[barrio_id])
        
        if len(df) < 2:
            return alerts
        
        # Comparar último mes con mes anterior
        latest = df.iloc[0]
        previous = df.iloc[1] if len(df) > 1 else None
        
        if previous is not None and latest["num_listings_airbnb"] is not None and previous["num_listings_airbnb"] is not None:
            change_pct = ((latest["num_listings_airbnb"] - previous["num_listings_airbnb"]) / previous["num_listings_airbnb"]) * 100
            
            if abs(change_pct) > threshold:
                priority = AlertPriority.HIGH if abs(change_pct) > 30 else AlertPriority.MEDIUM
                direction = "aumento" if change_pct > 0 else "disminución"
                
                alert = create_alert(
                    alert_type="cambio_presion_turistica",
                    barrio_id=barrio_id,
                    priority=priority,
                    title="Cambio significativo en presión turística",
                    message=(
                        f"{direction.capitalize()} del {abs(change_pct):.1f}% "
                        f"en número de listings Airbnb "
                        f"({previous['num_listings_airbnb']:.0f} → {latest['num_listings_airbnb']:.0f})"
                    ),
                    details={
                        "metric": "num_listings_airbnb",
                        "change_pct": change_pct,
                        "previous_value": previous["num_listings_airbnb"],
                        "new_value": latest["num_listings_airbnb"],
                        "previous_period": f"{previous['anio']}-{previous['mes']:02d}",
                        "current_period": f"{latest['anio']}-{latest['mes']:02d}",
                    },
                )
                
                alerts.append(alert)
    
    finally:
        conn.close()
    
    return alerts


def detect_security_changes(
    barrio_id: int,
    threshold: float = 15.0,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta cambios significativos en seguridad.
    
    Args:
        barrio_id: ID del barrio.
        threshold: Umbral de cambio porcentual (default: 15%).
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de alertas de seguridad.
    """
    return detect_changes(barrio_id, "tasa_criminalidad_1000hab", threshold, db_path)


def detect_regulation_changes(
    barrio_id: int,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta cambios en regulación (nuevas zonas tensionadas, etc.).
    
    Args:
        barrio_id: ID del barrio.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de alertas de regulación.
    """
    conn = _get_db_connection(db_path)
    
    alerts = []
    
    try:
        # Obtener datos de regulación
        query = """
            SELECT 
                barrio_id,
                anio,
                zona_tensionada,
                nivel_tension,
                derecho_tanteo
            FROM fact_regulacion
            WHERE barrio_id = ?
            ORDER BY anio DESC
            LIMIT 2
        """
        
        df = pd.read_sql_query(query, conn, params=[barrio_id])
        
        if len(df) < 2:
            return alerts
        
        latest = df.iloc[0]
        previous = df.iloc[1]
        
        # Detectar activación de zona tensionada
        if latest["zona_tensionada"] and not previous["zona_tensionada"]:
            alert = create_alert(
                alert_type="nueva_zona_tensionada",
                barrio_id=barrio_id,
                priority=AlertPriority.HIGH,
                title="Nueva zona tensionada activada",
                message=(
                    f"El barrio ha sido declarado zona tensionada en {latest['anio']}. "
                    f"Se aplican nuevas regulaciones de alquiler."
                ),
                details={
                    "year": latest["anio"],
                    "nivel_tension": latest["nivel_tension"],
                    "derecho_tanteo": latest["derecho_tanteo"],
                },
            )
            alerts.append(alert)
        
        # Detectar cambio en nivel de tensión
        if latest["nivel_tension"] != previous["nivel_tension"]:
            alert = create_alert(
                alert_type="cambio_nivel_tension",
                barrio_id=barrio_id,
                priority=AlertPriority.MEDIUM,
                title="Cambio en nivel de tensión",
                message=(
                    f"Nivel de tensión cambió de '{previous['nivel_tension']}' "
                    f"a '{latest['nivel_tension']}' en {latest['anio']}"
                ),
                details={
                    "previous_level": previous["nivel_tension"],
                    "new_level": latest["nivel_tension"],
                    "year": latest["anio"],
                },
            )
            alerts.append(alert)
    
    finally:
        conn.close()
    
    return alerts


def detect_all_changes(
    barrio_id: int,
    db_path: Optional[Path] = None
) -> List[Alert]:
    """
    Detecta todos los tipos de cambios para un barrio.
    
    Args:
        barrio_id: ID del barrio.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de todas las alertas detectadas.
    """
    all_alerts = []
    
    # Detectar cambios en precios
    all_alerts.extend(detect_price_changes(barrio_id, threshold=10.0, db_path=db_path))
    
    # Detectar cambios en presión turística
    all_alerts.extend(detect_tourism_pressure_changes(barrio_id, threshold=20.0, db_path=db_path))
    
    # Detectar cambios en seguridad
    all_alerts.extend(detect_security_changes(barrio_id, threshold=15.0, db_path=db_path))
    
    # Detectar cambios en regulación
    all_alerts.extend(detect_regulation_changes(barrio_id, db_path=db_path))
    
    return all_alerts

