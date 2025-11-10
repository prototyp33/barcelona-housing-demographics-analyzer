# Barcelona Housing Demographics Analyzer

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

## 📁 Project Structure

```
barcelona-housing-demographics-analyzer/
├── data/
│   ├── raw/           # Raw data from sources
│   └── processed/     # Cleaned and normalized data
├── docs/              # Documentation
├── notebooks/         # Jupyter notebooks for analysis
├── src/               # Source code
│   ├── data_extraction.py    # Data extraction from sources
│   ├── data_processing.py    # Data cleaning and normalization
│   ├── database_setup.py     # Database schema and setup
│   ├── analysis.py           # Analytical functions
│   └── app.py                # Streamlit dashboard
└── tests/             # Unit tests
```

## 🚀 Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
```bash
# Create .env file for API keys
export IDEALISTA_API_KEY=your_api_key_here  # Optional, for Idealista data
```

### Data Extraction

Extract data from all sources (INE, Open Data BCN, Idealista):

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

For detailed API usage and configuration, see [docs/API_usage.md](docs/API_usage.md).
For data structure and directory organization, see [docs/DATA_STRUCTURE.md](docs/DATA_STRUCTURE.md).

## 📚 Documentation

- [Vision and Objectives](docs/01_VISION_AND_OBJECTIVES.md) - Project goals and data requirements
- [API Usage Guide](docs/API_usage.md) - How to use data extraction APIs
- [Data Structure](docs/DATA_STRUCTURE.md) - Directory organization and file naming conventions
- [Extraction Improvements](docs/EXTRACTION_IMPROVEMENTS.md) - Advanced features and improvements
- [Project Milestones](docs/PROJECT_MILESTONES.md) - Development roadmap
