# SPIKE: Data Validation - Barcelona Housing Hedonic Model

**Duration:** 1 week (Dec 16-20, 2025)  
**Barrio Piloto:** Gràcia  
**Objetivo:** Validate if hedonic pricing model is viable with public data

## Quick Links

- [Master Tracker Issue](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/139)
- [Viability Report](outputs/reports/VIABILITY_REPORT.pdf) (pending)
- [Decision Record](outputs/reports/DECISION_RECORD.md) (pending)
- [Main Notebook](notebooks/01-gracia-hedonic-model.ipynb)

## Success Criteria (Go/No-Go)

- [ ] Match Rate ≥70%
- [ ] R² Ajustado ≥0.55
- [ ] Sample Size ≥100
- [ ] 4/5 OLS Assumptions Pass
- [ ] Coeficientes económicamente plausibles
- [ ] Documentación completa

## Current Status

**As of:** [Update daily]  
**Match Rate:** TBD  
**R²:** TBD  
**Decision:** PENDING

## Team

- **Data Engineer:** [Name]
- **Data Scientist:** [Name]
- **Product Manager:** [Name]

## Timeline

| Day | Tasks | Status |
|-----|-------|--------|
| Mon Dec 16 | Extract data (INE, Catastro) | ⏳ |
| Tue Dec 17 | Data linking & cleaning | ⏳ |
| Wed Dec 18 | Build OLS model | ⏳ |
| Thu Dec 19 | Model diagnostics | ⏳ |
| Fri Dec 20 | Report & Decision Meeting | ⏳ |

## Files Structure

spike-data-validation/
├── data/
│ ├── raw/ # Original data sources
│ │ ├── ine_precios_gracia.csv
│ │ └── catastro_gracia.csv
│ ├── processed/ # Cleaned & merged
│ │ └── gracia_merged.csv
│ └── logs/ # Extraction logs
├── notebooks/
│ └── 01-gracia-hedonic-model.ipynb
└── outputs/
├── reports/
│ ├── VIABILITY_REPORT.pdf
│ └── DECISION_RECORD.md
└── visualizations/
├── eda_01_price_distribution.png
└── diagnostics_01_assumptions.png

