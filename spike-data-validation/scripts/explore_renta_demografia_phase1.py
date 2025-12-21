#!/usr/bin/env python3
"""
Exploración de fact_renta y fact_demografia_ampliada para Fase 1 del Issue #238.

Este script:
1. Explora estructura y cobertura de fact_renta
2. Explora estructura y cobertura de fact_demografia_ampliada
3. Calcula correlaciones con precio_m2 para identificar variables relevantes
4. Genera reporte en JSON y Markdown

Uso:
    python3 spike-data-validation/scripts/explore_renta_demografia_phase1.py \
        --db data/processed/database.db \
        --output-dir spike-data-validation/data/logs
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import sqlite3
from scipy.stats import pearsonr

logger = logging.getLogger(__name__)

# Rutas por defecto
DEFAULT_DB = Path("data/processed/database.db")
DEFAULT_OUTPUT_DIR = Path("spike-data-validation/data/logs")
DEFAULT_DOCS_DIR = Path("spike-data-validation/docs")

# Barrios de Gràcia (para validar cobertura del spike)
GRACIA_BARRIOS = [28, 29, 30, 31, 32]


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def explore_fact_renta(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Explora estructura y cobertura de fact_renta.
    
    Args:
        conn: Conexión SQLite abierta
        
    Returns:
        Diccionario con resultados de la exploración
    """
    logger.info("=" * 70)
    logger.info("EXPLORACIÓN: fact_renta")
    logger.info("=" * 70)
    
    results: Dict[str, Any] = {}
    
    try:
        # 1. Estructura de la tabla
        logger.info("1. Analizando estructura de la tabla...")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(fact_renta)")
        columns_info = cursor.fetchall()
        
        columns = [col[1] for col in columns_info]
        column_types = {col[1]: col[2] for col in columns_info}
        
        results["structure"] = {
            "columns": columns,
            "column_types": column_types,
            "num_columns": len(columns)
        }
        logger.info(f"   ✅ {len(columns)} columnas encontradas: {', '.join(columns)}")
        
        # 2. Muestra de datos
        logger.info("2. Obteniendo muestra de datos...")
        df_sample = pd.read_sql_query("SELECT * FROM fact_renta LIMIT 10", conn)
        results["sample"] = df_sample.to_dict(orient="records")
        logger.info(f"   ✅ Muestra de {len(df_sample)} registros obtenida")
        
        # 3. Estadísticas generales
        logger.info("3. Calculando estadísticas generales...")
        stats_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT barrio_id) as unique_barrios,
                COUNT(DISTINCT anio) as unique_anios,
                MIN(anio) as min_anio,
                MAX(anio) as max_anio,
                COUNT(DISTINCT CASE WHEN barrio_id IN (28, 29, 30, 31, 32) THEN barrio_id END) as gracia_barrios
            FROM fact_renta
        """
        df_stats = pd.read_sql_query(stats_query, conn)
        stats = df_stats.iloc[0].to_dict()
        results["coverage"] = stats
        logger.info(f"   ✅ Total registros: {stats['total_records']}")
        logger.info(f"   ✅ Barrios únicos: {stats['unique_barrios']}")
        logger.info(f"   ✅ Años: {stats['min_anio']}-{stats['max_anio']} ({stats['unique_anios']} años)")
        logger.info(f"   ✅ Barrios Gràcia: {stats['gracia_barrios']}/5")
        
        # 4. Años disponibles
        logger.info("4. Analizando años disponibles...")
        years_query = """
            SELECT DISTINCT anio 
            FROM fact_renta 
            ORDER BY anio
        """
        df_years = pd.read_sql_query(years_query, conn)
        available_years = df_years['anio'].tolist()
        results["available_years"] = available_years
        logger.info(f"   ✅ Años disponibles: {available_years}")
        
        # 5. Valores nulos por columna
        logger.info("5. Analizando valores nulos...")
        null_query = """
            SELECT 
                SUM(CASE WHEN renta_euros IS NULL THEN 1 ELSE 0 END) as null_renta_euros,
                SUM(CASE WHEN renta_promedio IS NULL THEN 1 ELSE 0 END) as null_renta_promedio,
                SUM(CASE WHEN renta_mediana IS NULL THEN 1 ELSE 0 END) as null_renta_mediana,
                SUM(CASE WHEN renta_min IS NULL THEN 1 ELSE 0 END) as null_renta_min,
                SUM(CASE WHEN renta_max IS NULL THEN 1 ELSE 0 END) as null_renta_max,
                COUNT(*) as total
            FROM fact_renta
        """
        df_nulls = pd.read_sql_query(null_query, conn)
        null_stats = df_nulls.iloc[0].to_dict()
        results["null_counts"] = {
            "renta_euros": int(null_stats["null_renta_euros"]),
            "renta_promedio": int(null_stats["null_renta_promedio"]),
            "renta_mediana": int(null_stats["null_renta_mediana"]),
            "renta_min": int(null_stats["null_renta_min"]),
            "renta_max": int(null_stats["null_renta_max"]),
            "total_records": int(null_stats["total"])
        }
        logger.info(f"   ✅ Valores nulos analizados")
        
        # 6. Estadísticas descriptivas de variables numéricas
        logger.info("6. Calculando estadísticas descriptivas...")
        desc_query = """
            SELECT 
                AVG(renta_euros) as mean_renta_euros,
                AVG(renta_promedio) as mean_renta_promedio,
                AVG(renta_mediana) as mean_renta_mediana,
                MIN(renta_euros) as min_renta_euros,
                MAX(renta_euros) as max_renta_euros,
                MIN(renta_mediana) as min_renta_mediana,
                MAX(renta_mediana) as max_renta_mediana
            FROM fact_renta
            WHERE renta_euros IS NOT NULL
        """
        df_desc = pd.read_sql_query(desc_query, conn)
        if len(df_desc) > 0:
            desc_stats = df_desc.iloc[0].to_dict()
            results["descriptive_stats"] = {k: float(v) if v is not None else None for k, v in desc_stats.items()}
            logger.info(f"   ✅ Estadísticas descriptivas calculadas")
        
        # 7. Cobertura específica para Gràcia
        logger.info("7. Analizando cobertura para barrios de Gràcia...")
        gracia_query = """
            SELECT 
                barrio_id,
                COUNT(*) as records,
                MIN(anio) as min_anio,
                MAX(anio) as max_anio,
                COUNT(DISTINCT anio) as unique_anios
            FROM fact_renta
            WHERE barrio_id IN (28, 29, 30, 31, 32)
            GROUP BY barrio_id
            ORDER BY barrio_id
        """
        df_gracia = pd.read_sql_query(gracia_query, conn)
        results["gracia_coverage"] = df_gracia.to_dict(orient="records")
        logger.info(f"   ✅ Cobertura Gràcia: {len(df_gracia)} barrios con datos")
        
    except Exception as e:
        logger.error(f"Error explorando fact_renta: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results


def explore_fact_demografia_ampliada(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Explora estructura y cobertura de fact_demografia_ampliada.
    
    Args:
        conn: Conexión SQLite abierta
        
    Returns:
        Diccionario con resultados de la exploración
    """
    logger.info("=" * 70)
    logger.info("EXPLORACIÓN: fact_demografia_ampliada")
    logger.info("=" * 70)
    
    results: Dict[str, Any] = {}
    
    try:
        # 1. Estructura de la tabla
        logger.info("1. Analizando estructura de la tabla...")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(fact_demografia_ampliada)")
        columns_info = cursor.fetchall()
        
        columns = [col[1] for col in columns_info]
        column_types = {col[1]: col[2] for col in columns_info}
        
        results["structure"] = {
            "columns": columns,
            "column_types": column_types,
            "num_columns": len(columns)
        }
        logger.info(f"   ✅ {len(columns)} columnas encontradas: {', '.join(columns)}")
        
        # 2. Muestra de datos
        logger.info("2. Obteniendo muestra de datos...")
        df_sample = pd.read_sql_query("SELECT * FROM fact_demografia_ampliada LIMIT 10", conn)
        results["sample"] = df_sample.to_dict(orient="records")
        logger.info(f"   ✅ Muestra de {len(df_sample)} registros obtenida")
        
        # 3. Valores únicos de campos categóricos
        logger.info("3. Analizando valores únicos de campos categóricos...")
        unique_sexo = pd.read_sql_query("SELECT DISTINCT sexo FROM fact_demografia_ampliada WHERE sexo IS NOT NULL", conn)
        unique_grupo_edad = pd.read_sql_query("SELECT DISTINCT grupo_edad FROM fact_demografia_ampliada WHERE grupo_edad IS NOT NULL", conn)
        unique_nacionalidad = pd.read_sql_query("SELECT DISTINCT nacionalidad FROM fact_demografia_ampliada WHERE nacionalidad IS NOT NULL", conn)
        
        results["unique_values"] = {
            "sexo": unique_sexo['sexo'].tolist() if len(unique_sexo) > 0 else [],
            "grupo_edad": unique_grupo_edad['grupo_edad'].tolist() if len(unique_grupo_edad) > 0 else [],
            "nacionalidad": unique_nacionalidad['nacionalidad'].tolist() if len(unique_nacionalidad) > 0 else []
        }
        logger.info(f"   ✅ Valores únicos:")
        logger.info(f"      - sexo: {results['unique_values']['sexo']}")
        logger.info(f"      - grupo_edad: {results['unique_values']['grupo_edad']}")
        logger.info(f"      - nacionalidad: {len(results['unique_values']['nacionalidad'])} valores")
        
        # 4. Estadísticas generales
        logger.info("4. Calculando estadísticas generales...")
        stats_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT barrio_id) as unique_barrios,
                COUNT(DISTINCT anio) as unique_anios,
                MIN(anio) as min_anio,
                MAX(anio) as max_anio,
                COUNT(DISTINCT CASE WHEN barrio_id IN (28, 29, 30, 31, 32) THEN barrio_id END) as gracia_barrios
            FROM fact_demografia_ampliada
        """
        df_stats = pd.read_sql_query(stats_query, conn)
        stats = df_stats.iloc[0].to_dict()
        results["coverage"] = stats
        logger.info(f"   ✅ Total registros: {stats['total_records']}")
        logger.info(f"   ✅ Barrios únicos: {stats['unique_barrios']}")
        logger.info(f"   ✅ Años: {stats['min_anio']}-{stats['max_anio']} ({stats['unique_anios']} años)")
        logger.info(f"   ✅ Barrios Gràcia: {stats['gracia_barrios']}/5")
        
        # 5. Años disponibles
        logger.info("5. Analizando años disponibles...")
        years_query = """
            SELECT DISTINCT anio 
            FROM fact_demografia_ampliada 
            ORDER BY anio
        """
        df_years = pd.read_sql_query(years_query, conn)
        available_years = df_years['anio'].tolist()
        results["available_years"] = available_years
        logger.info(f"   ✅ Años disponibles: {available_years}")
        
        # 6. Valores nulos
        logger.info("6. Analizando valores nulos...")
        null_query = """
            SELECT 
                SUM(CASE WHEN poblacion IS NULL THEN 1 ELSE 0 END) as null_poblacion,
                SUM(CASE WHEN sexo IS NULL THEN 1 ELSE 0 END) as null_sexo,
                SUM(CASE WHEN grupo_edad IS NULL THEN 1 ELSE 0 END) as null_grupo_edad,
                SUM(CASE WHEN nacionalidad IS NULL THEN 1 ELSE 0 END) as null_nacionalidad,
                COUNT(*) as total
            FROM fact_demografia_ampliada
        """
        df_nulls = pd.read_sql_query(null_query, conn)
        null_stats = df_nulls.iloc[0].to_dict()
        results["null_counts"] = {
            "poblacion": int(null_stats["null_poblacion"]),
            "sexo": int(null_stats["null_sexo"]),
            "grupo_edad": int(null_stats["null_grupo_edad"]),
            "nacionalidad": int(null_stats["null_nacionalidad"]),
            "total_records": int(null_stats["total"])
        }
        logger.info(f"   ✅ Valores nulos analizados")
        
        # 7. Estadísticas descriptivas de población
        logger.info("7. Calculando estadísticas descriptivas de población...")
        desc_query = """
            SELECT 
                AVG(poblacion) as mean_poblacion,
                MIN(poblacion) as min_poblacion,
                MAX(poblacion) as max_poblacion,
                SUM(poblacion) as total_poblacion
            FROM fact_demografia_ampliada
            WHERE poblacion IS NOT NULL
        """
        df_desc = pd.read_sql_query(desc_query, conn)
        if len(df_desc) > 0:
            desc_stats = df_desc.iloc[0].to_dict()
            results["descriptive_stats"] = {k: float(v) if v is not None else None for k, v in desc_stats.items()}
            logger.info(f"   ✅ Estadísticas descriptivas calculadas")
        
        # 8. Cobertura específica para Gràcia
        logger.info("8. Analizando cobertura para barrios de Gràcia...")
        gracia_query = """
            SELECT 
                barrio_id,
                COUNT(*) as records,
                MIN(anio) as min_anio,
                MAX(anio) as max_anio,
                COUNT(DISTINCT anio) as unique_anios
            FROM fact_demografia_ampliada
            WHERE barrio_id IN (28, 29, 30, 31, 32)
            GROUP BY barrio_id
            ORDER BY barrio_id
        """
        df_gracia = pd.read_sql_query(gracia_query, conn)
        results["gracia_coverage"] = df_gracia.to_dict(orient="records")
        logger.info(f"   ✅ Cobertura Gràcia: {len(df_gracia)} barrios con datos")
        
    except Exception as e:
        logger.error(f"Error explorando fact_demografia_ampliada: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results


def calculate_correlations_with_price(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calcula correlaciones entre variables de renta/demografía y precio_m2.
    
    Args:
        conn: Conexión SQLite abierta
        
    Returns:
        Diccionario con correlaciones calculadas
    """
    logger.info("=" * 70)
    logger.info("CÁLCULO DE CORRELACIONES CON precio_m2")
    logger.info("=" * 70)
    
    results: Dict[str, Any] = {}
    
    try:
        # 1. Cargar fact_precios y calcular precio_m2_mean por barrio×año
        logger.info("1. Cargando fact_precios...")
        precios_query = """
            SELECT 
                barrio_id,
                anio,
                AVG(precio_m2_venta) as precio_m2_mean,
                AVG(precio_mes_alquiler) as precio_alquiler_mean
            FROM fact_precios
            WHERE precio_m2_venta IS NOT NULL
            GROUP BY barrio_id, anio
            ORDER BY barrio_id, anio
        """
        df_precios = pd.read_sql_query(precios_query, conn)
        logger.info(f"   ✅ {len(df_precios)} registros de precios cargados")
        
        # Filtrar solo barrios de Gràcia para relevancia del spike
        df_precios_gracia = df_precios[df_precios['barrio_id'].isin(GRACIA_BARRIOS)].copy()
        logger.info(f"   ✅ {len(df_precios_gracia)} registros de Gràcia")
        
        if len(df_precios_gracia) == 0:
            logger.warning("   ⚠️  No hay datos de precios para Gràcia")
            results["error"] = "No hay datos de precios para Gràcia"
            return results
        
        # 2. Cargar fact_renta y calcular agregaciones por barrio×año
        logger.info("2. Cargando fact_renta...")
        renta_query = """
            SELECT 
                barrio_id,
                anio,
                AVG(renta_euros) as renta_euros_mean,
                AVG(renta_promedio) as renta_promedio_mean,
                AVG(renta_mediana) as renta_mediana_mean,
                AVG(renta_min) as renta_min_mean,
                AVG(renta_max) as renta_max_mean
            FROM fact_renta
            WHERE barrio_id IN (28, 29, 30, 31, 32)
            GROUP BY barrio_id, anio
            ORDER BY barrio_id, anio
        """
        df_renta = pd.read_sql_query(renta_query, conn)
        logger.info(f"   ✅ {len(df_renta)} registros de renta cargados")
        
        # 3. Merge precios con renta
        logger.info("3. Calculando correlaciones con variables de renta...")
        df_merged = df_precios_gracia.merge(
            df_renta,
            on=['barrio_id', 'anio'],
            how='inner'
        )
        logger.info(f"   ✅ {len(df_merged)} registros matched")
        
        renta_correlations = {}
        if len(df_merged) > 0:
            renta_vars = ['renta_euros_mean', 'renta_promedio_mean', 'renta_mediana_mean', 
                          'renta_min_mean', 'renta_max_mean']
            
            for var in renta_vars:
                if var in df_merged.columns:
                    valid_data = df_merged[[var, 'precio_m2_mean']].dropna()
                    if len(valid_data) > 1:
                        corr, p_value = pearsonr(valid_data[var], valid_data['precio_m2_mean'])
                        renta_correlations[var] = {
                            "correlation": float(corr),
                            "p_value": float(p_value),
                            "n_observations": int(len(valid_data)),
                            "significant": p_value < 0.05
                        }
                        logger.info(f"      {var}: r={corr:.3f}, p={p_value:.3f}, n={len(valid_data)}")
        
        results["renta_correlations"] = renta_correlations
        
        # 4. Cargar fact_demografia_ampliada y calcular agregaciones
        logger.info("4. Cargando fact_demografia_ampliada...")
        demo_query = """
            SELECT 
                barrio_id,
                anio,
                SUM(poblacion) as poblacion_total,
                -- Proporción por sexo
                SUM(CASE WHEN sexo = 'hombre' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_hombres,
                SUM(CASE WHEN sexo = 'mujer' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_mujeres,
                -- Proporción por grupo de edad
                SUM(CASE WHEN grupo_edad = '18-34' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_18_34,
                SUM(CASE WHEN grupo_edad = '35-49' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_35_49,
                SUM(CASE WHEN grupo_edad = '50-64' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_50_64,
                SUM(CASE WHEN grupo_edad = '65+' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_65_plus,
                -- Proporción por nacionalidad
                SUM(CASE WHEN nacionalidad = 'España' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_espana,
                SUM(CASE WHEN nacionalidad != 'España' AND nacionalidad IS NOT NULL THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_extranjeros
            FROM fact_demografia_ampliada
            WHERE barrio_id IN (28, 29, 30, 31, 32)
            GROUP BY barrio_id, anio
            HAVING SUM(poblacion) > 0
            ORDER BY barrio_id, anio
        """
        df_demo = pd.read_sql_query(demo_query, conn)
        logger.info(f"   ✅ {len(df_demo)} registros demográficos cargados")
        
        # 5. Merge precios con demografía
        logger.info("5. Calculando correlaciones con variables demográficas...")
        df_merged_demo = df_precios_gracia.merge(
            df_demo,
            on=['barrio_id', 'anio'],
            how='inner'
        )
        logger.info(f"   ✅ {len(df_merged_demo)} registros matched")
        
        demo_correlations = {}
        if len(df_merged_demo) > 0:
            demo_vars = ['poblacion_total', 'prop_hombres', 'prop_mujeres', 
                        'prop_18_34', 'prop_35_49', 'prop_50_64', 'prop_65_plus',
                        'prop_espana', 'prop_extranjeros']
            
            for var in demo_vars:
                if var in df_merged_demo.columns:
                    valid_data = df_merged_demo[[var, 'precio_m2_mean']].dropna()
                    if len(valid_data) > 1:
                        corr, p_value = pearsonr(valid_data[var], valid_data['precio_m2_mean'])
                        demo_correlations[var] = {
                            "correlation": float(corr),
                            "p_value": float(p_value),
                            "n_observations": int(len(valid_data)),
                            "significant": p_value < 0.05
                        }
                        logger.info(f"      {var}: r={corr:.3f}, p={p_value:.3f}, n={len(valid_data)}")
        
        results["demografia_correlations"] = demo_correlations
        
        # 6. Identificar variables relevantes (|corr| > 0.3)
        logger.info("6. Identificando variables relevantes (|corr| > 0.3)...")
        relevant_vars = []
        
        for var, stats in renta_correlations.items():
            if abs(stats["correlation"]) > 0.3:
                relevant_vars.append({
                    "variable": var,
                    "type": "renta",
                    "correlation": stats["correlation"],
                    "p_value": stats["p_value"],
                    "significant": stats["significant"]
                })
        
        for var, stats in demo_correlations.items():
            if abs(stats["correlation"]) > 0.3:
                relevant_vars.append({
                    "variable": var,
                    "type": "demografia",
                    "correlation": stats["correlation"],
                    "p_value": stats["p_value"],
                    "significant": stats["significant"]
                })
        
        results["relevant_variables"] = relevant_vars
        logger.info(f"   ✅ {len(relevant_vars)} variables relevantes identificadas")
        
    except Exception as e:
        logger.error(f"Error calculando correlaciones: {e}", exc_info=True)
        results["error"] = str(e)
    
    return results


def generate_report(results: Dict[str, Any], output_dir: Path, docs_dir: Path) -> None:
    """
    Genera reporte en JSON y Markdown.
    
    Args:
        results: Diccionario con todos los resultados
        output_dir: Directorio para guardar JSON
        docs_dir: Directorio para guardar Markdown
    """
    logger.info("=" * 70)
    logger.info("GENERANDO REPORTES")
    logger.info("=" * 70)
    
    # 1. Guardar JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "fase1_exploracion_renta_demografia.json"
    
    # Convertir numpy types a Python nativos para JSON
    def convert_to_native(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        elif obj is None:
            return None
        # Intentar verificar si es NaN (solo para escalares)
        try:
            if pd.isna(obj) and not isinstance(obj, (str, dict, list)):
                return None
        except (ValueError, TypeError):
            pass
        return obj
    
    results_serializable = convert_to_native(results)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Reporte JSON guardado: {json_path}")
    
    # 2. Generar Markdown
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = docs_dir / "FASE1_EXPLORACION_RENTA_DEMOGRAFIA.md"
    
    md_content = generate_markdown_report(results)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f"✅ Reporte Markdown guardado: {md_path}")


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """
    Genera contenido Markdown del reporte.
    
    Args:
        results: Diccionario con todos los resultados
        
    Returns:
        Contenido Markdown como string
    """
    md = []
    md.append("# Fase 1: Exploración de fact_renta y fact_demografia_ampliada")
    md.append("")
    md.append("**Issue**: #238 - Integrar fact_renta y fact_demografia_ampliada al MACRO v0.2")
    md.append("**Fecha**: " + pd.Timestamp.now().strftime("%Y-%m-%d"))
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 📊 Resumen Ejecutivo")
    md.append("")
    
    # Resumen de fact_renta
    if "fact_renta" in results:
        renta = results["fact_renta"]
        if "coverage" in renta:
            cov = renta["coverage"]
            md.append("### fact_renta")
            md.append(f"- **Total registros**: {cov.get('total_records', 'N/A')}")
            md.append(f"- **Barrios únicos**: {cov.get('unique_barrios', 'N/A')}")
            md.append(f"- **Años**: {cov.get('min_anio', 'N/A')}-{cov.get('max_anio', 'N/A')}")
            md.append(f"- **Barrios Gràcia**: {cov.get('gracia_barrios', 'N/A')}/5")
            md.append("")
    
    # Resumen de fact_demografia_ampliada
    if "fact_demografia_ampliada" in results:
        demo = results["fact_demografia_ampliada"]
        if "coverage" in demo:
            cov = demo["coverage"]
            md.append("### fact_demografia_ampliada")
            md.append(f"- **Total registros**: {cov.get('total_records', 'N/A')}")
            md.append(f"- **Barrios únicos**: {cov.get('unique_barrios', 'N/A')}")
            md.append(f"- **Años**: {cov.get('min_anio', 'N/A')}-{cov.get('max_anio', 'N/A')}")
            md.append(f"- **Barrios Gràcia**: {cov.get('gracia_barrios', 'N/A')}/5")
            md.append("")
    
    # Variables relevantes
    if "correlations" in results and "relevant_variables" in results["correlations"]:
        relevant = results["correlations"]["relevant_variables"]
        md.append("### Variables Relevantes (|corr| > 0.3)")
        md.append(f"- **Total**: {len(relevant)} variables identificadas")
        md.append("")
        for var_info in relevant:
            md.append(f"- **{var_info['variable']}** ({var_info['type']}): r={var_info['correlation']:.3f}, p={var_info['p_value']:.3f}")
        md.append("")
    
    md.append("---")
    md.append("")
    md.append("## 📋 Estructura de fact_renta")
    md.append("")
    
    if "fact_renta" in results:
        renta = results["fact_renta"]
        if "structure" in renta:
            struct = renta["structure"]
            md.append(f"**Columnas**: {struct.get('num_columns', 'N/A')}")
            md.append("")
            md.append("| Columna | Tipo |")
            md.append("|---------|------|")
            for col, col_type in struct.get("column_types", {}).items():
                md.append(f"| {col} | {col_type} |")
            md.append("")
    
    md.append("---")
    md.append("")
    md.append("## 📋 Estructura de fact_demografia_ampliada")
    md.append("")
    
    if "fact_demografia_ampliada" in results:
        demo = results["fact_demografia_ampliada"]
        if "structure" in demo:
            struct = demo["structure"]
            md.append(f"**Columnas**: {struct.get('num_columns', 'N/A')}")
            md.append("")
            md.append("| Columna | Tipo |")
            md.append("|---------|------|")
            for col, col_type in struct.get("column_types", {}).items():
                md.append(f"| {col} | {col_type} |")
            md.append("")
        
        if "unique_values" in demo:
            unique = demo["unique_values"]
            md.append("### Valores Únicos")
            md.append(f"- **sexo**: {', '.join(unique.get('sexo', []))}")
            md.append(f"- **grupo_edad**: {', '.join(unique.get('grupo_edad', []))}")
            md.append(f"- **nacionalidad**: {len(unique.get('nacionalidad', []))} valores")
            md.append("")
    
    md.append("---")
    md.append("")
    md.append("## 🔗 Correlaciones con precio_m2")
    md.append("")
    md.append("### Variables de Renta")
    md.append("")
    md.append("| Variable | Correlación | p-value | n | Significativa |")
    md.append("|----------|-------------|---------|---|----------------|")
    
    if "correlations" in results and "renta_correlations" in results["correlations"]:
        for var, stats in results["correlations"]["renta_correlations"].items():
            sig = "✅" if stats["significant"] else "❌"
            md.append(f"| {var} | {stats['correlation']:.3f} | {stats['p_value']:.3f} | {stats['n_observations']} | {sig} |")
    md.append("")
    
    md.append("### Variables Demográficas")
    md.append("")
    md.append("| Variable | Correlación | p-value | n | Significativa |")
    md.append("|----------|-------------|---------|---|----------------|")
    
    if "correlations" in results and "demografia_correlations" in results["correlations"]:
        for var, stats in results["correlations"]["demografia_correlations"].items():
            sig = "✅" if stats["significant"] else "❌"
            md.append(f"| {var} | {stats['correlation']:.3f} | {stats['p_value']:.3f} | {stats['n_observations']} | {sig} |")
    md.append("")
    
    md.append("---")
    md.append("")
    md.append("## 💡 Recomendaciones para Fase 2")
    md.append("")
    
    if "correlations" in results and "relevant_variables" in results["correlations"]:
        relevant = results["correlations"]["relevant_variables"]
        if len(relevant) > 0:
            md.append("### Variables a Incluir en MACRO v0.3")
            md.append("")
            for var_info in relevant:
                md.append(f"- ✅ **{var_info['variable']}** ({var_info['type']}): r={var_info['correlation']:.3f}")
            md.append("")
        else:
            md.append("⚠️ No se identificaron variables con |corr| > 0.3. Revisar estrategia de agregación.")
            md.append("")
    
    md.append("---")
    md.append("")
    md.append("**Última actualización**: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    return "\n".join(md)


def main() -> int:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Exploración de fact_renta y fact_demografia_ampliada para Fase 1"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Ruta a la base de datos SQLite"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directorio para guardar reporte JSON"
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=DEFAULT_DOCS_DIR,
        help="Directorio para guardar reporte Markdown"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("FASE 1: EXPLORACIÓN fact_renta y fact_demografia_ampliada")
    logger.info("=" * 70)
    
    # Verificar base de datos
    if not args.db.exists():
        logger.error(f"Base de datos no encontrada: {args.db}")
        return 1
    
    # Conectar a base de datos
    conn = sqlite3.connect(str(args.db))
    
    try:
        # Explorar fact_renta
        results_renta = explore_fact_renta(conn)
        
        # Explorar fact_demografia_ampliada
        results_demo = explore_fact_demografia_ampliada(conn)
        
        # Calcular correlaciones
        results_corr = calculate_correlations_with_price(conn)
        
        # Consolidar resultados
        results = {
            "fact_renta": results_renta,
            "fact_demografia_ampliada": results_demo,
            "correlations": results_corr
        }
        
        # Generar reportes
        generate_report(results, args.output_dir, args.docs_dir)
        
        logger.info("=" * 70)
        logger.info("✅ FASE 1 COMPLETADA")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error en Fase 1: {e}", exc_info=True)
        return 1
        
    finally:
        conn.close()


if __name__ == "__main__":
    exit(main())

