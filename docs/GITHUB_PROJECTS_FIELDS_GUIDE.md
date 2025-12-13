# GitHub Projects Custom Fields - Guía Completa

**Fecha:** Diciembre 2025

---

## Campos Configurados

### 1. Status (Single Select)

**Opciones:**
- **Backlog** - "This item hasn't been started" (Gray #656D76)
- **In Progress** - "This is actively being worked on" (Blue #0969DA)
- **In Review** - "This item is in review" (Yellow #D4A72C)
- **Done** - "This has been completed" (Green #1A7F37)
- **Blocked** - "This item is blocked by a dependency or external factor" (Red #CF222E) ⚠️ **CORREGIR**

---

### 2. Priority (Single Select)

**Opciones:**
- **P0 - Critical** - "Blocker para release" (Red #CF222E)
- **P1 - High** - "Importante, target current sprint" (Orange #FB8500)
- **P2 - Medium** - "Nice-to-have, can slip" (Yellow #D4A72C)
- **P3 - Low** - "Backlog, future consideration" (Green #1A7F37) ⚠️ **AGREGAR**

---

### 3. Size (Single Select)

**Opciones:**
- XS (1-2 horas)
- S (3-5 horas)
- M (1 día)
- L (2-3 días)
- XL (1 semana+)

---

### 4. Estimate (Number)

**Propósito:** Horas estimadas o story points

**Ejemplo:** 8, 12, 40

---

### 5. Start date (Date)

**Propósito:** Fecha de inicio para Gantt chart

**Formato:** YYYY-MM-DD

**Ejemplo:** 2026-01-06

---

### 6. Target date (Date)

**Propósito:** Fecha objetivo para Gantt chart

**Formato:** YYYY-MM-DD

**Ejemplo:** 2026-01-17

---

### 7. Phase (Single Select)

**Opciones:**
- **Extraction** - Extracción de datos de fuentes externas
- **Processing** - Limpieza, normalización, linking
- **Modeling** - Modelos estadísticos y análisis
- **Reporting** - Reportes, dashboards, visualizaciones
- **Tracking** - Monitoreo, mantenimiento, updates

---

### 8. Outcome (Text)

**Propósito:** Texto libre describiendo el resultado esperado

**Ejemplo:** "PostgreSQL + PostGIS operational with schema v2.0 deployed"

---

### 9. Epic (Single Select) ⚠️ IMPORTANTE

**Propósito:** Clasificador de área técnica (NO es para referenciar el issue epic parent)

**Opciones:**
- **DATA** - Database y schema (Blue #0969DA)
- **ETL** - Extractors y pipeline (Purple #8250DF)
- **AN** - Analytics y modelos (Orange #FB8500)
- **VIZ** - Visualizaciones y dashboards (Green #1A7F37)
- **API** - REST API y endpoints (Red #CF222E)
- **INFRA** - Infraestructura y deployment (Gray #656D76)
- **UX** - User experience y diseño (Pink #BF3989)
- **PERF** - Performance y optimización (Yellow #D4A72C)
- **DOCS** - Documentación (Teal #218BFF)

**⚠️ NOTA:** Para referenciar el parent epic issue, usar en el body del issue:
- `Part of #187` (sintaxis de GitHub)
- O en sección "## Parent Epic" con `#187`

---

### 10. Release (Single Select) ⚠️ **CONFIGURAR OPCIONES**

**Opciones requeridas:**
- v2.0 Foundation
- v2.1 Enhanced Analytics
- v2.2 Dashboard Polish
- v2.3 Complete Coverage
- v3.0 Public API
- Backlog
- Future

**Cómo agregar:**
1. GitHub Projects → Click en "Release" field
2. Field settings → Add option
3. Agregar cada opción
4. Save

---

### 11. Quarter (Single Select)

**Opciones:**
- Q1 2026
- Q2 2026

---

### 12. Effort (weeks) (Number)

**Propósito:** Duración estimada en semanas

**Cálculo:** (Target date - Start date) / 7

**Ejemplo:** 1.6 semanas

**Helper script:** `scripts/roadmap/calculate_effort.py`

```bash
python scripts/roadmap/calculate_effort.py 2026-01-06 2026-01-17
# Output: 1.6
```

---

### 13. Sub-issues progress (Progress)

**Tipo:** Auto-tracking (GitHub native)

**Cómo funciona:**
- Se actualiza automáticamente cuando sub-issues se cierran
- Basado en checkboxes en issue body o issues vinculados

---

## Scripts de Automatización

### 1. Popular Campos en Issues Existentes

```bash
./scripts/populate_project_fields.sh
```

**Qué hace:**
- Lee mapeo de issues → campos
- Actualiza issue body con campos estructurados
- Calcula effort automáticamente

---

### 2. Verificar Campos

```bash
./scripts/verify_project_fields.sh
```

**Qué hace:**
- Verifica que todos los epics tengan campos requeridos
- Reporta campos faltantes

---

### 3. Calcular Effort

```bash
python scripts/roadmap/calculate_effort.py 2026-01-06 2026-01-17
# Output: 1.6
```

---

## Ejemplo de Uso Completo

### Crear Epic con Todos los Campos

```bash
gh issue create \
  --title "[EPIC] PostgreSQL Database & Schema v2.0" \
  --body "$(cat <<'EOF'
## 🎯 Goal
Setup PostgreSQL + PostGIS with complete schema v2.0

## 📊 Success Metrics
- Database uptime: ≥99%
- Query performance: <500ms (p95)
- Schema deployed with all tables

## Project Fields
**Start Date:** 2026-01-06
**Target Date:** 2026-01-17
**Epic:** DATA
**Release:** v2.0 Foundation
**Quarter:** Q1 2026
**Phase:** Extraction
**Priority:** P0
**Size:** L
**Estimate:** 12
**Effort (weeks):** 1.6
EOF
)" \
  --label "epic,database,v2.0,p0-critical" \
  --milestone "v2.0 Foundation"
```

---

## Roadmap View Configuration

### Configuración Recomendada

**Group by:** Release  
**Sort by:** Start date  
**Show:** Start date & Target date markers  
**Color by:** Epic

**Resultado:** Gantt chart visual con barras de epics agrupadas por release

---

## Troubleshooting

### Campo no aparece en Roadmap View

**Solución:**
1. Verificar que el campo existe en Project Settings
2. Verificar que las fechas están en formato YYYY-MM-DD
3. Verificar que el issue está agregado al proyecto

### Effort no se calcula automáticamente

**Solución:**
- GitHub Projects no calcula automáticamente
- Usar script `calculate_effort.py` y actualizar manualmente
- O incluir cálculo en `populate_project_fields.sh`

---

## Referencias

- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Roadmap View Setup](docs/ROADMAP_SETUP.md)
- [Project Automation Scripts](scripts/)

---

**Última actualización:** Diciembre 2025

