# Proceso de Interpolación de Renta Quarterly

**Fecha**: 2025-12-14  
**Script**: `scripts/export_socioeconomics_renta.py`  
**Función**: `interpolate_to_quarters()`

---

## 📋 Resumen

La renta familiar disponible en `fact_renta` tiene granularidad **anual** (2015-2023), mientras que los precios oficiales tienen granularidad **quarterly** (Q1-Q4). Para alinear ambos datasets y calcular métricas de affordability, se aplica una interpolación **forward-fill** que replica el valor anual en los 4 trimestres del año.

---

## 🔄 Estrategia de Interpolación

### Método: Forward-Fill (Repetición)

**Algoritmo:**
1. Para cada registro anual en `fact_renta`:
   - Se crean 4 registros quarterly (Q1, Q2, Q3, Q4)
   - Cada registro quarterly recibe el mismo valor de renta del año correspondiente
   - Se mantienen todas las métricas: `renta_annual`, `renta_min`, `renta_max`

**Ejemplo:**
```
Input (fact_renta):
  barrio_id=1, year=2015, renta_annual=11834.9

Output (quarterly):
  barrio_id=1, year=2015, quarter=Q1, renta_annual=11834.9
  barrio_id=1, year=2015, quarter=Q2, renta_annual=11834.9
  barrio_id=1, year=2015, quarter=Q3, renta_annual=11834.9
  barrio_id=1, year=2015, quarter=Q4, renta_annual=11834.9
```

---

## 📊 Implementación

### Código (simplificado)

```python
def interpolate_to_quarters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interpolate annual income data to quarterly using forward-fill.
    
    Strategy: Each year's income value is repeated for all 4 quarters.
    """
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    
    quarterly_records = []
    for _, row in df.iterrows():
        for quarter in quarters:
            quarterly_records.append({
                'barrio_id': row['barrio_id'],
                'barrio_nombre': row['barrio_nombre'],
                'year': row['year'],
                'quarter': quarter,
                'period': f"{row['year']}{quarter}",
                'renta_annual': row['renta_annual'],
                'renta_min': row['renta_min'],
                'renta_max': row['renta_max'],
                'source': row['source']
            })
    
    return pd.DataFrame(quarterly_records)
```

**Ubicación completa**: `scripts/export_socioeconomics_renta.py:58-89`

---

## ⚠️ Limitaciones y Consideraciones

### 1. **No Captura Variación Intra-Anual**
- ❌ La renta puede variar dentro del año, pero la interpolación asume constante
- ⚠️ Para análisis de corto plazo (quarterly), puede introducir sesgo

### 2. **Sin Extrapolación Temporal**
- ❌ Si faltan datos de un año, no se interpola desde años anteriores/posteriores
- ⚠️ Solo se replica el valor del año correspondiente

### 3. **Alineación con Precios**
- ✅ Permite calcular affordability metrics quarterly
- ✅ Mantiene consistencia temporal con precios

### 4. **Fuente de Datos**
- **Origen**: `fact_renta` (IDESCAT)
- **Granularidad original**: Anual
- **Período**: 2015-2023
- **Métricas**: `renta_annual`, `renta_min`, `renta_max`

---

## 📈 Impacto en Métricas de Affordability

Las métricas de affordability calculadas en el Master Table dependen de esta interpolación:

1. **`price_to_income_ratio`**: Precio de vivienda / Renta anual
   - ✅ Aceptable: ratio anual dividido por trimestre
   - ⚠️ Asume renta constante durante el año

2. **`rent_burden_pct`**: (Alquiler mensual × 12) / Renta anual × 100
   - ✅ Aceptable: alquiler quarterly vs renta anual
   - ⚠️ No captura variación estacional

3. **`affordability_index`**: Índice compuesto
   - ⚠️ Puede tener sesgo si la renta varía intra-anual

4. **`affordability_ratio`**: Ratio normalizado
   - ⚠️ Mismo sesgo potencial

---

## ✅ Validación

### Cobertura Temporal

| Año | Registros Anuales | Registros Quarterly | Multiplicador |
|-----|-------------------|---------------------|---------------|
| 2015 | 73 barrios | 292 (73 × 4) | 4.0x |
| 2016 | 73 barrios | 292 (73 × 4) | 4.0x |
| ... | ... | ... | ... |
| 2023 | 73 barrios | 292 (73 × 4) | 4.0x |

**Total esperado**: 73 barrios × 9 años × 4 quarters = **2,628 registros quarterly**

### Verificación en Master Table

```sql
SELECT 
    year,
    COUNT(DISTINCT barrio_id) as barrios,
    COUNT(*) as registros,
    COUNT(*) / COUNT(DISTINCT barrio_id) as quarters_per_barrio
FROM fact_housing_master
WHERE renta_annual IS NOT NULL
GROUP BY year
ORDER BY year;
```

**Resultado esperado**: 4 quarters por barrio por año

---

## 🔍 Alternativas Consideradas

### 1. **Interpolación Lineal**
- ❌ Rechazada: No hay datos quarterly reales para interpolar
- ❌ Requeriría asumir tendencia temporal sin evidencia

### 2. **Interpolación con Splines**
- ❌ Rechazada: Demasiado compleja para datos anuales
- ❌ Puede introducir artefactos

### 3. **Forward-Fill (Actual)**
- ✅ Simple y transparente
- ✅ Mantiene valores originales sin modificación
- ✅ Adecuado para análisis de tendencias anuales

### 4. **Backward-Fill**
- ❌ Rechazada: No tiene sentido para datos históricos
- ❌ Requeriría datos futuros

---

## 📝 Recomendaciones de Uso

### ✅ Apropiado para:
- Análisis de tendencias anuales
- Comparación entre barrios
- Modelos ML que usan renta como feature estática
- Análisis de affordability a nivel anual

### ⚠️ Usar con precaución:
- Análisis de variación quarterly de affordability
- Modelos que requieren variación temporal precisa
- Análisis de estacionalidad

### ❌ No usar para:
- Análisis de cambios intra-anuales de renta
- Predicción de variación quarterly de renta
- Análisis que requiere datos quarterly reales

---

## 🔗 Referencias

- **Script de interpolación**: `scripts/export_socioeconomics_renta.py`
- **Fuente de datos**: `fact_renta` (IDESCAT)
- **Master Table**: `data/processed/barcelona_housing_master_table.csv`
- **Tabla en DB**: `fact_housing_master`

---

## 📅 Historial

- **2025-12-14**: Documentación creada
- **2025-12-13**: Interpolación implementada en `export_socioeconomics_renta.py`

