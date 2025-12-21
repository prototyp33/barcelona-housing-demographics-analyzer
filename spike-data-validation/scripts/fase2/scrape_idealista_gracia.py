#!/usr/bin/env python3
"""
Scraping Idealista para Gràcia (Fase 2 - Issue #202).

Extrae anuncios de venta de Gràcia usando scraping web controlado.
Objetivo: 50-100 anuncios para matching con datos Catastro.

⚠️ IMPORTANTE: Scraping ético con delays largos para evitar bloqueos.
Idealista tiene medidas anti-bot muy agresivas.

Uso:
    python3 spike-data-validation/scripts/fase2/scrape_idealista_gracia.py
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

logger = logging.getLogger(__name__)

# Configuración
BASE_URL = "https://www.idealista.com"
GRACIA_SEARCH_URL = f"{BASE_URL}/venta-viviendas/barcelona/gracia/"
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Delays éticos (segundos)
DELAY_BETWEEN_PAGES = 5.0  # Delay entre páginas
DELAY_BETWEEN_REQUESTS = 2.0  # Delay entre requests
RANDOM_DELAY_RANGE = (1.0, 3.0)  # Delay aleatorio adicional


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """Espera aleatoria para simular comportamiento humano."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def extract_property_data(page: Page, property_url: str) -> Optional[Dict[str, Any]]:
    """
    Extrae datos de un anuncio individual.
    
    Args:
        page: Página de Playwright
        property_url: URL del anuncio
        
    Returns:
        Diccionario con datos del anuncio o None si falla
    """
    try:
        logger.debug("Extrayendo: %s", property_url)
        page.goto(property_url, wait_until="networkidle", timeout=30000)
        random_delay(*RANDOM_DELAY_RANGE)

        # Extraer datos básicos
        data: Dict[str, Any] = {
            "url": property_url,
            "timestamp": datetime.now().isoformat(),
        }

        # Precio
        try:
            precio_elem = page.query_selector('span[class*="price"]')
            if precio_elem:
                precio_text = precio_elem.inner_text()
                # Limpiar y convertir: "350.000 €" -> 350000
                precio_clean = precio_text.replace(".", "").replace("€", "").replace(",", ".").strip()
                try:
                    data["precio"] = float(precio_clean)
                except ValueError:
                    data["precio"] = None
        except Exception:
            data["precio"] = None

        # Superficie
        try:
            superficie_elem = page.query_selector('span:has-text("m²")')
            if superficie_elem:
                superficie_text = superficie_elem.inner_text()
                # Extraer número: "85 m²" -> 85
                import re
                match = re.search(r"(\d+(?:[.,]\d+)?)", superficie_text)
                if match:
                    data["superficie_m2"] = float(match.group(1).replace(",", "."))
        except Exception:
            data["superficie_m2"] = None

        # Habitaciones
        try:
            habitaciones_elem = page.query_selector('span:has-text("hab")')
            if habitaciones_elem:
                habitaciones_text = habitaciones_elem.inner_text()
                match = re.search(r"(\d+)", habitaciones_text)
                if match:
                    data["habitaciones"] = int(match.group(1))
        except Exception:
            data["habitaciones"] = None

        # Dirección
        try:
            direccion_elem = page.query_selector('h1[class*="title"], div[class*="address"]')
            if direccion_elem:
                data["direccion"] = direccion_elem.inner_text().strip()
        except Exception:
            data["direccion"] = None

        # Descripción (primeros 200 caracteres)
        try:
            desc_elem = page.query_selector('div[class*="description"]')
            if desc_elem:
                desc_text = desc_elem.inner_text().strip()
                data["descripcion"] = desc_text[:200] if len(desc_text) > 200 else desc_text
        except Exception:
            data["descripcion"] = None

        return data

    except PlaywrightTimeoutError:
        logger.warning("Timeout al cargar: %s", property_url)
        return None
    except Exception as exc:
        logger.warning("Error extrayendo %s: %s", property_url, exc)
        return None


def scrape_idealista_gracia(max_properties: int = 100, max_pages: int = 5) -> pd.DataFrame:
    """
    Scraping principal de Idealista para Gràcia.
    
    Args:
        max_properties: Máximo de propiedades a extraer
        max_pages: Máximo de páginas a procesar
        
    Returns:
        DataFrame con propiedades extraídas
    """
    logger.info("=" * 70)
    logger.info("SCRAPING IDEALISTA - GRÀCIA")
    logger.info("=" * 70)
    logger.info("URL: %s", GRACIA_SEARCH_URL)
    logger.info("Máximo propiedades: %s", max_properties)
    logger.info("Máximo páginas: %s", max_pages)
    logger.info("")

    properties: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        # Iniciar navegador con configuración anti-detección
        browser = p.chromium.launch(
            headless=False,  # Cambiar a True en producción, False para debugging
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="es-ES",
            timezone_id="Europe/Madrid",
        )
        
        # Añadir scripts para evitar detección
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:
            # Navegar a página de búsqueda
            logger.info("Cargando página de búsqueda...")
            page.goto(GRACIA_SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Esperar más tiempo para que se cargue el contenido dinámico
            logger.info("Esperando carga completa (puede tardar por protección anti-bot)...")
            random_delay(5, 8)  # Esperar más tiempo inicial
            
            # Verificar si hay página de protección
            page_title = page.title()
            page_content = page.content()
            
            if "cloudflare" in page_content.lower() or "checking your browser" in page_content.lower():
                logger.warning("⚠️  Detectada página de protección Cloudflare")
                logger.info("Esperando 10 segundos adicionales...")
                random_delay(10, 15)
                page.reload(wait_until="domcontentloaded", timeout=30000)
                random_delay(5, 8)
            
            # Verificar que la página se cargó correctamente
            if "idealista" not in page_title.lower() and "idealista" not in page_content.lower()[:500]:
                logger.error("❌ La página no se cargó correctamente. Posible bloqueo anti-bot.")
                logger.error("Título de página: %s", page_title)
                logger.error("Considera usar la API oficial de Idealista o aumentar delays")
                return pd.DataFrame()

            # Aceptar cookies si aparece
            try:
                cookie_button = page.query_selector('button:has-text("Aceptar"), button:has-text("Accept")')
                if cookie_button:
                    cookie_button.click()
                    random_delay(1, 2)
            except Exception:
                pass

            # Esperar a que se cargue el contenido de propiedades
            logger.info("Esperando a que se cargue el contenido de propiedades...")
            try:
                # Esperar a que aparezcan elementos de propiedades (varios selectores posibles)
                # Intentar múltiples selectores con más tiempo
                selectors_to_wait = [
                    'article',
                    '.item',
                    '[data-id]',
                    '.property-item',
                    'a[href*="/inmueble/"]',
                    'a[href*="/vivienda/"]',
                    '.detail-link',
                    '[class*="property"]',
                ]
                
                found_content = False
                for selector in selectors_to_wait:
                    try:
                        page.wait_for_selector(selector, timeout=15000, state="visible")
                        logger.info("   ✓ Contenido encontrado con selector: %s", selector)
                        found_content = True
                        break
                    except PlaywrightTimeoutError:
                        continue
                
                if not found_content:
                    logger.warning("   ⚠️  No se encontró contenido con selectores estándar")
                    logger.info("   Esperando 5 segundos adicionales...")
                    random_delay(5, 7)
                
                random_delay(2, 3)
            except PlaywrightTimeoutError:
                logger.warning("Timeout esperando contenido. Continuando de todas formas...")

            # Extraer URLs de propiedades de cada página
            page_num = 1
            property_urls: List[str] = []

            while page_num <= max_pages and len(property_urls) < max_properties:
                logger.info("Procesando página %s...", page_num)

                # Extraer URLs de anuncios en esta página (múltiples estrategias)
                try:
                    # Estrategia 1: Buscar enlaces con /inmueble/ o /vivienda/
                    selectors = [
                        'a[href*="/inmueble/"]',
                        'a[href*="/vivienda/"]',
                        'article a',
                        '.item a',
                        '[data-id] a',
                    ]
                    
                    found_links = False
                    for selector in selectors:
                        try:
                            property_links = page.query_selector_all(selector)
                            logger.debug("   Selector '%s': %s enlaces encontrados", selector, len(property_links))
                            
                            for link in property_links:
                                href = link.get_attribute("href")
                                if href:
                                    # Normalizar URL
                                    if "/inmueble/" in href or "/vivienda/" in href:
                                        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                                        if full_url not in property_urls:
                                            property_urls.append(full_url)
                                            found_links = True
                                            if len(property_urls) >= max_properties:
                                                break
                            
                            if found_links:
                                break
                        except Exception as exc:
                            logger.debug("   Selector '%s' falló: %s", selector, exc)
                            continue
                    
                    if not found_links:
                        # Debug: guardar HTML de la página para inspección
                        html_snippet = page.content()[:2000]
                        logger.warning("   No se encontraron enlaces. HTML snippet (primeros 2000 chars):")
                        logger.warning("   %s", html_snippet[:500])
                        
                except Exception as exc:
                    logger.warning("Error extrayendo URLs página %s: %s", page_num, exc)

                logger.info("   URLs encontradas hasta ahora: %s", len(property_urls))

                # Ir a siguiente página
                if page_num < max_pages and len(property_urls) < max_properties:
                    try:
                        # Múltiples selectores para botón siguiente
                        next_selectors = [
                            'a[aria-label*="Siguiente"]',
                            'a:has-text("Siguiente")',
                            'a:has-text("Siguiente página")',
                            '.pagination a:has-text(">")',
                            'button:has-text("Siguiente")',
                        ]
                        
                        next_button = None
                        for selector in next_selectors:
                            try:
                                next_button = page.query_selector(selector)
                                if next_button:
                                    break
                            except Exception:
                                continue
                        
                        if next_button:
                            next_button.click()
                            random_delay(DELAY_BETWEEN_PAGES, DELAY_BETWEEN_PAGES + 2)
                            # Esperar a que se cargue nueva página
                            try:
                                page.wait_for_load_state("networkidle", timeout=10000)
                            except PlaywrightTimeoutError:
                                pass
                        else:
                            logger.info("No hay más páginas disponibles")
                            break
                    except Exception as exc:
                        logger.info("No se pudo ir a siguiente página: %s", exc)
                        break

                page_num += 1

            # Extraer datos de cada propiedad
            logger.info("")
            logger.info("Extrayendo datos de %s propiedades...", len(property_urls))

            for i, prop_url in enumerate(property_urls[:max_properties], 1):
                logger.info("[%s/%s] %s", i, min(len(property_urls), max_properties), prop_url)

                prop_data = extract_property_data(page, prop_url)
                if prop_data:
                    properties.append(prop_data)

                # Delay entre propiedades
                if i < len(property_urls):
                    random_delay(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS + 2)

        finally:
            browser.close()

    # Convertir a DataFrame
    if properties:
        df = pd.DataFrame(properties)
        logger.info("")
        logger.info("✅ Extracción completada: %s propiedades", len(df))
        return df
    else:
        logger.warning("⚠️  No se extrajeron propiedades")
        return pd.DataFrame()


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Scraping Idealista para Gràcia")
    parser.add_argument("--max-properties", type=int, default=100, help="Máximo propiedades a extraer")
    parser.add_argument("--max-pages", type=int, default=5, help="Máximo páginas a procesar")
    parser.add_argument("--output", type=str, default=None, help="Ruta de salida CSV")
    args = parser.parse_args()

    # Scraping
    df = scrape_idealista_gracia(
        max_properties=args.max_properties,
        max_pages=args.max_pages,
    )

    if df.empty:
        logger.error("No se extrajeron datos")
        return 1

    # Guardar CSV
    output_path = Path(args.output) if args.output else OUTPUT_DIR / "idealista_gracia_scraped.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info("📄 CSV guardado: %s", output_path)

    # Guardar metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "num_properties": len(df),
        "completitud": {
            "precio": float(df["precio"].notna().sum() / len(df) * 100) if "precio" in df.columns else 0,
            "superficie": float(df["superficie_m2"].notna().sum() / len(df) * 100) if "superficie_m2" in df.columns else 0,
            "direccion": float(df["direccion"].notna().sum() / len(df) * 100) if "direccion" in df.columns else 0,
        },
    }
    metadata_path = OUTPUT_DIR / "idealista_scraping_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("📄 Metadata guardada: %s", metadata_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

