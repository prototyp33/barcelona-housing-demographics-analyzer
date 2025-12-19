"""
Script para extraer características de edificios en Gràcia usando API SOAP oficial del Catastro.

ACTUALIZADO: Usa API SOAP oficial (100% gratuita, sin API key)
Eliminada dependencia de catastro-api.es (servicio de terceros)

Criterios de Aceptación:
    ✓ ≥50 registros extraídos
    ✓ Columnas: referencia_catastral, superficie_m2, ano_construccion, plantas
    ✓ Completitud ≥70% en campos críticos
    ✓ Fuente oficial del Catastro (sin terceros)

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import sys

import pandas as pd

# Añadir directorio de scripts al PYTHONPATH para importar catastro_soap_client
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_soap_client import CatastroSOAPClient, CatastroSOAPError


LOG_DIR = Path("spike-data-validation/data/logs")
RAW_DIR = Path("spike-data-validation/data/raw")

LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    Configura logging para el script de extracción catastral.
    """
    log_path = LOG_DIR / "catastro_extraction.log"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


@dataclass
class SeedConfig:
    """
    Configuración de referencias catastrales iniciales (seed) para Gràcia.

    Attributes:
        seed_file: Ruta del CSV con referencias catastrales de Gràcia.
        max_records: Número máximo de referencias a procesar.
    """

    seed_file: Path = RAW_DIR / "gracia_refs_seed.csv"
    max_records: int = 100


def _to_optional_float(value: object) -> Optional[float]:
    """
    Convierte un valor a float opcional.

    Args:
        value: Valor a convertir.

    Returns:
        Float si es convertible y no es nulo, en caso contrario None.
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        # pd.isna puede fallar con ciertos tipos no soportados
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_seed_refs(config: SeedConfig) -> List[Dict[str, Any]]:
    """
    Carga el CSV de referencias catastrales de entrada.

    El archivo debe contener al menos una columna ``referencia_catastral`` y,
    opcionalmente, una columna ``direccion``. Si incluye ``lat`` y ``lon``,
    el extractor puede operar en modo alternativo por coordenadas (Consulta_RCCOOR),
    útil mientras `Consulta_DNPRC` está fallando (Issue #200).

    Args:
        config: Configuración con ruta y límite de registros.

    Returns:
        Lista de diccionarios con claves:
        - referencia_catastral
        - direccion (opcional)
        - lat, lon (opcionales)
        - metodo (opcional)

    Raises:
        FileNotFoundError: Si el CSV de seeds no existe.
        ValueError: Si faltan columnas requeridas.
    """
    if not config.seed_file.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de seeds de Gràcia: {config.seed_file}",
        )

    df = pd.read_csv(config.seed_file)
    if df.empty:
        raise ValueError("El archivo de seeds de Gràcia está vacío")

    df = df.copy()
    if "referencia_catastral" not in df.columns:
        raise ValueError(
            "El archivo de seeds debe contener la columna 'referencia_catastral'",
        )

    if len(df) > config.max_records:
        logger.info(
            "Archivo de seeds con %s filas, se limitará a las primeras %s",
            len(df),
            config.max_records,
        )
        df = df.iloc[: config.max_records]

    records: List[Dict[str, str]] = []
    # #region agent log
    import json
    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H4","location":"extract_catastro_gracia.py:load_seed_refs","message":"Analizando formato referencias","data":{"total_refs":len(df),"sample_refs":df["referencia_catastral"].head(3).tolist(),"sample_lens":[len(str(r)) for r in df["referencia_catastral"].head(3)]},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    # #endregion

    # #region agent log
    import time
    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run7","hypothesisId":"COORD_SEED","location":"extract_catastro_gracia.py:load_seed_refs","message":"Columnas seed detectadas","data":{"columns":df.columns.tolist(),"has_lat":("lat" in df.columns),"has_lon":("lon" in df.columns)},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion
    
    for _, row in df.iterrows():
        ref_raw = str(row["referencia_catastral"]).strip()
        # #region agent log
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"extract_catastro_gracia.py:load_seed_refs","message":"Procesando referencia","data":{"ref":ref_raw,"len":len(ref_raw)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        lat = _to_optional_float(row.get("lat"))
        lon = _to_optional_float(row.get("lon"))
        records.append(
            {
                "referencia_catastral": ref_raw,
                "direccion": str(row.get("direccion", "")).strip() or None,
                "lat": lat,
                "lon": lon,
                "metodo": str(row.get("metodo", "")).strip() or None,
                "barrio_id_seed": int(row.get("barrio_id")) if str(row.get("barrio_id", "")).strip().isdigit() else None,
                "barrio_nombre_seed": str(row.get("barrio_nombre", "")).strip() or None,
            }
        )

    logger.info("Cargadas %s referencias catastrales seed para Gràcia", len(records))
    return records


def enrich_with_catastro(
    client: CatastroSOAPClient,
    seed_refs: Iterable[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Enriquecen las referencias catastrales con datos de Catastro usando API SOAP oficial.

    Nota:
        Mientras `Consulta_DNPRC` esté caído (error 12), este método soporta un modo alternativo:
        si el seed incluye `lat` y `lon`, se consultará `Consulta_RCCOOR` para obtener al menos
        referencia + dirección.

    Args:
        client: Cliente SOAP oficial del Catastro.
        seed_refs: Iterable con diccionarios de seeds.

    Returns:
        DataFrame con columnas mínimas: ``referencia_catastral``, ``superficie_m2``,
        ``ano_construccion``, ``uso_principal``, ``direccion_normalizada``.
    """
    seeds_list = list(seed_refs)

    # Separar seeds con coordenadas vs sin coordenadas (permite seed mixto)
    coord_seeds: List[Tuple[float, float, Dict[str, Any]]] = []
    rc_seeds: List[Dict[str, Any]] = []
    for seed in seeds_list:
        lat = seed.get("lat")
        lon = seed.get("lon")
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            coord_seeds.append((float(lon), float(lat), seed))
        else:
            rc_seeds.append(seed)

    # #region agent log
    import time
    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"run7","hypothesisId":"COORD_FALLBACK","location":"extract_catastro_gracia.py:enrich_with_catastro","message":"Clasificando seed","data":{"total":len(seeds_list),"with_coords":len(coord_seeds),"without_coords":len(rc_seeds)},"timestamp":int(time.time()*1000)}) + '\n')
    # #endregion

    registros: List[Dict[str, Any]] = []

    # 1) Modo alternativo por coordenadas (Consulta_RCCOOR)
    if coord_seeds:
        logger.warning(
            "Seed con coordenadas detectado (%s filas). Activando modo alternativo por coordenadas "
            "(Consulta_RCCOOR). Nota: no devuelve superficie/año/uso.",
            len(coord_seeds),
        )

        for lon, lat, seed in coord_seeds:
            try:
                building = client.get_building_by_coordinates(lon=lon, lat=lat)
                if not building:
                    continue

                building = dict(building)
                building["lat"] = lat
                building["lon"] = lon
                building["direccion_seed"] = seed.get("direccion")
                building["metodo_seed"] = seed.get("metodo")
                building["barrio_id_seed"] = seed.get("barrio_id_seed")
                building["barrio_nombre_seed"] = seed.get("barrio_nombre_seed")
                registros.append(building)
            except CatastroSOAPError as exc:
                logger.warning("✗ Error consultando por coordenadas (%s,%s): %s", lon, lat, exc)
                continue

    # 2) Modo por RC (Consulta_DNPRC) - puede fallar actualmente
    if rc_seeds:
        referencias = [str(seed.get("referencia_catastral", "")).strip() for seed in rc_seeds]
        referencias = [r for r in referencias if r]
        direcciones_seed = {seed["referencia_catastral"]: seed.get("direccion") for seed in rc_seeds}

        if referencias:
            logger.info("Iniciando extracción batch desde API SOAP oficial (por RC)...")
            registros_rc = client.get_buildings_batch(
                referencias=referencias,
                continue_on_error=True,
                delay_seconds=1.0,  # 1 segundo entre peticiones
            )

            for registro in registros_rc:
                ref = registro.get("referencia_catastral")
                if ref and ref in direcciones_seed:
                    registro["direccion_seed"] = direcciones_seed[ref]
                registros.append(registro)

    if not registros:
        logger.warning("No se pudo enriquecer ninguna referencia catastral")
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    df = df.copy()

    # Validación de tipos y nulos siguiendo los estándares del proyecto
    for col in ["superficie_m2", "ano_construccion"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Mapear plantas desde uso_principal si está disponible (el SOAP no siempre devuelve plantas)
    # Por ahora, dejamos plantas como None si no está disponible
    if "plantas" not in df.columns:
        df["plantas"] = None

    # Asegurar columnas útiles del modo alternativo
    for col in ["lat", "lon", "metodo", "nota", "metodo_seed", "direccion_seed"]:
        if col not in df.columns:
            df[col] = None

    logger.info(
        "Total de registros enriquecidos con Catastro SOAP: %s (superficie_m2 not null: %s)",
        len(df),
        df["superficie_m2"].notna().sum() if "superficie_m2" in df.columns else 0,
    )

    return df


def save_catastro_data(df: pd.DataFrame) -> Path:
    """
    Guarda el DataFrame de atributos catastrales en CSV.

    Args:
        df: DataFrame con datos enriquecidos.

    Returns:
        Ruta del archivo CSV generado.
    """
    # Si el dataset viene principalmente de coordenadas, guardarlo separado
    modo_coords = "metodo" in df.columns and df["metodo"].astype(str).str.contains("coordenadas").any()
    output_path = RAW_DIR / ("catastro_gracia_coords.csv" if modo_coords else "catastro_gracia.csv")
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Datos catastrales de Gràcia guardados en %s", output_path)
    return output_path


def write_summary(df: pd.DataFrame) -> Path:
    """
    Genera un resumen estadístico de los datos de Catastro para Gràcia.

    Args:
        df: DataFrame con atributos catastrales.

    Returns:
        Ruta del archivo JSON de resumen.
    """
    def _safe_float(series: pd.Series) -> Optional[float]:
        series_num = pd.to_numeric(series, errors="coerce")
        if not series_num.notna().any():
            return None
        value = float(series_num.mean())
        return value if pd.notna(value) else None

    def _safe_min(series: pd.Series) -> Optional[float]:
        series_num = pd.to_numeric(series, errors="coerce")
        if not series_num.notna().any():
            return None
        value = float(series_num.min())
        return value if pd.notna(value) else None

    def _safe_max(series: pd.Series) -> Optional[float]:
        series_num = pd.to_numeric(series, errors="coerce")
        if not series_num.notna().any():
            return None
        value = float(series_num.max())
        return value if pd.notna(value) else None

    if df.empty:
        summary: Dict[str, object] = {
            "total_registros": 0,
            "superficie_media": None,
            "superficie_min": None,
            "superficie_max": None,
            "ano_construccion_min": None,
            "ano_construccion_max": None,
            "plantas_media": None,
            "warning": "DataFrame vacío tras enriquecimiento",
        }
    else:
        modo = None
        if "metodo" in df.columns and df["metodo"].astype(str).str.contains("coordenadas").any():
            modo = "coordenadas"
        elif "metodo" in df.columns and df["metodo"].notna().any():
            modo = str(df["metodo"].dropna().iloc[0])

        summary = {
            "total_registros": int(len(df)),
            "modo_extraccion": modo,
            "superficie_media": _safe_float(df["superficie_m2"]) if "superficie_m2" in df.columns else None,
            "superficie_min": _safe_min(df["superficie_m2"]) if "superficie_m2" in df.columns else None,
            "superficie_max": _safe_max(df["superficie_m2"]) if "superficie_m2" in df.columns else None,
            "ano_construccion_min": int(df["ano_construccion"].min())
            if df["ano_construccion"].notna().any()
            else None,
            "ano_construccion_max": int(df["ano_construccion"].max())
            if df["ano_construccion"].notna().any()
            else None,
            "plantas_media": float(df["plantas"].mean())
            if "plantas" in df.columns and df["plantas"].notna().any()
            else None,
            "campos_criticos_disponibles": bool(
                "superficie_m2" in df.columns
                and df["superficie_m2"].notna().any()
                and "ano_construccion" in df.columns
                and df["ano_construccion"].notna().any()
            ),
        }

    summary_path = LOG_DIR / "catastro_extraction_summary_200.json"
    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    logger.info("Resumen Catastro Gràcia guardado en %s", summary_path)

    if summary["total_registros"] < 50:
        logger.warning(
            "Solo se extrajeron %s registros catastrales (objetivo: ≥50).",
            summary["total_registros"],
        )
    else:
        logger.info(
            "✓ Criterio de tamaño cumplido: %s registros (≥50).",
            summary["total_registros"],
        )

    if summary.get("campos_criticos_disponibles") is False:
        logger.warning(
            "⚠️ Campos críticos (superficie/año) no disponibles. "
            "Esto es esperado si se usó modo coordenadas por caída de Consulta_DNPRC.",
        )

    return summary_path


def main() -> int:
    """
    Función principal para el Issue #200.

    Orquesta la carga de seeds, la consulta a API SOAP oficial del Catastro
    y el guardado de resultados para Gràcia.

    Returns:
        Código de salida (0 si éxito, 1 si error).
    """
    setup_logging()
    logger.info("=== Issue #200: Extracción de atributos catastrales para Gràcia ===")
    logger.info("Usando API SOAP oficial del Catastro (100% gratuita, sin API key)")

    try:
        seed_config = SeedConfig()
        seed_refs = load_seed_refs(seed_config)

        # Inicializar cliente SOAP oficial (no requiere API key)
        client = CatastroSOAPClient()
        logger.info("✓ Cliente SOAP oficial inicializado correctamente")

        df_catastro = enrich_with_catastro(client, seed_refs)

        if df_catastro.empty:
            logger.error("No se pudo obtener ningún dato de Catastro para Gràcia")
            write_summary(df_catastro)
            return 1

        save_catastro_data(df_catastro)
        write_summary(df_catastro)

        logger.info("✓ Extracción catastral completada correctamente para Gràcia")
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Error inesperado en la extracción catastral para Gràcia: %s",
            exc,
            exc_info=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


