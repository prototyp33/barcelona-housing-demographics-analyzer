#!/usr/bin/env python3
"""
Matching Catastro ↔ Idealista (Fase 2 - Issue #202).

Linkea inmuebles de Catastro con propiedades de Idealista usando:
- Clave principal: referencia_catastral (matching exacto)
- Clave secundaria: dirección + coordenadas (fuzzy matching si es necesario)

Genera dataset combinado para modelo hedónico MICRO.

Uso:
    python3 spike-data-validation/scripts/fase2/match_catastro_idealista.py
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Rutas por defecto
INPUT_CATASTRO = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
INPUT_IDEALISTA = Path("spike-data-validation/data/processed/fase2/idealista_gracia_mock.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def normalize_referencia_catastral(ref: str) -> str:
    """
    Normaliza referencia catastral para matching.
    
    Args:
        ref: Referencia catastral (puede ser 14, 18 o 20 caracteres)
        
    Returns:
        Referencia normalizada (14 caracteres base)
    """
    if pd.isna(ref) or not ref:
        return ""
    ref_str = str(ref).strip().upper()
    # Tomar primeros 14 caracteres (referencia base)
    return ref_str[:14] if len(ref_str) >= 14 else ref_str


def match_by_referencia_catastral(
    df_catastro: pd.DataFrame, df_idealista: pd.DataFrame
) -> pd.DataFrame:
    """
    Matching principal por referencia catastral.
    
    Estrategia:
    - Si hay múltiples inmuebles Catastro por referencia → tomar el primero (o promedio)
    - Matching uno-a-uno con Idealista
    
    Args:
        df_catastro: DataFrame de Catastro
        df_idealista: DataFrame de Idealista
        
    Returns:
        DataFrame combinado con matching exitoso
    """
    logger.info("Matching por referencia catastral...")
    
    # Normalizar referencias
    df_catastro = df_catastro.copy()
    df_idealista = df_idealista.copy()
    
    df_catastro["ref_base"] = df_catastro["referencia_catastral"].apply(
        normalize_referencia_catastral
    )
    df_idealista["ref_base"] = df_idealista["referencia_catastral"].apply(
        normalize_referencia_catastral
    )
    
    # Agrupar Catastro por referencia base (una observación por referencia)
    # Tomar el primer inmueble de cada referencia (o podemos promediar)
    logger.info("   Agrupando Catastro por referencia base...")
    catastro_grouped = df_catastro.groupby("ref_base").first().reset_index()
    logger.info("   Referencias Catastro únicas: %s (de %s inmuebles)", 
                len(catastro_grouped), len(df_catastro))
    
    # Matching exacto uno-a-uno
    df_merged = catastro_grouped.merge(
        df_idealista,
        on="ref_base",
        how="inner",
        suffixes=("_catastro", "_idealista"),
    )
    
    logger.info("   Matching exacto: %s referencias", len(df_merged))
    
    # Log detallado
    refs_catastro_unique = df_catastro["ref_base"].nunique()
    refs_idealista_unique = df_idealista["ref_base"].nunique()
    refs_matched = df_merged["ref_base"].nunique()
    
    logger.info("   Detalle:")
    logger.info("     Referencias Catastro únicas: %s", refs_catastro_unique)
    logger.info("     Referencias Idealista únicas: %s", refs_idealista_unique)
    logger.info("     Referencias matched: %s", refs_matched)
    logger.info("     Matching rate (refs): %.1f%%", refs_matched / refs_catastro_unique * 100 if refs_catastro_unique > 0 else 0)
    
    return df_merged


def validate_matching(df_merged: pd.DataFrame) -> Dict[str, Any]:
    """
    Valida calidad del matching.
    
    Args:
        df_merged: DataFrame con datos combinados
        
    Returns:
        Diccionario con métricas de validación
    """
    validation: Dict[str, Any] = {
        "total_matched": len(df_merged),
        "matching_rate": 0.0,
        "data_quality": {},
    }
    
    if df_merged.empty:
        return validation
    
    # Validar campos críticos
    required_catastro = ["superficie_m2", "ano_construccion"]
    required_idealista = ["price", "size"]
    
    for col in required_catastro:
        col_full = f"{col}_catastro"
        if col_full in df_merged.columns:
            null_pct = df_merged[col_full].isna().sum() / len(df_merged) * 100
            validation["data_quality"][col_full] = {
                "completitud": 100 - null_pct,
                "nulls": int(df_merged[col_full].isna().sum()),
            }
    
    for col in required_idealista:
        if col in df_merged.columns:
            null_pct = df_merged[col].isna().sum() / len(df_merged) * 100
            validation["data_quality"][col] = {
                "completitud": 100 - null_pct,
                "nulls": int(df_merged[col].isna().sum()),
            }
    
    # Validar consistencia superficie
    if "superficie_m2_catastro" in df_merged.columns and "size" in df_merged.columns:
        df_valid = df_merged[
            df_merged["superficie_m2_catastro"].notna() & df_merged["size"].notna()
        ].copy()
        if len(df_valid) > 0:
            # Calcular diferencia relativa
            df_valid["diff_superficie"] = (
                abs(df_valid["superficie_m2_catastro"] - df_valid["size"])
                / df_valid["superficie_m2_catastro"]
                * 100
            )
            validation["superficie_consistency"] = {
                "mean_diff_pct": float(df_valid["diff_superficie"].mean()),
                "max_diff_pct": float(df_valid["diff_superficie"].max()),
                "within_5pct": int((df_valid["diff_superficie"] <= 5).sum()),
            }
    
    return validation


def prepare_hedonic_dataset(df_merged: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dataset final para modelo hedónico.
    
    Args:
        df_merged: DataFrame con datos combinados
        
    Returns:
        DataFrame limpio y preparado para modelo
    """
    logger.info("Preparando dataset para modelo hedónico...")
    
    df_model = df_merged.copy()
    
    # Variable dependiente: precio (de Idealista)
    if "price" in df_model.columns:
        df_model["precio"] = df_model["price"]
    else:
        logger.warning("No se encontró columna 'price'")
        df_model["precio"] = None
    
    # Variables independientes: características de Catastro
    # Superficie
    if "superficie_m2_catastro" in df_model.columns:
        df_model["superficie_m2"] = df_model["superficie_m2_catastro"]
    elif "size" in df_model.columns:
        df_model["superficie_m2"] = df_model["size"]
    
    # Año construcción
    if "ano_construccion_catastro" in df_model.columns:
        df_model["ano_construccion"] = df_model["ano_construccion_catastro"]
    
    # Plantas
    if "plantas_catastro" in df_model.columns:
        df_model["plantas"] = df_model["plantas_catastro"]
    elif "floor" in df_model.columns:
        df_model["plantas"] = df_model["floor"]
    
    # Barrio (one-hot encoding se hará en el modelo)
    if "barrio_id_catastro" in df_model.columns:
        df_model["barrio_id"] = df_model["barrio_id_catastro"]
    elif "barrio_id" in df_model.columns:
        pass  # Ya existe
    else:
        logger.warning("No se encontró barrio_id")
    
    # Características adicionales de Idealista
    if "rooms" in df_model.columns:
        df_model["habitaciones"] = df_model["rooms"]
    if "bathrooms" in df_model.columns:
        df_model["banos"] = df_model["bathrooms"]
    if "exterior" in df_model.columns:
        df_model["exterior"] = df_model["exterior"]
    if "elevator" in df_model.columns:
        df_model["ascensor"] = df_model["elevator"]
    
    # Precio por m² (calculado)
    df_model["precio_m2"] = (
        df_model["precio"] / df_model["superficie_m2"]
        if "precio" in df_model.columns and "superficie_m2" in df_model.columns
        else None
    )
    
    # Filtrar filas con datos mínimos requeridos
    required_cols = ["precio", "superficie_m2"]
    df_model = df_model[
        df_model[required_cols].notna().all(axis=1)
    ].copy()
    
    logger.info("   Dataset preparado: %s observaciones", len(df_model))
    
    return df_model


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Matching Catastro ↔ Idealista")
    parser.add_argument("--catastro", type=str, default=None, help="CSV Catastro")
    parser.add_argument("--idealista", type=str, default=None, help="CSV Idealista")
    parser.add_argument("--output", type=str, default=None, help="Ruta de salida CSV")
    args = parser.parse_args()
    
    # Cargar datos
    catastro_path = Path(args.catastro) if args.catastro else INPUT_CATASTRO
    idealista_path = Path(args.idealista) if args.idealista else INPUT_IDEALISTA
    
    if not catastro_path.exists():
        logger.error("No se encuentra: %s", catastro_path)
        return 1
    
    if not idealista_path.exists():
        logger.error("No se encuentra: %s", idealista_path)
        return 1
    
    logger.info("=" * 70)
    logger.info("MATCHING CATASTRO ↔ IDEALISTA")
    logger.info("=" * 70)
    logger.info("Catastro: %s", catastro_path)
    logger.info("Idealista: %s", idealista_path)
    logger.info("")
    
    df_catastro = pd.read_csv(catastro_path)
    df_idealista = pd.read_csv(idealista_path)
    
    logger.info("📊 DATOS CARGADOS:")
    logger.info("   Catastro: %s inmuebles", len(df_catastro))
    logger.info("   Idealista: %s propiedades", len(df_idealista))
    logger.info("")
    
    # Matching
    df_merged = match_by_referencia_catastral(df_catastro, df_idealista)
    
    if df_merged.empty:
        logger.error("❌ No se encontraron matches")
        return 1
    
    # Validación
    logger.info("")
    logger.info("VALIDACIÓN DEL MATCHING:")
    validation = validate_matching(df_merged)
    
    # Calcular matching rates
    matching_rate_inmuebles = (
        len(df_merged) / len(df_catastro) * 100
        if len(df_catastro) > 0
        else 0
    )
    
    refs_catastro_unique = df_catastro["referencia_catastral"].apply(normalize_referencia_catastral).nunique()
    refs_matched = df_merged["ref_base"].nunique() if "ref_base" in df_merged.columns else len(df_merged)
    matching_rate_refs = (
        refs_matched / refs_catastro_unique * 100
        if refs_catastro_unique > 0
        else 0
    )
    
    validation["matching_rate"] = matching_rate_refs
    validation["matching_rate_inmuebles"] = matching_rate_inmuebles
    
    logger.info("   Matching rate (inmuebles): %.1f%% (%s/%s)", 
                matching_rate_inmuebles, len(df_merged), len(df_catastro))
    logger.info("   Matching rate (referencias): %.1f%% (%s/%s)", 
                matching_rate_refs, refs_matched, refs_catastro_unique)
    
    if "data_quality" in validation:
        logger.info("   Calidad de datos:")
        for col, stats in validation["data_quality"].items():
            logger.info("     %s: %.1f%% completitud", col, stats["completitud"])
    
    if "superficie_consistency" in validation:
        sc = validation["superficie_consistency"]
        logger.info("   Consistencia superficie:")
        logger.info("     Diferencia media: %.1f%%", sc["mean_diff_pct"])
        logger.info("     Dentro de 5%%: %s/%s", sc["within_5pct"], len(df_merged))
    
    # Preparar dataset para modelo
    logger.info("")
    df_model = prepare_hedonic_dataset(df_merged)
    
    if df_model.empty:
        logger.error("❌ Dataset para modelo está vacío")
        return 1
    
    # Guardar resultados
    output_path = Path(args.output) if args.output else OUTPUT_DIR / "catastro_idealista_matched.csv"
    df_model.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info("📄 CSV guardado: %s", output_path)
    logger.info("   Observaciones: %s", len(df_model))
    
    # Guardar metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "input_files": {
            "catastro": str(catastro_path),
            "idealista": str(idealista_path),
        },
        "matching": validation,
        "dataset_stats": {
            "total_observations": len(df_model),
            "precio_mean": float(df_model["precio"].mean()) if "precio" in df_model.columns else None,
            "precio_m2_mean": float(df_model["precio_m2"].mean()) if "precio_m2" in df_model.columns else None,
            "superficie_mean": float(df_model["superficie_m2"].mean()) if "superficie_m2" in df_model.columns else None,
        },
        "output_file": str(output_path),
    }
    
    metadata_path = OUTPUT_DIR / "matching_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("📄 Metadata guardada: %s", metadata_path)
    
    logger.info("")
    logger.info("✅ MATCHING COMPLETADO")
    logger.info("   Dataset listo para modelo hedónico: %s", output_path)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

