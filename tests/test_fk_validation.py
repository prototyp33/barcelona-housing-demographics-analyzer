"""Tests para el módulo de validación de integridad referencial (FK)."""

import pandas as pd
import pytest

from src.etl.validators import (
    FKValidationError,
    FKValidationResult,
    FKValidationStrategy,
    validate_all_fact_tables,
    validate_foreign_keys,
)


@pytest.fixture
def dim_barrios() -> pd.DataFrame:
    """Fixture con dimensión de barrios de prueba."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 3, 4, 5],
        "barrio_nombre": ["Raval", "Gótico", "Barceloneta", "Sant Pere", "Dreta Eixample"],
        "barrio_nombre_normalizado": [
            "raval", "gotic", "barceloneta", "sant pere", "dreta eixample"
        ],
    })


@pytest.fixture
def fact_precios_valid(dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """Fixture con precios válidos (todos los barrio_id existen)."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 3, 1, 2],
        "anio": [2022, 2022, 2022, 2023, 2023],
        "precio_m2_venta": [4500.0, 5200.0, 4800.0, 4600.0, 5300.0],
        "source": ["test"] * 5,
    })


@pytest.fixture
def fact_precios_invalid() -> pd.DataFrame:
    """Fixture con precios inválidos (algunos barrio_id no existen)."""
    return pd.DataFrame({
        "barrio_id": [1, 2, 99, 100, 3],  # 99 y 100 no existen
        "anio": [2022, 2022, 2022, 2022, 2022],
        "precio_m2_venta": [4500.0, 5200.0, 9999.0, 9999.0, 4800.0],
        "source": ["test"] * 5,
    })


class TestValidateForeignKeys:
    """Tests para la función validate_foreign_keys."""

    def test_valid_fks_returns_all_records(
        self,
        dim_barrios: pd.DataFrame,
        fact_precios_valid: pd.DataFrame,
    ) -> None:
        """Verifica que registros válidos pasan sin filtrar."""
        result_df, result = validate_foreign_keys(
            df=fact_precios_valid,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_precios",
            strategy="filter",
        )

        assert len(result_df) == len(fact_precios_valid)
        assert result.is_valid  # Usamos evaluación booleana
        assert result.invalid_records == 0
        assert result.valid_records == 5

    def test_invalid_fks_filtered_correctly(
        self,
        dim_barrios: pd.DataFrame,
        fact_precios_invalid: pd.DataFrame,
    ) -> None:
        """Verifica que registros inválidos se filtran en modo 'filter'."""
        result_df, result = validate_foreign_keys(
            df=fact_precios_invalid,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_precios",
            strategy="filter",
        )

        # Deben quedar solo los registros con barrio_id 1, 2, 3
        assert len(result_df) == 3
        assert not result.is_valid  # Usamos evaluación booleana
        assert result.invalid_records == 2
        assert result.valid_records == 3
        assert 99 in result.invalid_keys
        assert 100 in result.invalid_keys

    def test_strict_mode_raises_error(
        self,
        dim_barrios: pd.DataFrame,
        fact_precios_invalid: pd.DataFrame,
    ) -> None:
        """Verifica que modo 'strict' lanza excepción con FK inválidos."""
        with pytest.raises(FKValidationError) as exc_info:
            validate_foreign_keys(
                df=fact_precios_invalid,
                fk_column="barrio_id",
                reference_df=dim_barrios,
                pk_column="barrio_id",
                table_name="fact_precios",
                strategy="strict",
            )

        assert exc_info.value.table_name == "fact_precios"
        assert exc_info.value.total_invalid == 2
        assert 99 in exc_info.value.invalid_keys

    def test_warn_mode_does_not_modify_data(
        self,
        dim_barrios: pd.DataFrame,
        fact_precios_invalid: pd.DataFrame,
    ) -> None:
        """Verifica que modo 'warn' no modifica los datos."""
        result_df, result = validate_foreign_keys(
            df=fact_precios_invalid,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_precios",
            strategy="warn",
        )

        # En modo warn, todos los registros deben mantenerse
        assert len(result_df) == len(fact_precios_invalid)
        assert result.invalid_records == 2

    def test_empty_dataframe_returns_empty(
        self,
        dim_barrios: pd.DataFrame,
    ) -> None:
        """Verifica manejo de DataFrame vacío."""
        empty_df = pd.DataFrame(columns=["barrio_id", "anio", "precio_m2_venta"])

        result_df, result = validate_foreign_keys(
            df=empty_df,
            fk_column="barrio_id",
            reference_df=dim_barrios,
            pk_column="barrio_id",
            table_name="fact_precios",
            strategy="filter",
        )

        assert len(result_df) == 0
        assert result.is_valid  # Usamos evaluación booleana
        assert result.total_records == 0

    def test_missing_fk_column_raises_value_error(
        self,
        dim_barrios: pd.DataFrame,
    ) -> None:
        """Verifica que columna FK inexistente lanza ValueError."""
        df = pd.DataFrame({"wrong_column": [1, 2, 3]})

        with pytest.raises(ValueError) as exc_info:
            validate_foreign_keys(
                df=df,
                fk_column="barrio_id",
                reference_df=dim_barrios,
                pk_column="barrio_id",
                table_name="test",
                strategy="filter",
            )

        assert "barrio_id" in str(exc_info.value)


class TestValidateAllFactTables:
    """Tests para la función validate_all_fact_tables."""

    def test_validates_multiple_tables(
        self,
        dim_barrios: pd.DataFrame,
        fact_precios_valid: pd.DataFrame,
    ) -> None:
        """Verifica que valida múltiples tablas correctamente."""
        fact_renta = pd.DataFrame({
            "barrio_id": [1, 2],
            "anio": [2022, 2022],
            "renta_euros": [35000.0, 42000.0],
        })

        (
            precios_out,
            demo_out,
            demo_amp_out,
            renta_out,
            oferta_out,
            results,
        ) = validate_all_fact_tables(
            dim_barrios=dim_barrios,
            fact_precios=fact_precios_valid,
            fact_renta=fact_renta,
            strategy="filter",
        )

        assert len(results) == 2  # precios + renta
        assert all(r.is_valid for r in results)

    def test_handles_none_tables(
        self,
        dim_barrios: pd.DataFrame,
    ) -> None:
        """Verifica que maneja tablas None correctamente."""
        (
            precios_out,
            demo_out,
            demo_amp_out,
            renta_out,
            oferta_out,
            results,
        ) = validate_all_fact_tables(
            dim_barrios=dim_barrios,
            fact_precios=None,
            fact_demografia=None,
            strategy="filter",
        )

        assert len(results) == 0
        assert precios_out is None
        assert demo_out is None


class TestFKValidationResult:
    """Tests para la clase FKValidationResult."""

    def test_pct_invalid_calculation(self) -> None:
        """Verifica cálculo correcto del porcentaje de inválidos."""
        result = FKValidationResult(
            table_name="test",
            fk_column="barrio_id",
            total_records=100,
            valid_records=90,
            invalid_records=10,
        )

        assert result.pct_invalid == 10.0

    def test_pct_invalid_zero_records(self) -> None:
        """Verifica que 0 registros retorna 0% inválido."""
        result = FKValidationResult(
            table_name="test",
            fk_column="barrio_id",
            total_records=0,
            valid_records=0,
            invalid_records=0,
        )

        assert result.pct_invalid == 0.0

    def test_is_valid_property(self) -> None:
        """Verifica la propiedad is_valid."""
        valid_result = FKValidationResult(
            table_name="test",
            fk_column="barrio_id",
            total_records=100,
            valid_records=100,
            invalid_records=0,
        )
        invalid_result = FKValidationResult(
            table_name="test",
            fk_column="barrio_id",
            total_records=100,
            valid_records=90,
            invalid_records=10,
        )

        assert valid_result.is_valid  # Usamos evaluación booleana
        assert not invalid_result.is_valid

    def test_string_representation(self) -> None:
        """Verifica la representación string del resultado."""
        result = FKValidationResult(
            table_name="fact_precios",
            fk_column="barrio_id",
            total_records=100,
            valid_records=95,
            invalid_records=5,
        )

        str_repr = str(result)
        assert "fact_precios" in str_repr
        assert "barrio_id" in str_repr
        assert "INVÁLIDO" in str_repr
        assert "5.0%" in str_repr

