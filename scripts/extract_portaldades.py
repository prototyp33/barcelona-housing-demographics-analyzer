#!/usr/bin/env python3
"""
Script para extraer datos del Portal de Dades de Barcelona (Habitatge).

Este script usa scraping del portal y descarga
indicadores del "Habitatge" usando el Client ID.

Uso:
    
    # Extraer solo IDs (sin descargar)
    python scripts/extract_portaldades.py --scrape-only
    
    # Extraer IDs con indicadores
    python scripts/extract_portaldades.py
    
    # Ajustar número de páginas ej:
    python scripts/extract_portaldades.py --max-pages 3
"""

import argparse
import logging
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import PortalDadesExtractor, setup_logging


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Extrae indicadores del Portal de Dades de Barcelona (tema: Habitatge)"
    )
    
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Solo extraer IDs sin descargar archivos"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Número máximo de páginas a recorrer (default: todas)"
    )
    
    parser.add_argument(
        "--formato",
        choices=["CSV", "Excel"],
        default="CSV",
        help="Formato de descarga (default: CSV)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio donde guardar los datos (default: data/raw/)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Modo verbose (más información de logging)"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_to_file=True, log_level=log_level)
    
    # Preparar directorio de salida
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear extractor
    extractor = PortalDadesExtractor(output_dir=output_dir)
    
    print("\n" + "="*60)
    print("Portal de Dades - Extracción de Indicadores Habitatge")
    print("="*60)
    
    if args.scrape_only:
        print("Modo: Solo scraping (no se descargarán archivos)\n")
    else:
        print(f"Modo: Scraping + Descarga (formato: {args.formato})\n")
    
    try:
        # Extraer y opcionalmente descargar
        indicadores, archivos = extractor.extraer_y_descargar_habitatge(
            descargar=not args.scrape_only,
            formato=args.formato,
            max_pages=args.max_pages
        )
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("Resumen")
        print("="*60)
        print(f"Indicadores encontrados: {len(indicadores)}")
        
        if not args.scrape_only:
            descargados = len([p for p in archivos.values() if p is not None])
            fallidos = len([p for p in archivos.values() if p is None])
            print(f"Archivos descargados: {descargados}")
            if fallidos > 0:
                print(f"Archivos fallidos: {fallidos}")
        
        if indicadores:
            print(f"\nPrimeros 5 indicadores:")
            for i, indicador in enumerate(indicadores[:5], 1):
                nombre = indicador.get("nombre", "")
                id_ind = indicador.get("id_indicador", "")
                print(f"  {i}. {nombre[:60]}... (ID: {id_ind})")
            if len(indicadores) > 5:
                print(f"  ... y {len(indicadores) - 5} más")
        
        print("\n" + "="*60)
        return 0
        
    except KeyboardInterrupt:
        print("\n\nExtracción cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"\n\nError durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

