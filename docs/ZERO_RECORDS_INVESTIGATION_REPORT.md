# Zero Records Investigation Report

## Status: 🔍 ROOT CAUSE IDENTIFIED

**Issue**: `fact_calidad_aire` and `fact_turismo_intensidad` have 0 records, blocking Social Impact dashboard.

## Investigation Results

### 1. fact_calidad_aire (Air Quality)

**Root Causes:**
- ✅ Raw data file EXISTS: `opendatabcn_mapes-immissio-qualitat-aire_*.csv` (2.3 MB)
- ❌ Processing script MISSING: `src/processing/prepare_calidad_aire.py` does not exist
- ❌ ETL integration MISSING: Air quality not processed in `src/etl/pipeline.py`
- ⚠️  Data format: Raster/map format (TRAM, Rang, GEOM_WKT) - requires spatial processing

**File Structure:**
```
TRAM,Rang,GEOM_WKT
T04719W,20-30 µg/m³,"MultiLineString (...)"
```

**Required Actions:**
1. Create `src/processing/prepare_calidad_aire.py` to:
   - Parse raster data (TRAM polygons with concentration ranges)
   - Intersect with barrio geometries
   - Aggregate to barrio level (average concentration per barrio)
   - Transform to `fact_calidad_aire` format

2. Integrate into ETL pipeline:
   - Add air quality processing step in `src/etl/pipeline.py`
   - Load into `fact_calidad_aire` table

### 2. fact_turismo_intensidad (Tourism)

**Root Causes:**
- ❌ Raw data files MISSING: No files found for dataset IDs:
  - `intensitat-activitat-turistica`
  - `habitatges-us-turistic`
- ❌ Not in manifest.json: Datasets not registered
- ✅ Processing function EXISTS: `prepare_fact_turismo_intensidad` is ready
- ✅ ETL integration EXISTS: Tourism processing is in pipeline

**Required Actions:**
1. Extract tourism data:
   - Run OpenDataBCNExtractor for `tourism_intensity` dataset
   - Run OpenDataBCNExtractor for `tourism_hut` dataset
   - Verify dataset IDs are correct (may have changed)

2. Verify dataset IDs:
   - Check if `intensitat-activitat-turistica` and `habitatges-us-turistic` are valid
   - Search OpenData BCN API for correct IDs if needed

## Priority Actions

### P0 - Immediate (Blocking Dashboard)
1. **Create air quality processor** - Process existing raster file
2. **Integrate air quality into ETL** - Add to pipeline
3. **Extract tourism data** - Run extraction for missing datasets

### P1 - Follow-up
4. Verify dataset IDs for tourism (may need API search)
5. Add data quality checks for both tables

## Next Steps

See implementation scripts:
- `scripts/create_air_quality_processor.py` - Creates processing script
- `scripts/extract_tourism_data.py` - Extracts missing tourism data
- `scripts/integrate_air_quality_etl.py` - Adds to ETL pipeline
