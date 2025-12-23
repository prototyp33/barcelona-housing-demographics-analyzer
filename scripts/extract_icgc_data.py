#!/usr/bin/env python3
"""
Script para extraer datos de criminalidad del ICGC.

Este script intenta múltiples métodos para obtener datos:
1. Open Data BCN (si hay datasets de seguridad)
2. Scraping del visor ICGC (si está implementado)
3. Archivos CSV manuales (fallback)

Uso:
    python scripts/extract_icgc_data.py --anio-inicio 2020 --anio-fin 2024
"""

import argparse
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.icgc_extractor import ICGCExtractor


def main() -> int:
    """Ejecuta la extracción de datos del ICGC."""
    parser = argparse.ArgumentParser(
        description="Extrae datos de criminalidad del ICGC para Barcelona"
    )
    parser.add_argument(
        "--anio-inicio",
        type=int,
        default=2020,
        help="Año inicial del rango (default: 2020)",
    )
    parser.add_argument(
        "--anio-fin",
        type=int,
        default=2024,
        help="Año final del rango (default: 2024)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directorio donde guardar los datos (default: data/raw/icgc)",
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir or Path("data/raw/icgc")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== Extracción de datos ICGC ===")
    print(f"Rango de años: {args.anio_inicio}-{args.anio_fin}")
    print(f"Directorio de salida: {output_dir}")
    print()
    
    extractor = ICGCExtractor(output_dir=output_dir)
    
    try:
        df, metadata = extractor.extract_criminalidad_barrio(
            anio_inicio=args.anio_inicio,
            anio_fin=args.anio_fin,
        )
        
        if df is not None and not df.empty:
            print(f"✓ Datos extraídos exitosamente")
            print(f"  - Registros: {len(df)}")
            print(f"  - Método usado: {metadata.get('method_used', 'desconocido')}")
            print(f"  - Archivos descargados: {len(metadata.get('files_downloaded', []))}")
            
            if metadata.get("files_found"):
                print(f"  - Archivos CSV encontrados: {len(metadata['files_found'])}")
            
            return 0
        else:
            print("⚠️  No se pudieron obtener datos de criminalidad")
            print()
            print("Opciones:")
            print("1. Preparar archivos CSV manualmente en data/raw/icgc/")
            print("2. Verificar si hay datasets de seguridad en Open Data BCN")
            print("3. Contactar con ICGC/Mossos para acceso a datos oficiales")
            print()
            print("Formato esperado para CSV manual:")
            print("  - Columnas: barrio, anio, trimestre, robos, hurtos, agresiones")
            print("  - Nombre: icgc_criminalidad_*.csv")
            
            return 1
            
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

