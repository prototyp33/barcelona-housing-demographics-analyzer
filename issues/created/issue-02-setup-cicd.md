---
title: [SETUP] GitHub Actions CI/CD con testing automático
labels: ["sprint-1", "priority-critical", "type-infra", "effort-s"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 3 horas  
**Fecha límite:** 2025-12-10  

**Dependencias:**
- Ninguna

**Bloqueadores:**
- Ninguno conocido

**Documentación relacionada:**
- 📄 [CI Pipeline](.github/workflows/ci.yml)
- 📄 [Project Standards](.cursor/rules/000-project-standards.mdc)

---

## 📝 Descripción

Setup completo de CI/CD para mantener calidad de código. El pipeline ejecutará linting, type checking, y tests en cada push/PR.

**Valor de Negocio:**
Garantiza calidad de código antes de merge, previene regresiones, y mantiene estándares del proyecto. Esencial para desarrollo profesional.

**User Story:**
> Como desarrollador, necesito que el código se valide automáticamente antes de merge para mantener calidad y prevenir bugs.

---

## 🔧 Componentes Técnicos

### Archivos a crear/modificar:

- [ ] Verificar `.github/workflows/ci.yml` existe y está completo
- [ ] Añadir badge de build status en `README.md`
- [ ] Configurar Codecov (opcional pero recomendado)
- [ ] Verificar que `pyproject.toml` tiene configuración de ruff/mypy/pytest

### Workflow CI/CD

El workflow debe ejecutar:

1. **Linting** (Ruff)
   - Check: `ruff check src/ tests/`
   - Format: `ruff format --check src/ tests/`

2. **Type Checking** (mypy)
   - `mypy src/ --ignore-missing-imports`

3. **Tests** (pytest)
   - `pytest tests/ -v --cov=src --cov-report=xml`
   - Target: >80% coverage

4. **Security** (pip-audit)
   - `pip-audit --requirement requirements.txt`

### Configuración Requerida

```yaml
# .github/workflows/ci.yml debe incluir:

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff black isort
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

---

## ✅ Criterios de Aceptación

- [ ] Pipeline ejecuta en cada push a `main`/`develop`
- [ ] Pipeline ejecuta en cada PR a `main`
- [ ] Tests pasan en CI antes de merge
- [ ] Linting pasa sin errores
- [ ] Type checking pasa (warnings OK)
- [ ] Badge verde visible en README
- [ ] Codecov configurado (opcional)
- [ ] Documentación actualizada

---

## 🧪 Plan de Testing

### Validación del Pipeline

1. **Test local:**
   ```bash
   # Verificar que los comandos funcionan localmente
   ruff check src/ tests/
   ruff format --check src/ tests/
   mypy src/ --ignore-missing-imports
   pytest tests/ -v --cov=src
   ```

2. **Test en CI:**
   - Hacer un commit pequeño
   - Push a branch
   - Crear PR
   - Verificar que el workflow se ejecuta
   - Verificar que todos los jobs pasan

3. **Test de fallo:**
   - Introducir un error de linting intencional
   - Verificar que el pipeline falla correctamente

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Build success rate** | >95% | GitHub Actions history |
| **Tiempo de ejecución** | < 5 min | GitHub Actions logs |
| **Tests coverage** | >80% | Codecov report |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Tests flaky | Baja | Medio | Usar seeds fijos, mockear APIs |
| Rate limiting en CI | Baja | Bajo | Cache de dependencias |
| Configuración incorrecta | Media | Alto | Validar localmente primero |

---

## 📚 Referencias

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Setup](https://docs.codecov.com/docs)

---

## 🔗 Issues Relacionadas

- #1: [SETUP] Configurar GitHub Project Board
- #3: [FEAT-02] Investment Calculator - Core Logic

---

## 📝 Notas de Implementación

### Orden de Ejecución

1. **Paso 1:** Verificar que `.github/workflows/ci.yml` existe
   - Si no existe, crear basado en el template
   - Si existe, verificar que está completo

2. **Paso 2:** Probar localmente
   ```bash
   ruff check src/ tests/
   pytest tests/ -v
   ```

3. **Paso 3:** Hacer commit y push
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "ci: setup GitHub Actions CI/CD pipeline"
   git push origin main
   ```

4. **Paso 4:** Verificar en GitHub Actions
   - Ir a: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions
   - Verificar que el workflow se ejecuta
   - Verificar que todos los jobs pasan

5. **Paso 5:** Añadir badge a README
   ```markdown
   [![CI](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/actions/workflows/ci.yml)
   ```

6. **Paso 6:** Configurar Codecov (opcional)
   - Crear cuenta en codecov.io
   - Añadir token como secret
   - Verificar que coverage se sube

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

