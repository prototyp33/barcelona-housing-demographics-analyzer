# Consolidative Visualization Summary

This document provides an overview of the visualizations consolidated into the `visualizations/` folder.

## 📊 Summary of Consolidation

- **Total Visualizations**: 100+
- **Source**: Notebook outputs (71), `reports/` folder, `spike-data-validation/` results.
- **Key Updates**: Re-ran exploratory notebooks to reflect the current database state (~100,000+ records).

## 📂 Folder Structure

All visualizations are now located in:
`[visualizations/](file:///Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/visualizations/)`

## 🎨 Key Visualization Categories

### 1. Exploratory Data Analysis (EDA)

- **Price Distributions**: `01_exploratory_data_analysis_3_an_lisis_de_precios_a_id_3_precios_a_9_1.png`
- **Demographic Overview**: `01_exploratory_data_analysis_4_an_lisis_demogr_fico_a_id_4_demografia_a_15_0.png`
- **Correlations**: `01_exploratory_data_analysis_7_correlaciones_a_id_7_correlaciones_a_26_0.png`

### 2. Geospatial Analysis

- **Price Maps**: `02_geospatial_analysis_2_mapas_de_precios_a_id_2_precios_a_7_0.png`
- **Tourist Pressure**: `02_geospatial_analysis_5_mapas_de_turismo_a_id_5_turismo_a_17_0.png`

### 3. Time Series & Trends

- **Price Evolution**: `03_time_series_analysis_2_an_lisis_de_tendencias_a_id_2_tendencias_a_7_0.png`
- **COVID-19 Impact**: `03_time_series_analysis_7_impacto_covid_19_a_id_7_covid_a_19_0.png`

### 4. Advanced Analytics

- **Gentrification Risk**: `04_gentrification_analysis_6_barrios_en_riesgo_a_id_6_riesgo_a_17_0.png`
- **Investment Opportunity Mapper**: `04_Investment_Opportunity_Mapper` (Available images in folder)
- **Neighborhood Clustering**: `02_neighborhood_clustering_nivel_senior_real_estate_analytics_dynamic_modeling_4_0.png`

## 🛠️ Automated Extraction Script

The consolidation was performed using the following scripts:

- `scripts/extract_visualizations.py`: Extracts embedded PNGs from `.ipynb` files.
- `scripts/move_visualizations.py`: Collects static images from various project subdirectories.

---

_Generated on: 2026-01-19_
