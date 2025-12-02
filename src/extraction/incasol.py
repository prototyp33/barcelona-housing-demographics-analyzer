"""
Incasol Socrata Extractor Module - Extracción de datos de alquiler desde
Dades Obertes Catalunya (Generalitat) basados en fianzas de Incasòl.
"""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

from .base import BaseExtractor, logger


class IncasolSocrataExtractor(BaseExtractor):
    """
    Extractor de datos de alquiler (mercado de lloguer) desde Dades Obertes Catalunya.

    Este extractor está pensado para consumir datasets Socrata que exponen
    series históricas de alquiler basadas en fianzas de Incasòl, con
    granularidad al menos a nivel de barrio y trimestre.
    """

    BASE_URL = "https://analisi.transparenciacatalunya.cat/resource"

    def __init__(
        self,
        dataset_id: str,
        rate_limit_delay: float = 1.5,
        output_dir: Optional["Path"] = None,
        app_token: Optional[str] = None,
    ) -> None:
        """
        Inicializa el extractor de Incasòl (Socrata).

        Args:
            dataset_id: Identificador del dataset en Socrata
                (ej. 'xxxx-xxxx').
            rate_limit_delay: Tiempo de espera entre peticiones.
            output_dir: Directorio base para guardar datos raw.
            app_token: Token opcional de aplicación para la API Socrata.
        """
        super().__init__("incasol", rate_limit_delay, output_dir)
        self.dataset_id = dataset_id
        self.app_token = app_token

    def _build_headers(self) -> Dict[str, str]:
        """
        Construye las cabeceras HTTP para la petición a Socrata.

        Returns:
            Diccionario de cabeceras.
        """
        headers: Dict[str, str] = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        return headers

    def _fetch_page(
        self,
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Descarga una página de resultados desde la API Socrata.

        Args:
            params: Parámetros de consulta (incluyendo $limit, $offset, etc.).

        Returns:
            Lista de registros (dict) devueltos por la API.
        """
        url = f"{self.BASE_URL}/{self.dataset_id}.json"
        self._rate_limit()

        headers = self._build_headers()
        response: requests.Response = self.session.get(
            url,
            headers=headers,
            params=params,
            timeout=60,
        )

        if not self._validate_response(response):
            return []

        try:
            data = response.json()
            if isinstance(data, list):
                return data
            logger.warning("Respuesta Socrata no es una lista, devolviendo vacía")
            return []
        except Exception as exc:  # pragma: no cover - error raro de parseo
            logger.error(f"Error parseando respuesta Socrata: {exc}")
            return []

    def get_rent_by_neighborhood_quarter(
        self,
        year_start: int,
        year_end: int,
        min_contracts: int = 0,
        limit_per_page: int = 50000,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Obtiene la serie histórica de alquiler por barrio y trimestre.

        Esta implementación es genérica y asume un dataset Socrata con:
        - Alguna columna de año (ej. 'any', 'year')
        - Alguna columna de trimestre (ej. 'trimestre', 'quarter')
        - Columnas de barrio (código y nombre)
        - Columnas de precio y nº de contratos

        La normalización de nombres de columna se hace de forma heurística.

        Args:
            year_start: Año inicial (inclusive).
            year_end: Año final (inclusive).
            min_contracts: Umbral mínimo de contratos por punto de datos
                (0 = no filtrar).
            limit_per_page: Límite de filas por página (paginación Socrata).

        Returns:
            Tupla (df, metadata) donde:
                - df: DataFrame con columnas como mínimo:
                    - barrio_id o Codi_Barri
                    - Nom_Barri
                    - anio
                    - quarter
                    - rent_month
                    - rent_m2
                    - contracts
                - metadata: información de cobertura y estrategia usada.
        """
        metadata: Dict[str, Any] = {
            "source": "dades_obertes_catalunya_incasol",
            "strategy_used": "socrata_api",
            "success": False,
            "requested_range": {"start": year_start, "end": year_end},
            "dataset_id": self.dataset_id,
        }

        logger.info(
            "Extrayendo datos de alquiler desde Socrata "
            f"(dataset_id={self.dataset_id}, {year_start}-{year_end})",
        )

        all_rows: List[Dict[str, Any]] = []
        offset = 0

        # Construir filtro de años genérico (asumiendo columna 'any' o 'year')
        # La normalización fina se hará después.
        # Aquí solo restringimos el volumen de datos descargados.
        where_clauses = [
            f"any >= {year_start}",
            f"any <= {year_end}",
        ]
        where_expr = " AND ".join(where_clauses)

        while True:
            params: Dict[str, Any] = {
                "$limit": limit_per_page,
                "$offset": offset,
                "$where": where_expr,
            }

            page = self._fetch_page(params)
            if not page:
                break

            all_rows.extend(page)
            logger.debug(
                "Página descargada desde Socrata: "
                f"{len(page)} registros (offset={offset})",
            )

            if len(page) < limit_per_page:
                break

            offset += limit_per_page

        if not all_rows:
            logger.warning("No se obtuvieron datos desde Socrata")
            metadata["error"] = "No data"
            return pd.DataFrame(), metadata

        df_raw = pd.DataFrame(all_rows)

        # Heurísticas de detección de columnas
        def _find_col(candidates: List[str]) -> Optional[str]:
            for col in df_raw.columns:
                low = col.lower()
                if any(token in low for token in candidates):
                    return col
            return None

        year_col = _find_col(["any", "year", "anio"])
        quarter_col = _find_col(["trimestre", "quarter"])
        barrio_code_col = _find_col(["codi_barri", "codi barri", "codi_bar", "codi_territorial"])
        barrio_name_col = _find_col(["nom_barri", "nom barri", "barri", "barrio"])
        rent_month_col = _find_col(["lloguer_mitja_mensual", "lloguer mitja mensual", "rent_month"])
        rent_m2_col = _find_col(["lloguer_mitja_per_superficie", "lloguer mitja per superficie", "€/m2", "m2"])
        contracts_col = _find_col(["nombre_contractes", "n_contractes", "num_contractes", "contracts"])

        # Convertir a numérico donde tenga sentido
        if year_col and year_col in df_raw.columns:
            df_raw[year_col] = pd.to_numeric(df_raw[year_col], errors="coerce")
        if quarter_col and quarter_col in df_raw.columns:
            df_raw[quarter_col] = pd.to_numeric(df_raw[quarter_col], errors="coerce")
        if rent_month_col and rent_month_col in df_raw.columns:
            df_raw[rent_month_col] = pd.to_numeric(df_raw[rent_month_col], errors="coerce")
        if rent_m2_col and rent_m2_col in df_raw.columns:
            df_raw[rent_m2_col] = pd.to_numeric(df_raw[rent_m2_col], errors="coerce")
        if contracts_col and contracts_col in df_raw.columns:
            df_raw[contracts_col] = pd.to_numeric(df_raw[contracts_col], errors="coerce")

        # Filtro fino por rango de años
        if year_col and year_col in df_raw.columns:
            df_raw = df_raw[
                (df_raw[year_col] >= year_start) &
                (df_raw[year_col] <= year_end)
            ]

        # Filtro por nº mínimo de contratos
        if min_contracts > 0 and contracts_col and contracts_col in df_raw.columns:
            before = len(df_raw)
            df_raw = df_raw[df_raw[contracts_col] >= min_contracts]
            logger.info(
                "Aplicado filtro por contratos (>= %s): %s -> %s registros",
                min_contracts,
                before,
                len(df_raw),
            )

        if df_raw.empty:
            logger.warning("Datos vacíos después de filtros de año/contratos")
            metadata["error"] = "Empty after filters"
            return pd.DataFrame(), metadata

        # Construir DataFrame normalizado
        df_norm = pd.DataFrame()

        if barrio_code_col and barrio_code_col in df_raw.columns:
            df_norm["Codi_Barri"] = df_raw[barrio_code_col]
        if barrio_name_col and barrio_name_col in df_raw.columns:
            df_norm["Nom_Barri"] = df_raw[barrio_name_col]

        if year_col and year_col in df_raw.columns:
            df_norm["anio"] = df_raw[year_col].astype("Int64")
        if quarter_col and quarter_col in df_raw.columns:
            df_norm["quarter"] = df_raw[quarter_col].astype("Int64")

        if rent_month_col and rent_month_col in df_raw.columns:
            df_norm["rent_month"] = df_raw[rent_month_col]
        if rent_m2_col and rent_m2_col in df_raw.columns:
            df_norm["rent_m2"] = df_raw[rent_m2_col]
        if contracts_col and contracts_col in df_raw.columns:
            df_norm["contracts"] = df_raw[contracts_col].astype("Int64")

        # Registrar columnas originales útiles por si se necesitan en transform
        metadata["raw_columns"] = list(df_raw.columns)

        if "anio" in df_norm.columns:
            available_years = sorted(df_norm["anio"].dropna().unique().tolist())
            metadata["available_years"] = available_years

        metadata["records"] = len(df_norm)
        metadata["success"] = True

        # Guardar datos raw normalizados (no el JSON crudo) para facilitar ETL
        self._save_raw_data(
            df_norm,
            "incasol_rent",
            "csv",
            year_start=year_start,
            year_end=year_end,
            data_type="prices_alquiler",
        )

        logger.info(
            "✅ Datos de alquiler Incasòl (Socrata) extraídos: %s registros",
            len(df_norm),
        )

        return df_norm, metadata


