## 🤖 Automatización de Labels

<!-- 
     ⚡ Los labels y asignación se aplican automáticamente según el título del PR.
     
     Convenciones recomendadas para el título:
     - deps(python) o deps(pip) → labels: dependencies, python
     - deps(docker) → labels: dependencies, docker  
     - deps(actions) → labels: dependencies, github-actions
     - feature o feat → label: enhancement
     - fix o bug → label: bug
     - docs o documentation → label: documentation
     - test o testing → label: testing
     - refactor → label: refactor
     
     Ejemplos de títulos:
     - "deps(python): Actualizar pandas a 2.1.0"
     - "feature: Añadir calculadora de ROI por barrio"
     - "fix: Corregir deduplicación en fact_precios"
     - "docs: Actualizar guía de extracción de datos"
-->

---

## 📋 Descripción del Cambio

<!-- Resume los cambios en 2-3 líneas claras.
     Ejemplo: "Implementa calculadora de inversión que calcula ROI, cashflow y payback period
     basado en datos de fact_precios y fact_renta" -->

Resumen:

<!-- Tu descripción aquí -->

Motivación:

<!-- ¿Por qué es necesario este cambio? ¿Qué problema resuelve?
     Ejemplo: "Actualmente no existe una forma sencilla de evaluar la viabilidad de inversión
     por barrio usando los datos ya disponibles en database.db" -->

---

## 🔗 Issue Relacionada

<!-- Usa formato especial para auto-cerrar la issue al mergear.
     Opciones: Closes, Fixes, Resolves.
     Ejemplo: "Closes #86" -->

Closes #___

<!-- Si NO cierra la issue completamente (cambio parcial), puedes usar:
     Related to #___
     Part of #___ -->

---

## 🛠️ Tipo de Cambio

<!-- Marca UNA opción principal (puede haber secundarias si lo explicas en Notas para Revisores). -->

Tipo principal:
- [ ] 🐛 Bug fix - Corrige error existente
- [ ] ✨ Nueva feature - Añade funcionalidad nueva
- [ ] ♻️ Refactor - Mejora código sin cambiar funcionalidad
- [ ] 📝 Documentación - Cambios solo en docs (README, docstrings, guides)
- [ ] ✅ Tests - Añade o mejora tests (sin cambio funcional)
- [ ] 🔧 Chore - CI/CD, dependencies, configuración

Área afectada:
<!-- Marca todas las que apliquen. -->

- [ ] area:data - Extracción (scrapers, APIs, extractors)
- [ ] area:backend - ETL, database, processing
- [ ] area:frontend - Dashboard Streamlit
- [ ] area:docs - Documentación
- [ ] area:infra - CI/CD, deployment

---

## ✅ Checklist Obligatorio (Definition of Done)

<!-- Todos los items deben estar marcados antes de pedir review.
     Si alguno NO aplica, márcalo igualmente y explica por qué en "Notas para Revisores". -->

**Código**
- [ ] Funcionalidad implementada según especificación de la issue
- [ ] Linter pasando (ruff / black / flake8) sin errores
- [ ] Type hints añadidos en funciones públicas
- [ ] Sin warnings de seguridad o deprecation introducidos

**Tests**
- [ ] Tests unitarios añadidos/actualizados
- [ ] Tests de integración si aplica (cambios en ETL/database)
- [ ] Coverage ≥ 25% global y sin bajar cobertura en módulos críticos
- [ ] Tests pasan localmente (`pytest tests/ -v`)

**Documentación**
- [ ] Docstrings añadidos/actualizados (formato Google-style)
- [ ] README actualizado si cambia setup o features principales
- [ ] CHANGELOG.md actualizado con entrada de esta versión (si aplica)
- [ ] Comentarios añadidos en lógica compleja explicando el *por qué* (no el *qué*)

**Code Review (pre-check)**
- [ ] Auto-review completado (revisé mi propio código línea por línea)
- [ ] Sin código comentado o debug statements (`print`, logs sobrantes, etc.)
- [ ] Sin conflictos con `main` (rebase/merge actualizado)
- [ ] Commits descriptivos (idealmente formato Conventional Commits)

**CI/CD**
- [ ] GitHub Actions pasando (tests + linter)
- [ ] Branch actualizado con el último commit de `main`
- [ ] No hay secrets ni tokens expuestos en código o history

**Database (si aplica)**
- [ ] Migración SQL incluida si cambia el schema
- [ ] Cambio backward compatible (no rompe datos existentes)
- [ ] Foreign keys validadas si se añaden relaciones nuevas

---

## 🧪 Cómo Probar Este Cambio

<!-- Instrucciones claras para que el revisor (y tú en el futuro) validen el cambio. -->

### Setup Previo

```bash
# Checkout de la branch
git checkout <branch-name>

# Actualizar dependencias (si aplica)
pip install -r requirements.txt -r requirements-dev.txt

# Preparar database (si aplica)
# python scripts/migrations/run_migration.py
# o scripts/ETL relevantes
```

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/ -v

# Tests con coverage (configurado en pyproject.toml)
pytest tests/
```

### Validación Manual (si aplica)

Ejecutar dashboard:

```bash
streamlit run src/app/app.py
```

Navegar a:

<!-- Ej: "Página 'Market Cockpit' → sección 'Comparativa de barrios'" -->

Probar caso de uso:

- Acción 1:
- Acción 2:
- Resultado esperado: `___________`

### Casos de Prueba Críticos

<!-- Lista casos específicos que el revisor debe validar. -->

- Caso 1: [Descripción del caso crítico]
- Caso 2: [Descripción de segundo caso]
- Edge case: [Caso límite importante]

---

## 📸 Screenshots / Demos (si aplica)

<!-- Obligatorio para cambios en dashboard o UI. Opcional para backend si ayuda. -->

**Antes** (si aplica)

<!-- Screenshot del estado anterior (puede ser link o imagen adjunta). -->

**Después**

<!-- Screenshot o GIF del nuevo comportamiento. -->

**Demo Video (opcional)**

<!-- Link a Loom, YouTube unlisted, o GIF en GitHub. -->

---

## 🔧 Cambios Técnicos Detallados

<!-- Ayuda al revisor a entender el enfoque técnico sin tener que deducirlo solo del diff. -->

### Archivos Modificados

**Nuevos archivos:**
- `src/path/to/new_file.py` – [Propósito]
- `tests/test_new_file.py` – [Tests para new_file.py]

**Modificados:**
- `src/path/to/existing.py` – [Qué cambió y por qué]
- `src/app/pages/dashboard.py` – [Integración de nueva feature en UI]

**Eliminados (si aplica):**
- `src/deprecated/old_file.py` – [Razón de eliminación]

### Decisiones Técnicas Importantes

Decisión:
<!-- Ej: "Usar numpy-financial para cálculos de VAN/TIR en vez de implementar fórmulas manuales." -->

Razón:
<!-- Pros de la decisión tomada. -->

Trade-offs:
<!-- Contras o limitaciones aceptadas. -->

### Librerías Añadidas (si aplica)

- `library-name==version` – [Por qué es necesaria / dónde se usa]

### Cambios en Schema (si aplica)

```sql
-- Describir brevemente cambios en database schema
-- Ej: nueva tabla fact_renta_hist, nuevas columnas en dim_barrios, índices creados, etc.
```

### Consideraciones de Performance

<!-- Documenta si hay impacto relevante en rendimiento. -->

- Tiempo de ejecución: `___` (antes) → `___` (después)
- Queries optimizadas: [Descripción]
- Caching implementado: [Descripción]

---

## ⚠️ Impacto y Riesgos

### Impacto del Cambio

<!-- ¿A quién/qué afecta este cambio? Marca lo que aplique. -->

- [ ] Breaking change – Rompe funcionalidad existente (requiere migración o cambios coordinados)
- [ ] Cambio en API/interface – Otros módulos/consumidores pueden verse afectados
- [ ] Cambio en datos – Afecta estructura o significado de datos en `database.db`
- [ ] Cambio en UI – Usuarios verán diferencias visuales/funcionales
- [ ] Sin impacto externo – Cambio interno (refactor, tests, etc.)

### Riesgos Identificados

Riesgo:
<!-- Ej: "Si el extractor falla por rate limit, el ETL diario podría quedar incompleto." -->

Probabilidad: Alta / Media / Baja  

Mitigación:
<!-- Ej: "Implementar retry con backoff y alertas en caso de fallo repetido." -->

### Plan de Rollback

<!-- Si algo falla en producción, ¿cómo revertir? -->

- [ ] Fácil: Revert commit (no hay cambios de schema/datos complejos)
- [ ] Medio: Requiere migración de datos hacia atrás
- [ ] Difícil: Requiere intervención manual (explica qué habría que hacer)

---

## 🧪 Evidencia de Testing

<!-- Pega aquí salidas relevantes de tests para que el revisor no tenga que re-ejecutar todo si no es necesario. -->

**Test Results**

```bash
# Output de pytest
# Pega aquí el resultado resumido o completo

======================== test session starts ========================
collected X items

tests/test_module.py::test_function PASSED                    [ XX%]
...
===================== X passed in X.XXs =====================
```

**Coverage Report**

```bash
# Output de coverage
Name                      Stmts   Miss  Cover
---------------------------------------------
src/module.py               45      2    96%
---------------------------------------------
TOTAL                       45      2    96%
```

**Linter Results**

```bash
# Ejemplo con black/ruff/flake8

# black .
All done! ✨ 🍰 ✨
X files left unchanged.

# ruff check src/ tests/
# Sin output = todo correcto ✅

# flake8 src/ tests/
# Sin output = todo correcto ✅
```

---

## 📝 Notas para Revisores

<!-- Información adicional que ayude a enfocar el code review. -->

### Áreas que Necesitan Atención Especial

- Lógica compleja en `src/path/to/file.py:línea_X` – [Explicación del por qué es compleja]
- Performance crítico en `function_name()` – [Por qué es importante]
- Decisión controversial en `module.py` – [Justificación]

### Alternativas Consideradas

- Alternativa A:
  - Descripción:
  - Descartada porque: `___________`

- Alternativa B:
  - Descripción:
  - Descartada porque: `___________`

### Preguntas Abiertas

- ¿Es este el mejor enfoque para `___________`?
- ¿Deberíamos considerar `___________` en su lugar?

### Items del Checklist que NO Aplican

<!-- Si marcaste algo como N/A, explica aquí por qué. -->

- Item X: No aplica porque `___________`

---

## 🔜 Issues de Seguimiento

<!-- Si este PR no cubre todo el alcance de la issue original o genera trabajo futuro. -->

Quedó pendiente para otro PR:
- [ ] [Descripción de lo que falta] – Issue #___

Mejoras futuras identificadas:
- [ ] [Descripción de mejora] – Issue #___

Tech Debt creada (si aplica):
- [ ] [Descripción del tech debt] – Issue #___

---

## ✅ Checklist de Revisor

<!-- Para que la persona que revisa tenga una guía clara. -->

- [ ] Entendí el objetivo del cambio (descripción y motivación claras)
- [ ] El cambio está bien delimitado (no mezcla múltiples features sin relación)
- [ ] El código es legible y sigue los estándares del proyecto (naming, estilo, type hints)
- [ ] No veo problemas evidentes de seguridad (secrets, datos sensibles, inyección SQL)
- [ ] No veo riesgos de performance obvios (loops innecesarios, queries sin índices, etc.)
- [ ] Los tests cubren los casos principales y edge cases razonables
- [ ] La documentación es suficiente (docstrings, README, docs/* si aplica)
- [ ] El checklist de Definition of Done está completo o justificado
- [ ] CI/CD pasa sin errores (Actions en verde)
- [ ] Estoy cómodo aprobando este PR (o he dejado comentarios claros)

<!-- Gracias por contribuir a Barcelona Housing Demographics Analyzer 🙌 -->
