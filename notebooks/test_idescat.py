#!/usr/bin/env python3
"""
Script de prueba para verificar que el extractor de IDESCAT funciona correctamente.

Ejecutar:
    python notebooks/test_idescat.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_priority_sources import IDESCATExtractor

def main():
    print("=" * 60)
    print("TEST: Extractor de IDESCAT")
    print("=" * 60)
    print()
    
    try:
        # Crear extractor
        print("1. Creando extractor de IDESCAT...")
        extractor = IDESCATExtractor(output_dir=Path("data/raw"))
        print("   ✓ Extractor creado")
        print()
        
        # Intentar extraer datos para el año más reciente
        print("2. Extrayendo datos demográficos de Barcelona (año 2023)...")
        df, metadata = extractor.extract_demografia_barrios(year=2023, lang="es")
        print()
        
        # Verificar resultados
        if metadata.get("success"):
            print("   ✅ ÉXITO: Datos extraídos correctamente")
            print()
            print("   📊 Metadata:")
            print(f"      - Año: {metadata.get('year')}")
            print(f"      - Fuente: {metadata.get('source')}")
            print(f"      - Endpoint: {metadata.get('endpoint')}")
            if 'raw_filepath' in metadata:
                print(f"      - Archivo guardado: {metadata['raw_filepath']}")
            print()
            
            if df is not None and not df.empty:
                print(f"   📈 DataFrame: {len(df)} filas, {len(df.columns)} columnas")
                print(f"      Columnas: {list(df.columns)[:5]}...")
                print()
                print("   Primeras filas:")
                print(df.head())
            else:
                print("   ⚠️  DataFrame vacío (pero datos JSON guardados)")
                print("      Revisa el archivo JSON para ver la estructura de datos")
            
            print()
            print("=" * 60)
            print("✅ TEST COMPLETADO CON ÉXITO")
            print("=" * 60)
            return 0
        else:
            print("   ❌ ERROR: No se pudieron extraer datos")
            print(f"      Error: {metadata.get('error', 'Desconocido')}")
            print()
            print("=" * 60)
            print("❌ TEST FALLIDO")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print()
        print("   ❌ EXCEPCIÓN durante la extracción:")
        print(f"      {type(e).__name__}: {e}")
        print()
        import traceback
        print("   Traceback completo:")
        traceback.print_exc()
        print()
        print("=" * 60)
        print("❌ TEST FALLIDO")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

