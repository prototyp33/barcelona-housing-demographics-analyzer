"""
Unit tests para la función _parse_household_size.

Verifica que el parsing de tamaños de hogar funciona correctamente,
especialmente después del fix del regex (Issue #49).
"""

import pytest

from src.etl.transformations.utils import _parse_household_size


class TestParseHouseholdSize:
    """Tests para la función _parse_household_size."""

    def test_returns_none_for_none_input(self) -> None:
        """Verifica que retorna None cuando el input es None."""
        result = _parse_household_size(None)
        assert result is None

    def test_returns_none_for_empty_string(self) -> None:
        """Verifica que retorna None para string vacío."""
        result = _parse_household_size("")
        assert result is None

    def test_returns_none_for_whitespace_string(self) -> None:
        """Verifica que retorna None para string con solo espacios."""
        result = _parse_household_size("   ")
        assert result is None

    def test_returns_none_for_sense_dades(self) -> None:
        """Verifica que retorna None para 'sense dades'."""
        result = _parse_household_size("sense dades")
        assert result is None

    def test_returns_none_for_no_consta(self) -> None:
        """Verifica que retorna None para 'no consta'."""
        result = _parse_household_size("no consta")
        assert result is None

    def test_parses_simple_number(self) -> None:
        """Verifica que parsea correctamente un número simple."""
        result = _parse_household_size("3")
        assert result == 3.0

    def test_parses_number_with_text(self) -> None:
        """Verifica que parsea correctamente un número con texto."""
        result = _parse_household_size("3 personas")
        assert result == 3.0

    def test_parses_number_with_catalan_text(self) -> None:
        """Verifica que parsea correctamente texto en catalán."""
        result = _parse_household_size("3 persones")
        assert result == 3.0

    def test_parses_greater_than_symbol(self) -> None:
        """
        Verifica que parsea correctamente '>' seguido de número.
        
        Este es uno de los casos afectados por el bug del regex.
        """
        result = _parse_household_size(">5")
        assert result is not None
        assert result > 5.0  # Debería ser 5.5 o 6.0

    def test_parses_greater_than_with_space(self) -> None:
        """Verifica que parsea '> 5' con espacio."""
        result = _parse_household_size("> 5")
        assert result is not None
        assert result > 5.0

    def test_parses_o_mes_pattern(self) -> None:
        """
        Verifica que parsea correctamente 'X o més'.
        
        Este patrón es común en datos catalanes de tamaños de hogar.
        """
        result = _parse_household_size("6 o més")
        assert result is not None
        assert result >= 6.0

    def test_parses_mes_de_pattern(self) -> None:
        """
        Verifica que parsea correctamente 'mes de X'.
        
        Otro patrón común en datos catalanes.
        """
        result = _parse_household_size("mes de 4")
        assert result is not None
        assert result >= 4.0

    def test_case_insensitive(self) -> None:
        """Verifica que el parsing es case-insensitive."""
        result_lower = _parse_household_size("3 persones")
        result_upper = _parse_household_size("3 PERSONES")
        result_mixed = _parse_household_size("3 Persones")
        
        assert result_lower == result_upper == result_mixed == 3.0

    def test_handles_leading_trailing_whitespace(self) -> None:
        """Verifica que maneja espacios al inicio y final."""
        result = _parse_household_size("  3  ")
        assert result == 3.0

    def test_returns_none_for_text_without_number(self) -> None:
        """Verifica que retorna None cuando no hay número."""
        result = _parse_household_size("muchas personas")
        assert result is None

    def test_parses_first_number_only(self) -> None:
        """Verifica que usa solo el primer número encontrado."""
        result = _parse_household_size("de 3 a 5 personas")
        assert result == 3.0

    def test_parses_typical_household_sizes(self) -> None:
        """
        Verifica parsing de tamaños de hogar típicos.
        
        Estos son valores reales encontrados en los datos del Portal de Dades.
        """
        test_cases = [
            ("1", 1.0),
            ("2", 2.0),
            ("1 persona", 1.0),
            ("2 persones", 2.0),
            ("3 persones", 3.0),
            ("4 persones", 4.0),
            ("5 persones", 5.0),
        ]
        
        for input_val, expected in test_cases:
            result = _parse_household_size(input_val)
            assert result == expected, f"Falló para '{input_val}': esperado {expected}, obtenido {result}"


class TestParseHouseholdSizeRegexFix:
    """
    Tests específicos para verificar el fix del regex (Issue #49).
    
    El bug era que el regex usaba doble backslash (r"\\\\d+") en vez
    de backslash simple (r"\\d+"), lo que causaba que no se encontraran
    los dígitos correctamente.
    """

    def test_regex_finds_digits_in_simple_case(self) -> None:
        """Verifica que el regex encuentra dígitos en caso simple."""
        result = _parse_household_size("5")
        assert result == 5.0, "El regex debería encontrar el dígito 5"

    def test_regex_finds_digits_after_greater_than(self) -> None:
        """
        Verifica que el regex encuentra dígitos después de '>'.
        
        Este era el caso más afectado por el bug.
        """
        result = _parse_household_size(">6")
        assert result is not None, "El regex debería encontrar el dígito 6 después de '>'"

    def test_regex_finds_digits_in_o_mes_pattern(self) -> None:
        """
        Verifica que el regex encuentra dígitos en patrón 'o més'.
        
        Segundo caso afectado por el bug.
        """
        result = _parse_household_size("7 o més")
        assert result is not None, "El regex debería encontrar el dígito 7 en '7 o més'"

    def test_regex_finds_digits_in_mixed_text(self) -> None:
        """
        Verifica que el regex encuentra dígitos en texto mixto.
        
        Tercer caso afectado por el bug.
        """
        result = _parse_household_size("hogar de 4 personas")
        assert result == 4.0, "El regex debería encontrar el dígito 4"

    def test_multiple_digit_numbers(self) -> None:
        """Verifica que el regex maneja números de múltiples dígitos."""
        result = _parse_household_size("12 persones")
        assert result == 12.0, "El regex debería encontrar '12'"


