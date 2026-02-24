# Reporte de Consistencia de Datos

**Fecha**: 2026-02-19 13:11:23
**Base de datos**: `/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/data/processed/database.db`

---

## 1. Resumen Ejecutivo

- **Tablas con datos temporales**: 26
- **Tablas con gaps de años**: 0
- **Tablas con >10% nulos**: 15
- **Consistencia cruzada (barrios)**: 100.0%

---

## 2. Inconsistencia de Años (Gaps Temporales)

| Tabla | Min | Max | Años con datos | Gaps | CV% |
|-------|-----|-----|----------------|------|-----|
| fact_alquiler_mensual | 2014 | 2025 | 12/12 | ✓ | 14.0 |
| fact_calidad_aire | 2025 | 2025 | 1/1 | ✓ | 0.0 |
| fact_catastro_avanzado | 2018 | 2025 | 8/8 | ✓ | 0.0 |
| fact_comercio | 2025 | 2025 | 1/1 | ✓ | 0.0 |
| fact_demografia | 2015 | 2025 | 11/11 | ✓ | 0.0 |
| fact_demografia_ampliada | 2015 | 2025 | 11/11 | ✓ | 231.2 |
| fact_desempleo | 2023 | 2024 | 2/2 | ✓ | 0.0 |
| fact_educacion | 2026 | 2026 | 1/1 | ✓ | 0.0 |
| fact_esfuerzo_alquiler | 2015 | 2023 | 9/9 | ✓ | 1.0 |
| fact_hogares_avanzado | 2020 | 2024 | 5/5 | ✓ | 0.0 |
| fact_housing_master | 2015 | 2024 | 10/10 | ✓ | 0.9 |
| fact_medio_ambiente | 2025 | 2025 | 1/1 | ✓ | 0.0 |
| fact_movilidad | 2026 | 2026 | 1/1 | ✓ | 0.0 |
| fact_oferta_idealista | 2024 | 2025 | 2/2 | ✓ | 84.6 |
| fact_precios | 2012 | 2025 | 14/14 | ✓ | 20.0 |
| fact_precios_backup_20260110_111056 | 2012 | 2025 | 14/14 | ✓ | 21.2 |
| fact_presion_turistica | 2011 | 2025 | 15/15 | ✓ | 92.0 |
| fact_regulacion | 2000 | 2025 | 26/26 | ✓ | 101.7 |
| fact_renta | 2015 | 2025 | 11/11 | ✓ | 0.0 |
| fact_renta_avanzada | 2020 | 2023 | 4/4 | ✓ | 0.0 |
| fact_renta_hist | 2015 | 2023 | 9/9 | ✓ | 0.0 |
| fact_ruido | 2022 | 2022 | 1/1 | ✓ | 0.0 |
| fact_seguridad | 2020 | 2024 | 5/5 | ✓ | 0.0 |
| fact_servicios_salud | 2025 | 2025 | 1/1 | ✓ | 0.0 |
| fact_turismo_intensidad | 2008 | 2025 | 18/18 | ✓ | 71.8 |
| fact_vivienda_publica | 2026 | 2026 | 1/1 | ✓ | 0.0 |

**Leyenda**: CV% = Coeficiente de variación en registros/año (alto = inconsistencia).

---

## 3. Métricas Faltantes (Valores Nulos >5%)

### fact_calidad_aire (73 filas)

| Columna | % Nulos |
|---------|--------|
| pm25_mean | 100.0% |
| pm10_mean | 100.0% |
| o3_mean | 100.0% |
| max_distance_m | 100.0% |

### fact_catastro_avanzado (584 filas)

| Columna | % Nulos |
|---------|--------|
| superficie_media_m2 | 100.0% |
| num_plantas_avg | 100.0% |
| dataset_id | 100.0% |
| num_propietarios_fisica | 50.0% |
| num_propietarios_juridica | 50.0% |
| pct_propietarios_extranjeros | 37.5% |
| antiguedad_media_bloque | 37.5% |

### fact_comercio (73 filas)

| Columna | % Nulos |
|---------|--------|
| tasa_ocupacion_locales | 100.0% |
| pct_locales_ocupados | 100.0% |
| densidad_comercial_por_km2 | 95.9% |
| dataset_id | 95.9% |

### fact_demografia_ampliada (2,986 filas)

| Columna | % Nulos |
|---------|--------|
| grupo_edad | 24.4% |
| nacionalidad | 24.4% |

### fact_esfuerzo_alquiler (649 filas)

| Columna | % Nulos |
|---------|--------|
| renta_neta | 10.9% |

### fact_hogares_avanzado (365 filas)

| Columna | % Nulos |
|---------|--------|
| pct_hogares_unipersonales | 100.0% |
| dataset_id | 100.0% |

### fact_housing_master (2,742 filas)

| Columna | % Nulos |
|---------|--------|
| price_to_income_ratio | 11.4% |
| affordability_index | 11.3% |
| affordability_ratio | 11.3% |
| rent_burden_pct | 11.3% |
| renta_annual | 10.0% |
| renta_min | 10.0% |
| renta_max | 10.0% |
| source | 10.0% |

### fact_medio_ambiente (73 filas)

| Columna | % Nulos |
|---------|--------|
| nivel_ld_dia | 100.0% |
| nivel_ln_noche | 100.0% |
| nivel_lden_medio | 95.9% |
| pct_poblacion_expuesta_65db | 95.9% |
| dataset_id | 95.9% |

### fact_precios (10,999 filas)

| Columna | % Nulos |
|---------|--------|
| trimestre | 100.0% |
| precio_mes_alquiler | 92.1% |
| precio_m2_venta | 7.9% |

### fact_precios_backup_20260110_111056 (6,358 filas)

| Columna | % Nulos |
|---------|--------|
| trimestre | 100.0% |
| precio_mes_alquiler | 86.4% |
| precio_m2_venta | 13.6% |

### fact_renta_avanzada (292 filas)

| Columna | % Nulos |
|---------|--------|
| dataset_id | 100.0% |

### fact_renta_hist (657 filas)

| Columna | % Nulos |
|---------|--------|
| renta_mediana | 11.1% |
| renta_neta | 11.1% |

### fact_ruido (73 filas)

| Columna | % Nulos |
|---------|--------|
| etl_loaded_at | 100.0% |

### fact_servicios_salud (73 filas)

| Columna | % Nulos |
|---------|--------|
| densidad_servicios_por_km2 | 94.5% |
| dataset_id | 94.5% |

### fact_turismo_intensidad (438 filas)

| Columna | % Nulos |
|---------|--------|
| dataset_id | 100.0% |

### fact_vivienda_contexto_metropolitano (22 filas)

| Columna | % Nulos |
|---------|--------|
| pct_persona_fisica | 100.0% |
| pct_persona_juridica | 100.0% |
| pct_grandes_tenedores | 95.5% |

---

## 4. Consistencia Cruzada (Barrios)

Mide el solapamiento de barrios entre `fact_precios`, `fact_demografia_ampliada` y `fact_renta`.

- **Barrios en todas las tablas**: 73
- **Barrios en al menos una**: 73
- **Consistencia**: 100.0%

| Tabla | Barrios únicos |
|-------|----------------|
| fact_precios | 73 |
| fact_demografia_ampliada | 73 |
| fact_renta | 73 |

---

## 5. Inconsistencias de Rango entre Tablas Clave

Rangos de años disponibles por tabla (para cruces barrio-año):

| Tabla | Año min | Año max | Años comunes con fact_precios |
|-------|---------|---------|--------------------------------|
| fact_precios | 2012 | 2025 | 14 |
| fact_demografia_ampliada | 2015 | 2025 | 11 |
| fact_renta | 2015 | 2025 | 11 |
| fact_demografia | 2015 | 2025 | 11 |

**Nota**: Para análisis multivariable (precio + renta + demografía), usar solo años presentes en todas las tablas.

---

## 6. Cobertura por Año (Barrios)

Número de barrios con datos por tabla y año en tablas clave.

### fact_precios

| Año | Barrios |
|-----|---------|
| 2012 | 68 |
| 2013 | 70 |
| 2014 | 73 |
| 2015 | 73 |
| 2016 | 73 |
| 2017 | 73 |
| 2018 | 73 |
| 2019 | 73 |
| 2020 | 73 |
| 2021 | 73 |
| 2022 | 73 |
| 2023 | 73 |
| 2024 | 73 |
| 2025 | 73 |

### fact_demografia_ampliada

| Año | Barrios |
|-----|---------|
| 2015 | 73 |
| 2016 | 73 |
| 2017 | 73 |
| 2018 | 73 |
| 2019 | 73 |
| 2020 | 73 |
| 2021 | 73 |
| 2022 | 73 |
| 2023 | 73 |
| 2024 | 73 |
| 2025 | 73 |

### fact_renta

| Año | Barrios |
|-----|---------|
| 2015 | 73 |
| 2016 | 73 |
| 2017 | 73 |
| 2018 | 73 |
| 2019 | 73 |
| 2020 | 73 |
| 2021 | 73 |
| 2022 | 73 |
| 2023 | 73 |
| 2024 | 73 |
| 2025 | 73 |

---

## 7. Recomendaciones

- Revisar y documentar columnas con alta proporción de nulos.

---

## 8. Acciones Aplicadas (2026-01-19)

| Recomendación | Acción |
|---------------|--------|
| Documentar columnas con nulos | Creado `docs/DATA_NULL_COLUMNS_DOCUMENTATION.md` |
| fact_renta 2024-2025 | Script `scripts/extend_fact_renta_2024_2025.py` — forward-fill desde 2023 (source=estimated_forward_fill) |
| fact_demografia_ampliada históricos | Script `scripts/backfill_fact_demografia_ampliada.py` — 730 registros 2015-2024 desde fact_demografia |

**Nota**: Los datos de renta 2024-2025 son estimaciones. Ejecutar `python scripts/extend_fact_renta_2024_2025.py` (sin `--skip-extraction`) cuando IDESCAT publique datos oficiales.
