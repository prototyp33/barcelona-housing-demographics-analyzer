"""Fachada de compatibilidad para transformaciones ETL.

Este módulo existía originalmente como un archivo monolítico con toda la lógica
de limpieza y transformación para el ETL. Para mejorar la mantenibilidad, la
lógica se ha movido a módulos más pequeños dentro de ``src.etl.transformations``.

Para no romper código existente, este archivo actúa ahora como *facade* que
reemite las funciones públicas originales desde el nuevo paquete modular.
"""

from __future__ import annotations

from src.etl.transformations.dimensions import prepare_dim_barrios
from src.etl.transformations.demographics import (
    enrich_fact_demografia,
    prepare_demografia_ampliada,
    prepare_fact_demografia,
)
from src.etl.transformations.enrichment import (
    prepare_idealista_oferta,
    prepare_portaldades_precios,
)
from src.etl.transformations.market import (
    load_idescat_income,
    prepare_fact_precios,
    prepare_renta_barrio,
)


__all__ = [
    # Dimensiones
    "prepare_dim_barrios",
    # Demografía
    "prepare_fact_demografia",
    "enrich_fact_demografia",
    "prepare_demografia_ampliada",
    # Mercado
    "prepare_fact_precios",
    "prepare_renta_barrio",
    "load_idescat_income",

    # Enriquecimientos de mercado
    "prepare_portaldades_precios",
    "prepare_idealista_oferta",
]


