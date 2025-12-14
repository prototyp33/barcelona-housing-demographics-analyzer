# GitHub Projects Setup - Configuración Completa

**Fecha:** Diciembre 2025  
**Estado:** Configuración en progreso

---

## Campos Configurados

### Campos Críticos para Roadmap View

| # | Field Name | Type | Opciones/Configuración | Status |
|---|------------|------|------------------------|--------|
| 1 | **Status** | Single Select | Backlog, In Progress, In Review, Done, Blocked | ✅ |
| 2 | **Priority** | Single Select | P0, P1, P2, P3 (opcional) | ✅ |
| 3 | **Size** | Single Select | XS, S, M, L, XL | ✅ |
| 4 | **Estimate** | Number | Horas/story points | ✅ |
| 5 | **Start date** | Date | Para Gantt inicio | ✅ |
| 6 | **Target date** | Date | Para Gantt fin | ✅ |
| 7 | **Phase** | Single Select | Extraction, Processing, Modeling, Reporting, Tracking | ✅ |
| 8 | **Outcome** | Text | Texto libre | ✅ |
| 9 | **Epic** | Single Select | DATA, ETL, AN, VIZ, API, INFRA, UX, PERF, DOCS | ✅ |
| 10 | **Release** | Single Select | Ver opciones abajo | ⚠️ Necesita opciones |
| 11 | **Quarter** | Single Select | Q1 2026, Q2 2026 | ✅ |
| 12 | **Effort (weeks)** | Number | Duración en semanas | ✅ |
| 13 | **Sub-issues progress** | Progress | Auto-tracking | ✅ |

---

## Ajustes Recomendados

### 1. Release Field - Opciones Requeridas

**Agregar estas opciones en GitHub Projects:**

```
✅ v2.0 Foundation
✅ v2.1 Enhanced Analytics
✅ v2.2 Dashboard Polish
✅ v2.3 Complete Coverage
✅ v3.0 Public API
⚠️ Backlog (para issues no asignados aún)
⚠️ Future (para ideas post-v3.0)
```

**Cómo agregar:**
1. GitHub Projects → Click en "Release" field
2. Field settings → Add option
3. Agregar cada release una por una
4. Save

---

### 2. Status - Corrección de "Blocked"

**Descripción actual (incorrecta):**
> "This is ready to be picked up"

**Descripción correcta:**
> "This item is blocked by a dependency or external factor"

**Cómo cambiar:**
1. Click en Status field settings
2. Editar option "Blocked"
3. Cambiar description
4. Save

---

### 3. Priority - Agregar P3 (Opcional)

**Opciones actuales:** P0, P1, P2

**Recomendación:** Agregar P3 - Low

```
🔴 P0 - Critical (blocker para release)
🟠 P1 - High (importante, target current sprint)
🟡 P2 - Medium (nice-to-have, can slip)
🟢 P3 - Low (backlog, future consideration)
```

---

## Color Scheme Recomendado

### Status Colors

```yaml
Backlog: Gray (#656D76)
In progress: Blue (#0969DA)
In review: Yellow (#D4A72C)
Done: Green (#1A7F37)
Blocked: Red (#CF222E)
```

### Priority Colors

```yaml
P0: Red (#CF222E)
P1: Orange (#FB8500)
P2: Yellow (#D4A72C)
P3: Green (#1A7F37)  # Si agregas P3
```

### Epic Colors

```yaml
DATA: Blue (#0969DA)
ETL: Purple (#8250DF)
AN: Orange (#FB8500)
VIZ: Green (#1A7F37)
API: Red (#CF222E)
INFRA: Gray (#656D76)
UX: Pink (#BF3989)
PERF: Yellow (#D4A72C)
DOCS: Teal (#218BFF)
```

---

## Scripts de Automatización

### Script 1: Popular Campos en Issues Existentes

Ver: `scripts/populate_project_fields.sh`

### Script 2: Calcular Effort Automáticamente

Ver: `scripts/roadmap/calculate_effort.py`

---

## Workflow Completo - Ejemplo

### Epic: PostgreSQL Database & Schema v2.0

**Campos al crear:**

```yaml
Title: "[EPIC] PostgreSQL Database & Schema v2.0"
Status: Backlog
Priority: P0
Size: L
Estimate: 12
Start date: 2026-01-06
Target date: 2026-01-17
Phase: Extraction
Outcome: "PostgreSQL + PostGIS operational with schema v2.0 deployed"
Epic: DATA
Release: v2.0 Foundation
Quarter: Q1 2026
Effort (weeks): 1.6
Sub-issues progress: 0%
```

---

## Referencias

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Roadmap View Setup](docs/ROADMAP_SETUP.md)
- [Project Automation Scripts](scripts/)

---

**Última actualización:** Diciembre 2025

