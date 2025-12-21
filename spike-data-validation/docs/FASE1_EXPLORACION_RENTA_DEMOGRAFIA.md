# Fase 1: Exploración de fact_renta y fact_demografia_ampliada

**Issue**: #238 - Integrar fact_renta y fact_demografia_ampliada al MACRO v0.2
**Fecha**: 2025-12-21

---

## 📊 Resumen Ejecutivo

### fact_renta
- **Total registros**: 657
- **Barrios únicos**: 73
- **Años**: 2015-2023
- **Barrios Gràcia**: 5/5

### fact_demografia_ampliada
- **Total registros**: 2256
- **Barrios únicos**: 73
- **Años**: 2025-2025
- **Barrios Gràcia**: 5/5

### Variables Relevantes (|corr| > 0.3)
- **Total**: 9 variables identificadas

- **renta_euros_mean** (renta): r=0.312, p=0.037
- **renta_promedio_mean** (renta): r=0.312, p=0.037
- **renta_mediana_mean** (renta): r=0.310, p=0.038
- **renta_min_mean** (renta): r=0.342, p=0.022
- **poblacion_total** (demografia): r=0.915, p=0.029
- **prop_hombres** (demografia): r=0.658, p=0.227
- **prop_mujeres** (demografia): r=-0.658, p=0.227
- **prop_18_34** (demografia): r=0.763, p=0.134
- **prop_50_64** (demografia): r=-0.941, p=0.017

---

## 📋 Estructura de fact_renta

**Columnas**: 13

| Columna | Tipo |
|---------|------|
| id | INTEGER |
| barrio_id | INTEGER |
| anio | INTEGER |
| renta_euros | REAL |
| renta_promedio | REAL |
| renta_mediana | REAL |
| renta_min | REAL |
| renta_max | REAL |
| num_secciones | INTEGER |
| barrio_nombre_normalizado | TEXT |
| dataset_id | TEXT |
| source | TEXT |
| etl_loaded_at | TEXT |

---

## 📋 Estructura de fact_demografia_ampliada

**Columnas**: 11

| Columna | Tipo |
|---------|------|
| id | INTEGER |
| barrio_id | INTEGER |
| anio | INTEGER |
| sexo | TEXT |
| grupo_edad | TEXT |
| nacionalidad | TEXT |
| poblacion | INTEGER |
| barrio_nombre_normalizado | TEXT |
| dataset_id | TEXT |
| source | TEXT |
| etl_loaded_at | TEXT |

### Valores Únicos
- **sexo**: hombre, mujer
- **grupo_edad**: 18-34, 35-49, 50-64, 65+
- **nacionalidad**: 6 valores

---

## 🔗 Correlaciones con precio_m2

### Variables de Renta

| Variable | Correlación | p-value | n | Significativa |
|----------|-------------|---------|---|----------------|
| renta_euros_mean | 0.312 | 0.037 | 45 | ✅ |
| renta_promedio_mean | 0.312 | 0.037 | 45 | ✅ |
| renta_mediana_mean | 0.310 | 0.038 | 45 | ✅ |
| renta_min_mean | 0.342 | 0.022 | 45 | ✅ |
| renta_max_mean | 0.297 | 0.047 | 45 | ✅ |

### Variables Demográficas

| Variable | Correlación | p-value | n | Significativa |
|----------|-------------|---------|---|----------------|
| poblacion_total | 0.915 | 0.029 | 5 | ✅ |
| prop_hombres | 0.658 | 0.227 | 5 | ❌ |
| prop_mujeres | -0.658 | 0.227 | 5 | ❌ |
| prop_18_34 | 0.763 | 0.134 | 5 | ❌ |
| prop_35_49 | 0.215 | 0.729 | 5 | ❌ |
| prop_50_64 | -0.941 | 0.017 | 5 | ✅ |
| prop_65_plus | -0.171 | 0.783 | 5 | ❌ |
| prop_espana | nan | nan | 5 | ❌ |
| prop_extranjeros | nan | nan | 5 | ❌ |

---

## 💡 Recomendaciones para Fase 2

### Variables a Incluir en MACRO v0.3

- ✅ **renta_euros_mean** (renta): r=0.312
- ✅ **renta_promedio_mean** (renta): r=0.312
- ✅ **renta_mediana_mean** (renta): r=0.310
- ✅ **renta_min_mean** (renta): r=0.342
- ✅ **poblacion_total** (demografia): r=0.915
- ✅ **prop_hombres** (demografia): r=0.658
- ✅ **prop_mujeres** (demografia): r=-0.658
- ✅ **prop_18_34** (demografia): r=0.763
- ✅ **prop_50_64** (demografia): r=-0.941

---

**Última actualización**: 2025-12-21 12:54:32