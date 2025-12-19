"""
Script para generar seed CSV de referencias catastrales de Gràcia.

Este script intenta obtener referencias catastrales de edificios en Gràcia usando
diferentes estrategias:
1. Open Data BCN (si hay dataset de edificios con referencias catastrales)
2. Catastro por coordenadas (bbox de Gràcia) usando Consulta_RCCOOR (referencia + dirección)
3. Generación de seed CSV de ejemplo para testing

Issue: #200
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Añadir directorio de scripts al PYTHONPATH para importar catastro_soap_client
scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_soap_client import CatastroSOAPClient, CatastroSOAPError

# Configurar logging
LOG_DIR = Path("spike-data-validation/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "seed_generation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Bbox aproximado de Gràcia (Barcelona)
GRACIA_BBOX = {
    "lat_min": 41.395,
    "lat_max": 41.420,
    "lon_min": 2.150,
    "lon_max": 2.170,
}

def generate_grid_points(
    lat_min: float, lat_max: float, lon_min: float, lon_max: float, num_points: int = 10
) -> List[Dict[str, float]]:
    """
    Genera un grid de puntos dentro de un bbox.

    Args:
        lat_min: Latitud mínima
        lat_max: Latitud máxima
        lon_min: Longitud mínima
        lon_max: Longitud máxima
        num_points: Número de puntos por dimensión

    Returns:
        Lista de diccionarios con 'lat' y 'lon'
    """
    # Nota: evitamos numpy aquí porque puede causar fallos de import/segfault en algunos entornos
    # (visto en macOS + Python 3.12 con builds específicos). Para este seed, un linspace simple
    # en Python es suficiente.
    if num_points <= 1:
        lat_points = [float(lat_min)]
        lon_points = [float(lon_min)]
    else:
        lat_step = (lat_max - lat_min) / (num_points - 1)
        lon_step = (lon_max - lon_min) / (num_points - 1)
        lat_points = [float(lat_min + i * lat_step) for i in range(num_points)]
        lon_points = [float(lon_min + i * lon_step) for i in range(num_points)]

    points = []
    for lat in lat_points:
        for lon in lon_points:
            points.append({"lat": float(lat), "lon": float(lon)})

    return points


def query_catastro_by_coords(client: CatastroSOAPClient, lat: float, lon: float) -> Optional[Dict[str, object]]:
    """
    Consulta Catastro por coordenadas para obtener referencia catastral y dirección.

    Args:
        client: Cliente SOAP oficial del Catastro.
        lat: Latitud
        lon: Longitud

    Returns:
        Diccionario con datos mínimos (referencia/dirección/coords) o None si no se encuentra.
    """
    try:
        building = client.get_building_by_coordinates(lon=lon, lat=lat)
        if not building:
            return None

        # Añadir coords explícitamente para trazabilidad del seed
        building = dict(building)
        building["lat"] = float(lat)
        building["lon"] = float(lon)
        return building
    except CatastroSOAPError as exc:
        logger.debug(f"No se encontró edificio en ({lat}, {lon}): {exc}")
        return None


def search_opendata_bcn_edificios() -> Optional[pd.DataFrame]:
    """
    Busca datasets de Open Data BCN relacionados con edificios o catastro.

    Returns:
        DataFrame con referencias catastrales si se encuentra, None si no
    """
    import sys
    from pathlib import Path

    # Añadir raíz del proyecto al PYTHONPATH
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    try:
        from src.extraction.opendata import OpenDataBCNExtractor

        extractor = OpenDataBCNExtractor()

        # Buscar datasets relacionados con edificios
        datasets = extractor.get_dataset_list()
        edificios_datasets = [
            d for d in datasets if "edifici" in d.lower() or "catastr" in d.lower()
        ]

        logger.info(f"Encontrados {len(edificios_datasets)} datasets relacionados con edificios")

        # Si encontramos alguno, intentar descargarlo
        for dataset_id in edificios_datasets[:3]:  # Probar los primeros 3
            try:
                df, metadata = extractor.download_dataset(dataset_id, resource_format="csv")
                if df is not None and not df.empty:
                    # Buscar columnas que puedan contener referencias catastrales
                    ref_cols = [
                        col
                        for col in df.columns
                        if "referencia" in col.lower()
                        or "catastr" in col.lower()
                        or "rc" in col.lower()
                    ]
                    if ref_cols:
                        logger.info(f"Dataset {dataset_id} tiene columnas de referencia: {ref_cols}")
                        return df
            except Exception as e:
                logger.debug(f"Error procesando dataset {dataset_id}: {e}")
                continue

        return None
    except ImportError:
        logger.warning("No se pudo importar OpenDataBCNExtractor, saltando búsqueda en Open Data BCN")
        return None


def generate_seed_from_coordinates(
    target_count: int = 60, max_attempts: int = 200
) -> List[Dict[str, str]]:
    """
    Genera seed CSV consultando Catastro por coordenadas dentro de Gràcia.

    Args:
        target_count: Número objetivo de referencias a obtener
        max_attempts: Número máximo de intentos

    Returns:
        Lista de diccionarios con referencia_catastral y direccion
    """
    logger.info(
        f"Generando seed desde coordenadas de Gràcia (objetivo: {target_count} referencias)"
    )

    client = CatastroSOAPClient()

    points = generate_grid_points(
        GRACIA_BBOX["lat_min"],
        GRACIA_BBOX["lat_max"],
        GRACIA_BBOX["lon_min"],
        GRACIA_BBOX["lon_max"],
        num_points=15,  # Grid más denso para más cobertura
    )

    refs: List[Dict[str, str]] = []
    seen_refs = set()

    for i, point in enumerate(points[:max_attempts]):
        if len(refs) >= target_count:
            break

        result = query_catastro_by_coords(client, point["lat"], point["lon"])
        if not result:
            continue

        ref_catastral = str(result.get("referencia_catastral") or "").strip()
        if not ref_catastral:
            continue

        if ref_catastral not in seen_refs:
            seen_refs.add(ref_catastral)
            direccion = result.get("direccion_normalizada") or result.get("direccion") or ""
            refs.append(
                {
                    "referencia_catastral": ref_catastral,
                    "direccion": str(direccion),
                    "lat": f"{point['lat']:.6f}",
                    "lon": f"{point['lon']:.6f}",
                    "metodo": "coordenadas",
                }
            )
            logger.info(f"Referencia {len(refs)}/{target_count}: {ref_catastral}")

        if (i + 1) % 20 == 0:
            logger.info(f"Procesados {i+1}/{len(points)} puntos, encontradas {len(refs)} referencias")

    return refs


def create_example_seed() -> pd.DataFrame:
    """
    Crea un seed CSV de ejemplo con referencias catastrales sintéticas.

    Útil para testing cuando no se puede acceder a datos reales.

    Returns:
        DataFrame con referencias catastrales de ejemplo
    """
    logger.warning("Generando seed CSV de ejemplo (sintético)")

    # Formato de referencia catastral: 14 dígitos (ej: 1234567DF3813A0001AB)
    import random

    refs = []
    for i in range(60):
        # Generar referencia sintética (formato aproximado)
        ref = f"{random.randint(1000000, 9999999)}{random.choice(['DF', 'DF', 'DF', 'DF', 'DF'])}{random.randint(1000, 9999)}{random.choice(['A', 'B', 'C'])}{random.randint(10000, 99999)}{random.choice(['AB', 'CD', 'EF'])}"
        refs.append(
            {
                "referencia_catastral": ref,
                "direccion": f"Carrer de Gràcia {random.randint(1, 200)}, Barcelona",
            }
        )

    return pd.DataFrame(refs)


def main() -> int:
    """
    Función principal para generar seed CSV de referencias catastrales.

    Returns:
        Código de salida (0 = éxito, 1 = error)
    """
    output_path = Path("spike-data-validation/data/raw/gracia_refs_seed.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Iniciando generación de seed CSV para Gràcia")

    # Estrategia 1: Buscar en Open Data BCN
    logger.info("Estrategia 1: Buscando en Open Data BCN...")
    df_opendata = search_opendata_bcn_edificios()

    if df_opendata is not None and not df_opendata.empty:
        logger.info(f"✓ Encontrado dataset en Open Data BCN: {len(df_opendata)} registros")
        # Filtrar por Gràcia si hay columna de barrio
        # Guardar seed CSV
        df_opendata.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"Seed CSV guardado: {output_path}")
        return 0

    # Estrategia 2: Consultar Catastro por coordenadas
    logger.info("Estrategia 2: Consultando Catastro por coordenadas...")
    refs_coords = generate_seed_from_coordinates(target_count=60)

    if len(refs_coords) >= 50:
        logger.info(f"✓ Obtenidas {len(refs_coords)} referencias desde Catastro")
        df = pd.DataFrame(refs_coords)
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"Seed CSV guardado: {output_path}")
        return 0

    # Estrategia 3: Crear seed de ejemplo
    logger.warning(
        f"Solo se obtuvieron {len(refs_coords)} referencias. Generando seed de ejemplo..."
    )
    df_example = create_example_seed()
    df_example.to_csv(output_path, index=False, encoding="utf-8")
    logger.warning(
        f"⚠️ Seed CSV de EJEMPLO guardado: {output_path} "
        f"(reemplazar con datos reales antes de ejecutar Issue #200)"
    )

    # Resumen
    summary = {
        "total_referencias": len(df_example),
        "metodo": "ejemplo_sintetico",
        "advertencia": "Este seed CSV contiene datos sintéticos. Reemplazar con datos reales.",
    }

    summary_path = LOG_DIR / "seed_generation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Resumen guardado: {summary_path}")
    return 0


if __name__ == "__main__":
    exit(main())

