# Guía de Contribución - Barcelona Housing Demographics Analyzer

¡Gracias por tu interés en contribuir al proyecto! 🎉

Este documento explica cómo preparar el entorno, cómo proponer cambios (issues/PRs) y qué estándares seguimos para mantener una base de código saludable.

---

## 🧱 1. Requisitos Previos

Antes de contribuir, asegúrate de tener:

- Python **3.11+** instalado
- `git` instalado y configurado
- `pip` o `pipx` para instalar dependencias
- `sqlite3` disponible en tu sistema (para inspeccionar `database.db` si es necesario)

Opcional pero recomendable:
- Editor con soporte para Python (VSCode, PyCharm, Cursor, etc.)
- Extensión de Markdown para editar documentación

---

## 🛠️ 2. Setup del Entorno de Desarrollo

```bash
# 1. Clonar el repositorio
 git clone https://github.com/prototyp33/barcelona-housing-demographics-analyzer.git
 cd barcelona-housing-demographics-analyzer

# 2. Crear y activar entorno virtual (recomendado)
 python -m venv .venv
 source .venv/bin/activate  # macOS/Linux
 # .venv\Scripts\activate  # Windows

# 3. Instalar dependencias
 pip install -r requirements.txt -r requirements-dev.txt

# 4. Ejecutar tests para verificar que todo está OK
 pytest tests/ -v
```

Si algo falla en este punto, revisa `docs/DEBUGGING_DATASETS.md` y `docs/PROJECT_SETUP_CHECKLIST.md`.

---

## 🧭 3. Tipos de Contribuciones

Puedes contribuir de varias formas:

- 🐛 **Bug fixes**: corregir errores en extracción, ETL, base de datos o dashboard
- ✨ **Nuevas features**: añadir nuevas métricas, visualizaciones, extractores, etc.
- ♻️ **Refactors**: mejorar código existente sin cambiar funcionalidad
- ✅ **Tests**: ampliar cobertura de tests unitarios/integración
- 📝 **Documentación**: mejorar README, docs en `docs/` o `project-docs/`
- 🔧 **Infra/CI**: mejorar workflows de GitHub Actions, tooling, etc.

Si no estás seguro por dónde empezar, busca issues con los labels:
- `good-first-issue`
- `help-wanted`

---

## 🧵 4. Flujo de Trabajo con Git y GitHub

### 4.1. Branching

Usamos ramas de features sobre `main`:

- `main`: rama principal estable
- `feature/<nombre-descriptivo>`: nuevas features
- `fix/<bug-específico>`: corrección de bugs
- `refactor/<area>`: refactors
- `docs/<tema>`: cambios solo de documentación

Ejemplos:

```bash
git checkout -b feature/investment-calculator
# o
git checkout -b fix/opendata-timeout
```

### 4.2. Commits

Preferimos mensajes de commit descriptivos. Si puedes usar formato [Conventional Commits](https://www.conventionalcommits.org/) mejor:

```text
feat(analytics): add investment calculator core logic
fix(extraction): handle 404 responses from Open Data BCN
chore(ci): add label sync workflow
docs(project): document GitHub templates setup
```

### 4.3. Pull Requests

1. Crea una rama desde `main`.
2. Haz cambios pequeños y enfocados (1 PR = 1 objetivo claro).
3. Asegúrate de que los tests pasan localmente.
4. Abre un PR usando el template `.github/pull_request_template.md`.
5. Marca el checklist de Definition of Done.
6. Espera al menos 1 aprobación antes de merge.

Usamos **Squash & Merge** para mantener un historial limpio.

---

## 🐞 5. Abrir Issues

Antes de abrir una nueva issue:

1. Revisa issues existentes para evitar duplicados.
2. Usa los **templates** definidos en `.github/ISSUE_TEMPLATE/`:
   - `Feature Request` para nuevas funcionalidades
   - `Bug Report` para errores
   - `Research Task` para investigaciones técnicas
3. Proporciona la mayor cantidad de contexto posible (logs, screenshots, comandos exactos, etc.).

Las issues se etiquetan automáticamente con labels básicos gracias al frontmatter del template. El triage añadirá labels adicionales (`priority-*`, `area-*`, etc.).

---

## 🧪 6. Estándares de Código y Tests

### 6.1. Estilo de Código

- Seguir **PEP 8** (estilo Python)
- Usar **type hints** en funciones públicas
- Usar **docstrings** en formato Google-style
- Evitar `print`; usar `logging` con niveles apropiados

Herramientas configuradas en `pyproject.toml`:

- Ruff (linting + formato rápido)
- Black (formato backup)
- isort (orden de imports)
- mypy (type checking opcional)

Comandos útiles:

```bash
# Linting y formato
ruff check src/ tests/ scripts/
ruff format src/ tests/ scripts/  # o black src/ tests/

# Type checking
mypy src/
```

### 6.2. Tests

- Todos los cambios no triviales deben venir con tests.
- Cobertura objetivo global: **≥25% ahora**, subir gradualmente hacia 60%+.
- No romper tests existentes sin actualizar expectativas.

Ejecutar tests:

```bash
pytest tests/ -v
# Con coverage (configurado en pyproject.toml)
pytest tests/
```

---

## 🗄️ 7. Esquema de Datos y ETL

Antes de tocar ETL o base de datos:

1. Lee `docs/DATABASE_SCHEMA.md` para entender las tablas (`dim_barrios`, `fact_precios`, `fact_demografia`, etc.).
2. Revisa `src/database_setup.py` para validadores y helpers.
3. Revisa `src/etl/pipeline.py` y `src/etl/validators.py` para ver el flujo actual.

Los cambios en schema deben ir acompañados de:

- Scripts de migración (en `scripts/migrations/` si aplica)
- Actualización de documentación (DATABASE_SCHEMA, diagramas, etc.)
- Tests de integridad (`tests/test_fk_validation.py`, `tests/test_pipeline.py`)

---

## 🧩 8. PR Checklist (Resumen)

Antes de pedir review, verifica:

- [ ] Los tests pasan localmente (`pytest tests/ -v`)
- [ ] Linter sin errores (ruff / black / flake8)
- [ ] Type hints donde aplica
- [ ] Docstrings y documentación actualizados
- [ ] Template de PR rellenado completamente
- [ ] Issue relacionada enlazada (`Closes #N` o similar)
- [ ] No hay secrets en el código ni en el history de git

---

## 💬 9. Preguntas y Soporte

Si tienes dudas:

- Abre una **Research Task** para investigar un tema técnico.
- Usa discusiones de GitHub si se habilitan.
- Añade comentarios claros en tu PR indicando dónde necesitas feedback.

Este proyecto está pensado como **showcase profesional** y herramienta útil para la comunidad, así que la calidad y claridad del código y la documentación son prioritarias.

¡Gracias por ayudar a mejorar Barcelona Housing Demographics Analyzer! 🙌
