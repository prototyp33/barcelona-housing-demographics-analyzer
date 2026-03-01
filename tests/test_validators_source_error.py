"""
Tests para handle_source_error, is_critical_source y excepciones del módulo validators.
"""

import pytest

from src.etl.validators import (
    CriticalSourceError,
    handle_source_error,
    is_critical_source,
)


class TestIsCriticalSource:
    """Tests para is_critical_source."""

    def test_demographics_critical(self) -> None:
        """demographics es fuente crítica."""
        assert is_critical_source("demographics") is True
        assert is_critical_source("opendatabcn_demographics") is True

    def test_dim_barrios_critical(self) -> None:
        """dim_barrios es fuente crítica."""
        assert is_critical_source("dim_barrios") is True

    def test_idealista_optional(self) -> None:
        """idealista es fuente opcional."""
        assert is_critical_source("idealista") is False

    def test_renta_optional(self) -> None:
        """renta es fuente opcional."""
        assert is_critical_source("renta") is False
        assert is_critical_source("renta_historica") is False

    def test_idescat_optional(self) -> None:
        """idescat es fuente opcional."""
        assert is_critical_source("idescat") is False


class TestHandleSourceError:
    """Tests para handle_source_error."""

    def test_critical_source_raises(self) -> None:
        """Fuente crítica debe re-lanzar CriticalSourceError."""
        with pytest.raises(CriticalSourceError) as exc_info:
            handle_source_error(
                "demographics",
                ValueError("Datos no encontrados"),
                raise_if_critical=True,
            )
        assert "demographics" in str(exc_info.value)
        assert exc_info.value.source_name == "demographics"
        assert exc_info.value.original_error is not None

    def test_critical_source_no_raise_when_disabled(self) -> None:
        """Fuente crítica con raise_if_critical=False no debe lanzar."""
        handle_source_error(
            "demographics",
            ValueError("Datos no encontrados"),
            raise_if_critical=False,
        )
        # No lanza, solo log

    def test_optional_source_no_raise(self) -> None:
        """Fuente opcional no debe lanzar."""
        handle_source_error(
            "idealista",
            ValueError("API no disponible"),
            raise_if_critical=True,
        )
        # No lanza, solo log warning

    def test_optional_source_with_context(self) -> None:
        """Fuente opcional con contexto no debe lanzar."""
        handle_source_error(
            "portaldades",
            FileNotFoundError("Archivo no encontrado"),
            context="precios 2023",
            raise_if_critical=True,
        )
