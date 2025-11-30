#!/usr/bin/env python3
"""
Script para probar diferentes parámetros de la API de IDESCAT.

Este script prueba diferentes combinaciones de parámetros para obtener
datos desagregados por barrio del indicador m10409.
"""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List

BASE_URL = "https://api.idescat.cat/indicadors/v1/dades.json"

def test_api_params(indicator_id: str, params: Dict[str, str]) -> Dict[str, Any]:
    """
    Prueba la API con parámetros específicos.
    
    Args:
        indicator_id: ID del indicador (ej: m10409)
        params: Diccionario de parámetros
        
    Returns:
        Respuesta de la API como diccionario
    """
    params['i'] = indicator_id
    params['lang'] = 'es'
    
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    print(f"\n🔍 Probando: {url}")
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
            return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def analyze_response(data: Dict[str, Any]) -> None:
    """
    Analiza la respuesta de la API para extraer información útil.
    
    Args:
        data: Respuesta de la API
    """
    if not data or 'indicadors' not in data:
        print("⚠️ Respuesta vacía o inválida")
        return
    
    indicator_data = data['indicadors'].get('i', {})
    
    # Manejar caso donde 'i' puede ser una lista
    if isinstance(indicator_data, list):
        if len(indicator_data) > 0:
            indicator = indicator_data[0]
        else:
            print("⚠️ Lista de indicadores vacía")
            return
    else:
        indicator = indicator_data
    
    print(f"✅ Indicador: {indicator.get('c', 'N/A')}")
    print(f"   Descripción: {indicator.get('d', 'N/A')}")
    print(f"   ID: {indicator.get('id', 'N/A')}")
    
    # Verificar serie temporal
    if 'ts' in indicator:
        ts = indicator['ts']
        if isinstance(ts, str):
            values = ts.split(',')
            print(f"   Serie temporal: {len(values)} valores")
            print(f"   Valores: {values[:5]}... (primeros 5)")
    
    # Verificar territorio
    if 't' in indicator:
        territory = indicator['t']
        print(f"   Territorio: {territory.get('content', 'N/A')} (tipo: {territory.get('i', 'N/A')})")
    
    # Verificar año
    if 'r' in indicator:
        year = indicator['r']
        print(f"   Año: {year.get('content', 'N/A')}")
    
    # Buscar información de desagregación geográfica
    if 'geo' in str(data):
        print("   ✅ Contiene información geográfica")
    else:
        print("   ⚠️ No se encontró desagregación geográfica visible")

def main():
    """Función principal."""
    print("=" * 70)
    print("Prueba de Parámetros de API IDESCAT - Indicador m10409")
    print("=" * 70)
    
    indicator_id = "m10409"
    
    # Lista de combinaciones de parámetros a probar
    test_cases = [
        {
            "name": "Sin parámetros (default)",
            "params": {}
        },
        {
            "name": "Con geo Barcelona (080193)",
            "params": {"geo": "080193"}
        },
        {
            "name": "Con tipo territorio barrio (b)",
            "params": {"t": "b"}
        },
        {
            "name": "Con geo y tipo barrio",
            "params": {"geo": "080193", "t": "b"}
        },
        {
            "name": "Con parámetro p encapsulado (geo/080193)",
            "params": {"p": "geo/080193"}
        },
        {
            "name": "Con parámetro p (geo/080193;t/b)",
            "params": {"p": "geo/080193;t/b"}
        },
        {
            "name": "Con max para obtener más datos",
            "params": {"max": "100"}
        },
        {
            "name": "Con geo Barcelona y max",
            "params": {"geo": "080193", "max": "100"}
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n{'=' * 70}")
        print(f"Test: {test_case['name']}")
        print(f"{'=' * 70}")
        
        data = test_api_params(indicator_id, test_case['params'].copy())
        if data:
            analyze_response(data)
            results.append({
                "test": test_case['name'],
                "params": test_case['params'],
                "success": True,
                "data": data
            })
        else:
            results.append({
                "test": test_case['name'],
                "params": test_case['params'],
                "success": False
            })
    
    # Resumen
    print(f"\n{'=' * 70}")
    print("RESUMEN")
    print(f"{'=' * 70}")
    print(f"Tests exitosos: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    # Guardar resultados
    output_file = "data/raw/idescat/api_params_test_results.json"
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ Resultados guardados en: {output_file}")

if __name__ == "__main__":
    main()

