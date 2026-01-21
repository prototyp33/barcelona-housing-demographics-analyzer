# ⚖️ Fairness A/B Test Report
Generated: 2026-01-21 13:11:08

## 🚀 Comparison Summary

| Metric | Version 1 (Baseline) | Version 2 (Accessibility+) | Change | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MAE** | 370.94€ | 409.40€ | +10.4% | ⚠️ |
| **R2** | 0.8149 | 0.7591 | -0.0558 | ⚠️ |
| **GES** (Equity) | 0.6012 | 0.4266 | -0.1746 | 📉 |
| **IPR** (Income) | 0.8725 | 1.0027 | -0.1248 | ✅ |
| **PDI** (Dispersion) | 2.5802 | 3.7193 | 1.1391 | ⚠️ |

---

## 📍 Geographic Impact (MAE per District)

| District | V1 MAE | V2 MAE | Change |
| :--- | :--- | :--- | :--- |
| Ciutat Vella | 682.4€ | 945.8€ | +38.6% | ❌
| Sarrià-Sant Gervasi | 596.3€ | 706.1€ | +18.4% | ❌
| Eixample | 424.2€ | 350.1€ | -17.5% | ✅
| Gràcia | 419.8€ | 672.8€ | +60.3% | ❌
| Nou Barris | 358.8€ | 400.0€ | +11.5% | ❌
| Sant Martí | 325.2€ | 330.1€ | +1.5% | ❌
| Horta-Guinardó | 324.0€ | 300.9€ | -7.1% | ✅
| Sant Andreu | 288.4€ | 266.2€ | -7.7% | ✅
| Sants-Montjuïc | 263.5€ | 293.0€ | +11.2% | ❌
| Les Corts | 173.2€ | 128.2€ | -26.0% | ✅

---

## 💡 Key Findings

### 1. Accuracy vs Fairness Trade-off
Analysis reveals if the addition of TMB/OSM data helped reduce the gap between central and peripheral districts.

### 2. High-Error District Recovery
Specifically looking at districts like **Nou Barris** and **Ciutat Vella** to see if accessibility features corrected former undervaluations.

### 3. Dispersion & Consistency
The PDI index indicates if the model is producing "wilder" predictions or if it has become more grounded.
