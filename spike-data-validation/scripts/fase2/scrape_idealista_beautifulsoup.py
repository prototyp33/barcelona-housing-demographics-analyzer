#!/usr/bin/env python3
"""
Scraping de Idealista usando BeautifulSoup (alternativa a API y Playwright).

Basado en: https://www.octoparse.es/blog/como-extraer-los-datos-de-idealista-con-web-scraping

Ventajas:
- Más simple que Playwright (no requiere navegador completo)
- Menos detección anti-bot que Playwright
- Más rápido (solo parsing HTML, no ejecuta JavaScript)

Uso:
    python3 spike-data-validation/scripts/fase2/scrape_idealista_beautifulsoup.py \
        --max-pages 5 \
        --output idealista_gracia_scraped.csv
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# URL base para Gràcia
BASE_URL = "https://www.idealista.com/venta-viviendas/barcelona/gracia/"

# Headers exactos del artículo Octoparse (más simples)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def extract_property_data(listing: BeautifulSoup) -> Optional[Dict[str, Any]]:
    """
    Extrae datos de un listing individual.
    
    Usa selectores exactos del artículo Octoparse primero.
    
    Args:
        listing: Elemento BeautifulSoup con un listing
        
    Returns:
        Diccionario con datos de la propiedad o None si falla
    """
    try:
        # Selectores exactos del artículo Octoparse primero
        title_elem = listing.find('a', class_='item-link')
        price_elem = listing.find('span', class_='item-price')
        location_elem = listing.find('span', class_='item-detail')
        
        # Si no funcionan, intentar alternativos
        if not title_elem:
            title_elem = (
                listing.find('a', {'class': 'item-link'}) or
                listing.find('h2', class_='item-title') or
                listing.find('a', href=True)
            )
        
        if not price_elem:
            price_elem = (
                listing.find('div', class_='item-price') or
                listing.find('span', {'class': 'price'})
            )
        
        if not location_elem:
            location_elem = (
                listing.find('div', class_='item-detail') or
                listing.find('span', {'class': 'location'})
            )
        
        # Extraer superficie si está disponible
        surface_elem = (
            listing.find('span', class_='item-detail-surface') or
            listing.find('span', {'class': 'surface'})
        )
        
        # Extraer habitaciones si está disponible
        rooms_elem = (
            listing.find('span', class_='item-detail-rooms') or
            listing.find('span', {'class': 'rooms'})
        )
        
        if not title_elem or not price_elem:
            return None
        
        # Extraer URL
        url = title_elem.get('href', '')
        if url and not url.startswith('http'):
            url = f"https://www.idealista.com{url}"
        
        # Extraer texto
        title = title_elem.get_text(strip=True)
        price_text = price_elem.get_text(strip=True)
        location = location_elem.get_text(strip=True) if location_elem else ''
        surface = surface_elem.get_text(strip=True) if surface_elem else ''
        rooms = rooms_elem.get_text(strip=True) if rooms_elem else ''
        
        # Limpiar precio (remover símbolos, espacios)
        price_clean = price_text.replace('€', '').replace('.', '').replace(',', '').strip()
        try:
            price = int(price_clean) if price_clean else None
        except ValueError:
            price = None
        
        return {
            'title': title,
            'price': price,
            'price_text': price_text,
            'location': location,
            'surface': surface,
            'rooms': rooms,
            'url': url,
        }
        
    except Exception as e:
        logger.debug(f"Error extrayendo listing: {e}")
        return None


def scrape_page(url: str, page_num: int) -> List[Dict[str, Any]]:
    """
    Scrapea una página de resultados.
    
    Args:
        url: URL de la página
        page_num: Número de página (para logging)
        
    Returns:
        Lista de diccionarios con propiedades
    """
    properties = []
    
    try:
        logger.info(f"Scrapeando página {page_num}: {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Error HTTP {response.status_code} en página {page_num}")
            return properties
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar listings (código exacto del artículo primero)
        listings = soup.find_all('article', class_='item')
        
        if not listings:
            # Intentar selectores alternativos si el principal falla
            listings = (
                soup.find_all('article') or
                soup.find_all('div', class_='item') or
                soup.find_all('article', {'class': 'item'}) or
                soup.find_all('div', {'class': 'item'}) or
                soup.find_all('div', {'data-adid': True})
            )
        
        logger.info(f"   Encontrados {len(listings)} listings en página {page_num}")
        
        for listing in listings:
            prop_data = extract_property_data(listing)
            if prop_data:
                prop_data['page'] = page_num
                properties.append(prop_data)
        
        logger.info(f"   Extraídas {len(properties)} propiedades válidas")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red en página {page_num}: {e}")
    except Exception as e:
        logger.error(f"Error inesperado en página {page_num}: {e}")
    
    return properties


def scrape_idealista_gracia(max_pages: int = 5, delay: float = 3.0) -> pd.DataFrame:
    """
    Scrapea datos de Idealista para Gràcia.
    
    Args:
        max_pages: Número máximo de páginas a scrapear
        delay: Delay entre páginas (segundos)
        
    Returns:
        DataFrame con propiedades extraídas
    """
    logger.info("=" * 70)
    logger.info("SCRAPING IDEALISTA - GRÀCIA (BeautifulSoup)")
    logger.info("=" * 70)
    logger.info(f"URL base: {BASE_URL}")
    logger.info(f"Máximo páginas: {max_pages}")
    logger.info(f"Delay entre páginas: {delay}s")
    logger.info("")
    
    all_properties = []
    
    for page in range(1, max_pages + 1):
        # Construir URL de página
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}?pagina={page}"
        
        # Scrapear página
        properties = scrape_page(url, page)
        all_properties.extend(properties)
        
        # Delay entre páginas (importante para evitar bloqueos)
        if page < max_pages:
            logger.info(f"   Esperando {delay}s antes de siguiente página...")
            time.sleep(delay)
    
    logger.info("")
    logger.info(f"✅ Total propiedades extraídas: {len(all_properties)}")
    
    if not all_properties:
        logger.warning("⚠️  No se extrajeron propiedades. Verificar:")
        logger.warning("   1. Estructura HTML de Idealista puede haber cambiado")
        logger.warning("   2. Selectores CSS pueden necesitar ajuste")
        logger.warning("   3. Puede haber protección anti-bot activa")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_properties)
    return df


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Scrapear Idealista con BeautifulSoup")
    parser.add_argument("--max-pages", type=int, default=5, help="Máximo páginas a scrapear")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay entre páginas (segundos)")
    parser.add_argument("--output", type=str, default=None, help="Archivo CSV de salida")
    parser.add_argument("--test-mode", action="store_true", help="Modo test (solo 1 página)")
    args = parser.parse_args()
    
    if args.test_mode:
        args.max_pages = 1
        logger.info("🧪 Modo test activado (1 página)")
    
    # Scrapear
    df = scrape_idealista_gracia(max_pages=args.max_pages, delay=args.delay)
    
    if df.empty:
        logger.error("❌ No se pudieron extraer propiedades")
        logger.error("")
        logger.error("Posibles causas:")
        logger.error("   1. Estructura HTML de Idealista cambió")
        logger.error("   2. Selectores CSS necesitan actualización")
        logger.error("   3. Protección anti-bot activa")
        logger.error("")
        logger.error("Siguiente paso: Inspeccionar HTML manualmente y ajustar selectores")
        return 1
    
    # Guardar CSV
    output_path = Path(args.output) if args.output else Path("spike-data-validation/data/processed/fase2/idealista_gracia_scraped.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info(f"📄 CSV guardado: {output_path}")
    logger.info(f"   Propiedades: {len(df)}")
    logger.info(f"   Columnas: {', '.join(df.columns)}")
    
    # Estadísticas básicas
    if 'price' in df.columns:
        prices = df['price'].dropna()
        if len(prices) > 0:
            logger.info("")
            logger.info("📊 Estadísticas de precios:")
            logger.info(f"   Media: {prices.mean():.0f} €")
            logger.info(f"   Mediana: {prices.median():.0f} €")
            logger.info(f"   Min: {prices.min():.0f} €")
            logger.info(f"   Max: {prices.max():.0f} €")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

