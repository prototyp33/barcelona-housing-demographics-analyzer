#!/usr/bin/env python3
"""
Validar cambios extremos con datos externos y contexto histórico.

Este script investiga los 3 casos pendientes de validación:
- la Marina del Prat Vermell (2015): +135.0%
- Vallvidrera (2016): +117.6%
- Torre Baró (2019): +174.7%

Analiza datos fuente, contexto histórico y genera un reporte de validación.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import json

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

EXPORT_DIR = PROJECT_ROOT / "data" / "exports" / "anomalies"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        raise


def get_barrio_info(conn, barrio_nombre: str) -> Dict:
    """Obtener información básica del barrio."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            barrio_id,
            barrio_nombre,
            distrito_nombre,
            codi_barri,
            geometry_json IS NOT NULL as tiene_geometria
        FROM dim_barrios 
        WHERE barrio_nombre LIKE %s
    """, (f"%{barrio_nombre}%",))
    result = cursor.fetchone()
    if not result:
        return {}
    
    return {
        "barrio_id": result[0],
        "barrio_nombre": result[1],
        "distrito_nombre": result[2],
        "codi_barri": result[3],
        "tiene_geometria": result[4]
    }


def get_detailed_price_data(conn, barrio_id: int, year: int, 
                            window_years: int = 3) -> pd.DataFrame:
    """
    Obtener datos detallados de precios para un barrio y año específico.
    
    Args:
        conn: Conexión a PostgreSQL
        barrio_id: ID del barrio
        year: Año del cambio extremo
        window_years: Años antes y después para contexto
    
    Returns:
        DataFrame con datos detallados
    """
    query = """
        SELECT 
            p.anio,
            p.trimestre,
            p.precio_m2_venta,
            p.precio_mes_alquiler,
            p.source,
            p.dataset_id,
            p.periodo,
            COUNT(*) OVER (PARTITION BY p.anio) as registros_por_anio
        FROM fact_precios p
        WHERE p.barrio_id = %s
          AND p.anio BETWEEN %s AND %s
          AND (p.precio_m2_venta IS NOT NULL OR p.precio_mes_alquiler IS NOT NULL)
        ORDER BY p.anio, p.trimestre, p.precio_m2_venta
    """
    
    start_year = year - window_years
    end_year = year + window_years
    
    df = pd.read_sql_query(query, conn, params=(barrio_id, start_year, end_year))
    return df


def analyze_price_trends(df: pd.DataFrame, year: int) -> Dict:
    """
    Analizar tendencias de precios alrededor del año del cambio extremo.
    
    Args:
        df: DataFrame con datos de precios
        year: Año del cambio extremo
    
    Returns:
        Diccionario con análisis de tendencias
    """
    if len(df) == 0:
        return {"error": "No data available"}
    
    # Agregar por año
    yearly_stats = df.groupby('anio').agg({
        'precio_m2_venta': ['count', 'min', 'max', 'mean', 'median', 'std'],
        'precio_mes_alquiler': ['count', 'min', 'max', 'mean', 'median', 'std']
    }).round(2)
    
    # Aplanar columnas
    yearly_stats.columns = ['_'.join(col).strip('_') for col in yearly_stats.columns.values]
    
    # Calcular cambios porcentuales año a año
    if 'precio_m2_venta_mean' in yearly_stats.columns:
        yearly_stats['precio_change_pct'] = yearly_stats['precio_m2_venta_mean'].pct_change() * 100
        yearly_stats['precio_change_abs'] = yearly_stats['precio_m2_venta_mean'].diff()
    
    # Calcular CV (coeficiente de variación)
    if 'precio_m2_venta_mean' in yearly_stats.columns and 'precio_m2_venta_std' in yearly_stats.columns:
        yearly_stats['cv_precio'] = (yearly_stats['precio_m2_venta_std'] / 
                                     yearly_stats['precio_m2_venta_mean'] * 100).round(2)
    
    # Información específica del año del cambio
    year_data = yearly_stats.loc[year] if year in yearly_stats.index else None
    prev_year_data = yearly_stats.loc[year - 1] if (year - 1) in yearly_stats.index else None
    
    # Análisis de registros individuales del año
    year_records = df[df['anio'] == year].copy()
    prev_year_records = df[df['anio'] == year - 1].copy()
    
    analysis = {
        "yearly_stats": yearly_stats.to_dict('index'),
        "year_data": year_data.to_dict() if year_data is not None else None,
        "prev_year_data": prev_year_data.to_dict() if prev_year_data is not None else None,
        "year_records_count": len(year_records),
        "prev_year_records_count": len(prev_year_records),
        "year_sources": year_records['source'].unique().tolist() if 'source' in year_records.columns else [],
        "year_datasets": year_records['dataset_id'].unique().tolist() if 'dataset_id' in year_records.columns else [],
        "has_high_variance": False,
        "outlier_detection": {}
    }
    
    # Detectar alta varianza
    if year_data is not None and 'cv_precio' in year_data:
        analysis["has_high_variance"] = year_data['cv_precio'] > 50
    
    # Detectar outliers usando IQR
    if len(year_records) > 0 and 'precio_m2_venta' in year_records.columns:
        prices = year_records['precio_m2_venta'].dropna()
        if len(prices) > 0:
            Q1 = prices.quantile(0.25)
            Q3 = prices.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = year_records[
                (year_records['precio_m2_venta'] < lower_bound) | 
                (year_records['precio_m2_venta'] > upper_bound)
            ]
            
            analysis["outlier_detection"] = {
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "outlier_count": len(outliers),
                "outliers": outliers[['trimestre', 'precio_m2_venta', 'source']].to_dict('records') if len(outliers) > 0 else []
            }
    
    return analysis


def get_contextual_data(conn, barrio_id: int, year: int) -> Dict:
    """
    Obtener datos contextuales del barrio (demografía, renta, etc.).
    
    Args:
        conn: Conexión a PostgreSQL
        barrio_id: ID del barrio
        year: Año del cambio extremo
    
    Returns:
        Diccionario con datos contextuales
    """
    context = {}
    
    # Datos demográficos
    try:
        demo_query = """
            SELECT 
                anio,
                poblacion_total,
                renta_mediana,
                densidad_hab_km2
            FROM fact_demografia_ampliada
            WHERE barrio_id = %s
              AND anio BETWEEN %s AND %s
            ORDER BY anio
        """
        demo_df = pd.read_sql_query(demo_query, conn, params=(barrio_id, year - 2, year + 2))
        if len(demo_df) > 0:
            context["demographics"] = demo_df.to_dict('records')
    except Exception as e:
        context["demographics_error"] = str(e)
    
    # Datos de renta
    try:
        renta_query = """
            SELECT 
                anio,
                renta_mediana,
                renta_per_capita
            FROM fact_renta
            WHERE barrio_id = %s
              AND anio BETWEEN %s AND %s
            ORDER BY anio
        """
        renta_df = pd.read_sql_query(renta_query, conn, params=(barrio_id, year - 2, year + 2))
        if len(renta_df) > 0:
            context["renta"] = renta_df.to_dict('records')
    except Exception as e:
        context["renta_error"] = str(e)
    
    return context


def validate_extreme_change(conn, barrio_nombre: str, year: int, 
                           change_pct: float) -> Dict:
    """
    Validar un cambio extremo específico.
    
    Args:
        conn: Conexión a PostgreSQL
        barrio_nombre: Nombre del barrio
        year: Año del cambio extremo
        change_pct: Porcentaje de cambio detectado
    
    Returns:
        Diccionario con validación completa
    """
    print(f"\n{'='*80}")
    print(f"🔍 Validando: {barrio_nombre} ({year}): {change_pct:.1f}%")
    print(f"{'='*80}")
    
    # Información del barrio
    barrio_info = get_barrio_info(conn, barrio_nombre)
    if not barrio_info:
        return {"error": f"Barrio no encontrado: {barrio_nombre}"}
    
    print(f"📍 Barrio: {barrio_info['barrio_nombre']}")
    print(f"   Distrito: {barrio_info['distrito_nombre']}")
    print(f"   Codi Barri: {barrio_info['codi_barri']}")
    
    # Datos detallados de precios
    price_df = get_detailed_price_data(conn, barrio_info['barrio_id'], year)
    
    if len(price_df) == 0:
        return {"error": "No se encontraron datos de precios"}
    
    print(f"\n📊 Registros encontrados: {len(price_df)}")
    print(f"   Años: {price_df['anio'].min()} - {price_df['anio'].max()}")
    
    # Análisis de tendencias
    trend_analysis = analyze_price_trends(price_df, year)
    
    # Datos contextuales
    context_data = get_contextual_data(conn, barrio_info['barrio_id'], year)
    
    # Compilar validación
    validation = {
        "barrio_info": barrio_info,
        "change_info": {
            "year": year,
            "change_pct": change_pct,
            "change_type": "extreme" if abs(change_pct) > 100 else "significant"
        },
        "price_data": {
            "total_records": len(price_df),
            "year_range": {
                "min": int(price_df['anio'].min()),
                "max": int(price_df['anio'].max())
            },
            "sources": price_df['source'].unique().tolist() if 'source' in price_df.columns else [],
            "datasets": price_df['dataset_id'].unique().tolist() if 'dataset_id' in price_df.columns else []
        },
        "trend_analysis": trend_analysis,
        "contextual_data": context_data,
        "validation_assessment": assess_validation(barrio_info, trend_analysis, context_data, change_pct)
    }
    
    # Mostrar resumen
    print_validation_summary(validation)
    
    return validation


def assess_validation(barrio_info: Dict, trend_analysis: Dict, 
                     context_data: Dict, change_pct: float) -> Dict:
    """
    Evaluar si el cambio extremo es válido o un error.
    
    Args:
        barrio_info: Información del barrio
        trend_analysis: Análisis de tendencias
        context_data: Datos contextuales
        change_pct: Porcentaje de cambio
    
    Returns:
        Diccionario con evaluación
    """
    assessment = {
        "likely_valid": None,
        "confidence": "unknown",
        "reasons": [],
        "recommendations": []
    }
    
    # Verificar alta varianza
    if trend_analysis.get("has_high_variance", False):
        assessment["reasons"].append("Alta varianza detectada (CV > 50%)")
        assessment["likely_valid"] = False
        assessment["confidence"] = "high"
        assessment["recommendations"].append("Usar mediana en lugar de media")
    
    # Verificar outliers
    outlier_info = trend_analysis.get("outlier_detection", {})
    if outlier_info.get("outlier_count", 0) > 0:
        assessment["reasons"].append(f"{outlier_info['outlier_count']} outliers detectados")
        assessment["likely_valid"] = False
        assessment["confidence"] = "high"
        assessment["recommendations"].append("Filtrar outliers antes de agregar")
    
    # Verificar número de registros
    year_records = trend_analysis.get("year_records_count", 0)
    prev_records = trend_analysis.get("prev_year_records_count", 0)
    
    if year_records < 3:
        assessment["reasons"].append(f"Pocos registros en año del cambio ({year_records})")
        assessment["confidence"] = "medium"
        assessment["recommendations"].append("Buscar más datos fuente para este año")
    
    if prev_records < 3:
        assessment["reasons"].append(f"Pocos registros en año anterior ({prev_records})")
        assessment["confidence"] = "medium"
    
    # Verificar consistencia de fuentes
    year_sources = trend_analysis.get("year_sources", [])
    if len(year_sources) > 1:
        assessment["reasons"].append(f"Múltiples fuentes en año del cambio: {year_sources}")
        assessment["recommendations"].append("Verificar consistencia entre fuentes")
    
    # Contexto del barrio
    distrito = barrio_info.get("distrito_nombre", "")
    
    # Barrios de lujo pueden tener cambios más extremos
    barrios_lujo = ["Sarrià-Sant Gervasi", "Les Corts", "Eixample"]
    if any(lujo in distrito for lujo in barrios_lujo):
        assessment["reasons"].append(f"Barrio en distrito de lujo ({distrito})")
        if assessment["likely_valid"] is None:
            assessment["likely_valid"] = True
            assessment["confidence"] = "medium"
            assessment["reasons"].append("Cambios extremos más probables en barrios de lujo")
    
    # Si no hay razones para invalidar, considerar válido con baja confianza
    if assessment["likely_valid"] is None:
        assessment["likely_valid"] = True
        assessment["confidence"] = "low"
        assessment["reasons"].append("Requiere validación externa adicional")
        assessment["recommendations"].append("Consultar datos del Ayuntamiento de Barcelona")
        assessment["recommendations"].append("Revisar fuentes alternativas (IDESCAT, Portal de Dades)")
    
    return assessment


def print_validation_summary(validation: Dict):
    """Imprimir resumen de validación."""
    assessment = validation.get("validation_assessment", {})
    
    print(f"\n{'─'*80}")
    print("📋 RESUMEN DE VALIDACIÓN")
    print(f"{'─'*80}")
    
    likely_valid = assessment.get("likely_valid")
    confidence = assessment.get("confidence", "unknown")
    
    if likely_valid is False:
        print("❌ LIKELY INVALID (Probablemente un error de datos)")
    elif likely_valid is True:
        print("✅ LIKELY VALID (Probablemente un cambio real)")
    else:
        print("⚠️  UNCERTAIN (Requiere más investigación)")
    
    print(f"   Confianza: {confidence.upper()}")
    
    reasons = assessment.get("reasons", [])
    if reasons:
        print(f"\n📌 Razones:")
        for reason in reasons:
            print(f"   • {reason}")
    
    recommendations = assessment.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Recomendaciones:")
        for rec in recommendations:
            print(f"   • {rec}")
    
    # Mostrar estadísticas clave
    trend = validation.get("trend_analysis", {})
    year_data = trend.get("year_data")
    prev_data = trend.get("prev_year_data")
    
    if year_data and prev_data:
        print(f"\n📊 Estadísticas:")
        if 'precio_m2_venta_mean' in prev_data:
            print(f"   Año anterior ({validation['change_info']['year'] - 1}): "
                  f"{prev_data['precio_m2_venta_mean']:.2f} €/m² "
                  f"(n={prev_data.get('precio_m2_venta_count', 'N/A')})")
        if 'precio_m2_venta_mean' in year_data:
            print(f"   Año del cambio ({validation['change_info']['year']}): "
                  f"{year_data['precio_m2_venta_mean']:.2f} €/m² "
                  f"(n={year_data.get('precio_m2_venta_count', 'N/A')})")
        if 'cv_precio' in year_data:
            print(f"   CV (variabilidad): {year_data['cv_precio']:.1f}%")
    
    outlier_info = trend.get("outlier_detection", {})
    if outlier_info.get("outlier_count", 0) > 0:
        print(f"\n⚠️  Outliers detectados: {outlier_info['outlier_count']}")
        print(f"   Rango normal: {outlier_info['lower_bound']:.2f} - {outlier_info['upper_bound']:.2f} €/m²")


def main():
    """Función principal."""
    print("="*80)
    print("🔍 VALIDACIÓN DE CAMBIOS EXTREMOS CON DATOS EXTERNOS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Casos a validar
    cases_to_validate = [
        {"barrio": "la Marina del Prat Vermell", "year": 2015, "change_pct": 135.0},
        {"barrio": "Vallvidrera", "year": 2016, "change_pct": 117.6},
        {"barrio": "Torre Baró", "year": 2019, "change_pct": 174.7}
    ]
    
    conn = get_connection()
    all_validations = []
    
    try:
        for case in cases_to_validate:
            validation = validate_extreme_change(
                conn,
                case["barrio"],
                case["year"],
                case["change_pct"]
            )
            all_validations.append(validation)
            
            # Pequeña pausa entre casos
            print("\n")
    
    finally:
        conn.close()
    
    # Guardar resultados
    output_file = EXPORT_DIR / f"external_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convertir numpy types a Python natives para JSON
    def convert_to_json_serializable(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, (np.bool_, np.bool)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(item) for item in obj]
        elif pd.isna(obj):
            return None
        return obj
    
    serializable_validations = convert_to_json_serializable(all_validations)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_validations, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ Validación completada")
    print(f"📄 Resultados guardados en: {output_file}")
    print(f"{'='*80}")
    
    # Generar reporte Markdown
    generate_markdown_report(all_validations, EXPORT_DIR)
    
    return all_validations


def generate_markdown_report(validations: List[Dict], export_dir: Path):
    """Generar reporte en Markdown."""
    report_file = export_dir / f"external_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 🔍 Validación Externa de Cambios Extremos\n\n")
        f.write(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for i, validation in enumerate(validations, 1):
            if "error" in validation:
                f.write(f"## {i}. Error: {validation['error']}\n\n")
                continue
            
            barrio_info = validation.get("barrio_info", {})
            change_info = validation.get("change_info", {})
            assessment = validation.get("validation_assessment", {})
            
            f.write(f"## {i}. {barrio_info.get('barrio_nombre', 'Unknown')} ({change_info.get('year', 'N/A')})\n\n")
            f.write(f"**Cambio detectado**: {change_info.get('change_pct', 0):.1f}%\n\n")
            f.write(f"**Distrito**: {barrio_info.get('distrito_nombre', 'N/A')}\n\n")
            
            # Evaluación
            likely_valid = assessment.get("likely_valid")
            confidence = assessment.get("confidence", "unknown")
            
            if likely_valid is False:
                f.write("### ❌ Evaluación: LIKELY INVALID (Probablemente un error de datos)\n\n")
            elif likely_valid is True:
                f.write("### ✅ Evaluación: LIKELY VALID (Probablemente un cambio real)\n\n")
            else:
                f.write("### ⚠️ Evaluación: UNCERTAIN (Requiere más investigación)\n\n")
            
            f.write(f"**Confianza**: {confidence.upper()}\n\n")
            
            # Razones
            reasons = assessment.get("reasons", [])
            if reasons:
                f.write("### Razones:\n\n")
                for reason in reasons:
                    f.write(f"- {reason}\n")
                f.write("\n")
            
            # Recomendaciones
            recommendations = assessment.get("recommendations", [])
            if recommendations:
                f.write("### Recomendaciones:\n\n")
                for rec in recommendations:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # Estadísticas
            trend = validation.get("trend_analysis", {})
            year_data = trend.get("year_data")
            prev_data = trend.get("prev_year_data")
            
            if year_data and prev_data:
                f.write("### Estadísticas de Precios:\n\n")
                f.write("| Año | Precio Medio (€/m²) | Registros | CV (%) |\n")
                f.write("|-----|---------------------|-----------|--------|\n")
                
                if 'precio_m2_venta_mean' in prev_data:
                    cv_prev = prev_data.get('cv_precio', 'N/A')
                    f.write(f"| {change_info.get('year', 'N/A') - 1} | "
                           f"{prev_data['precio_m2_venta_mean']:.2f} | "
                           f"{prev_data.get('precio_m2_venta_count', 'N/A')} | "
                           f"{cv_prev if isinstance(cv_prev, (int, float)) else 'N/A'} |\n")
                
                if 'precio_m2_venta_mean' in year_data:
                    cv_year = year_data.get('cv_precio', 'N/A')
                    f.write(f"| {change_info.get('year', 'N/A')} | "
                           f"{year_data['precio_m2_venta_mean']:.2f} | "
                           f"{year_data.get('precio_m2_venta_count', 'N/A')} | "
                           f"{cv_year if isinstance(cv_year, (int, float)) else 'N/A'} |\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        f.write("## Resumen General\n\n")
        f.write("| Barrio | Año | Cambio (%) | Evaluación | Confianza |\n")
        f.write("|--------|-----|------------|------------|-----------|\n")
        
        for validation in validations:
            if "error" in validation:
                continue
            
            barrio_info = validation.get("barrio_info", {})
            change_info = validation.get("change_info", {})
            assessment = validation.get("validation_assessment", {})
            
            likely_valid = assessment.get("likely_valid")
            if likely_valid is False:
                eval_text = "❌ INVALID"
            elif likely_valid is True:
                eval_text = "✅ VALID"
            else:
                eval_text = "⚠️ UNCERTAIN"
            
            f.write(f"| {barrio_info.get('barrio_nombre', 'N/A')} | "
                   f"{change_info.get('year', 'N/A')} | "
                   f"{change_info.get('change_pct', 0):.1f}% | "
                   f"{eval_text} | "
                   f"{assessment.get('confidence', 'unknown').upper()} |\n")
    
    print(f"📄 Reporte Markdown generado: {report_file}")


if __name__ == "__main__":
    main()
