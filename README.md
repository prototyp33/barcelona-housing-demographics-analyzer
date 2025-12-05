# Barcelona Housing Demographics Analyzer

[![Issues Abiertas](https://img.shields.io/github/issues/prototyp33/barcelona-housing-demographics-analyzer?style=flat-square)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues)
[![Issues Cerradas](https://img.shields.io/github/issues-closed/prototyp33/barcelona-housing-demographics-analyzer?style=flat-square&color=success)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues?q=is%3Aissue+is%3Aclosed)
[![Pull Requests](https://img.shields.io/github/issues-pr/prototyp33/barcelona-housing-demographics-analyzer?style=flat-square)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/pulls)
[![Última Actualización](https://img.shields.io/github/last-commit/prototyp33/barcelona-housing-demographics-analyzer?style=flat-square)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/commits/main)

[![CI Status](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/workflows/CI%20Pipeline/badge.svg)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/prototyp33/barcelona-housing-demographics-analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/prototyp33/barcelona-housing-demographics-analyzer)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/pulls)

> 📊 Dashboard interactivo de análisis de vivienda y demografía en Barcelona

## 📊 Project Status

### Sprint Progress

![Sprint 1](https://img.shields.io/badge/Sprint%201-75%25-green?style=flat-square)
![Sprint 2](https://img.shields.io/badge/Sprint%202-0%25-lightgrey?style=flat-square)
![Sprint 3](https://img.shields.io/badge/Sprint%203-0%25-lightgrey?style=flat-square)
![Sprint 4](https://img.shields.io/badge/Sprint%204-0%25-lightgrey?style=flat-square)

### Data Quality

| Metric | Status | Target |
|--------|--------|--------|
| Data Completeness | 96.2% ✅ | ≥95% |
| Data Validity | 98.5% ✅ | ≥98% |
| Test Coverage | 78% ⚠️ | ≥80% |
| Docs Coverage | 65% ⚠️ | ≥70% |

### Quick Links

- 📋 [Project Board](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects)
- 📊 [Live Dashboard](https://barcelona-housing-analyzer.streamlit.app) *(si está desplegado)*
- 📖 [Documentation](./docs)
- 🐛 [Report Bug](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/new?template=bug_report.yml)
- ✨ [Request Feature](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/new?template=feature_request.yml)

Open-source dashboard to analyze the relationship between demographic evolution and housing prices in Barcelona.

## 📋 Vision and Objectives

This project aims to consolidate demographic data and housing prices from multiple public sources (INE, Open Data BCN, Idealista) into a unified, clean, and normalized database that enables integrated analysis, statistical correlations, and interactive visualizations.

**Key Objectives**:
- Integrate 3+ public data sources
- Ensure data quality: ≥95% completeness, ≥98% validity
- Maintain historical data from 2015-2025 (10 years)
- Enable analysis by neighborhood/district with temporal granularity (quarterly/annual)
- Support periodic updates (quarterly) with future automation capabilities

For detailed vision and objectives, see [docs/01_VISION_AND_OBJECTIVES.md](docs/01_VISION_AND_OBJECTIVES.md).

Additional context:
- [Project Charter & Developer Profile](docs/PROJECT_CHARTER.md)
- [Project Management Playbook](docs/PROJECT_MANAGEMENT.md)

## 📁 Project Structure

```
barcelona-housing-demographics-analyzer/
├── data/
│   ├── raw/           # Raw data from sources
│   └── processed/     # Cleaned and normalized data
├── docs/              # Documentation (planning assets + visuals/wireframes)
│   ├── planning/      # Roadmaps, discovery notes, sprint backlogs
│   └── visuals/       # Wireframes, diagrams, exploratory figures
├── notebooks/         # Jupyter notebooks for analysis
├── src/               # Source code
│   ├── extraction/           # Extractores modulares por fuente de datos
│   │   ├── base.py           # BaseExtractor, setup_logging
│   │   ├── opendata.py       # OpenDataBCNExtractor
│   │   ├── idealista.py      # IdealistaExtractor
│   │   ├── portaldades.py    # PortalDadesExtractor
│   │   └── ...               # INE, IDESCAT, Incasol
│   ├── etl/                  # Pipeline ETL y validadores
│   │   ├── pipeline.py       # run_etl() principal
│   │   └── validators.py     # Validación FK, clasificación de fuentes
│   ├── data_processing.py    # Facade de transformaciones
│   ├── database_setup.py     # Schema SQLite y helpers
│   ├── analysis.py           # Funciones analíticas
│   └── app/                  # Dashboard Streamlit modular
└── tests/             # Unit tests
```

## 🚀 Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
```

2. Create (or reuse) the project virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> 💡 Tip: in VS Code/Cursor run `Python: Select Interpreter` and pick `.venv` so notebooks, tests, and the run button always use the same interpreter.

3. (Optional) Set up environment variables for Idealista API:
```bash
# Register at https://developers.idealista.com/ to get API credentials
# Then set environment variables:
export IDEALISTA_API_KEY=your_api_key_here
export IDEALISTA_API_SECRET=your_api_secret_here
```

### 🏠 Interactive Dashboard (The Cockpit)

The project features a modern, modular Streamlit dashboard for visual analysis.

#### Run Locally

```bash
# Opción 1: Usando Makefile (recomendado)
make dashboard

# Opción 2: Comando directo con PYTHONPATH
PYTHONPATH=. streamlit run src/app/main.py
```

#### Run with Docker

```bash
# Build the container
docker build -t barcelona-housing-analytics .

# Run the container
docker run -p 8501:8501 barcelona-housing-analytics
```

Access the dashboard at `http://localhost:8501`.

**Key Features:**
- **Market Cockpit:** Real-time KPIs, Gross Yield Analysis, and YoY Price Variation.
- **Interactive Maps:** Price distribution and Affordability heatmaps (Choropleth).
- **Demographic Deep-dive:** Age structure, migration, and household composition.
- **Data Export:** Download the full cleaned database (SQLite) directly from the sidebar.

### Data Extraction

#### Extract Priority Sources (GeoJSON, Demographics, Income)

```bash
# Extract priority datasets (GeoJSON, extended demographics, income)
python scripts/extract_priority_sources.py

# Extract with verbose logging
python scripts/extract_priority_sources.py --log-level DEBUG
```

#### Extract Idealista Data (Requires API Credentials)

```bash
# Extract both sale and rent offers
python scripts/extract_idealista.py --operation both

# Extract only sale offers
python scripts/extract_idealista.py --operation sale

# Extract only rent offers
python scripts/extract_idealista.py --operation rent

# Extract for specific neighborhoods
python scripts/extract_idealista.py --operation both --barrios "Eixample" "Gràcia"
```

#### Extract All Sources (Legacy)

```bash
# Extract all data from 2015-2025
python scripts/extract_data.py --year-start 2015 --year-end 2025

# Extract from specific sources only
python scripts/extract_data.py --sources opendatabcn ine

# Verbose mode for debugging
python scripts/extract_data.py --verbose
```

Or use the Python module directly:

```python
from src.data_extraction import extract_all_sources

# Extract all sources
data = extract_all_sources(year_start=2015, year_end=2025)

# Extract specific sources
data = extract_all_sources(
    year_start=2020,
    year_end=2024,
    sources=["opendatabcn", "ine"]
)
```

Extracted data is automatically saved in `data/raw/` directory (organized by source in subdirectories).

**Example with custom output directory:**
```bash
python scripts/extract_data.py \
    --year-start 2015 \
    --year-end 2025 \
    --output-dir /custom/path/data
```

### Portal Dades (Habitatge) Scraper

Automate indicator discovery and downloads from Portal Dades (requires Playwright):

```bash
# Install Playwright once
pip install playwright
playwright install

# Scrape IDs + download all indicators (CSV by default)
python scripts/extract_portaldades.py

# Only list indicator IDs (no downloads)
python scripts/extract_portaldades.py --scrape-only

# Limit pagination
python scripts/extract_portaldades.py --max-pages 3
```

Downloaded files live under `data/raw/portaldades/` and the indicator catalog in `data/raw/portaldades/indicadores_habitatge.csv`.

### Data Processing and Loading (ETL)

Transform and load extracted data into a dimensional SQLite database:

```bash
# Process raw data and create/update database.db
python scripts/process_and_load.py \
    --raw-dir data/raw \
    --processed-dir data/processed \
    --log-level INFO
```

This creates `data/processed/database.db` with:
- **dim_barrios**: Neighborhood dimension table (73 barrios with GeoJSON geometries)
- **fact_demografia**: Standard demographic facts (population by year and barrio)
- **fact_demografia_ampliada**: Extended demographics (age groups and nationality by barrio, year, sex)
- **fact_precios**: Housing prices facts (sale and rental prices by year and barrio, deduplicated via `HousingCleaner`)
- **fact_renta**: Income facts (household disposable income by barrio and year)
- **etl_runs**: ETL execution audit log

**Query the database**:
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/processed/database.db')

# Get demographics with barrio names
df = pd.read_sql_query("""
    SELECT d.*, b.barrio_nombre, b.distrito_nombre
    FROM fact_demografia d
    JOIN dim_barrios b ON d.barrio_id = b.barrio_id
    WHERE d.anio = 2023
""", conn)

# Get extended demographics (age groups and nationality)
df_ampliada = pd.read_sql_query("""
    SELECT 
        b.barrio_nombre,
        d.anio,
        d.sexo,
        d.grupo_edad,
        d.nacionalidad,
        d.poblacion
    FROM fact_demografia_ampliada d
    JOIN dim_barrios b ON d.barrio_id = b.barrio_id
    WHERE d.anio = 2025
      AND d.grupo_edad = '18-34'
    ORDER BY d.poblacion DESC
""", conn)

# Get rent data by barrio
df_renta = pd.read_sql_query("""
    SELECT 
        b.barrio_nombre,
        b.distrito_nombre,
        r.anio,
        r.renta_euros,
        r.renta_mediana,
        r.num_secciones
    FROM fact_renta r
    JOIN dim_barrios b ON r.barrio_id = b.barrio_id
    WHERE r.anio = 2022
    ORDER BY r.renta_euros DESC
""", conn)

# Get barrios with geometry (for mapping)
df_geometrias = pd.read_sql_query("""
    SELECT 
        barrio_id,
        barrio_nombre,
        distrito_nombre,
        geometry_json
    FROM dim_barrios
    WHERE geometry_json IS NOT NULL
""", conn)
```

For detailed API usage and configuration, see [docs/API_usage.md](docs/API_usage.md).
For data structure and directory organization, see [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md).
For next steps and development roadmap, see [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md).

## 📋 Issue Management

This project uses a structured workflow for managing GitHub issues.

### Quick Commands (Makefile)

```bash
# Show all available commands
make help

# Validate issue drafts locally
make validate-issues

# Preview issues (dry-run)
make preview-issues

# Create a specific issue
make create-issue FILE=mi-issue.md

# Create all issues from drafts
make create-issues

# Sync metrics with documentation
make sync-issues
```

### Create a New Issue

1. **Create draft** from template:
   ```bash
   cp docs/issues/ejemplo-issue-draft.md docs/issues/mi-nueva-issue.md
   ```

2. **Edit the draft** with your requirements

3. **Validate locally**:
   ```bash
   make validate-issues
   # Or for a specific file:
   python3 scripts/validate_issues.py docs/issues/mi-nueva-issue.md
   ```

4. **Create in GitHub**:
   ```bash
   make create-issue FILE=mi-nueva-issue.md
   ```

### Issue Best Practices

See complete guide: [docs/BEST_PRACTICES_GITHUB_ISSUES.md](docs/BEST_PRACTICES_GITHUB_ISSUES.md)

**Quick checklist:**
- ✅ Descriptive title with type prefix `[FEATURE]`, `[BUG]`, `[DATA]`
- ✅ Clear "Objetivo/Descripción" section
- ✅ Acceptance criteria with checkboxes `- [ ]`
- ✅ Affected files listed
- ✅ Time estimation included
- ✅ Appropriate labels (`bug`, `enhancement`, `etl`, etc.)

### Project Metrics

View current metrics: [docs/PROJECT_METRICS.md](docs/PROJECT_METRICS.md)

Update metrics from GitHub:
```bash
make sync-issues
```

---

## 📚 Documentation

- **[Project Status](docs/PROJECT_STATUS.md)** ⭐ - Current state, achievements, issues, and next steps
- **[Project Metrics](docs/PROJECT_METRICS.md)** 📊 - Issue metrics and KPIs
- **[Best Practices - Issues](docs/BEST_PRACTICES_GITHUB_ISSUES.md)** - Issue creation guidelines
- [Issues to Create](docs/ISSUES_TO_CREATE.md) - GitHub issues ready to be created
- [Vision and Objectives](docs/01_VISION_AND_OBJECTIVES.md) - Project goals and data requirements
- [API Usage Guide](docs/API_usage.md) - How to use data extraction APIs
- [Data Structure](docs/DATA_STRUCTURE.md) - Directory organization and file naming conventions
- [Extraction Improvements](docs/EXTRACTION_IMPROVEMENTS.md) - Advanced features and improvements
- [Project Milestones](docs/PROJECT_MILESTONES.md) - Development roadmap
- [Next Steps](docs/NEXT_STEPS.md) - Immediate action plan and recommendations
- [Debugging Datasets](docs/DEBUGGING_DATASETS.md) - Guide for investigating CKAN datasets
