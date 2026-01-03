# ⚖️ Fairness A/B Test Report
Generated: 2026-01-03 13:34:36

## 🚀 Comparison Summary

| Metric | Version 1 (Baseline) | Version 2 (Accessibility+) | Change | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MAE** | 422.05€ | 448.99€ | +6.4% | ⚠️ |
| **R2** | 0.7204 | 0.6719 | -0.0485 | ⚠️ |
| **GES** (Equity) | 0.5116 | 0.3625 | -0.1492 | 📉 |
| **IPR** (Income) | 0.8806 | 0.9868 | -0.1062 | ✅ |
| **PDI** (Dispersion) | 4.7442 | 5.3318 | 0.5877 | ⚠️ |

---

## 📍 Geographic Impact (MAE per District)

| District | V1 MAE | V2 MAE | Change |
| :--- | :--- | :--- | :--- |
| Sarrià-Sant Gervasi | 815.5€ | 1021.9€ | +25.3% | ❌
| Gràcia | 714.7€ | 619.9€ | -13.3% | ✅
| Ciutat Vella | 693.9€ | 1048.7€ | +51.1% | ❌
| Sants-Montjuïc | 517.9€ | 438.4€ | -15.3% | ✅
| Nou Barris | 371.9€ | 394.4€ | +6.1% | ❌
| Sant Martí | 349.8€ | 324.3€ | -7.3% | ✅
| Horta-Guinardó | 278.4€ | 320.9€ | +15.3% | ❌
| Eixample | 271.8€ | 270.2€ | -0.6% | ✅
| Sant Andreu | 240.0€ | 246.6€ | +2.8% | ❌
| Les Corts | 239.6€ | 198.3€ | -17.2% | ✅

---

## 💡 Key Findings

### 1. Accuracy vs Fairness Trade-off
Analysis reveals if the addition of TMB/OSM data helped reduce the gap between central and peripheral districts.

### 2. High-Error District Recovery
Specifically looking at districts like **Nou Barris** and **Ciutat Vella** to see if accessibility features corrected former undervaluations.

### 3. Dispersion & Consistency
The PDI index indicates if the model is producing "wilder" predictions or if it has become more grounded.
