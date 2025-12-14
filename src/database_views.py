"""
Vistas analíticas para la base de datos.

Proporciona vistas SQL predefinidas para análisis comunes.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Definiciones de vistas
VIEW_DEFINITIONS = {
    "v_affordability_quarterly": """
    CREATE VIEW IF NOT EXISTS v_affordability_quarterly AS
    SELECT 
        fhm.barrio_id,
        db.barrio_nombre,
        fhm.year,
        fhm.quarter,
        fhm.preu_venda_m2,
        fhm.renta_annual,
        fhm.price_to_income_ratio,
        fhm.rent_burden_pct,
        fhm.affordability_index,
        CASE 
            WHEN fhm.affordability_index < 3 THEN 'Muy Baja'
            WHEN fhm.affordability_index < 5 THEN 'Baja'
            WHEN fhm.affordability_index < 7 THEN 'Media'
            WHEN fhm.affordability_index < 9 THEN 'Alta'
            ELSE 'Muy Alta'
        END as categoria_affordability
    FROM fact_housing_master fhm
    JOIN dim_barrios db ON fhm.barrio_id = db.barrio_id
    WHERE fhm.renta_annual IS NOT NULL
      AND fhm.preu_venda_m2 IS NOT NULL;
    """,
    
    "v_precios_evolucion_anual": """
    CREATE VIEW IF NOT EXISTS v_precios_evolucion_anual AS
    SELECT 
        fp.barrio_id,
        db.barrio_nombre,
        fp.anio,
        AVG(fp.precio_m2_venta) as precio_m2_venta_promedio,
        AVG(fp.precio_mes_alquiler) as precio_mes_alquiler_promedio,
        COUNT(*) as num_registros
    FROM fact_precios fp
    JOIN dim_barrios db ON fp.barrio_id = db.barrio_id
    WHERE fp.precio_m2_venta IS NOT NULL OR fp.precio_mes_alquiler IS NOT NULL
    GROUP BY fp.barrio_id, fp.anio
    ORDER BY fp.barrio_id, fp.anio;
    """,
    
    "v_demografia_resumen": """
    CREATE VIEW IF NOT EXISTS v_demografia_resumen AS
    SELECT 
        d.barrio_id,
        db.barrio_nombre,
        db.distrito_nombre,
        d.anio,
        d.poblacion_total,
        d.poblacion_hombres,
        d.poblacion_mujeres,
        d.hogares_totales,
        d.edad_media,
        d.porc_inmigracion,
        d.densidad_hab_km2,
        d.pct_mayores_65,
        d.pct_menores_15,
        d.indice_envejecimiento
    FROM fact_demografia d
    JOIN dim_barrios db ON d.barrio_id = db.barrio_id
    ORDER BY d.barrio_id, d.anio;
    """,
    
    "v_gentrificacion_tendencias": """
    CREATE VIEW IF NOT EXISTS v_gentrificacion_tendencias AS
    SELECT 
        db.barrio_id,
        db.barrio_nombre,
        p15.precio_m2_venta as precio_2015,
        p24.precio_m2_venta as precio_2024,
        CASE 
            WHEN p15.precio_m2_venta > 0 
            THEN ((p24.precio_m2_venta - p15.precio_m2_venta) / p15.precio_m2_venta * 100)
            ELSE NULL
        END as pct_cambio_precio,
        r15.renta_mediana as renta_2015,
        r24.renta_mediana as renta_2024,
        CASE 
            WHEN r15.renta_mediana > 0 
            THEN ((r24.renta_mediana - r15.renta_mediana) / r15.renta_mediana * 100)
            ELSE NULL
        END as pct_cambio_renta,
        d15.poblacion_total as poblacion_2015,
        d24.poblacion_total as poblacion_2024
    FROM dim_barrios db
    LEFT JOIN fact_precios p15 ON db.barrio_id = p15.barrio_id AND p15.anio = 2015
    LEFT JOIN fact_precios p24 ON db.barrio_id = p24.barrio_id AND p24.anio = 2024
    LEFT JOIN fact_renta r15 ON db.barrio_id = r15.barrio_id AND r15.anio = 2015
    LEFT JOIN fact_renta r24 ON db.barrio_id = r24.barrio_id AND r24.anio = 2024
    LEFT JOIN fact_demografia d15 ON db.barrio_id = d15.barrio_id AND d15.anio = 2015
    LEFT JOIN fact_demografia d24 ON db.barrio_id = d24.barrio_id AND d24.anio = 2024
    WHERE p15.precio_m2_venta IS NOT NULL 
      AND p24.precio_m2_venta IS NOT NULL;
    """,
}


def create_analytical_views(conn: sqlite3.Connection) -> dict[str, bool]:
    """
    Crea todas las vistas analíticas.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Diccionario con estado de creación de cada vista
    """
    results = {}
    
    for view_name, view_sql in VIEW_DEFINITIONS.items():
        try:
            conn.executescript(view_sql)
            results[view_name] = True
            logger.debug(f"Vista {view_name} creada exitosamente")
        except sqlite3.Error as e:
            logger.error(f"Error creando vista {view_name}: {e}")
            results[view_name] = False
    
    return results


def drop_analytical_views(conn: sqlite3.Connection) -> None:
    """Elimina todas las vistas analíticas."""
    for view_name in VIEW_DEFINITIONS.keys():
        try:
            conn.execute(f"DROP VIEW IF EXISTS {view_name}")
            logger.debug(f"Vista {view_name} eliminada")
        except sqlite3.Error as e:
            logger.warning(f"Error eliminando vista {view_name}: {e}")


def list_views(conn: sqlite3.Connection) -> list[str]:
    """Lista todas las vistas existentes."""
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='view' AND name LIKE 'v_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]

