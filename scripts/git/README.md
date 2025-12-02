# Scripts Git - Feature Branch Workflow

Scripts de ayuda para trabajar con feature branches siguiendo las convenciones del proyecto.

## Scripts Disponibles

### 1. `create_feature_branch.sh`

Crea una feature branch automáticamente desde una GitHub Issue.

**Uso:**
```bash
./scripts/git/create_feature_branch.sh <issue_number> [type]
```

**Ejemplos:**
```bash
# Crear branch para fix de issue #49
./scripts/git/create_feature_branch.sh 49 fix

# Crear branch para feature de issue #52
./scripts/git/create_feature_branch.sh 52 feature

# Crear branch para refactor de issue #43
./scripts/git/create_feature_branch.sh 43 refactor
```

**Tipos válidos:**
- `feature` (default): Nueva funcionalidad
- `fix`: Corrección de bug
- `refactor`: Refactorización de código
- `etl`: Trabajo relacionado con ETL
- `dashboard`: Mejoras del dashboard
- `docs`: Documentación
- `test`: Tests

**Qué hace:**
1. Obtiene el título de la issue desde GitHub
2. Actualiza `main` con los últimos cambios
3. Crea una nueva branch con nombre normalizado
4. Te cambia a la nueva branch

---

### 2. `create_pr.sh`

Crea un Pull Request automáticamente desde la branch actual.

**Uso:**
```bash
# Debes estar en una feature branch
./scripts/git/create_pr.sh
```

**Qué hace:**
1. Detecta el tipo de PR desde el nombre de la branch
2. Extrae el número de issue si existe
3. Genera un template de PR con checklist
4. Crea el PR en GitHub con las etiquetas apropiadas

**Requisitos:**
- Debes estar en una feature branch (no en `main`)
- Debes tener `gh` CLI instalado y autenticado
- Debes haber hecho al menos un commit

---

### 3. `sync_with_main.sh`

Sincroniza tu feature branch con `main` usando rebase.

**Uso:**
```bash
# Debes estar en una feature branch
./scripts/git/sync_with_main.sh
```

**Qué hace:**
1. Guarda cambios sin commitear en stash (si los hay)
2. Actualiza `main` con los últimos cambios
3. Hace rebase de tu branch sobre `main`
4. Restaura los cambios guardados

**Recomendado:**
- Ejecutar antes de crear PR
- Ejecutar periódicamente si trabajas en una branch por varios días

**Después de sync:**
```bash
git push origin tu-branch --force-with-lease
```

---

## Flujo de Trabajo Completo

### Escenario 1: Trabajar en una Issue existente

```bash
# 1. Crear branch desde issue
./scripts/git/create_feature_branch.sh 49 fix

# 2. Hacer cambios y commits
git add src/etl/transformations/utils.py
git commit -m "fix(etl): Corregir regex en _parse_household_size - Fixes #49"

git add tests/test_utils.py
git commit -m "test(etl): Añadir test para regex corregido"

# 3. Sincronizar con main (opcional pero recomendado)
./scripts/git/sync_with_main.sh

# 4. Push y crear PR
git push origin fix/49-regex-household-size
./scripts/git/create_pr.sh
```

### Escenario 2: Trabajar en una nueva feature sin issue

```bash
# 1. Crear branch manualmente
git checkout main
git pull origin main
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios y commits
git add ...
git commit -m "feat: Nueva funcionalidad"

# 3. Push y crear PR
git push origin feature/nueva-funcionalidad
./scripts/git/create_pr.sh
```

### Escenario 3: Actualizar branch existente

```bash
# Si main avanza mientras trabajas
./scripts/git/sync_with_main.sh

# Resolver conflictos si los hay
git add archivo_resuelto.py
git rebase --continue

# Push actualizado
git push origin tu-branch --force-with-lease
```

---

## Convenciones de Nombres

### Formato recomendado:
```
<tipo>/<issue-number>-<descripcion-corta>
```

**Ejemplos:**
- `fix/49-regex-household-size`
- `feature/52-validation-pipes-duplicados`
- `refactor/43-limpiar-orquestador-pipeline`
- `etl/idescat-extractor-integration`
- `dashboard/affordability-index-viz`
- `docs/audit-reciente-github-issues`

---

## Configuración Git Recomendada

Los siguientes alias y configuraciones están recomendados:

```bash
# Configuración automática (ya aplicada)
git config --local pull.rebase true
git config --local fetch.prune true

# Alias útiles (opcional)
git config --local alias.sync '!git fetch origin && git rebase origin/main'
git config --local alias.cleanup '!git branch --merged main | grep -v "\\* main" | xargs -n 1 git branch -d'
```

**Uso de alias:**
```bash
# Sincronizar branch actual con main
git sync

# Limpiar branches mergeadas
git cleanup
```

---

## Troubleshooting

### Error: "gh CLI no está instalado"
```bash
# Instalar gh CLI
brew install gh  # macOS
# o descargar desde: https://cli.github.com/
```

### Error: "No se encontró la Issue #XX"
- Verifica que la issue existe en GitHub
- Verifica que tienes acceso al repositorio
- Verifica que estás autenticado: `gh auth status`

### Error: "Branch ya existe"
- El script te preguntará si quieres cambiarte a ella
- O elimínala manualmente: `git branch -D nombre-branch`

### Conflictos en rebase
1. Resuelve los conflictos en los archivos marcados
2. `git add archivo_resuelto.py`
3. `git rebase --continue`
4. Si quieres cancelar: `git rebase --abort`

---

## Integración con GitHub Actions

Los workflows de CI/CD se ejecutan automáticamente cuando:
- Haces push a una feature branch (patrones: `feature/**`, `fix/**`, `etl/**`, `refactor/**`)
- Creas un Pull Request hacia `main`

**Workflows activos:**
- `etl-smoke.yml`: Ejecuta tests y validaciones ETL
- `project-sync.yml`: Sincroniza GitHub Projects cuando PR se mergea

---

## Buenas Prácticas

1. **Una branch por issue**: Facilita trazabilidad y code review
2. **Commits atómicos**: Un commit = un cambio lógico
3. **Mensajes descriptivos**: Usa formato `tipo(scope): descripción`
4. **Sync frecuente**: Actualiza tu branch con `main` regularmente
5. **PRs pequeños**: Mejor varios PRs pequeños que uno gigante
6. **Tests antes de PR**: Asegúrate de que los tests pasan localmente

---

## Referencias

- [Git Branching Strategy](./docs/PROJECT_MANAGEMENT.md)
- [GitHub Issues](./docs/GITHUB_ISSUES_AUDIT_RECIENTE.md)
- [Project Standards](.cursor/rules/000-project-standards.mdc)

