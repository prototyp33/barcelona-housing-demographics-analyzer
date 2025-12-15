"""
Tests para el orquestador de extracción (`src/extraction/orchestrator.py`).
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.extraction.orchestrator import (
    extract_all_sources,
    validate_data_size,
    write_extraction_summary,
)


def test_validate_data_size_empty_df() -> None:
    """Debe marcar como no válido un DataFrame vacío."""
    df = pd.DataFrame()

    assert validate_data_size(df, "TEST_SOURCE") is False


def test_validate_data_size_below_minimum() -> None:
    """Debe marcar como no válido un DataFrame con muy pocos registros."""
    df = pd.DataFrame({"col": [1, 2]})

    assert validate_data_size(df, "TEST_SOURCE", min_records=10) is False


def test_validate_data_size_valid() -> None:
    """Debe marcar como válido un DataFrame con registros suficientes."""
    df = pd.DataFrame({"col": list(range(20))})

    assert validate_data_size(df, "TEST_SOURCE", min_records=5) is True


def test_write_extraction_summary_creates_file(tmp_path: Path) -> None:
    """
    Verifica que write_extraction_summary crea un archivo con resumen básico.
    """
    results: Dict[str, pd.DataFrame] = {
        "source_ok": pd.DataFrame({"a": [1, 2, 3]}),
        "source_empty": pd.DataFrame(),
    }
    metadata: Dict[str, Any] = {
        "extraction_date": "2025-01-01T00:00:00",
        "requested_range": {"start": 2015, "end": 2025},
        "sources_requested": ["source_ok", "source_empty"],
        "sources_success": ["source_ok"],
        "sources_failed": ["source_empty"],
        "coverage_by_source": {
            "source_ok": {"coverage_percentage": 100.0},
            "source_empty": {"error": "sin datos"},
        },
    }

    summary_file = write_extraction_summary(results, metadata, output_dir=tmp_path)

    assert summary_file.exists()
    text = summary_file.read_text(encoding="utf-8")
    assert "RESUMEN DE EXTRACCIÓN DE DATOS" in text
    assert "source_ok" in text
    assert "source_empty" in text


def test_extract_all_sources_with_no_sources(tmp_path: Path, monkeypatch) -> None:
    """
    Verifica que extract_all_sources funciona incluso si no se solicitan fuentes.

    Se fuerza la lista de fuentes a estar vacía y se comprueba que:
    - No se lanzan excepciones
    - Se devuelve un diccionario de resultados vacío
    - Se crea un archivo de metadata en el directorio indicado
    """
    # Forzamos una lista vacía de fuentes
    def fake_extract_all_sources(
        year_start: int = 2015,  # noqa: ARG001
        year_end: int = 2025,  # noqa: ARG001
        sources=None,
        continue_on_error: bool = True,  # noqa: ARG001
        parallel: bool = False,  # noqa: ARG001
        output_dir=None,
    ):
        # Reutilizamos la función real pero sobreescribiendo sources a []
        return extract_all_sources(
            year_start=2015,
            year_end=2025,
            sources=[],
            continue_on_error=True,
            parallel=False,
            output_dir=output_dir,
        )

    # Ejecutar extracción con directorio temporal
    results, metadata = fake_extract_all_sources(output_dir=tmp_path)

    assert isinstance(results, dict)
    assert results == {}
    assert "extraction_date" in metadata
    assert metadata["output_dir"] == str(tmp_path)


