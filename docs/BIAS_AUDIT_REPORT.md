# 📊 Data Bias Audit Analysis & Recommendations

## Executive Summary

This report documents the findings of the 2026 Q1 Data Bias Audit. The audit revealed a high risk of overfitting in the baseline model and significant geographic disparities in prediction accuracy, particularly affecting peripheral vs. affluent districts.

---

## 🔍 Critical Findings

### 1. Overfitting Risk

**Status: MITIGATED (Jan 2026)**

- **Baseline Feature**: Training MAE reached ~0.03€/m², indicating memorization of the 73 neighborhoods.
- **Action Taken**: Implemented aggressive regularization (L1/L2, max_depth=3, gamma=5.0) and 5-fold cross-validation.
- **Current Metric**: Validation MAE stabilized at ~360€/m² with a Gap Ratio of 1.4x.

### 2. Geographic Equity

- **Nou Barris Distribution**: Historically shows the highest "undervaluation" according to fundamentals. This may indicate missing local amenities or safety proxies in the model.
- **Sarrià-Sant Gervasi**: High data density creates an implicit bias where the model captures affluent market dynamics more accurately than peripheral ones.

---

## 🎯 Fairness Metrics Framework

We track the following indices to ensure equitable decisions:

1. **Geographic Equity Score (GES)**:
   `GES = 1 - (std_dev_of_district_MAEs / mean_district_MAE)`

   - _Target_: > 0.85

2. **Income Parity Ratio (IPR)**:
   `IPR = MAE_low_income_districts / MAE_high_income_districts`

   - _Target_: 0.8 < IPR < 1.2

3. **Prediction Dispersion Index (PDI)**:
   `PDI = (95th_percentile_error - 5th_percentile_error) / median_error`
   - _Target_: < 3.0

---

## 🚀 Roadmap for Improvement

### Short-term (Jan 2026)

- [x] Implement Stratified 5-Fold CV.
- [x] Apply Ridge/XGB Regularization.
- [x] Integrate **TMB Accessibility Index** (Rail counts, Bus density, Hubs).

### Mid-term (Feb 2026)

- [x] Add **Environmental Quality** (Tree density & Green score).
- [x] Integrate **Vibrancy Proxy** (Commercial intensity as safety perception).
- [ ] Refine **Geographic Equity** via segment-weighted training.

---

## 📈 Impact Assessment (Phase 2)

| Metric  | Pre-Mitigation | Post-Phase 2 | Trend                             |
| :------ | :------------- | :----------- | :-------------------------------- |
| **GES** | 0.481          | 0.468        | 📉 (Relative disparity increased) |
| **IPR** | 1.078          | 1.028        | 📈 (Parity improved)              |
| **PDI** | 6.444          | 6.978        | 📉 (Outliers remains high)        |

**Analysis**: While absolute accuracy improved in all districts, the "easy" districts (Les Corts/Horta) gained more from the new features than the "hard" ones (Sarrià/Ciutat Vella), widening the relative gap.
**Next Step**: Segment-specific feature weighting to prioritize error reduction in high-MAE districts.
