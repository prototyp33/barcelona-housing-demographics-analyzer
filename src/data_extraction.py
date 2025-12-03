"""
MÓDULO DEPRECADO - Usa src.extraction en su lugar.

Este módulo se mantiene por compatibilidad con código legacy.
Será eliminado en una versión futura.

Migración recomendada:
    # Antes (DEPRECADO):
    from src.data_extraction import OpenDataBCNExtractor, setup_logging

    # Después (RECOMENDADO):
    from src.extraction import OpenDataBCNExtractor, setup_logging

El módulo modular src.extraction ofrece:
- Mejor organización del código
- Extractores especializados por fuente
- Mejor mantenibilidad y testing
"""

import warnings

# Emitir warning de deprecación al importar
warnings.warn(
    "El módulo 'src.data_extraction' está DEPRECADO y será eliminado en una versión futura. "
    "Usa 'src.extraction' en su lugar. "
    "Ejemplo: from src.extraction import OpenDataBCNExtractor, setup_logging",
    DeprecationWarning,
    stacklevel=2,
)

# Re-exportar todo desde el módulo modular para compatibilidad
from src.extraction import (
    # Base
    BaseExtractor,
    setup_logging,
    DATA_RAW_DIR,
    LOGS_DIR,
    EXTRACTION_LOGS_DIR,
    MIN_RECORDS_WARNING,
    logger,
    # Extractors
    INEExtractor,
    OpenDataBCNExtractor,
    IdealistaExtractor,
    PortalDadesExtractor,
    IDESCATExtractor,
    IncasolSocrataExtractor,
    # Orchestration
    extract_all_sources,
    write_extraction_summary,
)

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
    # Orchestration
    "extract_all_sources",
    "write_extraction_summary",
]

# Mensaje informativo para desarrolladores
_DEPRECATION_NOTICE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  AVISO: Este módulo (src.data_extraction) está DEPRECADO                     ║
║                                                                              ║
║  Migra a: from src.extraction import OpenDataBCNExtractor, setup_logging     ║
║                                                                              ║
║  El código legacy (2,547 líneas) ha sido reemplazado por módulos modulares: ║
║  - src/extraction/base.py       → BaseExtractor, setup_logging              ║
║  - src/extraction/opendata.py   → OpenDataBCNExtractor                       ║
║  - src/extraction/idealista.py  → IdealistaExtractor                         ║
║  - src/extraction/portaldades.py→ PortalDadesExtractor                       ║
║  - src/extraction/ine.py        → INEExtractor                               ║
║  - src/extraction/idescat.py    → IDESCATExtractor                           ║
║  - src/extraction/incasol.py    → IncasolSocrataExtractor                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
