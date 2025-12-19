#!/usr/bin/env python3
"""
Fase 2 (Issue #200): filtrar datos reales del Catastro a las referencias del seed de Gràcia.

Input:
- CSV parseado del XML masivo (Barcelona): catastro_barcelona_parsed.csv
- Seed de Gràcia: spike-data-validation/data/raw/gracia_refs_seed.csv

Output:
- spike-data-validation/data/processed/catastro_gracia_real.csv

Nota:
El seed actual contiene RC de 14 chars (PC1+PC2). Se filtra por coincidencia exacta.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Set

import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed",
        type=str,
        default="spike-data-validation/data/raw/gracia_refs_seed.csv",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="spike-data-validation/data/processed/catastro_barcelona_parsed.csv",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="spike-data-validation/data/processed/catastro_gracia_real.csv",
    )
    return parser.parse_args()


def load_seed_refs(seed_path: Path) -> pd.DataFrame:
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed no encontrado: {seed_path}")
    df = pd.read_csv(seed_path)
    if "referencia_catastral" not in df.columns:
        raise ValueError("Seed debe contener columna referencia_catastral")
    df = df.copy()
    df["referencia_catastral"] = df["referencia_catastral"].astype(str).str.strip()
    return df


def main() -> int:
    setup_logging()
    args = parse_args()
    seed_path = Path(args.seed)
    input_path = Path(args.input)
    output_path = Path(args.output)

    seed_df = load_seed_refs(seed_path)
    seed_set: Set[str] = set(seed_df["referencia_catastral"].dropna().astype(str).str.strip())
    logger.info("Seed refs: %s", len(seed_set))

    if not input_path.exists():
        raise FileNotFoundError(f"Input no encontrado: {input_path}")

    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Input vacío: %s", input_path)
        return 1
    if "referencia_catastral" not in df.columns:
        logger.error("Input no tiene columna referencia_catastral")
        return 1

    df = df.copy()
    df["referencia_catastral"] = df["referencia_catastral"].astype(str).str.strip()
    df_gracia = df[df["referencia_catastral"].isin(seed_set)].copy()

    # Añadir coords/dirección del seed si existen
    merge_cols: List[str] = ["referencia_catastral"]
    for col in ["lat", "lon", "direccion", "barrio_id", "barrio_nombre"]:
        if col in seed_df.columns:
            merge_cols.append(col)

    seed_small = seed_df[merge_cols].drop_duplicates(subset=["referencia_catastral"]).copy()
    df_gracia = df_gracia.merge(seed_small, on="referencia_catastral", how="left", suffixes=("", "_seed"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_gracia.to_csv(output_path, index=False, encoding="utf-8")

    logger.info("Gràcia filtrado: %s/%s", len(df_gracia), len(df))
    logger.info("Output: %s", output_path)
    return 0 if not df_gracia.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())


