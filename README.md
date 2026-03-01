# 🏠 Barcelona Housing Demographics Analyzer

[![CI Pipeline](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/prototyp33/barcelona-housing-demographics-analyzer)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/releases)
[![License](https://img.shields.io/github/license/prototyp33/barcelona-housing-demographics-analyzer)](LICENSE)
[![Issues](https://img.shields.io/github/issues/prototyp33/barcelona-housing-demographics-analyzer)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues)
[![Last commit](https://img.shields.io/github/last-commit/prototyp33/barcelona-housing-demographics-analyzer/main)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/commits/main)

A comprehensive data analytics platform for Barcelona's housing market, combining demographic data, accessibility metrics, and machine learning to provide insights into housing prices and neighborhood characteristics.

---

## 🎯 Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Git
- 4GB RAM minimum

### Installation

```bash
# Clone the repository
git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer

# Create virtual environment
python3 -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

#### Option 1: Streamlit Dashboard (Recommended)

```bash
./scripts/run_dashboard.sh
```

Then open http://localhost:8501 in your browser.

#### Option 2: FastAPI Backend

```bash
./scripts/run_api.sh
```

Then open http://localhost:8000/docs for API documentation.

#### Option 3: Manual with PYTHONPATH

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
streamlit run src/app/main.py
# or
uvicorn src.api.main:app --reload
```

---

## 📊 Features

### Data Pipeline

- **TMB/OSM Integration:** 1,071 bus stops + 165 rail stations
- **Demographic Data:** Population, age, immigration metrics
- **Accessibility Metrics:** Transit proximity, accessibility scores
- **Housing Prices:** Sale and rental prices per m²
- **Income Data:** Median household income by neighborhood

### Analytics

- **Fairness A/B Testing:** Compare model versions for equity
- **Neighborhood Clustering:** Identify similar areas
- **Price Predictions:** ML-based price forecasting
- **Trend Analysis:** Historical price evolution
- **Gentrification Risk:** Early warning indicators

### Visualizations

- Interactive maps with neighborhood boundaries
- Price heatmaps and trend charts
- Accessibility score visualizations
- Demographic breakdowns
- Correlation matrices

---

## 🗄️ Database Schema

### Core Tables

- `dim_barrios` - 73 Barcelona neighborhoods (dimension table)
- `fact_precios` - Housing prices (sale/rental)
- `fact_demografia_ampliada` - Granular demographic data
- `fact_renta` - Income statistics
- `fact_movilidad` - Accessibility metrics (NEW)

### Views

- `v_demografia_aggregated` - Aggregated demographic metrics
- `v_affordability_quarterly` - Affordability analysis
- `v_barrio_scorecard` - Comprehensive neighborhood metrics

See `docs/DATABASE_SCHEMA.md` for complete schema.

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Suite

```bash
pytest tests/test_fk_validation.py -v
pytest tests/test_data_extraction.py -v
```

### Run Fairness A/B Test

```bash
python scripts/fairness_ab_harness.py
```

### Coverage Report

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📁 Project Structure

```
barcelona-housing-demographics-analyzer/
├── src/
│   ├── api/              # FastAPI backend
│   ├── app/              # Streamlit dashboard
│   ├── etl/              # ETL pipeline
│   ├── extraction/       # Data extractors (TMB, OSM, Open Data BCN)
│   ├── processing/       # Data transformations
│   └── database_setup.py # Database schema
├── scripts/
│   ├── fairness_ab_harness.py  # A/B testing framework
│   └── test_issue_*.py         # Validation scripts
├── tests/                # Unit and integration tests
├── docs/                 # Documentation
├── data/
│   ├── raw/             # Raw extracted data
│   └── processed/       # Processed database
├── scripts/run_dashboard.sh   # Helper to run Streamlit
└── scripts/run_api.sh        # Helper to run FastAPI
```

---

## 🚀 Usage Examples

### Dashboard Navigation

1. **Overview** - High-level metrics and trends
2. **Market View** - Price analysis by neighborhood
3. **Demographics** - Population and age statistics
4. **Map Analysis** - Geographic visualizations
5. **Correlations** - Feature relationships
6. **Data Quality** - Pipeline health metrics

### API Endpoints

```bash
# Get all neighborhoods
curl http://localhost:8000/barrios

# Get specific neighborhood
curl http://localhost:8000/barrios/1

# Get price statistics
curl http://localhost:8000/stats/prices

# Get accessibility rankings
curl http://localhost:8000/accessibility/rankings
```

See http://localhost:8000/docs for interactive API documentation.

---

## 🔧 Configuration

### Environment Variables

```bash
export DB_PATH="data/processed/database.db"
export API_PORT=8000
export DASHBOARD_PORT=8501
```

### Streamlit Config

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

---

## 📈 Data Sources

- **TMB (Transports Metropolitans de Barcelona)** - Public transit data
- **OpenStreetMap** - Geographic and transit infrastructure
- **Open Data BCN** - Demographics, housing, income
- **INE (Instituto Nacional de Estadística)** - National statistics
- **Idealista** - Real estate listings (historical)

---

## 🎓 Key Metrics

### Model Performance

- **MAE:** 422€ (Mean Absolute Error)
- **R²:** 0.72 (Coefficient of Determination)
- **Coverage:** 73/73 neighborhoods (100%)

### Fairness Metrics

- **GES (Group Equity Score):** 0.51 (target: >0.70)
- **IPR (Income Parity Ratio):** 0.88 (target: 0.8-1.2)
- **PDI (Prediction Dispersion Index):** 4.74 (target: <5.0)

### Data Quality

- **Test Coverage:** 34.53%
- **Passing Tests:** 299/313
- **ETL Success Rate:** >95%

---

## 🛠️ Development

### Run ETL Pipeline

```bash
python -m src.etl.pipeline
```

### Create New View

```python
from src.database_views import create_analytical_views
import sqlite3

conn = sqlite3.connect('data/processed/database.db')
create_analytical_views(conn)
conn.close()
```

### Add New Extractor

1. Create extractor in `src/extraction/`
2. Inherit from `BaseExtractor`
3. Implement `extract()` method
4. Add to `orchestrator.py`

---

## 📚 Documentation

- **Next Steps:** `docs/NEXT_STEPS.md` - Phase 3 roadmap
- **Sprint Completion:** `docs/SPRINT_COMPLETION_FINAL.md` - Recent achievements
- **Database Schema:** `docs/DATABASE_SCHEMA.md` - Complete schema
- **Fairness Report:** `docs/FAIRNESS_AB_TEST_REPORT.md` - Latest A/B test results
- **Test Status:** `docs/TEST_STATUS_SUMMARY.md` - Testing overview

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

**Solution:** Use the helper scripts or set PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### "Port 8501 is already in use"

**Solution:** Kill existing process:

```bash
lsof -ti:8501 | xargs kill -9
```

### "Database file not found"

**Solution:** Run ETL pipeline to create database:

```bash
python -m src.etl.pipeline
```

### Streamlit theme warnings

**Solution:** These are harmless. Update `.streamlit/config.toml` to remove deprecated options.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8
- Add type hints
- Write docstrings
- Include tests
- Update documentation

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Data Sources:** TMB, OpenStreetMap, Open Data BCN, INE
- **Technologies:** Python, Streamlit, FastAPI, XGBoost, GeoPandas
- **Contributors:** See GitHub contributors page

---

## 📞 Support

- **Issues:** https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues
- **Discussions:** https://github.com/prototyp33/barcelona-housing-demographics-analyzer/discussions
- **Documentation:** `docs/` directory

---

## 🎯 Roadmap

### Phase 3 (Current)

- [ ] Feature engineering improvements
- [ ] Model fairness optimization
- [ ] Dashboard enhancements
- [ ] API expansion

### Future Phases

- [ ] Time series forecasting
- [ ] Gentrification risk scoring
- [ ] Investment opportunity ranking
- [ ] Mobile app

See `docs/NEXT_STEPS.md` for detailed roadmap.

---

**Last Updated:** 2026-01-03  
**Version:** 2.0.0  
**Status:** ✅ Production Ready
