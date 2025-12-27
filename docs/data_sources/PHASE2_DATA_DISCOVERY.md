# Phase 2 Data Discovery: Education & Environmental Quality

## Executive Summary

Research and validation of data sources for education levels and environmental quality (air pollution and noise) have been completed. These variables are critical for causal analysis of housing prices in Barcelona.

| Component             | Status | Source                 | Granularity     | Coverage           |
| --------------------- | ------ | ---------------------- | --------------- | ------------------ |
| **fact_educacion**    | ✅ GO  | Open Data BCN (Padró)  | Barrio (73)     | 2007-2023          |
| **fact_calidad_aire** | ✅ GO  | ASPB (Open Data BCN)   | 11 Stations     | 2018-2023 (Hourly) |
| **fact_soroll**       | ✅ GO  | Mapa Estratègic Soroll | Polygons/Raster | 2012, 2017, 2022   |

---

## 1. Education (fact_educacion)

### Source Overview

- **Dataset:** [Població de 16 anys i més per titulació acadèmica i sexe](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/pad_mdbas_niv-educa-esta_sexe)
- **Format:** CSV/JSON
- **Granularity:** Barrio-level (via `Codi_Barri`).

### Data Dictionary (`NIV_EDUCA_esta`)

Mapped using the "Dimensions of the Municipal Register of Inhabitants" dataset.

| Code | Catalan Label                                         | English Description                               |
| ---- | ----------------------------------------------------- | ------------------------------------------------- |
| 1    | Sense estudis                                         | Illiterate/No studies                             |
| 2    | Estudis primaris, certificat d'escolaritat, EGB       | Primary education                                 |
| 3    | Batxillerat elemental, graduat escolar, ESO, FPI      | Lower secondary education                         |
| 4    | Batxillerat superior, BUP, COU, FPII, CFGM grau mitjà | Upper secondary education                         |
| 5    | Estudis universitaris, CFGS grau superior             | Tertiary education (University/Higher Vocational) |
| 6    | No consta                                             | Not available                                     |

### Gentrification Proxy Logic

The rate of university-educated population (`Code 5`) will be used as a proxy for gentrification.

---

## 2. Air Quality (fact_calidad_aire)

### Source Overview

- **Dataset:** [Dades de les estacions de mesura de la qualitat de l'aire](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/qualitat-aire-detall-bcn)
- **Sensors:** 11 stations in Barcelona (e.g., Eixample, Gràcia, Poblenou).
- **Temporal Coverage:** 2018-2023 (Hourly data).

### Contaminant Mapping

| Code | Contaminant | Unit  |
| ---- | ----------- | ----- |
| 1    | SO2         | µg/m³ |
| 6    | CO          | mg/m³ |
| 7    | NO          | µg/m³ |
| 8    | NO2         | µg/m³ |
| 9    | PM2.5       | µg/m³ |
| 10   | PM10        | µg/m³ |
| 12   | NOx         | µg/m³ |
| 14   | O3          | µg/m³ |

### Spatial Aggregation Strategy

- **Method:** Inverse Distance Weighting (IDW) interpolation from 11 station centroids to the 73 barrio centroids.
- **Feasibility:** High. Previous spatial analyses show ≥80% coverage with <2km error.

---

## 3. Noise (fact_soroll)

### Source Overview

- **Dataset:** [Mapes de soroll de façanes del Mapa Estratègic de Soroll](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/facanes-mapa-estrategic-soroll)
- **Format:** GeoPackage (`.gpkg`).
- **Years:** 2012, 2017, 2022.

### Aggregation Method

Spatial join between noise source polygons/raster and barrio boundaries to calculate the mean `Lden` (day-evening-night) level per barrio.

---

## Next Steps

1. **Schema Design:** Create `fact_educacion`, `fact_calidad_aire`, and `fact_soroll` tables (Issue #217).
2. **ETL Development:** Implement Python scripts to download, map, and aggregate these sources into the master ABT.
3. **Validation:** Perform spatial join and IDW validation once the raw data is ingested.

> [!IMPORTANT]
> Pre-2018 air quality data requires integration with the Generalitat (XVPCA) API as the municipal portal coverage is limited before that period.
