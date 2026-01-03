# 🔍 Database Investigation Report

**Date:** 2026-01-03  
**Database:** `data/processed/database.db`  
**Investigation:** fact_demografia table status

---

## 📊 Current Database State

### Table Row Counts

| Table                      | Rows  | Status             |
| :------------------------- | :---- | :----------------- |
| `dim_barrios`              | 73    | ✅ Complete        |
| `fact_precios`             | 6,358 | ✅ Populated       |
| `fact_renta`               | 73    | ✅ Populated       |
| `fact_movilidad`           | 73    | ✅ Populated (NEW) |
| `fact_demografia`          | **0** | ⚠️ **EMPTY**       |
| `fact_demografia_ampliada` | 2,256 | ✅ Populated       |

### Demographic Data Breakdown

**fact_demografia_ampliada:**

- **Year:** 2025 only
- **Barrios:** 73 (100% coverage)
- **Records:** 2,256 (granular by age group, sex, nationality)
- **Source:** opendatabcn (pad_mdb_lloc-naix-continent_edat-q_sexe)
- **Last ETL:** 2025-12-28 17:21:19

**Sample Record:**

```
barrio_id: 1 (El Raval)
anio: 2025
sexo: hombre
grupo_edad: 18-34
nacionalidad: América
poblacion: 1,861
```

---

## 🔍 Root Cause Analysis

### Why is `fact_demografia` empty?

The ETL pipeline (`src/etl/pipeline.py` lines 1024-1040) uses **mutually exclusive logic**:

```python
if fact_demografia_ampliada is not None:
    # Load ampliada version
    insert_dataframe_in_batches(fact_demografia_ampliada, ...)
elif fact_demografia is not None:
    # Load standard version (THIS NEVER EXECUTES)
    insert_dataframe_in_batches(fact_demografia, ...)
```

**Conclusion:** The pipeline prioritizes the granular `fact_demografia_ampliada` table over the aggregated `fact_demografia` table. This is **by design**, not a bug.

---

## 🎯 Impact on Current Work

### Fairness A/B Harness

The harness script (`scripts/fairness_ab_harness.py`) originally tried to use:

- `poblacion_total` (from `fact_demografia`)
- `densidad_hab_km2` (from `fact_demografia`)

**Current workaround:** We simplified the baseline to use only `renta_mediana` since `fact_demografia` is empty.

### Options to Fix

**Option 1: Aggregate from ampliada (RECOMMENDED)**
Create a view or materialized aggregation:

```sql
CREATE VIEW fact_demografia_aggregated AS
SELECT
    barrio_id,
    anio,
    SUM(poblacion) as poblacion_total,
    SUM(CASE WHEN sexo = 'hombre' THEN poblacion ELSE 0 END) as poblacion_hombres,
    SUM(CASE WHEN sexo = 'mujer' THEN poblacion ELSE 0 END) as poblacion_mujeres
FROM fact_demografia_ampliada
GROUP BY barrio_id, anio;
```

**Option 2: Populate fact_demografia from ampliada**
Add a post-processing step in the ETL to aggregate ampliada → demografia.

**Option 3: Update harness to use ampliada directly**
Modify the A/B test to aggregate on-the-fly.

---

## 📋 Recommended Actions

### Immediate (Before merging PRs)

1. ✅ **Document this behavior** - Users should know that `fact_demografia` is intentionally empty
2. ⏳ **Create aggregation view** - Add to `database_views.py`
3. ⏳ **Update A/B harness** - Use the new view for demographic features

### Short-term (Next Sprint)

1. **Add to ETL pipeline:** Automatically populate `fact_demografia` from `ampliada` after loading
2. **Update documentation:** Clarify the relationship between the two tables
3. **Add validation:** Ensure both tables stay in sync

---

## 🗂️ Database Files Found

| File                         | Size   | Last Modified | Purpose                      |
| :--------------------------- | :----- | :------------ | :--------------------------- |
| `data/processed/database.db` | N/A    | Current       | **Primary DB** (used by ETL) |
| `data/database.db`           | 432 KB | 2025-12-28    | Legacy/backup                |
| `data/master.db`             | 3.7 MB | 2025-12-28    | Consolidated DB              |
| `data/master_backup_*.db`    | 400 KB | 2025-12-28    | Backup                       |

**Note:** All databases show `fact_demografia` as empty (0 rows).

---

## ✅ Conclusion

The `fact_demografia` table is **intentionally empty** because the ETL pipeline uses the more granular `fact_demografia_ampliada` table instead. This is not a bug, but it does require:

1. Creating an aggregation view for compatibility
2. Updating scripts that expect aggregated demographic data
3. Documenting this design decision

The current A/B harness works around this by using a simpler baseline (income only), but we should add demographic features back once we create the aggregation view.
