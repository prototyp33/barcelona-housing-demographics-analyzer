# 📋 Issues del Sprint 1 - Resumen Completo

## Sprint 1: Foundation Layer

**Semanas:** 1-2 (Dic 9-22, 2025)  
**Capacidad:** 20-30 horas  
**Milestone:** Quick Wins Foundation  
**Total Issues:** 6

---

## Issues Creadas

### Issue #1: [SETUP] Configurar GitHub Project Board
- **Archivo:** `issue-01-setup-project-board.md`
- **Labels:** `sprint-1`, `priority-critical`, `type-infra`, `effort-s`
- **Esfuerzo:** 2 horas
- **Estado:** 📝 Draft creado

### Issue #2: [SETUP] Implementar CI/CD con GitHub Actions
- **Archivo:** `issue-02-setup-cicd.md`
- **Labels:** `sprint-1`, `priority-critical`, `type-infra`, `effort-s`
- **Esfuerzo:** 3 horas
- **Estado:** 📝 Draft creado

### Issue #3: [FEAT-02] Investment Calculator - Core Logic
- **Archivo:** `issue-02-investment-calculator-core.md`
- **Labels:** `sprint-1`, `priority-high`, `type-feature`, `area-analytics`, `effort-m`, `epic`
- **Esfuerzo:** 8 horas
- **Dependencias:** Ninguna
- **Estado:** 📝 Draft creado

### Issue #4: [FEAT-02] Investment Calculator - UI Streamlit
- **Archivo:** `issue-04-investment-calculator-ui.md`
- **Labels:** `sprint-1`, `priority-high`, `type-feature`, `area-ui`, `effort-m`
- **Esfuerzo:** 6 horas
- **Dependencias:** #3 (Core Logic)
- **Estado:** 📝 Draft creado

### Issue #5: [FEAT-02] Investment Calculator - Tests
- **Archivo:** `issue-05-investment-calculator-tests.md`
- **Labels:** `sprint-1`, `priority-high`, `type-test`, `area-analytics`, `effort-s`
- **Esfuerzo:** 3 horas
- **Dependencias:** #3 (Core Logic)
- **Estado:** 📝 Draft creado

### Issue #6: [DOCS] Documentar arquitectura de analytics
- **Archivo:** `issue-06-docs-analytics.md`
- **Labels:** `sprint-1`, `priority-medium`, `type-docs`, `area-analytics`, `effort-s`
- **Esfuerzo:** 2 horas
- **Dependencias:** #3, #4 (Core Logic y UI)
- **Estado:** 📝 Draft creado

---

## Resumen de Esfuerzo

| Issue | Esfuerzo | Prioridad |
|-------|----------|-----------|
| #1 - Project Board | 2h | 🔴 Crítica |
| #2 - CI/CD | 3h | 🔴 Crítica |
| #3 - Calculator Core | 8h | 🟠 Alta |
| #4 - Calculator UI | 6h | 🟠 Alta |
| #5 - Calculator Tests | 3h | 🟠 Alta |
| #6 - Docs Analytics | 2h | 🟡 Media |
| **TOTAL** | **24h** | |

---

## Dependencias

```
#1 (Project Board)
  └─> Ninguna

#2 (CI/CD)
  └─> Ninguna

#3 (Calculator Core)
  └─> Ninguna

#4 (Calculator UI)
  └─> #3 (Calculator Core)

#5 (Calculator Tests)
  └─> #3 (Calculator Core)

#6 (Docs)
  └─> #3 (Calculator Core)
  └─> #4 (Calculator UI)
```

---

## Orden de Ejecución Recomendado

### Semana 1 (Días 1-5)

1. **Día 1:** #1 - Project Board (2h)
2. **Día 1:** #2 - CI/CD (3h)
3. **Día 2-3:** #3 - Calculator Core (8h)

### Semana 2 (Días 6-10)

4. **Día 4-5:** #4 - Calculator UI (6h)
5. **Día 6:** #5 - Calculator Tests (3h)
6. **Día 7:** #6 - Docs (2h)

**Total:** 24 horas distribuidas en 2 semanas

---

## Cómo Crear las Issues en GitHub

### Opción 1: Manual (Recomendado para revisar)

1. Ve a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/new
2. Para cada issue:
   - Copia el contenido del archivo `.md`
   - Pega en el editor de GitHub
   - Los labels se aplicarán automáticamente desde el frontmatter
   - Asigna al milestone "Quick Wins Foundation"

### Opción 2: Script Automático (Próximamente)

Un script puede leer estos archivos y crear las issues automáticamente.

---

## Checklist Pre-Sprint

- [ ] Todas las issues creadas en GitHub
- [ ] Issues asignadas al milestone correcto
- [ ] Labels aplicadas correctamente
- [ ] Dependencias configuradas en GitHub
- [ ] Project Board configurado
- [ ] Issues añadidas al Project Board

---

**Última actualización:** 2025-12-03  
**Sprint 1:** Foundation Layer (6 issues, 24h)

