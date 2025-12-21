#!/usr/bin/env python3
"""
Procesa todas las páginas de datos de Comet AI desde un archivo de texto completo.

Este script puede procesar el texto completo pegado directamente desde Comet AI,
que incluye múltiples páginas con diferentes formatos.

Uso:
    python3 process_all_comet_pages.py --input datos_completos.txt --output idealista_gracia.csv
"""

from __future__ import annotations

import argparse
import logging
import re
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


def parse_property_from_text(property_text: str) -> Optional[Dict[str, Any]]:
    """
    Parsea una propiedad desde texto (soporta múltiples formatos).
    
    Args:
        property_text: Texto de una propiedad
        
    Returns:
        Diccionario con los datos o None si hay error
    """
    data: Dict[str, Any] = {}
    
    try:
        # Precio (formato: "490.000 €" o "490000 €")
        precio_match = re.search(r'(?:Precio|Price):\s*([\d.]+)\s*€', property_text, re.IGNORECASE)
        if precio_match:
            precio_str = precio_match.group(1).replace('.', '')
            try:
                data['precio'] = int(precio_str)
            except ValueError:
                data['precio'] = None
        else:
            data['precio'] = None
        
        # Superficie (formato: "80.0 m²" o "80 m²" o "80,0 m²")
        superficie_match = re.search(r'(?:Superficie|Size|Superficie):\s*([\d.,]+)\s*m²', property_text, re.IGNORECASE)
        if superficie_match:
            superficie_str = superficie_match.group(1).replace(',', '.')
            try:
                data['superficie_m2'] = float(superficie_str)
            except ValueError:
                data['superficie_m2'] = None
        else:
            data['superficie_m2'] = None
        
        # Habitaciones
        habitaciones_match = re.search(r'(?:Habitaciones|Rooms|Habitaciones):\s*(\d+|null|n/d)', property_text, re.IGNORECASE)
        if habitaciones_match:
            habitaciones_str = habitaciones_match.group(1).lower()
            if habitaciones_str in ('null', 'n/d', 'n/d'):
                data['habitaciones'] = None
            else:
                try:
                    data['habitaciones'] = int(habitaciones_str)
                except ValueError:
                    data['habitaciones'] = None
        else:
            data['habitaciones'] = None
        
        # Baños
        banos_match = re.search(r'(?:Baños|Bathrooms|Baños):\s*(\d+|null|n/d)', property_text, re.IGNORECASE)
        if banos_match:
            banos_str = banos_match.group(1).lower()
            if banos_str in ('null', 'n/d', 'n/d'):
                data['banos'] = None
            else:
                try:
                    data['banos'] = int(banos_str)
                except ValueError:
                    data['banos'] = None
        else:
            data['banos'] = None
        
        # Localidad
        localidad_match = re.search(r'(?:Localidad|Location|Localidad):\s*(.+?)(?=\n(?:Link|Descripción|Detalles)|$)', property_text, re.DOTALL | re.IGNORECASE)
        if localidad_match:
            localidad = localidad_match.group(1).strip()
            # Limpiar markdown links
            localidad = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', localidad)
            data['localidad'] = localidad
        else:
            data['localidad'] = None
        
        # Link
        link_match = re.search(r'(?:Link|URL):\s*\[([^\]]+)\]\(([^\)]+)\)', property_text, re.IGNORECASE)
        if link_match:
            data['link'] = link_match.group(2)
        else:
            # Intentar sin formato markdown
            link_match = re.search(r'(?:Link|URL):\s*(https?://[^\s\n]+)', property_text, re.IGNORECASE)
            if link_match:
                data['link'] = link_match.group(1)
            else:
                data['link'] = None
        
        # Descripción
        descripcion_match = re.search(r'(?:Descripción|Description|Descripcion):\s*(.+?)(?=\n(?:Detalles|Details)|$)', property_text, re.DOTALL | re.IGNORECASE)
        if descripcion_match:
            descripcion = descripcion_match.group(1).strip()
            descripcion = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', descripcion)
            # Limpiar funciones de Python si existen
            descripcion = re.sub(r'\[functions\.execute_python:\d+\]', '', descripcion)
            data['descripcion'] = descripcion
        else:
            data['descripcion'] = None
        
        # Detalles
        detalles_match = re.search(r'(?:Detalles|Details):\s*(.+?)(?=\n(?:---|Propiedad|$))', property_text, re.DOTALL | re.IGNORECASE)
        if detalles_match:
            detalles = detalles_match.group(1).strip()
            if detalles.lower() in ('null', 'n/d', 'n/d'):
                data['detalles'] = None
            else:
                data['detalles'] = detalles
        else:
            data['detalles'] = None
        
        # Validar campos críticos
        if not data.get('precio') or not data.get('link'):
            return None
        
        return data
        
    except Exception as e:
        logger.debug(f"Error parseando propiedad: {e}")
        return None


def extract_all_properties(content: str) -> List[Dict[str, Any]]:
    """
    Extrae todas las propiedades del contenido completo.
    
    Soporta múltiples formatos:
    - ## Propiedad X (formato markdown)
    - Propiedad X (formato simple)
    
    Args:
        content: Contenido completo del texto
        
    Returns:
        Lista de diccionarios con propiedades
    """
    all_properties = []
    
    # Dividir por separadores de propiedad (soporta múltiples formatos)
    # Formato 1: ## Propiedad X
    # Formato 2: Propiedad X (sin ##)
    property_sections = re.split(r'(?:##\s*)?Propiedad\s+\d+', content, flags=re.IGNORECASE)
    
    # La primera sección suele ser el encabezado, omitirla
    for i, section in enumerate(property_sections[1:], 1):
        if not section.strip():
            continue
        
        prop_data = parse_property_from_text(section)
        if prop_data:
            all_properties.append(prop_data)
        else:
            logger.debug(f"No se pudo parsear propiedad {i}")
    
    return all_properties


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Procesa todas las páginas de Comet AI")
    parser.add_argument("--input", type=str, required=True, help="Archivo de texto con todas las páginas")
    parser.add_argument("--output", type=str, default=None, help="Archivo CSV de salida")
    parser.add_argument("--validate-only", action="store_true", help="Solo validar, no guardar")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"❌ Archivo no encontrado: {input_path}")
        return 1
    
    logger.info(f"Leyendo archivo: {input_path}")
    content = input_path.read_text(encoding='utf-8')
    
    # Extraer todas las propiedades
    all_properties = extract_all_properties(content)
    
    if not all_properties:
        logger.error("❌ No se encontraron propiedades válidas")
        return 1
    
    df = pd.DataFrame(all_properties)
    logger.info(f"✅ Total propiedades parseadas: {len(df)}")
    
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
    df_final = df[[col for col in columns_order if col in df.columns]]
    df_final.to_csv(output_path, index=False, encoding="utf-8")
    
    logger.info("")
    logger.info(f"📄 CSV guardado: {output_path}")
    logger.info(f"   Propiedades: {len(df_final)}")
    logger.info(f"   Columnas: {', '.join(df_final.columns)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

