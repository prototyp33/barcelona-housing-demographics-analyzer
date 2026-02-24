# Documentación de Columnas con Valores Nulos

**Fecha**: 2026-01-19  
**Origen**: Reporte de Consistencia de Datos (`reports/DATA_CONSISTENCY_REPORT.md`)

Este documento describe las columnas con >5% de valores nulos, su propósito y si los nulos son esperados.

---

## Tablas Principales

### fact_precios

| Columna | % Nulos | Explicación |
|---------|---------|-------------|
| trimestre | 100% | Portal de Dades publica datos anuales; la columna existe en el schema pero no se usa. |
| precio_mes_alquiler | 92.1% | Muchos datasets solo tienen precio de venta. Los datos de alquiler vienen de `fact_oferta_idealista` o datasets específicos. |
| precio_m2_venta | 7.9% | Algunos registros son solo de alquiler. |

**Recomendación**: Usar `COALESCE(precio_m2_venta, precio_m2_alquiler)` o filtrar por tipo de operación según el análisis.

---

### fact_housing_master

| Columna | % Nulos | Explicación |
|---------|---------|-------------|
| price_to_income_ratio | 11.4% | Requiere renta; barrios sin `fact_renta` para ese año quedan nulos. |
| affordability_index | 11.3% | Idem. |
| affordability_ratio | 11.3% | Idem. |
| rent_burden_pct | 11.3% | Idem. |
| renta_annual, renta_min, renta_max | 10.0% | `fact_renta` solo cubre 2015-2023; años fuera de rango = nulos. |
| source | 10.0% | Metadato opcional. |

**Recomendación**: Filtrar por años con renta disponible (2015-2023) para análisis de asequibilidad.

---

### fact_renta_hist

| Columna | % Nulos | Explicación |
|---------|---------|-------------|
| renta_mediana | 11.1% | Algunos datasets solo tienen media. |
| renta_neta | 11.1% | No todos los datasets incluyen renta neta. |

**Recomendación**: Usar `COALESCE(renta_mediana, renta_promedio, renta_euros)` para métricas principales.

---

### fact_esfuerzo_alquiler

| Columna | % Nulos | Explicación |
|---------|---------|-------------|
| renta_neta | 10.9% | Depende de `fact_renta`; años sin renta = nulos. |

---

## Tablas con Columnas 100% Nulas

Estas columnas existen en el schema pero no están pobladas por el ETL actual:

### fact_calidad_aire
- `pm25_mean`, `pm10_mean`, `o3_mean`, `max_distance_m`: Métricas de calidad del aire no implementadas aún.

### fact_catastro_avanzado
- `superficie_media_m2`, `num_plantas_avg`, `dataset_id`: Pendiente de extracción/transformación.
- `num_propietarios_fisica/juridica`, `pct_propietarios_extranjeros`, `antiguedad_media_bloque`: Parcialmente poblados.

### fact_comercio
- `tasa_ocupacion_locales`, `pct_locales_ocupados`: No disponibles en la fuente actual.
- `densidad_comercial_por_km2`: Parcialmente poblada.

### fact_hogares_avanzado
- `pct_hogares_unipersonales`, `dataset_id`: Pendiente.

### fact_medio_ambiente
- `nivel_ld_dia`, `nivel_ln_noche`: Ruido por periodo; estructura diferente a `fact_ruido`.
- `nivel_lden_medio`, `pct_poblacion_expuesta_65db`: Parcialmente poblados.

### fact_servicios_salud
- `densidad_servicios_por_km2`: Parcialmente poblada.

### fact_ruido
- `etl_loaded_at`: Metadato temporal; no crítico.

### fact_renta_avanzada, fact_turismo_intensidad
- `dataset_id`: Metadato opcional.

### fact_vivienda_contexto_metropolitano
- `pct_persona_fisica`, `pct_persona_juridica`, `pct_grandes_tenedores`: Datos de titularidad no disponibles en la fuente actual.

---

## Uso en Análisis

- **Evitar** filtrar por columnas con >50% nulos sin documentar el impacto.
- **Usar** `COALESCE` o `fillna` con estrategia explícita cuando sea apropiado.
- **Documentar** en los dashboards cuando se usen datos estimados o parciales.
