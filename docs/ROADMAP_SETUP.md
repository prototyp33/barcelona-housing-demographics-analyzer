# GitHub Projects Roadmap View: Setup Guide

## ✅ Completado Automáticamente

1. **Date Configuration:** `.roadmap_dates.env` creado con todas las fechas
2. **Epic Issues:** Scripts creados para generar epics con fechas
3. **User Stories:** Scripts creados para generar user stories
4. **Milestones:** 5 milestones creados (v2.0-v3.0)
5. **Labels:** Labels necesarios creados

## 📋 Pasos Manuales Restantes (15-20 minutos)

### Paso 1: Crear GitHub Project

1. Ve a: `https://github.com/prototyp33/barcelona-housing-demographics-analyzer`
2. Click en **Projects** tab
3. Click **New project** (botón verde)
4. **Select template:** "Roadmap"
5. **Project name:** `Barcelona Housing - Product Roadmap`
6. **Visibility:** Private
7. Click **Create**

### Paso 2: Configurar Custom Fields

1. Click **⚙️ Settings** (top right del project)
2. Under **Fields**, click **+ New field**

**Agregar estos campos:**

| Field Name | Type | Options/Config |
|------------|------|----------------|
| **Start date** | Date | (ya existe en template Roadmap) |
| **Target date** | Date | (ya existe en template Roadmap) |
| **Epic** | Single select | DATA, ETL, AN, VIZ, API, INFRA, UX, PERF, DOCS |
| **Release** | Single select | v2.0, v2.1, v2.2, v2.3, v3.0 |
| **Quarter** | Single select | Q1 2026, Q2 2026 |
| **Effort (weeks)** | Number | Min: 0.5, Max: 8 |
| **Status** | Single select | Not Started, In Progress, At Risk, Done |

### Paso 3: Agregar Issues al Project

1. Click **Add items** (bottom del project)
2. Search: `label:epic milestone:"v2.0 Foundation"`
3. Select all epic issues
4. Click **Add selected items**
5. Repeat para `label:user-story`

### Paso 4: Populate Date Fields

Para cada issue en el project:

1. Click en el issue card
2. En el panel lateral, encontrar **Start date** y **Target date**
3. Copiar fechas del body del issue (sección "📅 Timeline")
4. Fill in **Epic**, **Release**, **Quarter** fields

**Quick Reference (fechas principales):**

```
EPIC #173: PostgreSQL & Schema
  Start: 2026-01-06
  Target: 2026-01-17
  Epic: DATA
  Release: v2.0
  Quarter: Q1 2026

ETL Pipeline
  Start: 2026-01-13
  Target: 2026-01-19
  Epic: ETL
  Release: v2.0

Hedonic Model
  Start: 2026-01-20
  Target: 2026-01-26
  Epic: AN
  Release: v2.0

Dashboard MVP
  Start: 2026-01-20
  Target: 2026-01-26
  Epic: VIZ
  Release: v2.0

Deployment
  Start: 2026-01-27
  Target: 2026-01-27
  Epic: INFRA
  Release: v2.0
```

### Paso 5: Configurar Roadmap View

1. Click **Roadmap** tab (debería ser la vista por defecto)
2. Click **⚙️** (view settings, top right)
3. Configure:
   - **Start date field:** Start date
   - **Target date field:** Target date
   - **Group by:** Release (o Quarter)
   - **Sort by:** Start date (ascending)
   - **Zoom:** Weeks (o Months)
   - **Show markers:** Checked (muestra línea de hoy)

**Resultado:** Verás un Gantt chart con barras para cada epic!

## 🎯 Resultado Esperado

```
January 2026        │ February 2026     │ March 2026
────────────────────┼───────────────────┼──────────────
        6  13  20 27│  3  10  17  24    │  3  10  17 24
────────────────────┼───────────────────┼──────────────
v2.0                │                   │
│                   │                   │
├─DATA-001 ████     │                   │
├─DATA-002 ██████   │                   │
├─ETL-001    ███    │                   │
├─ETL-002    ███    │                   │
├─AN-001        ███ │                   │
├─VIZ-001       ███ │                   │
└─INFRA-001       █ │                   │
                    │                   │
                v2.0│                   │
                 │  │                   │
                    │ v2.1              │
                    ├─AN-002 ██████     │
                    └─...               │
```

## 📝 Scripts Disponibles

- `scripts/create_roadmap_epics_with_dates.sh` - Crear epic issues con fechas
- `scripts/create_user_stories_v2_0.sh` - Crear user stories para v2.0
- `scripts/verify_roadmap_setup.sh` - Verificar setup completo
- `scripts/roadmap_progress.sh` - Reporte de progreso del roadmap

## 🔗 Enlaces Útiles

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Roadmap View Guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-view)

