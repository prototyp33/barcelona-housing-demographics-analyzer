# Crear Issues de GitHub Automáticamente

El script `create_github_issues.py` parsea `docs/ISSUES_TO_CREATE.md` y crea issues en GitHub automáticamente.

## Requisitos Previos

1. **GitHub CLI instalado y autenticado:**
   ```bash
   gh auth login
   ```

2. **Repositorio configurado:**
   Asegúrate de estar en el directorio del repositorio y que `gh` esté configurado correctamente.

## Uso

```bash
python3 scripts/create_github_issues.py
```

El script:
- Parsea `docs/ISSUES_TO_CREATE.md`
- Extrae información de cada issue (título, descripción, labels, prioridad)
- Crea los issues en GitHub usando la CLI
- Muestra el progreso y URLs de los issues creados

## Estructura del Markdown

El script espera el siguiente formato en `docs/ISSUES_TO_CREATE.md`:

```markdown
### N. Tipo: Título
**Labels**: `label1`, `label2`  
**Prioridad**: `high|medium|low`  
**Milestone**: Milestone X (opcional)

**Descripción**:
Texto de descripción...

**Tareas**:
- [ ] Tarea 1
- [ ] Tarea 2

**Aceptación**:
Criterios de aceptación...
```

## Notas

- El script crea labels automáticamente si no existen (requiere permisos de repo)
- Las prioridades se mapean a labels: `priority:high`, `priority:medium`, `priority:low`
- Si un issue ya existe con el mismo título, GitHub mostrará un error (puedes ignorarlo)
