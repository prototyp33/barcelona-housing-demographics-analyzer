#!/usr/bin/env python3
"""
Script de ejemplo para extraer datos de todas las fuentes.

Uso:
    python scripts/extract_data.py --year-start 2015 --year-end 2025
    python scripts/extract_data.py --sources opendatabcn ine
    python scripts/extract_data.py --help
"""

import argparse
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_extraction import extract_all_sources


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Extrae datos de fuentes públicas para Barcelona Housing Demographics Analyzer"
    )
    
    parser.add_argument(
        "--year-start",
        type=int,
        default=2015,
        help="Año inicial para la extracción (default: 2015)"
    )
    
    parser.add_argument(
        "--year-end",
        type=int,
        default=2025,
        help="Año final para la extracción (default: 2025)"
    )
    
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["ine", "opendatabcn", "idealista"],
        default=None,
        help="Fuentes específicas a extraer (default: todas)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Modo verbose (más información de logging)"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abortar si una fuente falla (default: continuar con otras fuentes)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio donde guardar los datos extraídos (default: data/raw/)"
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    import logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Validar años
    if args.year_start > args.year_end:
        print("Error: year-start debe ser menor o igual a year-end")
        sys.exit(1)
    
    if args.year_start < 2015:
        print("Warning: Algunos datos pueden no estar disponibles antes de 2015")
    
    # Validar y preparar directorio de salida
    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                print(f"Directorio de salida creado: {output_dir}")
            except Exception as e:
                print(f"Error creando directorio de salida {output_dir}: {e}")
                sys.exit(1)
        elif not output_dir.is_dir():
            print(f"Error: {output_dir} existe pero no es un directorio")
            sys.exit(1)
    
    # Ejecutar extracción
    print(f"\n{'='*60}")
    print(f"Extrayendo datos de {args.year_start} a {args.year_end}")
    if args.sources:
        print(f"Fuentes: {', '.join(args.sources)}")
    else:
        print("Fuentes: todas (ine, opendatabcn, idealista)")
    print(f"{'='*60}\n")
    
    try:
        results, metadata = extract_all_sources(
            year_start=args.year_start,
            year_end=args.year_end,
            sources=args.sources,
            continue_on_error=not args.fail_fast,
            output_dir=output_dir
        )
        
        # Mostrar resumen
        print(f"\n{'='*60}")
        print("Resumen de extracción:")
        print(f"{'='*60}")
        total_records = 0
        for source, df in results.items():
            records = len(df)
            total_records += records
            status = "✓" if records > 0 else "✗"
            print(f"{status} {source:30s} {records:>10,} registros")
        
        print(f"\nTotal: {total_records:,} registros extraídos")
        
        # Mostrar ubicación de archivos
        output_path = metadata.get("output_dir", "data/raw/")
        print(f"\nDatos guardados en: {output_path}")
        print(f"Logs guardados en: logs/")
        if metadata.get("summary_file"):
            print(f"Resumen guardado en: {metadata['summary_file']}")
        
        # Mostrar resumen de cobertura
        if metadata.get("coverage_by_source"):
            print(f"\n{'='*60}")
            print("Cobertura Temporal:")
            print(f"{'='*60}")
            for source, cov_meta in metadata["coverage_by_source"].items():
                if isinstance(cov_meta, dict):
                    if "coverage_percentage" in cov_meta:
                        coverage = cov_meta["coverage_percentage"]
                        if coverage < 100:
                            missing = cov_meta.get("missing_years", [])
                            print(f"⚠ {source:30s} {coverage:>5.1f}% - Faltan: {missing[:5]}{'...' if len(missing) > 5 else ''}")
                        else:
                            print(f"✓ {source:30s} {coverage:>5.1f}% - Completo")
                    elif "error" in cov_meta:
                        print(f"✗ {source:30s} Error: {cov_meta['error'][:50]}")
        
        # Mostrar fuentes exitosas y fallidas
        if metadata.get("sources_success") or metadata.get("sources_failed"):
            print(f"\n{'='*60}")
            print("Estado de Fuentes:")
            print(f"{'='*60}")
            if metadata.get("sources_success"):
                print(f"✓ Exitosas: {', '.join(metadata['sources_success'])}")
            if metadata.get("sources_failed"):
                print(f"✗ Fallidas: {', '.join(metadata['sources_failed'])}")
        
        print(f"{'='*60}\n")
        
        # Retornar código de error si hay fuentes fallidas
        if metadata.get("sources_failed") and not args.fail_fast:
            return 1 if total_records == 0 else 0
        
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

