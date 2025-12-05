# 🏷️ Gestión de Labels - Guía Completa

## Visión General

Este documento describe el sistema completo de gestión de labels del proyecto Barcelona Housing Demographics Analyzer.

## 📋 Comandos Disponibles

### Ver Labels Actuales

```bash
python scripts/project_management/update_labels_extended.py list
```

### Sincronizar Labels

```bash
# Dry-run primero (recomendado)
python scripts/project_management/update_labels_extended.py sync --dry-run

# Sincronizar de verdad
python scripts/project_management/update_labels_extended.py sync
```

### Exportar Documentación

```bash
python scripts/project_management/update_labels_extended.py export [--output docs/labels.md]
```

### Ver Estadísticas

```bash
python scripts/project_management/update_labels_extended.py stats
```

### Limpiar Labels Obsoletos

```bash
# Dry-run primero
python scripts/project_management/update_labels_extended.py clean --dry-run

# Eliminar de verdad
python scripts/project_management/update_labels_extended.py clean
```

## 🏷️ Categorías de Labels

### Sprint Labels (6 labels)

Organizan el trabajo por período de tiempo.

| Label | Color | Descripción |
|-------|-------|-------------|
| `sprint-1` | Verde | Semanas 1-4: Quick Wins Foundation |
| `sprint-2` | Azul | Semanas 5-10: Core ML Engine |
| `sprint-3` | Morado | Semanas 11-18: Data Expansion |
| `sprint-4` | Naranja | Semanas 19-24: Differentiation Showcase |
| `sprint-backlog` | Gris | Post-v1.0.0 features |
| `sprint-blocked` | Rojo | Bloqueado por dependencias externas |

**Uso:** Cada issue DEBE tener exactamente un label de sprint.

### Priority Labels (4 labels)

Indican urgencia e importancia.

| Label | Color | Descripción |
|-------|-------|-------------|
| `priority-critical` | Rojo oscuro | 🔥 Bloqueante para milestone, resolver inmediatamente |
| `priority-high` | Naranja | ⬆️ Alta prioridad, completar en sprint actual |
| `priority-medium` | Amarillo | ➡️ Media prioridad, planificar para siguiente sprint |
| `priority-low` | Verde | ⬇️ Baja prioridad, nice-to-have |

**Uso:** Cada issue DEBE tener exactamente un label de prioridad.

### Type Labels (7 labels)

Categorizan el tipo de trabajo.

| Label | Color | Descripción |
|-------|-------|-------------|
| `type-feature` | Azul | ✨ Nueva funcionalidad |
| `type-bug` | Rojo | 🐛 Error a corregir |
| `type-refactor` | Azul claro | ♻️ Mejora técnica sin cambio funcional |
| `type-docs` | Azul | 📝 Documentación |
| `type-test` | Azul claro | 🧪 Testing y QA |
| `type-infra` | Rosa | ⚙️ Infraestructura y DevOps |
| `type-research` | Amarillo claro | 🔬 Spike/investigación técnica |

**Uso:** Cada issue DEBE tener exactamente un label de tipo.

### Area Labels (9 labels)

Indican el área técnica afectada.

| Label | Color | Descripción |
|-------|-------|-------------|
| `area-etl` | Morado claro | 📊 Pipeline de extracción y carga |
| `area-ml` | Verde claro | 🤖 Machine Learning y modelos |
| `area-analytics` | Azul claro | 📈 Lógica de negocio y cálculos |
| `area-ui` | Amarillo claro | 🎨 Interfaz Streamlit |
| `area-api` | Azul muy claro | 🔌 API REST FastAPI |
| `area-database` | Verde muy claro | 💾 Esquema y queries SQLite |
| `area-geospatial` | Naranja claro | 🗺️ Datos geo-espaciales y mapas |
| `area-monitoring` | Naranja muy claro | 🔔 Alertas y observabilidad |
| `area-extension` | Rosa claro | 🧩 Chrome Extension |

**Uso:** Las issues pueden tener múltiples labels de área.

### Status Labels (5 labels)

Indican el estado del workflow.

| Label | Color | Descripción |
|-------|-------|-------------|
| `status-blocked` | Rojo oscuro | 🚫 Bloqueado por dependencia |
| `status-in-progress` | Amarillo | 🔄 En desarrollo activo |
| `status-review` | Cian | 👀 Listo para code review |
| `status-testing` | Azul claro | 🧪 En fase de testing |
| `status-ready-to-merge` | Verde | ✅ Aprobado, listo para merge |

**Uso:** Actualizado automáticamente por GitHub Actions o manualmente.

### Effort Labels (5 labels)

Estimación de tiempo (t-shirt sizes).

| Label | Color | Descripción |
|-------|-------|-------------|
| `effort-xs` | Verde muy claro | ⏱️ <2 horas |
| `effort-s` | Verde claro | ⏱️ 2-5 horas |
| `effort-m` | Verde medio | ⏱️ 5-10 horas |
| `effort-l` | Verde oscuro | ⏱️ 10-20 horas |
| `effort-xl` | Verde muy oscuro | ⏱️ >20 horas (considerar dividir) |

**Uso:** Opcional pero recomendado para estimación.

### Special Labels (9 labels)

Casos especiales.

| Label | Color | Descripción |
|-------|-------|-------------|
| `good-first-issue` | Morado | 👍 Ideal para comenzar |
| `help-wanted` | Verde azulado | 🙋 Necesita input externo |
| `breaking-change` | Rojo | 💥 Rompe compatibilidad |
| `tech-debt` | Rosa | 🏗️ Deuda técnica a refactorizar |
| `duplicate` | Gris | 👥 Duplicado de otro issue |
| `wontfix` | Blanco | ❌ No se implementará |
| `future-v2` | Gris claro | 🔮 Post-v1.0.0 |
| `epic` | Morado oscuro | 🎯 Feature principal del roadmap |
| `sub-issue` | Gris claro | 📌 Sub-tarea de una epic |

**Uso:** Usar con moderación para casos especiales.

### Tech Labels (4 labels)

Tecnologías específicas.

| Label | Color | Descripción |
|-------|-------|-------------|
| `dependencies` | Azul | 📦 Actualizaciones de dependencias |
| `python` | Azul oscuro | 🐍 Relacionado con Python |
| `github-actions` | Azul | ⚙️ GitHub Actions / CI-CD |
| `docker` | Azul | 🐳 Docker y contenedores |

**Uso:** Opcional, para identificar tecnologías específicas.

## 📏 Convenciones de Naming

### Reglas

1. **Siempre minúsculas**
2. **Usar guiones para espacios** (kebab-case)
3. **Prefijo con categoría** (ej: `sprint-`, `priority-`)
4. **Descriptivo pero conciso**

### Ejemplos

✅ **Correcto:**
- `sprint-1`
- `priority-high`
- `area-ml`
- `type-feature`

❌ **Incorrecto:**
- `Sprint-1` (mayúscula)
- `priority_high` (underscore)
- `ML` (sin prefijo)
- `feature` (sin prefijo)

## 🤖 Automatización

### GitHub Actions

Los labels se sincronizan automáticamente cuando:
- Se modifica `scripts/project_management/update_labels_extended.py`
- Se ejecuta manualmente desde GitHub Actions UI

**Workflow:** `.github/workflows/sync_labels.yml`

### Documentación Auto-generada

El archivo `docs/labels.md` se genera automáticamente y **NO debe editarse manualmente**.

**Nota:** `docs/labels.md` está en `.gitignore` para evitar commits accidentales.

## 🔍 Troubleshooting

### Problema: GITHUB_TOKEN no configurado

**Solución 1: Usar gh CLI**
```bash
gh auth login
export GITHUB_TOKEN=$(gh auth token)
```

**Solución 2: Crear token manualmente**
1. Ir a https://github.com/settings/tokens/new
2. Scopes necesarios: `repo`, `workflow`
3. Exportar: `export GITHUB_TOKEN="ghp_xxxx"`

**Solución 3: Añadir a shell profile**
```bash
echo 'export GITHUB_TOKEN="ghp_xxxx"' >> ~/.zshrc
source ~/.zshrc
```

### Problema: Rate Limiting

El script incluye rate limiting automático (200ms entre requests).

Si aún así recibes errores:
```bash
# Verificar límite actual
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit
```

**Solución:** Esperar 1 hora o usar un token con más permisos.

### Problema: Labels Duplicados

Si hay labels duplicados con diferentes casos:

1. Listar todos:
```bash
python scripts/project_management/update_labels_extended.py list | grep -i "priority"
```

2. Limpiar manualmente en GitHub UI:
   https://github.com/prototyp33/barcelona-housing-demographics-analyzer/labels

3. Re-sincronizar:
```bash
python scripts/project_management/update_labels_extended.py sync
```

## ✅ Checklist de Validación

Después de sincronizar labels:

- [ ] Script ejecuta sin errores en dry-run
- [ ] Script ejecuta sin errores en modo real
- [ ] GitHub muestra 50+ labels correctamente
- [ ] Colores son consistentes con el plan
- [ ] Descripciones tienen emojis correctos
- [ ] `docs/labels.md` generado correctamente
- [ ] GitHub Action configurado y funcionando
- [ ] Documentación en README actualizada

## 📚 Referencias

- [GitHub Labels API](https://docs.github.com/en/rest/issues/labels)
- [Project Management Scripts](../scripts/project_management/README.md)
- [Sprint Planning Complete](SPRINT_PLANNING_COMPLETE.md)

---

**Última actualización:** 2025-12-03  
**Total de labels:** 50+ organizados en 8 categorías
