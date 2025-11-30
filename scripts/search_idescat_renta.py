#!/usr/bin/env python3
"""
Script para buscar indicadores de renta en la API de IDESCAT.

Este script explora la API de indicadores para encontrar IDs relacionados
con renta disponible por barrio.
"""

import json
import sys
from typing import List, Dict, Any

def search_renta_indicators(data: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
    """
    Busca indicadores relacionados con renta en la estructura de datos.
    
    Args:
        data: Datos JSON de la API
        keywords: Lista de palabras clave a buscar
        
    Returns:
        Lista de indicadores encontrados
    """
    results = []
    
    def search_recursive(items: List[Dict], path: List[str] = []):
        """Busca recursivamente en la estructura anidada."""
        for item in items:
            current_path = path + [item.get('content', '')]
            
            # Si tiene sub-items, buscar recursivamente
            if 'v' in item and isinstance(item['v'], list):
                search_recursive(item['v'], current_path)
            
            # Buscar en content y desc
            content = str(item.get('content', '')).lower()
            desc = str(item.get('desc', '')).lower()
            
            # Verificar si contiene alguna palabra clave
            if any(keyword in content or keyword in desc for keyword in keywords):
                results.append({
                    'id': item.get('id'),
                    'content': item.get('content'),
                    'desc': item.get('desc'),
                    'date': item.get('date'),
                    'path': ' > '.join([p for p in current_path if p])
                })
    
    # Iniciar búsqueda
    indicators = data.get('indicadors', {}).get('v', {}).get('v', [])
    search_recursive(indicators)
    
    return results


def main():
    """Función principal."""
    # Palabras clave a buscar
    keywords = ['renta', 'renda', 'income', 'disponible', 'ingres', 'ingreso', 
                'familiar', 'bruta', 'neta', 'per càpita', 'per capita']
    
    print("=" * 70)
    print("Búsqueda de Indicadores de Renta en IDESCAT API")
    print("=" * 70)
    print(f"\nPalabras clave: {', '.join(keywords)}")
    print("\nCargando datos de la API...")
    
    try:
        # Leer desde archivo si existe, sino desde stdin
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            import urllib.request
            url = "https://api.idescat.cat/indicadors/v1/nodes.json?lang=es"
            print(f"Descargando desde: {url}")
            with urllib.request.urlopen(url) as response:
                data = json.load(response)
        
        print("✓ Datos cargados")
        print("\nBuscando indicadores de renta...")
        
        results = search_renta_indicators(data, keywords)
        
        print(f"\n{'=' * 70}")
        print(f"Resultados encontrados: {len(results)}")
        print(f"{'=' * 70}\n")
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"{i}. ID: {result['id']}")
                print(f"   Contenido: {result['content']}")
                print(f"   Descripción: {result['desc']}")
                if result.get('date'):
                    print(f"   Fecha: {result['date']}")
                if result.get('path'):
                    print(f"   Ruta: {result['path']}")
                print()
            
            # Guardar resultados en archivo
            output_file = "data/raw/idescat/indicadores_renta_encontrados.json"
            import os
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"✓ Resultados guardados en: {output_file}")
            
            # Mostrar IDs únicos
            ids = [r['id'] for r in results if r.get('id')]
            print(f"\nIDs encontrados: {', '.join(ids)}")
            
        else:
            print("⚠ No se encontraron indicadores de renta con las palabras clave especificadas.")
            print("\nSugerencias:")
            print("1. Revisar la estructura completa de la API")
            print("2. Buscar manualmente en: https://www.idescat.cat/dades/")
            print("3. Considerar estrategias alternativas (web scraping, archivos públicos)")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

