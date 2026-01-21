# Zero Records Fix Plan - Air Quality & Tourism

## Status: 🔧 IMPLEMENTATION IN PROGRESS

**Issue**: `fact_calidad_aire` and `fact_turismo_intensidad` have 0 records

## Root Causes Identified

### 1. fact_calidad_aire (Air Quality)

**Problem:**
- ✅ Raw data file EXISTS: `opendatabcn_mapes-immissio-qualitat-aire_*.csv` (2.3 MB)
- ❌ Processing script MISSING: No `prepare_calidad_aire.py`
- ❌ ETL integration MISSING: Not processed in pipeline

**Data Format:**
- Raster/map format with TRAM polygons
- Columns: `TRAM`, `Rang` (concentration range), `GEOM_WKT`
- Requires spatial intersection with barrio geometries

**Solution Implemented:**
1. ✅ Created `src/processing/prepare_calidad_aire.py`
   - Parses concentration ranges from `Rang` column
   - Performs spatial intersection with barrio geometries
   - Aggregates to barrio level using weighted average by intersection area
   
2. ✅ Integrated into ETL pipeline (`src/etl/pipeline.py`)
   - Added import and processing call
   - Added table loading step

### 2. fact_turismo_intensidad (Tourism)

**Problem:**
- ❌ Raw data files MISSING
- ❌ Not in manifest.json
- ✅ Processing function EXISTS: `prepare_fact_turismo_intensidad` ready
- ✅ ETL integration EXISTS: Tourism processing in pipeline

**Expected Dataset IDs:**
- `tourism_intensity`: `intensitat-activitat-turistica`
- `tourism_hut`: `habitatges-us-turistic`

**Solution Implemented:**
1. ✅ Created `scripts/extract_tourism_data.py`
   - Extracts tourism datasets from OpenData BCN
   - Verifies dataset IDs are correct
   - Downloads historical data (2015-2025)

## Implementation Status

### ✅ Completed
- [x] Air quality processor created (`src/processing/prepare_calidad_aire.py`)
- [x] Air quality integrated into ETL pipeline
- [x] Tourism extraction script created
- [x] Investigation script created

### 🔄 Next Steps

1. **Test Air Quality Processing:**
   ```bash
   # Run ETL to process existing air quality file
   python scripts/process_and_load.py
   ```

2. **Extract Tourism Data:**
   ```bash
   # Extract missing tourism datasets
   python scripts/extract_tourism_data.py
   ```

3. **Verify Results:**
   ```bash
   # Check record counts
   sqlite3 data/processed/database.db "SELECT COUNT(*) FROM fact_calidad_aire;"
   sqlite3 data/processed/database.db "SELECT COUNT(*) FROM fact_turismo_intensidad;"
   ```

## Files Created/Modified

1. **`src/processing/prepare_calidad_aire.py`** (NEW)
   - Processes raster/map air quality data
   - Spatial aggregation to barrio level

2. **`src/etl/pipeline.py`** (MODIFIED)
   - Added air quality processing step
   - Added `fact_calidad_aire` table loading

3. **`scripts/extract_tourism_data.py`** (NEW)
   - Extracts tourism datasets from OpenData BCN
   - Verifies dataset IDs

4. **`scripts/investigate_zero_records.py`** (NEW)
   - Diagnostic script for zero record issues

## Testing

After running the ETL, verify:
```sql
-- Should return > 0
SELECT COUNT(*) FROM fact_calidad_aire;
SELECT COUNT(*) FROM fact_turismo_intensidad;
```

## Notes

- Air quality data is in raster format (TRAM polygons) - requires geopandas
- Tourism data needs to be extracted first before ETL can process it
- Both datasets are optional for the dashboard but important for Social Impact view
