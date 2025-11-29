"""
PortalDades Extractor Module - Extracción de datos del Portal de Dades de Barcelona.
"""

import csv
import os
import re
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .base import BaseExtractor, logger

# Playwright import (opcional, solo si está disponible)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class PortalDadesExtractor(BaseExtractor):
    """
    Extractor para el Portal de Dades de Barcelona usando Playwright y API con Client ID.
    
    Este extractor:
    1. Usa Playwright para hacer scraping del portal (navegación JavaScript)
    2. Extrae IDs de indicadores del tema "Habitatge"
    3. Descarga datos usando la API con Client ID proporcionado
    
    Requiere la variable de entorno PORTALDADES_CLIENT_ID para autenticación con la API.
    """
    
    BASE_URL = "https://portaldades.ajuntament.barcelona.cat"
    API_EXPORT_URL = f"{BASE_URL}/services/backend/rest/statistic/export"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        rate_limit_delay: float = 2.0,
        output_dir: Optional[Path] = None
    ):
        """
        Inicializa el extractor del Portal de Dades.
        
        Args:
            client_id: Client ID para la API (por defecto lee de PORTALDADES_CLIENT_ID)
            rate_limit_delay: Tiempo de espera entre peticiones
            output_dir: Directorio donde guardar los datos
        """
        super().__init__("PortalDades", rate_limit_delay, output_dir)
        
        # Obtener Client ID de parámetro o variable de entorno
        self.client_id = client_id or os.getenv("PORTALDADES_CLIENT_ID")
        if not self.client_id:
            logger.warning(
                "PORTALDADES_CLIENT_ID no encontrado. "
                "Configura la variable de entorno o pasa client_id al constructor."
            )
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning(
                "Playwright no está disponible. "
                "Instala con: pip install playwright && playwright install"
            )
        
        # Headers para la API
        self.api_headers = {
            "X-IBM-Client-Id": self.client_id or ""
        }
    
    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normaliza un título para usarlo como nombre de archivo."""
        if not title:
            return ""
        normalized = unicodedata.normalize("NFKD", title)
        normalized = normalized.encode("ascii", "ignore").decode("utf-8")
        normalized = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
        normalized = re.sub(r"[-\s]+", "_", normalized)
        return normalized
    
    def scrape_indicadores_habitatge(
        self,
        start_url: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Extrae metadatos de indicadores del tema "Habitatge" usando la API REST.
        
        Solo extrae datasets de tipo "Taula estadística" (source=STATISTICS), ignorando otros tipos
        como "Micodada", "Data Stories", "Enquesta", "Document", "Mapa", etc.
        
        Args:
            start_url: Ignorado (se usa la API REST directamente)
            max_pages: Número máximo de páginas a recorrer (None = todas)
            
        Returns:
            Lista de diccionarios con metadatos del indicador (solo "Taula estadística")
        """
        API_SEARCH_URL = f"{self.BASE_URL}/services/backend/rest/search"
        ROWS_PER_PAGE = 10
        
        logger.info("Extrayendo indicadores del Portal de Dades usando API REST")
        
        indicadores: List[Dict[str, str]] = []
        page_number = 1
        start = 0
        
        try:
            # Primera petición para obtener el total
            params = {
                "query": "",
                "start": 0,
                "rows": ROWS_PER_PAGE,
                "language": "ca",
                "source": "STATISTICS",
                "thesaurus": "Habitatge"
            }
            
            self._rate_limit()
            response = self.session.get(
                API_SEARCH_URL,
                params=params,
                headers=self.api_headers,
                timeout=60
            )
            
            if not self._validate_response(response):
                logger.error("Error en la primera petición a la API")
                return []
            
            data = response.json()
            total_count = data.get("count", 0)
            logger.info(f"Total de indicadores disponibles: {total_count}")
            
            if total_count == 0:
                logger.warning("No se encontraron indicadores")
                return []
            
            # Calcular número máximo de páginas
            total_pages = (total_count + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
            if max_pages:
                total_pages = min(total_pages, max_pages)
            
            logger.info(f"Procesando {total_pages} páginas (máximo {max_pages if max_pages else 'todas'})")
            
            # Procesar todas las páginas
            while start < total_count:
                if max_pages and page_number > max_pages:
                    logger.info(f"Límite de páginas alcanzado ({max_pages})")
                    break
                
                params["start"] = start
                self._rate_limit()
                
                try:
                    response = self.session.get(
                        API_SEARCH_URL,
                        params=params,
                        headers=self.api_headers,
                        timeout=60
                    )
                    
                    if not self._validate_response(response):
                        logger.warning(f"Error en la petición de la página {page_number}")
                        break
                    
                    data = response.json()
                    items = data.get("data", [])
                    
                    if not items:
                        logger.info(f"No hay más items en la página {page_number}")
                        break
                    
                    nuevos_en_pagina = 0
                    for item in items:
                        id_indicador = item.get("id")
                        if not id_indicador:
                            continue
                        
                        # Extraer metadatos
                        nombre = item.get("title", "Título no disponible")
                        descripcion = item.get("description", "")
                        doc_source = item.get("docSource", [])
                        origen_texto = ", ".join(doc_source) if doc_source else ""
                        publish_date = item.get("publishDate", "")
                        
                        # Formatear fecha
                        fecha_texto = ""
                        if publish_date:
                            try:
                                from datetime import datetime as dt
                                dt_obj = dt.fromisoformat(publish_date.replace("Z", "+00:00"))
                                fecha_texto = dt_obj.strftime("%d/%m/%Y")
                            except Exception:
                                fecha_texto = publish_date[:10] if len(publish_date) >= 10 else publish_date
                        
                        nombre_limpio = self._normalize_title(nombre)
                        detalle_url = f"{self.BASE_URL}/estadístiques/{id_indicador}"
                        
                        metadata = {
                            "id_indicador": id_indicador,
                            "nombre": nombre,
                            "nombre_limpio": nombre_limpio,
                            "descripcion": descripcion,
                            "fecha": fecha_texto,
                            "origen": origen_texto,
                            "tipo": "Taula estadística",
                            "categoria": "estadístiques",
                            "detalle_url": detalle_url
                        }
                        
                        indicadores.append(metadata)
                        nuevos_en_pagina += 1
                        logger.debug("Nuevo indicador: %s - %s", id_indicador, nombre[:80])
                    
                    logger.info(
                        "Página %s (start=%s): %s indicadores encontrados (total acumulado: %s)",
                        page_number,
                        start,
                        nuevos_en_pagina,
                        len(indicadores)
                    )
                    
                    start += ROWS_PER_PAGE
                    page_number += 1
                    
                except Exception as e:
                    logger.error(f"Error procesando página {page_number}: {e}")
                    logger.debug(traceback.format_exc())
                    break
                    
        except Exception as e:
            logger.error(f"Error durante la extracción: {e}")
            logger.debug(traceback.format_exc())
        
        logger.info(
            f"Total de indicadores 'Taula estadística' extraídos: {len(indicadores)}"
        )
        return indicadores
    
    def descargar_indicador(
        self,
        id_indicador: str,
        nombre: str,
        formato: str = "CSV"
    ) -> Optional[Path]:
        """
        Descarga un indicador específico usando la API con Client ID.
        
        Args:
            id_indicador: ID del indicador
            nombre: Nombre descriptivo (para el archivo)
            formato: Formato de descarga ("CSV" o "Excel")
            
        Returns:
            Path del archivo descargado o None
        """
        self._rate_limit()
        
        params = {
            "id": id_indicador,
            "fileformat": formato
        }
        
        try:
            response = self.session.get(
                self.API_EXPORT_URL,
                params=params,
                headers=self.api_headers,
                timeout=60
            )
            
            if not self._validate_response(response):
                return None
            
            # Normalizar nombre del archivo
            nombre_limpio = re.sub(r'[^\w\s-]', '', nombre).strip()
            nombre_limpio = re.sub(r'[-\s]+', '_', nombre_limpio)
            
            extension = formato.lower()
            if extension == "excel":
                extension = "xlsx"
            
            filename = f"portaldades_{nombre_limpio}_{id_indicador}.{extension}"
            filepath = self.output_dir / "portaldades" / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Descargado: {filename}")
            
            # Registrar en manifest
            # Inferir tipo de datos basándose en el nombre
            data_type = self._infer_portaldades_type(nombre_limpio)
            self._append_to_manifest(
                file_path=filepath,
                source="portaldades",
                data_type=data_type,
            )
            
            return filepath
        
        except Exception as e:
            logger.error(f"Error descargando indicador {id_indicador}: {e}")
            return None
    
    @staticmethod
    def _infer_portaldades_type(nombre: str) -> str:
        """
        Infiere el tipo de datos de un indicador de PortalDades.
        
        Args:
            nombre: Nombre normalizado del indicador
            
        Returns:
            Tipo de datos inferido
        """
        nombre_lower = nombre.lower()
        
        # Patrones para clasificación
        if any(p in nombre_lower for p in ["venda", "compravenda", "venta", "habitatge"]):
            if any(p in nombre_lower for p in ["m2", "superficie"]):
                return "prices_venta"
            return "prices_venta"
        elif any(p in nombre_lower for p in ["lloguer", "alquiler", "rent"]):
            return "prices_alquiler"
        elif any(p in nombre_lower for p in ["poblacio", "demografic", "habitants"]):
            return "demographics"
        elif any(p in nombre_lower for p in ["renda", "renta", "income"]):
            return "renta"
        
        return "housing_indicator"
    
    def extraer_y_descargar_habitatge(
        self,
        descargar: bool = True,
        formato: str = "CSV",
        max_pages: Optional[int] = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, Optional[Path]]]:
        """
        Extrae IDs de indicadores y opcionalmente los descarga.
        
        Args:
            descargar: Si True, descarga los indicadores después de extraerlos
            formato: Formato de descarga ("CSV" o "Excel")
            max_pages: Número máximo de páginas a recorrer
            
        Returns:
            Tupla con (lista de metadatos, diccionario de {id: path_descargado})
        """
        indicadores = self.scrape_indicadores_habitatge(max_pages=max_pages)
        
        if not indicadores:
            logger.warning("No se encontraron indicadores")
            return [], {}
        
        # Guardar lista de indicadores con metadatos
        metadata_file = self.output_dir / "portaldades" / "indicadores_habitatge.csv"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            "id_indicador",
            "nombre",
            "nombre_limpio",
            "descripcion",
            "fecha",
            "origen",
            "tipo",
            "categoria",
            "detalle_url"
        ]
        
        with open(metadata_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for indicador in indicadores:
                writer.writerow({k: indicador.get(k, "") for k in fieldnames})
        
        logger.info(f"Lista de indicadores guardada en: {metadata_file}")
        
        # Descargar si se solicita
        archivos_descargados: Dict[str, Optional[Path]] = {}
        
        if descargar:
            logger.info(f"Descargando {len(indicadores)} indicadores en formato {formato}...")
            for i, indicador in enumerate(indicadores, 1):
                id_indicador = indicador.get("id_indicador")
                nombre = indicador.get("nombre") or id_indicador
                logger.info(f"[{i}/{len(indicadores)}] Descargando: {nombre[:80]}...")
                path = self.descargar_indicador(id_indicador, nombre, formato)
                archivos_descargados[id_indicador] = path
        
        return indicadores, archivos_descargados
    
    @staticmethod
    def _accept_cookies(page) -> None:
        """Intenta aceptar el banner de cookies si aparece."""
        cookie_selectors = [
            "button.lw-consent-accept",
            "button[aria-label='Accept all cookies']",
            "#lw-banner button.lw-consent-accept",
        ]
        for selector in cookie_selectors:
            try:
                button = page.locator(selector)
                if button.count() > 0 and button.is_visible():
                    button.click()
                    page.wait_for_timeout(500)
                    logger.debug("Banner de cookies aceptado (%s)", selector)
                    break
            except Exception:
                continue
    
    @staticmethod
    def _scroll_to_load_more(page, pause_ms: int = 1500) -> None:
        """Realiza un scroll hasta el final de la página para disparar la carga incremental."""
        try:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        except Exception:
            logger.debug("No se pudo ejecutar scroll mediante evaluate, usando mouse.wheel")
            try:
                page.mouse.wheel(0, 2000)
            except Exception:
                logger.debug("No se pudo realizar scroll con mouse.wheel")
        page.wait_for_timeout(pause_ms)

