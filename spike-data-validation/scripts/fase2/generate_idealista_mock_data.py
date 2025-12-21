#!/usr/bin/env python3
"""
Genera datos de prueba (mock) de Idealista para validar el pipeline (Fase 2).

Mientras esperamos credenciales API de Idealista, este script genera datos
realistas basados en los datos Catastro ya obtenidos.

Los datos mock tienen:
- Estructura similar a Idealista API
- Precios realistas basados en superficie y barrio
- Variabilidad para simular mercado real
- Matching posible con referencias catastrales

Uso:
    python3 spike-data-validation/scripts/fase2/generate_idealista_mock_data.py
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

INPUT_CATASTRO = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Precios base por m² por barrio (euros/m²) - basados en mercado real de Gràcia
PRECIOS_BASE_M2 = {
    28: 4500,  # Vallcarca i els Penitents
    29: 4200,  # el Coll
    30: 4800,  # la Salut
    31: 5200,  # la Vila de Gràcia (más caro)
    32: 4700,  # el Camp d'en Grassot i Gràcia Nova
}

# Variabilidad de precios (±20%)
PRECIO_VARIABILITY = 0.20


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def generate_mock_idealista_property(
    catastro_row: pd.Series, seed: int = None
) -> Dict[str, Any]:
    """
    Genera un anuncio mock de Idealista basado en datos Catastro.
    
    Args:
        catastro_row: Fila del DataFrame de Catastro
        seed: Semilla para reproducibilidad
        
    Returns:
        Diccionario con datos mock de Idealista
    """
    if seed is not None:
        random.seed(seed)
    
    barrio_id = int(catastro_row.get("barrio_id", 31))
    superficie = catastro_row.get("superficie_m2", 80.0)
    ano_construccion = catastro_row.get("ano_construccion", 1970)
    direccion = catastro_row.get("direccion_normalizada", catastro_row.get("direccion", ""))
    referencia_catastral = catastro_row.get("referencia_catastral", "")
    
    # Precio base según barrio y superficie
    precio_base_m2 = PRECIOS_BASE_M2.get(barrio_id, 4800)
    
    # Ajustar precio según año de construcción (más nuevo = más caro)
    ano_factor = 1.0
    if ano_construccion:
        if ano_construccion >= 2010:
            ano_factor = 1.15  # +15% para muy nuevos
        elif ano_construccion >= 2000:
            ano_factor = 1.05  # +5% para nuevos
        elif ano_construccion < 1950:
            ano_factor = 0.90  # -10% para muy antiguos
    
    # Calcular precio con variabilidad
    precio_m2_ajustado = precio_base_m2 * ano_factor
    variacion = random.uniform(1 - PRECIO_VARIABILITY, 1 + PRECIO_VARIABILITY)
    precio_total = int(superficie * precio_m2_ajustado * variacion)
    
    # Generar características adicionales
    habitaciones = random.choices(
        [1, 2, 3, 4],
        weights=[0.15, 0.35, 0.35, 0.15],  # Distribución realista
    )[0]
    
    banos = max(1, habitaciones - 1) if habitaciones > 1 else 1
    
    # Planta (si está disponible en Catastro, usarla; sino generar)
    if pd.notna(catastro_row.get("plantas")):
        planta = int(catastro_row["plantas"])
    else:
        planta = random.choices(
            [0, 1, 2, 3, 4, 5],
            weights=[0.10, 0.20, 0.25, 0.25, 0.15, 0.05],
        )[0]
    
    # Estado (condición)
    estado = random.choices(
        ["good", "renew", "new"],
        weights=[0.60, 0.30, 0.10],
    )[0]
    
    # Orientación
    orientacion = random.choice(["norte", "sur", "este", "oeste", "noreste", "noroeste", "sureste", "suroeste"])
    
    # Fecha de publicación (últimos 30 días)
    dias_atras = random.randint(1, 30)
    fecha_publicacion = (datetime.now() - pd.Timedelta(days=dias_atras)).isoformat()
    
    # Construir URL mock
    url_id = referencia_catastral[:10] if referencia_catastral else f"mock_{random.randint(100000, 999999)}"
    url = f"https://www.idealista.com/inmueble/{url_id}/"
    
    return {
        "propertyId": url_id,
        "url": url,
        "price": precio_total,
        "priceByArea": int(precio_total / superficie) if superficie > 0 else precio_base_m2,
        "size": float(superficie),
        "rooms": habitaciones,
        "bathrooms": banos,
        "floor": planta,
        "exterior": random.choice([True, False]),
        "elevator": random.choice([True, False]) if planta > 1 else False,
        "parkingSpace": random.choice([True, False]),
        "condition": estado,
        "orientation": orientacion,
        "address": direccion,
        "district": "Gràcia",
        "neighborhood": catastro_row.get("barrio_nombre", "Gràcia"),
        "latitude": catastro_row.get("lat"),
        "longitude": catastro_row.get("lon"),
        "yearBuilt": int(ano_construccion) if pd.notna(ano_construccion) else None,
        "description": f"Vivienda en {catastro_row.get('barrio_nombre', 'Gràcia')}. {habitaciones} habitaciones, {banos} baños.",
        "publicationDate": fecha_publicacion,
        "operation": "sale",
        "propertyType": "flat",
        # Campos para matching con Catastro
        "referencia_catastral": referencia_catastral,
        "barrio_id": barrio_id,
    }


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Genera datos mock de Idealista")
    parser.add_argument("--input", type=str, default=None, help="CSV de Catastro (default: catastro_gracia_real.csv)")
    parser.add_argument("--output", type=str, default=None, help="Ruta de salida CSV")
    parser.add_argument("--sample", type=int, default=None, help="Muestrear N propiedades (default: todas)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla para reproducibilidad")
    args = parser.parse_args()
    
    # Cargar datos Catastro
    input_path = Path(args.input) if args.input else INPUT_CATASTRO
    
    if not input_path.exists():
        logger.error("No se encuentra: %s", input_path)
        logger.error("Ejecuta primero el parser y filtro de Catastro")
        return 1
    
    logger.info("=" * 70)
    logger.info("GENERACIÓN DATOS MOCK IDEALISTA")
    logger.info("=" * 70)
    logger.info("Input: %s", input_path)
    logger.info("Seed: %s", args.seed)
    logger.info("")
    
    df_catastro = pd.read_csv(input_path)
    logger.info("Cargadas %s propiedades de Catastro", len(df_catastro))
    
    # Muestrear si se especifica
    if args.sample and args.sample < len(df_catastro):
        df_catastro = df_catastro.sample(n=args.sample, random_state=args.seed).reset_index(drop=True)
        logger.info("Muestreadas %s propiedades", len(df_catastro))
    
    # Generar datos mock
    logger.info("Generando datos mock de Idealista...")
    mock_properties: List[Dict[str, Any]] = []
    
    for idx, row in df_catastro.iterrows():
        seed = args.seed + idx if args.seed else None
        mock_prop = generate_mock_idealista_property(row, seed=seed)
        mock_properties.append(mock_prop)
        
        if (idx + 1) % 50 == 0:
            logger.info("   Generadas %s/%s propiedades", idx + 1, len(df_catastro))
    
    df_mock = pd.DataFrame(mock_properties)
    logger.info("✅ Generadas %s propiedades mock", len(df_mock))
    
    # Guardar CSV
    output_path = Path(args.output) if args.output else OUTPUT_DIR / "idealista_gracia_mock.csv"
    df_mock.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info("📄 CSV guardado: %s", output_path)
    
    # Estadísticas
    logger.info("")
    logger.info("📊 ESTADÍSTICAS:")
    logger.info("   Precio medio: %.0f €", df_mock["price"].mean())
    logger.info("   Precio/m² medio: %.0f €/m²", df_mock["priceByArea"].mean())
    logger.info("   Superficie media: %.1f m²", df_mock["size"].mean())
    logger.info("   Habitaciones media: %.1f", df_mock["rooms"].mean())
    
    # Guardar metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "source": "mock_data",
        "based_on": str(input_path),
        "num_properties": len(df_mock),
        "seed": args.seed,
        "stats": {
            "precio_medio": float(df_mock["price"].mean()),
            "precio_m2_medio": float(df_mock["priceByArea"].mean()),
            "superficie_media": float(df_mock["size"].mean()),
            "habitaciones_media": float(df_mock["rooms"].mean()),
        },
        "note": "Datos mock generados para validar pipeline mientras se esperan credenciales API",
    }
    
    metadata_path = OUTPUT_DIR / "idealista_mock_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("📄 Metadata guardada: %s", metadata_path)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

