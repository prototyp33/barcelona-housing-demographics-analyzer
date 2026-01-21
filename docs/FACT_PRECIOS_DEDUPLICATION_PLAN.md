# fact_precios Deduplication Plan

## Problem Statement

The `fact_precios` table contains duplicate records that violate the intended uniqueness constraint. This causes:
- **Artificial narrowing of confidence intervals** in forecast models
- **Incorrect aggregations** when calculating averages
- **Data quality issues** when multiple sources report different values for the same barrio/year

Current state: ~6,358 records, but many are duplicates of the same (barrio_id, anio) combination.

## Root Cause

The unique index on `fact_precios` is:
```sql
CREATE UNIQUE INDEX idx_fact_precios_unique
ON fact_precios (
    barrio_id,
    anio,
    COALESCE(trimestre, -1),
    COALESCE(dataset_id, ''),
    COALESCE(source, '')
);
```

However, duplicates can occur when:
1. **Same barrio_id + anio** but different `dataset_id` or `source` (intended for multi-source data)
2. **Same barrio_id + anio** but one has NULL `trimestre` and another has a value
3. **ETL pipeline** loads data multiple times without proper deduplication
4. **Multiple sources** report the same indicator for the same barrio/year

## Investigation Tools

### 1. SQL Investigation Query
Run `scripts/investigate_fact_precios_duplicates.sql` to analyze duplicate patterns:

```bash
sqlite3 data/processed/database.db < scripts/investigate_fact_precios_duplicates.sql
```

Or use the shell script:
```bash
./scripts/run_duplicate_investigation.sh
```

### 2. Python Analysis Script
For interactive analysis and cleanup:

```bash
# Analyze only (safe, read-only)
python3 scripts/analyze_and_clean_duplicates.py

# Preview deletions
python3 scripts/analyze_and_clean_duplicates.py --preview 50

# Actually clean (creates backup first)
python3 scripts/analyze_and_clean_duplicates.py --clean
```

## Cleanup Strategy

### Option 1: Keep Most Recent (Recommended)
Keep the most recent record per (barrio_id, anio) based on `etl_loaded_at` timestamp.

**Pros:**
- Preserves latest data
- Simple and deterministic
- Works well for ETL re-runs

**Cons:**
- May lose valuable historical data from different sources
- Doesn't handle cases where different sources have different values

### Option 2: Keep Best Source
Prioritize sources in order: Idealista > Portal de Dades > Open Data BCN

**Pros:**
- Preserves data quality hierarchy
- Handles multi-source scenarios

**Cons:**
- More complex logic
- Requires source priority definition

### Option 3: Aggregate Values
For duplicates with same (barrio_id, anio), aggregate price values (AVG, MAX, etc.)

**Pros:**
- Preserves all information
- Good for forecasting (uses all available data)

**Cons:**
- May mask data quality issues
- Aggregation method needs careful consideration

## Recommended Approach

**For immediate cleanup:** Use Option 1 (Keep Most Recent) via the cleanup script.

**For long-term:** Modify ETL pipeline to:
1. Use `INSERT OR REPLACE` with proper unique constraint
2. Implement source priority logic
3. Add validation to prevent duplicates during load

## Implementation

### Step 1: Investigate
```bash
python3 scripts/analyze_and_clean_duplicates.py
```

Review the output to understand:
- How many duplicate groups exist
- Which sources are creating duplicates
- Whether price values conflict

### Step 2: Preview Deletions
```bash
python3 scripts/analyze_and_clean_duplicates.py --preview 50
```

Review which records would be deleted.

### Step 3: Clean (with backup)
```bash
python3 scripts/analyze_and_clean_duplicates.py --clean
```

This will:
1. Create a backup table (`fact_precios_backup_YYYYMMDD_HHMMSS`)
2. Delete duplicate records (keeping most recent)
3. Verify no duplicates remain

### Step 4: Verify
```sql
-- Should return 0 rows
SELECT barrio_id, anio, COUNT(*) as count
FROM fact_precios
GROUP BY barrio_id, anio
HAVING COUNT(*) > 1;
```

## Code Changes

### Updated `get_prices()` Function
The `src/analysis.py` function now includes deduplication logic in the SQL query using `ROW_NUMBER()` to select the most recent record per (barrio_id, anio).

This ensures that even if duplicates exist in the database, the analysis functions return clean data.

## Prevention

To prevent future duplicates:

1. **ETL Pipeline:** Modify `src/etl/transformations/market.py` to use `INSERT OR REPLACE` instead of `INSERT`
2. **Unique Constraint:** Ensure the unique index is properly enforced
3. **Validation:** Add checks in `src/etl/validators.py` to detect duplicates before load
4. **Monitoring:** Add data quality checks to detect duplicates in production

## Related Issues

- GitHub Issue #1: "Fix: Deduplicación agresiva en fact_precios" (from `docs/ISSUES_TO_CREATE.md`)
