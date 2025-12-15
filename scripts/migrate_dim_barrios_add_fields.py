#!/usr/bin/env python3
"""
Script de migración para añadir campos adicionales a dim_barrios.

Añade:
- codigo_ine: Código INE para matching
- centroide_lat/lon: Centroide calculado desde geometry_json
- area_km2: Área en km² calculada desde geometrías
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


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
    
    Usa aproximación simple (no considera curvatura de la Tierra).
    Para cálculos más precisos, usaría una librería como Shapely.
    
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
    # Aproximación: 1 grado ≈ 111 km (latitud)
    # Para longitud, ajustar por cos(latitud media)
    # Simplificación: usar factor promedio
    # En Barcelona (lat ~41.4°): 1° lat ≈ 111 km, 1° lon ≈ 83 km
    # Factor promedio: ~111 * 83 ≈ 9213 km² por grado²
    # Más preciso: usar latitud media del polígono
    
    # Calcular latitud media
    avg_lat = sum(coord[1] for coord in coords) / len(coords)
    lat_factor = 111.0  # km por grado de latitud
    lon_factor = 111.0 * abs(__import__("math").cos(__import__("math").radians(avg_lat)))
    
    # Área en km²
    area_km2 = area_deg2 * lat_factor * lon_factor
    
    return area_km2


def get_ine_codes() -> dict[int, str]:
    """
    Retorna mapeo de barrio_id a código INE.
    
    Nota: Este mapeo debe completarse manualmente o desde fuente oficial.
    Por ahora, retorna diccionario vacío para que se complete.
    """
    # TODO: Completar con códigos INE reales
    # Fuente: INE o mapeo manual basado en nombres
    return {}


def migrate_dim_barrios(conn: sqlite3.Connection) -> None:
    """
    Ejecuta migración añadiendo campos a dim_barrios.
    """
    logger.info("Iniciando migración de dim_barrios")
    
    # Verificar si las columnas ya existen
    cursor = conn.execute("PRAGMA table_info(dim_barrios)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    new_columns = {
        "codigo_ine": "TEXT",
        "centroide_lat": "REAL",
        "centroide_lon": "REAL",
        "area_km2": "REAL",
    }
    
    # Añadir columnas que no existen
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            logger.info(f"Añadiendo columna {col_name}")
            conn.execute(f"ALTER TABLE dim_barrios ADD COLUMN {col_name} {col_type}")
        else:
            logger.debug(f"Columna {col_name} ya existe")
    
    conn.commit()
    logger.info("✓ Columnas añadidas")
    
    # Poblar datos
    logger.info("Poblando nuevos campos...")
    
    cursor = conn.execute("""
        SELECT barrio_id, geometry_json, barrio_nombre
        FROM dim_barrios
        WHERE geometry_json IS NOT NULL
    """)
    
    barrios = cursor.fetchall()
    logger.info(f"Procesando {len(barrios)} barrios con geometría")
    
    # Obtener códigos INE
    ine_codes = get_ine_codes()
    
    updated = 0
    for barrio_id, geometry_json, barrio_nombre in barrios:
        # Calcular centroide
        centroid = calculate_centroid(geometry_json)
        if centroid:
            centroide_lat, centroide_lon = centroid
        else:
            centroide_lat = centroide_lon = None
        
        # Calcular área
        area_km2 = calculate_area_km2(geometry_json)
        
        # Obtener código INE
        codigo_ine = ine_codes.get(barrio_id)
        
        # Actualizar registro
        conn.execute("""
            UPDATE dim_barrios
            SET centroide_lat = ?,
                centroide_lon = ?,
                area_km2 = ?,
                codigo_ine = ?
            WHERE barrio_id = ?
        """, (centroide_lat, centroide_lon, area_km2, codigo_ine, barrio_id))
        
        if centroid or area_km2:
            updated += 1
    
    conn.commit()
    logger.info(f"✓ {updated} barrios actualizados")
    
    # Validar resultados
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN centroide_lat IS NOT NULL THEN 1 ELSE 0 END) as con_centroide,
            SUM(CASE WHEN area_km2 IS NOT NULL THEN 1 ELSE 0 END) as con_area,
            SUM(CASE WHEN codigo_ine IS NOT NULL THEN 1 ELSE 0 END) as con_ine
        FROM dim_barrios
    """)
    
    total, con_centroide, con_area, con_ine = cursor.fetchone()
    
    logger.info("=" * 80)
    logger.info("Resumen de migración:")
    logger.info(f"  Total barrios: {total}")
    logger.info(f"  Con centroide: {con_centroide} ({con_centroide/total*100:.1f}%)")
    logger.info(f"  Con área: {con_area} ({con_area/total*100:.1f}%)")
    logger.info(f"  Con código INE: {con_ine} ({con_ine/total*100:.1f}%)")
    logger.info("=" * 80)


def main() -> int:
    """Función principal."""
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return 1
    
    try:
        conn = create_connection(DB_PATH)
        
        try:
            migrate_dim_barrios(conn)
            logger.info("✅ Migración completada exitosamente")
            return 0
        finally:
            conn.close()
            
    except Exception as e:
        logger.exception(f"Error durante la migración: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

