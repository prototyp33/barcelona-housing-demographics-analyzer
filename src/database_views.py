"""Definición de vistas analíticas sobre el data warehouse SQLite."""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)


def create_analytical_views(conn: sqlite3.Connection) -> None:
    """
    Crea o recrea las vistas analíticas principales de forma idempotente.

    Vistas creadas:
        - v_affordability_quarterly
        - v_precios_evolucion_anual
        - v_demografia_resumen
        - v_gentrificacion_tendencias

    Args:
        conn: Conexión SQLite activa.
    """
    logger.info("Creando vistas analíticas si no existen")

    scripts = [
        # Vista de affordability trimestral basada en fact_housing_master
        """
        DROP VIEW IF EXISTS v_affordability_quarterly;
        CREATE VIEW v_affordability_quarterly AS
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
            END AS categoria_affordability
        FROM fact_housing_master fhm
        JOIN dim_barrios db ON fhm.barrio_id = db.barrio_id
        WHERE fhm.renta_annual IS NOT NULL
          AND fhm.preu_venda_m2 IS NOT NULL;
        """,
        # Evolución anual de precios por barrio
        """
        DROP VIEW IF EXISTS v_precios_evolucion_anual;
        CREATE VIEW v_precios_evolucion_anual AS
        SELECT 
            barrio_id,
            anio,
            AVG(precio_m2_venta) AS precio_m2_venta_promedio,
            AVG(precio_mes_alquiler) AS precio_mes_alquiler_promedio,
            COUNT(*) AS num_registros
        FROM fact_precios
        WHERE precio_m2_venta IS NOT NULL 
           OR precio_mes_alquiler IS NOT NULL
        GROUP BY barrio_id, anio
        ORDER BY barrio_id, anio;
        """,
        # Resumen demográfico por barrio y año
        """
        DROP VIEW IF EXISTS v_demografia_resumen;
        CREATE VIEW v_demografia_resumen AS
        SELECT 
            d.barrio_id,
            db.barrio_nombre,
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
        # Tendencias de gentrificación (2015 vs 2024)
        """
        DROP VIEW IF EXISTS v_gentrificacion_tendencias;
        CREATE VIEW v_gentrificacion_tendencias AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            p15.precio_m2_venta AS precio_2015,
            p24.precio_m2_venta AS precio_2024,
            ((p24.precio_m2_venta - p15.precio_m2_venta) / p15.precio_m2_venta * 100.0)
                AS pct_cambio_precio,
            r15.renta_mediana AS renta_2015,
            r24.renta_mediana AS renta_2024,
            ((r24.renta_mediana - r15.renta_mediana) / r15.renta_mediana * 100.0)
                AS pct_cambio_renta,
            d15.poblacion_total AS poblacion_2015,
            d24.poblacion_total AS poblacion_2024
        FROM dim_barrios db
        LEFT JOIN fact_precios p15 
               ON db.barrio_id = p15.barrio_id AND p15.anio = 2015
        LEFT JOIN fact_precios p24 
               ON db.barrio_id = p24.barrio_id AND p24.anio = 2024
        LEFT JOIN fact_renta r15 
               ON db.barrio_id = r15.barrio_id AND r15.anio = 2015
        LEFT JOIN fact_renta r24 
               ON db.barrio_id = r24.barrio_id AND r24.anio = 2024
        LEFT JOIN fact_demografia d15 
               ON db.barrio_id = d15.barrio_id AND d15.anio = 2015
        LEFT JOIN fact_demografia d24 
               ON db.barrio_id = d24.barrio_id AND d24.anio = 2024
        WHERE p15.precio_m2_venta IS NOT NULL 
          AND p24.precio_m2_venta IS NOT NULL;
        """,
    ]

    with conn:
        for script in scripts:
            conn.executescript(script)

    logger.info("Vistas analíticas creadas/actualizadas correctamente")


__all__ = ["create_analytical_views"]


