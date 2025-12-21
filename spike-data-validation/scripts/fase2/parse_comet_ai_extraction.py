#!/usr/bin/env python3
"""
Parsea datos extraídos de Comet AI (formato markdown) y los convierte a CSV estructurado.

Este script procesa el markdown generado por Comet AI y lo convierte al formato
esperado por el pipeline de matching con Catastro.

Uso:
    python3 spike-data-validation/scripts/fase2/parse_comet_ai_extraction.py \
        --input datos_comet_ai.md \
        --output idealista_gracia_comet.csv
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


def parse_markdown_property(property_text: str) -> Optional[Dict[str, Any]]:
    """
    Parsea el texto de una propiedad del markdown.
    
    Args:
        property_text: Texto de una propiedad en formato markdown
        
    Returns:
        Diccionario con los datos de la propiedad o None si hay error
    """
    data: Dict[str, Any] = {}
    
    try:
        # Precio (soporta: - **Precio:** o Precio:)
        # Formato 1: - **Precio:** 490.000 € (páginas 1-5)
        # Formato 2: Precio: 490.000 € (páginas 6-10)
        precio_match = re.search(r'- \*\*Precio:\*\*\s*([\d.]+)\s*€', property_text, re.IGNORECASE)
        if not precio_match:
            # Intentar formato 2 (sin - **)
            precio_match = re.search(r'^Precio:\s*([\d.]+)\s*€', property_text, re.IGNORECASE | re.MULTILINE)
        if not precio_match:
            # Intentar sin el símbolo € al final
            precio_match = re.search(r'- \*\*Precio:\*\*\s*([\d.]+)', property_text, re.IGNORECASE)
        if not precio_match:
            precio_match = re.search(r'^Precio:\s*([\d.]+)', property_text, re.IGNORECASE | re.MULTILINE)
        if precio_match:
            precio_str = precio_match.group(1).replace('.', '')
            try:
                data['precio'] = int(precio_str)
            except ValueError:
                logger.warning(f"No se pudo convertir precio: {precio_match.group(1)}")
                data['precio'] = None
        else:
            data['precio'] = None
        
        # Superficie (puede tener punto o coma decimal, con o sin m²)
        superficie_match = re.search(r'- \*\*Superficie:\*\*\s*([\d.,]+)\s*m²', property_text, re.IGNORECASE)
        if not superficie_match:
            superficie_match = re.search(r'^Superficie:\s*([\d.,]+)\s*m²', property_text, re.IGNORECASE | re.MULTILINE)
        if superficie_match:
            superficie_str = superficie_match.group(1).replace(',', '.')
            try:
                data['superficie_m2'] = float(superficie_str)
            except ValueError:
                logger.warning(f"No se pudo convertir superficie: {superficie_match.group(1)}")
                data['superficie_m2'] = None
        else:
            data['superficie_m2'] = None
        
        # Habitaciones (soporta null, n/d, y números)
        habitaciones_match = re.search(r'- \*\*Habitaciones:\*\*\s*(\d+|null|n/d)', property_text, re.IGNORECASE)
        if not habitaciones_match:
            habitaciones_match = re.search(r'^Habitaciones:\s*(\d+|null|n/d)', property_text, re.IGNORECASE | re.MULTILINE)
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
        
        # Baños (soporta null, n/d, y números)
        banos_match = re.search(r'- \*\*Baños:\*\*\s*(\d+|null|n/d)', property_text, re.IGNORECASE)
        if not banos_match:
            banos_match = re.search(r'^Baños:\s*(\d+|null|n/d)', property_text, re.IGNORECASE | re.MULTILINE)
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
        
        # Localidad (soporta ambos formatos)
        # Buscar hasta el siguiente campo o fin de bloque
        localidad_match = re.search(r'- \*\*Localidad:\*\*\s*(.+?)(?=\n- \*\*|^Localidad:|$)', property_text, re.DOTALL | re.IGNORECASE)
        if not localidad_match:
            localidad_match = re.search(r'^Localidad:\s*(.+?)(?=\n(?:Link|Descripción|Detalles|Propiedad|$))', property_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if localidad_match:
            localidad = localidad_match.group(1).strip()
            # Limpiar markdown links si existen
            localidad = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', localidad)
            # Limpiar funciones de Python si existen
            localidad = re.sub(r'\[functions\.execute_python:\d+\]', '', localidad)
            # Limpiar texto adicional después del link
            localidad = re.sub(r'\[idealista\].*', '', localidad, flags=re.IGNORECASE)
            data['localidad'] = localidad.strip()
        else:
            data['localidad'] = None
        
        # Link (soporta ambos formatos: markdown link o URL directa)
        # Formato 1: - **Link:** [text](url)
        # Formato 2: Link: [text](url) o Link: url
        link_match = re.search(r'- \*\*Link:\*\*\s*\[([^\]]+)\]\(([^\)]+)\)', property_text, re.IGNORECASE)
        if not link_match:
            link_match = re.search(r'^Link:\s*\[([^\]]+)\]\(([^\)]+)\)', property_text, re.IGNORECASE | re.MULTILINE)
        if link_match:
            data['link'] = link_match.group(2)
        else:
            # Intentar sin formato markdown (URL directa)
            link_match = re.search(r'- \*\*Link:\*\*\s*(https?://[^\s\n\)]+)', property_text, re.IGNORECASE)
            if not link_match:
                link_match = re.search(r'^Link:\s*(https?://[^\s\n\)]+)', property_text, re.IGNORECASE | re.MULTILINE)
            if link_match:
                data['link'] = link_match.group(1)
            else:
                data['link'] = None
        
        # Descripción (soporta ambos formatos)
        # Nota: puede ser "Descripción" o "Descripcion" (sin tilde)
        descripcion_match = re.search(r'- \*\*Descripci[oó]n:\*\*\s*(.+?)(?=\n- \*\*Detalles:|^Detalles:|$)', property_text, re.DOTALL | re.IGNORECASE)
        if not descripcion_match:
            descripcion_match = re.search(r'^Descripci[oó]n:\s*(.+?)(?=\n(?:Detalles|Propiedad|$))', property_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if descripcion_match:
            descripcion = descripcion_match.group(1).strip()
            # Limpiar markdown links si existen
            descripcion = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', descripcion)
            # Limpiar funciones de Python si existen
            descripcion = re.sub(r'\[functions\.execute_python:\d+\]', '', descripcion)
            data['descripcion'] = descripcion.strip()
        else:
            data['descripcion'] = None
        
        # Detalles (soporta ambos formatos)
        detalles_match = re.search(r'- \*\*Detalles:\*\*\s*(.+?)(?=\n---|^Propiedad|$)', property_text, re.DOTALL | re.IGNORECASE)
        if not detalles_match:
            detalles_match = re.search(r'^Detalles:\s*(.+?)(?=\n(?:---|Propiedad|$))', property_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if detalles_match:
            detalles = detalles_match.group(1).strip()
            if detalles.lower() in ('null', 'n/d', 'n/d'):
                data['detalles'] = None
            else:
                # Limpiar funciones de Python si existen
                detalles = re.sub(r'\[functions\.execute_python:\d+\]', '', detalles)
                data['detalles'] = detalles.strip()
        else:
            data['detalles'] = None
        
        # Validar que tenga al menos precio y link
        if not data.get('precio') or not data.get('link'):
            logger.warning(f"Propiedad sin precio o link, omitiendo")
            return None
        
        return data
        
    except Exception as e:
        logger.error(f"Error parseando propiedad: {e}")
        return None


def parse_markdown_file(markdown_path: Path) -> pd.DataFrame:
    """
    Parsea un archivo markdown con extracciones de Comet AI.
    
    Soporta múltiples formatos:
    - Páginas 1-5: ## Propiedad X con campos - **Campo:**
    - Páginas 6-10: Propiedad X con campos Campo:
    
    Args:
        markdown_path: Ruta al archivo markdown
        
    Returns:
        DataFrame con las propiedades parseadas
    """
    logger.info(f"Leyendo archivo markdown: {markdown_path}")
    
    content = markdown_path.read_text(encoding='utf-8')
    
    all_properties = []
    
    # Buscar todas las propiedades usando ambos formatos
    # Formato 1: ## Propiedad X (páginas 1-5)
    pattern1 = r'## Propiedad \d+\s*\n(.*?)(?=\n## Propiedad \d+|\n## Resumen|\nPagina \d+|$)'
    matches1 = re.finditer(pattern1, content, re.DOTALL)
    
    for match in matches1:
        property_text = match.group(1).strip()
        if property_text:
            prop_data = parse_markdown_property(property_text)
            if prop_data:
                all_properties.append(prop_data)
    
    # Formato 2: Propiedad X (páginas 6-10, sin ##)
    # Encontrar el inicio de "Pagina 6" y procesar desde ahí
    pagina6_start = content.find('Pagina 6')
    if pagina6_start != -1:
        pagina6_10_content = content[pagina6_start:]
        
        # Dividir por 'Propiedad X' (sin ##) - más confiable que regex con lookahead
        propiedades = re.split(r'\nPropiedad \d+\s*\n', pagina6_10_content)
        
        # La primera es el encabezado 'Pagina 6', las siguientes son las propiedades
        for prop_text in propiedades[1:]:
            prop_text = prop_text.strip()
            # Filtrar capturas muy cortas (menos de 50 caracteres probablemente son errores)
            if prop_text and len(prop_text) > 50:
                # Limpiar hasta la siguiente propiedad o página si está incluida
                # Buscar el final de la propiedad (antes de la siguiente o de "Pagina X")
                prop_text = re.split(r'\n\nPropiedad \d+|\n\nPagina \d+|\n1\. \[https', prop_text)[0].strip()
                
                if prop_text and len(prop_text) > 50:
                    prop_data = parse_markdown_property(prop_text)
                    if prop_data:
                        all_properties.append(prop_data)
    
    if not all_properties:
        logger.error("No se encontraron propiedades válidas en el archivo")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_properties)
    logger.info(f"✅ Parseadas {len(df)} propiedades válidas")
    
    return df


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Valida los datos extraídos.
    
    Args:
        df: DataFrame con propiedades
        
    Returns:
        Diccionario con métricas de validación
    """
    validation = {
        'total_properties': len(df),
        'with_price': df['precio'].notna().sum(),
        'with_superficie': df['superficie_m2'].notna().sum(),
        'with_habitaciones': df['habitaciones'].notna().sum(),
        'with_banos': df['banos'].notna().sum(),
        'with_localidad': df['localidad'].notna().sum(),
        'with_link': df['link'].notna().sum(),
        'with_descripcion': df['descripcion'].notna().sum(),
        'duplicate_links': df['link'].duplicated().sum(),
    }
    
    # Estadísticas de precios
    if df['precio'].notna().any():
        prices = df['precio'].dropna()
        validation['price_stats'] = {
            'mean': float(prices.mean()),
            'median': float(prices.median()),
            'min': int(prices.min()),
            'max': int(prices.max()),
        }
    
    # Estadísticas de superficie
    if df['superficie_m2'].notna().any():
        superficie = df['superficie_m2'].dropna()
        validation['superficie_stats'] = {
            'mean': float(superficie.mean()),
            'median': float(superficie.median()),
            'min': float(superficie.min()),
            'max': float(superficie.max()),
        }
    
    return validation


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Parsea datos de Comet AI a CSV")
    parser.add_argument("--input", type=str, required=True, help="Archivo markdown de entrada")
    parser.add_argument("--output", type=str, default=None, help="Archivo CSV de salida")
    parser.add_argument("--validate-only", action="store_true", help="Solo validar, no guardar CSV")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"❌ Archivo no encontrado: {input_path}")
        return 1
    
    # Parsear markdown
    df = parse_markdown_file(input_path)
    
    if df.empty:
        logger.error("❌ No se pudieron parsear propiedades")
        return 1
    
    # Validar datos
    validation = validate_data(df)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("VALIDACIÓN DE DATOS")
    logger.info("=" * 70)
    logger.info(f"Total propiedades: {validation['total_properties']}")
    logger.info(f"Con precio: {validation['with_price']} ({validation['with_price']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Con superficie: {validation['with_superficie']} ({validation['with_superficie']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Con habitaciones: {validation['with_habitaciones']} ({validation['with_habitaciones']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Con baños: {validation['with_banos']} ({validation['with_banos']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Con localidad: {validation['with_localidad']} ({validation['with_localidad']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Con link: {validation['with_link']} ({validation['with_link']/validation['total_properties']*100:.1f}%)")
    logger.info(f"Links duplicados: {validation['duplicate_links']}")
    
    if 'price_stats' in validation:
        logger.info("")
        logger.info("📊 Estadísticas de precios:")
        logger.info(f"   Media: {validation['price_stats']['mean']:,.0f} €")
        logger.info(f"   Mediana: {validation['price_stats']['median']:,.0f} €")
        logger.info(f"   Min: {validation['price_stats']['min']:,} €")
        logger.info(f"   Max: {validation['price_stats']['max']:,} €")
    
    if 'superficie_stats' in validation:
        logger.info("")
        logger.info("📊 Estadísticas de superficie:")
        logger.info(f"   Media: {validation['superficie_stats']['mean']:.1f} m²")
        logger.info(f"   Mediana: {validation['superficie_stats']['median']:.1f} m²")
        logger.info(f"   Min: {validation['superficie_stats']['min']:.1f} m²")
        logger.info(f"   Max: {validation['superficie_stats']['max']:.1f} m²")
    
    if args.validate_only:
        logger.info("")
        logger.info("✅ Validación completada (--validate-only)")
        return 0
    
    # Guardar CSV
    output_path = Path(args.output) if args.output else Path("spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ordenar columnas según formato esperado
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

