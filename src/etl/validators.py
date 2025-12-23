"""
Validación de Integridad Referencial y Manejo de Errores para el ETL Pipeline.

Este módulo proporciona:
1. Funciones para validar foreign keys antes de insertar datos
2. Clasificación de fuentes de datos como críticas vs opcionales
3. Helpers para manejo consistente de errores según criticidad

Uso típico:
    from src.etl.validators import (
        validate_foreign_keys,
        FKValidationError,
        handle_source_error,
        is_critical_source,
    )

    # Validar FK antes de insertar
    fact_precios_valid = validate_foreign_keys(
        df=fact_precios,
        fk_column="barrio_id",
        reference_df=dim_barrios,
        pk_column="barrio_id",
        table_name="fact_precios",
        strategy="filter",
    )

    # Manejar error según criticidad de la fuente
    try:
        data = extract_source("idealista")
    except Exception as e:
        handle_source_error("idealista", e)  # Solo log si es opcional
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, List, Optional, Set, Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# CLASIFICACIÓN DE FUENTES DE DATOS
# =============================================================================

# Fuentes críticas: si fallan, el pipeline debe detenerse
CRITICAL_SOURCES: FrozenSet[str] = frozenset({
    "dim_barrios",
    "demographics",
    "demographics_ampliada",
    "opendatabcn",
})

# Fuentes opcionales: si fallan, el pipeline continúa con advertencia
OPTIONAL_SOURCES: FrozenSet[str] = frozenset({
    "idealista",
    "portaldades",
    "renta",
    "idescat",
    "incasol",
    "geojson",
})


class SourceError(Exception):
    """Excepción base para errores de fuentes de datos."""

    def __init__(
        self,
        source_name: str,
        message: str,
        original_error: Optional[Exception] = None,
    ) -> None:
        """
        Inicializa la excepción.

        Args:
            source_name: Nombre de la fuente que falló.
            message: Mensaje descriptivo del error.
            original_error: Excepción original (si existe).
        """
        self.source_name = source_name
        self.original_error = original_error
        super().__init__(f"[{source_name}] {message}")


class CriticalSourceError(SourceError):
    """Excepción para errores en fuentes críticas que detienen el pipeline."""

    pass


def is_critical_source(source_name: str) -> bool:
    """
    Determina si una fuente es crítica para el pipeline.

    Args:
        source_name: Nombre de la fuente a verificar.

    Returns:
        True si la fuente es crítica, False si es opcional.

    Example:
        >>> is_critical_source("demographics")
        True
        >>> is_critical_source("idealista")
        False
    """
    # Normalizar nombre (lowercase, sin prefijos comunes)
    normalized = source_name.lower().replace("opendatabcn_", "").replace("_df", "")
    return normalized in CRITICAL_SOURCES or any(
        critical in normalized for critical in CRITICAL_SOURCES
    )


def handle_source_error(
    source_name: str,
    error: Exception,
    context: Optional[str] = None,
    raise_if_critical: bool = True,
) -> None:
    """
    Maneja un error según la criticidad de la fuente.

    Para fuentes críticas: log error y re-raise.
    Para fuentes opcionales: log warning y continuar.

    Args:
        source_name: Nombre de la fuente que falló.
        error: Excepción capturada.
        context: Contexto adicional para el mensaje (opcional).
        raise_if_critical: Si True, re-raise para fuentes críticas.

    Raises:
        CriticalSourceError: Si la fuente es crítica y raise_if_critical=True.

    Example:
        >>> try:
        ...     data = load_idealista()
        >>> except Exception as e:
        ...     handle_source_error("idealista", e)  # Solo log warning
    """
    ctx_msg = f" ({context})" if context else ""
    is_critical = is_critical_source(source_name)

    if is_critical:
        logger.error(
            "❌ Error CRÍTICO en fuente '%s'%s: %s",
            source_name,
            ctx_msg,
            error,
            exc_info=True,
        )
        if raise_if_critical:
            raise CriticalSourceError(
                source_name=source_name,
                message=f"Fuente crítica falló{ctx_msg}: {error}",
                original_error=error,
            ) from error
    else:
        logger.warning(
            "⚠ Error en fuente opcional '%s'%s: %s (continuando pipeline)",
            source_name,
            ctx_msg,
            error,
        )


# =============================================================================
# VALIDACIÓN DE FOREIGN KEYS
# =============================================================================


class FKValidationStrategy(Enum):
    """Estrategia de validación de foreign keys."""

    STRICT = "strict"  # Falla si hay FK inválidos
    FILTER = "filter"  # Filtra registros con FK inválidos
    WARN = "warn"  # Solo advierte, no modifica datos


class FKValidationError(Exception):
    """Excepción lanzada cuando la validación FK falla en modo strict."""

    def __init__(
        self,
        message: str,
        table_name: str,
        invalid_keys: Set[int],
        total_invalid: int,
    ) -> None:
        """
        Inicializa la excepción con contexto detallado.

        Args:
            message: Mensaje descriptivo del error.
            table_name: Nombre de la tabla donde se detectó el problema.
            invalid_keys: Conjunto de claves foráneas inválidas.
            total_invalid: Número total de registros afectados.
        """
        super().__init__(message)
        self.table_name = table_name
        self.invalid_keys = invalid_keys
        self.total_invalid = total_invalid


@dataclass
class FKValidationResult:
    """Resultado de una validación de foreign keys."""

    table_name: str
    fk_column: str
    total_records: int
    valid_records: int
    invalid_records: int
    invalid_keys: Set[int] = field(default_factory=set)
    strategy_applied: FKValidationStrategy = FKValidationStrategy.STRICT
    filtered_df: Optional[pd.DataFrame] = None

    @property
    def is_valid(self) -> bool:
        """Retorna True si todos los registros tienen FK válidos."""
        return self.invalid_records == 0

    @property
    def pct_invalid(self) -> float:
        """Porcentaje de registros inválidos."""
        if self.total_records == 0:
            return 0.0
        return (self.invalid_records / self.total_records) * 100

    def __str__(self) -> str:
        """Representación legible del resultado."""
        status = "✓ VÁLIDO" if self.is_valid else "⚠ INVÁLIDO"
        return (
            f"FK Validation [{self.table_name}.{self.fk_column}]: {status}\n"
            f"  Total: {self.total_records:,} | "
            f"Válidos: {self.valid_records:,} | "
            f"Inválidos: {self.invalid_records:,} ({self.pct_invalid:.1f}%)"
        )


def validate_foreign_keys(
    df: pd.DataFrame,
    fk_column: str,
    reference_df: pd.DataFrame,
    pk_column: str,
    table_name: str,
    strategy: Union[str, FKValidationStrategy] = FKValidationStrategy.FILTER,
) -> Tuple[pd.DataFrame, FKValidationResult]:
    """
    Valida que todos los valores de una columna FK existan en la tabla de referencia.

    Esta función verifica la integridad referencial antes de insertar datos en la
    base de datos, evitando errores de FK y registros huérfanos.

    Args:
        df: DataFrame con los datos a validar.
        fk_column: Nombre de la columna que contiene la foreign key.
        reference_df: DataFrame de referencia (tabla padre).
        pk_column: Nombre de la columna PK en la tabla de referencia.
        table_name: Nombre de la tabla (para logging y errores).
        strategy: Estrategia de validación:
            - "strict": Lanza FKValidationError si hay FK inválidos.
            - "filter": Filtra registros con FK inválidos (por defecto).
            - "warn": Solo advierte, retorna el DataFrame sin modificar.

    Returns:
        Tupla (DataFrame validado/filtrado, FKValidationResult con estadísticas).

    Raises:
        FKValidationError: Si strategy="strict" y hay FK inválidos.
        ValueError: Si las columnas especificadas no existen.

    Example:
        >>> fact_precios, result = validate_foreign_keys(
        ...     df=fact_precios,
        ...     fk_column="barrio_id",
        ...     reference_df=dim_barrios,
        ...     pk_column="barrio_id",
        ...     table_name="fact_precios",
        ...     strategy="filter"
        ... )
        >>> print(result)
        FK Validation [fact_precios.barrio_id]: ✓ VÁLIDO
          Total: 1,000 | Válidos: 1,000 | Inválidos: 0 (0.0%)
    """
    # Normalizar strategy a enum
    if isinstance(strategy, str):
        strategy = FKValidationStrategy(strategy.lower())

    # Validar que las columnas existen
    if fk_column not in df.columns:
        raise ValueError(
            f"Columna FK '{fk_column}' no existe en DataFrame. "
            f"Columnas disponibles: {list(df.columns)}"
        )
    if pk_column not in reference_df.columns:
        raise ValueError(
            f"Columna PK '{pk_column}' no existe en DataFrame de referencia. "
            f"Columnas disponibles: {list(reference_df.columns)}"
        )

    # Manejar DataFrame vacío
    if df.empty:
        logger.debug("DataFrame %s vacío, nada que validar", table_name)
        return df.copy(), FKValidationResult(
            table_name=table_name,
            fk_column=fk_column,
            total_records=0,
            valid_records=0,
            invalid_records=0,
            invalid_keys=set(),
            strategy_applied=strategy,
            filtered_df=df.copy(),
        )

    # Obtener conjunto de PKs válidos
    valid_pks: Set[int] = set(reference_df[pk_column].dropna().unique())

    # Obtener valores FK del DataFrame
    fk_values = df[fk_column].dropna()

    # Encontrar FKs inválidos
    invalid_mask = ~df[fk_column].isin(valid_pks) & df[fk_column].notna()
    invalid_keys: Set[int] = set(df.loc[invalid_mask, fk_column].unique())
    invalid_count = invalid_mask.sum()

    total_records = len(df)
    valid_count = total_records - invalid_count

    result = FKValidationResult(
        table_name=table_name,
        fk_column=fk_column,
        total_records=total_records,
        valid_records=valid_count,
        invalid_records=invalid_count,
        invalid_keys=invalid_keys,
        strategy_applied=strategy,
    )

    # Logging según resultado
    if result.is_valid:
        logger.info(
            "✓ Validación FK %s.%s: %s registros válidos",
            table_name,
            fk_column,
            total_records,
        )
    else:
        # Mostrar los primeros valores inválidos para debugging
        sample_invalid = sorted(list(invalid_keys))[:5]
        sample_str = ", ".join(str(k) for k in sample_invalid)
        if len(invalid_keys) > 5:
            sample_str += f"... (+{len(invalid_keys) - 5} más)"

        log_msg = (
            f"⚠ Validación FK {table_name}.{fk_column}: "
            f"{invalid_count:,} registros con FK inválidos ({result.pct_invalid:.1f}%). "
            f"Claves inválidas: [{sample_str}]"
        )

        if strategy == FKValidationStrategy.STRICT:
            logger.error(log_msg)
            raise FKValidationError(
                message=(
                    f"Integridad referencial violada en {table_name}.{fk_column}: "
                    f"{invalid_count:,} registros tienen FK que no existen en la tabla padre. "
                    f"Claves inválidas: {sample_invalid}"
                ),
                table_name=table_name,
                invalid_keys=invalid_keys,
                total_invalid=invalid_count,
            )
        elif strategy == FKValidationStrategy.FILTER:
            logger.warning(log_msg + " [FILTRANDO]")
            df = df[~invalid_mask].copy()
            result.filtered_df = df
        else:  # WARN
            logger.warning(log_msg + " [SIN ACCIÓN]")

    if result.filtered_df is None:
        result.filtered_df = df.copy()

    return result.filtered_df, result


def validate_all_fact_tables(
    dim_barrios: pd.DataFrame,
    fact_precios: Optional[pd.DataFrame] = None,
    fact_demografia: Optional[pd.DataFrame] = None,
    fact_demografia_ampliada: Optional[pd.DataFrame] = None,
    fact_renta: Optional[pd.DataFrame] = None,
    fact_oferta_idealista: Optional[pd.DataFrame] = None,
    fact_regulacion: Optional[pd.DataFrame] = None,
    fact_presion_turistica: Optional[pd.DataFrame] = None,
    fact_seguridad: Optional[pd.DataFrame] = None,
    fact_ruido: Optional[pd.DataFrame] = None,
    strategy: Union[str, FKValidationStrategy] = FKValidationStrategy.FILTER,
) -> Tuple[
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    Optional[pd.DataFrame],
    List[FKValidationResult],
]:
    """
    Valida todas las tablas de hechos contra dim_barrios.

    Esta es una función conveniente que valida todas las fact tables de una vez,
    aplicando la misma estrategia a todas.

    Args:
        dim_barrios: DataFrame con la dimensión de barrios (tabla padre).
        fact_precios: DataFrame de precios (opcional).
        fact_demografia: DataFrame de demografía (opcional).
        fact_demografia_ampliada: DataFrame de demografía ampliada (opcional).
        fact_renta: DataFrame de renta (opcional).
        fact_oferta_idealista: DataFrame de oferta Idealista (opcional).
        fact_regulacion: DataFrame de regulación (opcional).
        fact_presion_turistica: DataFrame de presión turística (opcional).
        fact_seguridad: DataFrame de seguridad (opcional).
        fact_ruido: DataFrame de ruido (opcional).
        strategy: Estrategia de validación a aplicar.

        Returns:
            Tupla con:
            - fact_precios validado (o None si era None)
            - fact_demografia validado (o None si era None)
            - fact_demografia_ampliada validado (o None si era None)
            - fact_renta validado (o None si era None)
            - fact_oferta_idealista validado (o None si era None)
            - fact_regulacion validado (o None si era None)
            - Lista de FKValidationResult con estadísticas de cada tabla

    Example:
        >>> (
        ...     fact_precios,
        ...     fact_demo,
        ...     fact_demo_amp,
        ...     fact_renta,
        ...     fact_oferta,
        ...     results
        ... ) = validate_all_fact_tables(
        ...     dim_barrios=dim_barrios,
        ...     fact_precios=fact_precios,
        ...     strategy="filter"
        ... )
        >>> for r in results:
        ...     print(r)
    """
    results: List[FKValidationResult] = []

    # Validar fact_precios
    if fact_precios is not None and not fact_precios.empty:
        fact_precios, result = validate_foreign_keys(
            df=fact_precios,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_precios",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_demografia
    if fact_demografia is not None and not fact_demografia.empty:
        fact_demografia, result = validate_foreign_keys(
            df=fact_demografia,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_demografia",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_demografia_ampliada
    if fact_demografia_ampliada is not None and not fact_demografia_ampliada.empty:
        fact_demografia_ampliada, result = validate_foreign_keys(
            df=fact_demografia_ampliada,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_demografia_ampliada",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_renta
    if fact_renta is not None and not fact_renta.empty:
        fact_renta, result = validate_foreign_keys(
            df=fact_renta,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_renta",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_oferta_idealista
    if fact_oferta_idealista is not None and not fact_oferta_idealista.empty:
        fact_oferta_idealista, result = validate_foreign_keys(
            df=fact_oferta_idealista,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_oferta_idealista",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_regulacion
    if fact_regulacion is not None and not fact_regulacion.empty:
        fact_regulacion, result = validate_foreign_keys(
            df=fact_regulacion,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_regulacion",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_presion_turistica
    if fact_presion_turistica is not None and not fact_presion_turistica.empty:
        fact_presion_turistica, result = validate_foreign_keys(
            df=fact_presion_turistica,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_presion_turistica",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_seguridad
    if fact_seguridad is not None and not fact_seguridad.empty:
        fact_seguridad, result = validate_foreign_keys(
            df=fact_seguridad,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_seguridad",
            strategy=strategy,
        )
        results.append(result)

    # Validar fact_ruido
    if fact_ruido is not None and not fact_ruido.empty:
        fact_ruido, result = validate_foreign_keys(
            df=fact_ruido,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_ruido",
            strategy=strategy,
        )
        results.append(result)

    # Resumen de validación
    if results:
        total_invalid = sum(r.invalid_records for r in results)
        total_records = sum(r.total_records for r in results)
        if total_invalid > 0:
            logger.warning(
                "Resumen validación FK: %s/%s registros inválidos en %s tablas",
                total_invalid,
                total_records,
                len(results),
            )
        else:
            logger.info(
                "✓ Validación FK completada: %s registros válidos en %s tablas",
                total_records,
                len(results),
            )

    return (
        fact_precios,
        fact_demografia,
        fact_demografia_ampliada,
        fact_renta,
        fact_oferta_idealista,
        fact_regulacion,
        fact_presion_turistica,
        fact_seguridad,
        fact_ruido,
        results,
    )


__all__ = [
    # Clasificación de fuentes
    "CRITICAL_SOURCES",
    "OPTIONAL_SOURCES",
    "SourceError",
    "CriticalSourceError",
    "is_critical_source",
    "handle_source_error",
    # Validación FK
    "FKValidationStrategy",
    "FKValidationError",
    "FKValidationResult",
    "validate_foreign_keys",
    "validate_all_fact_tables",
]

