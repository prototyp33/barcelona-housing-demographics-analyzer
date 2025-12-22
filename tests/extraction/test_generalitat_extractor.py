from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.extraction.generalitat_extractor import GeneralitatExtractor


class DummyResponse:
    """Respuesta simulada para requests.Session.get."""

    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> Any:
        return self._payload


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Directorio temporal para archivos raw."""
    return tmp_path / "data" / "raw"


def test_extract_indice_referencia_happy_path(monkeypatch, output_dir: Path) -> None:
    """Debe combinar datos de varios años y guardar un CSV en manifest."""
    # Datos simulados por año
    responses_by_year: Dict[int, List[Dict[str, Any]]] = {
        2024: [
            {"codi_barri": "01", "indice_referencia": 900.0},
            {"codi_barri": "02", "indice_referencia": 950.0},
        ],
        2025: [
            {"codi_barri": "01", "indice_referencia": 920.0},
            {"codi_barri": "02", "indice_referencia": 970.0},
        ],
    }

    extractor = GeneralitatExtractor(output_dir=output_dir)

    def fake_get(self, url, params=None, timeout=60):  # noqa: D401, ARG002
        """Simula peticiones HTTP devolviendo JSON por año."""
        year = params.get("year")
        payload: Any = responses_by_year.get(year, [])
        return DummyResponse(200, payload)

    # Parchar la sesión interna
    monkeypatch.setattr(type(extractor.session), "get", fake_get, raising=False)

    df, meta = extractor.extract_indice_referencia(2024, 2025)

    assert not df.empty
    assert set(df["anio"].unique()) == {2024, 2025}
    assert meta["success"] is True
    assert meta["records"] == len(df)

    source_dir = output_dir / "generalitat"
    csv_files = list(source_dir.glob("generalitat_indice_referencia_*.csv"))
    assert csv_files, "No se generó archivo CSV de salida para la Generalitat"

    manifest_path = output_dir / "manifest.json"
    assert manifest_path.exists(), "No se generó manifest.json para la Generalitat"


def test_extract_indice_referencia_no_data(monkeypatch, output_dir: Path) -> None:
    """Debe devolver DataFrame vacío y success=False si no hay datos."""
    extractor = GeneralitatExtractor(output_dir=output_dir)

    def fake_get(self, url, params=None, timeout=60):  # noqa: D401, ARG002
        """Simula peticiones HTTP sin datos."""
        return DummyResponse(200, [])

    monkeypatch.setattr(type(extractor.session), "get", fake_get, raising=False)

    df, meta = extractor.extract_indice_referencia(2024, 2024)

    assert df.empty
    assert meta["success"] is False


