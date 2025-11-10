# API Usage Guide

## External APIs and Ethical Scraping

This document provides guidelines for using external APIs and web scraping practices with the data extraction module.

## Quick Start

### Basic Usage

```python
from src.data_extraction import extract_all_sources

# Extraer datos de todas las fuentes (2015-2025)
data = extract_all_sources(year_start=2015, year_end=2025)

# Extraer solo de fuentes específicas
data = extract_all_sources(
    year_start=2020,
    year_end=2024,
    sources=["opendatabcn", "ine"]
)
```

### Individual Extractors

```python
from src.data_extraction import INEExtractor, OpenDataBCNExtractor, IdealistaExtractor

# INE
ine = INEExtractor()
demographics = ine.get_demographic_data(2015, 2025)

# Open Data BCN
bcn = OpenDataBCNExtractor()
demographics_bcn = bcn.get_demographics_by_neighborhood(2015, 2025)
housing_bcn = bcn.get_housing_data_by_neighborhood(2015, 2025)

# Idealista (requiere API key)
idealista = IdealistaExtractor(api_key="your_api_key")
prices = idealista.get_housing_prices_by_neighborhood("Eixample", "sale")
```

## APIs Details

### INE (Instituto Nacional de Estadística)

**Description**: Official Spanish statistics institute providing demographic and census data.

**Usage**:
- Access via web interface: https://www.ine.es/
- API REST: https://servicios.ine.es/wstempus/js/es/
- Data format: CSV, Excel, JSON

**Rate Limits**:
- Default: 2 seconds between requests
- No official API key required for public data
- Respect server load, avoid aggressive scraping

**Example**:
```python
from src.data_extraction import INEExtractor

extractor = INEExtractor(rate_limit_delay=2.0)
data = extractor.get_demographic_data(year_start=2015, year_end=2025)
```

**Available Data**:
- Population by municipality
- Demographics by age and sex
- Births and deaths
- Migration data
- Housing statistics

### Barcelona Open Data

**Description**: Barcelona city open data portal using CKAN API.

**Usage**:
- Base URL: https://opendata-ajuntament.barcelona.cat/
- API URL: https://opendata-ajuntament.barcelona.cat/data/api/3/action
- Data format: CSV, JSON, XLSX

**Rate Limits**:
- Default: 1.5 seconds between requests
- No API key required
- Public datasets available

**Example**:
```python
from src.data_extraction import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()

# List available datasets
datasets = extractor.get_dataset_list()

# Get dataset info
info = extractor.get_dataset_info("demografia-per-barris")

# Download dataset
data = extractor.download_dataset(
    "demografia-per-barris",
    resource_format="csv",
    year_start=2015,
    year_end=2025
)
```

**Available Datasets** (IDs CKAN confirmados):
- `pad_mdbas_sexe`: Población por sexo y barrio
- `est-padro-edat-any-a-any`: Población por edad
- `habitatges-2na-ma`: Precios de venta (confirmado)
- `est-mercat-immobiliari-lloguer-mitja-mensual`: Precios de alquiler

**Nuevos Métodos Disponibles**:
```python
from src.data_extraction import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()

# Extraer datos demográficos (con IDs correctos)
df_demo, metadata = extractor.extract_demographics_ckan(2015, 2025)

# Extraer precios de venta
df_venta, metadata = extractor.extract_housing_venta(2015, 2025)

# Extraer precios de alquiler
df_alquiler, metadata = extractor.extract_housing_alquiler(2015, 2025)
```

**Finding Datasets**:
```python
# List all available datasets
extractor = OpenDataBCNExtractor()
all_datasets = extractor.get_dataset_list()

# Search for specific dataset
for dataset_id in all_datasets:
    info = extractor.get_dataset_info(dataset_id)
    if "vivienda" in info.get('title', '').lower():
        print(f"Found: {dataset_id} - {info.get('title')}")
```

### Idealista

**Description**: Real estate platform with housing prices and listings.

**Usage**:
- Official API: https://developers.idealista.com/ (requires registration)
- API URL: https://api.idealista.com/3.5
- Data format: JSON

**Rate Limits**:
- Default: 3 seconds between requests (ethical scraping)
- Official API: Rate limits defined by API plan
- **Important**: Always use official API when available

**API Key Setup**:
1. Register at https://developers.idealista.com/
2. Create an application to get API credentials
3. Set environment variable: `export IDEALISTA_API_KEY=your_key`
4. Or pass directly: `IdealistaExtractor(api_key="your_key")`

**Example**:
```python
import os
from src.data_extraction import IdealistaExtractor

# Using environment variable
extractor = IdealistaExtractor()

# Or with explicit API key
extractor = IdealistaExtractor(api_key=os.getenv("IDEALISTA_API_KEY"))

# Get housing prices (requires API implementation)
prices = extractor.get_housing_prices_by_neighborhood(
    neighborhood="Eixample",
    operation="sale",  # or "rent"
    year_start=2020,
    year_end=2024
)
```

**Ethical Considerations**:
1. **Always prefer official API** over web scraping
2. Respect robots.txt: https://www.idealista.com/robots.txt
3. Implement rate limiting (minimum 3 seconds between requests)
4. Use appropriate User-Agent headers
5. Don't overload servers with excessive requests
6. Cache data appropriately to avoid redundant requests
7. Follow Idealista's Terms of Service

**Alternative Data Sources**:
- Idealista/data: https://www.idealista.com/data/ (public reports)
- Download public reports instead of scraping listings

## Ethical Scraping Guidelines

### General Principles

1. **Respect robots.txt**: Always check and follow robots.txt files
2. **Implement rate limiting**: Minimum delays between requests
3. **Use official APIs**: Prefer APIs over scraping when available
4. **Follow terms of service**: Read and comply with ToS
5. **Cache data appropriately**: Avoid redundant requests
6. **Use proper headers**: Identify your bot with User-Agent
7. **Handle errors gracefully**: Don't retry excessively on errors

### Rate Limiting Best Practices

```python
# Recommended delays:
INE_RATE_LIMIT = 2.0  # seconds
OPENDATABCN_RATE_LIMIT = 1.5  # seconds
IDEALISTA_RATE_LIMIT = 3.0  # seconds (more conservative)
```

### Error Handling

The extraction module includes:
- Automatic retry with exponential backoff
- Rate limit detection and handling
- Comprehensive logging
- Graceful degradation on errors

## Data Storage

All extracted data is automatically saved in `data/raw/` directory:

```
data/raw/
├── ine/
│   └── ine_demographics_2015_2025_20250101_120000.csv
├── opendatabcn/
│   ├── opendatabcn_demografia-per-barris_20250101_120000.csv
│   └── opendatabcn_habitatge-per-barris_20250101_120000.csv
└── idealista/
    └── idealista_report_20250101.pdf
```

## Configuration

### Environment Variables

Create a `.env` file (or set environment variables):

```bash
# Idealista API Key (optional)
IDEALISTA_API_KEY=your_api_key_here

# Extraction settings
EXTRACTION_YEAR_START=2015
EXTRACTION_YEAR_END=2025
```

### Custom Rate Limits

```python
# Adjust rate limits per extractor
ine = INEExtractor(rate_limit_delay=2.0)
bcn = OpenDataBCNExtractor(rate_limit_delay=1.5)
idealista = IdealistaExtractor(rate_limit_delay=3.0)
```

## Troubleshooting

### Common Issues

1. **Rate Limit Errors (429)**
   - Increase `rate_limit_delay` parameter
   - Wait longer between extraction runs

2. **Connection Timeouts**
   - Check internet connection
   - Verify API endpoints are accessible
   - Increase timeout values if needed

3. **Missing Data**
   - Verify dataset IDs are correct
   - Check date ranges are valid
   - Review logs for specific errors

4. **API Key Issues (Idealista)**
   - Verify API key is valid
   - Check API key has required permissions
   - Review API documentation for changes

### Logging

The module uses Python's logging framework. To adjust log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # More verbose
```

## Best Practices

1. **Run extractions during off-peak hours** when possible
2. **Store raw data** before processing to avoid re-extraction
3. **Version control** extraction scripts, not raw data
4. **Monitor extraction logs** for errors and warnings
5. **Test with small date ranges** before full extraction
6. **Document any custom configurations** or workarounds
7. **Respect data source policies** and update scripts if APIs change

