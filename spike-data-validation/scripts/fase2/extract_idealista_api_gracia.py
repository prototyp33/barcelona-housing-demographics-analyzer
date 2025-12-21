#!/usr/bin/env python3
"""
Extracción de Idealista usando API oficial (Fase 2 - Issue #202).

Usa la API oficial de Idealista para extraer anuncios de venta en Gràcia.
Alternativas:
1. Cliente GitHub: https://github.com/yagueto/idealista-api
2. Extractor propio: src/extraction/idealista.py

Requisitos:
- Credenciales API: IDEALISTA_API_KEY y IDEALISTA_API_SECRET
- Obtener credenciales en: https://developers.idealista.com/

Uso:
    # Con variables de entorno
    export IDEALISTA_API_KEY=your_key
    export IDEALISTA_API_SECRET=your_secret
    python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py
    
    # O con argumentos
    python3 spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py \\
        --api-key YOUR_KEY --api-secret YOUR_SECRET
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Intentar importar cliente de GitHub primero
try:
    from idealista_api import Idealista, Search
    GITHUB_CLIENT_AVAILABLE = True
except ImportError:
    GITHUB_CLIENT_AVAILABLE = False

# Importar extractor propio como fallback
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
try:
    from src.extraction.idealista import IdealistaExtractor
    OWN_EXTRACTOR_AVAILABLE = True
except ImportError:
    OWN_EXTRACTOR_AVAILABLE = False

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Location IDs para Gràcia (necesitan ser descubiertos o configurados)
# Ver: scripts/build_idealista_location_ids.py para descubrir IDs
GRACIA_LOCATION_IDS = {
    # Estos son ejemplos, necesitan ser descubiertos usando la API
    # "0-EU-ES-08-019-001-000-028",  # Vallcarca
    # "0-EU-ES-08-019-001-000-029",  # el Coll
    # etc.
}

# Barcelona city ID (usado como fallback)
BARCELONA_CITY_ID = "0-EU-ES-08-019-001-000"


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def extract_with_github_client(
    api_key: str, api_secret: str, max_properties: int = 100
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Extrae datos usando el cliente de GitHub (yagueto/idealista-api).
    
    Args:
        api_key: API key de Idealista
        api_secret: API secret de Idealista
        max_properties: Máximo de propiedades a extraer
        
    Returns:
        Tupla con (DataFrame o None, metadata)
    """
    logger.info("Usando cliente GitHub: yagueto/idealista-api")
    
    metadata: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "method": "github_client",
        "success": False,
    }
    
    try:
        idealista = Idealista(api_key=api_key, api_secret=api_secret)
        
        # Buscar en Barcelona/Gràcia
        # Nota: Necesitamos el location_id correcto para Gràcia
        # Por ahora usamos Barcelona city y filtramos después
        
        all_properties: List[Dict[str, Any]] = []
        page = 1
        max_pages = (max_properties // 50) + 1
        
        while len(all_properties) < max_properties and page <= max_pages:
            logger.info("Buscando página %s...", page)
            
            request = Search(
                "es",
                location_id=BARCELONA_CITY_ID,
                property_type="homes",
                operation="sale",
                max_items=min(50, max_properties - len(all_properties)),
                num_page=page,
            )
            
            response = idealista.query(request)
            
            if not response or not response.element_list:
                logger.info("No hay más resultados")
                break
            
            logger.info("   Encontrados: %s propiedades", len(response.element_list))
            
            # Filtrar por Gràcia (usando neighborhood o district)
            for prop in response.element_list:
                neighborhood = prop.get("neighborhood", "").lower()
                district = prop.get("district", "").lower()
                
                # Filtrar por barrios de Gràcia
                gracia_keywords = ["gracia", "gràcia", "vallcarca", "coll", "salut"]
                if any(kw in neighborhood or kw in district for kw in gracia_keywords):
                    all_properties.append(prop)
            
            page += 1
            
            # Rate limiting
            if page <= max_pages:
                import time
                time.sleep(2)  # Delay entre páginas
        
        if all_properties:
            df = pd.DataFrame(all_properties)
            metadata["success"] = True
            metadata["num_properties"] = len(df)
            logger.info("✅ Extraídas %s propiedades de Gràcia", len(df))
            return df, metadata
        else:
            logger.warning("No se encontraron propiedades en Gràcia")
            metadata["error"] = "No properties found"
            return None, metadata
            
    except Exception as exc:
        logger.error("Error usando cliente GitHub: %s", exc)
        metadata["error"] = str(exc)
        return None, metadata


def extract_with_own_extractor(
    api_key: str, api_secret: str, max_properties: int = 100
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Extrae datos usando nuestro extractor propio.
    
    Args:
        api_key: API key de Idealista
        api_secret: API secret de Idealista
        max_properties: Máximo de propiedades a extraer
        
    Returns:
        Tupla con (DataFrame o None, metadata)
    """
    logger.info("Usando extractor propio: src/extraction/idealista.py")
    
    try:
        extractor = IdealistaExtractor(
            api_key=api_key,
            api_secret=api_secret,
            rate_limit_delay=3.0,
        )
        
        # Buscar propiedades en Barcelona (filtrar Gràcia después)
        df, metadata = extractor.search_properties(
            operation="sale",
            location=BARCELONA_CITY_ID,
            max_items=max_properties,
        )
        
        if df is not None and not df.empty:
            # Filtrar por Gràcia
            # Asumimos que hay campos 'neighborhood' o 'district'
            if "neighborhood" in df.columns:
                df_gracia = df[
                    df["neighborhood"].str.lower().str.contains("gracia|gràcia|vallcarca|coll|salut", na=False)
                ].copy()
            elif "district" in df.columns:
                df_gracia = df[
                    df["district"].str.lower().str.contains("gracia|gràcia", na=False)
                ].copy()
            else:
                logger.warning("No se encontraron campos para filtrar Gràcia")
                df_gracia = df.copy()
            
            logger.info("✅ Extraídas %s propiedades de Gràcia", len(df_gracia))
            return df_gracia, metadata
        else:
            logger.warning("No se encontraron propiedades")
            return None, metadata
            
    except Exception as exc:
        logger.error("Error usando extractor propio: %s", exc)
        return None, {"error": str(exc)}


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Extraer datos de Idealista API para Gràcia")
    parser.add_argument("--api-key", type=str, default=None, help="API key de Idealista")
    parser.add_argument("--api-secret", type=str, default=None, help="API secret de Idealista")
    parser.add_argument("--max-properties", type=int, default=100, help="Máximo propiedades a extraer")
    parser.add_argument("--output", type=str, default=None, help="Ruta de salida CSV")
    args = parser.parse_args()
    
    # Obtener credenciales
    api_key = args.api_key or os.getenv("IDEALISTA_API_KEY")
    api_secret = args.api_secret or os.getenv("IDEALISTA_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("❌ Credenciales API no encontradas")
        logger.error("")
        logger.error("Opciones:")
        logger.error("1. Configurar variables de entorno:")
        logger.error("   export IDEALISTA_API_KEY=your_key")
        logger.error("   export IDEALISTA_API_SECRET=your_secret")
        logger.error("")
        logger.error("2. O usar argumentos:")
        logger.error("   --api-key YOUR_KEY --api-secret YOUR_SECRET")
        logger.error("")
        logger.error("3. Obtener credenciales en: https://developers.idealista.com/")
        logger.error("")
        logger.error("4. Instalar cliente GitHub (opcional):")
        logger.error("   pip install git+https://github.com/yagueto/idealista-api.git")
        return 1
    
    logger.info("=" * 70)
    logger.info("EXTRACCIÓN IDEALISTA API - GRÀCIA")
    logger.info("=" * 70)
    logger.info("Método disponible:")
    logger.info("  - Cliente GitHub: %s", "✅ Disponible" if GITHUB_CLIENT_AVAILABLE else "❌ No instalado")
    logger.info("  - Extractor propio: %s", "✅ Disponible" if OWN_EXTRACTOR_AVAILABLE else "❌ No disponible")
    logger.info("")
    
    # Intentar usar cliente GitHub primero, luego extractor propio
    df = None
    metadata: Dict[str, Any] = {}
    
    if GITHUB_CLIENT_AVAILABLE:
        logger.info("Intentando con cliente GitHub...")
        df, metadata = extract_with_github_client(api_key, api_secret, args.max_properties)
    
    if df is None and OWN_EXTRACTOR_AVAILABLE:
        logger.info("Intentando con extractor propio...")
        df, metadata = extract_with_own_extractor(api_key, api_secret, args.max_properties)
    
    if df is None or df.empty:
        logger.error("❌ No se pudieron extraer datos")
        logger.error("Verifica:")
        logger.error("  1. Credenciales API válidas")
        logger.error("  2. Límite de API no excedido (150 calls/mes)")
        logger.error("  3. Conexión a internet")
        return 1
    
    # Guardar CSV
    output_path = Path(args.output) if args.output else OUTPUT_DIR / "idealista_gracia_api.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info("📄 CSV guardado: %s", output_path)
    logger.info("   Propiedades: %s", len(df))
    
    # Guardar metadata
    metadata["num_properties"] = len(df)
    metadata["output_file"] = str(output_path)
    metadata_path = OUTPUT_DIR / "idealista_api_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("📄 Metadata guardada: %s", metadata_path)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

