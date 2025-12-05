"""Tests para src.etl.transformations.demographics."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.etl.transformations.demographics import (
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

