## ✅ Baseline MACRO v0.1 (Gràcia) — decisión final basada en evidencia

**Dataset macro (agregado)**  
- Input: `spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv` (175 filas)  
- Nivel: `barrio_id × anio × dataset_id`  
- Target: `precio_m2_mean`  

**Script**  
- `spike-data-validation/scripts/train_macro_baseline_gracia.py`

**Outputs**  
- Reporte: `spike-data-validation/data/logs/macro_baseline_model_203.json`  
- Predicciones temporal (dummies): `spike-data-validation/data/processed/macro_baseline_predictions_203_temporal_dummies.csv`  
- Predicciones temporal (YEAR_TREND): `spike-data-validation/data/processed/macro_baseline_predictions_203_temporal_year_trend.csv`  
- Predicciones temporal (FE-only): `spike-data-validation/data/processed/macro_baseline_predictions_203_temporal_fe_only.csv`  
- Predicciones temporal (**Structural-only**): `spike-data-validation/data/processed/macro_baseline_predictions_203_temporal_structural_only.csv`

---

### Resultados (split temporal 2025 = test)

#### Modelo DUMMIES (dummies de año + dataset + barrio)
- Random split (80/20): **R²=0.928, RMSE=194.36, MAE=164.17**
- Temporal split (2025): **R²=-0.767, RMSE=798.33, MAE=752.26**
  - Nota: no extrapola bien a un año no visto en train (la dummy del año nuevo no se puede aprender).

#### Modelo YEAR_TREND (anio_num + dummies dataset + dummies barrio)
- Random split (80/20): **R²=0.903, RMSE=225.27, MAE=193.01**
- Temporal split (2025): **R²=0.687, RMSE=335.80, MAE=294.75**
  - Nota: es equivalente a FE-only en este spike (estructurales barrio-constantes + dummies barrio ⇒ colinealidad).

#### Modelo FE-only (anio_num + dummies dataset + dummies barrio; **sin estructurales**)
- Temporal split (2025): **R²=0.687, RMSE=335.80**

#### ✅ Modelo Structural-only (estructurales + anio_num + dummies dataset; **sin dummies barrio**) — **Baseline v0.1**
- Temporal split (2025): **R²=0.710, RMSE=323.47**
  - Mejor generalización a 2025 y evita la colinealidad perfecta.

---

### Interpretación de coeficientes (Baseline v0.1 = Structural-only)

**Importante**: como usamos `drop_first=True`, los coeficientes de dummies son **efectos relativos** a una categoría baseline (omitida).

- En **Structural-only** NO hay `barrio_*`: los estructurales actúan como **proxy** de diferencias entre barrios (parsimonia).
- **Efecto temporal**:
  - `anio_num` ≈ **+121.77 €/m²/año**
- **Coeficientes**:
  - Ver `spike-data-validation/data/logs/macro_baseline_coefficients_203_structural_only_temporal.csv`

---

### Validaciones adicionales (sesgo / dispersión en 2025)

- **Scatter Real vs Predicho (test 2025)**:
  - PNG: `spike-data-validation/data/logs/scatter_temporal_structural_only_203.png`
  - Resumen JSON: `spike-data-validation/data/logs/scatter_temporal_structural_only_203_summary.json`
  - **Resultado**: **mean_residual = +203.28 €/m² ⇒ el modelo tiende a subestimar en 2025**

---

### Nota de alcance (crítica)
Este baseline es **macro**, no un hedonic micro:
- Portal Dades `precio_m2` es agregado por barrio/periodo/indicador.
- En Fase 1, Catastro aporta X imputado/agregado por barrio (no micro real).
**Micro‑hedonic (edificio-a-edificio) queda para Fase 2** con Catastro real + un `y` granular compatible.

