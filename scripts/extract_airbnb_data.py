#!/usr/bin/env python3
"""
Script para extraer datos de Inside Airbnb para Barcelona.

Este script descarga los datos más recientes de Inside Airbnb y los guarda
en data/raw/airbnb/ para su procesamiento posterior.

Fuente: http://insideairbnb.com/get-the-data.html
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.extract_priority_sources import InsideAirbnbExtractor


def main() -> int:
    """Extrae datos de Inside Airbnb para Barcelona."""
    print("=" * 80)
    print("EXTRACCIÓN DE DATOS DE INSIDE AIRBNB PARA BARCELONA")
    print("=" * 80)
    
    # Directorio de salida
    output_dir = project_root / "data" / "raw" / "airbnb"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Directorio de salida: {output_dir}")
    
    # Crear extractor
    extractor = InsideAirbnbExtractor(output_dir=output_dir)
    
    # Extraer datos (solo listings por ahora, calendar y reviews son opcionales)
    print("\n🔍 Buscando URLs de datos de Barcelona...")
    results, metadata = extractor.extract_airbnb_data(
        file_types=["listings", "calendar", "reviews"]
    )
    
    # Mostrar resultados
    print("\n" + "=" * 80)
    print("RESUMEN DE EXTRACCIÓN")
    print("=" * 80)
    
    if metadata.get("success", False):
        print("✅ Extracción completada exitosamente")
        print(f"\nArchivos descargados: {len(metadata.get('files_downloaded', []))}")
        for file_type in metadata.get("files_downloaded", []):
            records = metadata.get(f"{file_type}_records", 0)
            columns = metadata.get(f"{file_type}_columns", [])
            print(f"  - {file_type}: {records:,} registros, {len(columns)} columnas")
        
        if metadata.get("files_failed"):
            print(f"\n⚠️  Archivos fallidos: {', '.join(metadata['files_failed'])}")
        
        print(f"\n📁 Datos guardados en: {output_dir}")
        return 0
    else:
        print("❌ Error en la extracción")
        if "error" in metadata:
            print(f"   Error: {metadata['error']}")
        if metadata.get("files_failed"):
            print(f"   Archivos fallidos: {', '.join(metadata['files_failed'])}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

