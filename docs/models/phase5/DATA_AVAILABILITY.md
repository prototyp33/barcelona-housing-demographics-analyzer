# 📊 ESG Data Availability & Configuration

## Current Data Status

### ✅ Available Data by Year

| Metric                | Years Available | Records          | Notes                                     |
| --------------------- | --------------- | ---------------- | ----------------------------------------- |
| **Educación**         | 2025            | 73 neighborhoods | Total centers only (no breakdown by type) |
| **Vivienda Pública**  | 2024            | 73 neighborhoods | Public housing units                      |
| **Seguridad**         | 2020-2024       | 292 records/year | Crime rates per 1000 residents            |
| **Presión Turística** | 2011-2025       | Varies           | Airbnb listings data                      |

### 🎯 Dashboard Configuration

The ESG view now uses **smart data fetching** that automatically selects the most recent available data for each metric:

- **Left Column (Infrastructure)**:
  - Education data: 2025
  - Public housing: 2024 (fallback from 2025)
- **Right Column (Safety & Tourism)**:
  - Crime data: 2024
  - Tourism data: 2025 (fallback from 2024)

## What You'll See Now

### 📚 Infraestructura Social (Left)

**For Year 2025:**

- ✅ **Top 10 Barrios by Educational Centers** (Bar Chart)
  - Shows total_centros_educativos
  - Sorted descending
  - Color gradient: Blues

**Top Neighborhoods:**

1. la Dreta de l'Eixample - 177 centers
2. la Vila de Gràcia - 107 centers
3. Sant Gervasi - la Bonanova - 105 centers
4. Sarrià - 96 centers
5. la Maternitat i Sant Ramon - 90 centers

**For Year 2024:**

- ✅ **Top 10 Barrios by Public Housing** (Bar Chart)
  - Shows viviendas_proteccion_oficial
  - Horizontal orientation
  - Color gradient: GnBu

### 🛡️ Seguridad y Entorno Turístico (Right)

**For Year 2024:**

- ✅ **Crime vs. Tourism Scatter Plot**
  - X-axis: Crime rate (tasa_criminalidad_1000hab)
  - Y-axis: Airbnb listings (num_listings_airbnb)
  - Bubble size: Average nightly price
  - Colors: Districts
  - 292 data points

**Data Coverage:**

- Crime data: 292 records (all districts)
- Tourism data: 370+ records for 2024, 439 for 2025

## Technical Implementation

### Smart Query Logic

The data loaders now use subqueries to fetch the most recent data:

```sql
LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
    AND e.anio = (SELECT MAX(anio) FROM fact_educacion WHERE anio <= ?)
```

This means:

- If you request year 2025, it gets 2025 education data
- If you request year 2024, it gets the latest available (still 2025 for education)
- If you request year 2023, it falls back gracefully

### Fallback Behavior

1. **Data exists for requested year**: Shows that data
2. **Data doesn't exist**: Shows most recent available data ≤ requested year
3. **No data at all**: Shows friendly empty state message

## How to Use

### In the Dashboard:

1. **Navigate to "🌱 Social ESG" tab**
2. **Read the info banner** at the top explaining data years
3. **View both columns** - they now show complementary data
4. **Use district filter** (sidebar) to focus on specific areas
5. **Hover over charts** for detailed neighborhood information

### Expected Behavior:

- **Year selector is now ignored** - dashboard uses optimal years automatically
- **Left column**: Always shows latest infrastructure data
- **Right column**: Always shows latest safety/tourism data
- **Info messages**: Appear when specific metrics aren't available

## Data Quality Notes

### Education Data (2025)

- ✅ All 73 neighborhoods covered
- ⚠️ Only `total_centros_educativos` has values
- ⚠️ Breakdown by type (infantil, primaria, etc.) is all zeros
- **Workaround**: Showing total centers instead of pie chart

### Public Housing (2024)

- ✅ All 73 neighborhoods covered
- ✅ `viviendas_proteccion_oficial` has real values
- **Display**: Top 10 bar chart

### Crime Data (2024)

- ✅ 292 records (4 records per neighborhood on average)
- ✅ `tasa_criminalidad_1000hab` populated
- ✅ Additional fields: delitos_patrimonio, delitos_seguridad_personal

### Tourism Data (2025)

- ✅ 439 records (monthly data aggregated)
- ✅ `num_listings_airbnb` populated
- ✅ `precio_noche_promedio` available
- ⚠️ Some neighborhoods have NaN prices (filled with median)

## Troubleshooting

### "Datos no disponibles" Messages

**If you see this for Infrastructure:**

- Check that year ≥ 2024 (for housing) or ≥ 2025 (for education)
- Verify database has data: `SELECT COUNT(*) FROM fact_educacion;`

**If you see this for Safety:**

- Check that year ≥ 2020 and ≤ 2024
- Verify: `SELECT DISTINCT anio FROM fact_seguridad;`

### Scatter Plot Not Showing

**Common causes:**

1. All `precio_noche_promedio` values are NaN
   - **Fix**: Code now fills with median
2. No crime data for selected year
   - **Fix**: Use year 2024 or earlier
3. District filter too restrictive
   - **Fix**: Select "Todos" in sidebar

### Empty Pie/Bar Charts

**Education pie chart empty:**

- Expected - breakdown data not available
- Shows bar chart instead

**Public housing bar chart empty:**

- Year must be 2024
- Check: `SELECT COUNT(*) FROM fact_vivienda_publica WHERE anio = 2024;`

## Future Enhancements

### Short Term

- [ ] Add year indicators to each chart title
- [ ] Show data freshness timestamps
- [ ] Add download buttons for raw data

### Medium Term

- [ ] Populate education breakdown data
- [ ] Add 2025 crime data when available
- [ ] Create combined multi-year views

### Long Term

- [ ] Implement time-series animations
- [ ] Add predictive models for missing years
- [ ] Create data quality dashboard

---

**Last Updated**: 2026-01-21  
**Dashboard URL**: http://localhost:8501  
**Status**: ✅ Fully Operational
