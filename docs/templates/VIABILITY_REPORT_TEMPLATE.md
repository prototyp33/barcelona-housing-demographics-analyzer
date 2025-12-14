# Viability Report Template - Hedonic Pricing Model Spike

**Spike:** Data Validation - Barcelona Housing Hedonic Model  
**Barrio Piloto:** Gràcia  
**Fecha:** [Fecha de finalización]  
**Autor(es):** [Nombre(s)]

---

## Executive Summary (0.5 páginas)

### Pregunta Central

¿Es viable construir un modelo hedónico de precios de vivienda con datos públicos para Barcelona?

### Respuesta (Go/No-Go/Conditions)

**[GO / NO-GO / GO WITH CONDITIONS]**

### Key Metrics Table

| Métrica | Target | Resultado | Status |
|---------|--------|-----------|--------|
| Match Rate | ≥70% | [X%] | ✅/❌ |
| R² Ajustado | ≥0.55 | [X.XX] | ✅/❌ |
| Sample Size | ≥100 | [XXX] | ✅/❌ |
| OLS Assumptions | ≥4/5 | [X/5] | ✅/❌ |
| Coeficientes Plausibles | Sí | [Sí/No] | ✅/❌ |

### Recomendación

[1-2 oraciones resumiendo la decisión y razones principales]

---

## Methodology (1 página)

### Data Sources Used

**Fuente 1: [Nombre]**
- Dataset/Endpoint: [URL o nombre]
- Período: [Años]
- Granularidad: [Barrio/Mes/Transacción]
- Registros obtenidos: [Número]
- Método de acceso: [API/CSV/Scraping]

**Fuente 2: [Nombre]**
- [Mismo formato]

### Linking Method

**Método utilizado:** [Referencia Catastral / Fuzzy Address / Barrio-Mes]

**Proceso:**
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

**Match Rate por método:**
- Método 1: [X%]
- Método 2: [X%] (si aplica)
- Método final: [X%]

### Sample Characteristics

- **Período:** [Año inicio] - [Año fin]
- **Barrio(s):** [Nombre(s)]
- **Observaciones finales:** [N]
- **Variables incluidas:** [Lista]

### Problems Encountered

- **Problema 1:** [Descripción breve]
  - Impacto: [Alto/Medio/Bajo]
  - Solución aplicada: [Qué se hizo]

- **Problema 2:** [Descripción breve]
  - [Mismo formato]

---

## Model Results (1 página)

### Final Model Specification

```
ln(precio) = β₀ + β₁·ln(superficie) + β₂·antiguedad + β₃·plantas + β₄·ascensor + ε
```

### Coefficients Table

| Variable | Coeficiente | Std Error | t-value | p-value | Interpretación |
|----------|-------------|-----------|---------|---------|----------------|
| Intercept | [X.XX] | [X.XX] | [X.XX] | [X.XXX] | [Interpretación] |
| ln(superficie) | [X.XX] | [X.XX] | [X.XX] | [X.XXX] | Elasticidad: [X%] aumento en precio por [X%] aumento en superficie |
| antiguedad | [X.XX] | [X.XX] | [X.XX] | [X.XXX] | [X]€ reducción por año de antigüedad |
| plantas | [X.XX] | [X.XX] | [X.XX] | [X.XXX] | [X]€ adicionales por planta |
| ascensor | [X.XX] | [X.XX] | [X.XX] | [X.XXX] | [X]€ adicionales si tiene ascensor |

### Model Performance

- **R²:** [X.XXX]
- **R² Ajustado:** [X.XXX] ✅/❌ (Target: ≥0.55)
- **F-statistic:** [X.XX] (p-value: [X.XXX])
- **Sample Size:** [XXX] ✅/❌ (Target: ≥100)

### Diagnostics Summary

| Test | Resultado | Status |
|------|-----------|--------|
| Normalidad (Shapiro-Wilk) | p=[X.XXX] | ✅/❌ |
| Homocedasticidad (Breusch-Pagan) | p=[X.XXX] | ✅/❌ |
| Multicollinearity (VIF) | Max VIF=[X.XX] | ✅/❌ |
| Autocorrelación (Durbin-Watson) | DW=[X.XX] | ✅/❌ |
| Outliers | [N] puntos | ✅/❌ |

**Total Tests Passing:** [X/5] ✅/❌ (Target: ≥4/5)

### Key Visualizations

[Incluir 2-3 gráficos clave: Q-Q plot, residuals vs fitted, price distribution]

---

## Lessons Learned (0.5 páginas)

### What Worked Well ✅

- [Aspecto positivo 1]
- [Aspecto positivo 2]
- [Aspecto positivo 3]

### What Was Difficult ❌

- [Desafío 1]
  - Causa: [Por qué fue difícil]
  - Impacto: [Cómo afectó el spike]

- [Desafío 2]
  - [Mismo formato]

### Surprises 💡

- [Hallazgo inesperado 1]
- [Hallazgo inesperado 2]

### Recommendations for v2.0

- [Recomendación 1]
- [Recomendación 2]
- [Recomendación 3]

---

## PRD Changes Required (1 página)

### 1. Success Metrics

**Cambio propuesto:**
- R² target: [Mantener 0.55 / Ajustar a X.XX]
- Match rate target: [Mantener 70% / Ajustar a X%]
- Sample size mínimo: [Mantener 100 / Ajustar a XXX]

**Justificación:** [Por qué cambiar o mantener]

### 2. Data Layer

**Unit of Analysis:**
- [ ] Transacción individual (si match rate ≥70%)
- [ ] Barrio-Mes agregado (si match rate <70%)

**Cambios al schema:**
- [ ] Agregar tabla: [Nombre] para [Propósito]
- [ ] Modificar tabla: [Nombre] para incluir [Campo]
- [ ] Sin cambios necesarios

### 3. ETL Pipeline

**Fuentes confirmadas viables:**
- ✅ [Fuente 1] - [Confirmación]
- ✅ [Fuente 2] - [Confirmación]

**Fuentes no viables / alternativas:**
- ❌ [Fuente 3] - [Razón] → Alternativa: [Fuente alternativa]

**Nuevos extractores necesarios:**
- [ ] [Extractor 1] - Prioridad: [Alta/Media/Baja]
- [ ] [Extractor 2] - Prioridad: [Alta/Media/Baja]

### 4. Architecture

**Database:**
- ✅ PostgreSQL confirmado viable
- ✅ PostGIS necesario para [Propósito]

**Modeling:**
- ✅ OLS confirmado viable
- [ ] Considerar alternativas: [Robust Regression / ML models] si [Condición]

**Dashboard:**
- ✅ Streamlit confirmado viable
- [ ] Consideraciones: [Notas sobre performance, escalabilidad]

### 5. Timeline Adjustments

**Cambios propuestos:**
- [ ] Mantener timeline original
- [ ] Extender timeline por [X semanas] debido a [Razón]
- [ ] Reducir scope: [Feature X] movido a v2.1

### 6. Scope Changes

**Features reducidas/eliminadas:**
- [ ] [Feature X] - Movida a v2.2 (razón: [Razón])
- [ ] [Feature Y] - Eliminada (razón: [Razón])

**Features nuevas/priorizadas:**
- [ ] [Feature Z] - Agregada (razón: [Razón])

---

## Decision Record (0.5 páginas)

### Status

**[GO / NO-GO / GO WITH CONDITIONS]**

### Criteria Met/Not Met

| Criterio | Target | Resultado | Met? |
|----------|--------|-----------|------|
| Match Rate | ≥70% | [X%] | ✅/❌ |
| R² Ajustado | ≥0.55 | [X.XX] | ✅/❌ |
| Sample Size | ≥100 | [XXX] | ✅/❌ |
| OLS Assumptions | ≥4/5 | [X/5] | ✅/❌ |
| Coeficientes Plausibles | Sí | [Sí/No] | ✅/❌ |

### Justification

[2-3 oraciones explicando la decisión basada en los resultados]

### Next Steps (if GO)

- [ ] Issue de implementación creada: #[Número]
- [ ] Lecciones aprendidas documentadas en [Ubicación]
- [ ] PRD actualizado con cambios propuestos
- [ ] Sprint planning para v2.0 (fecha: [Fecha])

### Path Forward (if NO-GO)

- [ ] Razones documentadas: [Lista]
- [ ] Alternativas evaluadas: [Lista]
- [ ] Recomendación final: [Qué hacer a continuación]

---

## Appendices

### A. Data Quality Metrics

- Completeness: [X%]
- Validity: [X%]
- Consistency: [X%]

### B. Alternative Models Tested

- [Modelo alternativo 1]: R²=[X.XX], Razón de rechazo: [Razón]
- [Modelo alternativo 2]: R²=[X.XX], Razón de rechazo: [Razón]

### C. References

- [Enlace a notebook]
- [Enlace a datasets]
- [Enlaces a documentación relevante]

---

**Firma:** [Nombre]  
**Fecha:** [Fecha]  
**Aprobado por:** [Nombre(s)]

