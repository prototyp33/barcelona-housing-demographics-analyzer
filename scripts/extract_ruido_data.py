#!/usr/bin/env python3
"""
Script para extraer datos de contaminación acústica (ruido) de Open Data BCN.

Este script intenta múltiples métodos para obtener datos:
1. Datasets CSV agregados por barrio (preferido)
2. Mapas ráster del Mapa Estratégico de Ruido
3. Datos de sensores de la red de monitorización
4. Archivos CSV manuales (fallback)

Uso:
    python scripts/extract_ruido_data.py --anio 2022
"""

import argparse
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.ruido_extractor import RuidoExtractor


def main() -> int:
    """Ejecuta la extracción de datos de ruido."""
    parser = argparse.ArgumentParser(
        description="Extrae datos de contaminación acústica para Barcelona"
    )
    parser.add_argument(
        "--anio",
        type=int,
        default=2022,
        help="Año de los datos (default: 2022, último MER disponible)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio donde guardar los datos (default: data/raw/ruido)",
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir or Path("data/raw/ruido")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Extracción de datos de ruido ===")
    print(f"Año: {args.anio}")
    print(f"Directorio de salida: {output_dir}")
    print()
    
    extractor = RuidoExtractor(output_dir=output_dir)
    
    try:
        # Intentar extraer datos agregados por barrio (método preferido)
        df, metadata = extractor.extract_ruido_barrio(anio=args.anio)
        
        if df is not None and not df.empty:
            print(f"✓ Datos extraídos exitosamente")
            print(f"  - Registros: {len(df)}")
            print(f"  - Método usado: {metadata.get('method_used', 'desconocido')}")
            print(f"  - Archivos descargados: {len(metadata.get('files_downloaded', []))}")
            
            if metadata.get("files_found"):
                print(f"  - Archivos CSV encontrados: {len(metadata['files_found'])}")
            
            return 0
        else:
            print("⚠️  No se pudieron obtener datos de ruido agregados")
            print()
            print("Intentando extraer mapas ráster...")
            
            # Intentar extraer mapas ráster
            raster_path, raster_metadata = extractor.extract_mapas_ruido(anio=args.anio)
            
            if raster_path and raster_path.exists():
                print(f"✓ Mapa ráster descargado: {raster_path}")
                print("  Nota: El procesamiento de rásteres requiere rasterio y geopandas")
                return 0
            else:
                print("⚠️  No se pudieron obtener datos de ruido por ningún método")
                print()
                print("Opciones:")
                print("1. Preparar archivos CSV manualmente en data/raw/ruido/")
                print("2. Verificar si hay datasets de ruido en Open Data BCN")
                print("3. Descargar mapas ráster manualmente desde Open Data BCN")
                print()
                print("Formato esperado para CSV manual:")
                print("  - Columnas: barrio, anio, nivel_lden, nivel_ld, nivel_ln")
                print("  - Nombre: ruido_*.csv")
                
                return 1
            
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

