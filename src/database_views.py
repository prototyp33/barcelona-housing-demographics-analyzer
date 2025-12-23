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
        - v_barrio_scorecard
        - v_tendencias_consolidadas
        - v_affordability_detallado
        - v_riesgo_gentrificacion
        - v_correlaciones_cruzadas

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
        # Scorecard completo por barrio (optimizado - solo datos más recientes)
        """
        DROP VIEW IF EXISTS v_barrio_scorecard;
        CREATE VIEW v_barrio_scorecard AS
        WITH 
        -- Subconsultas optimizadas para obtener solo el último año de cada tabla
        precios_ultimo AS (
            SELECT barrio_id, 
                   MAX(anio) as max_anio,
                   AVG(precio_m2_venta) AS precio_m2_venta,
                   AVG(precio_mes_alquiler) AS precio_mes_alquiler
            FROM fact_precios 
            WHERE anio = (SELECT MAX(anio) FROM fact_precios)
            GROUP BY barrio_id
        ),
        demo_ultimo AS (
            SELECT barrio_id,
                   AVG(poblacion_total) AS poblacion_total,
                   AVG(edad_media) AS edad_media,
                   AVG(densidad_hab_km2) AS densidad_hab_km2,
                   AVG(porc_inmigracion) AS porc_inmigracion
            FROM fact_demografia 
            WHERE anio = (SELECT MAX(anio) FROM fact_demografia)
            GROUP BY barrio_id
        ),
        renta_ultimo AS (
            SELECT barrio_id, AVG(renta_mediana) AS renta_mediana
            FROM fact_renta 
            WHERE anio = (SELECT MAX(anio) FROM fact_renta)
            GROUP BY barrio_id
        ),
        regulacion_ultimo AS (
            SELECT barrio_id,
                   MAX(zona_tensionada) AS zona_tensionada,
                   MAX(nivel_tension) AS nivel_tension,
                   AVG(indice_referencia_alquiler) AS indice_referencia_alquiler,
                   AVG(num_licencias_vut) AS num_licencias_vut
            FROM fact_regulacion 
            WHERE anio = (SELECT MAX(anio) FROM fact_regulacion)
            GROUP BY barrio_id
        ),
        turismo_ultimo AS (
            SELECT barrio_id,
                   AVG(num_listings_airbnb) AS num_listings_airbnb,
                   AVG(pct_entire_home) AS pct_entire_home,
                   AVG(tasa_ocupacion) AS tasa_ocupacion
            FROM fact_presion_turistica 
            WHERE anio = (SELECT MAX(anio) FROM fact_presion_turistica)
            GROUP BY barrio_id
        ),
        seguridad_ultimo AS (
            SELECT barrio_id,
                   AVG(tasa_criminalidad_1000hab) AS tasa_criminalidad_1000hab,
                   AVG(delitos_patrimonio) AS delitos_patrimonio,
                   AVG(delitos_seguridad_personal) AS delitos_seguridad_personal
            FROM fact_seguridad 
            WHERE anio = (SELECT MAX(anio) FROM fact_seguridad)
            GROUP BY barrio_id
        ),
        ruido_ultimo AS (
            SELECT barrio_id,
                   AVG(nivel_lden_medio) AS nivel_lden_medio,
                   AVG(pct_poblacion_expuesta_65db) AS pct_poblacion_expuesta_65db
            FROM fact_ruido
            GROUP BY barrio_id
        )
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            db.distrito_nombre,
            COALESCE(p.max_anio, 2024) AS ultimo_anio_datos,
            p.precio_m2_venta AS precio_m2_venta_promedio,
            p.precio_mes_alquiler AS precio_mes_alquiler_promedio,
            d.poblacion_total AS poblacion_total_promedio,
            d.edad_media AS edad_media_promedio,
            d.densidad_hab_km2 AS densidad_hab_km2_promedio,
            d.porc_inmigracion AS porc_inmigracion_promedio,
            r.renta_mediana AS renta_mediana_promedio,
            reg.zona_tensionada,
            reg.nivel_tension,
            reg.indice_referencia_alquiler AS indice_referencia_alquiler_promedio,
            reg.num_licencias_vut AS num_licencias_vut_promedio,
            t.num_listings_airbnb AS num_listings_airbnb_promedio,
            t.pct_entire_home AS pct_entire_home_promedio,
            t.tasa_ocupacion AS tasa_ocupacion_promedio,
            s.tasa_criminalidad_1000hab AS tasa_criminalidad_1000hab_promedio,
            s.delitos_patrimonio AS delitos_patrimonio_promedio,
            s.delitos_seguridad_personal AS delitos_seguridad_personal_promedio,
            ru.nivel_lden_medio AS nivel_lden_medio_promedio,
            ru.pct_poblacion_expuesta_65db AS pct_poblacion_expuesta_65db_promedio
        FROM dim_barrios db
        LEFT JOIN precios_ultimo p ON db.barrio_id = p.barrio_id
        LEFT JOIN demo_ultimo d ON db.barrio_id = d.barrio_id
        LEFT JOIN renta_ultimo r ON db.barrio_id = r.barrio_id
        LEFT JOIN regulacion_ultimo reg ON db.barrio_id = reg.barrio_id
        LEFT JOIN turismo_ultimo t ON db.barrio_id = t.barrio_id
        LEFT JOIN seguridad_ultimo s ON db.barrio_id = s.barrio_id
        LEFT JOIN ruido_ultimo ru ON db.barrio_id = ru.barrio_id;
        """,
        # Tendencias consolidadas (evolución temporal de todas las métricas)
        """
        DROP VIEW IF EXISTS v_tendencias_consolidadas;
        CREATE VIEW v_tendencias_consolidadas AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            p.anio AS anio,
            -- Precios
            AVG(p.precio_m2_venta) AS precio_m2_venta,
            AVG(p.precio_mes_alquiler) AS precio_mes_alquiler,
            -- Demografía
            AVG(d.poblacion_total) AS poblacion_total,
            AVG(d.edad_media) AS edad_media,
            AVG(d.densidad_hab_km2) AS densidad_hab_km2,
            -- Renta
            AVG(r.renta_mediana) AS renta_mediana,
            -- Regulación
            MAX(reg.zona_tensionada) AS zona_tensionada,
            MAX(reg.nivel_tension) AS nivel_tension,
            AVG(reg.indice_referencia_alquiler) AS indice_referencia_alquiler,
            -- Presión turística (agregado anual)
            AVG(pt.num_listings_airbnb) AS num_listings_airbnb_anual,
            AVG(pt.pct_entire_home) AS pct_entire_home_anual,
            AVG(pt.tasa_ocupacion) AS tasa_ocupacion_anual,
            -- Seguridad (agregado anual)
            AVG(s.tasa_criminalidad_1000hab) AS tasa_criminalidad_1000hab_anual,
            AVG(s.delitos_patrimonio) AS delitos_patrimonio_anual,
            -- Ruido
            AVG(ru.nivel_lden_medio) AS nivel_lden_medio,
            AVG(ru.pct_poblacion_expuesta_65db) AS pct_poblacion_expuesta_65db
        FROM dim_barrios db
        INNER JOIN fact_precios p ON db.barrio_id = p.barrio_id
        LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id AND p.anio = d.anio
        LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id AND p.anio = r.anio
        LEFT JOIN fact_regulacion reg ON db.barrio_id = reg.barrio_id AND p.anio = reg.anio
        LEFT JOIN fact_presion_turistica pt ON db.barrio_id = pt.barrio_id AND p.anio = pt.anio
        LEFT JOIN fact_seguridad s ON db.barrio_id = s.barrio_id AND p.anio = s.anio
        LEFT JOIN fact_ruido ru ON db.barrio_id = ru.barrio_id AND p.anio = ru.anio
        WHERE p.anio IS NOT NULL
        GROUP BY db.barrio_id, db.barrio_nombre, p.anio
        ORDER BY db.barrio_id, p.anio;
        """,
        # Affordability detallado con factores de regulación y presión turística
        """
        DROP VIEW IF EXISTS v_affordability_detallado;
        CREATE VIEW v_affordability_detallado AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            p.anio,
            -- Precios y renta
            AVG(p.precio_m2_venta) AS precio_m2_venta,
            AVG(p.precio_mes_alquiler) AS precio_mes_alquiler,
            AVG(r.renta_mediana) AS renta_mediana,
            -- Cálculo de affordability básico
            CASE 
                WHEN AVG(r.renta_mediana) > 0 
                THEN (AVG(p.precio_m2_venta) * 70) / (AVG(r.renta_mediana) / 12)
                ELSE NULL
            END AS price_to_income_ratio,
            CASE 
                WHEN AVG(r.renta_mediana) > 0 
                THEN (AVG(p.precio_mes_alquiler) * 12) / AVG(r.renta_mediana) * 100
                ELSE NULL
            END AS rent_burden_pct,
            -- Factores de regulación
            MAX(reg.zona_tensionada) AS zona_tensionada,
            MAX(reg.nivel_tension) AS nivel_tension,
            AVG(reg.indice_referencia_alquiler) AS indice_referencia_alquiler,
            AVG(reg.num_licencias_vut) AS num_licencias_vut,
            -- Presión turística
            AVG(pt.num_listings_airbnb) AS num_listings_airbnb,
            AVG(pt.pct_entire_home) AS pct_entire_home,
            -- Clasificación de affordability
            CASE 
                WHEN (AVG(p.precio_m2_venta) * 70) / (AVG(r.renta_mediana) / 12) < 3 THEN 'Muy Baja'
                WHEN (AVG(p.precio_m2_venta) * 70) / (AVG(r.renta_mediana) / 12) < 5 THEN 'Baja'
                WHEN (AVG(p.precio_m2_venta) * 70) / (AVG(r.renta_mediana) / 12) < 7 THEN 'Media'
                WHEN (AVG(p.precio_m2_venta) * 70) / (AVG(r.renta_mediana) / 12) < 9 THEN 'Alta'
                ELSE 'Muy Alta'
            END AS categoria_affordability
        FROM dim_barrios db
        INNER JOIN fact_precios p ON db.barrio_id = p.barrio_id
        LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id AND p.anio = r.anio
        LEFT JOIN fact_regulacion reg ON db.barrio_id = reg.barrio_id AND p.anio = reg.anio
        LEFT JOIN fact_presion_turistica pt ON db.barrio_id = pt.barrio_id AND p.anio = pt.anio
        WHERE p.precio_m2_venta IS NOT NULL
        GROUP BY db.barrio_id, db.barrio_nombre, p.anio
        ORDER BY db.barrio_id, p.anio;
        """,
        # Indicadores de riesgo de gentrificación
        """
        DROP VIEW IF EXISTS v_riesgo_gentrificacion;
        CREATE VIEW v_riesgo_gentrificacion AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            -- Cambios de precio (últimos 5 años)
            p_actual.precio_m2_venta AS precio_actual,
            p_anterior.precio_m2_venta AS precio_5_anios_atras,
            CASE 
                WHEN p_anterior.precio_m2_venta > 0 
                THEN ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / p_anterior.precio_m2_venta * 100.0)
                ELSE NULL
            END AS pct_cambio_precio_5_anios,
            -- Cambios demográficos
            d_actual.poblacion_total AS poblacion_actual,
            d_anterior.poblacion_total AS poblacion_5_anios_atras,
            CASE 
                WHEN d_anterior.poblacion_total > 0 
                THEN ((d_actual.poblacion_total - d_anterior.poblacion_total) / d_anterior.poblacion_total * 100.0)
                ELSE NULL
            END AS pct_cambio_poblacion_5_anios,
            d_actual.edad_media AS edad_media_actual,
            d_anterior.edad_media AS edad_media_5_anios_atras,
            -- Cambios en renta
            r_actual.renta_mediana AS renta_actual,
            r_anterior.renta_mediana AS renta_5_anios_atras,
            CASE 
                WHEN r_anterior.renta_mediana > 0 
                THEN ((r_actual.renta_mediana - r_anterior.renta_mediana) / r_anterior.renta_mediana * 100.0)
                ELSE NULL
            END AS pct_cambio_renta_5_anios,
            -- Presión turística actual
            pt_actual.num_listings_airbnb AS num_listings_airbnb_actual,
            -- Seguridad actual
            s_actual.tasa_criminalidad_1000hab AS tasa_criminalidad_actual,
            -- Score de riesgo (0-100, mayor = más riesgo)
            CASE 
                WHEN p_anterior.precio_m2_venta > 0 AND r_anterior.renta_mediana > 0 THEN
                    MIN(100, 
                        -- Aumento de precio > 30% = alto riesgo
                        CASE WHEN ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / p_anterior.precio_m2_venta * 100.0) > 30 THEN 30 ELSE 0 END +
                        -- Aumento de renta < aumento de precio = riesgo
                        CASE WHEN ((r_actual.renta_mediana - r_anterior.renta_mediana) / r_anterior.renta_mediana * 100.0) < 
                                  ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / p_anterior.precio_m2_venta * 100.0) * 0.5 THEN 25 ELSE 0 END +
                        -- Alta presión turística = riesgo
                        CASE WHEN pt_actual.num_listings_airbnb > 100 THEN 20 ELSE 0 END +
                        -- Disminución de población joven = riesgo
                        CASE WHEN d_actual.edad_media > d_anterior.edad_media + 2 THEN 15 ELSE 0 END +
                        -- Alta criminalidad = riesgo
                        CASE WHEN s_actual.tasa_criminalidad_1000hab > 50 THEN 10 ELSE 0 END
                    )
                ELSE NULL
            END AS score_riesgo_gentrificacion,
            -- Clasificación de riesgo (basada en suma de factores)
            CASE 
                WHEN (
                    CASE WHEN ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) > 30 THEN 30 ELSE 0 END +
                    CASE WHEN ((r_actual.renta_mediana - r_anterior.renta_mediana) / NULLIF(r_anterior.renta_mediana, 0) * 100.0) < 
                              ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) * 0.5 THEN 25 ELSE 0 END +
                    CASE WHEN COALESCE(pt_actual.num_listings_airbnb, 0) > 100 THEN 20 ELSE 0 END +
                    CASE WHEN d_actual.edad_media > COALESCE(d_anterior.edad_media, 0) + 2 THEN 15 ELSE 0 END +
                    CASE WHEN COALESCE(s_actual.tasa_criminalidad_1000hab, 0) > 50 THEN 10 ELSE 0 END
                ) >= 70 THEN 'Alto'
                WHEN (
                    CASE WHEN ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) > 30 THEN 30 ELSE 0 END +
                    CASE WHEN ((r_actual.renta_mediana - r_anterior.renta_mediana) / NULLIF(r_anterior.renta_mediana, 0) * 100.0) < 
                              ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) * 0.5 THEN 25 ELSE 0 END +
                    CASE WHEN COALESCE(pt_actual.num_listings_airbnb, 0) > 100 THEN 20 ELSE 0 END +
                    CASE WHEN d_actual.edad_media > COALESCE(d_anterior.edad_media, 0) + 2 THEN 15 ELSE 0 END +
                    CASE WHEN COALESCE(s_actual.tasa_criminalidad_1000hab, 0) > 50 THEN 10 ELSE 0 END
                ) >= 40 THEN 'Medio'
                WHEN (
                    CASE WHEN ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) > 30 THEN 30 ELSE 0 END +
                    CASE WHEN ((r_actual.renta_mediana - r_anterior.renta_mediana) / NULLIF(r_anterior.renta_mediana, 0) * 100.0) < 
                              ((p_actual.precio_m2_venta - p_anterior.precio_m2_venta) / NULLIF(p_anterior.precio_m2_venta, 0) * 100.0) * 0.5 THEN 25 ELSE 0 END +
                    CASE WHEN COALESCE(pt_actual.num_listings_airbnb, 0) > 100 THEN 20 ELSE 0 END +
                    CASE WHEN d_actual.edad_media > COALESCE(d_anterior.edad_media, 0) + 2 THEN 15 ELSE 0 END +
                    CASE WHEN COALESCE(s_actual.tasa_criminalidad_1000hab, 0) > 50 THEN 10 ELSE 0 END
                ) >= 20 THEN 'Bajo'
                ELSE 'Muy Bajo'
            END AS categoria_riesgo
        FROM dim_barrios db
        LEFT JOIN fact_precios p_actual ON db.barrio_id = p_actual.barrio_id 
            AND p_actual.anio = (SELECT MAX(anio) FROM fact_precios WHERE barrio_id = db.barrio_id)
        LEFT JOIN fact_precios p_anterior ON db.barrio_id = p_anterior.barrio_id 
            AND p_anterior.anio = (SELECT MAX(anio) FROM fact_precios WHERE barrio_id = db.barrio_id AND anio <= (SELECT MAX(anio) - 5 FROM fact_precios WHERE barrio_id = db.barrio_id))
        LEFT JOIN fact_demografia d_actual ON db.barrio_id = d_actual.barrio_id 
            AND d_actual.anio = (SELECT MAX(anio) FROM fact_demografia WHERE barrio_id = db.barrio_id)
        LEFT JOIN fact_demografia d_anterior ON db.barrio_id = d_anterior.barrio_id 
            AND d_anterior.anio = (SELECT MAX(anio) FROM fact_demografia WHERE barrio_id = db.barrio_id AND anio <= (SELECT MAX(anio) - 5 FROM fact_demografia WHERE barrio_id = db.barrio_id))
        LEFT JOIN fact_renta r_actual ON db.barrio_id = r_actual.barrio_id 
            AND r_actual.anio = (SELECT MAX(anio) FROM fact_renta WHERE barrio_id = db.barrio_id)
        LEFT JOIN fact_renta r_anterior ON db.barrio_id = r_anterior.barrio_id 
            AND r_anterior.anio = (SELECT MAX(anio) FROM fact_renta WHERE barrio_id = db.barrio_id AND anio <= (SELECT MAX(anio) - 5 FROM fact_renta WHERE barrio_id = db.barrio_id))
        LEFT JOIN fact_presion_turistica pt_actual ON db.barrio_id = pt_actual.barrio_id 
            AND pt_actual.anio = (SELECT MAX(anio) FROM fact_presion_turistica WHERE barrio_id = db.barrio_id)
        LEFT JOIN fact_seguridad s_actual ON db.barrio_id = s_actual.barrio_id 
            AND s_actual.anio = (SELECT MAX(anio) FROM fact_seguridad WHERE barrio_id = db.barrio_id)
        WHERE p_actual.precio_m2_venta IS NOT NULL;
        """,
        # Correlaciones cruzadas (preparado para análisis estadístico)
        """
        DROP VIEW IF EXISTS v_correlaciones_cruzadas;
        CREATE VIEW v_correlaciones_cruzadas AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            p.anio,
            -- Variables económicas
            AVG(p.precio_m2_venta) AS precio_m2_venta,
            AVG(p.precio_mes_alquiler) AS precio_mes_alquiler,
            AVG(r.renta_mediana) AS renta_mediana,
            -- Variables demográficas
            AVG(d.poblacion_total) AS poblacion_total,
            AVG(d.edad_media) AS edad_media,
            AVG(d.densidad_hab_km2) AS densidad_hab_km2,
            AVG(d.porc_inmigracion) AS porc_inmigracion,
            -- Variables de regulación
            AVG(reg.indice_referencia_alquiler) AS indice_referencia_alquiler,
            AVG(reg.num_licencias_vut) AS num_licencias_vut,
            -- Variables de presión turística
            AVG(pt.num_listings_airbnb) AS num_listings_airbnb,
            AVG(pt.pct_entire_home) AS pct_entire_home,
            AVG(pt.tasa_ocupacion) AS tasa_ocupacion,
            -- Variables de seguridad
            AVG(s.tasa_criminalidad_1000hab) AS tasa_criminalidad_1000hab,
            AVG(s.delitos_patrimonio) AS delitos_patrimonio,
            -- Variables de ruido
            AVG(ru.nivel_lden_medio) AS nivel_lden_medio,
            AVG(ru.pct_poblacion_expuesta_65db) AS pct_poblacion_expuesta_65db
        FROM dim_barrios db
        INNER JOIN fact_precios p ON db.barrio_id = p.barrio_id
        LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id AND p.anio = d.anio
        LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id AND p.anio = r.anio
        LEFT JOIN fact_regulacion reg ON db.barrio_id = reg.barrio_id AND p.anio = reg.anio
        LEFT JOIN fact_presion_turistica pt ON db.barrio_id = pt.barrio_id AND p.anio = pt.anio
        LEFT JOIN fact_seguridad s ON db.barrio_id = s.barrio_id AND p.anio = s.anio
        LEFT JOIN fact_ruido ru ON db.barrio_id = ru.barrio_id AND p.anio = ru.anio
        WHERE p.precio_m2_venta IS NOT NULL
        GROUP BY db.barrio_id, db.barrio_nombre, p.anio
        ORDER BY db.barrio_id, p.anio;
        """,
    ]

    with conn:
        for script in scripts:
            conn.executescript(script)

    logger.info("Vistas analíticas creadas/actualizadas correctamente")


__all__ = ["create_analytical_views"]


