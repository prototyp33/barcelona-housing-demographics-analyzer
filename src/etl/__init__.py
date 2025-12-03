from .pipeline import run_etl
from .validators import (
    # Clasificación de fuentes
    CRITICAL_SOURCES,
    OPTIONAL_SOURCES,
    CriticalSourceError,
    SourceError,
    handle_source_error,
    is_critical_source,
    # Validación FK
    FKValidationError,
    FKValidationResult,
    FKValidationStrategy,
    validate_all_fact_tables,
    validate_foreign_keys,
)

__all__ = [
    "run_etl",
    # Clasificación de fuentes y manejo de errores
    "CRITICAL_SOURCES",
    "OPTIONAL_SOURCES",
    "SourceError",
    "CriticalSourceError",
    "is_critical_source",
    "handle_source_error",
    # Validadores de integridad referencial
    "FKValidationError",
    "FKValidationResult",
    "FKValidationStrategy",
    "validate_foreign_keys",
    "validate_all_fact_tables",
]
