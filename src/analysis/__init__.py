"""Módulos de análisis avanzados (fase 2+).

Actualmente expone utilidades relacionadas con la segmentación de mercado
K-Means en barrios de Barcelona.
"""

from .market_segmentation import (  # noqa: F401
    SubmarketMetadata,
    assign_submarket,
    build_submarket_mapping,
)


