# Development Environment Setup Guide

**Proyecto:** Barcelona Housing Demographics Analyzer  
**Última actualización:** Diciembre 2025

---

## Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Setup Inicial](#setup-inicial)
3. [Configuración del Entorno](#configuración-del-entorno)
4. [Herramientas de Desarrollo](#herramientas-de-desarrollo)
5. [Configuración de IDE](#configuración-de-ide)
6. [Testing y Quality Assurance](#testing-y-quality-assurance)
7. [Troubleshooting](#troubleshooting)

---

## Prerrequisitos

### Software Requerido

| Software | Versión Mínima | Instalación |
|----------|----------------|-------------|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) o `pyenv` |
| Git | 2.30+ | [git-scm.com](https://git-scm.com/downloads) |
| PostgreSQL | 14+ (opcional para v2.0) | [postgresql.org](https://www.postgresql.org/download/) |
| Docker | 20.10+ (opcional) | [docker.com](https://www.docker.com/get-started) |

### Herramientas Recomendadas

- **GitHub CLI** (`gh`) - Para gestión de issues y PRs
- **jq** - Para procesar JSON en scripts
- **tree** - Para visualizar estructura de directorios
- **pre-commit** - Para hooks de Git

---

## Setup Inicial

### 1. Clonar Repositorio

```bash
git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
```

### 2. Crear Virtual Environment

```bash
# Crear venv principal (para desarrollo general)
python3 -m venv .venv

# Activar
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Actualizar pip
pip install --upgrade pip setuptools wheel
```

### 3. Instalar Dependencias del Proyecto

```bash
# Instalar dependencias base
pip install -r requirements.txt

# Instalar dependencias de desarrollo (si existe)
if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
fi
```

### 4. Instalar Pre-commit Hooks (Opcional pero Recomendado)

```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Verificar
pre-commit run --all-files
```

---

## Configuración del Entorno

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env  # Si existe template
# Editar .env con tus valores
```

**Variables comunes:**

```bash
# Database (para v2.0+)
DATABASE_URL=postgresql://user:password@localhost:5432/barcelona_housing

# APIs
INE_API_KEY=your_key_here
OPENDATA_BCN_API_KEY=your_key_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Environment
ENVIRONMENT=development
```

**Importante:** `.env` está en `.gitignore` - nunca commitear credenciales.

### Configuración de Paths

El proyecto usa paths relativos. Verificar estructura:

```bash
# Estructura esperada
barcelona-housing-demographics-analyzer/
├── src/              # Código fuente
├── tests/            # Tests unitarios
├── data/             # Datos (raw y processed)
├── notebooks/        # Jupyter notebooks
├── docs/             # Documentación
├── scripts/          # Scripts de utilidad
└── .env              # Variables de entorno (no commitear)
```

---

## Herramientas de Desarrollo

### Linting y Formateo

El proyecto usa **Ruff** para linting y formateo:

```bash
# Instalar ruff
pip install ruff

# Linting
ruff check src/ tests/

# Formateo automático
ruff format src/ tests/

# Verificar antes de commit
ruff check . && ruff format --check .
```

### Type Checking

Usamos **mypy** para type checking opcional:

```bash
# Instalar mypy
pip install mypy

# Verificar tipos
mypy src/ --ignore-missing-imports
```

### Testing

Framework: **pytest**

```bash
# Instalar pytest y plugins
pip install pytest pytest-cov pytest-mock

# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ -v --cov=src --cov-report=html

# Tests específicos
pytest tests/test_extraction.py -v
```

**Target:** Coverage ≥80% para código crítico.

---

## Configuración de IDE

### VS Code / Cursor

**Extensiones recomendadas:**

- Python (Microsoft)
- Pylance (type checking)
- Ruff (linting)
- Jupyter (notebooks)
- GitLens (Git integration)

**Configuración `.vscode/settings.json`:**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

1. **Configurar Interpreter:**
   - File → Settings → Project → Python Interpreter
   - Seleccionar `.venv/bin/python`

2. **Configurar Tests:**
   - File → Settings → Tools → Python Integrated Tools
   - Testing: pytest
   - Test runner: pytest

3. **Configurar Code Style:**
   - File → Settings → Editor → Code Style → Python
   - Importar estilo desde `.pylintrc` o configurar manualmente

---

## Testing y Quality Assurance

### Ejecutar Suite Completa

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Security scan (opcional)
pip install bandit
bandit -r src/
```

### Pre-commit Checklist

Antes de cada commit:

- [ ] Código pasa linting (`ruff check .`)
- [ ] Código formateado (`ruff format .`)
- [ ] Tests pasan (`pytest tests/`)
- [ ] Coverage ≥80% para código nuevo
- [ ] Type hints agregados donde aplica
- [ ] Docstrings agregados para funciones públicas

---

## Configuración de Git

### Git Hooks

El proyecto incluye pre-commit hooks (si instalaste pre-commit):

```bash
# Verificar hooks instalados
ls -la .git/hooks/

# Ejecutar manualmente
pre-commit run --all-files
```

### Conventional Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Formato
<type>(<scope>): <subject>

# Ejemplos
feat(etl): add INE price extractor
fix(database): correct foreign key constraint
docs(readme): update setup instructions
test(extraction): add unit tests for Portal Dades
```

**Tipos comunes:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `test`: Tests
- `refactor`: Refactorización
- `chore`: Tareas de mantenimiento

---

## Base de Datos (v2.0+)

### Setup PostgreSQL Local (Opcional)

```bash
# Instalar PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Crear base de datos
createdb barcelona_housing

# Conectar
psql barcelona_housing

# Ejecutar schema
psql barcelona_housing < src/database/schema_v2.sql
```

### Usar Docker (Alternativa)

```bash
# Crear contenedor PostgreSQL
docker run --name barcelona-housing-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=barcelona_housing \
  -p 5432:5432 \
  -d postgres:14

# Conectar
psql -h localhost -U postgres -d barcelona_housing
```

---

## Troubleshooting

### Error: "Python version mismatch"

**Solución:**
```bash
# Verificar versión
python3 --version

# Usar pyenv para gestionar versiones
pyenv install 3.11.0
pyenv local 3.11.0
```

### Error: "Package installation fails"

**Solución:**
```bash
# Actualizar pip y herramientas
pip install --upgrade pip setuptools wheel

# Instalar dependencias del sistema (macOS)
brew install geos proj  # Para geopandas

# Reinstalar paquetes problemáticos
pip install --force-reinstall <package-name>
```

### Error: "Import errors in IDE"

**Solución:**
- Verificar que el IDE está usando el venv correcto
- En VS Code: Cmd+Shift+P → "Python: Select Interpreter" → Elegir `.venv/bin/python`
- Reiniciar el IDE después de cambiar interpreter

### Error: "Tests fail with database connection"

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
pg_isready

# O usar SQLite para tests (más rápido)
# Configurar en tests/conftest.py
```

---

## Recursos Adicionales

- [Project README](../../README.md)
- [Contributing Guidelines](../../.github/CONTRIBUTING.md)
- [Git Workflow](../../docs/GIT_WORKFLOW.md)
- [Python Best Practices](../../.cursor/rules/000-project-standards.mdc)

---

**Última actualización:** Diciembre 2025

