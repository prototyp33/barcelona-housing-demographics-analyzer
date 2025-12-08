# Streamlit Design & Data Architecture

This file documents the design-phase decisions and data strategies for the Barcelona Housing Demographics Analyzer.

## Data Strategy

We use a hybrid approach of **Real Data** and **Mock Data** to ensure the application is functional and testable even when some API credentials are missing.

### 1. Real Data
*   **Sources**: Open Data BCN, Idescat.
*   **Storage**: SQLite (`data/processed/database.db`).
*   **Key Datasets**:
    *   **Housing Prices**: `fact_precios` (2012-2025).
    *   **Demographics**: `fact_demografia` (2015-2023).
    *   **Income**: `fact_renta` (2022-2023). 2022 data was manually backfilled using `scripts/load_renta_2022.py`.

### 2. Mock Data
*   **Context**: Used for features where API keys are sensitive or missing (e.g., Idealista Real-time API).
*   **Dataset**: `fact_oferta_idealista`.
*   **Generator**: `scripts/generate_mock_idealista.py`.
    *   Generates ~1,900 records.
    *   Covers "sale" and "rent" operations.
    *   Simulates realistic price variations by district.
*   **Regeneration**: Run the script to wipe and recreate mock entries.

## Development Workflow

### Branching
*   **Feature Branches**: `feat/<feature-name>`
*   **Spikes/Prototypes**: `spike/<topic>`

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run src/app/main.py
```

### Data Availability Check
To verify the state of the database (real vs mock coverage):
```bash
python scripts/audit_data_availability.py
```

## UI/UX Guidelines
*   **Framework**: Streamlit.
*   **Styling**: Custom CSS injected via `src/app/styles.py`.
*   **Components**: Reusable widgets in `src/app/components.py` (Cards, KPIs, Breadcrumbs).
*   **Loading States**: Use `render_skeleton_kpi` instead of generic spinners for key metrics.
