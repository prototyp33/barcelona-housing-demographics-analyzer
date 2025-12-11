from typing import Any

import pytest
import requests

from src.extraction.bcn_income import BcnIncomeExtractor


class DummyResponse:
    """Respuesta HTTP simulada para tests."""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status code {self.status_code}")


@pytest.fixture(autouse=True)
def fast_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita esperas reales durante tests."""

    monkeypatch.setattr("src.extraction.bcn_income.time.sleep", lambda *_: None)


def _patch_get(monkeypatch: pytest.MonkeyPatch, extractor: BcnIncomeExtractor, text: str) -> None:
    """Parcha session.get para devolver un CSV simulado."""

    def fake_get(url: str, timeout: Any = None) -> DummyResponse:
        return DummyResponse(text=text)

    monkeypatch.setattr(extractor, "_build_candidate_urls", lambda year: [f"http://fake/{year}.csv"])
    monkeypatch.setattr(extractor.session, "get", fake_get)


def test_extract_income_single_year_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica extracción y limpieza eliminando totales con CSV realista (coma)."""

    csv_text = """Any,Codi_Districte,Nom_Districte,Codi_Barri,Nom_Barri,Seccio_Censal,Import_Euros
2021,1,Ciutat Vella,1,el Raval,1,14078
2021,1,Ciutat Vella,,Total Barcelona,,30000
"""
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    extractor.MIN_BARRIOS = 1  # Relajar cobertura para prueba unitaria
    _patch_get(monkeypatch, extractor, csv_text)

    df = extractor.extract_income_by_barrio(2022, 2022)

    assert len(df) == 1
    assert set(df.columns) == {
        "codigo_barrio",
        "barrio_nombre",
        "anio",
        "renta_per_capita",
        "fuente",
    }
    assert df.iloc[0]["codigo_barrio"] == 1
    assert df.iloc[0]["barrio_nombre"] == "el Raval"
    assert df.iloc[0]["anio"] == 2022
    assert df.iloc[0]["renta_per_capita"] == 14078
    assert df.iloc[0]["fuente"] == "OpenDataBCN"


def test_extract_income_non_numeric(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lanza error cuando Import_Euros no es numérico (abc)."""

    csv_text = """Nom_Barri;Codi_Barri;Import_Euros
Ciutat Vella;1;abc
"""
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    _patch_get(monkeypatch, extractor, csv_text)

    with pytest.raises(ValueError):
        extractor.extract_income_by_barrio(2022, 2022)


def test_extract_income_missing_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lanza error si faltan columnas esenciales."""

    csv_text = """Nom_Barri;Import_Euros
Ciutat Vella;20000
"""
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    _patch_get(monkeypatch, extractor, csv_text)

    with pytest.raises(ValueError):
        extractor.extract_income_by_barrio(2022, 2022)


def test_extract_income_with_placeholders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lanza error cuando Import_Euros contiene '..' o nulos."""

    csv_text = """Nom_Barri;Codi_Barri;Import_Euros
Ciutat Vella;1;..
"""
    extractor = BcnIncomeExtractor(rate_limit_delay=0)
    _patch_get(monkeypatch, extractor, csv_text)

    with pytest.raises(ValueError):
        extractor.extract_income_by_barrio(2022, 2022)


def test_save_writes_under_bcn(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Confirma que el guardado usa directorio bcn en output_dir."""

    csv_text = """Nom_Barri;Codi_Barri;Import_Euros
Ciutat Vella;1;20000
"""
    extractor = BcnIncomeExtractor(rate_limit_delay=0, output_dir=tmp_path)
    extractor.MIN_BARRIOS = 1
    _patch_get(monkeypatch, extractor, csv_text)
    df = extractor.extract_income_by_barrio(2022, 2022)

    path = extractor.save(df, "renta_test")
    assert path.parent.name == "bcn"
    assert path.exists()

