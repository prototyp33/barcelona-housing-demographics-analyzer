#!/usr/bin/env python3
"""
Fase 2 (Issue #200): comparación de Catastro imputado (Fase 1) vs real (Fase 2).

Genera/actualiza el reporte:
- spike-data-validation/docs/ANALISIS_IMPUTADO_VS_REAL.md

Inputs por defecto:
- spike-data-validation/data/processed/catastro_gracia_imputado.csv
- spike-data-validation/data/processed/catastro_gracia_real.csv
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

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
        "--imputed",
        type=str,
        default="spike-data-validation/data/processed/catastro_gracia_imputado.csv",
    )
    parser.add_argument(
        "--real",
        type=str,
        default="spike-data-validation/data/processed/catastro_gracia_real.csv",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="spike-data-validation/docs/ANALISIS_IMPUTADO_VS_REAL.md",
    )
    return parser.parse_args()


def _require_cols(df: pd.DataFrame, cols: list[str], name: str) -> None:
    missing = sorted(set(cols) - set(df.columns))
    if missing:
        raise ValueError(f"{name}: faltan columnas requeridas: {missing}")


def main() -> int:
    setup_logging()
    args = parse_args()
    imputed_path = Path(args.imputed)
    real_path = Path(args.real)
    out_path = Path(args.out)

    if not imputed_path.exists():
        raise FileNotFoundError(f"Imputado no encontrado: {imputed_path}")
    if not real_path.exists():
        raise FileNotFoundError(f"Real no encontrado: {real_path}")

    df_imp = pd.read_csv(imputed_path)
    df_real = pd.read_csv(real_path)
    if df_imp.empty:
        logger.error("Imputado vacío: %s", imputed_path)
        return 1
    if df_real.empty:
        logger.error("Real vacío: %s", real_path)
        return 1

    _require_cols(df_imp, ["referencia_catastral", "superficie_m2", "ano_construccion", "plantas"], "imputado")
    _require_cols(df_real, ["referencia_catastral"], "real")

    # Normalizar tipos
    df_imp = df_imp.copy()
    df_real = df_real.copy()
    df_imp["referencia_catastral"] = df_imp["referencia_catastral"].astype(str).str.strip()
    df_real["referencia_catastral"] = df_real["referencia_catastral"].astype(str).str.strip()

    for col in ["superficie_m2", "ano_construccion", "plantas"]:
        df_imp[col] = pd.to_numeric(df_imp[col], errors="coerce")
        if col in df_real.columns:
            df_real[col] = pd.to_numeric(df_real[col], errors="coerce")

    df_comp = df_imp.merge(df_real, on="referencia_catastral", how="inner", suffixes=("_imp", "_real"))
    match_rate = len(df_comp) / float(df_imp["referencia_catastral"].nunique()) * 100.0

    # Métricas solo si existen las columnas reales
    superficie_stats = None
    ano_stats = None
    plantas_stats = None

    if "superficie_m2_real" in df_comp.columns:
        diff = (df_comp["superficie_m2_imp"] - df_comp["superficie_m2_real"]).abs()
        superficie_stats = {
            "mean": float(diff.mean()),
            "std": float(diff.std()),
            "gt20": int((diff > 20).sum()),
            "gt20_pct": float((diff > 20).mean() * 100.0),
        }

    if "ano_construccion_real" in df_comp.columns:
        diff = (df_comp["ano_construccion_imp"] - df_comp["ano_construccion_real"]).abs()
        ano_stats = {
            "mean": float(diff.mean()),
            "std": float(diff.std()),
            "gt20": int((diff > 20).sum()),
            "gt20_pct": float((diff > 20).mean() * 100.0),
        }

    if "plantas_real" in df_comp.columns:
        diff = (df_comp["plantas_imp"] - df_comp["plantas_real"]).abs()
        plantas_stats = {
            "mean": float(diff.mean()),
            "std": float(diff.std()),
            "gt2": int((diff > 2).sum()),
            "gt2_pct": float((diff > 2).mean() * 100.0),
        }

    ts = datetime.now(timezone.utc).isoformat()
    lines = []
    lines.append("# Análisis: Catastro imputado vs real (Gràcia)")
    lines.append("")
    lines.append(f"**Timestamp**: {ts}")
    lines.append("")
    lines.append("## Matching")
    lines.append("")
    lines.append(f"- **Imputado (RC únicas)**: {df_imp['referencia_catastral'].nunique()}")
    lines.append(f"- **Real (filas)**: {len(df_real)}")
    lines.append(f"- **Intersección (filas)**: {len(df_comp)}")
    lines.append(f"- **Match rate vs imputado**: {match_rate:.1f}%")
    lines.append("")

    lines.append("## Diferencias (abs)")
    lines.append("")
    if superficie_stats:
        lines.append("### Superficie (m²)")
        lines.append(f"- Diferencia media: {superficie_stats['mean']:.1f} (±{superficie_stats['std']:.1f})")
        lines.append(
            f"- Diff > 20 m²: {superficie_stats['gt20']} ({superficie_stats['gt20_pct']:.1f}%)",
        )
        lines.append("")
    else:
        lines.append("- **Superficie**: no disponible en dataset real parseado.")
        lines.append("")

    if ano_stats:
        lines.append("### Año construcción")
        lines.append(f"- Diferencia media: {ano_stats['mean']:.1f} (±{ano_stats['std']:.1f})")
        lines.append(f"- Diff > 20 años: {ano_stats['gt20']} ({ano_stats['gt20_pct']:.1f}%)")
        lines.append("")
    else:
        lines.append("- **Año construcción**: no disponible en dataset real parseado.")
        lines.append("")

    if plantas_stats:
        lines.append("### Plantas")
        lines.append(f"- Diferencia media: {plantas_stats['mean']:.2f} (±{plantas_stats['std']:.2f})")
        lines.append(f"- Diff > 2 plantas: {plantas_stats['gt2']} ({plantas_stats['gt2_pct']:.1f}%)")
        lines.append("")
    else:
        lines.append("- **Plantas**: no disponible en dataset real parseado.")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Reporte actualizado: %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


