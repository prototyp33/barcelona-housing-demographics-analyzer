"""
Extraction Package - Módulos para extracción de datos de múltiples fuentes.

Este paquete contiene extractores especializados para cada fuente de datos:
- INE: Instituto Nacional de Estadística
- OpenData BCN: Datos abiertos del Ayuntamiento de Barcelona
- Idealista: Precios de vivienda (API)
- PortalDades: Portal de Dades de Barcelona
"""

from .base import (
    BaseExtractor,
    setup_logging,
    DATA_RAW_DIR,
    LOGS_DIR,
    EXTRACTION_LOGS_DIR,
    MIN_RECORDS_WARNING,
    logger,
)
from .ine import INEExtractor
from .opendata import OpenDataBCNExtractor
from .idealista import IdealistaExtractor
from .portaldades import PortalDadesExtractor
from .orchestrator import extract_all_sources, write_extraction_summary

__all__ = [
    # Base
    "BaseExtractor",
    "setup_logging",
    "DATA_RAW_DIR",
    "LOGS_DIR",
    "EXTRACTION_LOGS_DIR",
    "MIN_RECORDS_WARNING",
    "logger",
    # Extractors
    "INEExtractor",
    "OpenDataBCNExtractor",
    "IdealistaExtractor",
    "PortalDadesExtractor",
    # Orchestration
    "extract_all_sources",
    "write_extraction_summary",
]

