# Project Management Automation Scripts

Scripts para automatizar la configuración y gestión del GitHub Project Board, milestones, labels e issues.

## 📋 Scripts Disponibles

### 1. `setup_labels.py`

Configura los 34 labels del proyecto según la estrategia definida.

**Uso:**
```bash
# Desde raíz del proyecto
export GITHUB_TOKEN="ghp_tu_token"
python scripts/project_management/setup_labels.py --dry-run  # Verificar
python scripts/project_management/setup_labels.py            # Aplicar
```

**Labels creados:**
- Sprint labels (4): `sprint-1` a `sprint-4`
- Priority labels (4): `priority-critical`, `priority-high`, `priority-medium`, `priority-low`
- Type labels (6): `type-feature`, `type-bug`, `type-refactor`, `type-docs`, `type-test`, `type-chore`
- Status labels (4): `status-blocked`, `status-in-progress`, `status-review`, `status-ready`
- Area labels (6): `area-etl`, `area-ml`, `area-ui`, `area-analytics`, `area-database`, `area-api`
- Special labels (6): `epic`, `sub-issue`, `good-first-issue`, `help-wanted`, `wontfix`, `duplicate`
- Tech labels (4): `dependencies`, `python`, `github-actions`, `docker`

### 2. `setup_milestones.py`

Crea los 4 milestones del roadmap según el plan de sprints.

**Uso:**
```bash
python scripts/project_management/setup_milestones.py --dry-run
python scripts/project_management/setup_milestones.py
```

**Milestones creados:**
- #9: Quick Wins Foundation (Due: 2025-01-31)
- #10: Core ML Engine (Due: 2025-02-28)
- #11: Data Expansion (Due: 2025-04-04)
- #12: Differentiation Showcase (Due: 2025-05-16)

### 3. `create_initial_issues.py`

Crea las 3 issues iniciales del Sprint 1 (Quick Wins).

**Uso:**
```bash
python scripts/project_management/create_initial_issues.py --dry-run
python scripts/project_management/create_initial_issues.py
```

**Issues creadas:**
- #86: [FEATURE-02] Calculadora de Viabilidad de Inversión
- #87: [FEATURE-13] Segmentación Automática de Barrios con K-Means
- #88: [FEATURE-05] Sistema de Notificaciones con Change Detection

### 4. `create_remaining_issues.py`

Crea las 7 issues restantes de los Sprints 2-4.

**Uso:**
```bash
# Crear todas las issues
python scripts/project_management/create_remaining_issues.py --dry-run
python scripts/project_management/create_remaining_issues.py

# Crear solo issues de un sprint específico
python scripts/project_management/create_remaining_issues.py --sprint 2
python scripts/project_management/create_remaining_issues.py --sprint 3
python scripts/project_management/create_remaining_issues.py --sprint 4
```

**Issues creadas:**
- Sprint 2: #89 (POI Analysis), #90 (Temas Light/Dark)
- Sprint 3: #91 (ML Predicción), #92 (Series Temporales)
- Sprint 4: #93 (Accesibilidad), #94 (Calidad Ambiental), #95 (Gentrificación)

### 5. `setup_complete.py`

Script maestro que ejecuta todos los scripts anteriores en orden.

**Uso:**
```bash
python scripts/project_management/setup_complete.py --dry-run
python scripts/project_management/setup_complete.py
```

### 6. `update_labels_extended.py`

Gestión completa de labels del proyecto con todas las categorías del plan completo.

**Comandos disponibles:**

```bash
# Ver labels actuales
python scripts/project_management/update_labels_extended.py list

# Sincronizar todos los labels (dry-run primero)
python scripts/project_management/update_labels_extended.py sync --dry-run
python scripts/project_management/update_labels_extended.py sync

# Exportar documentación a markdown
python scripts/project_management/update_labels_extended.py export [--output docs/labels.md]

# Ver estadísticas de labels
python scripts/project_management/update_labels_extended.py stats

# Limpiar labels obsoletos
python scripts/project_management/update_labels_extended.py clean --dry-run
python scripts/project_management/update_labels_extended.py clean
```

**Labels gestionados (50+ labels):**
- **Sprint labels (6):** `sprint-1` a `sprint-4`, `sprint-backlog`, `sprint-blocked`
- **Priority labels (4):** `priority-critical`, `priority-high`, `priority-medium`, `priority-low`
- **Type labels (7):** `type-feature`, `type-bug`, `type-refactor`, `type-docs`, `type-test`, `type-infra`, `type-research`
- **Area labels (9):** `area-etl`, `area-ml`, `area-analytics`, `area-ui`, `area-api`, `area-database`, `area-geospatial`, `area-monitoring`, `area-extension`
- **Status labels (5):** `status-blocked`, `status-in-progress`, `status-review`, `status-testing`, `status-ready-to-merge`
- **Effort labels (5):** `effort-xs`, `effort-s`, `effort-m`, `effort-l`, `effort-xl`
- **Special labels (9):** `good-first-issue`, `help-wanted`, `breaking-change`, `tech-debt`, `duplicate`, `wontfix`, `future-v2`, `epic`, `sub-issue`
- **Tech labels (4):** `dependencies`, `python`, `github-actions`, `docker`

**Características:**
- ✅ Validación de colores hex
- ✅ Validación de contexto del repositorio
- ✅ Exportación a markdown para documentación
- ✅ Estadísticas por categoría
- ✅ Limpieza de labels obsoletos
- ✅ Modo dry-run para todas las operaciones

## 🔑 Requisitos

### Dependencias Python

```bash
pip install requests
```

Verificar que `requests` esté en `requirements.txt`:
```bash
grep requests requirements.txt
```

### Personal Access Token

Necesitas un GitHub Personal Access Token con permisos:
- ✅ `repo` (Full control)
- ✅ `project` (Full control) - Solo si usas Project Board automation

**Generar token:**
1. Ve a: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Selecciona scopes: `repo`, `project`
4. Copia el token (solo se muestra una vez)

**Configurar token:**
```bash
# Opción 1: Variable de entorno
export GITHUB_TOKEN="ghp_tu_token_aqui"

# Opción 2: GitHub CLI (automático)
gh auth login
```

## 📊 Outputs y Logs

Los scripts generan logs en:
- `data/logs/` (si se implementa logging a archivo)
- Salida estándar (stdout) con resumen de operaciones

## 🔗 Documentación Relacionada

- [Roadmap del Proyecto](../../docs/roadmap.md)
- [Project Management](../../docs/PROJECT_MANAGEMENT.md)
- [Project Charter](../../docs/PROJECT_CHARTER.md)
- [Issue Workflow](../../docs/ISSUE_WORKFLOW.md)

## 🚀 Workflow Recomendado

### Configuración Inicial (Primera vez)

```bash
# 1. Configurar token
export GITHUB_TOKEN="ghp_xxx"

# 2. Crear labels
python scripts/project_management/setup_labels.py

# 3. Crear milestones
python scripts/project_management/setup_milestones.py

# 4. Crear issues Sprint 1
python scripts/project_management/create_initial_issues.py

# 5. Crear issues Sprints 2-4
python scripts/project_management/create_remaining_issues.py
```

### Mantenimiento (Actualizaciones)

```bash
# Actualizar labels si cambia la estrategia
python scripts/project_management/setup_labels.py

# Actualizar milestones si cambian fechas
python scripts/project_management/setup_milestones.py
```

## ⚠️ Notas Importantes

1. **Dry-run siempre primero:** Usa `--dry-run` para verificar cambios antes de aplicarlos
2. **Project Board:** La creación del Project Board debe hacerse manualmente desde GitHub UI (limitación de API)
3. **Idempotencia:** Los scripts son idempotentes - puedes ejecutarlos múltiples veces sin problemas
4. **Rate Limiting:** GitHub tiene rate limits (5000 req/hora para autenticados)

## 🐛 Troubleshooting

### Error: "GITHUB_TOKEN no configurado"
```bash
# Solución: Configurar token
export GITHUB_TOKEN="ghp_xxx"
# O usar gh CLI
gh auth login
```

### Error: "Permission denied"
```bash
# Verificar permisos del token
gh auth status
# Regenerar token con permisos correctos
```

### Error: "Rate limit exceeded"
```bash
# Esperar 1 hora o usar token con más permisos
# Los tokens autenticados tienen límite más alto
```

## 📝 Contribuir

Si añades nuevos scripts de project management:
1. Añádelos a este directorio
2. Actualiza este README
3. Sigue el patrón de logging y error handling existente
4. Incluye `--dry-run` en todos los scripts

