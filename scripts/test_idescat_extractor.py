#!/usr/bin/env python3
"""
Script de prueba para el extractor de IDESCAT.

Este script demuestra cómo usar el IDESCATExtractor para extraer datos
de renta histórica por barrio.

Uso:
    python scripts/test_idescat_extractor.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.idescat import IDESCATExtractor
from src.extraction.base import logger

def main():
    """Función principal para probar el extractor."""
    print("=" * 60)
    print("Test del IDESCATExtractor")
    print("=" * 60)
    
    # Crear instancia del extractor
    extractor = IDESCATExtractor(rate_limit_delay=1.0)
    
    print(f"\n✓ Extractor inicializado: {extractor.source_name}")
    print(f"  Base URL: {extractor.BASE_URL}")
    print(f"  API URL: {extractor.API_BASE_URL}")
    
    # Intentar extraer datos (período reducido para prueba)
    print("\n" + "=" * 60)
    print("Intentando extraer datos de renta (2020-2020)...")
    print("=" * 60)
    
    try:
        df, metadata = extractor.get_renta_by_barrio(year_start=2020, year_end=2020)
        
        print(f"\nResultado:")
        print(f"  Éxito: {metadata.get('success', False)}")
        print(f"  Estrategia usada: {metadata.get('strategy_used', 'N/A')}")
        
        if not df.empty:
            print(f"  Registros extraídos: {len(df)}")
            print(f"  Columnas: {list(df.columns)}")
            print(f"\nPrimeras filas:")
            print(df.head())
        else:
            print(f"  Registros extraídos: 0")
            print(f"  Nota: El extractor está implementado pero requiere")
            print(f"        investigación adicional para identificar el")
            print(f"        indicador específico de renta en la API de IDESCAT.")
            if "error" in metadata:
                print(f"  Error: {metadata['error']}")
            if "note" in metadata:
                print(f"  Nota: {metadata['note']}")
        
        print("\n" + "=" * 60)
        print("Test completado")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error durante la extracción: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

