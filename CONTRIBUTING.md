# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir al proyecto! Esta guía te ayudará a empezar.

## 🚀 Quick Start

### 1. Fork y Clone

```bash
# Fork el repo en GitHub, luego:
git clone https://github.com/TU-USUARIO/barcelona-housing-demographics-analyzer.git
cd barcelona-housing-demographics-analyzer
```

### 2. Setup Entorno

```bash
# Crear virtualenv
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Instalar pre-commit hooks
pre-commit install
```

### 3. Crear Branch

```bash
# Convención: tipo/issue-numero-descripcion
git checkout -b feature/85-implementar-ine-extractor
git checkout -b fix/86-crash-enrich-demografia
git checkout -b refactor/87-split-data-processing
```

### 4. Desarrollo

```bash
# Hacer cambios
# Ejecutar tests frecuentemente
make test

# Verificar estilo
make lint

# Formatear código
make format
```

#### Estructura del Proyecto

**Reglas de organización**:
- `src/` - Código de producción (módulos reutilizables)
- `scripts/` - Scripts ejecutables (CLI tools)
- `spikes/` - Investigaciones temporales
- `notebooks/` - Análisis exploratorio
- `tests/` - Tests automatizados

**Reglas de dependencias**:
- `src/` NO puede importar de `scripts/`, `spikes/`, `notebooks/`
- `scripts/` puede importar de `src/` pero NO de otros scripts
- `spikes/` puede importar de `src/` pero NO de `scripts/`
- Evitar dependencias cíclicas entre módulos

Ver documentación completa:
- [`docs/PROJECT_STRUCTURE_PROPOSAL.md`](../docs/PROJECT_STRUCTURE_PROPOSAL.md) - Estructura propuesta
- [`docs/architecture/DEPENDENCIES.md`](../docs/architecture/DEPENDENCIES.md) - Reglas de dependencias
```

### 5. Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Formato: tipo(scope): descripción
git commit -m "feat(etl): implementar INEExtractor base"
git commit -m "fix(enrichment): verificar existencia de edad_media"
git commit -m "docs: actualizar guía de contribución"
git commit -m "test: añadir tests para enrich_fact_demografia"
```

**Tipos válidos**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `test`: Añadir o modificar tests
- `refactor`: Cambios de código sin afectar funcionalidad
- `perf`: Mejoras de performance
- `chore`: Cambios en build, configs, etc.

### 6. Push y Pull Request

```bash
# Push a tu fork
git push origin feature/85-implementar-ine-extractor

# Crear PR en GitHub
gh pr create --title "feat(etl): Implementar INEExtractor completo" \
  --body "Closes #85"
```

## 📋 Crear Issues

Antes de empezar a trabajar, crea o asigna una issue:

### Opción A: Crear Issue desde Draft (Recomendado)

```bash
# 1. Crear draft
cp docs/issues/ejemplo-issue-draft.md docs/issues/mi-nueva-feature.md

# 2. Editar contenido
vim docs/issues/mi-nueva-feature.md

# 3. Validar
make validate-issues

# 4. Crear en GitHub
make create-issue FILE=mi-nueva-feature.md
```

### Opción B: Crear Issue Directamente en GitHub

1. Ve a [Issues](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/new/choose)
2. Selecciona un template
3. Completa todos los campos requeridos
4. Añade labels apropiados
5. Create issue

### Mejores Prácticas para Issues

Ver guía completa: [docs/BEST_PRACTICES_GITHUB_ISSUES.md](docs/BEST_PRACTICES_GITHUB_ISSUES.md)

**Checklist rápido**:
- ✅ Título descriptivo con emoji y tipo
- ✅ Descripción clara del problema/feature
- ✅ Archivos afectados listados
- ✅ Criterios de aceptación con checkboxes
- ✅ Estimación de tiempo
- ✅ Labels apropiados

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
make test

# Con coverage
make test-coverage

# Tests específicos
pytest tests/test_cleaners.py -v
pytest tests/test_pipeline.py::test_etl_handles_missing_files_gracefully -v
```

### Escribir Tests

Ejemplo de test unitario:

```python
import pytest
from src.etl.transformations.utils import _parse_household_size


def test_parse_household_size_valid_range():
    """Test que _parse_household_size acepta rangos válidos."""
    assert _parse_household_size("1-2 personas") == "1-2"
    assert _parse_household_size("3-4 personas") == "3-4"


def test_parse_household_size_invalid():
    """Test que retorna None para inputs inválidos."""
    assert _parse_household_size("invalid") is None
    assert _parse_household_size(None) is None
```

## 📝 Code Style

### Formateo

Usamos `black` para formateo automático:

```bash
# Formatear todo el código
make format

# Verificar sin modificar
make lint
```

### Docstrings

Usa formato Google para docstrings:

```python
def prepare_fact_precios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara DataFrame de precios para carga en fact_precios.
    
    Deduplica registros manteniendo granularidad multi-fuente y
    normaliza formatos de columnas.
    
    Args:
        df: DataFrame raw de precios con columnas requeridas
    
    Returns:
        DataFrame limpio listo para carga en database.db
    
    Raises:
        ValueError: Si faltan columnas requeridas
        
    Example:
        >>> df = pd.DataFrame({"barrio_id": [1], "precio": [100]})
        >>> clean_df = prepare_fact_precios(df)
    """
```

### Type Hints

Usa type hints en funciones públicas:

```python
from pathlib import Path
from typing import Optional, List, Dict
import pandas as pd


def load_data(
    filepath: Path,
    columns: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    """..."""
```

## 🔄 Pull Request Process

### 1. Antes de Crear PR

- ✅ Todos los tests pasan (`make test`)
- ✅ Código formateado (`make format`)
- ✅ Linters pasan (`make lint`)
- ✅ Commits siguen Conventional Commits
- ✅ Branch actualizado con main

### 2. Crear PR

Usa el template automático o incluye:

```markdown
## 🎯 Issue Relacionada

Closes #XX

## 📝 Descripción de Cambios

- Cambio 1
- Cambio 2

## 🧪 Cómo Probar

```bash
python scripts/process_and_load.py
pytest tests/test_cleaners.py -v
```

## ✅ Checklist

- [ ] Tests pasan localmente
- [ ] Código formateado con black
- [ ] Docstrings actualizados
- [ ] CHANGELOG.md actualizado (si aplica)
```

### 3. Review y Merge

- 🔍 Code review requerido
- ✅ CI debe pasar
- 🔀 Merge con squash (mantiene historia limpia)

## 🐛 Reportar Bugs

Si encuentras un bug:

1. **Busca** si ya existe un issue similar
2. Si no existe, **crea uno nuevo** con:
   - Título descriptivo: `🐛 Bug: [descripción breve]`
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Logs de error (si aplica)
   - Entorno (Python version, OS)

## 💡 Proponer Features

Para proponer nuevas funcionalidades:

1. **Crea un issue** con tipo `enhancement`
2. Describe:
   - Qué problema resuelve
   - Casos de uso
   - Alternativas consideradas
3. Espera feedback antes de implementar

## ❓ Preguntas

- 💬 [Discussions](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/discussions)
- 🐛 [Issues](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues)

## 📚 Recursos

- [Documentación del Proyecto](docs/)
- [Mejores Prácticas de Issues](docs/BEST_PRACTICES_GITHUB_ISSUES.md)
- [Flujo de Trabajo de Issues](docs/ISSUE_WORKFLOW.md)
- [Roadmap del Proyecto](docs/PROJECT_MILESTONES.md)

---

¡Gracias por contribuir! 🎉

