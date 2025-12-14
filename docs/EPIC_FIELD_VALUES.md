# Epic Field - Valores Oficiales

**Fecha:** Diciembre 2025  
**Propósito:** Referencia oficial de valores del campo Epic en GitHub Projects

---

## ⚠️ IMPORTANTE

El campo **Epic** es un **clasificador de área técnica**, NO es para referenciar el número del issue epic parent.

Para referenciar el parent epic, usar en el body del issue: `Part of #NUMBER`

---

## Valores Oficiales del Campo Epic

| Valor | Descripción | Color | Ejemplos de Uso |
|-------|-------------|-------|-----------------|
| **DATA** | Database, schema, models | Blue #0969DA | Create tables, schema design, migrations |
| **ETL** | Extractors, pipelines, data loading | Purple #8250DF | Build extractors, ETL pipelines, data ingestion |
| **AN** | Analytics, statistical models | Orange #FB8500 | Hedonic models, DiD analysis, forecasting |
| **VIZ** | Visualizations, dashboards | Green #1A7F37 | Streamlit pages, Plotly charts, maps |
| **API** | REST API y endpoints | Red #CF222E | FastAPI endpoints, authentication, rate limiting |
| **INFRA** | Infrastructure, DevOps, CI/CD | Gray #656D76 | Database setup, deployment, monitoring |
| **UX** | User experience, design | Pink #BF3989 | UI redesign, user flows, accessibility |
| **PERF** | Performance optimization | Yellow #D4A72C | Query optimization, caching, load testing |
| **DOCS** | Documentation | Teal #218BFF | Architecture docs, API docs, user guides |

---

## Ejemplos de Uso por Issue

### DATA (Database & Schema)
- ✅ "Create fact_precios table" → **Epic: DATA**
- ✅ "Implement schema v2.0" → **Epic: DATA**
- ✅ "Create indexes and constraints" → **Epic: DATA**
- ✅ "Database migration script" → **Epic: DATA**

### ETL (Extractors & Pipelines)
- ✅ "Build INE price extractor" → **Epic: ETL**
- ✅ "Portal de Dades extractor" → **Epic: ETL**
- ✅ "ETL pipeline v3.0" → **Epic: ETL**
- ✅ "Data validation pipeline" → **Epic: ETL**

### AN (Analytics & Models)
- ✅ "Implement hedonic pricing model" → **Epic: AN**
- ✅ "Diff-in-Diff regulatory analysis" → **Epic: AN**
- ✅ "Price decomposition algorithm" → **Epic: AN**
- ✅ "Forecasting model" → **Epic: AN**

### VIZ (Visualizations)
- ✅ "Market Cockpit page" → **Epic: VIZ**
- ✅ "Barrio Deep Dive page" → **Epic: VIZ**
- ✅ "Interactive map with Plotly" → **Epic: VIZ**
- ✅ "Export to PDF functionality" → **Epic: VIZ**

### API (REST API)
- ✅ "FastAPI implementation" → **Epic: API**
- ✅ "JWT authentication" → **Epic: API**
- ✅ "Rate limiting middleware" → **Epic: API**
- ✅ "API documentation (OpenAPI)" → **Epic: API**

### INFRA (Infrastructure)
- ✅ "PostgreSQL setup on Render" → **Epic: INFRA**
- ✅ "CI/CD pipeline configuration" → **Epic: INFRA**
- ✅ "Monitoring and alerting" → **Epic: INFRA**
- ✅ "Database backup strategy" → **Epic: INFRA**

### UX (User Experience)
- ✅ "Dashboard redesign" → **Epic: UX**
- ✅ "Mobile responsive layout" → **Epic: UX**
- ✅ "User onboarding flow" → **Epic: UX**
- ✅ "Accessibility improvements" → **Epic: UX**

### PERF (Performance)
- ✅ "Query optimization" → **Epic: PERF**
- ✅ "Redis caching layer" → **Epic: PERF**
- ✅ "Load testing suite" → **Epic: PERF**
- ✅ "Database index tuning" → **Epic: PERF**

### DOCS (Documentation)
- ✅ "Architecture documentation" → **Epic: DOCS**
- ✅ "API documentation" → **Epic: DOCS**
- ✅ "User guide and tutorials" → **Epic: DOCS**
- ✅ "Migration guide" → **Epic: DOCS**

---

## Configuración en GitHub Projects UI

1. Ir a **GitHub Projects** → "Barcelona Housing - Roadmap"
2. Seleccionar un issue
3. En el panel lateral, buscar el campo **Epic**
4. Seleccionar el valor apropiado de la lista desplegable

**Valores disponibles:**
- DATA
- ETL
- AN
- VIZ
- API
- INFRA
- UX
- PERF
- DOCS

---

## Verificación

Para verificar que un issue tiene el Epic field configurado correctamente:

1. Ver en GitHub Projects → Campo "Epic" debe mostrar uno de los 9 valores
2. Ver en el body del issue → Sección "Project Fields" debe mencionar `**Epic:** DATA` (o el valor correspondiente)

---

## Referencias

- **Guía Completa:** `docs/EPIC_FIELD_USAGE.md`
- **Project Fields Guide:** `docs/GITHUB_PROJECTS_FIELDS_GUIDE.md`
- **Fase 1 Reference:** `docs/FASE1_CUSTOM_FIELDS_REFERENCE.md`

---

**Última actualización:** Diciembre 2025

