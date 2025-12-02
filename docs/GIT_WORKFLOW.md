# Git Workflow - Feature Branches

**Última actualización:** 2025-12-02

Esta guía describe el flujo de trabajo con feature branches para el proyecto Barcelona Housing Demographics Analyzer.

---

## 🎯 Objetivo

Mantener `main` estable y funcional mientras trabajamos en features, fixes y mejoras en branches separadas que se integran vía Pull Requests.

---

## 📋 Convenciones de Nombres

### Formato Estándar
```
<tipo>/<issue-number>-<descripcion-corta>
```

### Tipos de Branches

| Tipo | Uso | Ejemplo |
|------|-----|---------|
| `feature/` | Nueva funcionalidad | `feature/52-validation-pipes-duplicados` |
| `fix/` | Corrección de bug | `fix/49-regex-household-size` |
| `refactor/` | Refactorización | `refactor/43-limpiar-orquestador-pipeline` |
| `etl/` | Trabajo ETL específico | `etl/idescat-extractor-integration` |
| `dashboard/` | Mejoras del dashboard | `dashboard/affordability-index-viz` |
| `docs/` | Documentación | `docs/audit-reciente-github-issues` |
| `test/` | Tests | `test/fact-precios-deduplication` |

---

## 🚀 Flujo de Trabajo Paso a Paso

### 1. Crear Feature Branch desde Issue

**Opción A: Usando script automático (recomendado)**
```bash
./scripts/git/create_feature_branch.sh <issue_number> [type]
```

**Ejemplo:**
```bash
./scripts/git/create_feature_branch.sh 49 fix
# Crea: fix/49-regex-household-size
```

**Opción B: Manualmente**
```bash
git checkout main
git pull origin main
git checkout -b fix/49-regex-household-size
```

---

### 2. Trabajar en la Branch

**Hacer commits pequeños y frecuentes:**
```bash
# Formato de mensaje: tipo(scope): descripción
git add src/etl/transformations/utils.py
git commit -m "fix(etl): Corregir regex en _parse_household_size

- Cambiar r'\\d+' por r'\d+' en líneas 46, 52, 58
- Añadir validación para valores edge case

Fixes #49"

# Más cambios...
git add tests/test_utils.py
git commit -m "test(etl): Añadir test para regex corregido"
```

**Tipos de commits:**
- `fix`: Corrección de bug
- `feat`: Nueva funcionalidad
- `docs`: Documentación
- `test`: Tests
- `refactor`: Refactorización
- `style`: Formato (sin cambios lógicos)
- `etl`: Cambios específicos de ETL

---

### 3. Mantener Branch Actualizada

**Sincronizar con main periódicamente:**
```bash
# Opción A: Usando script (recomendado)
./scripts/git/sync_with_main.sh

# Opción B: Manualmente
git fetch origin
git rebase origin/main
```

**Si hay conflictos:**
```bash
# 1. Resolver conflictos en archivos marcados
# 2. Añadir archivos resueltos
git add archivo_resuelto.py
# 3. Continuar rebase
git rebase --continue
```

---

### 4. Push y Crear Pull Request

**Push de la branch:**
```bash
git push origin fix/49-regex-household-size
```

**Crear PR:**
```bash
# Opción A: Usando script (recomendado)
./scripts/git/create_pr.sh

# Opción B: Manualmente con gh CLI
gh pr create --title "Fix: Corregir regex en _parse_household_size (#49)" \
  --body "Fixes #49" \
  --label "bug,etl,priority-medium"

# Opción C: Desde GitHub UI
# GitHub mostrará un link automático después del push
```

---

### 5. Code Review y Merge

**Durante code review:**
- Responde a comentarios
- Haz push de cambios adicionales si es necesario
- El PR se actualiza automáticamente

**Después de aprobación:**
- Merge se hace desde GitHub UI (botón "Merge pull request")
- GitHub Projects moverá automáticamente la tarjeta a "Done"
- La issue se cerrará automáticamente si el PR tiene "Fixes #XX"

---

### 6. Limpieza Post-Merge

**Eliminar branch local:**
```bash
git checkout main
git pull origin main
git branch -d fix/49-regex-household-size
```

**Eliminar branch remota (opcional):**
```bash
git push origin --delete fix/49-regex-household-size
```

---

## 🔧 Scripts Disponibles

Ver documentación completa en [`scripts/git/README.md`](../scripts/git/README.md)

### `create_feature_branch.sh`
Crea branch automáticamente desde GitHub Issue.

### `create_pr.sh`
Crea Pull Request con template automático.

### `sync_with_main.sh`
Sincroniza branch con main usando rebase.

---

## 📊 Integración con GitHub

### GitHub Issues
- Referencia issues en commits: `Fixes #49`, `Closes #52`
- GitHub cerrará automáticamente la issue al mergear PR

### GitHub Projects
- Al crear PR desde branch vinculada a issue → tarjeta se mueve automáticamente
- Al mergear PR → tarjeta se mueve a "Done" (workflow `project-sync.yml`)

### GitHub Actions (CI/CD)
- **ETL Smoke Test**: Se ejecuta en push a feature branches y en PRs
- **Project Sync**: Se ejecuta cuando PR se mergea

---

## ✅ Checklist Pre-Merge

Antes de crear PR, verifica:

- [ ] **Tests**: Todos los tests unitarios pasan (`pytest`)
- [ ] **ETL Smoke Test**: Pipeline ejecuta sin errores
- [ ] **Code Quality**: No hay warnings de linter
- [ ] **Documentation**: README/docs actualizados si es necesario
- [ ] **Database**: Schema migrations aplicadas (si aplica)
- [ ] **Data Quality**: Métricas ≥95% completeness, ≥98% validity
- [ ] **Conflicts**: Branch sincronizada con main
- [ ] **Commits**: Mensajes descriptivos y atómicos

---

## 🚨 Troubleshooting

### Branch desactualizada con main
```bash
./scripts/git/sync_with_main.sh
# O manualmente:
git fetch origin
git rebase origin/main
```

### Conflictos en rebase
1. Resolver conflictos manualmente
2. `git add archivo_resuelto.py`
3. `git rebase --continue`

### Cambios sin commitear al hacer sync
El script `sync_with_main.sh` te preguntará si quieres guardarlos en stash.

### PR no cierra issue automáticamente
Asegúrate de que el PR tiene "Fixes #XX" o "Closes #XX" en el body o en un commit.

---

## 📚 Referencias

- [Git Branching Strategy](./PROJECT_MANAGEMENT.md)
- [GitHub Issues](./GITHUB_ISSUES_AUDIT_RECIENTE.md)
- [Project Standards](../.cursor/rules/000-project-standards.mdc)
- [Scripts Git](../scripts/git/README.md)

---

## 💡 Ejemplos Prácticos

### Ejemplo 1: Fix de Bug (Issue #49)

```bash
# 1. Crear branch
./scripts/git/create_feature_branch.sh 49 fix

# 2. Hacer cambios
# ... editar archivos ...

# 3. Commit
git add src/etl/transformations/utils.py
git commit -m "fix(etl): Corregir regex en _parse_household_size - Fixes #49"

# 4. Tests
git add tests/test_utils.py
git commit -m "test(etl): Añadir test para regex corregido"

# 5. Sync y push
./scripts/git/sync_with_main.sh
git push origin fix/49-regex-household-size

# 6. Crear PR
./scripts/git/create_pr.sh
```

### Ejemplo 2: Nueva Feature (Issue #52)

```bash
# 1. Crear branch
./scripts/git/create_feature_branch.sh 52 feature

# 2. Desarrollo iterativo
git add src/etl/transformations/market.py
git commit -m "feat(etl): Añadir validación de pipes duplicados"

git add tests/test_market.py
git commit -m "test(etl): Tests para validación de pipes"

# 3. Documentación
git add docs/VALIDATION_PIPES.md
git commit -m "docs: Documentar validación de pipes duplicados"

# 4. Push y PR
git push origin feature/52-validation-pipes-duplicados
./scripts/git/create_pr.sh
```

---

**¿Preguntas?** Consulta los scripts en `scripts/git/` o revisa la documentación del proyecto.

