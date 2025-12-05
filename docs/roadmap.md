# 🗺️ Roadmap 2025 - Barcelona Housing Demographics Analyzer

## Visión General

Roadmap de 24 semanas (6 meses) organizado en 4 sprints, con 8 features priorizadas basadas en el análisis comparativo de propuestas de expansión.

## 📅 Timeline Visual

```
Ene 2025          Feb 2025          Mar 2025          Abr 2025          May 2025
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│    SPRINT 1      │     SPRINT 2     │     SPRINT 3     │     SPRINT 3     │    SPRINT 4      │
│   Quick Wins     │    Core ML       │  Data Expansion  │  Data Expansion  │    Showcase      │
│  (Semanas 1-4)   │ (Semanas 5-10)   │ (Semanas 11-14)  │ (Semanas 15-18)  │ (Semanas 19-24)  │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ #02 Calculator   │                  │                  │                  │                  │
│ #13 Clustering   │ #01 ML Predict   │ #07 POI Analysis │                  │ #03 Gentrific.   │
│ #05 Alertas      │                  │ #28 API REST     │                  │ #27 Chrome Ext   │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┴──────────────────┘
     v0.2.0              v0.3.0              v0.4.0                               v1.0.0
```

## 🏃 Sprint 1: Quick Wins Foundation (Semanas 1-4)

**Objetivo:** Dashboard con 3 features funcionales para showcase inmediato.

**Milestone:** `Quick Wins Foundation`  
**Release:** `v0.2.0`  
**Due Date:** 2025-01-31

### Features

| ID | Feature | Esfuerzo | Prioridad | Estado |
|----|---------|----------|-----------|--------|
| #02 | [Calculadora de Inversión](features/feature-02-calculator.md) | 15-20h | 🔴 Alta | 🔄 Pendiente |
| #13 | Clustering de Barrios (K-Means) | 15-18h | 🔴 Alta | 🔄 Pendiente |
| #05 | Sistema de Alertas | 12-15h | 🟡 Media | 🔄 Pendiente |

### Criterios de Éxito
- [ ] 3 features desplegadas en Streamlit Cloud
- [ ] Tests unitarios >80% cobertura
- [ ] Documentación completa en `docs/features/`
- [ ] Demo funcional para portfolio

---

## 🤖 Sprint 2: Core ML Engine (Semanas 5-10)

**Objetivo:** Modelo predictivo en producción con tracking de accuracy.

**Milestone:** `Core ML Engine`  
**Release:** `v0.3.0`  
**Due Date:** 2025-02-28

### Features

| ID | Feature | Esfuerzo | Prioridad | Estado |
|----|---------|----------|-----------|--------|
| #01 | Predicción ML de Precios | 25-30h | 🔴 Alta | 🔄 Pendiente |

### Sub-tareas
- [ ] Feature engineering pipeline
- [ ] Entrenamiento modelos (Linear, XGBoost, etc.)
- [ ] Cross-validation y hyperparameter tuning
- [ ] UI de predicciones en Streamlit
- [ ] Backtesting con datos históricos
- [ ] Model versioning básico

### Criterios de Éxito
- [ ] Modelo con MAE < 15% en precio medio
- [ ] Predicciones para los 73 barrios
- [ ] Visualización de intervalos de confianza
- [ ] Documentación de metodología

---

## 📊 Sprint 3: Data Expansion (Semanas 11-18)

**Objetivo:** Enriquecimiento de datos + infraestructura escalable.

**Milestone:** `Data Expansion`  
**Release:** `v0.4.0`  
**Due Date:** 2025-04-04

### Features

| ID | Feature | Esfuerzo | Prioridad | Estado |
|----|---------|----------|-----------|--------|
| #07 | Análisis POI (OpenStreetMap) | 20-25h | 🟡 Media | 🔄 Pendiente |
| #28 | API REST (FastAPI) | 15-20h | 🟡 Media | 🔄 Pendiente |

### Sub-tareas POI
- [ ] Extractor Overpass API
- [ ] Categorías: transporte, comercio, ocio, salud, educación
- [ ] Cálculo de "walkability score" por barrio
- [ ] Correlación POI-precios

### Sub-tareas API
- [ ] Setup FastAPI con SQLAlchemy
- [ ] Endpoints CRUD barrios
- [ ] Endpoint predicciones
- [ ] Autenticación API Key
- [ ] Rate limiting
- [ ] Documentación OpenAPI

### Criterios de Éxito
- [ ] >10 categorías POI mapeadas
- [ ] API con <100ms latencia p95
- [ ] Documentación Swagger completa

---

## 🎨 Sprint 4: Differentiation Showcase (Semanas 19-24)

**Objetivo:** Features visuales + distribución multicanal.

**Milestone:** `Differentiation Showcase`  
**Release:** `v1.0.0` 🎉  
**Due Date:** 2025-05-16

### Features

| ID | Feature | Esfuerzo | Prioridad | Estado |
|----|---------|----------|-----------|--------|
| #03 | Índice de Gentrificación | 20-25h | 🟡 Media | 🔄 Pendiente |
| #27 | Chrome Extension | 15-20h | 🟢 Baja | 🔄 Pendiente |

### Sub-tareas Gentrificación
- [ ] Definir indicadores (precio, renta, demografía, POI)
- [ ] Cálculo del índice compuesto
- [ ] Visualización de "heatmap de riesgo"
- [ ] Comparativa temporal (2015-2025)

### Sub-tareas Chrome Extension
- [ ] Manifest v3 setup
- [ ] Detección de páginas Idealista/Fotocasa
- [ ] Popup con métricas del barrio
- [ ] Predicción de precio inline
- [ ] Publicación en Chrome Web Store

### Criterios de Éxito
- [ ] Índice de gentrificación para 73 barrios
- [ ] Extension publicada y funcional
- [ ] >100 instalaciones en primer mes
- [ ] Blog post técnico publicado

---

## 📈 Métricas de Proyecto

### KPIs Técnicos

| Métrica | Target Sprint 1 | Target v1.0 |
|---------|-----------------|-------------|
| Test Coverage | >80% | >90% |
| Latencia Dashboard | <2s | <1s |
| Uptime Streamlit | >99% | >99.5% |
| Bugs Críticos | 0 | 0 |

### KPIs de Impacto

| Métrica | Target v1.0 |
|---------|-------------|
| Usuarios únicos/mes | >500 |
| Instalaciones Chrome | >100 |
| GitHub Stars | >50 |
| Menciones en redes | >10 |

---

## 🚫 Backlog (No Priorizado)

Features interesantes pero fuera del scope actual:

| ID | Feature | Razón de Exclusión |
|----|---------|-------------------|
| #11 | Time Series ARIMA | Complejidad alta, valor marginal vs XGBoost |
| #21 | LLM Descriptions | Costos API, no esencial para MVP |
| #29 | WhatsApp Bot | Complejidad integración |
| #30 | Mobile App | Fuera de scope web |

---

## 📋 Weekly Rituals

### Lunes: Planning
- [ ] Revisar milestone actual
- [ ] Seleccionar 2-3 issues para la semana
- [ ] Crear branch `feature/*`

### Miércoles: Checkpoint
- [ ] Actualizar issues con progreso
- [ ] Identificar blockers
- [ ] Push de WIP

### Viernes: Review & Deploy
- [ ] PR a develop
- [ ] Merge si CI pasa
- [ ] Actualizar CHANGELOG.md
- [ ] Deploy si release

---

## 📚 Recursos

- [GitHub Project Board](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects)
- [Milestones](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/milestones)
- [Documento de Análisis Original](../planning/)

