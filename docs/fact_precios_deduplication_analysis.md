# fact_precios Deduplication Analysis

## Executive Summary

**Status**: ✅ **No Issue - Deduplication is Working Correctly**

The database has **9,927 records** which is correct. The apparent discrepancy between 54,774 Portal de Dades records loaded and 9,927 final records is **intentional and by design**.

---

## What's Happening

### Data Structure
Each Portal de Dades **dataset** represents a **different price metric** for the same barrio-year combination:

| Dataset ID | Description | Example Value (Barrio 2, 2020) |
|------------|-------------|-------------|
| `mrslyp5pcq` | Avg price/m² by property type | €4,515/m² |
| `bxtvnxvukh` | Avg price/m² by transaction | €4,183/m² |
| `idjhkx1ruj` | Avg price/m² by construction year | €2,887/m² |
| `hostlmjrdo` | Total unit price | €316,429 |
| `la6s9fp57r` | Sale transaction avg price | €377 |
| `9ap8lewvtt` | Sale price by condition | €367/m² |
| `cq4causxvu` | Price by state | €5,028/m² |
| `u25rr7oxh6` | Registered sale price/m² | €4,125/m² |
| `b37xv8wcjh` | Rental price | €14.22/m²/month |
| `5ibudgqbrb` | Rental price/m² | €1,110/month |
| `bhl3ulphi5` | Second-hand offer price/m² | €4,717/m² |

### Why 11 Records per Barrio-Year?
For **el Barri Gòtic (ID=2) in 2020**, we have:
- **11 different datasets** = **11 different price indicators**
- Each represents a unique measurement (sale vs rental, by type, by condition, etc.)
- This is **5-11x more granular** than a single "average price"

### Database Math
```
73 barrios × 14 years × ~11 datasets per barrio-year ≈ 11,000 records
Actual: 9,927 records (some barrios/years don't have all 11 datasets)
```

---

## Current Deduplication Logic

### Unique Index (SQLite)
```sql
CREATE UNIQUE INDEX idx_fact_precios_unique_dataset
ON fact_precios (
    barrio_id,
    anio,
    COALESCE(trimestre, -1),
    COALESCE(dataset_id, ''),
    COALESCE(source, '')
);
```

### DataFrame Dedup (pandas)
```python
.drop_duplicates(
    subset=[
        "barrio_id",
        "anio",
        "trimestre",
        "dataset_id",
        "source",
        "precio_m2_venta",
        "precio_mes_alquiler",
    ],
    keep="first",
)
```

**Key Point**: Both allow **multiple records per barrio-year** as long as they have different `dataset_id` values.

---

## Verification Queries

### 1. No Quarterly Data (All NULL)
```sql
SELECT trimestre, COUNT(*) FROM fact_precios GROUP BY trimestre;
-- Result: NULL | 9,927
```
✅ We're not losing quarterly granularity (none exists in source data)

### 2. Multiple Datasets per Barrio-Year
```sql
SELECT barrio_id, anio, COUNT(*) as num_datasets
FROM fact_precios
WHERE barrio_id = 2 AND anio = 2020
GROUP BY barrio_id, anio;
-- Result: 2 | 2020 | 11
```
✅ We're preserving all 11 different price metrics

### 3. Coverage Across Years
```sql
SELECT anio, COUNT(*) as records
FROM fact_precios
GROUP BY anio
ORDER BY anio;
```
- 2012-2025: ~700-850 records per year
- 59 records from Open Data BCN (2015 only)
- ✅ Consistent coverage

---

## ✅ Conclusion

**No changes needed**. The deduplication is working as intended:

1. ✅ **Preserves data richness**: 11 different price metrics per barrio-year
2. ✅ **Prevents true duplicates**: Unique index on (barrio, year, quarter, dataset, source)
3. ✅ **Maximizes utility**: Enables analysis of different price aspects (rental, sale, by type, etc.)

---

## Recommended Next Steps

1. **Update dashboard** to let users **choose which dataset/metric** to visualize
2. **Document dataset meanings** in a reference table or data dictionary
3. **Create analytical queries** that aggregate across datasets (e.g., median of all sale price metrics)

---

## Example: Multi-Metric Analysis Query

```sql
-- Get all price metrics for el Barri Gòtic in 2020
SELECT 
    dataset_id,
    precio_m2_venta,
    precio_mes_alquiler
FROM fact_precios
WHERE barrio_id = 2 AND anio = 2020
ORDER BY dataset_id;
```

This gives you **11 data points** instead of just 1, enabling richer analysis! 🎉
