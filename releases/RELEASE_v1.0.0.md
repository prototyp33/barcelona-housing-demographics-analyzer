# Barcelona Housing Demographics Analyzer — v1.0.0

**Release Date:** February 24, 2026  
**First stable release** — Modelo robusto, dashboard funcional y API lista para producción.

---

## Highlights

| Componente | Estado |
|------------|--------|
| **Modelo ML** | R²=0.8083, MAE≈318€/m², IPR 1.73 (fairness gate) |
| **Dashboard** | Streamlit con 10+ vistas (Overview, Mapas, Inversión, ESG, etc.) |
| **API** | FastAPI con predicciones, inversión y estadísticas |
| **Datos** | 73 barrios, 2012–2025 precios, 2015–2025 demografía/renta |
| **Tests** | 34.53% cobertura, CI passing |

---

## Quick Start

```bash
git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
git checkout v1.0.0

python3 -m venv myenv && source myenv/bin/activate
pip install -r requirements.txt

# Ejecutar ETL (genera data/processed/database.db)
python -m src.etl.pipeline

# Dashboard
./run_dashboard.sh   # http://localhost:8501

# API
./run_api.sh         # http://localhost:8000/docs
```

---

## What's New in v1.0

### Modelo Phase 5
- Social ESG features integradas
- Fairness A/B testing harness
- VotingRegressor (XGBoost + RF + GradientBoost)
- IPR dentro del gate [0.8, 1.8]

### API REST
- Predicciones de precios por barrio
- Recomendaciones de inversión
- Estadísticas por año/distrito
- Documentación Swagger en `/docs`

### Datos
- Renta 2015–2025 (forward-fill 2024–2025)
- Demografía ampliada 2015–2025
- 20+ datasets avanzados (educación, salud, turismo, etc.)
- Tabla maestra para Looker Studio

### Dashboard
- Design System unificado
- Market Intelligence (gap negociación, gentrificación)
- Data Quality metrics
- Correlaciones y análisis avanzado

---

## Assets

- **Código fuente**: Este release
- **Base de datos**: Generar con `python -m src.etl.pipeline` (ver docs)
- **Modelos**: Entrenar con `scripts/optimize_model.py` (ver spike-data-validation)

---

## Full Changelog

Ver [CHANGELOG.md](../CHANGELOG.md) para la lista completa de cambios.

---

## Próximos pasos (v2.0)

- Migración PostgreSQL (opcional)
- ETL automatizado (scheduling)
- API pública documentada
- Análisis DiD (Difference-in-Differences)
