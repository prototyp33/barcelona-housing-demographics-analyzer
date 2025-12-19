#!/usr/bin/env python3
"""
Genera seed de referencias catastrales para Gràcia muestreando dentro de polígonos oficiales.

Objetivo:
- Obtener ~60 referencias reales (no inventadas) con cobertura equitativa de los 5 barrios de Gràcia
  (codi_barri: 28-32), usando `Consulta_RCCOOR` (coordenadas -> referencia + dirección).

Estrategia:
1) Cargar GeoJSON oficial de barrios desde `data/raw/geojson/`.
2) Filtrar barrios 28-32.
3) Para cada barrio, muestrear N puntos aleatorios dentro del polígono (rechazo en bbox).
4) Consultar Catastro por coordenadas para obtener referencia catastral real.
5) Guardar seed CSV con distribución garantizada por barrio.

Output por defecto:
- spike-data-validation/data/raw/gracia_refs_seed.csv

Nota:
Ejecutar con `.venv-spike/bin/python`.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from shapely.geometry import Point, shape
from shapely.prepared import prep

import sys

# Import local client
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_soap_client import CatastroSOAPClient, CatastroSOAPError

logger = logging.getLogger(__name__)

RAW_DIR = Path("spike-data-validation/data/raw")
LOG_DIR = Path("spike-data-validation/data/logs")

DEFAULT_GEOJSON = Path("data/raw/geojson/barrios_geojson_20251115_162533_398394.json")
DEFAULT_OUTPUT = RAW_DIR / "gracia_refs_seed.csv"

GRACIA_BARRIO_IDS = [28, 29, 30, 31, 32]


@dataclass(frozen=True)
class BarrioPolygon:
    """Contenedor de geometría y metadatos de un barrio."""

    barrio_id: int
    barrio_nombre: str
    distrito_nombre: str
    geom: Any
    geom_prepared: Any


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(LOG_DIR / "seed_generation_by_barrio.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def _fix_mojibake(text: Optional[str]) -> Optional[str]:
    """
    Intenta corregir cadenas con mojibake (p.ej. 'GrÃ cia' -> 'Gràcia').
    """
    if not text:
        return text
    if "Ã" not in text:
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def load_gracia_polygons(geojson_path: Path) -> Dict[int, BarrioPolygon]:
    """
    Carga polígonos de los 5 barrios de Gràcia desde un GeoJSON FeatureCollection.
    """
    if not geojson_path.exists():
        raise FileNotFoundError(f"No se encontró GeoJSON: {geojson_path}")

    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"GeoJSON inesperado: type={payload.get('type')}")

    barrios: Dict[int, BarrioPolygon] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        barrio_id = props.get("codi_barri")
        if barrio_id not in GRACIA_BARRIO_IDS:
            continue

        barrio_nombre = _fix_mojibake(str(props.get("nom_barri") or "")) or ""
        distrito_nombre = _fix_mojibake(str(props.get("nom_districte") or "")) or ""
        geom = shape(feature.get("geometry"))
        barrios[int(barrio_id)] = BarrioPolygon(
            barrio_id=int(barrio_id),
            barrio_nombre=barrio_nombre,
            distrito_nombre=distrito_nombre,
            geom=geom,
            geom_prepared=prep(geom),
        )

    missing = sorted(set(GRACIA_BARRIO_IDS) - set(barrios.keys()))
    if missing:
        raise ValueError(f"Faltan barrios de Gràcia en el GeoJSON: {missing}")

    return barrios


def sample_point_within_polygon(poly: BarrioPolygon, max_attempts: int = 5000) -> Tuple[float, float]:
    """
    Muestra un punto (lon, lat) uniforme por rechazo dentro del bbox del polígono.
    """
    minx, miny, maxx, maxy = poly.geom.bounds
    for _ in range(max_attempts):
        lon = random.uniform(minx, maxx)
        lat = random.uniform(miny, maxy)
        pt = Point(lon, lat)
        if poly.geom_prepared.contains(pt):
            return lon, lat
    raise RuntimeError(f"No se pudo samplear un punto dentro del polígono barrio_id={poly.barrio_id}")


def generate_seed(
    geojson_path: Path,
    output_path: Path,
    points_per_barrio: int,
    max_query_attempts_per_barrio: int,
    seed: int,
) -> pd.DataFrame:
    """
    Genera el seed muestreando por barrio y consultando Catastro por coordenadas.
    """
    random.seed(seed)

    barrios = load_gracia_polygons(geojson_path)
    client = CatastroSOAPClient()

    # #region agent log
    import time
    with open("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log", "a") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "debug-session",
                    "runId": "run9",
                    "hypothesisId": "SEED_BY_BARRIO",
                    "location": "generate_gracia_seed_by_barrio.py:generate_seed",
                    "message": "Inicio",
                    "data": {"points_per_barrio": points_per_barrio, "seed": seed},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    # #endregion

    rows: List[Dict[str, Any]] = []
    seen_refs: set[str] = set()

    for barrio_id in GRACIA_BARRIO_IDS:
        poly = barrios[barrio_id]
        target = points_per_barrio
        attempts = 0
        successes = 0

        while successes < target and attempts < max_query_attempts_per_barrio:
            attempts += 1
            lon, lat = sample_point_within_polygon(poly)
            try:
                building = client.get_building_by_coordinates(lon=lon, lat=lat)
            except CatastroSOAPError as exc:
                logger.warning("Error Catastro (coords) barrio %s: %s", barrio_id, exc)
                continue

            if not building or not building.get("referencia_catastral"):
                continue

            ref = str(building.get("referencia_catastral")).strip()
            if not ref or ref in seen_refs:
                continue

            seen_refs.add(ref)
            successes += 1

            rows.append(
                {
                    "referencia_catastral": ref,
                    "direccion": building.get("direccion_normalizada"),
                    "lat": round(float(lat), 6),
                    "lon": round(float(lon), 6),
                    "metodo": "coordenadas",
                    "barrio_id": int(barrio_id),
                    "barrio_nombre": poly.barrio_nombre,
                    "distrito_nombre": poly.distrito_nombre,
                    "datos_imputados": False,
                    "metodo_obtencion": "catastro_rccoor_por_poligono",
                }
            )

        logger.info(
            "Barrio %s (%s): %s/%s referencias (%s intentos)",
            barrio_id,
            poly.barrio_nombre,
            successes,
            target,
            attempts,
        )

        if successes < target:
            logger.warning(
                "No se alcanzó el objetivo para barrio %s: %s/%s. Considera aumentar max_attempts.",
                barrio_id,
                successes,
                target,
            )

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    # #region agent log
    with open("/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log", "a") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "debug-session",
                    "runId": "run9",
                    "hypothesisId": "SEED_BY_BARRIO",
                    "location": "generate_gracia_seed_by_barrio.py:generate_seed",
                    "message": "Fin",
                    "data": {"rows": int(len(df)), "counts_by_barrio": df["barrio_id"].value_counts().to_dict()},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
    # #endregion

    return df


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--geojson", type=str, default=str(DEFAULT_GEOJSON))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--points-per-barrio", type=int, default=12)
    parser.add_argument("--max-attempts-per-barrio", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()

    geojson_path = Path(args.geojson)
    output_path = Path(args.output)

    logger.info("=== Generación seed Gràcia por barrio (28-32) ===")
    logger.info("GeoJSON: %s", geojson_path)
    logger.info("Output: %s", output_path)

    df = generate_seed(
        geojson_path=geojson_path,
        output_path=output_path,
        points_per_barrio=int(args.points_per_barrio),
        max_query_attempts_per_barrio=int(args.max_attempts_per_barrio),
        seed=int(args.seed),
    )

    if df.empty:
        logger.error("No se pudo generar ninguna referencia")
        return 1

    ok = True
    for barrio_id in GRACIA_BARRIO_IDS:
        if (df["barrio_id"] == barrio_id).sum() == 0:
            ok = False
            logger.error("Cobertura incompleta: sin filas para barrio_id=%s", barrio_id)

    logger.info("Total referencias: %s", len(df))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


