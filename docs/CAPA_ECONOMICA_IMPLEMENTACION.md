# Implementación de Capa Económica para Análisis de Correlaciones

**Fecha:** 17 de Enero 2026  
**Estado:** ✅ Completado (Fase 1)

---

## 📊 Resumen Ejecutivo

Se ha implementado la capa económica consolidada para habilitar análisis de correlaciones entre variables demográficas y económicas en los 73 barrios de Barcelona.

### Objetivos Cumplidos

1. ✅ **Vista consolidada económica** (`v_economia_consolidada`)
2. ✅ **Vista de correlaciones mejorada** (`v_correlaciones_cruzadas`)
3. ✅ **Métricas económicas derivadas** (affordability, ratio precio/renta)
4. ✅ **Integración de múltiples fuentes económicas**

---

## 🗂️ Estructura de Datos Económicos

### Tablas de Hechos Económicas Existentes

| Tabla | Registros | Años | Cobertura | Estado |
|-------|-----------|------|-----------|--------|
| `fact_precios` | 6,358 | 2012-2025 | 73 barrios | ✅ Completo |
| `fact_renta` | 73 | 2022 | 73 barrios | ⚠️ Solo 1 año |
| `fact_renta_avanzada` | 292 | 2020-2023 | 73 barrios | ✅ 4 años |
| `fact_desempleo` | 1,752 | 2023-2024 | 73 barrios | ⚠️ Solo 2 años |
| `fact_catastro_avanzado` | 584 | 2021-2024 | 73 barrios | ✅ 4 años |
| `fact_hogares_avanzado` | 365 | 2020-2024 | 73 barrios | ✅ 5 años |

### Indicadores Económicos Disponibles

#### 1. **Renta e Ingresos**
- `renta_euros`: Renta disponible per cápita (€)
- `renta_promedio`: Renta promedio por barrio
- `renta_mediana`: Renta mediana por barrio
- `renta_bruta_llar`: Renta bruta por hogar (€)
- `indice_gini`: Índice de Gini (desigualdad 0-1)
- `ratio_p80_p20`: Ratio percentil 80 / percentil 20

#### 2. **Precios de Vivienda**
- `precio_m2_venta`: Precio por m² en venta (€/m²)
- `precio_mes_alquiler`: Precio mensual de alquiler (€/mes)

#### 3. **Mercado Laboral**
- `tasa_desempleo_estimada`: Tasa de desempleo (%)
- `num_desempleados`: Número absoluto de desempleados

#### 4. **Métricas Derivadas (Nuevas)**
- `ratio_precio_renta_mensual`: Precio m² / (Renta mediana / 12)
- `pct_renta_destinada_alquiler`: (Alquiler anual / Renta mediana) × 100
- `affordability_index`: Renta mediana / (Alquiler mensual × 12)

---

## 🔍 Vistas Analíticas Creadas

### 1. `v_economia_consolidada`

**Propósito:** Vista consolidada específica para análisis económico-demográfico.

**Campos principales:**
- Variables económicas básicas (precios, renta)
- Renta avanzada (desigualdad: Gini, P80/P20)
- Desempleo
- Métricas derivadas (affordability, ratios)
- Variables demográficas (para correlaciones)
- Variables de hogares y catastro

**Uso:**
```sql
SELECT 
    barrio_nombre,
    anio,
    precio_m2_venta,
    renta_mediana,
    indice_gini,
    tasa_desempleo,
    affordability_index
FROM v_economia_consolidada
WHERE anio >= 2020;
```

### 2. `v_correlaciones_cruzadas` (Mejorada)

**Propósito:** Vista completa para análisis de correlaciones entre todas las dimensiones.

**Mejoras implementadas:**
- ✅ Incluye todos los indicadores económicos (renta básica + avanzada)
- ✅ Incluye desempleo
- ✅ Métricas derivadas económicas
- ✅ Variables demográficas completas
- ✅ Variables de regulación, turismo, seguridad, ruido

**Uso:**
```sql
SELECT 
    barrio_nombre,
    anio,
    precio_m2_venta,
    renta_mediana,
    indice_gini,
    poblacion_total,
    edad_media,
    porc_inmigracion,
    tasa_desempleo
FROM v_correlaciones_cruzadas
WHERE anio >= 2020;
```

---

## 📈 Métricas Derivadas Explicadas

### 1. `ratio_precio_renta_mensual`
**Fórmula:** `precio_m2_venta / (renta_mediana / 12)`

**Interpretación:**
- Indica cuántos meses de renta mediana se necesitan para comprar 1 m²
- Valores altos = vivienda menos asequible
- Útil para comparar asequibilidad entre barrios

### 2. `pct_renta_destinada_alquiler`
**Fórmula:** `(precio_mes_alquiler × 12 / renta_mediana) × 100`

**Interpretación:**
- Porcentaje de renta anual destinado al alquiler
- Regla general: >30% = sobrecarga económica
- Valores altos = menor capacidad de ahorro

### 3. `affordability_index`
**Fórmula:** `renta_mediana / (precio_mes_alquiler × 12)`

**Interpretación:**
- Ratio de renta anual vs. gasto anual en alquiler
- Valores >1 = renta suficiente para alquiler
- Valores <1 = renta insuficiente (sobrecarga)

---

## 🔄 Próximos Pasos (Fase 2)

### 1. Completar Cobertura Temporal

**Prioridad Alta:**
- [ ] Extraer datos históricos de renta (2015-2024)
  - Dataset: `renda-disponible-llars-bcn`
  - Método: Usar `OpenDataBCNExtractor.download_dataset_historical()`
- [ ] Extraer datos históricos de desempleo (2015-2024)
  - Dataset: `est-padro-parats`
  - Método: Similar a renta

**Script sugerido:**
```bash
python scripts/extract_priority_sources.py \
    --sources renta desempleo \
    --year-start 2015 \
    --year-end 2024
```

### 2. Agregar Indicadores Económicos Adicionales

**Prioridad Media:**
- [ ] Actividad económica por barrio (licencias comerciales)
- [ ] Tasa de actividad laboral (ocupados / población activa)
- [ ] Renta disponible neta (después de impuestos)
- [ ] Índice de precios al consumo por barrio (si disponible)

### 3. Análisis de Correlaciones

**Prioridad Alta:**
- [ ] Crear script de análisis de correlaciones
  - Usar `v_economia_consolidada` como fuente
  - Calcular correlaciones Pearson/Spearman
  - Visualizar matriz de correlaciones
- [ ] Identificar correlaciones significativas
  - Precio vs. Renta
  - Desempleo vs. Precio
  - Gini vs. Gentrificación
  - Affordability vs. Demografía

**Script sugerido:**
```python
# scripts/analyze_economic_correlations.py
from src.analysis.descriptive import calculate_correlations

correlations = calculate_correlations(
    metrics=['precio_m2_venta', 'renta_mediana', 'indice_gini', 
             'tasa_desempleo', 'poblacion_total', 'edad_media'],
    year=2023,
    db_path='data/processed/database.db'
)
```

---

## 📝 Notas Técnicas

### Limitaciones Actuales

1. **Cobertura temporal limitada:**
   - Renta básica: Solo 2022
   - Desempleo: Solo 2023-2024
   - Renta avanzada: 2020-2023 (buena cobertura)

2. **Datos faltantes:**
   - Algunos barrios pueden no tener todos los indicadores
   - Las métricas derivadas requieren ambos: precio Y renta

3. **Granularidad:**
   - Datos principalmente anuales
   - Algunos indicadores pueden tener granularidad trimestral

### Recomendaciones

1. **Para análisis de correlaciones:**
   - Usar años con mayor cobertura (2020-2023)
   - Filtrar registros con datos completos
   - Considerar imputación para datos faltantes

2. **Para análisis temporal:**
   - Priorizar `fact_precios` (mejor cobertura: 2012-2025)
   - Usar `fact_renta_avanzada` para años 2020-2023
   - Completar datos históricos antes de análisis de tendencias

---

## ✅ Checklist de Implementación

- [x] Crear vista `v_economia_consolidada`
- [x] Mejorar vista `v_correlaciones_cruzadas`
- [x] Agregar métricas derivadas económicas
- [x] Integrar todas las fuentes económicas
- [x] Documentar estructura y uso
- [ ] Extraer datos históricos faltantes (Fase 2)
- [ ] Crear script de análisis de correlaciones (Fase 2)
- [ ] Validar cobertura completa (Fase 2)

---

## 📚 Referencias

- **Vista consolidada:** `src/database_views.py` (líneas 532-600)
- **Tablas económicas:** `src/database_setup.py`
- **Extractores:** `src/extraction/opendata.py`, `src/extraction/bcn_income.py`
- **Análisis:** `src/analysis/descriptive.py` (función `calculate_correlations`)
