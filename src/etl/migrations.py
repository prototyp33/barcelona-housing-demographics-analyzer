"""Funciones de migración e infraestructura ETL (dim_barrios, códigos INE, etc.)."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


def calculate_centroid(geometry_json: str) -> Optional[Tuple[float, float]]:
    """
    Calcula el centroide de una geometría GeoJSON simple.

    Args:
        geometry_json: Cadena JSON con una geometría GeoJSON (Polygon o MultiPolygon).

    Returns:
        Tupla (latitud, longitud) del centroide o ``None`` si no se puede calcular.
    """
    if not geometry_json:
        return None

    try:
        geom = json.loads(geometry_json)
    except json.JSONDecodeError as exc:
        logger.warning("Error decodificando GeoJSON para centroide: %s", exc)
        return None

    geom_type = geom.get("type")
    if geom_type == "Polygon":
        coords = geom.get("coordinates", [])
        if not coords:
            return None
        ring = coords[0]
    elif geom_type == "MultiPolygon":
        coords = geom.get("coordinates", [])
        if not coords or not coords[0]:
            return None
        ring = coords[0][0]
    else:
        logger.warning("Tipo de geometría no soportado para centroide: %s", geom_type)
        return None

    if not isinstance(ring, list) or len(ring) < 3:
        return None

    try:
        lons = [float(point[0]) for point in ring]
        lats = [float(point[1]) for point in ring]
    except (TypeError, ValueError) as exc:
        logger.warning("Coordenadas inválidas en GeoJSON: %s", exc)
        return None

    centroid_lon = sum(lons) / len(lons)
    centroid_lat = sum(lats) / len(lats)
    return centroid_lat, centroid_lon


def _calculate_polygon_area_deg2(coords: Iterable[Iterable[float]]) -> Optional[float]:
    """Calcula el área de un polígono en grados² usando la fórmula de Shoelace."""
    points: List[Tuple[float, float]] = []
    for point in coords:
        try:
            lon = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError, IndexError):
            continue
        points.append((lon, lat))

    n = len(points)
    if n < 3:
        return None

    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return abs(area) / 2.0


def calculate_area_km2(geometry_json: str) -> Optional[float]:
    """
    Calcula el área aproximada en km² de una geometría GeoJSON.

    Returns:
        Área aproximada en km² o ``None`` si no se puede calcular.
    """
    if not geometry_json:
        return None

    try:
        geom = json.loads(geometry_json)
    except json.JSONDecodeError as exc:
        logger.warning("Error decodificando GeoJSON para área: %s", exc)
        return None

    geom_type = geom.get("type")
    if geom_type == "Polygon":
        coords = geom.get("coordinates", [])
        if not coords:
            return None
        ring = coords[0]
        area_deg2 = _calculate_polygon_area_deg2(ring)
    elif geom_type == "MultiPolygon":
        total_area_deg2 = 0.0
        for polygon in geom.get("coordinates", []):
            if not polygon:
                continue
            ring = polygon[0]
            partial = _calculate_polygon_area_deg2(ring)
            if partial is not None:
                total_area_deg2 += partial
        area_deg2 = total_area_deg2 if total_area_deg2 > 0 else None
    else:
        logger.warning("Tipo de geometría no soportado para área: %s", geom_type)
        return None

    if area_deg2 is None:
        return None

    import math

    try:
        coords_sample = geom.get("coordinates", [])
        sample_ring = coords_sample[0] if geom_type == "Polygon" else coords_sample[0][0]
        lats = [float(p[1]) for p in sample_ring]
        avg_lat = sum(lats) / len(lats)
    except Exception:  # noqa: BLE001
        avg_lat = 41.4

    lat_factor_km = 111.0
    lon_factor_km = 111.0 * abs(math.cos(math.radians(avg_lat)))

    area_km2 = area_deg2 * lat_factor_km * lon_factor_km
    return area_km2


def get_ine_codes(mapping_path: Optional[Path] = None) -> Dict[int, str]:
    """
    Carga el mapeo de ``barrio_id`` a código INE desde un archivo JSON.

    Devuelve un diccionario vacío si el archivo no existe o no es válido.
    """
    if mapping_path is None:
        project_root = Path(__file__).resolve().parents[2]
        mapping_path = project_root / "data" / "reference" / "barrio_ine_mapping.json"

    if not mapping_path.exists():
        logger.warning("Archivo de mapeo INE no encontrado: %s", mapping_path)
        return {}

    try:
        raw = json.loads(mapping_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Error al decodificar barrio_ine_mapping.json: %s", exc)
        return {}

    mapping: Dict[int, str] = {}
    for key, value in raw.items():
        try:
            barrio_id = int(key)
            code = str(value)
        except (TypeError, ValueError):
            logger.warning("Entrada inválida en mapeo INE: %r -> %r", key, value)
            continue

        if not code.startswith("08019") or len(code) != 8:
            logger.warning("Código INE con formato inesperado para barrio %s: %s", barrio_id, code)
        mapping[barrio_id] = code

    logger.info("Mapeo INE cargado: %s barrios", len(mapping))
    return mapping


def migrate_dim_barrios_if_needed(conn: sqlite3.Connection) -> None:
    """
    Ejecuta migración idempotente sobre ``dim_barrios`` para añadir campos derivados.
    """
    logger.info("Aplicando migración idempotente de dim_barrios (centroides, áreas, códigos INE)")

    try:
        cursor = conn.execute("PRAGMA table_info(dim_barrios)")
        existing_columns = {row[1] for row in cursor.fetchall()}
    except sqlite3.Error as exc:
        logger.warning("No se pudo inspeccionar dim_barrios: %s", exc)
        return

    new_columns = {
        "codigo_ine": "TEXT",
        "centroide_lat": "REAL",
        "centroide_lon": "REAL",
        "area_km2": "REAL",
    }

    try:
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                logger.info("Añadiendo columna %s a dim_barrios", col_name)
                conn.execute(f"ALTER TABLE dim_barrios ADD COLUMN {col_name} {col_type}")
        conn.commit()
    except sqlite3.Error as exc:
        logger.warning("Error añadiendo columnas a dim_barrios: %s", exc)
        return

    try:
        cursor = conn.execute(
            """
            SELECT barrio_id, geometry_json, codigo_ine
            FROM dim_barrios
            """
        )
        rows = cursor.fetchall()
    except sqlite3.Error as exc:
        logger.warning("No se pudo leer dim_barrios para migración: %s", exc)
        return

    ine_codes = get_ine_codes()

    updated = 0
    for barrio_id, geometry_json, codigo_ine in rows:
        if geometry_json is None and codigo_ine is not None:
            continue

        centroide_lat: Optional[float] = None
        centroide_lon: Optional[float] = None
        area_km2: Optional[float] = None

        if geometry_json:
            centroid = calculate_centroid(geometry_json)
            if centroid:
                centroide_lat, centroide_lon = centroid
            area_km2 = calculate_area_km2(geometry_json)

        final_codigo_ine = codigo_ine or ine_codes.get(barrio_id)

        try:
            conn.execute(
                """
                UPDATE dim_barrios
                SET centroide_lat = COALESCE(centroide_lat, ?),
                    centroide_lon = COALESCE(centroide_lon, ?),
                    area_km2 = COALESCE(area_km2, ?),
                    codigo_ine = COALESCE(codigo_ine, ?)
                WHERE barrio_id = ?
                """,
                (centroide_lat, centroide_lon, area_km2, final_codigo_ine, barrio_id),
            )
            if centroide_lat is not None or area_km2 is not None or final_codigo_ine:
                updated += 1
        except sqlite3.Error as exc:
            logger.warning("Error actualizando barrio %s en dim_barrios: %s", barrio_id, exc)

    try:
        conn.commit()
    except sqlite3.Error as exc:
        logger.warning("Error haciendo commit de migración dim_barrios: %s", exc)
        return

    logger.info("Migración dim_barrios completada. Barrios actualizados: %s", updated)


__all__ = [
    "calculate_centroid",
    "calculate_area_km2",
    "get_ine_codes",
    "migrate_dim_barrios_if_needed",
]

