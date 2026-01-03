"""Routers package initialization."""

from .barrios import router as barrios_router
from .predictions import router as predictions_router
from .investment import router as investment_router
from .clusters import router as clusters_router
from .stats import router as stats_router

__all__ = [
    "barrios_router",
    "predictions_router",
    "investment_router",
    "clusters_router",
    "stats_router",
]
