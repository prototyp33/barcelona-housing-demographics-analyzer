"""Funciones auxiliares compartidas para transformaciones ETL.

Centraliza utilidades que se usan en varios módulos de transformaciones:
- Logger y ``HousingCleaner``
- Parsing de tamaños de hogar
- Carga de CSV del Portal de Dades con detección de encoding
- Búsqueda de ficheros e interpretación de timestamps de Portal de Dades
- Normalización y mapeo de territorios a ``barrio_id``
- Helpers de edad y nacionalidad
"""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.transform.cleaners import HousingCleaner


logger = logging.getLogger(__name__)

# Inicializar cleaner compartido para todas las transformaciones
cleaner = HousingCleaner()


def _parse_household_size(label: Optional[str]) -> Optional[float]:
    """Convierte el descriptor de tamaño de hogar en un valor numérico aproximado."""

    if label is None:
        return None
    normalized = str(label).strip().lower()
    if not normalized or normalized in {"sense dades", "no consta"}:
        return None

    if normalized.startswith(">"):
        digits = re.findall(r"\d+", normalized)
        if digits:
            return max(float(digits[0]) + 1.0, float(digits[0]) + 0.5)
        return None

    if "o més" in normalized or "mes de" in normalized:
        digits = re.findall(r"\d+", normalized)
        if digits:
            base = float(digits[0])
            return max(base, base + 1.0)
        return None

    digits = re.findall(r"\d+", normalized)
    if digits:
        return float(digits[0])

    return None


def _load_portaldades_csv(filepath: Path) -> pd.DataFrame:
    """Carga un archivo CSV del Portal de Dades con detección automática de encoding."""
    try:
        import chardet
    except ImportError:
        logger.warning(
            "Module 'chardet' not found. Falling back to 'utf-8'. "
            "Install it with 'pip install chardet'.",
        )
        return pd.read_csv(filepath, encoding="utf-8", low_memory=False)

    # Detectar encoding
    with open(filepath, "rb") as file:
        raw_data = file.read(10000)
        detected = chardet.detect(raw_data)
        encoding = detected.get("encoding", "utf-8")

    # Intentar leer con diferentes encodings
    encodings_to_try = [encoding, "utf-8", "latin-1", "iso-8859-1"]
    for enc in encodings_to_try:
        try:
            return pd.read_csv(filepath, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue

    raise ValueError(f"No se pudo leer el archivo {filepath} con ningún encoding")


def _append_tag(current: Optional[str], new_tag: str) -> str:
    """Agrega una etiqueta de forma idempotente a una cadena delimitada por '|'."
    """
    if not new_tag:
        return "" if current is None or pd.isna(current) else str(current)

    tags: List[str] = []
    if current is not None and not pd.isna(current):
        tags = [token for token in str(current).split("|") if token]
    if new_tag not in tags:
        tags.append(new_tag)
    return "|".join(tags)


def _find_portaldades_file(portaldades_dir: Path, indicator_id: str) -> Optional[Path]:
    """Devuelve la última versión disponible de un indicador del Portal de Dades."""
    pattern = f"portaldades_*_{indicator_id}.csv"
    candidates = sorted(portaldades_dir.glob(pattern), key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def _extract_year_from_temps(temps_str: str) -> Optional[int]:
    """Extrae el año de una cadena de tiempo ISO del Portal de Dades."""
    try:
        dt_value = datetime.fromisoformat(temps_str.replace("Z", "+00:00"))
        return dt_value.year
    except (ValueError, AttributeError, TypeError):
        return None


def _map_territorio_to_barrio_id(
    territorio: str,
    territorio_type: str,
    dim_barrios: pd.DataFrame,
) -> Optional[int]:
    """
    Mapea un nombre de territorio del Portal de Dades a un ``barrio_id``.

    Args:
        territorio: Nombre del territorio (barrio, distrito, municipio).
        territorio_type: Tipo de territorio (\"Barri\", \"Districte\", \"Municipi\").
        dim_barrios: DataFrame con la dimensión de barrios.

    Returns:
        ``barrio_id`` si se encuentra, ``None`` si no.
    """
    if territorio_type == "Barri":
        territorio_normalizado = cleaner.normalize_neighborhoods(territorio)

        alias_target = cleaner.barrio_alias_overrides.get(territorio_normalizado)
        if alias_target:
            match = dim_barrios[
                dim_barrios["barrio_nombre_normalizado"] == alias_target
            ]
            if not match.empty:
                return int(match.iloc[0]["barrio_id"])

        match = dim_barrios[
            dim_barrios["barrio_nombre_normalizado"] == territorio_normalizado
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])

        match = dim_barrios[
            dim_barrios["barrio_nombre"]
            .str.strip()
            .str.lower()
            == territorio.strip().lower()
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])

        match = dim_barrios[
            dim_barrios["barrio_nombre"].str.contains(
                territorio,
                case=False,
                na=False,
                regex=False,
            )
        ]
        if not match.empty:
            match = match.sort_values("barrio_nombre", key=lambda series: series.str.len())
            return int(match.iloc[0]["barrio_id"])

        territorio_parts = territorio_normalizado.split()
        if len(territorio_parts) > 1:
            for part in territorio_parts:
                if len(part) > 3:
                    match = dim_barrios[
                        dim_barrios["barrio_nombre_normalizado"].str.contains(
                            part,
                            na=False,
                            regex=False,
                        )
                    ]
                    if not match.empty:
                        match = match.sort_values(
                            "barrio_nombre",
                            key=lambda series: series.str.len(),
                        )
                        return int(match.iloc[0]["barrio_id"])

        candidates = dim_barrios["barrio_nombre_normalizado"].dropna().unique().tolist()
        close = get_close_matches(territorio_normalizado, candidates, n=1, cutoff=0.8)
        if close:
            match = dim_barrios[
                dim_barrios["barrio_nombre_normalizado"] == close[0]
            ]
            if not match.empty:
                logger.info(
                    "Fuzzy match: '%s' -> '%s'",
                    territorio,
                    match.iloc[0]["barrio_nombre"],
                )
                return int(match.iloc[0]["barrio_id"])

        logger.warning(
            "No se pudo mapear el territorio '%s' (normalizado: '%s') a ningún barrio "
            "conocido.",
            territorio,
            territorio_normalizado,
        )
        return None

    if territorio_type == "Districte":
        # No asignamos distritos directamente a un solo barrio para evitar sesgos.
        return None

    # Para municipio u otros niveles agregados, no mapeamos.
    return None


def _edad_quinquenal_to_range(edad_q: int) -> Tuple[int, int]:
    """
    Convierte código de edad quinquenal (EDAT_Q) a rango de edad.

    Args:
        edad_q: Código de edad quinquenal (0-20).

    Returns:
        Tupla (edad_min, edad_max).
    """
    if edad_q < 0 or edad_q > 20:
        return (0, 0)
    edad_min = edad_q * 5
    edad_max = edad_min + 4 if edad_q < 20 else 999
    return (edad_min, edad_max)


def _edad_quinquenal_to_custom_group(edad_q: int) -> Optional[str]:
    """
    Agrupa edad quinquenal en grupos personalizados.

    Args:
        edad_q: Código de edad quinquenal (0-20).

    Returns:
        Grupo de edad personalizado o ``None`` si no aplica.
    """
    edad_min, _ = _edad_quinquenal_to_range(edad_q)

    if 18 <= edad_min <= 34:
        return "18-34"
    if 35 <= edad_min <= 49:
        return "35-49"
    if 50 <= edad_min <= 64:
        return "50-64"
    if edad_min >= 65:
        return "65+"
    return None


def _map_continente_to_nacionalidad(continente_code: int) -> str:
    """
    Mapea código de continente de nacimiento a categoría de nacionalidad.

    Args:
        continente_code: Código de continente (1-5, 999).

    Returns:
        Categoría de nacionalidad.
    """
    mapping = {
        1: "Europa",
        2: "América",
        3: "África",
        4: "Asia",
        5: "Oceanía",
        999: "No consta",
    }
    return mapping.get(continente_code, "Desconocido")


__all__ = [
    "logger",
    "cleaner",
    "_parse_household_size",
    "_load_portaldades_csv",
    "_append_tag",
    "_find_portaldades_file",
    "_extract_year_from_temps",
    "_map_territorio_to_barrio_id",
    "_edad_quinquenal_to_range",
    "_edad_quinquenal_to_custom_group",
    "_map_continente_to_nacionalidad",
]


