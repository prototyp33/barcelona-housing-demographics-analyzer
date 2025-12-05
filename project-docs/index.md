# Project Docs Index

## Entradas de Cambios

### 2025-12-04 - GitHub Templates Setup

**Archivo:** `.github/ISSUE_TEMPLATE/` structure  
**Descripción:** Configuración de templates para issues y PRs

**Archivos añadidos:**
- `config.yml` - Menú de selección de templates
- `feature_request.md` - Template para nuevas features
- `bug_report.md` - Template para reportar bugs
- `research_task.md` - Template para investigación técnica
- `pull_request_template.md` - Template para PRs

**Propósito:** Estandarizar contribuciones y mejorar calidad de issues  
**Relacionado:** `CONTRIBUTING.md` (a crear en siguiente etapa)

### 2025-12-04 - Issue Templates Content (Etapa 2)

**Archivos:** `.github/ISSUE_TEMPLATE/*.md`

**Descripción:** Contenido completo de templates de issues.

**Templates completados:**
- `feature_request.md` - Template para proponer features
- `bug_report.md` - Template para reportar bugs
- `research_task.md` - Template para investigaciones técnicas

**Características:**
- Frontmatter YAML con labels automáticos
- Comentarios HTML guiando a usuarios
- Checkboxes interactivos para opciones
- Ejemplos específicos del proyecto

**Próximo paso:** PR template y CONTRIBUTING.md (Etapa 3)

### 2025-12-04 - PR Template y CONTRIBUTING.md (Etapa 3)

**Archivos:** `.github/pull_request_template.md`, `.github/CONTRIBUTING.md`

**Descripción:** Templates y guías completas para contribuciones

**PR Template incluye:**
- Descripción del cambio + issue relacionada (`Closes #___`)
- Tipo de cambio (bug/feature/refactor/docs/tests/chore)
- Checklist de Definition of Done (15+ items)
- Instrucciones de testing paso a paso
- Sección de screenshots/demos para UI
- Cambios técnicos detallados (archivos, decisiones, schema)
- Impacto, riesgos y plan de rollback
- Evidencia de testing (pytest, coverage, linter)
- Notas para revisores + checklist de revisor

**CONTRIBUTING.md incluye:**
- Setup completo (Python 3.11+, venv, pip, pytest)
- Flujo Git (branch naming, conventional commits, PR process)
- Convenciones de código (PEP 8, type hints, docstrings Google-style)
- Definition of Done explícita
- Testing y quality assurance (pytest, ruff, coverage ≥25%)
- Guía de code review
- Troubleshooting común

**Relacionado con:** Etapa 2 (issue templates), Sprint 1 objetivos

**Próximo paso:** Etapa 4 (Labels y GitHub Actions)
