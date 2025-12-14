"""
Módulo de migraciones de base de datos.

Proporciona funciones reutilizables para migraciones y actualizaciones
de esquema que se integran en el pipeline ETL.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_centroid(geometry_json: str) -> tuple[float, float] | None:
    """
    Calcula el centroide de una geometría GeoJSON.
    
    Args:
        geometry_json: GeoJSON string (Polygon o MultiPolygon)
    
    Returns:
        Tupla (lat, lon) o None si no se puede calcular
    """
    if not geometry_json:
        return None
    
    try:
        geom = json.loads(geometry_json)
        
        # Extraer coordenadas según tipo
        if geom.get("type") == "Polygon":
            coords = geom["coordinates"][0]  # Exterior ring
        elif geom.get("type") == "MultiPolygon":
            # Usar el primer polígono
            coords = geom["coordinates"][0][0]
        else:
            logger.warning(f"Tipo de geometría no soportado: {geom.get('type')}")
            return None
        
        # Calcular centroide simple (promedio de coordenadas)
        # GeoJSON usa [lon, lat] orden
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        centroid_lon = sum(lons) / len(lons)
        centroid_lat = sum(lats) / len(lats)
        
        return (centroid_lat, centroid_lon)
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Error calculando centroide: {e}")
        return None


def calculate_area_km2(geometry_json: str) -> float | None:
    """
    Calcula el área en km² de una geometría GeoJSON.
    
    Args:
        geometry_json: GeoJSON string (Polygon o MultiPolygon)
    
    Returns:
        Área en km² o None si no se puede calcular
    """
    if not geometry_json:
        return None
    
    try:
        geom = json.loads(geometry_json)
        
        # Extraer coordenadas según tipo
        if geom.get("type") == "Polygon":
            coords = geom["coordinates"][0]  # Exterior ring
        elif geom.get("type") == "MultiPolygon":
            # Sumar áreas de todos los polígonos
            total_area = 0.0
            for polygon in geom["coordinates"]:
                area = _calculate_polygon_area(polygon[0])
                if area:
                    total_area += area
            return total_area
        else:
            return None
        
        return _calculate_polygon_area(coords)
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Error calculando área: {e}")
        return None


def _calculate_polygon_area(coords: list) -> float | None:
    """
    Calcula área de un polígono usando Shoelace formula.
    
    Args:
        coords: Lista de coordenadas [lon, lat]
    
    Returns:
        Área en km²
    """
    if len(coords) < 3:
        return None
    
    # Shoelace formula para área en grados²
    area_deg2 = 0.0
    n = len(coords)
    
    for i in range(n):
        j = (i + 1) % n
        area_deg2 += coords[i][0] * coords[j][1]
        area_deg2 -= coords[j][0] * coords[i][1]
    
    area_deg2 = abs(area_deg2) / 2.0
    
    # Convertir grados² a km²
    # Calcular latitud media
    import math
    avg_lat = sum(coord[1] for coord in coords) / len(coords)
    lat_factor = 111.0  # km por grado de latitud
    lon_factor = 111.0 * abs(math.cos(math.radians(avg_lat)))
    
    # Área en km²
    area_km2 = area_deg2 * lat_factor * lon_factor
    
    return area_km2


def get_ine_codes() -> dict[int, str]:
    """
    Retorna mapeo de barrio_id a código INE.
    
    Nota: El INE no tiene códigos oficiales para barrios (solo municipios).
    Usamos formato compuesto: código municipio (08019) + codi_barri del Ajuntament.
    
    Returns:
        Diccionario con mapeo barrio_id -> codigo_ine
    """
    from pathlib import Path
    import json
    
    mapping_file = Path(__file__).parent.parent.parent / "data" / "reference" / "barrio_ine_mapping.json"
    
    if not mapping_file.exists():
        logger.warning(f"Archivo de mapeo INE no encontrado: {mapping_file}")
        return {}
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping_str = json.load(f)
            # Convertir keys de string a int
            return {int(k): v for k, v in mapping_str.items() if v is not None}
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"Error leyendo mapeo INE: {e}")
        return {}


def migrate_dim_barrios_if_needed(conn: sqlite3.Connection) -> dict[str, int]:
    """
    Migra dim_barrios añadiendo campos adicionales si no existen.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Diccionario con estadísticas de migración
    """
    logger.info("Verificando migración de dim_barrios...")
    
    # Verificar si las columnas ya existen
    cursor = conn.execute("PRAGMA table_info(dim_barrios)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = {
        "codigo_ine": "TEXT",
        "centroide_lat": "REAL",
        "centroide_lon": "REAL",
        "area_km2": "REAL",
    }
    
    columns_added = 0
    # Añadir columnas que no existen
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            logger.debug(f"Añadiendo columna {col_name}")
            conn.execute(f"ALTER TABLE dim_barrios ADD COLUMN {col_name} {col_type}")
            columns_added += 1
    
    if columns_added > 0:
        conn.commit()
        logger.info(f"✓ {columns_added} columnas añadidas a dim_barrios")
    
    # Verificar si hay datos que poblar
    cursor = conn.execute("""
        SELECT COUNT(*) FROM dim_barrios
        WHERE (geometry_json IS NOT NULL AND (centroide_lat IS NULL OR area_km2 IS NULL))
           OR codigo_ine IS NULL
    """)
    needs_population = cursor.fetchone()[0] > 0
    
    if not needs_population:
        logger.debug("dim_barrios ya tiene todos los campos poblados")
        return {
            "columns_added": columns_added,
            "barrios_updated": 0,
            "barrios_with_centroid": 0,
            "barrios_with_area": 0,
        }
    
    # Poblar datos
    logger.info("Poblando campos adicionales de dim_barrios...")
    
    cursor = conn.execute("""
        SELECT barrio_id, geometry_json, barrio_nombre
        FROM dim_barrios
        WHERE (geometry_json IS NOT NULL AND (centroide_lat IS NULL OR area_km2 IS NULL))
           OR codigo_ine IS NULL
    """)
    
    barrios = cursor.fetchall()
    logger.debug(f"Procesando {len(barrios)} barrios que necesitan actualización")
    
    updated = 0
    with_centroid = 0
    with_area = 0
    with_ine = 0
    
    # Obtener mapeo INE una sola vez
    ine_codes = get_ine_codes()
    
    for barrio_id, geometry_json, barrio_nombre in barrios:
        # Calcular centroide
        centroid = calculate_centroid(geometry_json)
        if centroid:
            centroide_lat, centroide_lon = centroid
            with_centroid += 1
        else:
            centroide_lat = centroide_lon = None
        
        # Calcular área
        area_km2 = calculate_area_km2(geometry_json)
        if area_km2:
            with_area += 1
        
        # Obtener código INE
        codigo_ine = ine_codes.get(barrio_id)
        if codigo_ine:
            with_ine += 1
        
        # Actualizar registro si hay cambios
        needs_update = centroid or area_km2 or codigo_ine
        if needs_update:
            conn.execute("""
                UPDATE dim_barrios
                SET centroide_lat = COALESCE(?, centroide_lat),
                    centroide_lon = COALESCE(?, centroide_lon),
                    area_km2 = COALESCE(?, area_km2),
                    codigo_ine = COALESCE(?, codigo_ine)
                WHERE barrio_id = ?
            """, (centroide_lat, centroide_lon, area_km2, codigo_ine, barrio_id))
            updated += 1
    
    conn.commit()
    
    if updated > 0:
        logger.info(f"✓ {updated} barrios actualizados")
    
    return {
        "columns_added": columns_added,
        "barrios_updated": updated,
        "barrios_with_centroid": with_centroid,
        "barrios_with_area": with_area,
        "barrios_with_ine": with_ine,
    }

