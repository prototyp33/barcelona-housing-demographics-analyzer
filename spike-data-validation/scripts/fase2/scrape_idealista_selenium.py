#!/usr/bin/env python3
"""
Scraping de Idealista usando Selenium con Firefox (basado en video tutorial).

Referencia:
- Video: https://www.youtube.com/watch?v=I6Q4B4CSPtU
- Repositorio: https://github.com/JuanPMC/comprar_casa

El video menciona que Selenium con Firefox es más efectivo que requests
para evitar bloqueos, ya que simula un navegador real.

Uso:
    python3 spike-data-validation/scripts/fase2/scrape_idealista_selenium.py \
        --max-pages 3
"""

from __future__ import annotations

import argparse
import logging
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    try:
        from webdriver_manager.firefox import GeckoDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

# URL base para Gràcia
BASE_URL = "https://www.idealista.com/venta-viviendas/barcelona/gracia/"

# Delays aleatorios según código que funciona (2-20 segundos)
MIN_DELAY = 2.0
MAX_DELAY = 20.0

# Delays para comportamiento humano entre páginas
MIN_HUMAN_DELAY = 3.0
MAX_HUMAN_DELAY = 8.0


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def random_delay(min_sec: float = MIN_DELAY, max_sec: float = MAX_DELAY) -> None:
    """Espera aleatoria para simular comportamiento humano."""
    delay = random.uniform(min_sec, max_sec)
    logger.debug(f"Esperando {delay:.2f}s...")
    time.sleep(delay)


def simulate_human_behavior(driver: webdriver.Firefox) -> None:
    """
    Simula comportamiento humano para evitar detección.
    
    Comportamiento más natural:
    - Espera inicial (como un humano que lee)
    - Scrolling gradual y pausado (como lectura real)
    - Movimientos de mouse naturales
    - Pausas variables entre acciones
    """
    try:
        # 1. Espera inicial más larga (humano leyendo la página)
        initial_wait = random.uniform(2.0, 4.0)
        logger.debug(f"Espera inicial: {initial_wait:.1f}s (simulando lectura)")
        time.sleep(initial_wait)
        
        # 2. Scrolling gradual hacia abajo (como un humano leyendo)
        window_height = driver.execute_script("return window.innerHeight")
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scrolling en pasos más naturales (más pausas, más variación)
        scroll_steps = random.randint(4, 8)  # Más pasos para ser más natural
        current_scroll = 0
        
        for i in range(scroll_steps):
            # Scroll más pequeño y variable
            scroll_amount = window_height * random.uniform(0.2, 0.5)
            current_scroll += scroll_amount
            
            # No scroll más allá del final
            if current_scroll > total_height:
                current_scroll = total_height
            
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            
            # Pausa variable después de cada scroll (como leyendo)
            scroll_pause = random.uniform(0.8, 2.5)  # Pausas más largas
            time.sleep(scroll_pause)
            
            # Ocasionalmente hacer un pequeño scroll hacia arriba (comportamiento natural)
            if random.random() < 0.3:  # 30% de probabilidad
                back_scroll = random.randint(50, 200)
                current_scroll = max(0, current_scroll - back_scroll)
                driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                time.sleep(random.uniform(0.5, 1.0))
        
        # 3. Movimiento del mouse sobre elementos (más natural)
        try:
            actions = ActionChains(driver)
            # Mover mouse a diferentes posiciones (simulando hover sobre elementos)
            for _ in range(random.randint(2, 4)):
                x_offset = random.randint(-200, 200)
                y_offset = random.randint(-200, 200)
                actions.move_by_offset(x_offset, y_offset).perform()
                time.sleep(random.uniform(0.2, 0.6))
        except Exception:
            # Si falla, no es crítico
            pass
        
        # 4. Scroll final hacia abajo (para asegurar que todo está cargado)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.5, 3.0))  # Pausa final más larga
        
        # 5. Scroll hacia arriba un poco (comportamiento natural de revisar)
        driver.execute_script("window.scrollBy(0, -300);")
        time.sleep(random.uniform(0.5, 1.0))
        
        logger.debug("✅ Comportamiento humano simulado (scrolling gradual, pausas naturales)")
        
    except Exception as e:
        logger.debug(f"Error simulando comportamiento humano: {e}")
        # No es crítico, continuar de todas formas


def accept_cookies_if_present(driver: webdriver.Firefox) -> bool:
    """
    Intenta aceptar el banner de cookies si está presente.
    
    Returns:
        True si se aceptaron cookies, False si no había banner
    """
    cookie_selectors = [
        "button[id*='cookie']",
        "button[class*='cookie']",
        "button[aria-label*='cookie' i]",
        "button[aria-label*='aceptar' i]",
        "button[aria-label*='accept' i]",
        "#cookie-consent button",
        ".cookie-consent button",
        "button.lw-consent-accept",
    ]
    
    for selector in cookie_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    # Esperar un poco antes de hacer click (comportamiento humano)
                    time.sleep(random.uniform(0.5, 1.5))
                    element.click()
                    logger.info("✅ Banner de cookies aceptado")
                    time.sleep(random.uniform(0.5, 1.0))
                    return True
        except Exception:
            continue
    
    return False


def wait_for_captcha_resolution(driver: webdriver.Firefox, max_wait_seconds: int = 300) -> bool:
    """
    Espera a que el usuario resuelva el CAPTCHA manualmente (modo visible).
    
    Verifica periódicamente si el contenido de la página está disponible,
    lo que indica que el CAPTCHA fue resuelto.
    
    Args:
        driver: Driver de Selenium
        max_wait_seconds: Tiempo máximo de espera en segundos (default: 5 minutos)
        
    Returns:
        True si el contenido se cargó (CAPTCHA resuelto), False si timeout
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔒 CAPTCHA DETECTADO")
    logger.info("=" * 70)
    logger.info("Por favor, resuelve el CAPTCHA en el navegador visible.")
    logger.info(f"Esperando hasta {max_wait_seconds} segundos...")
    logger.info("")
    
    start_time = time.time()
    check_interval = 3  # Verificar cada 3 segundos
    
    # Selectores que indican que el contenido está cargado (CAPTCHA resuelto)
    content_selectors = [
        "article.item",
        "div.item-info-container",
        "section.items-container",
        "div.items-list"
    ]
    
    while (time.time() - start_time) < max_wait_seconds:
        # Verificar si el contenido está disponible
        for selector in content_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and any(elem.is_displayed() for elem in elements):
                    elapsed = int(time.time() - start_time)
                    logger.info("")
                    logger.info(f"✅ CAPTCHA resuelto! (Tiempo: {elapsed}s)")
                    logger.info("Continuando con el scraping...")
                    logger.info("")
                    return True
            except Exception:
                continue
        
        # Verificar si todavía hay CAPTCHA visible
        page_source = driver.page_source.lower()
        if 'captcha' not in page_source and 'cloudflare' not in page_source:
            # Puede que el CAPTCHA ya no esté, pero el contenido tampoco
            # Continuar verificando...
            pass
        
        # Esperar antes de verificar de nuevo
        time.sleep(check_interval)
        
        # Mostrar progreso cada 15 segundos
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed > 0:
            remaining = max_wait_seconds - elapsed
            logger.info(f"   Esperando... ({elapsed}s / {max_wait_seconds}s) - Quedan {remaining}s")
    
    # Timeout
    elapsed = int(time.time() - start_time)
    logger.warning("")
    logger.warning(f"⏱️  Timeout esperando resolución de CAPTCHA ({elapsed}s)")
    logger.warning("El CAPTCHA no fue resuelto a tiempo.")
    return False


def setup_firefox_driver(headless: bool = True, use_webdriver_manager: bool = True) -> Optional[webdriver.Firefox]:
    """
    Configura driver de Firefox con opciones mejoradas.
    
    Usa webdriver_manager para gestionar geckodriver automáticamente si está disponible.
    Esto simplifica la instalación y gestión del driver.
    
    Args:
        headless: Si True, ejecuta en modo headless
        use_webdriver_manager: Si True, usa webdriver_manager para instalar geckodriver automáticamente
        
    Returns:
        Driver de Firefox configurado o None si falla
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium no está instalado")
        logger.error("Instalar: pip install selenium")
        return None
    
    try:
        options = FirefoxOptions()
        
        if headless:
            options.add_argument('--headless')
        
        # Opciones adicionales para evitar detección (según código que funciona)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Headers según tutorial: "Soy un navegador Firefox en Windows"
        options.set_preference('dom.webdriver.enabled', False)
        options.set_preference('useAutomationExtension', False)
        options.set_preference('general.useragent.override', 
                              'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0')
        
        # Configurar servicio (usar webdriver_manager si está disponible)
        if use_webdriver_manager and WEBDRIVER_MANAGER_AVAILABLE:
            try:
                service = FirefoxService(GeckoDriverManager().install())
                logger.debug("✅ Usando webdriver_manager para geckodriver")
            except Exception as e:
                logger.warning(f"webdriver_manager no disponible, usando geckodriver del sistema: {e}")
                service = FirefoxService()
        else:
            if use_webdriver_manager:
                logger.warning("webdriver_manager no instalado. Instalar: pip install webdriver-manager")
            service = FirefoxService()
        
        # Crear driver
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(60)  # Timeout más largo para cargas lentas
        
        # Maximizar ventana (comportamiento más natural)
        if not headless:
            driver.maximize_window()
        
        logger.info("✅ Driver Firefox configurado (comportamiento humano mejorado)")
        return driver
        
    except Exception as e:
        logger.error(f"Error configurando Firefox driver: {e}")
        if not WEBDRIVER_MANAGER_AVAILABLE:
            logger.error("Sugerencia: pip install webdriver-manager (instala geckodriver automáticamente)")
        else:
            logger.error("Asegúrate de tener geckodriver instalado")
            logger.error("macOS: brew install geckodriver")
        return None


def extract_property_data_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extrae datos usando BeautifulSoup según metodología del tutorial.
    
    El tutorial usa BeautifulSoup para parsear el HTML obtenido por Selenium.
    Busca contenedores con clase 'item-info-container' y extrae:
    - Precio: h2 con clase 'item-price'
    - Detalles: span dentro de características (habitaciones, m²)
    - Descripción y Link: texto descriptivo y href
    
    Args:
        html_content: Contenido HTML de la página
        
    Returns:
        Lista de diccionarios con propiedades extraídas
    """
    import re
    
    properties = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Buscar contenedores: según HTML real, cada propiedad está en <article class="item">
        # y dentro hay <div class="item-info-container">. Buscar ambos para mayor robustez.
        containers = soup.find_all('article', class_='item')
        
        # Si no encontramos articles, intentar div.item-info-container directamente
        if len(containers) == 0:
            logger.debug("No se encontraron 'article.item', intentando 'div.item-info-container'...")
            containers = soup.find_all('div', class_='item-info-container')
            if len(containers) == 0:
                containers = soup.find_all('div', class_='item')
            if len(containers) == 0:
                containers = soup.find_all('div', class_=lambda x: x and 'item' in str(x).lower())
        
        # Si encontramos articles, buscar item-info-container dentro de cada uno
        if containers and all(c.name == 'article' for c in containers):
            # Buscar item-info-container dentro de cada article
            info_containers = []
            for article in containers:
                info_div = article.find('div', class_='item-info-container')
                if info_div:
                    info_containers.append(info_div)
                else:
                    # Si no hay item-info-container, usar el article completo
                    info_containers.append(article)
            containers = info_containers if info_containers else containers
        
        logger.info(f"Encontrados {len(containers)} contenedores de propiedades")
        
        for container in containers:
            try:
                data: Dict[str, Any] = {}
                
                # Precio: según código que funciona
                # div.find("span", class_="item-price h2-simulated").get_text().split("€")[0]
                price_elem = container.find('span', class_='item-price h2-simulated')
                if not price_elem:
                    # Fallback
                    price_elem = (
                        container.find('span', class_='item-price') or
                        container.find('span', class_=lambda x: x and 'item-price' in str(x)) or
                        container.find('h2', class_='item-price')
                    )
                
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Limpiar según código que funciona: split("€")[0] y luego limpiar puntos
                    price_clean = price_text.split("€")[0].replace('.', '').replace(',', '').strip()
                    try:
                        data['precio'] = int(price_clean) if price_clean else None
                    except ValueError:
                        data['precio'] = None
                    data['precio_text'] = price_text
                else:
                    data['precio'] = None
                    data['precio_text'] = ''
                
                # Detalles: extracción directa según código que funciona
                # Buscar div.item-detail-char y extraer spans.item-detail
                detail_container = container.find('div', class_='item-detail-char')
                if detail_container:
                    caracteristicas = detail_container.find_all('span', class_='item-detail')
                    
                    # Extracción directa: primer span = habitaciones, segundo = tamaño, tercero = descripción
                    if len(caracteristicas) >= 1:
                        habitaciones_text = caracteristicas[0].get_text(strip=True)
                        # Extraer número: "2 hab." -> 2
                        habitaciones_match = re.search(r'(\d+)', habitaciones_text)
                        data['habitaciones'] = int(habitaciones_match.group(1)) if habitaciones_match else None
                    else:
                        data['habitaciones'] = None
                    
                    if len(caracteristicas) >= 2:
                        tamanio_text = caracteristicas[1].get_text(strip=True)
                        # Extraer número: "80 m²" -> 80.0
                        tamanio_match = re.search(r'(\d+(?:[.,]\d+)?)', tamanio_text)
                        if tamanio_match:
                            data['superficie_m2'] = float(tamanio_match.group(1).replace(',', '.'))
                        else:
                            data['superficie_m2'] = None
                    else:
                        data['superficie_m2'] = None
                    
                    if len(caracteristicas) >= 3:
                        data['detalles'] = caracteristicas[2].get_text(strip=True)
                    else:
                        data['detalles'] = ''
                else:
                    # Fallback: buscar directamente
                    detail_spans = container.find_all('span', class_='item-detail')
                    if len(detail_spans) >= 1:
                        habitaciones_text = detail_spans[0].get_text(strip=True)
                        habitaciones_match = re.search(r'(\d+)', habitaciones_text)
                        data['habitaciones'] = int(habitaciones_match.group(1)) if habitaciones_match else None
                    else:
                        data['habitaciones'] = None
                    
                    if len(detail_spans) >= 2:
                        tamanio_text = detail_spans[1].get_text(strip=True)
                        tamanio_match = re.search(r'(\d+(?:[.,]\d+)?)', tamanio_text)
                        if tamanio_match:
                            data['superficie_m2'] = float(tamanio_match.group(1).replace(',', '.'))
                        else:
                            data['superficie_m2'] = None
                    else:
                        data['superficie_m2'] = None
                    
                    data['detalles'] = ' '.join([span.get_text(strip=True) for span in detail_spans[2:]]) if len(detail_spans) > 2 else ''
                
                # Link y dirección (según HTML real)
                link_elem = container.find('a', class_='item-link', href=True)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href and not href.startswith('http'):
                        data['link'] = f"https://www.idealista.com{href}"
                    else:
                        data['link'] = href
                    
                    # Dirección: según HTML real, está en el atributo 'title' del link
                    # Ejemplo: title="Piso en calle de Antonio López, Comillas, Madrid"
                    title_attr = link_elem.get('title', '')
                    if title_attr:
                        # Extraer dirección del title: "Piso en calle de Antonio López, Comillas, Madrid"
                        # Remover "Piso en " si está presente y tomar primeras 2 partes separadas por coma
                        title_clean = title_attr.replace('Piso en ', '').replace('Casa en ', '').strip()
                        direccion_parts = title_clean.split(',')[:2]
                        data['localidad'] = ', '.join(direccion_parts).strip()
                    else:
                        # Fallback: intentar extraer del texto del link
                        link_text = link_elem.get_text(strip=True)
                        if link_text:
                            # Remover primeros caracteres y tomar primeras 2 partes separadas por coma
                            direccion_parts = link_text[9:].replace("\n", "").split(",")[:2]
                            data['localidad'] = "".join(direccion_parts).strip()
                        else:
                            data['localidad'] = ''
                else:
                    data['link'] = ''
                    data['localidad'] = ''
                
                # Descripción completa (según HTML real: <div class="item-description description"><p class="ellipsis">...)
                desc_elem = container.find('div', class_='item-description')
                if not desc_elem:
                    # Fallback: buscar también con clase 'description'
                    desc_elem = container.find('div', class_=lambda x: x and 'item-description' in str(x))
                
                if desc_elem:
                    # Buscar párrafo dentro (puede tener clase 'ellipsis')
                    desc_p = desc_elem.find('p', class_='ellipsis')
                    if not desc_p:
                        desc_p = desc_elem.find('p')
                    
                    if desc_p:
                        data['descripcion'] = desc_p.get_text(strip=True)
                    else:
                        data['descripcion'] = desc_elem.get_text(strip=True)
                else:
                    data['descripcion'] = ''
                
                # Solo agregar si tiene precio o descripción
                if data.get('precio') or data.get('descripcion'):
                    properties.append(data)
                    
            except Exception as e:
                logger.debug(f"Error extrayendo contenedor: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error parseando HTML con BeautifulSoup: {e}")
    
    return properties


def get_url_for_page_number(base_url: str, page_num: int) -> str:
    """
    Genera URL dinámica para paginación según metodología del tutorial.
    
    El tutorial usa f-strings para inyectar el número de página en la URL base.
    
    Args:
        base_url: URL base obtenida de filtros manuales
        page_num: Número de página (1, 2, 3, ...)
        
    Returns:
        URL completa con número de página
    """
    if page_num == 1:
        return base_url
    else:
        # Agregar parámetro de paginación
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}pagina={page_num}"


def scrape_page(driver: webdriver.Firefox, url: str, page_num: int, cache_dir: Optional[Path] = None, headless: bool = True) -> List[Dict[str, Any]]:
    """
    Scrapea una página según metodología del tutorial.
    
    Metodología:
    1. Selenium obtiene HTML (carga JavaScript completo)
    2. Guarda HTML localmente para evitar peticiones innecesarias
    3. BeautifulSoup parsea el HTML guardado
    4. Extrae datos usando selectores específicos
    
    Args:
        driver: Driver de Selenium
        url: URL de la página
        page_num: Número de página
        cache_dir: Directorio para guardar HTML cacheado
        
    Returns:
        Lista de diccionarios con propiedades
    """
    properties = []
    cache_file = None
    
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"page_{page_num}.html"
    
    try:
        # Verificar si ya tenemos el HTML cacheado
        if cache_file and cache_file.exists():
            logger.info(f"   Usando HTML cacheado para página {page_num}")
            html_content = cache_file.read_text(encoding='utf-8')
        else:
            logger.info(f"Scrapeando página {page_num}: {url}")
            
            # Navegar a la página
            logger.debug(f"Navegando a: {url}")
            driver.get(url)
            
            # 1. Esperar inicial más larga (como un humano que espera a que cargue completamente)
            initial_wait = random.uniform(3.0, 5.0)
            logger.debug(f"Espera inicial después de carga: {initial_wait:.1f}s")
            time.sleep(initial_wait)
            
            # 2. Aceptar cookies si están presentes (comportamiento humano)
            # Esperar un poco antes de buscar cookies (como un humano que lee)
            time.sleep(random.uniform(0.5, 1.5))
            accept_cookies_if_present(driver)
            
            # 3. Esperar a que cargue el contenido (JavaScript completo)
            # Definir selectores para usar en múltiples lugares
            selectors = [
                "article.item",
                "div.item-info-container",
                "section.items-container",
                "div.items-list"
            ]
            
            # Intentar múltiples selectores con timeout más largo
            try:
                element_found = False
                for selector in selectors:
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        element_found = True
                        logger.debug(f"Elemento encontrado: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if not element_found:
                    raise TimeoutException("No se encontró ningún contenedor esperado")
                
                # 4. Simular comportamiento humano (scrolling, mouse movements)
                logger.debug("Simulando comportamiento humano...")
                simulate_human_behavior(driver)
                
                # 5. Esperar un poco más después de simular comportamiento
                time.sleep(random.uniform(1.0, 2.0))
                
            except TimeoutException:
                logger.warning(f"Timeout esperando contenido en página {page_num}")
                page_source = driver.page_source
                page_url = driver.current_url
                
                if 'cloudflare' in page_source.lower() or 'checking your browser' in page_source.lower():
                    logger.error("⚠️  Cloudflare detectado - Bloqueado")
                elif 'uso indebido' in page_source.lower() or 'acceso bloqueado' in page_source.lower() or 'se ha detectado un uso indebido' in page_source.lower():
                    logger.error("")
                    logger.error("=" * 70)
                    logger.error("🚫 BLOQUEO DE IP DETECTADO")
                    logger.error("=" * 70)
                    logger.error("Idealista ha bloqueado tu IP por 'uso indebido'.")
                    logger.error("")
                    logger.error("💡 SOLUCIONES:")
                    logger.error("")
                    logger.error("1. 🔄 Usar VPN (recomendado para pruebas)")
                    logger.error("   - Conecta a una VPN y vuelve a ejecutar el script")
                    logger.error("")
                    logger.error("2. 📱 Cambiar de red")
                    logger.error("   - Usa otra WiFi o móvil como hotspot")
                    logger.error("")
                    logger.error("3. ⏰ Esperar (bloqueo puede ser temporal)")
                    logger.error("   - Espera 1-2 horas y vuelve a intentar")
                    logger.error("")
                    logger.error("4. 🔑 Usar API oficial (única opción estable)")
                    logger.error("   - Obtener credenciales: https://developers.idealista.com/")
                    logger.error("")
                    logger.error("=" * 70)
                    logger.error("")
                elif 'captcha' in page_source.lower():
                    logger.error("⚠️  CAPTCHA detectado")
                    # Si no está en modo headless, esperar a que el usuario resuelva el CAPTCHA
                    if not headless:
                        captcha_resolved = wait_for_captcha_resolution(driver, max_wait_seconds=300)
                        if captcha_resolved:
                            # Intentar encontrar contenido de nuevo después de resolver CAPTCHA
                            try:
                                for selector in selectors:
                                    try:
                                        WebDriverWait(driver, 10).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                        )
                                        logger.info("✅ Contenido encontrado después de resolver CAPTCHA")
                                        # Simular comportamiento humano antes de continuar
                                        simulate_human_behavior(driver)
                                        time.sleep(random.uniform(1.0, 2.0))
                                        break
                                    except TimeoutException:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error después de resolver CAPTCHA: {e}")
                    else:
                        logger.error("   💡 Sugerencia: Usa --no-headless para resolver CAPTCHA manualmente")
                else:
                    logger.warning("Página cargada pero no se encontraron contenedores esperados")
                    # Intentar parsear de todas formas
                # No retornar aquí, intentar parsear el HTML que tenemos
            
            # Obtener HTML completo (con JavaScript ejecutado)
            html_content = driver.page_source
            
            # Guardar HTML localmente según metodología del tutorial
            if cache_file:
                cache_file.write_text(html_content, encoding='utf-8')
                logger.debug(f"   HTML guardado en cache: {cache_file}")
        
        # Parsear con BeautifulSoup según metodología del tutorial
        properties = extract_property_data_from_html(html_content)
        
        # Agregar número de página a cada propiedad
        for prop in properties:
            prop['page'] = page_num
        
        logger.info(f"   Extraídas {len(properties)} propiedades válidas")
        
    except Exception as e:
        logger.error(f"Error scrapeando página {page_num}: {e}")
    
    return properties


def scrape_idealista_gracia(
    max_pages: int = 3, 
    headless: bool = True, 
    use_cache: bool = True,
    restart_driver_per_page: bool = False
) -> pd.DataFrame:
    """
    Scrapea datos de Idealista según metodología del tutorial.
    
    Flujo según tutorial:
    1. Bucle For para recorrer páginas
    2. Selenium (Firefox) obtiene HTML
    3. BeautifulSoup parsea HTML
    4. Sleep aleatorio (2-20s) entre páginas
    5. CSV Export
    
    Args:
        max_pages: Número máximo de páginas
        headless: Si True, ejecuta en modo headless
        use_cache: Si True, guarda HTML localmente para evitar peticiones
        restart_driver_per_page: Si True, cierra y reabre el driver entre páginas
                                 (menos detectable pero más lento)
        
    Returns:
        DataFrame con propiedades extraídas
    """
    logger.info("=" * 70)
    logger.info("SCRAPING IDEALISTA - GRÀCIA (Metodología Tutorial)")
    logger.info("=" * 70)
    logger.info(f"URL base: {BASE_URL}")
    logger.info(f"Máximo páginas: {max_pages}")
    logger.info(f"Modo headless: {headless}")
    logger.info(f"Cache HTML: {use_cache}")
    logger.info(f"Reiniciar driver por página: {restart_driver_per_page}")
    logger.info("")
    
    if not SELENIUM_AVAILABLE:
        logger.error("❌ Selenium no está instalado")
        logger.error("Instalar: pip install selenium")
        return pd.DataFrame()
    
    # Directorio para cache HTML
    cache_dir = Path("spike-data-validation/data/raw/idealista_cache") if use_cache else None
    
    all_properties = []
    driver = None
    
    try:
        # Bucle For según metodología del tutorial
        for page in range(1, max_pages + 1):
            # Si restart_driver_per_page, crear nuevo driver para cada página
            if restart_driver_per_page or driver is None:
                if driver is not None:
                    driver.quit()
                    logger.debug("Driver cerrado (reinicio por página)")
                    # Esperar un poco antes de crear nuevo driver
                    time.sleep(random.uniform(1.0, 2.0))
                
                driver = setup_firefox_driver(headless=headless)
                if not driver:
                    logger.error(f"❌ No se pudo crear driver para página {page}")
                    break
            
            # Generar URL dinámica según tutorial
            url = get_url_for_page_number(BASE_URL, page)
            
            # Scrapear página (Selenium + BeautifulSoup)
            properties = scrape_page(driver, url, page, cache_dir, headless=headless)
            all_properties.extend(properties)
            
            # Sleep aleatorio entre páginas (según código que funciona: 2-20 segundos)
            if page < max_pages:
                delay = random.randint(int(MIN_DELAY), int(MAX_DELAY))  # Usar randint como en el código que funciona
                logger.info(f"   Esperando {delay}s antes de siguiente página (simulando lectura humana)...")
                time.sleep(delay)
        
        logger.info("")
        logger.info(f"✅ Total propiedades extraídas: {len(all_properties)}")
        
    finally:
        if driver is not None:
            driver.quit()
            logger.info("Driver cerrado")
    
    if not all_properties:
        logger.warning("⚠️  No se extrajeron propiedades")
        logger.warning("Verificar:")
        logger.warning("   1. Selectores CSS pueden necesitar ajuste")
        logger.warning("   2. Estructura HTML puede haber cambiado")
        logger.warning("   3. Puede haber protección anti-bot activa")
        return pd.DataFrame()
    
    return pd.DataFrame(all_properties)


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Scrapear Idealista con Selenium")
    parser.add_argument("--max-pages", type=int, default=3, help="Máximo páginas a scrapear")
    parser.add_argument("--no-headless", action="store_true", help="Ejecutar con navegador visible")
    parser.add_argument("--no-cache", action="store_true", help="No usar cache HTML")
    parser.add_argument("--restart-driver", action="store_true", 
                       help="Cerrar y reabrir driver entre páginas (menos detectable pero más lento)")
    parser.add_argument("--output", type=str, default=None, help="Archivo CSV de salida")
    args = parser.parse_args()
    
    # Scrapear según metodología del tutorial
    df = scrape_idealista_gracia(
        max_pages=args.max_pages, 
        headless=not args.no_headless,
        use_cache=not args.no_cache,
        restart_driver_per_page=args.restart_driver
    )
    
    if df.empty:
        logger.error("❌ No se pudieron extraer propiedades")
        return 1
    
    # Guardar CSV según metodología del tutorial (CSV Export)
    output_path = Path(args.output) if args.output else Path("spike-data-validation/data/processed/fase2/idealista_gracia_selenium.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Estructurar columnas según tutorial: precio, localidad, tamanio, habitaciones, descripcion, link
    df_final = df.copy()
    
    # Renombrar columnas para coincidir con formato del tutorial
    column_mapping = {
        'superficie_m2': 'tamanio',
        'descripcion': 'descripcion',
        'link': 'link',
        'precio': 'precio',
        'localidad': 'localidad',
        'habitaciones': 'habitaciones'
    }
    
    # Seleccionar y renombrar columnas
    columns_to_keep = ['precio', 'localidad', 'superficie_m2', 'habitaciones', 'descripcion', 'link']
    df_final = df_final[[col for col in columns_to_keep if col in df_final.columns]]
    df_final = df_final.rename(columns={'superficie_m2': 'tamanio'})
    
    df_final.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info(f"📄 CSV guardado (formato tutorial): {output_path}")
    logger.info(f"   Propiedades: {len(df_final)}")
    logger.info(f"   Columnas: {', '.join(df_final.columns)}")
    
    # Estadísticas básicas
    if 'precio' in df.columns:
        prices = df['precio'].dropna()
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

