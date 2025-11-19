#!/usr/bin/env python3
"""Discovery script to map Barcelona barrios to Idealista RapidAPI locationIds."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.extract_priority_sources import IdealistaRapidAPIExtractor
from src.data_processing import _normalize_text

BARCELONA_CITY_ID = "0-EU-ES-08-019-001-000"
INPUT_DIM_BARRIOS = REPO_ROOT / "data" / "processed" / "dim_barrios.csv"
SQLITE_DB = REPO_ROOT / "data" / "processed" / "database.db"
OUTPUT_FILE = REPO_ROOT / "data" / "processed" / "barrio_location_ids.csv"
MAX_PAGES = 20
MAX_ITEMS = 40
SLEEP_TIME = 1.5


def load_dim_barrios() -> pd.DataFrame:
    if INPUT_DIM_BARRIOS.exists():
        df = pd.read_csv(INPUT_DIM_BARRIOS)
        return df
    if SQLITE_DB.exists():
        import sqlite3

        with sqlite3.connect(SQLITE_DB) as conn:
            df = pd.read_sql_query("SELECT * FROM dim_barrios", conn)
            return df
    raise FileNotFoundError("No se encontró dim_barrios (ni CSV ni database.db)")


def main() -> None:
    print("🚀 Descubriendo locationIds de Idealista para Barcelona...")
    df_dim = load_dim_barrios()
    if "barrio_nombre" in df_dim.columns:
        name_col = "barrio_nombre"
    elif "nom_barrio" in df_dim.columns:
        name_col = "nom_barrio"
    else:
        raise ValueError("dim_barrios debe tener la columna 'barrio_nombre' o 'nom_barrio'")

    df_dim["barrio_norm"] = df_dim[name_col].apply(_normalize_text)
    target_set = set(df_dim["barrio_norm"])
    print(f"Objetivo: {len(target_set)} barrios")

    extractor = IdealistaRapidAPIExtractor()
    found_ids: Dict[str, str] = {}
    page = 1

    while len(found_ids) < len(target_set) and page <= MAX_PAGES:
        print(f"\n--- Página {page}/{MAX_PAGES} | encontrados {len(found_ids)}/{len(target_set)} ---")
        df_page, meta = extractor.list_home_properties(
            location_id=BARCELONA_CITY_ID,
            operation="sale",
            num_page=page,
            max_items=MAX_ITEMS,
            locale="es",
            locationName="Barcelona",
            location="es",
        )
        if df_page is None or df_page.empty:
            print("No llegaron anuncios, deteniendo búsqueda.")
            break

        for _, row in df_page.iterrows():
            neigh = row.get("neighborhood")
            loc_id = row.get("locationId")
            if not neigh or not loc_id:
                continue
            neigh_norm = _normalize_text(neigh)
            if neigh_norm in target_set and neigh_norm not in found_ids:
                found_ids[neigh_norm] = loc_id
                district = row.get("district")
                print(f"  ✓ {neigh} ({district}) -> {loc_id}")

        page += 1
        time.sleep(SLEEP_TIME)

    if len(found_ids) < len(target_set):
        print(
            f"⚠️ Solo se encontraron {len(found_ids)} de {len(target_set)} barrios."
            " Los faltantes se marcarán como vacíos en el CSV."
        )
    else:
        print("🎉 ¡Todos los barrios identifcados!")

    records = []
    timestamp = datetime.utcnow().isoformat()
    for _, row in df_dim.iterrows():
        record = row.to_dict()
        norm = row["barrio_norm"]
        record["idealista_locationId"] = found_ids.get(norm)
        record["location_discovered_at"] = timestamp if norm in found_ids else None
        records.append(record)

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"📁 Archivo guardado en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
