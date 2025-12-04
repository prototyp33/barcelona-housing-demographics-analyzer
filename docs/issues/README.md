# Issues Drafts

Este directorio contiene borradores de issues antes de crearlas en GitHub.

## 📋 Uso

1. **Crear borrador de issue:**
   ```bash
   cp .github/ISSUE_TEMPLATE.md docs/issues/nueva-issue-draft.md
   ```

2. **Editar el borrador** con tu editor favorito

3. **Validar localmente:**
   ```bash
   python scripts/validate_issues.py docs/issues/nueva-issue-draft.md
   ```

4. **Crear issue en GitHub:**
   ```bash
   gh issue create --title "..." --body-file docs/issues/nueva-issue-draft.md
   ```

5. **Mover a archivado** después de crear:
   ```bash
   mv docs/issues/nueva-issue-draft.md docs/issues/archived/
   ```

## 📁 Estructura

```
docs/issues/
├── README.md (este archivo)
├── nueva-issue-draft.md (ejemplo)
└── archived/ (issues ya creadas en GitHub)
```

## ✅ Validación

Todas las issues deben pasar la validación antes de crearse:

- ✅ Tiene sección "Objetivo" o "Descripción"
- ✅ Tiene "Criterios de Aceptación" con checkboxes
- ✅ Tiene estimación de tiempo numérica
- ✅ Sigue formato [TIPO] en título (recomendado)

Ver: [Mejores Prácticas](../BEST_PRACTICES_GITHUB_ISSUES.md)

