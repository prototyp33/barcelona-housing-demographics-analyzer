#!/usr/bin/env python3
"""
Genera scatter Real vs Predicho (split temporal) para detectar sesgo y dispersión (Issue #203).

Usa los CSVs de predicciones exportados por `train_macro_baseline_gracia.py`, que contienen:
- `y_true`, `y_pred`, `residual`, `anio`, `barrio_id`, `dataset_id` (según modelo)

Output:
- PNG scatter: `spike-data-validation/data/logs/scatter_temporal_203.png`
- JSON resumen: `spike-data-validation/data/logs/scatter_temporal_203_summary.json`
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

DEFAULT_INPUT = PROCESSED_DIR / "macro_baseline_predictions_203_temporal_structural_only.csv"
DEFAULT_OUT_PNG = LOG_DIR / "scatter_temporal_structural_only_203.png"
DEFAULT_OUT_JSON = LOG_DIR / "scatter_temporal_structural_only_203_summary.json"


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def setup_matplotlib_cache() -> None:
    """Configura cache writable para Matplotlib/Fontconfig en entornos sandbox."""
    cache_root = LOG_DIR / "_mpl_cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)


def _import_matplotlib_pyplot():
    setup_matplotlib_cache()
    import matplotlib  # noqa: WPS433

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: WPS433

    return plt


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(description="Scatter real vs predicho (split temporal) - Issue #203")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT), help="CSV de predicciones temporal.")
    parser.add_argument("--out-png", type=str, default=str(DEFAULT_OUT_PNG), help="Ruta PNG de salida.")
    parser.add_argument("--out-json", type=str, default=str(DEFAULT_OUT_JSON), help="Ruta JSON resumen.")
    return parser.parse_args()


def summarize(df: pd.DataFrame) -> Dict[str, Any]:
    """Resumen de dispersión y sesgo."""
    required = {"y_true", "y_pred", "residual"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    y_true = pd.to_numeric(df["y_true"], errors="coerce")
    y_pred = pd.to_numeric(df["y_pred"], errors="coerce")
    residual = pd.to_numeric(df["residual"], errors="coerce")
    valid = df.copy()
    valid["y_true"] = y_true
    valid["y_pred"] = y_pred
    valid["residual"] = residual
    valid = valid.dropna(subset=["y_true", "y_pred", "residual"]).copy()

    if valid.empty:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "n_rows": int(len(df)),
            "n_valid": 0,
            "error": "No hay filas válidas (y_true/y_pred/residual nulos).",
        }

    mae = float(valid["residual"].abs().mean())
    mean_resid = float(valid["residual"].mean())
    rmse = float((valid["residual"] ** 2).mean() ** 0.5)

    years: List[int] = []
    if "anio" in valid.columns:
        years = sorted(pd.to_numeric(valid["anio"], errors="coerce").dropna().astype(int).unique().tolist())

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_rows": int(len(df)),
        "n_valid": int(len(valid)),
        "anio_test": years,
        "mae": mae,
        "rmse": rmse,
        "mean_residual": mean_resid,
        "bias_hint": "subestima" if mean_resid > 0 else "sobreestima" if mean_resid < 0 else "centrado",
    }


def plot_scatter(df: pd.DataFrame, out_png: Path) -> None:
    """Plot real vs pred con línea y=x."""
    required = {"y_true", "y_pred"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    y_true = pd.to_numeric(df["y_true"], errors="coerce")
    y_pred = pd.to_numeric(df["y_pred"], errors="coerce")
    valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna().copy()
    if valid.empty:
        raise ValueError("No hay filas válidas para plotear (y_true/y_pred nulos).")

    plt = _import_matplotlib_pyplot()

    lo = float(min(valid["y_true"].min(), valid["y_pred"].min()))
    hi = float(max(valid["y_true"].max(), valid["y_pred"].max()))

    plt.figure(figsize=(8, 6))
    plt.scatter(valid["y_true"], valid["y_pred"], alpha=0.65)
    plt.plot([lo, hi], [lo, hi], "r--", linewidth=1, label="Predicción perfecta (y=x)")
    plt.xlabel("Precio Real (€/m²)")
    plt.ylabel("Precio Predicho (€/m²)")
    plt.title("Structural-only: Real vs Predicho (split temporal)")
    plt.legend()
    plt.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=150)
    plt.close()


def main() -> int:
    setup_logging()
    args = parse_args()

    input_path = Path(args.input)
    out_png = Path(args.out_png)
    out_json = Path(args.out_json)

    if not input_path.exists():
        logger.error("Input no encontrado: %s", input_path)
        return 1

    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Input vacío: %s", input_path)
        return 1

    try:
        plot_scatter(df, out_png)
        logger.info("PNG guardado: %s", out_png)
    except ValueError as exc:
        logger.error("No se pudo generar el scatter: %s", exc)
        return 1

    summary = summarize(df)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Resumen JSON guardado: %s", out_json)
    logger.info(
        "Resumen: n_valid=%s | RMSE=%.2f | MAE=%.2f | mean_residual=%.2f | hint=%s",
        summary.get("n_valid"),
        float(summary.get("rmse", float("nan"))),
        float(summary.get("mae", float("nan"))),
        float(summary.get("mean_residual", float("nan"))),
        summary.get("bias_hint"),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


