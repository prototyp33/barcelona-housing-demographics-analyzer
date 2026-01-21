# 🚀 Quick Start - Próximos Pasos

## Acción Inmediata Recomendada

### 1. Investigar Cambios Extremos (2-3 horas)

Los cambios >100% detectados necesitan validación:

```bash
# Ver datos fuente para Baró de Viver (2015)
psql -d barcelona_housing -c "
SELECT barrio_id, anio, precio_m2_venta, source, dataset_id 
FROM fact_precios 
WHERE barrio_id IN (
    SELECT barrio_id FROM dim_barrios WHERE barrio_nombre LIKE '%Baró de Viver%'
) AND anio BETWEEN 2014 AND 2016
ORDER BY anio;
"
```

**Objetivo**: Determinar si +239.8% es error o cambio real

---

### 2. Regenerar Tabla Maestra con Mejoras (5 min)

```bash
python scripts/create_master_table_for_looker.py
```

**Resultado**: Tabla con 50 columnas (16 nuevas de calidad)

---

### 3. Validar Calidad de Datos (2 min)

```bash
python scripts/validate_master_table_quality.py
```

**Resultado**: Reporte de problemas detectados

---

### 4. Usar Datos Suavizados en Visualizaciones

```bash
python scripts/add_smoothed_data_to_master.py
```

**Resultado**: `master_table_barcelona_housing_smoothed.csv` con columnas `*_suavizado`

---

## Archivos Clave

- **Tabla maestra**: `data/exports/looker_studio/master_table_barcelona_housing.csv`
- **Tabla suavizada**: `data/exports/looker_studio/master_table_barcelona_housing_smoothed.csv`
- **Reportes**: `data/exports/anomalies/*.csv`
- **EDA**: `notebooks/05_eda_master_table.ipynb`

---

## Filtros Recomendados en Looker Studio

```
tiene_anomalias = 0 AND completitud_datos >= 50
```

