"""
Script to load GeoJSON geometries into dim_barrios table.

This script reads a GeoJSON file from data/raw/geometries/, normalizes
neighborhood names using HousingCleaner, validates the JSON structure,
and updates the geometry_json column in dim_barrios.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.database_setup import create_connection, DEFAULT_DB_NAME, ensure_database_path
from src.transform.cleaners import HousingCleaner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_PROCESSED_DIR = Path("data/processed")
DEFAULT_GEOMETRIES_DIR = Path("data/raw/geometries")


def validate_geojson_structure(geometry: Dict) -> bool:
    """
    Validate that a geometry dictionary has the required GeoJSON structure.
    
    Args:
        geometry: Dictionary containing geometry data
    
    Returns:
        True if valid GeoJSON geometry, False otherwise
    """
    if not isinstance(geometry, dict):
        return False
    
    # GeoJSON geometry must have 'type' and 'coordinates'
    if 'type' not in geometry or 'coordinates' not in geometry:
        return False
    
    # Validate geometry type
    valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 
                   'MultiLineString', 'MultiPolygon', 'GeometryCollection']
    if geometry['type'] not in valid_types:
        logger.warning(f"Invalid geometry type: {geometry['type']}")
        return False
    
    return True


def load_geojson_file(geojson_path: Path) -> Optional[Dict]:
    """
    Load and parse a GeoJSON file.
    
    Args:
        geojson_path: Path to the GeoJSON file
    
    Returns:
        Parsed GeoJSON dictionary or None if loading fails
    
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")
    
    logger.info(f"Loading GeoJSON file: {geojson_path}")
    
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Validate top-level structure
        if not isinstance(geojson_data, dict):
            logger.error("GeoJSON file is not a valid JSON object")
            return None
        
        if geojson_data.get('type') != 'FeatureCollection':
            logger.warning(
                f"GeoJSON type is '{geojson_data.get('type')}', "
                f"expected 'FeatureCollection'"
            )
            return None
        
        features = geojson_data.get('features', [])
        logger.info(f"Found {len(features)} features in GeoJSON")
        
        return geojson_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {geojson_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading GeoJSON file {geojson_path}: {e}", exc_info=True)
        return None


def get_barrio_mapping(conn: sqlite3.Connection) -> Dict[str, int]:
    """
    Get a mapping from normalized barrio names to barrio_id.
    
    Args:
        conn: Database connection
    
    Returns:
        Dictionary mapping normalized names to barrio_id
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT barrio_id, barrio_nombre_normalizado, barrio_nombre
        FROM dim_barrios
    """)
    
    mapping = {}
    for row in cursor.fetchall():
        barrio_id, nombre_normalizado, nombre = row
        # Map both normalized name and original name (normalized)
        mapping[nombre_normalizado] = barrio_id
        if nombre:
            # Also try normalizing the original name in case it differs
            cleaner = HousingCleaner()
            normalized_original = cleaner.normalize_neighborhoods(nombre)
            if normalized_original and normalized_original != nombre_normalizado:
                mapping[normalized_original] = barrio_id
    
    logger.info(f"Loaded mapping for {len(mapping)} barrio names")
    return mapping


def extract_barrio_name_from_feature(feature: Dict) -> Optional[str]:
    """
    Extract barrio name from a GeoJSON feature's properties.
    
    Tries multiple common property names used in GeoJSON files.
    
    Args:
        feature: GeoJSON feature dictionary
    
    Returns:
        Barrio name string or None if not found
    """
    properties = feature.get('properties', {})
    
    # Try common property names
    name_keys = [
        'Nom_Barri', 'nom_barri', 'NOM_BARRI',
        'barrio_nombre', 'barrio', 'Barrio',
        'name', 'Name', 'NAME',
        'nom', 'Nom', 'NOM'
    ]
    
    for key in name_keys:
        if key in properties:
            name = properties[key]
            if name and isinstance(name, str) and name.strip():
                return name.strip()
    
    return None


def extract_barrio_code_from_feature(feature: Dict) -> Optional[int]:
    """
    Extract barrio code (codi_barri) from a GeoJSON feature's properties.
    
    Args:
        feature: GeoJSON feature dictionary
    
    Returns:
        Barrio code as integer or None if not found
    """
    properties = feature.get('properties', {})
    
    # Try common property names for codes
    code_keys = [
        'Codi_Barri', 'codi_barri', 'CODI_BARRI',
        'barrio_id', 'barrioId', 'id'
    ]
    
    for key in code_keys:
        if key in properties:
            code = properties[key]
            if code is not None:
                try:
                    return int(code)
                except (ValueError, TypeError):
                    continue
    
    return None


def update_geometries(
    geojson_path: Path,
    db_path: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> bool:
    """
    Load geometries from GeoJSON and update dim_barrios table.
    
    Args:
        geojson_path: Path to the GeoJSON file
        db_path: Path to database file (defaults to data/processed/database.db)
        processed_dir: Directory containing processed data
        dry_run: If True, only validate without updating database
    
    Returns:
        True if successful, False otherwise
    """
    # Determine database path
    if processed_dir is None:
        processed_dir = DEFAULT_PROCESSED_DIR
    else:
        processed_dir = Path(processed_dir)
    
    if db_path is None:
        db_path = ensure_database_path(None, processed_dir)
    else:
        db_path = ensure_database_path(db_path, processed_dir)
    
    logger.info(f"Starting geometry loading process")
    logger.info(f"GeoJSON file: {geojson_path}")
    logger.info(f"Database: {db_path}")
    logger.info(f"Dry run: {dry_run}")
    
    if not geojson_path.exists():
        logger.error(f"GeoJSON file not found: {geojson_path}")
        return False
    
    # Load GeoJSON
    geojson_data = load_geojson_file(geojson_path)
    if geojson_data is None:
        return False
    
    features = geojson_data.get('features', [])
    if not features:
        logger.warning("No features found in GeoJSON")
        return False
    
    # Connect to database
    conn = create_connection(db_path)
    cleaner = HousingCleaner()
    
    try:
        # Get barrio mapping
        barrio_mapping = get_barrio_mapping(conn)
        if not barrio_mapping:
            logger.error("No barrios found in database")
            return False
        
        # Process features
        logger.info(f"Processing {len(features)} features...")
        updates = []
        skipped = []
        errors = []
        
        for idx, feature in enumerate(features, 1):
            if feature.get('type') != 'Feature':
                logger.debug(f"Feature {idx}: Skipping non-Feature type")
                skipped.append(f"Feature {idx}: Not a Feature type")
                continue
            
            geometry = feature.get('geometry')
            if not geometry:
                logger.debug(f"Feature {idx}: No geometry found")
                skipped.append(f"Feature {idx}: No geometry")
                continue
            
            # Validate geometry structure
            if not validate_geojson_structure(geometry):
                logger.warning(f"Feature {idx}: Invalid geometry structure")
                errors.append(f"Feature {idx}: Invalid geometry structure")
                continue
            
            # Try to find barrio_id
            barrio_id = None
            barrio_name = None
            
            # First try by code
            barrio_code = extract_barrio_code_from_feature(feature)
            if barrio_code:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT barrio_id FROM dim_barrios WHERE barrio_id = ?",
                    (barrio_code,)
                )
                result = cursor.fetchone()
                if result:
                    barrio_id = result[0]
                    logger.debug(f"Feature {idx}: Found barrio_id {barrio_id} by code")
            
            # If not found by code, try by name
            if barrio_id is None:
                barrio_name = extract_barrio_name_from_feature(feature)
                if barrio_name:
                    # Fix encoding issues
                    barrio_name = cleaner._fix_mojibake(barrio_name)
                    # Normalize name
                    normalized_name = cleaner.normalize_neighborhoods(barrio_name)
                    barrio_id = barrio_mapping.get(normalized_name)
                    
                    if barrio_id:
                        logger.debug(
                            f"Feature {idx}: Found barrio_id {barrio_id} "
                            f"by name '{barrio_name}' (normalized: '{normalized_name}')"
                        )
            
            if barrio_id is None:
                logger.warning(
                    f"Feature {idx}: Could not match to barrio. "
                    f"Name: '{barrio_name}', Code: {barrio_code}"
                )
                skipped.append(
                    f"Feature {idx}: No match (name: '{barrio_name}', code: {barrio_code})"
                )
                continue
            
            # Convert geometry to JSON string and validate
            try:
                geometry_json_str = json.dumps(geometry, ensure_ascii=False)
                # Validate by parsing back
                json.loads(geometry_json_str)
            except (TypeError, ValueError) as e:
                logger.error(f"Feature {idx}: Invalid JSON in geometry: {e}")
                errors.append(f"Feature {idx}: JSON validation failed")
                continue
            
            updates.append({
                'barrio_id': barrio_id,
                'geometry_json': geometry_json_str,
                'barrio_name': barrio_name or f"barrio_id_{barrio_id}"
            })
        
        logger.info(f"Processed {len(features)} features:")
        logger.info(f"  - Updates: {len(updates)}")
        logger.info(f"  - Skipped: {len(skipped)}")
        logger.info(f"  - Errors: {len(errors)}")
        
        if skipped:
            logger.debug("Skipped features:")
            for skip in skipped[:10]:  # Show first 10
                logger.debug(f"  {skip}")
            if len(skipped) > 10:
                logger.debug(f"  ... and {len(skipped) - 10} more")
        
        if errors:
            logger.warning("Features with errors:")
            for error in errors[:10]:  # Show first 10
                logger.warning(f"  {error}")
            if len(errors) > 10:
                logger.warning(f"  ... and {len(errors) - 10} more")
        
        if not updates:
            logger.error("No valid updates to apply")
            return False
        
        if dry_run:
            logger.info("DRY RUN: Would update the following barrios:")
            for update in updates[:20]:  # Show first 20
                logger.info(
                    f"  barrio_id {update['barrio_id']}: "
                    f"{update['barrio_name']}"
                )
            if len(updates) > 20:
                logger.info(f"  ... and {len(updates) - 20} more")
            logger.info("DRY RUN: No changes made to database")
            return True
        
        # Update database
        logger.info("Updating database...")
        timestamp = datetime.now().isoformat()
        cursor = conn.cursor()
        
        updated_count = 0
        with conn:
            for update in updates:
                try:
                    cursor.execute("""
                        UPDATE dim_barrios
                        SET geometry_json = ?,
                            etl_updated_at = ?
                        WHERE barrio_id = ?
                    """, (
                        update['geometry_json'],
                        timestamp,
                        update['barrio_id']
                    ))
                    if cursor.rowcount > 0:
                        updated_count += 1
                except sqlite3.Error as e:
                    logger.error(
                        f"Error updating barrio_id {update['barrio_id']}: {e}"
                    )
                    continue
        
        logger.info(f"Successfully updated {updated_count} barrios")
        
        # Verify updates
        cursor.execute("""
            SELECT COUNT(*) FROM dim_barrios WHERE geometry_json IS NOT NULL
        """)
        total_with_geometry = cursor.fetchone()[0]
        logger.info(f"Total barrios with geometry: {total_with_geometry}")
        
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
    
    finally:
        conn.close()
        logger.info("Database connection closed")


def find_geojson_files(geometries_dir: Path) -> list[Path]:
    """
    Find all GeoJSON files in the specified directory.
    
    Args:
        geometries_dir: Directory to search
    
    Returns:
        List of GeoJSON file paths
    """
    if not geometries_dir.exists():
        return []
    
    geojson_files = []
    for ext in ['*.geojson', '*.json']:
        geojson_files.extend(geometries_dir.glob(ext))
        geojson_files.extend(geometries_dir.glob(ext.upper()))
    
    return sorted(geojson_files)


def main() -> None:
    """Main entry point for the geometry loading script."""
    parser = argparse.ArgumentParser(
        description="Load GeoJSON geometries into dim_barrios table"
    )
    parser.add_argument(
        "--geojson",
        type=Path,
        default=None,
        help="Path to GeoJSON file (defaults to first .geojson/.json in data/raw/geometries/)",
    )
    parser.add_argument(
        "--geometries-dir",
        type=Path,
        default=DEFAULT_GEOMETRIES_DIR,
        help=f"Directory containing GeoJSON files (default: {DEFAULT_GEOMETRIES_DIR})",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to database file (defaults to data/processed/database.db)",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Directory containing processed data (defaults to data/processed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and show what would be updated without making changes",
    )
    
    args = parser.parse_args()
    
    # Find GeoJSON file
    geojson_path = args.geojson
    if geojson_path is None:
        geojson_files = find_geojson_files(args.geometries_dir)
        if not geojson_files:
            logger.error(
                f"No GeoJSON files found in {args.geometries_dir}. "
                f"Please specify --geojson or place a .geojson/.json file in the directory."
            )
            exit(1)
        geojson_path = geojson_files[0]
        logger.info(f"Using first GeoJSON file found: {geojson_path}")
        if len(geojson_files) > 1:
            logger.info(f"Other files found: {geojson_files[1:]}")
    
    success = update_geometries(
        geojson_path=geojson_path,
        db_path=args.db_path,
        processed_dir=args.processed_dir,
        dry_run=args.dry_run,
    )
    
    if success:
        logger.info("Geometry loading completed successfully")
        exit(0)
    else:
        logger.error("Geometry loading failed")
        exit(1)


if __name__ == "__main__":
    main()

