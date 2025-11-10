#!/usr/bin/env python3
"""
Script temporal para debugging de datasets CKAN.

Este script ayuda a investigar qué recursos están disponibles en los datasets
de Open Data Barcelona y encontrar los IDs correctos.
"""

import requests
import json
import re
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

CKAN_API_BASE = "https://opendata-ajuntament.barcelona.cat/data/api/3/action"


def debug_dataset_resources(dataset_id):
    """
    Ver TODOS los recursos de un dataset con detalles completos.
    
    Args:
        dataset_id: ID del dataset en CKAN
        
    Returns:
        Diccionario con {año: url} si se encontraron recursos
    """
    print(f"\n{'='*70}")
    print(f"INVESTIGANDO DATASET: {dataset_id}")
    print(f"{'='*70}\n")
    
    api_url = f"{CKAN_API_BASE}/package_show"
    
    try:
        response = requests.get(api_url, params={"id": dataset_id}, timeout=30)
        
        if response.status_code == 404:
            print(f"❌ Error 404: Dataset '{dataset_id}' no encontrado")
            print(f"   El ID puede haber cambiado o el dataset no existe.\n")
            return {}
        
        response.raise_for_status()
        data = response.json()
        
        if not data['success']:
            print(f"❌ Error: API devolvió success=False")
            print(f"   Mensaje: {data.get('error', {}).get('message', 'N/A')}\n")
            return {}
        
        dataset = data['result']
        
        print(f"📦 Nombre: {dataset['title']}")
        print(f"📝 Descripción: {dataset.get('notes', 'N/A')[:150]}...")
        print(f"🔗 URL: https://opendata-ajuntament.barcelona.cat/data/dataset/{dataset_id}")
        print(f"\n{'='*70}")
        print(f"RECURSOS DISPONIBLES ({len(dataset['resources'])} total)")
        print(f"{'='*70}\n")
        
        csv_count = 0
        year_resources = {}
        
        for i, r in enumerate(dataset['resources'], 1):
            is_csv = r.get('format', '').lower() in ['csv', 'text/csv']
            
            if is_csv:
                csv_count += 1
            
            print(f"[{i}] {r.get('name', 'Sin nombre')}")
            print(f"    📄 Formato: {r.get('format', 'N/A')}")
            print(f"    🔗 URL: {r.get('url', 'N/A')[:80]}...")
            print(f"    📅 Creado: {r.get('created', 'N/A')}")
            print(f"    📊 Tamaño: {r.get('size', 'N/A')} bytes")
            
            # Intentar extraer año del nombre
            name = r.get('name', '')
            year_match = re.search(r'(\d{4})', name)
            if year_match:
                year = year_match.group(1)
                year_resources[year] = r.get('url', '')
                print(f"    📆 Año detectado: {year}")
            
            print()
        
        print(f"{'='*70}")
        print(f"RESUMEN")
        print(f"{'='*70}")
        print(f"✓ Total recursos: {len(dataset['resources'])}")
        print(f"✓ Recursos CSV: {csv_count}")
        if year_resources:
            print(f"✓ Años detectados: {sorted(year_resources.keys())}")
        print()
        
        return year_resources
        
    except requests.RequestException as e:
        print(f"❌ Error de red: {e}\n")
        return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {}


def search_dataset_by_keyword(keyword, max_results=10):
    """
    Buscar datasets por palabra clave usando package_search.
    
    Args:
        keyword: Palabra clave para buscar
        max_results: Número máximo de resultados a mostrar
        
    Returns:
        Lista de IDs de datasets encontrados
    """
    print(f"\n{'='*70}")
    print(f"BUSCANDO DATASETS CON PALABRA: '{keyword}'")
    print(f"{'='*70}\n")
    
    api_url = f"{CKAN_API_BASE}/package_search"
    params = {
        'q': keyword,
        'rows': max_results
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data['result']['count'] == 0:
            print(f"❌ No se encontraron datasets con '{keyword}'\n")
            return []
        
        print(f"✓ Encontrados {data['result']['count']} datasets (mostrando primeros {max_results})\n")
        
        dataset_ids = []
        for i, dataset in enumerate(data['result']['results'], 1):
            dataset_id = dataset['name']
            dataset_ids.append(dataset_id)
            
            print(f"[{i}] {dataset['title']}")
            print(f"    ID: {dataset_id}")
            print(f"    URL: https://opendata-ajuntament.barcelona.cat/data/dataset/{dataset_id}")
            print(f"    Recursos: {len(dataset.get('resources', []))} archivos")
            
            # Mostrar tags si existen
            tags = [tag.get('name', '') for tag in dataset.get('tags', [])]
            if tags:
                print(f"    Tags: {', '.join(tags[:5])}")
            print()
        
        return dataset_ids
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_venta_dataset():
    """Analiza el dataset de venta para entender por qué solo tiene 2015."""
    print("\n" + "="*70)
    print("ANÁLISIS DETALLADO: DATASET DE VENTA")
    print("="*70)
    
    venta_years = debug_dataset_resources("habitatges-2na-ma")
    
    if venta_years:
        print(f"\n📊 Años disponibles en dataset de venta:")
        for year in sorted(venta_years.keys()):
            print(f"   - {year}")
        print(f"\n💡 Nota: Si solo se descargó 2015, puede ser que:")
        print(f"   1. Solo 2015 está dentro del rango solicitado")
        print(f"   2. Los otros años tienen nombres diferentes")
        print(f"   3. Los otros años están en recursos con nombres sin año")
    else:
        print("\n⚠️ No se encontraron recursos con años detectados")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SCRIPT DE DEBUGGING - DATASETS OPEN DATA BCN")
    print("="*70)
    
    # 1. Investigar VENTA (ya sabemos que funciona parcialmente)
    print("\n### 1. DATASET DE VENTA ###")
    analyze_venta_dataset()
    
    # 2. Buscar ALQUILER por palabra clave
    print("\n### 2. BÚSQUEDA DE DATASETS DE ALQUILER ###")
    alquiler_ids = search_dataset_by_keyword("lloguer")
    
    # 3. Investigar el primer resultado de alquiler si existe
    if alquiler_ids:
        print("\n### 3. INVESTIGANDO PRIMER DATASET DE ALQUILER ###")
        debug_dataset_resources(alquiler_ids[0])
    
    # 4. Buscar datasets de mercado inmobiliario
    print("\n### 4. BÚSQUEDA DE DATASETS DE MERCADO INMOBILIARIO ###")
    mercado_ids = search_dataset_by_keyword("mercat immobiliari")
    
    # 5. Buscar datasets de vivienda en general
    print("\n### 5. BÚSQUEDA DE DATASETS DE VIVIENDA ###")
    vivienda_ids = search_dataset_by_keyword("habitatge")
    
    # 6. Buscar datasets de precios
    print("\n### 6. BÚSQUEDA DE DATASETS DE PRECIOS ###")
    precios_ids = search_dataset_by_keyword("preu")
    
    print("\n" + "="*70)
    print("DEBUGGING COMPLETADO")
    print("="*70)
    print("\n💡 Próximos pasos:")
    print("   1. Revisa los IDs encontrados arriba")
    print("   2. Actualiza DATASETS en data_extraction.py con los IDs correctos")
    print("   3. Ejecuta la extracción nuevamente")
    print("="*70 + "\n")

