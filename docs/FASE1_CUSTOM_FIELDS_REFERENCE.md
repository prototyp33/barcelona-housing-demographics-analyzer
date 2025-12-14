# Fase 1: Custom Fields Reference

**Fecha:** Diciembre 2025  
**Propósito:** Configurar custom fields en GitHub Projects UI después de crear issues

---

## 📋 Instrucciones

1. Ejecutar `scripts/create_fase_1_issues.sh` para crear todas las issues
2. Ir a **GitHub Projects** → "Barcelona Housing - Roadmap"
3. Para cada issue, configurar los campos según la tabla abajo
4. Usar este documento como referencia rápida

---

## 📊 Custom Fields por Issue

### Epic Principal: [EPIC] Fase 1: Database Infrastructure

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | XL |
| **Estimate** | 49 |
| **Epic** | DATA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-06 |
| **Target Date** | 2026-01-17 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 1.2 |
| **Outcome** | PostgreSQL schema v2.0 operational with 8 fact + 2 dim tables |

---

### DATA-101: Create 8 fact tables

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | L |
| **Estimate** | 8 |
| **Epic** | DATA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-06 |
| **Target Date** | 2026-01-08 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.3 |
| **Outcome** | 8 fact tables created and validated |

---

### DATA-102: Create 2 dimension tables

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | L |
| **Estimate** | 6 |
| **Epic** | DATA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-06 |
| **Target Date** | 2026-01-08 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.3 |
| **Outcome** | 2 dimension tables created and populated |

---

### DATA-103: Create indexes and foreign key constraints

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | M |
| **Estimate** | 4 |
| **Epic** | DATA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-09 |
| **Target Date** | 2026-01-09 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.1 |
| **Outcome** | Indexes created, query performance <100ms |

---

### DATA-104: Update schema.sql with v2.0 changes

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | M |
| **Estimate** | 4 |
| **Epic** | DATA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-10 |
| **Target Date** | 2026-01-10 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.1 |
| **Outcome** | schema.sql v2.0 complete with migration scripts |

---

### INFRA-101: Setup PostgreSQL testing database on Render

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P0 |
| **Size** | M |
| **Estimate** | 3 |
| **Epic** | INFRA |
| **Release** | v2.0 Foundation |
| **Phase** | Infrastructure |
| **Start Date** | 2026-01-10 |
| **Target Date** | 2026-01-10 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.1 |
| **Outcome** | PostgreSQL+PostGIS test DB operational on Render |

---

### DOCS-101: Document schema v2.0 in architecture docs

| Campo | Valor |
|-------|-------|
| **Status** | Backlog |
| **Priority** | P1 |
| **Size** | S |
| **Estimate** | 2 |
| **Epic** | DOCS |
| **Release** | v2.0 Foundation |
| **Phase** | Documentation |
| **Start Date** | 2026-01-13 |
| **Target Date** | 2026-01-13 |
| **Quarter** | Q1 2026 |
| **Effort (weeks)** | 0.1 |
| **Outcome** | DATABASE_SCHEMA_V2.md complete with ER diagram |

---

## 📈 Resumen de Esfuerzo

| Issue | Horas | Semanas | Fecha Inicio | Fecha Fin |
|-------|-------|---------|--------------|-----------|
| Epic | 49 | 1.2 | 2026-01-06 | 2026-01-17 |
| DATA-101 | 8 | 0.3 | 2026-01-06 | 2026-01-08 |
| DATA-102 | 6 | 0.3 | 2026-01-06 | 2026-01-08 |
| DATA-103 | 4 | 0.1 | 2026-01-09 | 2026-01-09 |
| DATA-104 | 4 | 0.1 | 2026-01-10 | 2026-01-10 |
| INFRA-101 | 3 | 0.1 | 2026-01-10 | 2026-01-10 |
| DOCS-101 | 2 | 0.1 | 2026-01-13 | 2026-01-13 |
| **TOTAL** | **27** | **1.0** | - | - |

**Nota:** El Epic tiene 49h porque incluye overhead, coordinación, y buffer.

---

## 🔍 Búsqueda Rápida en GitHub Projects

Para encontrar issues rápidamente:

```bash
# Epic
gh issue list --label epic --milestone "Fase 1: Database Infrastructure"

# Sub-issues
gh issue list --milestone "Fase 1: Database Infrastructure" --label "user-story"
```

---

## 📝 CSV Source

Los datos originales están en: `data/reference/fase1_custom_fields.csv`

---

**Última actualización:** Diciembre 2025

