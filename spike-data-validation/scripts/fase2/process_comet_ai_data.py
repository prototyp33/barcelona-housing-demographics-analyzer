#!/usr/bin/env python3
"""
Procesa datos extraídos de Comet AI directamente desde texto o archivo.

Este script puede procesar datos de Comet AI desde:
1. Un archivo markdown con todas las páginas
2. Texto pegado directamente (stdin)
3. Múltiples archivos markdown

Uso:
    # Desde archivo
    python3 process_comet_ai_data.py --input datos.md
    
    # Desde stdin (pegar texto)
    python3 process_comet_ai_data.py --input - < datos.txt
    
    # Múltiples archivos
    python3 process_comet_ai_data.py --input pagina1.md pagina2.md pagina3.md
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_property_section(property_text: str) -> Optional[Dict[str, Any]]:
    """
    Parsea una sección de propiedad del markdown.
    
    Args:
        property_text: Texto de una propiedad
        
    Returns:
        Diccionario con los datos o None si hay error
    """
    data: Dict[str, Any] = {}
    
    try:
        # Precio (formato: "490.000 €" o "490000 €")
        precio_match = re.search(r'\*\*Precio:\*\*\s*([\d.]+)\s*€', property_text)
        if precio_match:
            precio_str = precio_match.group(1).replace('.', '')
            try:
                data['precio'] = int(precio_str)
            except ValueError:
                data['precio'] = None
        else:
            data['precio'] = None
        
        # Superficie (formato: "80.0 m²" o "80,0 m²")
        superficie_match = re.search(r'\*\*Superficie:\*\*\s*([\d.,]+)\s*m²', property_text)
        if superficie_match:
            superficie_str = superficie_match.group(1).replace(',', '.')
            try:
                data['superficie_m2'] = float(superficie_str)
            except ValueError:
                data['superficie_m2'] = None
        else:
            data['superficie_m2'] = None
        
        # Habitaciones
        habitaciones_match = re.search(r'\*\*Habitaciones:\*\*\s*(\d+|null)', property_text)
        if habitaciones_match:
            habitaciones_str = habitaciones_match.group(1)
            data['habitaciones'] = None if habitaciones_str.lower() == 'null' else int(habitaciones_str)
        else:
            data['habitaciones'] = None
        
        # Baños
        banos_match = re.search(r'\*\*Baños:\*\*\s*(\d+|null)', property_text)
        if banos_match:
            banos_str = banos_match.group(1)
            data['banos'] = None if banos_str.lower() == 'null' else int(banos_str)
        else:
            data['banos'] = None
        
        # Localidad
        localidad_match = re.search(r'\*\*Localidad:\*\*\s*(.+?)(?=\n\*\*|$)', property_text, re.DOTALL)
        if localidad_match:
            localidad = localidad_match.group(1).strip()
            localidad = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', localidad)
            data['localidad'] = localidad
        else:
            data['localidad'] = None
        
        # Link
        link_match = re.search(r'\*\*Link:\*\*\s*\[([^\]]+)\]\(([^\)]+)\)', property_text)
        if link_match:
            data['link'] = link_match.group(2)
        else:
            link_match = re.search(r'\*\*Link:\*\*\s*(https?://[^\s]+)', property_text)
            data['link'] = link_match.group(1) if link_match else None
        
        # Descripción
        descripcion_match = re.search(r'\*\*Descripción:\*\*\s*(.+?)(?=\n\*\*|$)', property_text, re.DOTALL)
        if descripcion_match:
            descripcion = descripcion_match.group(1).strip()
            descripcion = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', descripcion)
            data['descripcion'] = descripcion
        else:
            data['descripcion'] = None
        
        # Detalles
        detalles_match = re.search(r'\*\*Detalles:\*\*\s*(.+?)(?=\n---|$)', property_text, re.DOTALL)
        if detalles_match:
            detalles = detalles_match.group(1).strip()
            data['detalles'] = None if detalles.lower() == 'null' else detalles
        else:
            data['detalles'] = None
        
        # Validar campos críticos
        if not data.get('precio') or not data.get('link'):
            return None
        
        return data
        
    except Exception as e:
        logger.debug(f"Error parseando propiedad: {e}")
        return None


def parse_markdown_content(content: str, page_num: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Parsea contenido markdown y extrae propiedades.
    
    Args:
        content: Contenido markdown
        page_num: Número de página (opcional)
        
    Returns:
        Lista de diccionarios con propiedades
    """
    # Dividir por separadores de propiedad
    property_sections = re.split(r'## Propiedad \d+', content)
    
    properties = []
    for i, section in enumerate(property_sections[1:], 1):
        prop_data = parse_property_section(section)
        if prop_data:
            if page_num is not None:
                prop_data['page'] = page_num
            properties.append(prop_data)
    
    return properties


def process_input_files(input_paths: List[str]) -> pd.DataFrame:
    """
    Procesa uno o múltiples archivos de entrada.
    
    Args:
        input_paths: Lista de rutas a archivos (o ["-"] para stdin)
        
    Returns:
        DataFrame con todas las propiedades
    """
    all_properties = []
    
    for input_path_str in input_paths:
        if input_path_str == "-":
            # Leer desde stdin
            logger.info("Leyendo desde stdin...")
            content = sys.stdin.read()
            properties = parse_markdown_content(content)
            all_properties.extend(properties)
        else:
            input_path = Path(input_path_str)
            if not input_path.exists():
                logger.warning(f"Archivo no encontrado: {input_path}, omitiendo")
                continue
            
            logger.info(f"Procesando archivo: {input_path}")
            content = input_path.read_text(encoding='utf-8')
            
            # Detectar si hay múltiples páginas
            page_markers = re.findall(r'# Extracción.*?Página (\d+)', content, re.IGNORECASE)
            
            if page_markers:
                # Dividir por páginas
                page_sections = re.split(r'# Extracción.*?Página \d+', content, flags=re.IGNORECASE)
                for i, page_content in enumerate(page_sections[1:], 1):
                    properties = parse_markdown_content(page_content, page_num=i)
                    all_properties.extend(properties)
            else:
                # Una sola página
                properties = parse_markdown_content(content, page_num=1)
                all_properties.extend(properties)
    
    if not all_properties:
        logger.error("No se encontraron propiedades válidas")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_properties)
    logger.info(f"✅ Total propiedades parseadas: {len(df)}")
    
    return df


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Procesa datos de Comet AI a CSV")
    parser.add_argument("--input", type=str, nargs="+", required=True, 
                       help="Archivo(s) markdown de entrada (usar '-' para stdin)")
    parser.add_argument("--output", type=str, default=None, help="Archivo CSV de salida")
    parser.add_argument("--validate-only", action="store_true", help="Solo validar, no guardar")
    args = parser.parse_args()
    
    # Procesar archivos
    df = process_input_files(args.input)
    
    if df.empty:
        logger.error("❌ No se pudieron procesar propiedades")
        return 1
    
    # Validar
    validation = {
        'total': len(df),
        'with_price': df['precio'].notna().sum(),
        'with_superficie': df['superficie_m2'].notna().sum(),
        'with_habitaciones': df['habitaciones'].notna().sum(),
        'with_banos': df['banos'].notna().sum(),
        'with_localidad': df['localidad'].notna().sum(),
        'with_link': df['link'].notna().sum(),
        'duplicate_links': df['link'].duplicated().sum(),
    }
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("VALIDACIÓN DE DATOS")
    logger.info("=" * 70)
    logger.info(f"Total propiedades: {validation['total']}")
    logger.info(f"Con precio: {validation['with_price']} ({validation['with_price']/validation['total']*100:.1f}%)")
    logger.info(f"Con superficie: {validation['with_superficie']} ({validation['with_superficie']/validation['total']*100:.1f}%)")
    logger.info(f"Con habitaciones: {validation['with_habitaciones']} ({validation['with_habitaciones']/validation['total']*100:.1f}%)")
    logger.info(f"Con baños: {validation['with_banos']} ({validation['with_banos']/validation['total']*100:.1f}%)")
    logger.info(f"Con localidad: {validation['with_localidad']} ({validation['with_localidad']/validation['total']*100:.1f}%)")
    logger.info(f"Con link: {validation['with_link']} ({validation['with_link']/validation['total']*100:.1f}%)")
    logger.info(f"Links duplicados: {validation['duplicate_links']}")
    
    if df['precio'].notna().any():
        prices = df['precio'].dropna()
        logger.info("")
        logger.info("📊 Estadísticas de precios:")
        logger.info(f"   Media: {prices.mean():,.0f} €")
        logger.info(f"   Mediana: {prices.median():,.0f} €")
        logger.info(f"   Min: {prices.min():,} €")
        logger.info(f"   Max: {prices.max():,} €")
    
    if df['superficie_m2'].notna().any():
        superficie = df['superficie_m2'].dropna()
        logger.info("")
        logger.info("📊 Estadísticas de superficie:")
        logger.info(f"   Media: {superficie.mean():.1f} m²")
        logger.info(f"   Mediana: {superficie.median():.1f} m²")
        logger.info(f"   Min: {superficie.min():.1f} m²")
        logger.info(f"   Max: {superficie.max():.1f} m²")
    
    if args.validate_only:
        logger.info("")
        logger.info("✅ Validación completada (--validate-only)")
        return 0
    
    # Guardar CSV
    output_path = Path(args.output) if args.output else Path("spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    columns_order = ['precio', 'superficie_m2', 'habitaciones', 'banos', 'localidad', 'link', 'descripcion', 'detalles']
    if 'page' in df.columns:
        columns_order.append('page')
    
    df_final = df[[col for col in columns_order if col in df.columns]]
    df_final.to_csv(output_path, index=False, encoding="utf-8")
    
    logger.info("")
    logger.info(f"📄 CSV guardado: {output_path}")
    logger.info(f"   Propiedades: {len(df_final)}")
    logger.info(f"   Columnas: {', '.join(df_final.columns)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

