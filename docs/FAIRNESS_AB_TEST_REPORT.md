# ⚖️ Fairness A/B Test Report
Generated: 2026-01-03 12:51:15

## 🚀 Comparison Summary

| Metric | Version 1 (Baseline) | Version 2 (Accessibility+) | Change | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MAE** | 523.46€ | 559.78€ | +6.9% | ⚠️ |
| **R2** | 0.5601 | 0.4913 | -0.0688 | ⚠️ |
| **GES** (Equity) | 0.2614 | 0.2137 | -0.0477 | 📉 |
| **IPR** (Income) | 1.0817 | 1.2098 | +0.1280 | ⚠️ |
| **PDI** (Dispersion) | 4.7393 | 4.5868 | -0.1525 | ✅ |

---

## 📍 Geographic Impact (MAE per District)

| District | V1 MAE | V2 MAE | Change |
| :--- | :--- | :--- | :--- |
| Ciutat Vella | 1621.0€ | 1863.3€ | +15.0% | ❌
| Sarrià-Sant Gervasi | 902.3€ | 1206.3€ | +33.7% | ❌
| Gràcia | 696.1€ | 627.4€ | -9.9% | ✅
| Eixample | 531.1€ | 459.8€ | -13.4% | ✅
| Nou Barris | 467.4€ | 481.8€ | +3.1% | ❌
| Sant Martí | 465.6€ | 396.0€ | -15.0% | ✅
| Horta-Guinardó | 375.9€ | 357.9€ | -4.8% | ✅
| Sant Andreu | 311.6€ | 361.6€ | +16.0% | ❌
| Sants-Montjuïc | 276.6€ | 323.6€ | +17.0% | ❌
| Les Corts | 129.0€ | 332.5€ | +157.8% | ❌

---

## 💡 Key Findings

### 1. Accuracy vs Fairness Trade-off
Analysis reveals if the addition of TMB/OSM data helped reduce the gap between central and peripheral districts.

### 2. High-Error District Recovery
Specifically looking at districts like **Nou Barris** and **Ciutat Vella** to see if accessibility features corrected former undervaluations.

### 3. Dispersion & Consistency
The PDI index indicates if the model is producing "wilder" predictions or if it has become more grounded.
