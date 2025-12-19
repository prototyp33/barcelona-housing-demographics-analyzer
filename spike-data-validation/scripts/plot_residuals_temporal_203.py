#!/usr/bin/env python3
"""
Genera un plot de residuos para detectar sesgo temporal (Issue #203).

Este script utiliza el output del modelo macro baseline (YEAR_TREND) en split temporal:
- `spike-data-validation/data/processed/macro_baseline_predictions_203_temporal_year_trend.csv`

Notas:
- En el split temporal actual, el test es típicamente un solo año (por defecto 2025).
  Por tanto, el eje "tiempo" no aporta mucha variación; el criterio principal es si
  los residuos están centrados alrededor de 0 para ese año (no sesgo).

Outputs:
- PNG: `spike-data-validation/data/logs/residuals_temporal_year_trend_203.png`
- CSV resumen: `spike-data-validation/data/logs/residuals_temporal_year_trend_203_summary.csv`
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

DEFAULT_INPUT = PROCESSED_DIR / "macro_baseline_predictions_203_temporal_year_trend.csv"
DEFAULT_OUT_PNG = LOG_DIR / "residuals_temporal_year_trend_203.png"
DEFAULT_OUT_SUMMARY = LOG_DIR / "residuals_temporal_year_trend_203_summary.csv"
DEFAULT_OUT_JSON = LOG_DIR / "residuals_temporal_year_trend_203_summary.json"


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def setup_matplotlib_cache() -> None:
    """
    Configura rutas de caché de Matplotlib/Fontconfig en un directorio writable.

    Motivo:
    - En entornos sandbox (o CI) el HOME puede ser de solo lectura. Matplotlib y fontconfig
      intentan escribir cache en `~/.matplotlib` y `~/.cache/fontconfig`.
    """
    cache_root = LOG_DIR / "_mpl_cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    # Matplotlib config/cache
    os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    # Fontconfig cache (resuelve "No writable cache directories")
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)


def _import_matplotlib_pyplot():
    """
    Importa pyplot usando backend no interactivo.

    Returns:
        Módulo `matplotlib.pyplot`.
    """
    setup_matplotlib_cache()
    import matplotlib  # noqa: WPS433

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: WPS433

    return plt


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(description="Plot de residuos vs tiempo (split temporal) - Issue #203")
    parser.add_argument("--input", type=str, default=str(DEFAULT_INPUT), help="CSV de predicciones temporal.")
    parser.add_argument("--out-png", type=str, default=str(DEFAULT_OUT_PNG), help="Ruta PNG de salida.")
    parser.add_argument(
        "--out-summary",
        type=str,
        default=str(DEFAULT_OUT_SUMMARY),
        help="Ruta CSV resumen de salida.",
    )
    parser.add_argument(
        "--out-json",
        type=str,
        default=str(DEFAULT_OUT_JSON),
        help="Ruta JSON resumen de salida.",
    )
    return parser.parse_args()


def build_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Construye un resumen de residuos para validación rápida.

    Args:
        df: DataFrame de predicciones con `y_true`, `y_pred`, `residual`.

    Returns:
        Dict con métricas globales y por grupo.

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    required = {"y_true", "y_pred", "residual", "anio"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    resid = pd.to_numeric(df["residual"], errors="coerce")
    y_true = pd.to_numeric(df["y_true"], errors="coerce")
    y_pred = pd.to_numeric(df["y_pred"], errors="coerce")

    valid = df.copy()
    valid["residual"] = resid
    valid["y_true"] = y_true
    valid["y_pred"] = y_pred
    valid = valid.dropna(subset=["residual", "y_true", "y_pred"]).copy()

    if valid.empty:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "n_rows": int(len(df)),
            "n_valid": 0,
            "error": "No hay filas válidas (y_true/y_pred/residual nulos).",
        }

    mae = float((valid["residual"].abs()).mean())
    mean_resid = float(valid["residual"].mean())
    median_resid = float(valid["residual"].median())

    out: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(df)),
        "n_valid": int(len(valid)),
        "anio_test": sorted(pd.to_numeric(valid["anio"], errors="coerce").dropna().astype(int).unique().tolist()),
        "mae": mae,
        "mean_residual": mean_resid,
        "median_residual": median_resid,
        "bias_hint": "subestima" if mean_resid > 0 else "sobreestima" if mean_resid < 0 else "centrado",
    }

    # Resumen por barrio/dataset si existen
    group_cols = [c for c in ["barrio_id", "dataset_id"] if c in valid.columns]
    if group_cols:
        grp = (
            valid.groupby(group_cols, dropna=False)
            .agg(
                n=("residual", "size"),
                mean_residual=("residual", "mean"),
                mae=("residual", lambda s: float(s.abs().mean())),
            )
            .reset_index()
            .sort_values("mae", ascending=False)
        )
        out["group_cols"] = group_cols
        out["top_groups_by_mae"] = grp.head(10).to_dict(orient="records")

    return out


def plot_residuals(df: pd.DataFrame, out_png: Path) -> None:
    """
    Genera el plot de residuos vs año, con línea 0.

    Args:
        df: DataFrame con columnas `anio` y `residual`.
        out_png: Ruta de salida PNG.

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    if "anio" not in df.columns or "residual" not in df.columns:
        raise ValueError("El DataFrame debe contener 'anio' y 'residual'.")

    plot_df = df.copy()
    plot_df["anio"] = pd.to_numeric(plot_df["anio"], errors="coerce")
    plot_df["residual"] = pd.to_numeric(plot_df["residual"], errors="coerce")
    plot_df = plot_df.dropna(subset=["anio", "residual"]).copy()

    if plot_df.empty:
        raise ValueError("No hay datos válidos para plotear (anio/residual nulos).")

    plt = _import_matplotlib_pyplot()
    plt.figure(figsize=(10, 5))

    # Si solo hay un año (caso típico), metemos un pequeño jitter en X para visualizar dispersión.
    unique_years = plot_df["anio"].unique()
    if len(unique_years) == 1:
        x = plot_df["anio"] + (pd.Series(range(len(plot_df))) % 7 - 3) * 0.01
    else:
        x = plot_df["anio"]

    plt.scatter(x, plot_df["residual"], alpha=0.6)
    plt.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.xlabel("Año")
    plt.ylabel("Residuo (€/m²)")
    plt.title("Residuos del Modelo vs Tiempo (split temporal - YEAR_TREND)")
    plt.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=150)
    plt.close()


def main() -> int:
    setup_logging()
    args = parse_args()

    input_path = Path(args.input)
    out_png = Path(args.out_png)
    out_summary = Path(args.out_summary)
    out_json = Path(args.out_json)

    if not input_path.exists():
        logger.error("Input no encontrado: %s", input_path)
        return 1

    df = pd.read_csv(input_path)
    if df.empty:
        logger.error("Input vacío: %s", input_path)
        return 1

    # La salida ya trae residual, pero lo recalculamos por seguridad si falta.
    if "residual" not in df.columns and {"y_true", "y_pred"} <= set(df.columns):
        df = df.copy()
        df["residual"] = pd.to_numeric(df["y_true"], errors="coerce") - pd.to_numeric(df["y_pred"], errors="coerce")

    try:
        plot_residuals(df, out_png)
        logger.info("PNG guardado: %s", out_png)
    except ValueError as exc:
        logger.error("No se pudo generar el plot: %s", exc)
        return 1

    summary = build_summary(df)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary.get("top_groups_by_mae", [])).to_csv(out_summary, index=False, encoding="utf-8")
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Resumen CSV guardado: %s", out_summary)
    logger.info("Resumen JSON guardado: %s", out_json)

    logger.info(
        "Resumen: n_valid=%s | mean_residual=%.2f | MAE=%.2f | hint=%s",
        summary.get("n_valid"),
        float(summary.get("mean_residual", float("nan"))),
        float(summary.get("mae", float("nan"))),
        summary.get("bias_hint"),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


