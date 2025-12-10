# 🚀 Guía de Configuración del Proyecto

## Requisitos previos

1. **GitHub Token con permisos:**
   ```bash
   # Crear token en: https://github.com/settings/tokens
   # Permisos necesarios:
   # - repo (full access)
   # - project (read/write)
   # - admin:org (si es organización)
   
   export GITHUB_TOKEN="ghp_tu_token_aqui"
   ```

2. **Instalar dependencias:**
   ```bash
   pip install PyGithub requests
   ```

## Paso 1: Configuración base

```bash
python .github/scripts/setup_project_complete.py
```

**Esto configurará:**
- ✅ 30+ labels categorizados
- ✅ 7 milestones con fechas
- ✅ Instrucciones para campos personalizados
- ✅ Instrucciones para vistas
- ✅ Verificación de templates

**Sigue las instrucciones en pantalla** para configurar:
- Campos personalizados en Project v2
- Vistas del proyecto
- Automatizaciones built-in

## Paso 2: Crear issues iniciales

```bash
python .github/scripts/create_sprint_issues.py
```

**Esto creará:**
- 3 issues del Sprint 1 completamente configuradas
- Con labels, milestone y descripción completa

## Paso 3: Vincular issues al proyecto

### Opción A: Manualmente

1. Ve a tu proyecto
2. Click en "+ Add item"
3. Busca las issues por número
4. Configura campos personalizados

### Opción B: Automáticamente (recomendado)

```bash
# Sincronizar issue individual
python .github/scripts/project_automation.py --issue 24 --auto-detect

# O sincronizar múltiples issues
for issue_num in 24 25 26; do
  python .github/scripts/project_automation.py --issue $issue_num --auto-detect
done
```

## Paso 4: Verificar configuración

### Checklist:

- [ ] Labels creados y visibles en Issues
- [ ] Milestones creados con fechas
- [ ] Proyecto tiene campos personalizados configurados
- [ ] Vistas del proyecto creadas (Board, Table, Roadmap)
- [ ] Automatizaciones activadas
- [ ] Issues del Sprint 1 creadas y vinculadas
- [ ] Workflows de GitHub Actions activos

### Verificación visual:

```bash
# Ver labels
gh label list

# Ver milestones
gh milestone list

# Ver issues
gh issue list --label sprint-1
```

## Configuración recomendada del proyecto

### Campos personalizados:

1. **Impacto** (Single select): High, Medium, Low
2. **Fuente de Datos** (Single select): IDESCAT, Incasòl, etc.
3. **Sprint** (Iteration): Sprints de 2 semanas
4. **Estado DQC** (Single select): Pending, Passed, Failed
5. **Owner** (Text)
6. **KPI Objetivo** (Text)
7. **Confidence** (Number): 0-100

### Vistas recomendadas:

1. **Sprint Board**: Board agrupado por Status
2. **Planning View**: Table agrupada por Sprint
3. **Roadmap**: Timeline por Iterations
4. **Quality Tracking**: Table filtrada por DQC

### Automatizaciones:

1. **Built-in**: Auto-move to Done when closed
2. **Built-in**: Auto-archive after 30 days
3. **GitHub Actions**: AI PM audit (daily)
4. **GitHub Actions**: DQC updates (on PR)
5. **GitHub Actions**: Metrics dashboard (daily)

## Troubleshooting

### Error: "Project not found"

- Verifica que `PROJECT_NUMBER` sea correcto
- Para usuario personal: el proyecto debe estar en tu perfil
- Para organización: el proyecto debe estar en la organización

### Error: "Insufficient permissions"

- Token necesita `project` scope
- Para org: necesita `admin:org`

### Issues no se añaden al proyecto

- Añade label "roadmap" para auto-add
- O usa script de sincronización manual

## Próximos pasos

1. ✅ Completa configuración del proyecto
2. 📋 Revisa issues del Sprint 1
3. 🏃 Comienza desarrollo
4. 📊 Monitorea métricas en dashboard
5. 🔄 Itera según feedback de AI PM

