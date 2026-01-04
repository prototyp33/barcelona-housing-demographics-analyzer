#!/usr/bin/env python3
"""
Script para procesar datos de vivienda pública y poblar fact_vivienda_publica.

Fuentes:
- IDESCAT: Datos municipales distribuidos (stock, iniciadas, terminadas).
- Open Data BCN: Datos reales por barrio (habitatges tutelats, licencias de obra).
- Gencat: Datos municipales distribuidos (viviendas vacías, demanda VPO, ayudas).
"""

import logging
import sqlite3
import sys
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def get_connection() -> sqlite3.Connection:
    """Crea una conexión a la base de datos."""
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
    return sqlite3.connect(db_path)


def get_barrios_with_weights(conn: sqlite3.Connection) -> pd.DataFrame:
    """Obtiene pesos de barrios usando población (vista agregada)."""
    query = """
    SELECT 
        db.barrio_id,
        db.barrio_nombre,
        COALESCE(MAX(d.poblacion_total), 0) as peso
    FROM dim_barrios db
    LEFT JOIN v_demografia_aggregated d ON db.barrio_id = d.barrio_id
    GROUP BY db.barrio_id, db.barrio_nombre
    HAVING peso > 0
    ORDER BY db.barrio_id
    """
    return pd.read_sql_query(query, conn)


def process_idescat_file(filepath: Path, barrios_df: pd.DataFrame) -> pd.DataFrame:
    """Procesa un archivo de IDESCAT y distribuye valores."""
    logger.info(f"Procesando IDESCAT: {filepath.name}")
    df = pd.read_csv(filepath)
    if df.empty: return pd.DataFrame()
    year_match = re.search(r'_(\d{4})_', filepath.name)
    anio = int(year_match.group(1)) if year_match else datetime.now().year
    row = df.iloc[0]
    cols_to_distribute = {
        "viviendas_proteccion_oficial": "vpo_est",
        "viviendas_iniciadas_vpo": "vpo_iniciadas_est",
        "viviendas_iniciadas_total": "total_iniciadas_est",
        "viviendas_terminadas_vpo": "vpo_terminadas_est",
        "viviendas_terminadas_total": "total_terminadas_est",
        "viviendas_principales": "principales_est",
        "viviendas_no_principales": "no_principales_est"
    }
    total_peso = barrios_df["peso"].sum()
    results = []
    for _, b_row in barrios_df.iterrows():
        prop = b_row["peso"] / total_peso if total_peso > 0 else 1.0/len(barrios_df)
        entry = {"barrio_id": int(b_row["barrio_id"]), "anio": anio, "source_idescat": "idescat_estimado"}
        for idescat_col, target_col in cols_to_distribute.items():
            val = row.get(idescat_col)
            entry[target_col] = round(val * prop, 2) if pd.notna(val) else 0
        results.append(entry)
    return pd.DataFrame(results)


def process_opendata_habitatges_tutelats(filepath: Path) -> pd.DataFrame:
    """Procesa dataset de habitatges tutelats de Open Data BCN."""
    logger.info(f"Procesando Open Data BCN (Tutelats): {filepath.name}")
    try: df = pd.read_csv(filepath, encoding="utf-8-sig")
    except Exception: df = pd.read_csv(filepath)
    if df.empty: return pd.DataFrame()
    barrio_id_col = next((c for c in df.columns if any(p in c.lower() for p in ["neighborhood_id", "codi_barri", "addresses_neighborhood_id"])), None)
    if not barrio_id_col: return pd.DataFrame()
    df_agg = df.groupby(barrio_id_col).size().reset_index()
    df_agg.columns = ["barrio_id", "vpo_real"]
    df_agg["source_opendata"] = "opendatabcn_real"
    return df_agg


def process_opendata_licencias(filepath: Path) -> pd.DataFrame:
    """Procesa dataset de licencias de obra de Open Data BCN."""
    logger.info(f"Procesando Open Data BCN (Licencias): {filepath.name}")
    try: df = pd.read_csv(filepath, encoding="utf-8-sig")
    except Exception: df = pd.read_csv(filepath)
    if df.empty: return pd.DataFrame()
    barrio_id_col = next((c for c in df.columns if any(p in c.lower() for p in ["neighborhood_id", "codi_barri", "addresses_neighborhood_id"])), None)
    if not barrio_id_col: return pd.DataFrame()
    if 'tipo_obra' not in df.columns:
        df['tipo_obra'] = "mayor" if "major" in filepath.name.lower() else "menor"
    df_agg = df.groupby([barrio_id_col, 'tipo_obra']).size().unstack(fill_value=0).reset_index()
    rename_dict = {}
    for col in df_agg.columns:
        if str(col).lower() == "mayor": rename_dict[col] = "num_licencias_mayor"
        if str(col).lower() == "menor": rename_dict[col] = "num_licencias_menor"
    df_agg = df_agg.rename(columns=rename_dict)
    if "num_licencias_mayor" not in df_agg.columns: df_agg["num_licencias_mayor"] = 0
    if "num_licencias_menor" not in df_agg.columns: df_agg["num_licencias_menor"] = 0
    return df_agg[["barrio_id", "num_licencias_mayor", "num_licencias_menor"]]


def process_gencat_data(filepath: Path, barrios_df: pd.DataFrame) -> pd.DataFrame:
    """Procesa datos de Gencat y los distribuye por barrios."""
    logger.info(f"Procesando Gencat: {filepath.name}")
    try: df = pd.read_csv(filepath)
    except Exception: return pd.DataFrame()
    if df.empty: return pd.DataFrame()
    total_val = len(df)
    count_cols = [c for c in df.columns if any(p in c.lower() for p in ["nombre", "vivienda", "ajut", "unitat", "quantitat"])]
    if count_cols:
        for c in count_cols:
            try:
                v = pd.to_numeric(df[c], errors='coerce').sum()
                if v > total_val: total_val = v
            except Exception: pass
    total_peso = barrios_df["peso"].sum()
    col_name = "viviendas_vacias_est" if "vqqv" in filepath.name else ("demanda_vpo_est" if "jtbt" in filepath.name else "ayudas_alquiler_est")
    results = []
    for _, b_row in barrios_df.iterrows():
        prop = b_row["peso"] / total_peso if total_peso > 0 else 1.0/len(barrios_df)
        results.append({"barrio_id": int(b_row["barrio_id"]), col_name: round(total_val * prop, 2)})
    return pd.DataFrame(results)


def main():
    try:
        conn = get_connection()
        barrios_df = get_barrios_with_weights(conn)
        vivienda_dir = PROJECT_ROOT / "data" / "raw" / "viviendapublica"
        if not vivienda_dir.exists(): return 1
            
        df_idescat = pd.DataFrame()
        files = list(vivienda_dir.glob("*idescat*.csv"))
        if files: df_idescat = process_idescat_file(max(files, key=lambda p: p.stat().st_mtime), barrios_df)
            
        df_opendata = pd.DataFrame()
        files = list(vivienda_dir.glob("*opendatabcn_serveissocials_habitatges*tutelats*.csv"))
        if files: df_opendata = process_opendata_habitatges_tutelats(max(files, key=lambda p: p.stat().st_mtime))
            
        df_licencias = pd.DataFrame()
        files = list(vivienda_dir.glob("*opendatabcn_licencias_obra*.csv"))
        if files: df_licencias = process_opendata_licencias(max(files, key=lambda p: p.stat().st_mtime))
            
        df_vacias = pd.DataFrame()
        files = list(vivienda_dir.glob("*gencat*vqqv*.csv"))
        if files: df_vacias = process_gencat_data(max(files, key=lambda p: p.stat().st_mtime), barrios_df)
            
        df_demanda = pd.DataFrame()
        files = list(vivienda_dir.glob("*gencat*jtbt*.csv"))
        if files: df_demanda = process_gencat_data(max(files, key=lambda p: p.stat().st_mtime), barrios_df)
            
        df_ayudas = pd.DataFrame()
        files = list(vivienda_dir.glob("*gencat*vbp2*.csv"))
        if files: df_ayudas = process_gencat_data(max(files, key=lambda p: p.stat().st_mtime), barrios_df)
            
        if df_idescat.empty and df_opendata.empty and df_licencias.empty and df_vacias.empty and df_demanda.empty and df_ayudas.empty:
            logger.error("No hay datos para procesar"); return 1
            
        final_df = barrios_df[["barrio_id"]].copy()
        for df in [df_idescat, df_opendata, df_licencias, df_vacias, df_demanda, df_ayudas]:
            if not df.empty: final_df = final_df.merge(df, on="barrio_id", how="left")
            
        default_cols = {
            "vpo_real": np.nan, "vpo_est": 0, "vpo_iniciadas_est": 0, "total_iniciadas_est": 0,
            "vpo_terminadas_est": 0, "total_terminadas_est": 0, "principales_est": 0, "no_principales_est": 0,
            "num_licencias_mayor": 0, "num_licencias_menor": 0, "viviendas_vacias_est": 0, "demanda_vpo_est": 0, "ayudas_alquiler_est": 0
        }
        for col, default in default_cols.items():
            if col not in final_df.columns: final_df[col] = default
            
        final_df["viviendas_proteccion_oficial"] = final_df["vpo_real"].fillna(final_df["vpo_est"])
        final_df["viviendas_iniciadas_vpo"] = final_df["vpo_real"].fillna(final_df["vpo_iniciadas_est"])
        
        # Determinar origen
        final_df["source"] = "idescat_estimado"
        if "source_opendata" in final_df.columns:
            final_df["source"] = np.where(final_df["vpo_real"].notna(), "opendatabcn_real", final_df["source"])
        
        if not df_idescat.empty:
            anio = int(df_idescat["anio"].iloc[0])
        else:
            anio = int(datetime.now().year)
            
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fact_vivienda_publica WHERE anio = ?", (anio,))
        
        inserted = 0
        for _, row in final_df.iterrows():
            cursor.execute("""
                INSERT INTO fact_vivienda_publica 
                (barrio_id, anio, viviendas_proteccion_oficial, 
                 viviendas_iniciadas_vpo, viviendas_iniciadas_total,
                 viviendas_terminadas_vpo, viviendas_terminadas_total,
                 viviendas_principales, viviendas_no_principales,
                 num_licencias_mayor, num_licencias_menor,
                 viviendas_vacias, demanda_vpo, ayudas_alquiler,
                 source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row["barrio_id"]), anio, row["viviendas_proteccion_oficial"],
                row["viviendas_iniciadas_vpo"], row["total_iniciadas_est"],
                row["vpo_terminadas_est"], row["total_terminadas_est"],
                row["principales_est"], row["no_principales_est"],
                int(row["num_licencias_mayor"]), int(row["num_licencias_menor"]),
                row["viviendas_vacias_est"], row["demanda_vpo_est"], row["ayudas_alquiler_est"],
                row["source"], datetime.now().isoformat()
            ))
            inserted += 1
            
        conn.commit(); conn.close()
        logger.info(f"✅ Éxito: {inserted} registros actualizados en fact_vivienda_publica")
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}"); traceback.print_exc(); return 1

if __name__ == "__main__":
    import traceback
    main()
