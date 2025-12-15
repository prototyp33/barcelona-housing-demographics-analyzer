"""
Tests para el módulo principal de la aplicación Streamlit (`src/app.py`).
"""

from pathlib import Path
from typing import Any, List
import importlib.util

import pandas as pd
import pytest
import sqlite3
from unittest.mock import MagicMock, patch


def _load_streamlit_app_module():
    """
    Carga el módulo de la aplicación Streamlit desde `src/app.py`.

    Se hace así porque existe un paquete `src.app` y un fichero `src/app.py`,
    y Python prioriza el paquete, por lo que no podemos usar un import normal.

    Returns:
        Módulo cargado dinámicamente con la app Streamlit.
    """
    project_root = Path(__file__).resolve().parents[1]
    module_path = project_root / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("streamlit_app_module", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - protección adicional
        raise RuntimeError(f"No se pudo cargar el módulo de app desde {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


app = _load_streamlit_app_module()


class DummyStreamlit:
    """Dummy simple para capturar llamadas a Streamlit en tests."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def error(self, msg: Any) -> None:
        """Simula st.error almacenando el mensaje."""
        self.errors.append(str(msg))

    def warning(self, msg: Any) -> None:
        """Simula st.warning almacenando el mensaje."""
        self.warnings.append(str(msg))


@pytest.fixture
def dummy_st() -> DummyStreamlit:
    """
    Fixture que proporciona un objeto Streamlit simulado.

    Returns:
        Instancia de DummyStreamlit para inspeccionar mensajes.
    """
    return DummyStreamlit()


def test_load_map_data_database_not_found(
    monkeypatch: pytest.MonkeyPatch,
    dummy_st: DummyStreamlit,
) -> None:
    """
    Verifica que load_map_data devuelve un DataFrame vacío cuando no existe la base de datos.
    """
    # Usar un path que no exista
    fake_db = Path("/tmp/non_existing_db.sqlite")
    monkeypatch.setattr(app, "DB_PATH", fake_db)
    monkeypatch.setattr(app, "st", dummy_st)

    # Usar la función original sin el decorador de cache de Streamlit
    load_fn = getattr(app.load_map_data, "__wrapped__", app.load_map_data)
    df = load_fn()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    # Se debe haber informado el error al usuario
    assert any("Database not found" in msg for msg in dummy_st.errors)


def test_load_map_data_successful_load(
    monkeypatch: pytest.MonkeyPatch,
    dummy_st: DummyStreamlit,
    tmp_path: Path,
) -> None:
    """
    Verifica que load_map_data carga datos y transforma geometry_json en geometry.
    """

    # DataFrame simulado que normalmente vendría de la base de datos
    raw_df = pd.DataFrame(
        {
            "barrio_id": [1],
            "barrio_nombre": ["Barrio 1"],
            "distrito_nombre": ["Distrito 1"],
            "geometry_json": ['{"type": "Polygon", "coordinates": []}'],
        }
    )

    class DummyConnection:
        """Conexión simulada sin comportamiento real."""

        def close(self) -> None:
            return None

    class DummySqlite:
        """Módulo sqlite3 simulado para el módulo de app."""

        @staticmethod
        def connect(_db_path: Path) -> "DummyConnection":  # type: ignore[name-defined]
            return DummyConnection()

    class DummyPandas:
        """Módulo pandas simulado para el módulo de app."""

        @staticmethod
        def read_sql_query(query: str, conn: DummyConnection) -> pd.DataFrame:  # noqa: ARG001
            return raw_df

    db_path = tmp_path / "fake_db.sqlite"
    db_path.touch()

    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "DB_PATH", db_path)
    # Sobrescribir dependencias internas del módulo app
    monkeypatch.setattr(app, "sqlite3", DummySqlite)
    monkeypatch.setattr(app, "pd", DummyPandas)

    load_fn = getattr(app.load_map_data, "__wrapped__", app.load_map_data)
    df = load_fn()

    assert not df.empty
    # geometry_json debe desaparecer y aparecer geometry
    assert "geometry_json" not in df.columns
    assert "geometry" in df.columns
    assert isinstance(df.loc[0, "geometry"], dict)
    assert df.loc[0, "geometry"]["type"] == "Polygon"
    # No debería haberse llamado a st.error
    assert dummy_st.errors == []


def test_load_map_data_handles_exception(
    monkeypatch: pytest.MonkeyPatch,
    dummy_st: DummyStreamlit,
    tmp_path: Path,
) -> None:
    """
    Verifica que load_map_data maneja excepciones devolviendo un DataFrame vacío.
    """

    class FailingSqlite:
        """Módulo sqlite3 simulado que siempre lanza un error al conectar."""

        @staticmethod
        def connect(_db_path: Path) -> sqlite3.Connection:  # type: ignore[override]
            raise sqlite3.OperationalError("boom")

    db_path = tmp_path / "fake_db_error.sqlite"
    db_path.touch()

    monkeypatch.setattr(app, "st", dummy_st)
    monkeypatch.setattr(app, "DB_PATH", db_path)
    monkeypatch.setattr(app, "sqlite3", FailingSqlite)

    load_fn = getattr(app.load_map_data, "__wrapped__", app.load_map_data)
    df = load_fn()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
    # Debe registrarse un error hacia el usuario
    assert any("Error loading data" in msg for msg in dummy_st.errors)


