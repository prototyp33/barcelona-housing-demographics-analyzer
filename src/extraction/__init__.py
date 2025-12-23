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
from .idescat import IDESCATExtractor
from .incasol import IncasolSocrataExtractor
from .generalitat_extractor import GeneralitatExtractor
from .airbnb_extractor import AirbnbExtractor
from .icgc_extractor import ICGCExtractor
from .ruido_extractor import RuidoExtractor
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
    "IDESCATExtractor",
    "IncasolSocrataExtractor",
    "GeneralitatExtractor",
    "AirbnbExtractor",
    "ICGCExtractor",
    "RuidoExtractor",
    # Orchestration
    "extract_all_sources",
    "write_extraction_summary",
]

