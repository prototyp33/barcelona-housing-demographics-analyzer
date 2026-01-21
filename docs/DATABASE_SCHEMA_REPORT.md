# Reporte de Esquema de Base de Datos
Generado el: 2026-01-04 13:32:05

## 📊 Resumen
- **Tablas:** 31
- **Vistas:** 15
- **Total:** 46

## 📋 Tablas
### `dim_barrios`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER | 🔑 PK |
| 2 | `barrio_nombre` | TEXT | NOT NULL |
| 3 | `barrio_nombre_normalizado` | TEXT | NOT NULL |
| 4 | `distrito_id` | INTEGER |  |
| 5 | `distrito_nombre` | TEXT |  |
| 6 | `municipio` | TEXT |  |
| 7 | `ambito` | TEXT |  |
| 8 | `codi_districte` | TEXT |  |
| 9 | `codi_barri` | TEXT |  |
| 10 | `geometry_json` | TEXT |  |
| 11 | `source_dataset` | TEXT |  |
| 12 | `etl_created_at` | TEXT |  |
| 13 | `etl_updated_at` | TEXT |  |
| 14 | `codigo_ine` | TEXT |  |
| 15 | `centroide_lat` | REAL |  |
| 16 | `centroide_lon` | REAL |  |
| 17 | `area_km2` | REAL |  |
#### 📇 Índices
- `idx_dim_barrios_nombre` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Cobertura barrios:** 73/73 (100.0%)

### `dim_barrios_extended`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER | 🔑 PK |
| 2 | `barrio_nombre` | TEXT | NOT NULL |
| 3 | `distrito_nombre` | TEXT |  |
| 4 | `indice_gentrificacion_relativo` | REAL |  |
| 5 | `indice_vulnerabilidad_socioeconomica` | REAL |  |
| 6 | `clase_social_predominante` | TEXT |  |
| 7 | `perfil_demografico_resumen` | TEXT |  |
| 8 | `precio_m2_venta_actual` | REAL |  |
| 9 | `variacion_precio_12m` | REAL |  |
| 10 | `densidad_comercial_kpi` | REAL |  |
| 11 | `etl_updated_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📈 Estadísticas
- **Registros:** 73
- **Cobertura barrios:** 73/73 (100.0%)

### `dim_tiempo`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `time_id` | INTEGER | 🔑 PK |
| 2 | `anio` | INTEGER | NOT NULL |
| 3 | `trimestre` | INTEGER |  |
| 4 | `mes` | INTEGER |  |
| 5 | `periodo` | TEXT |  |
| 6 | `year_quarter` | TEXT |  |
| 7 | `year_month` | TEXT |  |
| 8 | `es_fin_de_semana` | INTEGER | DEFAULT 0 |
| 9 | `es_verano` | INTEGER | DEFAULT 0 |
| 10 | `estacion` | TEXT |  |
| 11 | `dia_semana` | TEXT |  |
| 12 | `fecha_inicio` | TEXT |  |
| 13 | `fecha_fin` | TEXT |  |
#### 📇 Índices
- `idx_dim_tiempo_anio` 
- `idx_dim_tiempo_anio_trimestre` 
- `idx_dim_tiempo_periodo` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 50
- **Rango años:** 2015 - 2024

### `etl_quality_metrics`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `timestamp` | TEXT | NOT NULL |
| 3 | `completeness` | REAL |  |
| 4 | `validity` | REAL |  |
| 5 | `consistency` | REAL |  |
| 6 | `timeliness` | INTEGER |  |
| 7 | `run_id` | TEXT |  |
#### 🔗 Claves Foráneas
- `run_id` → `etl_runs(run_id)`
#### 📈 Estadísticas
- **Registros:** 0

### `etl_runs`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `run_id` | TEXT | 🔑 PK |
| 2 | `started_at` | TEXT | NOT NULL |
| 3 | `finished_at` | TEXT | NOT NULL |
| 4 | `status` | TEXT | NOT NULL |
| 5 | `parameters` | TEXT |  |
#### 📇 Índices
- `sqlite_autoindex_etl_runs_1` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 72

### `fact_calidad_aire`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `no2_mean` | REAL |  |
| 5 | `pm25_mean` | REAL |  |
| 6 | `pm10_mean` | REAL |  |
| 7 | `o3_mean` | REAL |  |
| 8 | `stations_nearby` | INTEGER |  |
| 9 | `max_distance_m` | REAL |  |
| 10 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_calidad_aire_barrio_fecha` 
- `idx_fact_calidad_aire_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_catastro_avanzado`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_propietarios_fisica` | INTEGER |  |
| 5 | `num_propietarios_juridica` | INTEGER |  |
| 6 | `pct_propietarios_extranjeros` | REAL |  |
| 7 | `superficie_media_m2` | REAL |  |
| 8 | `num_plantas_avg` | REAL |  |
| 9 | `antiguedad_media_bloque` | REAL |  |
| 10 | `dataset_id` | TEXT |  |
| 11 | `source` | TEXT | DEFAULT 'opendata_bcn_cadastre' |
| 12 | `etl_loaded_at` | TEXT |  |
| 13 | `indice_penalizacion_topografica` | REAL |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_catastro_avanzado_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 584
- **Rango años:** 2018 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_comercio`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_locales_comerciales` | INTEGER | DEFAULT 0 |
| 5 | `num_terrazas` | INTEGER | DEFAULT 0 |
| 6 | `num_licencias` | INTEGER | DEFAULT 0 |
| 7 | `total_establecimientos` | INTEGER | DEFAULT 0 |
| 8 | `densidad_comercial_por_km2` | REAL |  |
| 9 | `densidad_comercial_por_1000hab` | REAL |  |
| 10 | `tasa_ocupacion_locales` | REAL |  |
| 11 | `pct_locales_ocupados` | REAL |  |
| 12 | `dataset_id` | TEXT |  |
| 13 | `source` | TEXT | DEFAULT 'opendata_bcn' |
| 14 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_comercio_barrio_fecha` 
- `idx_fact_comercio_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 70
- **Rango años:** 2025 - 2025
- **Cobertura barrios:** 70/73 (95.9%)

### `fact_demografia`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `poblacion_total` | INTEGER |  |
| 5 | `poblacion_hombres` | INTEGER |  |
| 6 | `poblacion_mujeres` | INTEGER |  |
| 7 | `hogares_totales` | INTEGER |  |
| 8 | `edad_media` | REAL |  |
| 9 | `porc_inmigracion` | REAL |  |
| 10 | `densidad_hab_km2` | REAL |  |
| 11 | `dataset_id` | TEXT |  |
| 12 | `source` | TEXT |  |
| 13 | `etl_loaded_at` | TEXT |  |
| 14 | `pct_mayores_65` | REAL |  |
| 15 | `pct_menores_15` | REAL |  |
| 16 | `indice_envejecimiento` | REAL |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_demografia_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2024 - 2024
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_demografia_ampliada`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `sexo` | TEXT |  |
| 5 | `grupo_edad` | TEXT |  |
| 6 | `nacionalidad` | TEXT |  |
| 7 | `poblacion` | INTEGER |  |
| 8 | `barrio_nombre_normalizado` | TEXT |  |
| 9 | `dataset_id` | TEXT |  |
| 10 | `source` | TEXT |  |
| 11 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_demografia_ampliada_barrio_anio` 
#### 📈 Estadísticas
- **Registros:** 2,256
- **Rango años:** 2025 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_desempleo`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `mes` | INTEGER |  |
| 5 | `num_desempleados` | INTEGER |  |
| 6 | `tasa_desempleo_estimada` | REAL |  |
| 7 | `dataset_id` | TEXT |  |
| 8 | `source` | TEXT | DEFAULT 'opendata_bcn_desempleo' |
| 9 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_desempleo_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_educacion`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_centros_infantil` | INTEGER | DEFAULT 0 |
| 5 | `num_centros_primaria` | INTEGER | DEFAULT 0 |
| 6 | `num_centros_secundaria` | INTEGER | DEFAULT 0 |
| 7 | `num_centros_fp` | INTEGER | DEFAULT 0 |
| 8 | `num_centros_universidad` | INTEGER | DEFAULT 0 |
| 9 | `total_centros_educativos` | INTEGER | DEFAULT 0 |
| 10 | `dataset_id` | TEXT |  |
| 11 | `source` | TEXT | DEFAULT 'opendata_bcn_educacion' |
| 12 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_educacion_barrio_fecha` 
- `idx_fact_educacion_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2025 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_hogares_avanzado`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `promedio_personas_por_hogar` | REAL |  |
| 5 | `pct_hogares_unipersonales` | REAL |  |
| 6 | `num_hogares_con_menores` | INTEGER |  |
| 7 | `pct_hogares_nacionalidad_extranjera` | REAL |  |
| 8 | `pct_presencia_mujeres` | REAL |  |
| 9 | `dataset_id` | TEXT |  |
| 10 | `source` | TEXT | DEFAULT 'opendata_bcn_padro' |
| 11 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_hogares_avanzado_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 365
- **Rango años:** 2020 - 2024
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_housing_master`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `barrio_nombre` | TEXT |  |
| 4 | `year` | INTEGER | NOT NULL |
| 5 | `quarter` | TEXT | NOT NULL |
| 6 | `period` | TEXT |  |
| 7 | `preu_lloguer_mensual` | REAL |  |
| 8 | `preu_lloguer_m2` | REAL |  |
| 9 | `preu_venda_total` | REAL |  |
| 10 | `preu_venda_m2` | REAL |  |
| 11 | `source_rental` | TEXT |  |
| 12 | `source_sales` | TEXT |  |
| 13 | `renta_annual` | REAL |  |
| 14 | `renta_min` | REAL |  |
| 15 | `renta_max` | REAL |  |
| 16 | `price_to_income_ratio` | REAL |  |
| 17 | `rent_burden_pct` | REAL |  |
| 18 | `affordability_index` | REAL |  |
| 19 | `affordability_ratio` | REAL |  |
| 20 | `anyo_construccion_promedio` | REAL |  |
| 21 | `antiguedad_anos` | REAL |  |
| 22 | `num_edificios` | REAL |  |
| 23 | `pct_edificios_pre1950` | REAL |  |
| 24 | `superficie_m2` | REAL |  |
| 25 | `pct_edificios_con_ascensor_proxy` | REAL |  |
| 26 | `log_price_sales` | REAL |  |
| 27 | `log_price_rental` | REAL |  |
| 28 | `building_age_dynamic` | REAL |  |
| 29 | `source` | TEXT |  |
| 30 | `year_quarter` | TEXT |  |
| 31 | `time_index` | INTEGER |  |
| 32 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_housing_master_barrio_year` 
- `idx_fact_housing_master_year_quarter` 
- `idx_fact_housing_master_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 2,742
- **Cobertura barrios:** 71/73 (97.3%)

### `fact_hut`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_licencias_vut` | INTEGER |  |
| 5 | `densidad_vut_por_100_viviendas` | REAL |  |
| 6 | `dataset_id` | TEXT |  |
| 7 | `source` | TEXT | DEFAULT 'generalitat_vut' |
| 8 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_hut_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_medio_ambiente`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `nivel_lden_medio` | REAL |  |
| 5 | `nivel_ld_dia` | REAL |  |
| 6 | `nivel_ln_noche` | REAL |  |
| 7 | `pct_poblacion_expuesta_65db` | REAL |  |
| 8 | `superficie_zonas_verdes_m2` | REAL |  |
| 9 | `num_parques_jardines` | INTEGER | DEFAULT 0 |
| 10 | `num_arboles` | INTEGER | DEFAULT 0 |
| 11 | `m2_zonas_verdes_por_habitante` | REAL |  |
| 12 | `dataset_id` | TEXT |  |
| 13 | `source` | TEXT | DEFAULT 'opendata_bcn' |
| 14 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_medio_ambiente_barrio_fecha` 
- `idx_fact_medio_ambiente_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 70
- **Rango años:** 2025 - 2025
- **Cobertura barrios:** 70/73 (95.9%)

### `fact_movilidad`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER |  |
| 2 | `anio` | INTEGER |  |
| 3 | `mes` | INTEGER |  |
| 4 | `estaciones_metro` | REAL |  |
| 5 | `estaciones_bus` | INTEGER |  |
| 6 | `estaciones_bicing` | INTEGER |  |
| 7 | `dist_metro_m` | REAL |  |
| 8 | `dist_bus_m` | REAL |  |
| 9 | `access_score` | REAL |  |
| 10 | `etl_loaded_at` | TEXT |  |
| 11 | `source` | TEXT |  |
#### 📇 Índices
- `idx_fact_movilidad_barrio_fecha` 
- `idx_fact_movilidad_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2026 - 2026
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_oferta_idealista`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `operacion` | TEXT | NOT NULL |
| 4 | `anio` | INTEGER | NOT NULL |
| 5 | `mes` | INTEGER | NOT NULL |
| 6 | `num_anuncios` | INTEGER |  |
| 7 | `precio_medio` | REAL |  |
| 8 | `precio_mediano` | REAL |  |
| 9 | `precio_min` | REAL |  |
| 10 | `precio_max` | REAL |  |
| 11 | `precio_m2_medio` | REAL |  |
| 12 | `precio_m2_mediano` | REAL |  |
| 13 | `superficie_media` | REAL |  |
| 14 | `superficie_mediana` | REAL |  |
| 15 | `habitaciones_media` | REAL |  |
| 16 | `barrio_nombre_normalizado` | TEXT |  |
| 17 | `dataset_id` | TEXT |  |
| 18 | `source` | TEXT |  |
| 19 | `etl_loaded_at` | TEXT |  |
| 20 | `is_mock` | INTEGER | DEFAULT 0 |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_oferta_idealista_barrio_fecha` 
- `idx_fact_oferta_idealista_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 1,898
- **Rango años:** 2024 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_precios`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `periodo` | TEXT |  |
| 5 | `trimestre` | INTEGER |  |
| 6 | `precio_m2_venta` | REAL |  |
| 7 | `precio_mes_alquiler` | REAL |  |
| 8 | `dataset_id` | TEXT |  |
| 9 | `source` | TEXT |  |
| 10 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_precios_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 6,358
- **Rango años:** 2012 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_presion_turistica`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER |  |
| 2 | `anio` | INTEGER |  |
| 3 | `mes` | INTEGER |  |
| 4 | `num_listings_airbnb` | INTEGER |  |
| 5 | `precio_noche_promedio` | REAL |  |
| 6 | `pct_entire_home` | REAL |  |
| 7 | `tasa_ocupacion` | REAL |  |
| 8 | `num_reviews_mes` | INTEGER |  |
#### 📇 Índices
- `idx_fact_presion_turistica_barrio_fecha` 
- `idx_fact_presion_turistica_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 2,093
- **Rango años:** 2011 - 2025
- **Cobertura barrios:** 71/73 (97.3%)

### `fact_regulacion`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER |  |
| 2 | `anio` | INTEGER |  |
| 3 | `zona_tensionada` | INTEGER |  |
| 4 | `nivel_tension` | TEXT |  |
| 5 | `indice_referencia_alquiler` | REAL |  |
| 6 | `num_licencias_vut` | INTEGER |  |
| 7 | `derecho_tanteo` | INTEGER |  |
#### 📇 Índices
- `idx_fact_regulacion_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 894
- **Rango años:** 2000 - 2025
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_renta`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `renta_euros` | REAL |  |
| 5 | `renta_promedio` | REAL |  |
| 6 | `renta_mediana` | REAL |  |
| 7 | `renta_min` | REAL |  |
| 8 | `renta_max` | REAL |  |
| 9 | `num_secciones` | INTEGER |  |
| 10 | `barrio_nombre_normalizado` | TEXT |  |
| 11 | `dataset_id` | TEXT |  |
| 12 | `source` | TEXT |  |
| 13 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_renta_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2023 - 2023
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_renta_avanzada`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `renta_bruta_llar` | REAL |  |
| 5 | `indice_gini` | REAL |  |
| 6 | `ratio_p80_p20` | REAL |  |
| 7 | `dataset_id` | TEXT |  |
| 8 | `source` | TEXT | DEFAULT 'opendata_bcn_atles_renda' |
| 9 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_renta_avanzada_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 292
- **Rango años:** 2020 - 2023
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_ruido`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `nivel_lden_medio` | REAL |  |
| 5 | `nivel_ld_dia` | REAL |  |
| 6 | `nivel_ln_noche` | REAL |  |
| 7 | `pct_poblacion_expuesta_65db` | REAL |  |
| 8 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_ruido_barrio_fecha` 
- `idx_fact_ruido_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2022 - 2022
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_seguridad`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `barrio_id` | INTEGER |  |
| 2 | `anio` | INTEGER |  |
| 3 | `trimestre` | INTEGER |  |
| 4 | `delitos_patrimonio` | INTEGER |  |
| 5 | `delitos_seguridad_personal` | INTEGER |  |
| 6 | `tasa_criminalidad_1000hab` | REAL |  |
#### 📇 Índices
- `idx_fact_seguridad_barrio_fecha` 
- `idx_fact_seguridad_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 1,460
- **Rango años:** 2020 - 2024
- **Cobertura barrios:** 73/73 (100.0%)

### `fact_servicios_salud`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_centros_salud` | INTEGER | DEFAULT 0 |
| 5 | `num_hospitales` | INTEGER | DEFAULT 0 |
| 6 | `num_farmacias` | INTEGER | DEFAULT 0 |
| 7 | `total_servicios_sanitarios` | INTEGER | DEFAULT 0 |
| 8 | `densidad_servicios_por_km2` | REAL |  |
| 9 | `densidad_servicios_por_1000hab` | REAL |  |
| 10 | `dataset_id` | TEXT |  |
| 11 | `source` | TEXT | DEFAULT 'opendata_bcn' |
| 12 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_servicios_salud_barrio_fecha` 
- `idx_fact_servicios_salud_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 69
- **Rango años:** 2025 - 2025
- **Cobertura barrios:** 69/73 (94.5%)

### `fact_soroll`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `lden_mean` | REAL |  |
| 5 | `pct_exposed_65db` | REAL |  |
| 6 | `area_covered_m2` | REAL |  |
| 7 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_soroll_barrio_fecha` 
- `idx_fact_soroll_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_turismo_intensidad`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `indice_intensidad_turistica` | REAL |  |
| 5 | `num_establecimientos_turisticos` | INTEGER |  |
| 6 | `dataset_id` | TEXT |  |
| 7 | `source` | TEXT | DEFAULT 'opendata_bcn_turisme' |
| 8 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_turismo_intensidad_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_visados`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `num_visados_obra_nueva` | INTEGER |  |
| 5 | `num_viviendas_proyectadas` | INTEGER |  |
| 6 | `presupuesto_total_euros` | REAL |  |
| 7 | `dataset_id` | TEXT |  |
| 8 | `source` | TEXT | DEFAULT 'coac_visados' |
| 9 | `etl_loaded_at` | TEXT |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_visados_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 0
- **Cobertura barrios:** 0/73 (0.0%)

### `fact_vivienda_contexto_metropolitano`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `ambito` | TEXT | NOT NULL |
| 3 | `anio_inicio` | INTEGER | NOT NULL |
| 4 | `anio_fin` | INTEGER | NOT NULL |
| 5 | `propiedad_total` | REAL |  |
| 6 | `propiedad_pagada` | REAL |  |
| 7 | `propiedad_pendiente` | REAL |  |
| 8 | `alquiler_total` | REAL |  |
| 9 | `alquiler_mercado` | REAL |  |
| 10 | `alquiler_social` | REAL |  |
| 11 | `cesion_gratuita` | REAL |  |
| 12 | `pct_persona_fisica` | REAL |  |
| 13 | `pct_persona_juridica` | REAL |  |
| 14 | `pct_grandes_tenedores` | REAL |  |
| 15 | `source` | TEXT |  |
| 16 | `etl_loaded_at` | TEXT |  |
#### 📇 Índices
- `sqlite_autoindex_fact_vivienda_contexto_metropolitano_1` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 22

### `fact_vivienda_publica`
#### 📌 Columnas
| # | Nombre | Tipo | Atributos |
|---|--------|------|-----------|
| 1 | `id` | INTEGER | 🔑 PK |
| 2 | `barrio_id` | INTEGER | NOT NULL |
| 3 | `anio` | INTEGER | NOT NULL |
| 4 | `contratos_alquiler_nuevos` | INTEGER |  |
| 5 | `fianzas_depositadas_euros` | REAL |  |
| 6 | `renta_media_mensual_alquiler` | REAL |  |
| 7 | `viviendas_proteccion_oficial` | INTEGER |  |
| 8 | `dataset_id` | TEXT |  |
| 9 | `source` | TEXT | DEFAULT 'incasol_idescat' |
| 10 | `etl_loaded_at` | TEXT |  |
| 11 | `viviendas_iniciadas_vpo` | INTEGER |  |
| 12 | `viviendas_iniciadas_total` | INTEGER |  |
| 13 | `viviendas_terminadas_vpo` | INTEGER |  |
| 14 | `viviendas_terminadas_total` | INTEGER |  |
| 15 | `viviendas_principales` | INTEGER |  |
| 16 | `viviendas_no_principales` | INTEGER |  |
| 17 | `num_licencias_mayor` | INTEGER |  |
| 18 | `num_licencias_menor` | INTEGER |  |
| 19 | `viviendas_vacias` | REAL |  |
| 20 | `demanda_vpo` | REAL |  |
| 21 | `ayudas_alquiler` | REAL |  |
#### 🔗 Claves Foráneas
- `barrio_id` → `dim_barrios(barrio_id)`
#### 📇 Índices
- `idx_fact_vivienda_publica_barrio_fecha` 
- `idx_fact_vivienda_publica_unique` (UNIQUE)
#### 📈 Estadísticas
- **Registros:** 73
- **Rango años:** 2024 - 2024
- **Cobertura barrios:** 73/73 (100.0%)

## 👁️ Vistas
### `fact_accesibilidad`
⚠️ Error al inspeccionar vista: no such column: tiempo_medio_centro_minutos

### `fact_airbnb`
⚠️ Error al inspeccionar vista: no such column: etl_loaded_at

### `fact_centralidad`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `anio` | INTEGER |
| 3 | `densidad_comercial_por_km2` | REAL |
| 4 | `densidad_servicios_por_km2` | REAL |
| 5 | `indice_centralidad_bruto` |  |
| 6 | `etl_loaded_at` | TEXT |
- **Registros:** 70

### `fact_control_alquiler`
⚠️ Error al inspeccionar vista: no such column: etl_loaded_at

### `v_affordability_detallado`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `anio` | INTEGER |
| 4 | `precio_m2_venta` |  |
| 5 | `precio_mes_alquiler` |  |
| 6 | `renta_mediana` |  |
| 7 | `price_to_income_ratio` |  |
| 8 | `rent_burden_pct` |  |
| 9 | `zona_tensionada` |  |
| 10 | `nivel_tension` |  |
| 11 | `indice_referencia_alquiler` |  |
| 12 | `num_licencias_vut` |  |
| 13 | `num_listings_airbnb` |  |
| 14 | `pct_entire_home` |  |
| 15 | `categoria_affordability` |  |
- **Registros:** 1,011

### `v_affordability_quarterly`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `year` | INTEGER |
| 4 | `quarter` | TEXT |
| 5 | `preu_venda_m2` | REAL |
| 6 | `renta_annual` | REAL |
| 7 | `price_to_income_ratio` | REAL |
| 8 | `rent_burden_pct` | REAL |
| 9 | `affordability_index` | REAL |
| 10 | `categoria_affordability` |  |
- **Registros:** 2,431

### `v_barrio_scorecard`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `distrito_nombre` | TEXT |
| 4 | `ultimo_anio_datos` |  |
| 5 | `precio_m2_venta_promedio` |  |
| 6 | `precio_mes_alquiler_promedio` |  |
| 7 | `poblacion_total_promedio` |  |
| 8 | `edad_media_promedio` |  |
| 9 | `densidad_hab_km2_promedio` |  |
| 10 | `porc_inmigracion_promedio` |  |
| 11 | `renta_mediana_promedio` |  |
| 12 | `zona_tensionada` |  |
| 13 | `nivel_tension` |  |
| 14 | `indice_referencia_alquiler_promedio` |  |
| 15 | `num_licencias_vut_promedio` |  |
| 16 | `num_listings_airbnb_promedio` |  |
| 17 | `pct_entire_home_promedio` |  |
| 18 | `tasa_ocupacion_promedio` |  |
| 19 | `tasa_criminalidad_1000hab_promedio` |  |
| 20 | `delitos_patrimonio_promedio` |  |
| 21 | `delitos_seguridad_personal_promedio` |  |
| 22 | `nivel_lden_medio_promedio` |  |
| 23 | `pct_poblacion_expuesta_65db_promedio` |  |
- **Registros:** 73

### `v_correlaciones_cruzadas`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `anio` | INTEGER |
| 4 | `precio_m2_venta` |  |
| 5 | `precio_mes_alquiler` |  |
| 6 | `renta_mediana` |  |
| 7 | `poblacion_total` |  |
| 8 | `edad_media` |  |
| 9 | `densidad_hab_km2` |  |
| 10 | `porc_inmigracion` |  |
| 11 | `indice_referencia_alquiler` |  |
| 12 | `num_licencias_vut` |  |
| 13 | `num_listings_airbnb` |  |
| 14 | `pct_entire_home` |  |
| 15 | `tasa_ocupacion` |  |
| 16 | `tasa_criminalidad_1000hab` |  |
| 17 | `delitos_patrimonio` |  |
| 18 | `nivel_lden_medio` |  |
| 19 | `pct_poblacion_expuesta_65db` |  |
- **Registros:** 1,011

### `v_demografia_aggregated`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `anio` | INTEGER |
| 3 | `poblacion_total` |  |
| 4 | `poblacion_hombres` |  |
| 5 | `poblacion_mujeres` |  |
| 6 | `edad_media` |  |
| 7 | `porc_inmigracion` |  |
| 8 | `pct_mayores_65` |  |
| 9 | `pct_menores_15` |  |
| 10 | `indice_envejecimiento` |  |
| 11 | `source` |  |
| 12 | `etl_loaded_at` |  |
- **Registros:** 73

### `v_demografia_resumen`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `anio` | INTEGER |
| 4 | `poblacion_total` | INTEGER |
| 5 | `poblacion_hombres` | INTEGER |
| 6 | `poblacion_mujeres` | INTEGER |
| 7 | `hogares_totales` | INTEGER |
| 8 | `edad_media` | REAL |
| 9 | `porc_inmigracion` | REAL |
| 10 | `densidad_hab_km2` | REAL |
| 11 | `pct_mayores_65` | REAL |
| 12 | `pct_menores_15` | REAL |
| 13 | `indice_envejecimiento` | REAL |
- **Registros:** 73

### `v_gentrificacion_tendencias`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `precio_2015` | REAL |
| 4 | `precio_2024` | REAL |
| 5 | `pct_cambio_precio` |  |
| 6 | `renta_2015` | REAL |
| 7 | `renta_2024` | REAL |
| 8 | `pct_cambio_renta` |  |
| 9 | `poblacion_2015` | INTEGER |
| 10 | `poblacion_2024` | INTEGER |
- **Registros:** 2,780

### `v_precios_evolucion_anual`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `anio` | INTEGER |
| 3 | `precio_m2_venta_promedio` |  |
| 4 | `precio_mes_alquiler_promedio` |  |
| 5 | `num_registros` |  |
- **Registros:** 1,014

### `v_riesgo_gentrificacion`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `precio_actual` | REAL |
| 4 | `precio_5_anios_atras` | REAL |
| 5 | `pct_cambio_precio_5_anios` |  |
| 6 | `poblacion_actual` | INTEGER |
| 7 | `poblacion_5_anios_atras` | INTEGER |
| 8 | `pct_cambio_poblacion_5_anios` |  |
| 9 | `edad_media_actual` | REAL |
| 10 | `edad_media_5_anios_atras` | REAL |
| 11 | `renta_actual` | REAL |
| 12 | `renta_5_anios_atras` | REAL |
| 13 | `pct_cambio_renta_5_anios` |  |
| 14 | `num_listings_airbnb_actual` | INTEGER |
| 15 | `tasa_criminalidad_actual` | REAL |
| 16 | `score_riesgo_gentrificacion` |  |
| 17 | `categoria_riesgo` |  |
- **Registros:** 61,712

### `v_tendencias_consolidadas`
#### 📌 Columnas
| # | Nombre | Tipo |
|---|--------|------|
| 1 | `barrio_id` | INTEGER |
| 2 | `barrio_nombre` | TEXT |
| 3 | `anio` | INTEGER |
| 4 | `precio_m2_venta` |  |
| 5 | `precio_mes_alquiler` |  |
| 6 | `poblacion_total` |  |
| 7 | `edad_media` |  |
| 8 | `densidad_hab_km2` |  |
| 9 | `renta_mediana` |  |
| 10 | `zona_tensionada` |  |
| 11 | `nivel_tension` |  |
| 12 | `indice_referencia_alquiler` |  |
| 13 | `num_listings_airbnb_anual` |  |
| 14 | `pct_entire_home_anual` |  |
| 15 | `tasa_ocupacion_anual` |  |
| 16 | `tasa_criminalidad_1000hab_anual` |  |
| 17 | `delitos_patrimonio_anual` |  |
| 18 | `nivel_lden_medio` |  |
| 19 | `pct_poblacion_expuesta_65db` |  |
- **Registros:** 1,014

### `vw_gentrification_risk`
⚠️ Error al inspeccionar vista: no such column: e.pct_universitarios

## 📊 Resumen de Cobertura (Tablas Fact)
| Tabla | Registros | Años | Barrios |
|-------|-----------|------|---------|
| `fact_calidad_aire` | 0 | N/A | 0/73 (0%) |
| `fact_catastro_avanzado` | 584 | 2018-2025 | 73/73 (100%) |
| `fact_comercio` | 70 | 2025-2025 | 70/73 (96%) |
| `fact_demografia` | 73 | 2024-2024 | 73/73 (100%) |
| `fact_demografia_ampliada` | 2,256 | 2025-2025 | 73/73 (100%) |
| `fact_desempleo` | 0 | N/A | 0/73 (0%) |
| `fact_educacion` | 73 | 2025-2025 | 73/73 (100%) |
| `fact_hogares_avanzado` | 365 | 2020-2024 | 73/73 (100%) |
| `fact_housing_master` | 2,742 | N/A | 71/73 (97%) |
| `fact_hut` | 0 | N/A | 0/73 (0%) |
| `fact_medio_ambiente` | 70 | 2025-2025 | 70/73 (96%) |
| `fact_movilidad` | 73 | 2026-2026 | 73/73 (100%) |
| `fact_oferta_idealista` | 1,898 | 2024-2025 | 73/73 (100%) |
| `fact_precios` | 6,358 | 2012-2025 | 73/73 (100%) |
| `fact_presion_turistica` | 2,093 | 2011-2025 | 71/73 (97%) |
| `fact_regulacion` | 894 | 2000-2025 | 73/73 (100%) |
| `fact_renta` | 73 | 2023-2023 | 73/73 (100%) |
| `fact_renta_avanzada` | 292 | 2020-2023 | 73/73 (100%) |
| `fact_ruido` | 73 | 2022-2022 | 73/73 (100%) |
| `fact_seguridad` | 1,460 | 2020-2024 | 73/73 (100%) |
| `fact_servicios_salud` | 69 | 2025-2025 | 69/73 (95%) |
| `fact_soroll` | 0 | N/A | 0/73 (0%) |
| `fact_turismo_intensidad` | 0 | N/A | 0/73 (0%) |
| `fact_visados` | 0 | N/A | 0/73 (0%) |
| `fact_vivienda_contexto_metropolitano` | 22 | N/A | N/A |
| `fact_vivienda_publica` | 73 | 2024-2024 | 73/73 (100%) |