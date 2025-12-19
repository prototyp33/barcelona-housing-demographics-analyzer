"""
Cliente ligero para la API de catastro-api.es usado en el spike de Gràcia.

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class CatastroAPIError(Exception):
    """Error de alto nivel para problemas con la API de catastro-api.es."""


@dataclass
class CatastroAPIConfig:
    """
    Configuración para el cliente de catastro-api.es.

    Attributes:
        base_url: URL base de la API.
        api_key: API key para autenticación.
        timeout: Timeout en segundos para peticiones HTTP.
    """

    base_url: str = "https://catastro-api.es/api"
    api_key: Optional[str] = None
    timeout: int = 20


class CatastroAPIClient:
    """
    Cliente mínimo para acceder a catastro-api.es.

    Este cliente se usa únicamente en el contexto del spike para obtener
    atributos de edificios (superficie, año de construcción, plantas, dirección).
    """

    def __init__(self, config: Optional[CatastroAPIConfig] = None) -> None:
        """
        Inicializa el cliente usando ``CATASTRO_API_KEY`` del entorno si es posible.

        Args:
            config: Configuración explícita; si es None, se construye a partir
                de variables de entorno.

        Raises:
            CatastroAPIError: Si no se encuentra la API key.
        """
        if config is None:
            api_key = os.getenv("CATASTRO_API_KEY")
            config = CatastroAPIConfig(api_key=api_key)

        if not config.api_key:
            raise CatastroAPIError(
                "CATASTRO_API_KEY no está configurada en el entorno. "
                "Configura la clave antes de ejecutar el spike.",
            )

        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.config.api_key})

    def get_building_by_rc(self, ref_catastral: str) -> Dict[str, Any]:
        """
        Obtiene información de un inmueble a partir de su referencia catastral.

        Args:
            ref_catastral: Referencia catastral completa (20 caracteres).

        Returns:
            Diccionario con atributos relevantes del inmueble.

        Raises:
            CatastroAPIError: Si la API devuelve un error o el payload es inválido.
        """
        if not ref_catastral:
            raise CatastroAPIError("La referencia catastral está vacía")

        url = f"{self.config.base_url}/rc"
        params = {"rc": ref_catastral}

        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
        except requests.RequestException as exc:
            raise CatastroAPIError(f"Error de red al consultar Catastro API: {exc}") from exc

        if response.status_code >= 400:
            raise CatastroAPIError(
                f"Respuesta HTTP {response.status_code} de Catastro API: {response.text}",
            )

        try:
            payload: Dict[str, Any] = response.json()
        except ValueError as exc:
            raise CatastroAPIError("No se pudo parsear el JSON devuelto por Catastro API") from exc

        # La estructura exacta depende de la API; aquí se asume un formato genérico.
        # Estos campos deben ajustarse a la documentación real de catastro-api.es.
        inmueble: Dict[str, Any] = payload.get("inmueble") or payload

        superficie = inmueble.get("superficie_construida") or inmueble.get("superficie")
        ano_construccion = inmueble.get("ano_construccion") or inmueble.get("anio_construccion")
        plantas = inmueble.get("plantas") or inmueble.get("numero_plantas")

        direccion_info = inmueble.get("direccion") or {}
        direccion_normalizada = " ".join(
            str(part).strip()
            for part in [
                direccion_info.get("via"),
                direccion_info.get("numero"),
                direccion_info.get("escalera"),
                direccion_info.get("planta"),
                direccion_info.get("puerta"),
            ]
            if part
        ).strip()

        result: Dict[str, Any] = {
            "referencia_catastral": ref_catastral,
            "superficie_m2": float(superficie) if superficie is not None else None,
            "ano_construccion": int(ano_construccion) if ano_construccion is not None else None,
            "plantas": int(plantas) if plantas is not None else None,
            "direccion_normalizada": direccion_normalizada or None,
        }

        logger.debug("Respuesta Catastro para %s: %s", ref_catastral, result)
        return result


