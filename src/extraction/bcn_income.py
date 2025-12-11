import io
import logging
import logging.handlers
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

from src.extraction.base import BaseExtractor, LOGS_DIR


class BcnIncomeExtractor(BaseExtractor):
    """
    Extractor de renta per cápita por barrio usando Open Data BCN.

    Descarga los CSV anuales del dataset de renta familiar disponible bruta,
    limpia filas de totales y normaliza al esquema interno.
    """

    MIN_BARRIOS = 65
    # Mapas específicos por año cuando se conozcan URLs exactas
    YEAR_URLS: Dict[int, str] = {
        2015: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "9a69cefe-dcc5-400c-8647-4e438f7ae12b/download/"
            "2015_renda_disponible_llars_per_persona.csv"
        ),
        2016: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "bc48d45b-1046-4496-93c1-fbdac1fd47d0/download/"
            "2016_renda_disponible_llars_per_persona.csv"
        ),
        2017: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "dc0c1ad4-8b5e-4762-b999-2d4ffc95a718/download/"
            "2017_renda_disponible_llars_per_persona.csv"
        ),
        2018: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "9f5a6152-0075-4111-abec-7b5d62655dd3/download/"
            "2018_renda_disponible_llars_per_persona.csv"
        ),
        2019: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "0e205580-6d55-4599-bd13-086de83130b8/download/"
            "2019_renda_disponible_llars_per_persona.csv"
        ),
        2020: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "afe5b67d-7948-4e79-a88c-d51e55fe3ac6/download/"
            "2020_renda_disponible_llars_per_persona.csv"
        ),
        2021: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "e14509ca-9cba-43ec-b925-3beb5c69c2c7/download/"
            "2021_renda_disponible_llars_per_persona.csv"
        ),
        2022: (
            "https://opendata-ajuntament.barcelona.cat/data/dataset/"
            "78db0c75-fa56-4604-9510-8b92834a7fd2/resource/"
            "3df0c5b9-de69-4c94-b924-57540e52932f/download/"
            "2022_renda_disponible_llars_per_persona.csv"
        ),
    }
    URL_PATTERNS: List[str] = [
        # Plantillas conocidas del dataset; se prueban en orden
        (
            "https://opendata-ajuntament.barcelona.cat/resources/"
            "est-renda-familiar-disponible-bruta/est-renda-familiar-disponible-bruta-{year}.csv"
        ),
        (
            "https://opendata-ajuntament.barcelona.cat/resources/"
            "est-renda-familiar-disponible-bruta/renda-familiar-disponible-{year}.csv"
        ),
        (
            "https://opendata-ajuntament.barcelona.cat/resources/"
            "est-renda-familiar-disponible-bruta/renda-disponible-{year}.csv"
        ),
    ]

    def __init__(self, rate_limit_delay: float = 2.0, output_dir: Optional[Path] = None):
        """
        Inicializa el extractor configurando logging y parámetros base.

        Args:
            rate_limit_delay: Tiempo de espera entre peticiones HTTP en segundos (mínimo 2s).
            output_dir: Directorio donde persistir archivos raw.

        Raises:
            ValueError: Si se proporciona un delay negativo.
        """
        if rate_limit_delay < 0:
            raise ValueError("rate_limit_delay no puede ser negativo")

        enforced_delay = max(rate_limit_delay, 2.0)
        super().__init__(
            source_name="bcn",
            rate_limit_delay=enforced_delay,
            output_dir=output_dir,
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            log_file = LOGS_DIR / "bcn_income.log"
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        self.logger.propagate = False

    def extract_income_by_barrio(self, start_year: int, end_year: int) -> pd.DataFrame:
        """
        Extrae la renta per cápita por barrio para el rango indicado.

        Args:
            start_year: Año inicial de la extracción.
            end_year: Año final de la extracción.

        Returns:
            DataFrame con columnas [codigo_barrio, barrio_nombre, anio,
            renta_per_capita, fuente].

        Raises:
            RuntimeError: Si no se pudo descargar ningún año.
            ValueError: Si la cobertura de barrios es insuficiente o datos no numéricos.
            requests.RequestException: Si ocurre un error de red no recuperable.
        """
        frames: List[pd.DataFrame] = []
        for year in range(start_year, end_year + 1):
            df_year = self._fetch_year(year)
            if df_year is None:
                self.logger.warning("No se pudo obtener datos para %s", year)
                continue
            frames.append(df_year)

        if not frames:
            raise RuntimeError("No se pudo obtener ningún CSV de renta desde Open Data BCN")

        result = pd.concat(frames, ignore_index=True)
        barrio_count = result["codigo_barrio"].nunique()
        if barrio_count < self.MIN_BARRIOS:
            raise ValueError(
                f"Cobertura insuficiente de barrios ({barrio_count} < {self.MIN_BARRIOS})"
            )

        self.logger.info("Extracción completada con %s registros", len(result))
        return result

    def save(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Persiste los datos de renta extraídos utilizando las utilidades base.

        Args:
            df: DataFrame con datos de renta ya transformados.
            filename: Prefijo de nombre de archivo a utilizar.

        Returns:
            Ruta del archivo guardado.
        """
        return self._save_raw_data(
            data=df,
            filename=filename,
            format="csv",
            data_type="renta",
            year_start=int(df["anio"].min()) if not df.empty else None,
            year_end=int(df["anio"].max()) if not df.empty else None,
        )

    def _fetch_year(self, year: int) -> Optional[pd.DataFrame]:
        """
        Descarga y transforma el CSV de un año concreto probando múltiples URLs.

        Args:
            year: Año objetivo.

        Returns:
            DataFrame transformado para el año, o None si fallan todas las URLs.
        """
        last_error: Optional[Exception] = None
        for url in self._build_candidate_urls(year):
            self._rate_limit()
            try:
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                time.sleep(2)  # Cumplir rate limiting explícito
            except requests.RequestException as exc:
                self.logger.warning("Fallo al descargar %s: %s", url, exc)
                last_error = exc
                continue

            try:
                df_raw = self._read_csv_response(response)
                df_clean = self._clean_and_map(df_raw, year)
                return df_clean
            except ValueError as exc:
                self.logger.error("CSV inválido para %s: %s", url, exc)
                last_error = exc
                continue
            except Exception as exc:  # noqa: BLE001
                self.logger.error("Error inesperado limpiando CSV %s: %s", url, exc, exc_info=True)
                last_error = exc
                continue

        if last_error:
            if isinstance(last_error, ValueError):
                raise last_error
            if isinstance(last_error, requests.RequestException):
                raise last_error
        return None

    def _build_candidate_urls(self, year: int) -> List[str]:
        """
        Genera URLs posibles para un año dado usando patrones conocidos.

        Args:
            year: Año a interpolar.

        Returns:
            Lista de URLs posibles en orden de prioridad.
        """
        candidates: List[str] = []
        direct = self.YEAR_URLS.get(year)
        if direct:
            candidates.append(direct)
        candidates.extend(pattern.format(year=year) for pattern in self.URL_PATTERNS)
        return candidates

    def _read_csv_response(self, response: requests.Response) -> pd.DataFrame:
        """
        Lee un CSV desde la respuesta HTTP, soportando separador ';' o ','.

        Args:
            response: Respuesta HTTP con contenido CSV.

        Returns:
            DataFrame con los datos crudos del CSV.

        Raises:
            ValueError: Si no se puede parsear el CSV.
        """
        text = response.text
        required = {"Nom_Barri", "Codi_Barri", "Import_Euros"}
        for sep in (";", ","):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                if not df.empty and required.issubset(df.columns):
                    return df
            except Exception:
                continue
        raise ValueError("No se pudo leer el CSV con separadores estándar (; o ,)")

    def _clean_and_map(self, df: pd.DataFrame, year: int) -> pd.DataFrame:
        """
        Limpia filas de totales y normaliza columnas al esquema interno.

        Args:
            df: DataFrame crudo del CSV.
            year: Año asociado al CSV.

        Returns:
            DataFrame normalizado con columnas finales.

        Raises:
            ValueError: Si faltan columnas requeridas o valores no numéricos.
        """
        required_cols = {"Nom_Barri", "Codi_Barri", "Import_Euros"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Columnas requeridas ausentes: {missing}")

        df_work = df.copy()

        # Eliminar filas de totales y entradas sin código de barrio
        df_work = df_work[df_work["Codi_Barri"].notna()]
        df_work["Codi_Barri"] = pd.to_numeric(df_work["Codi_Barri"], errors="coerce")
        df_work = df_work[df_work["Codi_Barri"].between(1, 73, inclusive="both")]

        df_work["Nom_Barri"] = df_work["Nom_Barri"].astype(str)
        df_work = df_work[~df_work["Nom_Barri"].str.lower().str.contains("total")]

        df_work["Import_Euros"] = pd.to_numeric(df_work["Import_Euros"], errors="coerce")
        if df_work["Import_Euros"].isna().any():
            raise ValueError("Valores no numéricos detectados en Import_Euros")

        df_work = df_work.rename(
            columns={
                "Codi_Barri": "codigo_barrio",
                "Nom_Barri": "barrio_nombre",
                "Import_Euros": "renta_per_capita",
            }
        )
        df_work["anio"] = year
        df_work["fuente"] = "OpenDataBCN"

        columns = [
            "codigo_barrio",
            "barrio_nombre",
            "anio",
            "renta_per_capita",
            "fuente",
        ]
        return df_work[columns]

