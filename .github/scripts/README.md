# Scripts de Automatización de GitHub Projects

Scripts para automatizar la gestión de GitHub Projects v2 usando GraphQL API.

## Scripts Disponibles

### 1. `project_automation.py`

Sincroniza issues con GitHub Projects v2 y actualiza campos personalizados.

**Uso básico:**
```bash
# Sincronizar issue con auto-detección
python .github/scripts/project_automation.py --issue 24 --auto-detect

# Sincronizar con campos específicos
python .github/scripts/project_automation.py \
  --issue 24 \
  --impact High \
  --fuente IDESCAT \
  --sprint "Sprint 1" \
  --kpi-objetivo "Extractor funcional con tests pasando"
```

**Opciones:**
- `--issue`: Número del issue (requerido)
- `--impact`: High, Medium, Low
- `--fuente`: IDESCAT, Incasòl, OpenData BCN, Portal Dades, Internal
- `--sprint`: Sprint 1, Sprint 2, etc.
- `--kpi-objetivo`: Descripción del KPI objetivo
- `--auto-detect`: Detecta automáticamente campos desde el issue

### 2. `project_metrics.py`

Genera métricas del proyecto desde Projects v2.

**Uso:**
```bash
# Ver métricas en consola
python .github/scripts/project_metrics.py

# Exportar a JSON
python .github/scripts/project_metrics.py --export-json metrics.json
```

## Configuración

### Variables de Entorno

Los scripts requieren `GITHUB_TOKEN` con permisos:
- `repo` (acceso al repositorio)
- `project` (acceso a Projects v2)
- `workflow` (para workflows de GitHub Actions)

**Obtener token:**
```bash
# Opción 1: Usar gh CLI
gh auth token

# Opción 2: Crear Personal Access Token (PAT)
# GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
# Scopes: repo, project, workflow
```

### Configuración del Proyecto

1. **Obtener PROJECT_NUMBER:**
   - Ve a tu proyecto en GitHub
   - El número está en la URL: `github.com/orgs/ORG/projects/PROJECT_NUMBER`

2. **Verificar campos personalizados:**
   - Los campos deben existir en el proyecto según `docs/PROJECT_MANAGEMENT.md`
   - Campos requeridos: Impacto, Fuente de Datos, Sprint, Estado DQC, Owner, KPI objetivo

## Workflow de GitHub Actions

El workflow `.github/workflows/project-automation.yml` se ejecuta automáticamente cuando:
- Se abre un issue → Lo añade al proyecto con auto-detección
- Se cierra un issue → Registra el evento (GitHub mueve automáticamente a Done)

## Ejemplos de Uso

### Sincronizar múltiples issues

```bash
# Sincronizar issues del Sprint 1
for issue_num in 24 25 26 27; do
  python .github/scripts/project_automation.py \
    --issue $issue_num \
    --sprint "Sprint 1" \
    --auto-detect
done
```

### Generar reporte semanal

```bash
# Generar métricas y guardar
python .github/scripts/project_metrics.py \
  --export-json data/logs/project_metrics_$(date +%Y%m%d).json
```

## Troubleshooting

### Error: "Proyecto no encontrado"
- Verifica que `PROJECT_NUMBER` en el script sea correcto
- Verifica que el token tenga permisos de `project`

### Error: "Campo no encontrado"
- Verifica que los campos existan en el proyecto
- Los nombres deben coincidir exactamente (case-sensitive)

### Error: "Issue ya está en el proyecto"
- Esto es normal, el script intentará actualizar los campos existentes

## Referencias

- [GitHub GraphQL API Docs](https://docs.github.com/en/graphql)
- [Projects v2 API](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/using-the-api-to-manage-projects)
- [Project Management Playbook](../docs/PROJECT_MANAGEMENT.md)

