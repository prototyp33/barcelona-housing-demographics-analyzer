"""Transformaciones ETL modulares para dimensiones, hechos y enriquecimientos.

Este paquete agrupa la lógica que antes vivía en ``src/data_processing.py`` en
módulos más pequeños y cohesionados. Se mantiene una fachada de compatibilidad
en ``src/data_processing.py`` que reexporta las funciones públicas.
"""

from __future__ import annotations

from .dimensions import prepare_dim_barrios
from .demographics import (
    enrich_fact_demografia,
    prepare_demografia_ampliada,
    prepare_fact_demografia,
)
from .market import prepare_fact_precios, prepare_renta_barrio
from .enrichment import prepare_idealista_oferta, prepare_portaldades_precios

__all__ = [
    "prepare_dim_barrios",
    "prepare_fact_demografia",
    "enrich_fact_demografia",
    "prepare_demografia_ampliada",
    "prepare_fact_precios",
    "prepare_renta_barrio",
    "prepare_portaldades_precios",
    "prepare_idealista_oferta",
]


