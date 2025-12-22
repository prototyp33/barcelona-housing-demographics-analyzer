"""
Generalitat Extractor Module - Extracción de índice de referencia de alquileres.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

from .base import BaseExtractor, logger


class GeneralitatExtractor(BaseExtractor):
    """
    Extractor para índice de referencia de alquileres de la Generalitat.

    API de referencia (documentación pública):
    https://habitatge.gencat.cat/ca/dades/indicadors-estadistics/

    Nota:
        Esta implementación está diseñada para ser robusta aunque la API
        exacta cambie. Se centralizan las URLs base y parámetros en un
        único método para facilitar ajustes posteriores.
    """

    BASE_URL: str = "https://habitatge.gencat.cat"

    def __init__(
        self,
        rate_limit_delay: float = 1.5,
        output_dir: Optional[Path] = None,
    ) -> None:
        """
        Inicializa el extractor de la Generalitat.

        Args:
            rate_limit_delay: Tiempo de espera entre peticiones HTTP (segundos).
            output_dir: Directorio donde guardar los datos raw.
        """
        super().__init__("Generalitat", rate_limit_delay, output_dir)

    def _build_request_params(self, year: int) -> Dict[str, Any]:
        """
        Construye los parámetros para la petición HTTP del año dado.

        Esta función actúa como punto único de configuración de la API.

        Args:
            year: Año para el que se solicitan datos.

        Returns:
            Diccionario con parámetros para la petición.
        """
        return {
            "year": year,
        }

    def _fetch_year_data(self, year: int) -> pd.DataFrame:
        """
        Descarga datos del índice de referencia para un año concreto.

        Args:
            year: Año a descargar.

        Returns:
            DataFrame con los datos del año (puede estar vacío).

        Raises:
            requests.RequestException: Si la petición HTTP falla.
        """
        # Endpoint genérico; se ajustará cuando se confirmen detalles de la API.
        url = f"{self.BASE_URL}/api/lloguer/indice-referencia"
        params = self._build_request_params(year)

        self._rate_limit()

        logger.info("Solicitando índice de referencia Generalitat para año %s", year)
        response = self.session.get(url, params=params, timeout=60)

        if not self._validate_response(response):
            # _validate_response ya registra logs detallados
            raise requests.RequestException(
                f"Respuesta HTTP no válida para año {year}: "
                f"status={response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            logger.error("Error parseando JSON de Generalitat para año %s: %s", year, exc)
            raise

        # La estructura exacta puede variar; asumimos lista de registros tipo dict.
        if isinstance(data, dict) and "results" in data:
            records: List[Dict[str, Any]] = data.get("results", [])
        elif isinstance(data, list):
            records = data
        else:
            logger.warning(
                "Formato de respuesta inesperado para año %s: %s", year, type(data)
            )
            records = []

        if not records:
            logger.warning(
                "Generalitat: sin registros para año %s en índice de referencia", year
            )
            return pd.DataFrame()

        df = pd.DataFrame.from_records(records)
        df["anio"] = year
        return df

    def extract_indice_referencia(
        self,
        anio_inicio: int,
        anio_fin: int,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extrae el índice de referencia de alquileres para un rango de años.

        Args:
            anio_inicio: Año inicial del rango.
            anio_fin: Año final del rango (inclusive).

        Returns:
            Tupla con:
                - DataFrame combinado con todos los años.
                - Metadata de cobertura por año y estado de la extracción.
        """
        if anio_fin < anio_inicio:
            raise ValueError("anio_fin no puede ser menor que anio_inicio")

        all_frames: List[pd.DataFrame] = []
        years_success: List[int] = []
        years_failed: List[int] = []

        for year in range(anio_inicio, anio_fin + 1):
            try:
                year_df = self._fetch_year_data(year)
                if not year_df.empty:
                    all_frames.append(year_df)
                    years_success.append(year)
                else:
                    years_failed.append(year)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Error extrayendo índice de referencia Generalitat para año %s: %s",
                    year,
                    exc,
                )
                years_failed.append(year)

        coverage: Dict[str, Any] = {
            "requested_range": {"start": anio_inicio, "end": anio_fin},
            "years_success": sorted(years_success),
            "years_failed": sorted(years_failed),
        }

        if not all_frames:
            coverage["success"] = False
            coverage["records"] = 0
            logger.warning(
                "No se obtuvieron datos de índice de referencia de la Generalitat "
                "para el rango %s-%s",
                anio_inicio,
                anio_fin,
            )
            return pd.DataFrame(), coverage

        df_combined = pd.concat(all_frames, ignore_index=True)
        coverage["success"] = True
        coverage["records"] = len(df_combined)

        # Guardar datos raw y registrar en manifest
        self._save_raw_data(
            df_combined,
            filename="generalitat_indice_referencia",
            format="csv",
            year_start=anio_inicio,
            year_end=anio_fin,
            data_type="regulacion",
        )

        logger.info(
            "Índice de referencia Generalitat extraído: %s registros (%s-%s)",
            len(df_combined),
            anio_inicio,
            anio_fin,
        )
        return df_combined, coverage


__all__ = ["GeneralitatExtractor"]


