# GitHub Projects Views Setup - Guía Completa

**Fecha:** Diciembre 2025  
**Propósito:** Configurar 3 vistas en GitHub Projects para tracking del proyecto

---

## 📋 Vistas a Configurar

1. **Vista A: Roadmap (Gantt Chart)** - Visualización temporal
2. **Vista B: Sprint Board (Kanban)** - Tracking diario
3. **Vista C: Epic Dashboard (Table)** - Vista ejecutiva

---

## Vista A: Roadmap (Gantt Chart) ✅ CRITICAL

### Configuración

**Tipo:** Roadmap  
**Nombre:** "📅 Roadmap - Releases"

**Configuración:**
- **Group by:** Release
- **Sort by:** Start date
- **Show:** Start date, Target date markers
- **Zoom:** Weeks
- **Color by:** Epic (opcional)

### Pasos en GitHub UI

1. Ir a GitHub Projects → "Barcelona Housing - Roadmap"
2. Click en "Views" → "+ New view"
3. Seleccionar "Roadmap"
4. Configurar:
   - Group by: Release
   - Sort by: Start date
   - Show markers: Start date, Target date
   - Zoom: Weeks
5. Guardar vista

### Resultado Visual Esperado

```
Jan 2026        │ Feb 2026       │ Mar 2026
────────────────┼────────────────┼────────────────
v2.0 Foundation │                │
  Fase 1 ████   │                │
  Fase 2        │ ████████       │
  Fase 4        │                │ ████
                │                │
v2.1 Enhanced   │                │
  Fase 3        │        ████████│████
```

### Uso

- Ver timeline de epics
- Identificar overlaps
- Planning de sprints
- Visualizar dependencias temporales

---

## Vista B: Sprint Board (Kanban) ✅ CRITICAL

### Configuración

**Tipo:** Board  
**Nombre:** "🏃 Sprint - Current Work"

**Configuración:**
- **Column field:** Status
- **Columns:** Backlog → In Progress → In Review → Done → Blocked
- **Group by:** None (flat board)
- **Sort:** Priority DESC
- **Filter:** Quarter = Q1 2026

### Pasos en GitHub UI

1. Ir a GitHub Projects → "Barcelona Housing - Roadmap"
2. Click en "Views" → "+ New view"
3. Seleccionar "Board"
4. Configurar:
   - Column field: Status
   - Agregar columnas: Backlog, In Progress, In Review, Done, Blocked
   - Group by: None
   - Sort: Priority (Descending)
   - Filter: Quarter = Q1 2026
5. Guardar vista

### Resultado Visual Esperado

```
┌─────────┬─────────────┬───────────┬──────┬─────────┐
│ Backlog │ In Progress │ In Review │ Done │ Blocked │
├─────────┼─────────────┼───────────┼──────┼─────────┤
│ #188    │             │           │      │         │
│ #189    │             │           │      │         │
│ #190    │             │           │      │         │
│   ...   │             │           │      │         │
└─────────┴─────────────┴───────────┴──────┴─────────┘
```

### Uso

- Daily standups
- Ver qué está en progreso
- Identificar blockers
- Tracking de estado diario

---

## Vista C: Epic Dashboard (Table) ✅ RECOMMENDED

### Configuración

**Tipo:** Table  
**Nombre:** "📊 Epic Dashboard"

**Configuración:**
- **Group by:** Epic (DATA, ETL, INFRA, DOCS)
- **Columns:** Title, Release, Priority, Estimate, Effort, Progress, Start, Target
- **Filter:** Labels contains "epic"
- **Sort:** Start date

### Pasos en GitHub UI

1. Ir a GitHub Projects → "Barcelona Housing - Roadmap"
2. Click en "Views" → "+ New view"
3. Seleccionar "Table"
4. Configurar:
   - Group by: Epic
   - Agregar columnas: Title, Release, Priority, Estimate, Effort (weeks), Start Date, Target Date
   - Filter: Labels contains "epic"
   - Sort: Start date (Ascending)
5. Guardar vista

### Resultado Visual Esperado

```
┌──────┬───────────────────┬─────────┬──────────┬────────┬──────────┐
│ Epic │ Title             │ Release │ Priority │ Effort │ Progress │
├──────┼───────────────────┼─────────┼──────────┼────────┼──────────┤
│ DATA │ Fase 1: Database  │ v2.0    │ P0       │ 1.2w   │ 0/6 ✅   │
│ ETL  │ Fase 2: Critical  │ v2.0    │ P0       │ 6.4w   │ 0/13 ✅  │
│ ETL  │ Fase 3: Complem   │ v2.1    │ P1       │ 15.7w  │ 0/17 ✅  │
│ INFRA│ Fase 4: Integrat  │ v2.0    │ P0       │ 5.5w   │ 0/10 ✅  │
└──────┴───────────────────┴─────────┴──────────┴────────┴──────────┘
```

### Uso

- Reporting a stakeholders
- Ver progreso por área técnica
- Planning de capacidad
- Vista ejecutiva de alto nivel

---

## ⏱️ Tiempo Estimado

- **Vista A (Roadmap):** 10 minutos
- **Vista B (Sprint Board):** 10 minutos
- **Vista C (Epic Dashboard):** 10 minutos
- **Total:** 30 minutos

**Alternativa rápida:** Solo Vista A + B (20 min), Vista C después

---

## ✅ Checklist de Configuración

### Vista A: Roadmap
- [ ] Vista creada con nombre "📅 Roadmap - Releases"
- [ ] Group by: Release configurado
- [ ] Sort by: Start date configurado
- [ ] Start date y Target date markers visibles
- [ ] Zoom: Weeks configurado
- [ ] Epics aparecen en el timeline

### Vista B: Sprint Board
- [ ] Vista creada con nombre "🏃 Sprint - Current Work"
- [ ] Column field: Status configurado
- [ ] 5 columnas creadas (Backlog, In Progress, In Review, Done, Blocked)
- [ ] Group by: None configurado
- [ ] Sort: Priority DESC configurado
- [ ] Filter: Quarter = Q1 2026 aplicado
- [ ] Issues aparecen en las columnas correctas

### Vista C: Epic Dashboard
- [ ] Vista creada con nombre "📊 Epic Dashboard"
- [ ] Group by: Epic configurado
- [ ] Columnas agregadas (Title, Release, Priority, Estimate, Effort, Start, Target)
- [ ] Filter: Labels contains "epic" aplicado
- [ ] Sort: Start date configurado
- [ ] Epics aparecen agrupados por categoría técnica

---

## 🔗 Referencias

- **GitHub Projects Docs:** https://docs.github.com/en/issues/planning-and-tracking-with-projects
- **Custom Fields Guide:** `docs/GITHUB_PROJECTS_FIELDS_GUIDE.md`
- **Project Setup:** `docs/GITHUB_PROJECTS_SETUP.md`

---

**Última actualización:** Diciembre 2025

