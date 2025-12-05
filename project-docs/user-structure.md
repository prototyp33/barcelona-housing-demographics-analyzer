# Estructura y Flujo de Usuario

## Flujo de Contribución

### Issue Creation Workflow

1. Usuario visita GitHub Issues → `New Issue`.
2. GitHub muestra menú con 3 opciones (config.yml):
   - **Feature Request**
   - **Bug Report**
   - **Research Task**
3. Usuario selecciona el template correspondiente → formulario pre-llenado.
4. Usuario completa los campos requeridos (contexto, descripción, criterios de aceptación, etc.).
5. La issue se crea con labels automáticos definidos en el frontmatter del template.
6. La issue aparece en el Project Board en la columna inicial `Icebox` (o equivalente) para priorización.

---

### Pull Request Workflow

#### 1. Preparación

- Developer encuentra issue en Project Board (columna "Ready for Sprint")
- Comenta en issue: "Trabajando en esto"
- Crea branch desde `main` actualizado:

```bash
git checkout main
git pull origin main
git checkout -b feature/nombre-descriptivo
```

#### 2. Desarrollo

Implementa cambios siguiendo `CONTRIBUTING.md`:

- Código cumple PEP 8, type hints, docstrings
- Tests añadidos/actualizados (coverage ≥25%)
- Linter pasa (`ruff check . && black . && isort .`)

Commits siguiendo Conventional Commits:

```bash
git commit -m "feat: add investment calculator module"
git commit -m "test: add unit tests for affordability calculations"
```

#### 3. Pre-PR Checklist

```bash
# Ejecutar antes de abrir PR
pytest tests/ -v                    # Tests pasan
pytest --cov=src --cov-report=html  # Coverage ≥25%
ruff check .                        # No errores
black .                             # Código formateado
isort .                             # Imports ordenados
```

#### 4. Abrir Pull Request

- Push branch: `git push origin feature/nombre-descriptivo`
- GitHub → "New Pull Request"
- Template se carga automáticamente (`.github/pull_request_template.md`)
- Completar todas las secciones:
  - Descripción clara (2-3 líneas)
  - `Closes #numero` para auto-cerrar issue
  - Marcar tipo de cambio + áreas afectadas
  - ✅ Completar checklist de Definition of Done (15+ items)
  - Añadir instrucciones de testing
  - Screenshots si cambios en UI
  - Evidencia de tests (copiar output de pytest/coverage)

#### 5. Code Review

GitHub Actions CI/CD ejecuta automáticamente:

- `pytest tests/ -v`
- `ruff check .`
- `pytest --cov=src --cov-fail-under=25`

CI debe estar en ✅ verde antes de review

Reviewer usa Checklist de Revisor del template:

- Code quality (legible, SOLID, sin duplicación)
- Tests (cubren casos principales y edge cases)
- Documentation (docstrings, README actualizado)
- Architecture (sigue estructura existente)
- Security & Performance

Mínimo 1 aprobación requerida

#### 6. Merge

- Developer hace ajustes si se solicitan cambios
- Una vez aprobado:
  - Squash merge (mantener historial limpio)
  - Issue se cierra automáticamente (por `Closes #___`)
  - Tarjeta se mueve a "Done" en Project Board

Post-merge:

- Verificar CI en `main`
- Actualizar milestone progress
- Notificar en Discord/Slack si feature importante

#### 7. Roles y Responsabilidades

| Rol | Responsabilidad |
|-----|----------------|
| **Developer** | Seguir `CONTRIBUTING.md`, completar PR template, responder a feedback |
| **Reviewer** | Usar checklist de revisor, feedback constructivo, aprobar cuando cumple DoD |
| **Maintainer** (@prototyp33) | Merge final, release management, mantener quality gates |

#### 8. Tiempos Esperados

- Review inicial: < 24h (días laborables)
- Feedback del developer: < 48h
- Re-review después de cambios: < 12h
- Merge: Inmediato tras aprobación final

Si PR no tiene actividad en 7 días, se marca como `status:stale`.
