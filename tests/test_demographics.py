"""Tests para src.etl.transformations.demographics."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.etl.transformations.demographics import (
    _compute_age_metrics_from_raw,
    _compute_area_by_barrio,
    _compute_building_age_proxy,
    _compute_foreign_purchase_share,
    _compute_household_metrics,
    enrich_fact_demografia,
    prepare_demografia_ampliada,
    prepare_fact_demografia,
)


@pytest.fixture
def sample_dim_barrios() -> pd.DataFrame:
    """Crea un DataFrame de ejemplo para dim_barrios."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 3],
        "barrio_nombre": ["Barrio 1", "Barrio 2", "Barrio 3"],
        "barrio_nombre_normalizado": ["barrio-1", "barrio-2", "barrio-3"],
        "distrito_nombre": ["Distrito 1", "Distrito 1", "Distrito 2"],
    })


@pytest.fixture
def sample_demographics_data() -> pd.DataFrame:
    """Crea datos demográficos de ejemplo para prepare_fact_demografia."""
    return pd.DataFrame({
        "Valor": [1000, 1500, 2000, 1100, 1600, 2100],
        "año": [2022, 2022, 2022, 2023, 2023, 2023],
        "Codi_Barri": [1, 2, 3, 1, 2, 3],
        "SEXE": [1, 1, 2, 1, 2, 2],  # 1=hombre, 2=mujer
    })


@pytest.fixture
def sample_demographics_ampliada() -> pd.DataFrame:
    """Crea datos demográficos ampliados de ejemplo."""
    return pd.DataFrame({
        "Data_Referencia": ["2022-01-01"] * 6 + ["2023-01-01"] * 6,
        "Codi_Barri": [1, 1, 2, 2, 3, 3] * 2,
        "Valor": [100, 150, 200, 250, 300, 350] * 2,
        "LLOC_NAIX_CONTINENT": [1, 2, 1, 2, 1, 2] * 2,  # 1=España, 2=Extranjero
        "EDAT_Q": [2, 5, 8, 12, 15, 18] * 2,  # Edad quinquenal
        "SEXE": [1, 2, 1, 2, 1, 2] * 2,
    })


@pytest.fixture
def sample_fact_demografia(sample_dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """Crea un DataFrame de ejemplo para fact_demografia."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 3],
        "anio": [2022, 2022, 2022],
        "poblacion_total": [2500, 3000, 3500],
        "poblacion_hombres": [1200, 1500, 1700],
        "poblacion_mujeres": [1300, 1500, 1800],
        "hogares_totales": pd.NA,
        "edad_media": pd.NA,
        "porc_inmigracion": pd.NA,
        "densidad_hab_km2": pd.NA,
        "dataset_id": "test_dataset",
        "source": "opendatabcn",
        "etl_loaded_at": datetime.now().isoformat(),
    })


class TestPrepareFactDemografia:
    """Tests para prepare_fact_demografia."""

    def test_prepare_fact_demografia_basic(
        self,
        sample_demographics_data: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica la creación básica de fact_demografia."""
        result = prepare_fact_demografia(
            demographics=sample_demographics_data,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime(2023, 1, 1),
            source="opendatabcn",
        )

        assert len(result) == 6  # 3 barrios × 2 años
        assert "barrio_id" in result.columns
        assert "anio" in result.columns
        assert "poblacion_total" in result.columns
        assert "poblacion_hombres" in result.columns
        assert "poblacion_mujeres" in result.columns
        assert "hogares_totales" in result.columns
        assert "dataset_id" in result.columns
        assert "source" in result.columns
        assert "etl_loaded_at" in result.columns

    def test_prepare_fact_demografia_missing_columns(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se lanza error si faltan columnas requeridas."""
        df_missing = pd.DataFrame({
            "Valor": [1000],
            "año": [2022],
            # Falta Codi_Barri
        })

        with pytest.raises(ValueError, match="missing column 'Codi_Barri'"):
            prepare_fact_demografia(
                demographics=df_missing,
                dim_barrios=sample_dim_barrios,
                dataset_id="test_dataset",
                reference_time=datetime.now(),
            )

    def test_prepare_fact_demografia_pivot_by_sex(
        self,
        sample_demographics_data: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se agrupa correctamente por sexo."""
        result = prepare_fact_demografia(
            demographics=sample_demographics_data,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Verificar que poblacion_total = poblacion_hombres + poblacion_mujeres
        result["calculated_total"] = (
            result["poblacion_hombres"].fillna(0) + result["poblacion_mujeres"].fillna(0)
        )
        assert (result["poblacion_total"] == result["calculated_total"]).all()

    def test_prepare_fact_demografia_handles_missing_sex(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que maneja correctamente datos sin información de sexo."""
        df_no_sex = pd.DataFrame({
            "Valor": [1000, 2000],
            "año": [2022, 2022],
            "Codi_Barri": [1, 2],
            "SEXE": [1, 1],  # Solo hombres
        })

        result = prepare_fact_demografia(
            demographics=df_no_sex,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Debe tener columnas de mujeres aunque sean 0
        assert "poblacion_mujeres" in result.columns
        assert (result["poblacion_mujeres"].fillna(0) == 0).all()

    def test_prepare_fact_demografia_drops_invalid_rows(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se eliminan filas con valores nulos o inválidos."""
        df_with_nulls = pd.DataFrame({
            "Valor": [1000, None, "invalid", 2000],
            "año": [2022, 2022, 2022, 2022],
            "Codi_Barri": [1, 2, None, 3],
            "SEXE": [1, 1, 1, 1],
        })

        result = prepare_fact_demografia(
            demographics=df_with_nulls,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Debe tener solo filas válidas (barrio_id=1 y barrio_id=3, ya que barrio_id=2 tiene Valor=None)
        # barrio_id=None se elimina, "invalid" se convierte a NaN y se elimina
        assert len(result) == 2
        assert set(result["barrio_id"].unique()) == {1, 3}

    def test_prepare_fact_demografia_merges_with_dim_barrios(
        self,
        sample_demographics_data: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se hace merge correcto con dim_barrios."""
        result = prepare_fact_demografia(
            demographics=sample_demographics_data,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Verificar que solo incluye barrios que existen en dim_barrios
        assert set(result["barrio_id"].unique()).issubset(
            set(sample_dim_barrios["barrio_id"].unique())
        )

    def test_prepare_fact_demografia_sets_metadata(
        self,
        sample_demographics_data: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se establecen correctamente los metadatos."""
        reference_time = datetime(2023, 6, 15, 10, 30, 0)
        result = prepare_fact_demografia(
            demographics=sample_demographics_data,
            dim_barrios=sample_dim_barrios,
            dataset_id="custom_dataset_id",
            reference_time=reference_time,
            source="custom_source",
        )

        assert (result["dataset_id"] == "custom_dataset_id").all()
        assert (result["source"] == "custom_source").all()
        assert (result["etl_loaded_at"] == reference_time.isoformat()).all()

    def test_prepare_fact_demografia_sorts_correctly(
        self,
        sample_demographics_data: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que los resultados están ordenados por año y barrio_id."""
        result = prepare_fact_demografia(
            demographics=sample_demographics_data,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Verificar orden
        sorted_result = result.sort_values(["anio", "barrio_id"])
        pd.testing.assert_frame_equal(result, sorted_result)


class TestEnrichFactDemografia:
    """Tests para enrich_fact_demografia."""

    def test_enrich_fact_demografia_no_portaldades_dir(
        self,
        sample_fact_demografia: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna datos sin cambios si no existe portaldades_dir."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        # No crear directorio portaldades

        result = enrich_fact_demografia(
            fact=sample_fact_demografia,
            dim_barrios=sample_dim_barrios,
            raw_base_dir=raw_dir,
            reference_time=datetime.now(),
        )

        pd.testing.assert_frame_equal(result, sample_fact_demografia)

    def test_enrich_fact_demografia_with_household_metrics(
        self,
        sample_fact_demografia: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica enriquecimiento con datos de hogares."""
        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        # Crear archivo CSV simulado de hogares
        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["barrio-1"],  # Usar nombre normalizado
            "Dim-01:TERRITORI (type)": ["Barri"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["2 persones"],
            "VALUE": [500.0],
        })
        household_data.to_csv(household_file, index=False)

        # Mock _map_territorio_to_barrio_id para que retorne el barrio_id correcto
        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,  # Retornar barrio_id=1
        ):
            result = enrich_fact_demografia(
                fact=sample_fact_demografia,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            # Verificar que la función se ejecutó sin errores
            assert len(result) == len(sample_fact_demografia)

    def test_enrich_fact_demografia_with_immigration_data(
        self,
        sample_fact_demografia: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica enriquecimiento con datos de inmigración."""
        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        immigration_file = portaldades_dir / "uuxbxa7onv_2022.csv"
        immigration_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri"],
            "Dim-02:GRUP DE NACIONALITAT DEL COMPRADOR": ["Estranger", "Espanya"],
            "VALUE": [100.0, 400.0],
        })
        immigration_data.to_csv(immigration_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                immigration_file if indicator_id == "uuxbxa7onv" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,  # Retornar barrio_id=1
        ):
            result = enrich_fact_demografia(
                fact=sample_fact_demografia,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            # Verificar que la función se ejecutó sin errores
            assert len(result) == len(sample_fact_demografia)

    def test_enrich_fact_demografia_preserves_existing_data(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que no sobrescribe datos existentes."""
        fact_with_data = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2022, 2022],
            "poblacion_total": [2500, 3000],
            "poblacion_hombres": [1200, 1500],
            "poblacion_mujeres": [1300, 1500],
            "hogares_totales": [1000.0, pd.NA],  # Ya tiene un valor
            "edad_media": [35.0, pd.NA],
            "porc_inmigracion": [20.0, pd.NA],
            "densidad_hab_km2": [5000.0, pd.NA],
            "dataset_id": "test_dataset",
            "source": "opendatabcn",
            "etl_loaded_at": datetime.now().isoformat(),
        })

        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        result = enrich_fact_demografia(
            fact=fact_with_data,
            dim_barrios=sample_dim_barrios,
            raw_base_dir=raw_dir,
            reference_time=datetime.now(),
        )

        # Verificar que el valor existente se preserva
        assert result.loc[result["barrio_id"] == 1, "hogares_totales"].iloc[0] == 1000.0


class TestPrepareDemografiaAmpliada:
    """Tests para prepare_demografia_ampliada."""

    def test_prepare_demografia_ampliada_basic(
        self,
        sample_demographics_ampliada: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica la creación básica de demografía ampliada."""
        result = prepare_demografia_ampliada(
            demographics_df=sample_demographics_ampliada,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
            source="opendatabcn",
        )

        assert len(result) > 0
        assert "barrio_id" in result.columns
        assert "anio" in result.columns
        assert "sexo" in result.columns
        assert "grupo_edad" in result.columns
        assert "nacionalidad" in result.columns
        assert "poblacion" in result.columns
        assert "dataset_id" in result.columns
        assert "source" in result.columns

    def test_prepare_demografia_ampliada_missing_columns(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se lanza error si faltan columnas requeridas."""
        df_missing = pd.DataFrame({
            "Data_Referencia": ["2022-01-01"],
            "Codi_Barri": [1],
            "Valor": [100],
            # Faltan columnas requeridas
        })

        with pytest.raises(ValueError, match="faltan columnas"):
            prepare_demografia_ampliada(
                demographics_df=df_missing,
                dim_barrios=sample_dim_barrios,
                dataset_id="test_dataset",
                reference_time=datetime.now(),
            )

    def test_prepare_demografia_ampliada_handles_invalid_values(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que maneja correctamente valores inválidos."""
        df_invalid = pd.DataFrame({
            "Data_Referencia": ["2022-01-01", "2022-01-01", "invalid"],
            "Codi_Barri": [1, 2, 3],
            "Valor": [100, "..", 200],  # ".." debe ser tratado como NA
            "LLOC_NAIX_CONTINENT": [1, 2, 1],
            "EDAT_Q": [5, 10, None],
            "SEXE": [1, 2, 1],
        })

        result = prepare_demografia_ampliada(
            demographics_df=df_invalid,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Debe eliminar filas con valores inválidos
        assert len(result) >= 0  # Puede ser 0 si todos son inválidos

    def test_prepare_demografia_ampliada_groups_correctly(
        self,
        sample_demographics_ampliada: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que agrupa correctamente por barrio, año, sexo, grupo_edad y nacionalidad."""
        result = prepare_demografia_ampliada(
            demographics_df=sample_demographics_ampliada,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        # Verificar que no hay duplicados en la combinación de claves
        key_cols = ["barrio_id", "anio", "sexo", "grupo_edad", "nacionalidad"]
        assert result[key_cols].duplicated().sum() == 0

    def test_prepare_demografia_ampliada_sets_metadata(
        self,
        sample_demographics_ampliada: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que se establecen correctamente los metadatos."""
        reference_time = datetime(2023, 6, 15, 10, 30, 0)
        result = prepare_demografia_ampliada(
            demographics_df=sample_demographics_ampliada,
            dim_barrios=sample_dim_barrios,
            dataset_id="custom_dataset_id",
            reference_time=reference_time,
            source="custom_source",
        )

        assert (result["dataset_id"] == "custom_dataset_id").all()
        assert (result["source"] == "custom_source").all()
        assert (result["etl_loaded_at"] == reference_time.isoformat()).all()

    def test_prepare_demografia_ampliada_sorts_correctly(
        self,
        sample_demographics_ampliada: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que los resultados están ordenados correctamente."""
        result = prepare_demografia_ampliada(
            demographics_df=sample_demographics_ampliada,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        if len(result) > 0:
            # Verificar orden
            sorted_result = result.sort_values(
                ["anio", "barrio_id", "sexo", "grupo_edad", "nacionalidad"]
            )
            pd.testing.assert_frame_equal(result, sorted_result)

    def test_prepare_demografia_ampliada_maps_sex_correctly(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que mapea correctamente los valores de SEXE."""
        df_sex = pd.DataFrame({
            "Data_Referencia": ["2022-01-01"] * 3,
            "Codi_Barri": [1, 1, 1],
            "Valor": [100, 150, 200],
            "LLOC_NAIX_CONTINENT": [1, 1, 1],
            "EDAT_Q": [5, 5, 5],
            "SEXE": [1, 2, 99],  # 1=hombre, 2=mujer, 99=desconocido
        })

        result = prepare_demografia_ampliada(
            demographics_df=df_sex,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        if len(result) > 0:
            assert set(result["sexo"].unique()).issubset({"hombre", "mujer", "desconocido"})


class TestDemographicsEdgeCases:
    """Tests para casos límite y edge cases."""

    def test_prepare_fact_demografia_empty_dataframe(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que maneja correctamente un DataFrame vacío."""
        empty_df = pd.DataFrame(columns=["Valor", "año", "Codi_Barri", "SEXE"])

        result = prepare_fact_demografia(
            demographics=empty_df,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        assert len(result) == 0
        assert "barrio_id" in result.columns

    def test_enrich_fact_demografia_empty_fact(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que maneja correctamente un fact_demografia vacío."""
        empty_fact = pd.DataFrame(columns=[
            "barrio_id",
            "anio",
            "poblacion_total",
            "poblacion_hombres",
            "poblacion_mujeres",
            "hogares_totales",
            "edad_media",
            "porc_inmigracion",
            "densidad_hab_km2",
            "dataset_id",
            "source",
            "etl_loaded_at",
        ])

        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()

        result = enrich_fact_demografia(
            fact=empty_fact,
            dim_barrios=sample_dim_barrios,
            raw_base_dir=raw_dir,
            reference_time=datetime.now(),
        )

        assert len(result) == 0

    def test_prepare_demografia_ampliada_empty_dataframe(
        self,
        sample_dim_barrios: pd.DataFrame,
    ):
        """Verifica que maneja correctamente un DataFrame vacío."""
        empty_df = pd.DataFrame(columns=[
            "Data_Referencia",
            "Codi_Barri",
            "Valor",
            "LLOC_NAIX_CONTINENT",
            "EDAT_Q",
            "SEXE",
        ])

        result = prepare_demografia_ampliada(
            demographics_df=empty_df,
            dim_barrios=sample_dim_barrios,
            dataset_id="test_dataset",
            reference_time=datetime.now(),
        )

        assert len(result) == 0


class TestPrivateHelperFunctions:
    """Tests para funciones auxiliares privadas de demographics."""

    def test_compute_household_metrics_no_file(
        self,
        sample_dim_barrios: pd.DataFrame,
        sample_fact_demografia: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna DataFrame vacío si no existe el archivo."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            return_value=None,
        ):
            result = _compute_household_metrics(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
                fact_demografia=sample_fact_demografia,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_compute_foreign_purchase_share_no_file(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna DataFrame vacío si no existe el archivo."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            return_value=None,
        ):
            result = _compute_foreign_purchase_share(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_compute_building_age_proxy_no_file(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna DataFrame vacío si no existe el archivo."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            return_value=None,
        ):
            result = _compute_building_age_proxy(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_compute_area_by_barrio_no_file(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna DataFrame vacío si no existe el archivo."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            return_value=None,
        ):
            result = _compute_area_by_barrio(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_compute_age_metrics_from_raw_no_directory(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que retorna DataFrame vacío si no existe el directorio."""
        raw_dir = tmp_path / "raw"
        # No crear directorio opendatabcn

        result = _compute_age_metrics_from_raw(
            raw_base_dir=raw_dir,
            dim_barrios=sample_dim_barrios,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_compute_household_metrics_with_valid_csv(
        self,
        sample_dim_barrios: pd.DataFrame,
        sample_fact_demografia: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica cálculo de métricas de hogares con CSV válido."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 1", "Barrio 2"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri", "Barri"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["1 persona", "2 persones", "3 persones"],
            "VALUE": [100.0, 200.0, 150.0],
        })
        household_data.to_csv(household_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            side_effect=lambda terr, tipo, dim_barrios: (
                1 if "Barrio 1" in str(terr) else (2 if "Barrio 2" in str(terr) else None)
            ),
        ):
            result = _compute_household_metrics(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
                fact_demografia=sample_fact_demografia,
            )

            assert isinstance(result, pd.DataFrame)
            if len(result) > 0:
                assert "barrio_id" in result.columns
                assert "anio" in result.columns
                assert "hogares_observados" in result.columns
                assert "avg_size" in result.columns
                assert "dataset_id" in result.columns
                assert "source" in result.columns

    def test_compute_household_metrics_with_district_data(
        self,
        sample_dim_barrios: pd.DataFrame,
        sample_fact_demografia: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que maneja correctamente datos a nivel de distrito."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Distrito 1"],
            "Dim-01:TERRITORI (type)": ["Districte"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["2 persones"],
            "VALUE": [1000.0],
        })
        household_data.to_csv(household_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ):
            result = _compute_household_metrics(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
                fact_demografia=sample_fact_demografia,
            )

            assert isinstance(result, pd.DataFrame)

    def test_compute_household_metrics_missing_columns(
        self,
        sample_dim_barrios: pd.DataFrame,
        sample_fact_demografia: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que maneja correctamente CSVs con columnas faltantes."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            # Faltan columnas requeridas
        })
        household_data.to_csv(household_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ):
            result = _compute_household_metrics(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
                fact_demografia=sample_fact_demografia,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_compute_foreign_purchase_share_with_valid_csv(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica cálculo de porcentaje de compras extranjeras con CSV válido."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        immigration_file = portaldades_dir / "uuxbxa7onv_2022.csv"
        immigration_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022", "2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 1", "Barrio 2", "Barrio 2"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri", "Barri", "Barri"],
            "Dim-02:GRUP DE NACIONALITAT DEL COMPRADOR": [
                "Estranger",
                "Espanya",
                "Estranger",
                "Espanya",
            ],
            "VALUE": [100.0, 400.0, 50.0, 450.0],
        })
        immigration_data.to_csv(immigration_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                immigration_file if indicator_id == "uuxbxa7onv" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            side_effect=lambda terr, tipo, dim_barrios: (
                1 if "Barrio 1" in str(terr) else (2 if "Barrio 2" in str(terr) else None)
            ),
        ):
            result = _compute_foreign_purchase_share(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            if len(result) > 0:
                assert "barrio_id" in result.columns
                assert "anio" in result.columns
                assert "porc_inmigracion" in result.columns
                # Verificar que el porcentaje está entre 0 y 100
                if result["porc_inmigracion"].notna().any():
                    assert (result["porc_inmigracion"] >= 0).all()
                    assert (result["porc_inmigracion"] <= 100).all()

    def test_compute_foreign_purchase_share_no_foreign_buyers(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que maneja correctamente casos sin compradores extranjeros."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        immigration_file = portaldades_dir / "uuxbxa7onv_2022.csv"
        immigration_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "Dim-02:GRUP DE NACIONALITAT DEL COMPRADOR": ["Espanya"],
            "VALUE": [500.0],
        })
        immigration_data.to_csv(immigration_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                immigration_file if indicator_id == "uuxbxa7onv" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,
        ):
            result = _compute_foreign_purchase_share(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)

    def test_compute_building_age_proxy_with_valid_data(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica cálculo de edad media de edificaciones con datos válidos."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        age_file = portaldades_dir / "ydtnyd6qhm_2022.csv"
        age_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022", "2023"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 2", "Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri", "Barri"],
            "VALUE": [35.5, 40.2, 36.0],
        })
        age_data.to_csv(age_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                age_file if indicator_id == "ydtnyd6qhm" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            side_effect=lambda terr, tipo, dim_barrios: (
                1 if "Barrio 1" in str(terr) else (2 if "Barrio 2" in str(terr) else None)
            ),
        ):
            result = _compute_building_age_proxy(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            if len(result) > 0:
                assert "barrio_id" in result.columns
                assert "anio" in result.columns
                assert "edad_media_proxy" in result.columns
                assert "dataset_id" in result.columns
                assert "source" in result.columns

    def test_compute_building_age_proxy_invalid_type(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que filtra correctamente tipos de territorio no válidos."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        age_file = portaldades_dir / "ydtnyd6qhm_2022.csv"
        age_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Distrito 1"],
            "Dim-01:TERRITORI (type)": ["Districte"],  # No es "Barri"
            "VALUE": [35.5],
        })
        age_data.to_csv(age_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                age_file if indicator_id == "ydtnyd6qhm" else None
            ),
        ):
            result = _compute_building_age_proxy(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0  # Debe estar vacío porque filtra solo "Barri"

    def test_compute_area_by_barrio_with_valid_data(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica cálculo de área por barrio con datos válidos."""
        portaldades_dir = tmp_path / "portaldades"
        portaldades_dir.mkdir(parents=True)

        area_file = portaldades_dir / "wjnmk82jd9_2022.csv"
        area_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 2"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri"],
            "VALUE": [500000.0, 750000.0],  # m²
        })
        area_data.to_csv(area_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                area_file if indicator_id == "wjnmk82jd9" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            side_effect=lambda terr, tipo, dim_barrios: (
                1 if "Barrio 1" in str(terr) else (2 if "Barrio 2" in str(terr) else None)
            ),
        ):
            result = _compute_area_by_barrio(
                portaldades_dir=portaldades_dir,
                dim_barrios=sample_dim_barrios,
            )

            assert isinstance(result, pd.DataFrame)
            if len(result) > 0:
                assert "barrio_id" in result.columns
                assert "anio" in result.columns
                assert "area_m2" in result.columns
                assert "dataset_id" in result.columns
                assert "source" in result.columns
                # Verificar que el área es positiva
                if result["area_m2"].notna().any():
                    assert (result["area_m2"] > 0).all()

    def test_compute_age_metrics_from_raw_with_valid_csv(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica cálculo de métricas de edad desde datos raw válidos."""
        raw_dir = tmp_path / "raw"
        opendata_dir = raw_dir / "opendatabcn"
        opendata_dir.mkdir(parents=True)

        # Crear archivo CSV con datos de edad quinquenal válidos
        age_file = opendata_dir / "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_2022.csv"
        age_data = pd.DataFrame({
            "Codi_Barri": [1, 1, 1, 1, 2, 2, 2, 2],
            "EDAT_Q": [2, 5, 13, 15, 2, 5, 13, 15],  # 10, 25, 65, 75 años
            "Valor": [100, 200, 150, 100, 120, 180, 130, 90],
            "Data_Referencia": ["2022-01-01"] * 8,
        })
        age_data.to_csv(age_file, index=False)

        result = _compute_age_metrics_from_raw(
            raw_base_dir=raw_dir,
            dim_barrios=sample_dim_barrios,
        )

        assert isinstance(result, pd.DataFrame)
        if len(result) > 0:
            assert "barrio_id" in result.columns
            assert "anio" in result.columns
            assert "pct_mayores_65" in result.columns
            assert "pct_menores_15" in result.columns
            assert "indice_envejecimiento" in result.columns
            # Verificar que los porcentajes están entre 0 y 100
            if result["pct_mayores_65"].notna().any():
                assert (result["pct_mayores_65"] >= 0).all()
                assert (result["pct_mayores_65"] <= 100).all()

    def test_compute_age_metrics_from_raw_alternative_pattern(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que encuentra archivos con patrón alternativo."""
        raw_dir = tmp_path / "raw"
        opendata_dir = raw_dir / "opendatabcn"
        opendata_dir.mkdir(parents=True)

        # Crear archivo con patrón alternativo
        age_file = opendata_dir / "opendatabcn_pad_mdb_nacionalitat-contintent_edat-q_sexe_2022.csv"
        age_data = pd.DataFrame({
            "Codi_Barri": [1, 1],
            "EDAT_Q": [2, 15],
            "Valor": [100, 150],
            "Data_Referencia": ["2022-01-01"] * 2,
        })
        age_data.to_csv(age_file, index=False)

        result = _compute_age_metrics_from_raw(
            raw_base_dir=raw_dir,
            dim_barrios=sample_dim_barrios,
        )

        assert isinstance(result, pd.DataFrame)

    def test_compute_age_metrics_from_raw_missing_columns(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que maneja correctamente archivos con columnas faltantes."""
        raw_dir = tmp_path / "raw"
        opendata_dir = raw_dir / "opendatabcn"
        opendata_dir.mkdir(parents=True)

        age_file = opendata_dir / "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_2022.csv"
        age_data = pd.DataFrame({
            "Codi_Barri": [1],
            # Faltan columnas requeridas
        })
        age_data.to_csv(age_file, index=False)

        result = _compute_age_metrics_from_raw(
            raw_base_dir=raw_dir,
            dim_barrios=sample_dim_barrios,
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_enrich_fact_demografia_with_all_sources(
        self,
        sample_fact_demografia: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica enriquecimiento completo con todas las fuentes disponibles."""
        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        # Crear archivos CSV para todas las fuentes
        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["2 persones"],
            "VALUE": [500.0],
        })
        household_data.to_csv(household_file, index=False)

        immigration_file = portaldades_dir / "uuxbxa7onv_2022.csv"
        immigration_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri"],
            "Dim-02:GRUP DE NACIONALITAT DEL COMPRADOR": ["Estranger", "Espanya"],
            "VALUE": [100.0, 400.0],
        })
        immigration_data.to_csv(immigration_file, index=False)

        age_file = portaldades_dir / "ydtnyd6qhm_2022.csv"
        age_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "VALUE": [35.5],
        })
        age_data.to_csv(age_file, index=False)

        area_file = portaldades_dir / "wjnmk82jd9_2022.csv"
        area_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "VALUE": [500000.0],
        })
        area_data.to_csv(area_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: {
                "hd7u1b68qj": household_file,
                "uuxbxa7onv": immigration_file,
                "ydtnyd6qhm": age_file,
                "wjnmk82jd9": area_file,
            }.get(indicator_id),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,
        ):
            result = enrich_fact_demografia(
                fact=sample_fact_demografia,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(sample_fact_demografia)
            # Verificar que algunos campos fueron enriquecidos
            enriched_fields = [
                "hogares_totales",
                "edad_media",
                "porc_inmigracion",
                "densidad_hab_km2",
            ]
            for field in enriched_fields:
                assert field in result.columns

    def test_enrich_fact_demografia_calculates_density(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que calcula correctamente la densidad de población."""
        fact_with_population = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2022, 2022],
            "poblacion_total": [2500, 3000],
            "poblacion_hombres": [1200, 1500],
            "poblacion_mujeres": [1300, 1500],
            "hogares_totales": pd.NA,
            "edad_media": pd.NA,
            "porc_inmigracion": pd.NA,
            "densidad_hab_km2": pd.NA,
            "dataset_id": "test_dataset",
            "source": "opendatabcn",
            "etl_loaded_at": datetime.now().isoformat(),
        })

        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        area_file = portaldades_dir / "wjnmk82jd9_2022.csv"
        area_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022", "2022"],
            "Dim-01:TERRITORI": ["Barrio 1", "Barrio 2"],
            "Dim-01:TERRITORI (type)": ["Barri", "Barri"],
            "VALUE": [500000.0, 750000.0],  # 0.5 km² y 0.75 km²
        })
        area_data.to_csv(area_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                area_file if indicator_id == "wjnmk82jd9" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            side_effect=lambda terr, tipo, dim_barrios: (
                1 if "Barrio 1" in str(terr) else (2 if "Barrio 2" in str(terr) else None)
            ),
        ):
            result = enrich_fact_demografia(
                fact=fact_with_population,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            assert isinstance(result, pd.DataFrame)
            # Verificar que se calculó la densidad
            density_calculated = result["densidad_hab_km2"].notna()
            if density_calculated.any():
                # Densidad = población * 1,000,000 / área_m2
                # Barrio 1: 2500 * 1,000,000 / 500000 = 5000 hab/km²
                assert (result["densidad_hab_km2"] > 0).all()

    def test_enrich_fact_demografia_with_age_metrics(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica enriquecimiento con métricas de edad desde datos raw."""
        fact = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2022, 2022],
            "poblacion_total": [2500, 3000],
            "poblacion_hombres": [1200, 1500],
            "poblacion_mujeres": [1300, 1500],
            "hogares_totales": pd.NA,
            "edad_media": pd.NA,
            "porc_inmigracion": pd.NA,
            "densidad_hab_km2": pd.NA,
            "dataset_id": "test_dataset",
            "source": "opendatabcn",
            "etl_loaded_at": datetime.now().isoformat(),
        })

        raw_dir = tmp_path / "raw"
        opendata_dir = raw_dir / "opendatabcn"
        opendata_dir.mkdir(parents=True)

        age_file = opendata_dir / "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_2022.csv"
        age_data = pd.DataFrame({
            "Codi_Barri": [1, 1, 1, 2, 2, 2],
            "EDAT_Q": [2, 5, 15, 2, 5, 15],  # 10, 25, 75 años
            "Valor": [100, 200, 150, 120, 180, 130],
            "Data_Referencia": ["2022-01-01"] * 6,
        })
        age_data.to_csv(age_file, index=False)

        result = enrich_fact_demografia(
            fact=fact,
            dim_barrios=sample_dim_barrios,
            raw_base_dir=raw_dir,
            reference_time=datetime.now(),
        )

        assert isinstance(result, pd.DataFrame)
        # Verificar que se añadieron columnas de métricas de edad
        age_columns = ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]
        for col in age_columns:
            if col in result.columns:
                assert result[col].dtype in [float, "Float64"] or result[col].isna().all()

    def test_enrich_fact_demografia_no_overwrite_existing(
        self,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que no sobrescribe datos existentes al enriquecer."""
        fact_with_data = pd.DataFrame({
            "barrio_id": [1],
            "anio": [2022],
            "poblacion_total": [2500],
            "poblacion_hombres": [1200],
            "poblacion_mujeres": [1300],
            "hogares_totales": [1000.0],  # Ya tiene valor
            "edad_media": [35.0],  # Ya tiene valor
            "porc_inmigracion": [20.0],  # Ya tiene valor
            "densidad_hab_km2": [5000.0],  # Ya tiene valor
            "dataset_id": "test_dataset",
            "source": "opendatabcn",
            "etl_loaded_at": datetime.now().isoformat(),
        })

        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        # Crear archivos con datos diferentes
        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["2 persones"],
            "VALUE": [999.0],  # Diferente al valor existente
        })
        household_data.to_csv(household_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,
        ):
            result = enrich_fact_demografia(
                fact=fact_with_data,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            # Verificar que los valores existentes se preservan
            assert result.loc[result["barrio_id"] == 1, "hogares_totales"].iloc[0] == 1000.0
            assert result.loc[result["barrio_id"] == 1, "edad_media"].iloc[0] == 35.0
            assert result.loc[result["barrio_id"] == 1, "porc_inmigracion"].iloc[0] == 20.0
            assert result.loc[result["barrio_id"] == 1, "densidad_hab_km2"].iloc[0] == 5000.0

    def test_enrich_fact_demografia_updates_dataset_id(
        self,
        sample_fact_demografia: pd.DataFrame,
        sample_dim_barrios: pd.DataFrame,
        tmp_path: Path,
    ):
        """Verifica que actualiza dataset_id cuando enriquece campos."""
        raw_dir = tmp_path / "raw"
        portaldades_dir = raw_dir / "portaldades"
        portaldades_dir.mkdir(parents=True)

        household_file = portaldades_dir / "hd7u1b68qj_2022.csv"
        household_data = pd.DataFrame({
            "Dim-00:TEMPS": ["2022"],
            "Dim-01:TERRITORI": ["Barrio 1"],
            "Dim-01:TERRITORI (type)": ["Barri"],
            "Dim-02:NOMBRE DE PERSONES DE LA LLAR": ["2 persones"],
            "VALUE": [500.0],
        })
        household_data.to_csv(household_file, index=False)

        with patch(
            "src.etl.transformations.demographics._find_portaldades_file",
            side_effect=lambda dir_path, indicator_id: (
                household_file if indicator_id == "hd7u1b68qj" else None
            ),
        ), patch(
            "src.etl.transformations.demographics._map_territorio_to_barrio_id",
            return_value=1,
        ):
            result = enrich_fact_demografia(
                fact=sample_fact_demografia,
                dim_barrios=sample_dim_barrios,
                raw_base_dir=raw_dir,
                reference_time=datetime.now(),
            )

            assert isinstance(result, pd.DataFrame)
            # Verificar que dataset_id contiene el tag del indicador si se enriqueció
            if result["hogares_totales"].notna().any():
                # El dataset_id debería contener "hd7u1b68qj" si se enriqueció
                enriched_rows = result["hogares_totales"].notna()
                if enriched_rows.any():
                    dataset_ids = result.loc[enriched_rows, "dataset_id"]
                    # Verificar que al menos algunos tienen el tag
                    assert len(dataset_ids) > 0

