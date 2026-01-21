"""Definición de vistas analíticas sobre el data warehouse SQLite."""

from __future__ import annotations

import logging
import sqlite3

logger = logging.getLogger(__name__)


def create_analytical_views(conn: sqlite3.Connection) -> None:
    """
    Crea o recrea las vistas analíticas principales de forma idempotente.

    Vistas creadas:
        - v_demografia_aggregated (NEW: agregación de fact_demografia_ampliada)
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
        # Vista de agregación demográfica desde fact_demografia_ampliada
        # Esta vista proporciona las métricas estándar que normalmente estarían en fact_demografia
        """
        DROP VIEW IF EXISTS v_demografia_aggregated;
        CREATE VIEW v_demografia_aggregated AS
        SELECT 
            barrio_id,
            anio,
            SUM(poblacion) AS poblacion_total,
            SUM(CASE WHEN sexo = 'Home' OR sexo = 'Hombre' THEN poblacion ELSE 0 END) AS poblacion_hombres,
            SUM(CASE WHEN sexo = 'Dona' OR sexo = 'Mujer' THEN poblacion ELSE 0 END) AS poblacion_mujeres,
            -- Calcular edad media ponderada (aproximación basada en grupos de edad)
            CASE 
                WHEN SUM(poblacion) > 0 THEN
                    ROUND(
                        (SUM(CASE 
                            WHEN grupo_edad LIKE '%0-4%' OR grupo_edad LIKE '%0 a 4%' THEN poblacion * 2
                            WHEN grupo_edad LIKE '%5-9%' OR grupo_edad LIKE '%5 a 9%' THEN poblacion * 7
                            WHEN grupo_edad LIKE '%10-14%' OR grupo_edad LIKE '%10 a 14%' THEN poblacion * 12
                            WHEN grupo_edad LIKE '%15-19%' OR grupo_edad LIKE '%15 a 19%' THEN poblacion * 17
                            WHEN grupo_edad LIKE '%18-34%' OR grupo_edad LIKE '%18 a 34%' THEN poblacion * 26
                            WHEN grupo_edad LIKE '%20-24%' OR grupo_edad LIKE '%20 a 24%' THEN poblacion * 22
                            WHEN grupo_edad LIKE '%25-29%' OR grupo_edad LIKE '%25 a 29%' THEN poblacion * 27
                            WHEN grupo_edad LIKE '%30-34%' OR grupo_edad LIKE '%30 a 34%' THEN poblacion * 32
                            WHEN grupo_edad LIKE '%35-39%' OR grupo_edad LIKE '%35 a 39%' THEN poblacion * 37
                            WHEN grupo_edad LIKE '%35-64%' OR grupo_edad LIKE '%35 a 64%' THEN poblacion * 49.5
                            WHEN grupo_edad LIKE '%40-44%' OR grupo_edad LIKE '%40 a 44%' THEN poblacion * 42
                            WHEN grupo_edad LIKE '%45-49%' OR grupo_edad LIKE '%45 a 49%' THEN poblacion * 47
                            WHEN grupo_edad LIKE '%50-54%' OR grupo_edad LIKE '%50 a 54%' THEN poblacion * 52
                            WHEN grupo_edad LIKE '%55-59%' OR grupo_edad LIKE '%55 a 59%' THEN poblacion * 57
                            WHEN grupo_edad LIKE '%60-64%' OR grupo_edad LIKE '%60 a 64%' THEN poblacion * 62
                            WHEN grupo_edad LIKE '%65-69%' OR grupo_edad LIKE '%65 a 69%' THEN poblacion * 67
                            WHEN grupo_edad LIKE '%65%' OR grupo_edad LIKE '%65 i més%' THEN poblacion * 75
                            WHEN grupo_edad LIKE '%70-74%' OR grupo_edad LIKE '%70 a 74%' THEN poblacion * 72
                            WHEN grupo_edad LIKE '%75-79%' OR grupo_edad LIKE '%75 a 79%' THEN poblacion * 77
                            WHEN grupo_edad LIKE '%80-84%' OR grupo_edad LIKE '%80 a 84%' THEN poblacion * 82
                            WHEN grupo_edad LIKE '%85%' OR grupo_edad LIKE '%85 i més%' THEN poblacion * 87
                            ELSE poblacion * 40  -- Default para grupos no reconocidos
                        END)) / SUM(poblacion), 1
                    )
                ELSE NULL
            END AS edad_media,
            -- Porcentaje de inmigración (nacidos fuera de España)
            CASE 
                WHEN SUM(poblacion) > 0 THEN
                    ROUND(
                        100.0 * SUM(CASE 
                            WHEN nacionalidad NOT IN ('Espanya', 'España', 'Europa') 
                                OR nacionalidad IN ('Àfrica', 'África', 'Amèrica', 'América', 'Àsia', 'Asia', 'Oceania', 'Oceanía')
                            THEN poblacion 
                            ELSE 0 
                        END) / SUM(poblacion), 2
                    )
                ELSE NULL
            END AS porc_inmigracion,
            -- Porcentaje de mayores de 65
            CASE 
                WHEN SUM(poblacion) > 0 THEN
                    ROUND(
                        100.0 * SUM(CASE 
                            WHEN grupo_edad LIKE '%65%' OR grupo_edad LIKE '%70%' OR grupo_edad LIKE '%75%' 
                                OR grupo_edad LIKE '%80%' OR grupo_edad LIKE '%85%'
                            THEN poblacion 
                            ELSE 0 
                        END) / SUM(poblacion), 2
                    )
                ELSE NULL
            END AS pct_mayores_65,
            -- Porcentaje de menores de 15
            CASE 
                WHEN SUM(poblacion) > 0 THEN
                    ROUND(
                        100.0 * SUM(CASE 
                            WHEN grupo_edad LIKE '%0-4%' OR grupo_edad LIKE '%5-9%' OR grupo_edad LIKE '%10-14%'
                                OR grupo_edad LIKE '%0 a 4%' OR grupo_edad LIKE '%5 a 9%' OR grupo_edad LIKE '%10 a 14%'
                            THEN poblacion 
                            ELSE 0 
                        END) / SUM(poblacion), 2
                    )
                ELSE NULL
            END AS pct_menores_15,
            -- Índice de envejecimiento (mayores 65 / menores 15)
            CASE 
                WHEN SUM(CASE 
                    WHEN grupo_edad LIKE '%0-4%' OR grupo_edad LIKE '%5-9%' OR grupo_edad LIKE '%10-14%'
                        OR grupo_edad LIKE '%0 a 4%' OR grupo_edad LIKE '%5 a 9%' OR grupo_edad LIKE '%10 a 14%'
                    THEN poblacion 
                    ELSE 0 
                END) > 0 THEN
                    ROUND(
                        100.0 * SUM(CASE 
                            WHEN grupo_edad LIKE '%65%' OR grupo_edad LIKE '%70%' OR grupo_edad LIKE '%75%' 
                                OR grupo_edad LIKE '%80%' OR grupo_edad LIKE '%85%'
                            THEN poblacion 
                            ELSE 0 
                        END) / SUM(CASE 
                            WHEN grupo_edad LIKE '%0-4%' OR grupo_edad LIKE '%5-9%' OR grupo_edad LIKE '%10-14%'
                                OR grupo_edad LIKE '%0 a 4%' OR grupo_edad LIKE '%5 a 9%' OR grupo_edad LIKE '%10 a 14%'
                            THEN poblacion 
                            ELSE 0 
                        END), 2
                    )
                ELSE NULL
            END AS indice_envejecimiento,
            'fact_demografia_ampliada' AS source,
            MAX(etl_loaded_at) AS etl_loaded_at
        FROM fact_demografia_ampliada
        GROUP BY barrio_id, anio
        ORDER BY barrio_id, anio;
        """,
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
        # Vistas base para visualizaciones (alquiler mensual/anual y métricas housing)
        """
        DROP VIEW IF EXISTS v_alquiler_mensual;
        CREATE VIEW v_alquiler_mensual AS
        SELECT
            db.barrio_id,
            db.barrio_nombre,
            db.distrito_nombre,
            t.time_id,
            am.anio,
            am.mes,
            t.periodo AS year_month,
            AVG(am.precio_mes_alquiler) AS precio_mes_alquiler,
            COUNT(*) AS num_observaciones
        FROM fact_alquiler_mensual am
        INNER JOIN dim_barrios db ON db.barrio_id = am.barrio_id
        LEFT JOIN dim_tiempo t ON t.anio = am.anio AND t.mes = am.mes AND t.periodo = printf('%04d-%02d', am.anio, am.mes)
        WHERE am.precio_mes_alquiler IS NOT NULL
        GROUP BY db.barrio_id, db.barrio_nombre, db.distrito_nombre, t.time_id, am.anio, am.mes, t.periodo
        ORDER BY db.barrio_id, am.anio, am.mes;
        """,
        """
        DROP VIEW IF EXISTS v_alquiler_anual;
        CREATE VIEW v_alquiler_anual AS
        SELECT
            barrio_id,
            barrio_nombre,
            distrito_nombre,
            anio,
            AVG(precio_mes_alquiler) AS precio_mes_alquiler,
            COUNT(DISTINCT mes) AS meses_con_datos
        FROM v_alquiler_mensual
        GROUP BY barrio_id, barrio_nombre, distrito_nombre, anio
        ORDER BY barrio_id, anio;
        """,
        """
        DROP VIEW IF EXISTS v_precios_anual;
        CREATE VIEW v_precios_anual AS
        WITH venta AS (
            SELECT barrio_id, anio, AVG(precio_m2_venta) AS precio_m2_venta
            FROM fact_precios
            WHERE precio_m2_venta IS NOT NULL
            GROUP BY barrio_id, anio
        )
        SELECT
            db.barrio_id,
            db.barrio_nombre,
            db.distrito_nombre,
            y.anio,
            v.precio_m2_venta,
            a.precio_mes_alquiler,
            a.meses_con_datos AS alquiler_meses_con_datos
        FROM dim_barrios db
        INNER JOIN (
            SELECT barrio_id, anio FROM venta
            UNION
            SELECT barrio_id, anio FROM v_alquiler_anual
        ) y ON y.barrio_id = db.barrio_id
        LEFT JOIN venta v ON v.barrio_id = y.barrio_id AND v.anio = y.anio
        LEFT JOIN v_alquiler_anual a ON a.barrio_id = y.barrio_id AND a.anio = y.anio
        ORDER BY db.barrio_id, y.anio;
        """,
        """
        DROP VIEW IF EXISTS v_metricas_housing;
        CREATE VIEW v_metricas_housing AS
        SELECT
            p.barrio_id,
            p.barrio_nombre,
            p.distrito_nombre,
            p.anio,
            p.precio_m2_venta,
            p.precio_mes_alquiler,
            r.renta_euros,
            r.renta_mediana,
            -- Métricas (con fallback renta_euros si renta_mediana no está)
            CASE
                WHEN COALESCE(r.renta_mediana, r.renta_euros) > 0 AND p.precio_m2_venta IS NOT NULL
                THEN p.precio_m2_venta / (COALESCE(r.renta_mediana, r.renta_euros) / 12.0)
                ELSE NULL
            END AS ratio_precio_renta_mensual,
            CASE
                WHEN p.precio_mes_alquiler > 0 AND COALESCE(r.renta_mediana, r.renta_euros) > 0
                THEN (p.precio_mes_alquiler * 12.0) / COALESCE(r.renta_mediana, r.renta_euros) * 100.0
                ELSE NULL
            END AS pct_renta_destinada_alquiler,
            CASE
                WHEN COALESCE(r.renta_mediana, r.renta_euros) > 0 AND p.precio_mes_alquiler > 0
                THEN COALESCE(r.renta_mediana, r.renta_euros) / (p.precio_mes_alquiler * 12.0)
                ELSE NULL
            END AS affordability_index,
            d.poblacion_total,
            d.edad_media,
            d.pct_mayores_65
        FROM v_precios_anual p
        LEFT JOIN fact_renta r ON r.barrio_id = p.barrio_id AND r.anio = p.anio
        LEFT JOIN fact_demografia d ON d.barrio_id = p.barrio_id AND d.anio = p.anio
        ORDER BY p.barrio_id, p.anio;
        """,
        # Modelo estrella (BI): dims + facts con claves `*_id` y medidas (sin nombres repetidos)
        """
        DROP VIEW IF EXISTS v_dim_barrios_star;
        CREATE VIEW v_dim_barrios_star AS
        SELECT
            barrio_id,
            barrio_nombre,
            distrito_nombre,
            codi_districte,
            codi_barri,
            geometry_json
        FROM dim_barrios;
        """,
        """
        DROP VIEW IF EXISTS v_dim_tiempo_star;
        CREATE VIEW v_dim_tiempo_star AS
        SELECT
            time_id,
            periodo,
            anio,
            trimestre,
            mes,
            year_quarter,
            year_month,
            estacion,
            fecha_inicio,
            fecha_fin
        FROM dim_tiempo;
        """,
        """
        DROP VIEW IF EXISTS v_fact_housing_anual_star;
        CREATE VIEW v_fact_housing_anual_star AS
        SELECT
            mh.barrio_id,
            t.time_id,
            mh.anio,
            mh.precio_m2_venta,
            mh.precio_mes_alquiler,
            mh.renta_euros,
            mh.renta_mediana,
            mh.ratio_precio_renta_mensual,
            mh.pct_renta_destinada_alquiler,
            mh.affordability_index,
            mh.poblacion_total,
            mh.edad_media,
            mh.pct_mayores_65
        FROM v_metricas_housing mh
        INNER JOIN dim_tiempo t
            ON t.periodo = printf('%04d', mh.anio)
           AND t.mes IS NULL
           AND t.trimestre IS NULL;
        """,
        """
        DROP VIEW IF EXISTS v_fact_alquiler_mensual_star;
        CREATE VIEW v_fact_alquiler_mensual_star AS
        SELECT
            am.barrio_id,
            t.time_id,
            am.anio,
            am.mes,
            am.precio_mes_alquiler,
            am.dataset_id,
            am.source
        FROM fact_alquiler_mensual am
        INNER JOIN dim_tiempo t
            ON t.periodo = printf('%04d-%02d', am.anio, am.mes)
           AND t.mes = am.mes;
        """,
        # Vista consolidada de economía (nueva - para análisis de correlaciones económicas)
        """
        DROP VIEW IF EXISTS v_economia_consolidada;
        CREATE VIEW v_economia_consolidada AS
        WITH venta AS (
            SELECT barrio_id, anio, AVG(precio_m2_venta) AS precio_m2_venta
            FROM fact_precios
            WHERE precio_m2_venta IS NOT NULL
            GROUP BY barrio_id, anio
        ),
        alquiler AS (
            SELECT barrio_id, anio, AVG(precio_mes_alquiler) AS precio_mes_alquiler
            FROM fact_alquiler_mensual
            WHERE precio_mes_alquiler IS NOT NULL
            GROUP BY barrio_id, anio
        ),
        years AS (
            SELECT barrio_id, anio FROM venta
            UNION
            SELECT barrio_id, anio FROM alquiler
        )
        SELECT
            db.barrio_id,
            db.barrio_nombre,
            db.distrito_nombre,
            y.anio,
            -- Variables económicas básicas
            v.precio_m2_venta AS precio_m2_venta,
            a.precio_mes_alquiler AS precio_mes_alquiler,
            -- Renta básica
            AVG(r.renta_euros) AS renta_euros,
            AVG(r.renta_promedio) AS renta_promedio,
            AVG(r.renta_mediana) AS renta_mediana,
            -- Renta avanzada (desigualdad)
            AVG(ra.renta_bruta_llar) AS renta_bruta_llar,
            AVG(ra.indice_gini) AS indice_gini,
            AVG(ra.ratio_p80_p20) AS ratio_p80_p20,
            -- Desempleo
            AVG(des.tasa_desempleo_estimada) AS tasa_desempleo,
            AVG(des.num_desempleados) AS num_desempleados,
            -- Métricas derivadas económicas
            CASE 
                WHEN COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) > 0 AND v.precio_m2_venta IS NOT NULL
                THEN v.precio_m2_venta / (COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) / 12.0)
                ELSE NULL 
            END AS ratio_precio_renta_mensual,
            CASE 
                WHEN a.precio_mes_alquiler > 0 AND COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) > 0
                THEN (a.precio_mes_alquiler * 12.0) / COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) * 100.0
                ELSE NULL 
            END AS pct_renta_destinada_alquiler,
            CASE 
                WHEN COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) > 0 AND a.precio_mes_alquiler > 0
                THEN COALESCE(AVG(r.renta_mediana), AVG(r.renta_euros)) / (a.precio_mes_alquiler * 12.0)
                ELSE NULL 
            END AS affordability_index,
            -- Variables demográficas (para correlaciones)
            AVG(d.poblacion_total) AS poblacion_total,
            AVG(d.edad_media) AS edad_media,
            AVG(d.densidad_hab_km2) AS densidad_hab_km2,
            AVG(d.porc_inmigracion) AS porc_inmigracion,
            AVG(d.pct_mayores_65) AS pct_mayores_65,
            -- Variables de hogares (económicas)
            AVG(ha.promedio_personas_por_hogar) AS promedio_personas_por_hogar,
            AVG(ha.pct_hogares_unipersonales) AS pct_hogares_unipersonales,
            AVG(ha.pct_hogares_nacionalidad_extranjera) AS pct_hogares_extranjeros,
            AVG(ha.pct_presencia_mujeres) AS pct_presencia_mujeres,
            -- Variables de catastro (económicas)
            AVG(ca.superficie_media_m2) AS superficie_media_m2,
            AVG(ca.pct_propietarios_extranjeros) AS pct_propietarios_extranjeros,
            AVG(ca.antiguedad_media_bloque) AS antiguedad_media_bloque
        FROM dim_barrios db
        INNER JOIN years y ON y.barrio_id = db.barrio_id
        LEFT JOIN venta v ON v.barrio_id = y.barrio_id AND v.anio = y.anio
        LEFT JOIN alquiler a ON a.barrio_id = y.barrio_id AND a.anio = y.anio
        LEFT JOIN fact_demografia d ON db.barrio_id = d.barrio_id AND y.anio = d.anio
        LEFT JOIN fact_renta r ON db.barrio_id = r.barrio_id AND y.anio = r.anio
        LEFT JOIN fact_renta_avanzada ra ON db.barrio_id = ra.barrio_id AND y.anio = ra.anio
        LEFT JOIN fact_desempleo des ON db.barrio_id = des.barrio_id AND y.anio = des.anio
        LEFT JOIN fact_hogares_avanzado ha ON db.barrio_id = ha.barrio_id AND y.anio = ha.anio
        LEFT JOIN fact_catastro_avanzado ca ON db.barrio_id = ca.barrio_id AND y.anio = ca.anio
        GROUP BY db.barrio_id, db.barrio_nombre, db.distrito_nombre, y.anio
        ORDER BY db.barrio_id, y.anio;
        """,
        # Correlaciones cruzadas (mejorada - incluye todos los indicadores económicos)
        """
        DROP VIEW IF EXISTS v_correlaciones_cruzadas;
        CREATE VIEW v_correlaciones_cruzadas AS
        SELECT 
            db.barrio_id,
            db.barrio_nombre,
            db.distrito_nombre,
            p.anio,
            -- Variables económicas (completas)
            AVG(p.precio_m2_venta) AS precio_m2_venta,
            AVG(p.precio_mes_alquiler) AS precio_mes_alquiler,
            AVG(r.renta_mediana) AS renta_mediana,
            AVG(ra.renta_bruta_llar) AS renta_bruta_llar,
            AVG(ra.indice_gini) AS indice_gini,
            AVG(ra.ratio_p80_p20) AS ratio_p80_p20,
            AVG(des.tasa_desempleo_estimada) AS tasa_desempleo,
            -- Métricas derivadas económicas
            CASE 
                WHEN AVG(r.renta_mediana) > 0 
                THEN AVG(p.precio_m2_venta) / (AVG(r.renta_mediana) / 12.0)
                ELSE NULL 
            END AS ratio_precio_renta_mensual,
            CASE 
                WHEN AVG(p.precio_mes_alquiler) > 0 AND AVG(r.renta_mediana) > 0
                THEN (AVG(p.precio_mes_alquiler) * 12.0) / AVG(r.renta_mediana) * 100.0
                ELSE NULL 
            END AS pct_renta_destinada_alquiler,
            -- Variables demográficas
            AVG(d.poblacion_total) AS poblacion_total,
            AVG(d.edad_media) AS edad_media,
            AVG(d.densidad_hab_km2) AS densidad_hab_km2,
            AVG(d.porc_inmigracion) AS porc_inmigracion,
            AVG(d.pct_mayores_65) AS pct_mayores_65,
            -- Variables de regulación
            AVG(reg.indice_referencia_alquiler) AS indice_referencia_alquiler,
            AVG(reg.zona_tensionada) AS zona_tensionada,
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
        LEFT JOIN fact_renta_avanzada ra ON db.barrio_id = ra.barrio_id AND p.anio = ra.anio
        LEFT JOIN fact_desempleo des ON db.barrio_id = des.barrio_id AND p.anio = des.anio
        LEFT JOIN fact_regulacion reg ON db.barrio_id = reg.barrio_id AND p.anio = reg.anio
        LEFT JOIN fact_presion_turistica pt ON db.barrio_id = pt.barrio_id AND p.anio = pt.anio
        LEFT JOIN fact_seguridad s ON db.barrio_id = s.barrio_id AND p.anio = s.anio
        LEFT JOIN fact_ruido ru ON db.barrio_id = ru.barrio_id AND p.anio = ru.anio
        WHERE p.precio_m2_venta IS NOT NULL
        GROUP BY db.barrio_id, db.barrio_nombre, db.distrito_nombre, p.anio
        ORDER BY db.barrio_id, p.anio;
        """,
    ]

    with conn:
        for script in scripts:
            conn.executescript(script)

    logger.info("Vistas analíticas creadas/actualizadas correctamente")


__all__ = ["create_analytical_views"]


