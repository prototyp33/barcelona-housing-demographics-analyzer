# Epic Field - Guía de Uso Correcto

**Fecha:** Diciembre 2025

---

## ⚠️ Confusión Común

El campo **Epic** en GitHub Projects es un **clasificador de área técnica**, NO es para referenciar el número del issue epic parent.

---

## Epic Field = Categoría Técnica

El campo "Epic" es similar a un label estructurado que clasifica el trabajo por área técnica:

| Valor | Descripción | Color |
|-------|-------------|-------|
| **DATA** | Database, schema, models | Blue #0969DA |
| **ETL** | Extractors, pipelines, data loading | Purple #8250DF |
| **AN** | Analytics, statistical models | Orange #FB8500 |
| **VIZ** | Visualizations, dashboards | Green #1A7F37 |
| **API** | REST API y endpoints | Red #CF222E |
| **INFRA** | Infrastructure, DevOps, CI/CD | Gray #656D76 |
| **UX** | User experience, design | Pink #BF3989 |
| **PERF** | Performance optimization | Yellow #D4A72C |
| **DOCS** | Documentation | Teal #218BFF |

### Ejemplos de Uso

- Issue: "Create fact_precios table" → **Epic: DATA**
- Issue: "Build INE extractor" → **Epic: ETL**
- Issue: "Implement hedonic model" → **Epic: AN**
- Issue: "Market Cockpit page" → **Epic: VIZ**

---

## Parent Epic = Referencia en Body del Issue

Para referenciar el issue epic parent, debes hacerlo en el **body del issue**, NO en el custom field.

### Opción 1: Sintaxis de GitHub (Recomendado)

```markdown
Part of #187
```

Esto crea un link automático y GitHub mostrará la relación en la UI.

### Opción 2: Sección Explícita

```markdown
## Parent Epic

#187
```

### Opción 3: En Sección Relacionado

```markdown
## 🔗 Relacionado

Part of #187

**Depends on:** #188, #189
```

---

## Ejemplo Completo: Sub-Issue de Fase 1

### Issue Body

```markdown
## 📋 Objetivo
Crear las 8 nuevas tablas fact para la expansión de arquitectura v2.0.

## 🎯 Criterios de Aceptación
- [ ] fact_desempleo creada con constraints FK
- [ ] fact_educacion creada con constraints FK
- ...

## 🔗 Relacionado
Part of #187

**Depends on:** #188, #189

## Project Fields
**Epic:** DATA (categoría técnica)
**Start Date:** 2026-01-06
**Target Date:** 2026-01-09
```

### Custom Fields en GitHub Projects UI

| Campo | Valor |
|-------|-------|
| **Epic** | DATA |
| **Start Date** | 2026-01-06 |
| **Target Date** | 2026-01-09 |
| **Priority** | P0 |
| **Status** | Backlog |

---

## Scripts Actualizados

Los scripts ahora usan correctamente:

1. **Epic Field:** Categoría técnica (DATA, ETL, AN, etc.)
2. **Body del Issue:** `Part of #EPIC_NUMBER` para referenciar parent epic

### Ejemplo en Script

```bash
gh issue create \
  --title "[FASE 1.1] Create 8 New Fact Tables" \
  --body "$(cat <<EOF
## 📋 Objetivo
...

## 🔗 Relacionado
Part of #187

## Project Fields
**Epic:** DATA (categoría técnica)
EOF
)"
```

---

## Verificación

Para verificar que un issue está correctamente vinculado:

1. **Parent Epic Link:** Ver en el body del issue → `Part of #187`
2. **Epic Field:** Ver en GitHub Projects → Campo "Epic" = DATA
3. **GitHub UI:** El parent epic mostrará los sub-issues automáticamente

---

## Referencias

- **GitHub Docs:** [Linking Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- **Project Fields Guide:** `docs/GITHUB_PROJECTS_FIELDS_GUIDE.md`
- **Fase 1 Setup:** `docs/FASE1_SETUP_INSTRUCTIONS.md`

---

**Última actualización:** Diciembre 2025

