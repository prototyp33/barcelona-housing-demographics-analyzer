# 📊 Configuración de GitHub Project Board

Este documento describe cómo configurar los campos personalizados del Project Board "SPIKE BCN Housing - product" para las issues del milestone Q1 2026.

## 🔐 Requisitos Previos

### 1. Autenticación con scopes necesarios

```bash
# Refrescar autenticación con scopes de Projects
gh auth refresh -s read:project -s write:project
```

### 2. Obtener Project ID

```bash
# Listar projects disponibles
gh project list --owner prototyp33

# Obtener Project ID específico
PROJECT_ID=$(gh project list --owner prototyp33 --format json | \
  jq -r '.[] | select(.title=="SPIKE BCN Housing - product") | .id')
echo "Project ID: $PROJECT_ID"
```

## 📋 Configuración de Campos

### Campos Disponibles

| Campo | Tipo | Valores |
|-------|------|---------|
| **Status** | Single Select | Backlog, Ready, In Progress, In Review, Done, Blocked, Archived |
| **Priority** | Single Select | Critical, High, Medium, Low, Frozen |
| **Size** | Single Select | XS, S, M, L, XL, XXL |
| **Estimate** | Number | Días estimados (1-20) |
| **Start Date** | Date | Fecha de inicio (YYYY-MM-DD) |
| **Target Date** | Date | Fecha objetivo (YYYY-MM-DD) |
| **Phase** | Single Select | Research, Foundation, Development, Enhancement, Bug Fix, Documentation, Testing, Launch, Maintenance |
| **Effort (weeks)** | Number | Semanas estimadas (0.5-4) |
| **Quarter** | Single Select | Q1 2026, Q2 2026, Q3 2026, Q4 2026 |
| **Release** | Single Select | v0.3.0-alpha.1, v0.3.0-alpha.2, v0.3.0-beta.1, v0.3.0 |

## 🎯 Configuración por Issue

### Sprint 1 (Issues #245-#247)

#### Issue #245: Educación
```yaml
Status: Ready
Priority: High
Size: M (5 SP)
Estimate: 3 días
Start Date: 2026-01-07
Target Date: 2026-01-14
Phase: Development
Effort (weeks): 1.0
Quarter: Q1 2026
Release: v0.3.0-alpha.1
```

#### Issue #246: Movilidad
```yaml
Status: Ready
Priority: High
Size: L (8 SP)
Estimate: 5 días
Start Date: 2026-01-15
Target Date: 2026-01-24
Phase: Development
Effort (weeks): 1.5
Quarter: Q1 2026
Release: v0.3.0-alpha.1
```

#### Issue #247: Vivienda Pública
```yaml
Status: Backlog
Priority: Medium
Size: M (5 SP)
Estimate: 3 días
Start Date: 2026-01-27
Target Date: 2026-02-07
Phase: Development
Effort (weeks): 1.0
Quarter: Q1 2026
Release: v0.3.0-alpha.2
```

### Sprint 2 (Issues #248-#250)

#### Issue #248: Zonas Verdes
```yaml
Status: Backlog
Priority: Medium
Size: S (3 SP)
Estimate: 2 días
Start Date: 2026-02-03
Target Date: 2026-02-14
Phase: Development
Effort (weeks): 0.5
Quarter: Q1 2026
Release: v0.3.0-alpha.2
```

#### Issue #249: Salud
```yaml
Status: Backlog
Priority: Medium
Size: S (3 SP)
Estimate: 2 días
Start Date: 2026-02-03
Target Date: 2026-02-10
Phase: Development
Effort (weeks): 0.5
Quarter: Q1 2026
Release: v0.3.0-alpha.2
```

#### Issue #250: Contaminación Aire
```yaml
Status: Backlog
Priority: Medium
Size: M (5 SP)
Estimate: 5 días
Start Date: 2026-02-03
Target Date: 2026-02-14
Phase: Development
Effort (weeks): 1.0
Quarter: Q1 2026
Release: v0.3.0-alpha.2
```

### Sprint 3 (Issues #251-#253)

#### Issue #251: Comercio
```yaml
Status: Backlog
Priority: Medium
Size: M (4 SP)
Estimate: 2.5 días
Start Date: 2026-02-17
Target Date: 2026-02-21
Phase: Development
Effort (weeks): 0.5
Quarter: Q1 2026
Release: v0.3.0-beta.1
```

#### Issue #252: Dashboard Integration
```yaml
Status: Backlog
Priority: Critical
Size: L (8 SP)
Estimate: 5 días
Start Date: 2026-02-24
Target Date: 2026-03-07
Phase: Enhancement
Effort (weeks): 1.5
Quarter: Q1 2026
Release: v0.3.0-beta.1
```

#### Issue #253: ETL Automation
```yaml
Status: Backlog
Priority: High
Size: M (5 SP)
Estimate: 5 días
Start Date: 2026-02-24
Target Date: 2026-03-07
Phase: Development
Effort (weeks): 1.0
Quarter: Q1 2026
Release: v0.3.0-beta.1
```

### Sprint 4 (Issues #254-#255)

#### Issue #254: Catastro
```yaml
Status: Backlog
Priority: Low
Size: XL (13 SP)
Estimate: 8 días
Start Date: 2026-03-10
Target Date: 2026-03-24
Phase: Development
Effort (weeks): 2.0
Quarter: Q1 2026
Release: v0.3.0
```

#### Issue #255: Documentación Final
```yaml
Status: Backlog
Priority: High
Size: M (5 SP)
Estimate: 3 días
Start Date: 2026-03-24
Target Date: 2026-03-31
Phase: Documentation
Effort (weeks): 1.0
Quarter: Q1 2026
Release: v0.3.0
```

## 🚀 Métodos de Configuración

### Método 1: Script Automático (Recomendado)

```bash
# 1. Refrescar autenticación
gh auth refresh -s read:project -s write:project

# 2. Ejecutar script
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
bash scripts/configure_project_fields.sh
```

### Método 2: Configuración Manual vía GitHub UI

1. Ir a: https://github.com/users/prototyp33/projects
2. Seleccionar project "SPIKE BCN Housing - product"
3. Para cada issue (#245-#255):
   - Hacer clic en la issue
   - Editar campos en el panel lateral
   - Guardar cambios

### Método 3: GraphQL API Directa

```bash
# Ejemplo para Issue #245
PROJECT_ID="<project_id>"
ITEM_ID="<item_id>"
FIELD_ID="<field_id>"

gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(
      input: {
        projectId: "'$PROJECT_ID'"
        itemId: "'$ITEM_ID'"
        fieldId: "'$FIELD_ID'"
        value: {
          singleSelectOptionId: "<option_id>"
        }
      }
    ) {
      projectV2Item {
        id
      }
    }
  }
'
```

## 📊 Resumen de Configuración

| Issue | Status | Priority | Size | Estimate | Effort | Release |
|-------|--------|----------|------|----------|--------|---------|
| #245 | Ready | High | M | 3 días | 1.0 sem | v0.3.0-alpha.1 |
| #246 | Ready | High | L | 5 días | 1.5 sem | v0.3.0-alpha.1 |
| #247 | Backlog | Medium | M | 3 días | 1.0 sem | v0.3.0-alpha.2 |
| #248 | Backlog | Medium | S | 2 días | 0.5 sem | v0.3.0-alpha.2 |
| #249 | Backlog | Medium | S | 2 días | 0.5 sem | v0.3.0-alpha.2 |
| #250 | Backlog | Medium | M | 5 días | 1.0 sem | v0.3.0-alpha.2 |
| #251 | Backlog | Medium | M | 2.5 días | 0.5 sem | v0.3.0-beta.1 |
| #252 | Backlog | Critical | L | 5 días | 1.5 sem | v0.3.0-beta.1 |
| #253 | Backlog | High | M | 5 días | 1.0 sem | v0.3.0-beta.1 |
| #254 | Backlog | Low | XL | 8 días | 2.0 sem | v0.3.0 |
| #255 | Backlog | High | M | 3 días | 1.0 sem | v0.3.0 |

**Total:** 60 Story Points = 36 días = 7.2 semanas

## 🔍 Verificación

```bash
# Ver issues en el project
gh project view <project_id> --owner prototyp33

# Ver campos de una issue específica
gh issue view 245 --repo prototyp33/barcelona-housing-demographics-analyzer
```

## 📝 Notas

- Los campos personalizados pueden requerir configuración manual si no existen en el project
- Algunos campos (como "Outcome" y "Epic") pueden requerir creación previa en GitHub
- El script automático intenta configurar todos los campos, pero puede fallar si faltan permisos o campos no existen
