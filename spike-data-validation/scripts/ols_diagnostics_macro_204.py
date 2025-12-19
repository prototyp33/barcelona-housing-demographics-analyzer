#!/usr/bin/env python3
"""
Issue #204 - Diagnósticos OLS para el baseline MACRO v0.1 (Structural-only).

Objetivo:
- Evaluar supuestos clásicos OLS sobre el modelo macro (Gràcia, Structural-only).
- Target: que al menos 4/5 tests estén en zona aceptable.

Tests implementados:
- Normalidad de residuos (Shapiro–Wilk) + Q-Q plot.
- Homocedasticidad (Breusch–Pagan).
- Multicolinealidad (VIF).
- Autocorrelación (Durbin–Watson).
- Outliers / influencia (Cook’s distance).

Outputs:
- JSON resumen: `spike-data-validation/data/logs/ols_diagnostics_macro_204.json`
- PNG Q-Q plot: `spike-data-validation/data/logs/ols_qqplot_residuals_204.png`
- PNG residuos vs ajustados: `spike-data-validation/data/logs/ols_resid_vs_fitted_204.png`
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import probplot, shapiro
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

INPUT_AGG = PROCESSED_DIR / "gracia_merged_agg_barrio_anio_dataset.csv"
DEFAULT_OUT_JSON = LOG_DIR / "ols_diagnostics_macro_204.json"
QQ_PNG = LOG_DIR / "ols_qqplot_residuals_204.png"
RESID_FITTED_PNG = LOG_DIR / "ols_resid_vs_fitted_204.png"

logger = logging.getLogger(__name__)


def _json_safe_default(obj: Any) -> Any:
    """
    Adaptador para tipos de NumPy en json.dumps.

    Convierte numpy.bool_, numpy.integer, numpy.floating a tipos nativos.
    Cualquier otro tipo desconocido se convierte a string.
    """
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    return str(obj)


@dataclass
class TestResult:
    """Resultado de un test individual de diagnóstico."""

    name: str
    passed: bool
    metric: float | None
    p_value: float | None
    threshold: str
    details: Dict[str, Any]


def setup_logging() -> None:
    """Configura logging para el script."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def setup_matplotlib_cache() -> None:
    """
    Configura rutas de caché de Matplotlib/Fontconfig en un directorio writable.

    Evita errores en entornos donde HOME/~/.cache no son escribibles.
    """
    cache_root = LOG_DIR / "_mpl_cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)


def _import_matplotlib_pyplot():
    """Importa pyplot con backend no interactivo (Agg)."""
    setup_matplotlib_cache()
    import matplotlib  # noqa: WPS433

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: WPS433

    return plt


def build_structural_only_design(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Construye X, y y nombres de columnas para el modelo Structural-only.

    Args:
        df: DataFrame agregado macro.

    Returns:
        (X, y, feature_names)

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    required = [
        "precio_m2_mean",
        "superficie_m2_barrio_mean",
        "ano_construccion_barrio_mean",
        "plantas_barrio_mean",
        "anio",
        "dataset_id",
    ]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas para Structural-only: {missing}")

    base = df.dropna(subset=required).copy()

    X_parts: List[np.ndarray] = [np.ones(len(base))]
    names: List[str] = ["intercept"]

    for c in [
        "superficie_m2_barrio_mean",
        "ano_construccion_barrio_mean",
        "plantas_barrio_mean",
    ]:
        X_parts.append(pd.to_numeric(base[c], errors="coerce").to_numpy(dtype=float))
        names.append(c)

    year_num = pd.to_numeric(base["anio"], errors="coerce").to_numpy(dtype=float)
    X_parts.append(year_num)
    names.append("anio_num")

    d_ds = pd.get_dummies(base["dataset_id"].astype(str), prefix="ds", drop_first=True)
    if not d_ds.empty:
        X_parts.append(d_ds.to_numpy(dtype=float))
        names.extend(d_ds.columns.tolist())

    X = np.column_stack(X_parts)
    y = pd.to_numeric(base["precio_m2_mean"], errors="coerce").to_numpy(dtype=float)
    return X, y, names


def run_diagnostics(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Ejecuta los diagnósticos OLS y devuelve un resumen.

    Args:
        X: Matriz de diseño (incluye intercept).
        y: Target.
        feature_names: Nombres de columnas de X.

    Returns:
        Diccionario con resultados detallados y bandera global de éxito.
    """
    model = sm.OLS(y, X).fit()
    resid = model.resid

    results: List[TestResult] = []

    # 1. Normalidad (Shapiro–Wilk)
    try:
        sh_stat, sh_p = shapiro(resid)
        norm_passed = sh_p > 0.05
        results.append(
            TestResult(
                name="shapiro_wilk_normality",
                passed=norm_passed,
                metric=float(sh_stat),
                p_value=float(sh_p),
                threshold="p > 0.05",
                details={},
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error en Shapiro–Wilk: %s", exc)
        results.append(
            TestResult(
                name="shapiro_wilk_normality",
                passed=False,
                metric=None,
                p_value=None,
                threshold="p > 0.05",
                details={"error": str(exc)},
            ),
        )

    # 2. Homocedasticidad (Breusch–Pagan)
    try:
        lm_stat, lm_pvalue, f_stat, f_pvalue = het_breuschpagan(resid, X)
        homo_passed = lm_pvalue > 0.05
        results.append(
            TestResult(
                name="breusch_pagan_homoskedasticity",
                passed=homo_passed,
                metric=float(lm_stat),
                p_value=float(lm_pvalue),
                threshold="p > 0.05",
                details={"f_stat": float(f_stat), "f_pvalue": float(f_pvalue)},
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error en Breusch–Pagan: %s", exc)
        results.append(
            TestResult(
                name="breusch_pagan_homoskedasticity",
                passed=False,
                metric=None,
                p_value=None,
                threshold="p > 0.05",
                details={"error": str(exc)},
            ),
        )

    # 3. Multicolinealidad (VIF)
    try:
        vifs: Dict[str, float] = {}
        for i, col in enumerate(feature_names):
            vif_val = float(variance_inflation_factor(X, i))
            vifs[col] = vif_val
        # Ignoramos el intercept para el criterio
        max_vif = max(v for k, v in vifs.items() if k != "intercept")
        vif_passed = max_vif < 10.0
        results.append(
            TestResult(
                name="vif_multicollinearity",
                passed=vif_passed,
                metric=float(max_vif),
                p_value=None,
                threshold="max VIF (sin intercept) < 10",
                details={"vifs": vifs},
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error calculando VIF: %s", exc)
        results.append(
            TestResult(
                name="vif_multicollinearity",
                passed=False,
                metric=None,
                p_value=None,
                threshold="max VIF (sin intercept) < 10",
                details={"error": str(exc)},
            ),
        )

    # 4. Autocorrelación (Durbin–Watson)
    try:
        dw_val = float(durbin_watson(resid))
        dw_passed = 1.5 <= dw_val <= 2.5
        results.append(
            TestResult(
                name="durbin_watson_autocorrelation",
                passed=dw_passed,
                metric=dw_val,
                p_value=None,
                threshold="1.5 <= DW <= 2.5",
                details={},
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error en Durbin–Watson: %s", exc)
        results.append(
            TestResult(
                name="durbin_watson_autocorrelation",
                passed=False,
                metric=None,
                p_value=None,
                threshold="1.5 <= DW <= 2.5",
                details={"error": str(exc)},
            ),
        )

    # 5. Outliers / influencia (Cook’s distance)
    try:
        influence = model.get_influence()
        cooks_d = influence.cooks_distance[0]
        n = len(cooks_d)
        thresh = 4.0 / max(n, 1)
        num_extremos = int(np.sum(cooks_d > thresh))
        cooks_passed = num_extremos == 0
        results.append(
            TestResult(
                name="cooks_distance_outliers",
                passed=cooks_passed,
                metric=float(num_extremos),
                p_value=None,
                threshold="Cook's D <= 4/n para todos los puntos",
                details={"threshold": float(thresh)},
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error calculando Cook's distance: %s", exc)
        results.append(
            TestResult(
                name="cooks_distance_outliers",
                passed=False,
                metric=None,
                p_value=None,
                threshold="Cook's D <= 4/n para todos los puntos",
                details={"error": str(exc)},
            ),
        )

    # Q-Q plot y resid vs fitted para inspección visual
    plt = _import_matplotlib_pyplot()

    plt.figure()
    probplot(resid, dist="norm", plot=plt)
    plt.title("Q-Q plot residuos (Structural-only, Issue #204)")
    plt.tight_layout()
    QQ_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(QQ_PNG, dpi=150)
    plt.close()

    fitted = model.fittedvalues
    plt.figure()
    plt.scatter(fitted, resid, alpha=0.6)
    plt.axhline(0.0, color="red", linestyle="--", linewidth=1)
    plt.xlabel("Fitted values")
    plt.ylabel("Residuos")
    plt.title("Residuos vs Fitted (Structural-only, Issue #204)")
    plt.tight_layout()
    plt.savefig(RESID_FITTED_PNG, dpi=150)
    plt.close()

    passed_count = sum(tr.passed for tr in results)
    summary: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_obs": int(len(y)),
        "tests": [asdict(tr) for tr in results],
        "passed_tests": int(passed_count),
        "total_tests": int(len(results)),
        "criterion_target": ">=4/5 tests pasan",
        "criterion_met": bool(passed_count >= 4),
        "artifacts": {
            "qqplot_png": str(QQ_PNG),
            "resid_vs_fitted_png": str(RESID_FITTED_PNG),
        },
        "model_summary_short": {
            "r2": float(model.rsquared),
            "rmse": float(np.sqrt(np.mean(resid**2))),
        },
    }
    return summary


def main() -> int:
    """Punto de entrada principal del script."""
    setup_logging()
    logger.info("=== Issue #204: Diagnósticos OLS (baseline macro Structural-only) ===")

    if not INPUT_AGG.exists():
        logger.error("Input macro no encontrado: %s", INPUT_AGG)
        return 1

    df = pd.read_csv(INPUT_AGG)
    if df.empty:
        logger.error("Input macro vacío: %s", INPUT_AGG)
        return 1

    try:
        X, y, names = build_structural_only_design(df)
    except ValueError as exc:
        logger.error("Error construyendo diseño Structural-only: %s", exc)
        return 1

    logger.info("Diseño Structural-only construido: X.shape=%s, y.shape=%s", X.shape, y.shape)

    summary = run_diagnostics(X, y, names)

    DEFAULT_OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=_json_safe_default),
        encoding="utf-8",
    )
    logger.info(
        "Resumen de diagnósticos guardado en %s (tests OK: %s/%s, criterio_met=%s)",
        DEFAULT_OUT_JSON,
        summary["passed_tests"],
        summary["total_tests"],
        summary["criterion_met"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


