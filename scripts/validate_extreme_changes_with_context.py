#!/usr/bin/env python3
"""
Validar cambios extremos con contexto cualitativo operacionalizado.

Este script integra conocimiento experto del mercado inmobiliario de Barcelona
para distinguir entre cambios reales del mercado y artefactos de la muestra.
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
import warnings

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

# 1. DICCIONARIO DE CONTEXTO (La "Inteligencia" del script)
# Define rangos lógicos y banderas de riesgo por código de barrio (Codi_Barri)
CONTEXT_RULES = {
    '12': { # la Marina del Prat Vermell
        'name': 'la Marina del Prat Vermell',
        'type': 'DEVELOPING', # Zona en desarrollo
        'min_price_logic': 1200, # Menos de esto suele ser suelo/industrial en 2014
        'max_price_logic': 3500,
        'risk_factor': 'GENTRIFICATION',
        'notes': 'Refleja transición de zona industrial a vivienda habitable.'
    },
    '22': { # Vallvidrera
        'name': 'Vallvidrera, el Tibidabo i les Planes',
        'type': 'HETEROGENEOUS', # Mezcla de zonas muy distintas
        'min_price_logic': 2500, # Menos de esto suele ser Les Planes (menor valor)
        'max_price_logic': 8000,
        'risk_factor': 'SUBZONE_MIX',
        'notes': 'Mezcla de zona noble de Vallvidrera y zona rural de Les Planes.'
    },
    '54': { # Torre Baró
        'name': 'Torre Baró',
        'type': 'PERIPHERAL',
        'min_price_logic': 800,
        'max_price_logic': 2200, # Más de esto suele ser Obra Nueva puntual entregada
        'risk_factor': 'NEW_BUILD_BIAS',
        'notes': 'Barrio periférico con impacto significativo de obra nueva/VPO.'
    }
}

# Rangos generales por distrito (fallback)
DISTRICT_RULES = {
    "Sarrià-Sant Gervasi": {"min": 2500, "max": 8000, "risk": "LUXURY_AREA"},
    "Les Corts": {"min": 2500, "max": 7500, "risk": "LUXURY_AREA"},
    "Eixample": {"min": 2000, "max": 6500, "risk": "CENTRAL_PREMIUM"},
    "Nou Barris": {"min": 800, "max": 2800, "risk": "PERIPHERAL_LOW"},
    "Sant Martí": {"min": 1500, "max": 5000, "risk": "DEVELOPING_TECH"},
    "Ciutat Vella": {"min": 1800, "max": 6000, "risk": "TOURISM_IMPACT"},
    "Sants-Montjuïc": {"min": 1500, "max": 4500, "risk": "MIXED_DEVELOPMENT"},
    "Horta-Guinardó": {"min": 1500, "max": 4000, "risk": "RESIDENTIAL_STABLE"},
    "Sant Andreu": {"min": 1500, "max": 3800, "risk": "RESIDENTIAL_UPCOMING"},
    "Gràcia": {"min": 2000, "max": 5500, "risk": "GENTRIFIED_BOHEMIAN"}
}


def get_connection():
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        raise


def validate_with_context(codi_barri: str, distrito_nombre: str, 
                          price: float, n_count: int, year: int) -> Dict:
    """
    Aplica lógica cualitativa sobre los datos cuantitativos.
    """
    flags = []
    confidence = 'HIGH'
    risk_factor = 'STANDARD'
    notes = ''
    
    # 1. Check de Muestra Pequeña
    if n_count < 5:
        flags.append('LOW_N_SAMPLE')
        confidence = 'LOW'
        notes = f"N bajo (n={n_count}): Probable medición de edificios específicos, no mercado."
    
    # 2. Check de Contexto Específico por Barrio
    if codi_barri in CONTEXT_RULES:
        ctx = CONTEXT_RULES[codi_barri]
        risk_factor = ctx['risk_factor']
        notes += f" {ctx['notes']}"
        
        # Validación de Rangos Lógicos
        if price < ctx['min_price_logic']:
            flags.append(f"BELOW_LOGIC_THRESHOLD_({ctx['min_price_logic']})")
            if confidence != 'LOW': confidence = 'MEDIUM'
            
        elif price > ctx['max_price_logic']:
            flags.append(f"ABOVE_LOGIC_THRESHOLD_({ctx['max_price_logic']})")
            if risk_factor == 'NEW_BUILD_BIAS':
                flags.append('LIKELY_NEW_BUILD_ARTIFACT')
                confidence = 'LOW'
    
    # 3. Fallback a Reglas de Distrito
    elif distrito_nombre in DISTRICT_RULES:
        dist_ctx = DISTRICT_RULES[distrito_nombre]
        risk_factor = dist_ctx['risk']
        
        if price < dist_ctx['min']:
            flags.append(f"BELOW_DISTRICT_THRESHOLD_({dist_ctx['min']})")
            if confidence != 'LOW': confidence = 'MEDIUM'
        elif price > dist_ctx['max']:
            flags.append(f"ABOVE_DISTRICT_THRESHOLD_({dist_ctx['max']})")
            if confidence != 'LOW': confidence = 'MEDIUM'
            
    return {
        'Validation_Flags': flags,
        'Confidence_Score': confidence,
        'Risk_Factor': risk_factor,
        'Notes': notes.strip()
    }


def get_barrio_info(conn, barrio_nombre: str) -> Dict:
    """Obtener información básica del barrio."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            barrio_id,
            barrio_nombre,
            distrito_nombre,
            codi_barri
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
        "codi_barri": str(result[3])
    }


def analyze_barrio_case(conn, barrio_nombre: str, year: int, change_pct: float) -> Dict:
    """Investigar un caso específico usando la base de datos y lógica cualitativa."""
    info = get_barrio_info(conn, barrio_nombre)
    if not info:
        return {"error": f"Barrio {barrio_nombre} no encontrado"}
    
    barrio_id = info['barrio_id']
    codi_barri = info['codi_barri']
    distrito = info['distrito_nombre']
    
    # Obtener precios del año actual y anterior
    query = """
        SELECT anio, AVG(precio_m2_venta) as avg_price, COUNT(*) as count
        FROM fact_precios
        WHERE barrio_id = %s AND anio IN (%s, %s) AND precio_m2_venta IS NOT NULL
        GROUP BY anio
        ORDER BY anio
    """
    
    df_prices = pd.read_sql_query(query, conn, params=(barrio_id, year - 1, year))
    
    if len(df_prices) < 2:
        return {"error": f"Datos insuficientes para {barrio_nombre} en {year} y {year-1}"}
    
    # Datos del año del cambio
    year_row = df_prices[df_prices['anio'] == year].iloc[0]
    prev_row = df_prices[df_prices['anio'] == year - 1].iloc[0]
    
    current_price = float(year_row['avg_price'])
    current_count = int(year_row['count'])
    
    prev_price = float(prev_row['avg_price'])
    prev_count = int(prev_row['count'])
    
    # Aplicar validación de contexto
    current_validation = validate_with_context(codi_barri, distrito, current_price, current_count, year)
    prev_validation = validate_with_context(codi_barri, distrito, prev_price, prev_count, year - 1)
    
    # Determinar si el cambio es válido o composición de muestra
    interpretation = "LIKELY_VALID_MARKET_CHANGE"
    if current_validation['Confidence_Score'] == 'LOW' or prev_validation['Confidence_Score'] == 'LOW':
        interpretation = "LIKELY_SAMPLE_COMPOSITION_ARTIFACT"
        
    # Casos especiales de gentrificación (Marina Prat Vermell)
    if codi_barri == '12' and current_price > 1200 and prev_price < 1200:
        interpretation = "VALID_GENTRIFICATION_TRANSITION"
        current_validation['Confidence_Score'] = 'HIGH' # Validamos que este salto es "normal" en este contexto
        
    return {
        "barrio": barrio_nombre,
        "codi_barri": codi_barri,
        "distrito": distrito,
        "year": year,
        "change_pct": change_pct,
        "pre-change": {"year": year-1, "price": prev_price, "count": prev_count, "validation": prev_validation},
        "post-change": {"year": year, "price": current_price, "count": current_count, "validation": current_validation},
        "interpretation": interpretation
    }


def main():
    """Función principal para ejecutar la validación de los 3 casos."""
    warnings.filterwarnings('ignore')
    
    print("="*80)
    print("🔍 VALIDACIÓN OPERACIONALIZADA DE CAMBIOS EXTREMOS")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    cases = [
        {"barrio": "la Marina del Prat Vermell", "year": 2015, "change_pct": 135.0},
        {"barrio": "Vallvidrera", "year": 2016, "change_pct": 117.6},
        {"barrio": "Torre Baró", "year": 2019, "change_pct": 174.7}
    ]
    
    conn = get_connection()
    results = []
    
    try:
        for case in cases:
            res = analyze_barrio_case(conn, case["barrio"], case["year"], case["change_pct"])
            if "error" not in res:
                results.append(res)
                print_summary(res)
    finally:
        conn.close()
    
    # Guardar resultados JSON
    output_path = EXPORT_DIR / f"operationalized_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Resultados guardados en: {output_path}")
    generate_final_report(results)


def print_summary(res: Dict):
    """Imprimir resumen legible por consola."""
    print(f"\n📌 BARRIO: {res['barrio']} ({res['codi_barri']}) - {res['year']}")
    print(f"   Cambio: {res['change_pct']}%")
    print(f"   Interpretación: {res['interpretation']}")
    
    pre = res['pre-change']
    post = res['post-change']
    
    print(f"   • {pre['year']}: {pre['price']:.2f}€/m² (n={pre['count']}) -> {pre['validation']['Confidence_Score']} confidence")
    if pre['validation']['Validation_Flags']:
        print(f"     Flags: {', '.join(pre['validation']['Validation_Flags'])}")
        
    print(f"   • {post['year']}: {post['price']:.2f}€/m² (n={post['count']}) -> {post['validation']['Confidence_Score']} confidence")
    if post['validation']['Validation_Flags']:
        print(f"     Flags: {', '.join(post['validation']['Validation_Flags'])}")
    
    if post['validation']['Notes']:
        print(f"   • Notas: {post['validation']['Notes']}")


def generate_final_report(results: List[Dict]):
    """Generar reporte Markdown final."""
    report_path = PROJECT_ROOT / "docs" / "OPERATIONALIZED_VALIDATION_REPORT.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 📑 Reporte de Validación Operacionalizada de Cambios Extremos\n\n")
        f.write(f"**Fecha**: {datetime.now().strftime('%Y-%m-%d')}\n\n")
        f.write("Este reporte integra lógica cualitativa de mercado para distinguir entre tendencias reales y artefactos de muestra.\n\n")
        
        f.write("## 📊 Resumen de Casos\n\n")
        f.write("| Barrio | Año | Cambio | Interpretación | Confianza |\n")
        f.write("|--------|-----|--------|----------------|-----------|\n")
        
        for r in results:
            conf = r['post-change']['validation']['Confidence_Score']
            f.write(f"| {r['barrio']} | {r['year']} | {r['change_pct']}% | {r['interpretation']} | {conf} |\n")
            
        f.write("\n---\n\n")
        
        for r in results:
            f.write(f"### 📍 {r['barrio']} ({r['year']})\n\n")
            f.write(f"- **Diagnóstico**: `{r['interpretation']}`\n")
            f.write(f"- **Cambio**: {r['change_pct']}% ({r['pre-change']['price']:.0f}€ → {r['post-change']['price']:.0f}€)\n")
            f.write(f"- **Muestra**: n={r['pre-change']['count']} (prev) | n={r['post-change']['count']} (actual)\n")
            f.write(f"- **Flags Detectados**: `{', '.join(r['post-change']['validation']['Validation_Flags'] or ['NONE'])}` / `{', '.join(r['pre-change']['validation']['Validation_Flags'] or ['NONE'])}` (prev)\n")
            f.write(f"- **Factor de Riesgo**: `{r['post-change']['validation']['Risk_Factor']}`\n")
            f.write(f"- **Notas Contextuales**: {r['post-change']['validation']['Notes']}\n\n")
            
        f.write("## 🧠 Lógica de Validación Aplicada\n\n")
        f.write("1. **LOW_N_SAMPLE**: Activada cuando N < 5. Indica que estamos midiendo edificios, no el mercado.\n")
        f.write("2. **LOGIC_THRESHOLD**: Activada cuando los precios escapan de los rangos históricos razonables para el barrio/distrito.\n")
        f.write("3. **NEW_BUILD_ARTIFACT**: Específica para Torre Baró y barrios periféricos donde una entrega de obra nueva/VPO distorsiona el promedio anual.\n")
        f.write("4. **GENTRIFICATION_TRANSITION**: Reconoce saltos válidos en zonas de desarrollo como Marina del Prat Vermell.\n")

    print(f"📄 Reporte Markdown generado en: {report_path}")


if __name__ == "__main__":
    main()
