# 📘 Guía de Mejores Prácticas: GitHub Projects & Gestión Ágil

**Proyecto:** Barcelona Housing Demographics Analyzer  
**Versión del Estándar:** 1.0  
**Última actualización:** Diciembre 2025

Esta guía define cómo utilizamos GitHub Projects para mantener el flujo de trabajo eficiente, transparente y automatizado. Nuestra filosofía es **"Code meets Context"**: la gestión del proyecto vive donde vive el código.

---

## 1. Ciclo de Vida de una Issue (The Workflow)

Cada tarea debe seguir un flujo predecible desde su creación hasta su finalización. No saltamos pasos para asegurar la calidad (especialmente los Checks de Calidad de Datos - DQC).

### Estados del Tablero (Status)

| Estado | Descripción | Criterio de Entrada | Criterio de Salida |
| :--- | :--- | :--- | :--- |
| **📥 Backlog** | Ideas y tareas futuras. | Cualquiera puede crearla. | Tiene descripción clara y Label de prioridad. |
| **🎯 Ready** | Listo para trabajar en este Sprint. | Asignado a un Sprint, tiene Owner y estimación. | Developer mueve a "In Progress". |
| **🔨 In Progress** | Trabajo activo. **Límite WIP: 2**. | Developer empieza a codificar. | PR creado y vinculado. |
| **👀 In Review** | Esperando revisión de código o validación de datos. | PR abierto. Tests automáticos pasando. | PR aprobado (Merge). |
| **✅ Done** | Completado y verificado. | Código mergeado + DQC Passed. | N/A (Se archiva en 30 días). |

> **Nota:** Los estados se mueven automáticamente mediante workflows de GitHub Actions (ver `.github/workflows/project-automation.yml`).

---

## 2. Anatomía de una Issue Perfecta

No trabajamos con issues vacías. Usamos los templates configurados, pero como regla general, toda issue debe contener:

### 2.1 Título Claro

Formato: `[Prefijo] Verbo + Objeto`

- ✅ **Bien:** `[ETL] Extraer datos de API Idealista`
- ✅ **Bien:** `[S1] Investigar ID indicador renta IDESCAT`
- ❌ **Mal:** `Arreglar datos`
- ❌ **Mal:** `Bug en el código`

### 2.2 Estructura del Cuerpo

```markdown
## Objetivo
[Descripción clara del qué y por qué]

## Contexto
[Información relevante: dependencias, bloqueadores, etc.]

## Criterios de Aceptación (DoD)
- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Tests unitarios pasando

## Impacto KPI
- **KPI:** [Objetivo medible]
- **Fuente:** [IDESCAT, Incasòl, etc.]
- **Bloquea:** [Issue relacionada si aplica]
```

### 2.3 Metadatos (Campos Personalizados)

Toda issue debe tener estos campos configurados:

| Campo | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| **Impacto** | Single Select | Urgencia de la tarea | High, Medium, Low |
| **Fuente de Datos** | Single Select | Origen de los datos | IDESCAT, Incasòl, OpenData BCN |
| **Sprint** | Iteration | Sprint asignado | Sprint 1, Sprint 2 |
| **Estado DQC** | Single Select | Estado de calidad de datos | Pending, Passed, Failed |
| **KPI Objetivo** | Text | Objetivo medible | "Cobertura ≥80% para 2015-2023" |
| **Owner** | Text | Responsable | Nombre del developer |
| **Confidence** | Number | Nivel de certeza técnica (0-100) | 85 |

> **Automatización:** Los campos se pueden sincronizar automáticamente usando `python .github/scripts/project_automation.py --issue <NUM> --auto-detect`

---

## 3. Estrategia de Labels (Taxonomía)

Usamos un sistema de colores semántico (configurado por `setup_project_complete.py`) para escanear el tablero visualmente en segundos.

### 3.1 Categorías de Labels

| Color | Categoría | Labels | Uso |
| :--- | :--- | :--- | :--- |
| 🔴 **Rojo** | Prioridad/Bug | `bug`, `priority-high`, `blocked` | Urgencia crítica |
| 🟢 **Verde** | Funcionalidad | `feature`, `analysis`, `testing` | Nuevas capacidades |
| 🔵 **Azul** | Documentación/UI | `dashboard`, `documentation` | Interfaz y docs |
| 🟡 **Amarillo** | Datos | `data-extraction`, `data-quality`, `etl` | Pipelines y ETL |
| 🟣 **Púrpura** | Roadmap | `roadmap`, `sprint-1`, `sprint-2` | Hitos estratégicos |
| ⚪ **Gris** | Estado | `in-progress`, `needs-review` | Estado del trabajo |

### 3.2 Reglas de Etiquetado

1. **Mínimo 2 labels por issue:**
   - Un label de tipo (feature, bug, etc.)
   - Un label de dominio (data-extraction, dashboard, etc.)

2. **Labels de Sprint:**
   - Usar `sprint-1`, `sprint-2`, etc. para agrupar por iteración
   - Complementa el campo `Sprint` (Iteration)

3. **Labels de Fuente:**
   - `idescat`, `incasl`, `opendatabcn`, `portal-dades`
   - Debe coincidir con el campo "Fuente de Datos"

> **Automatización:** Los labels se crean automáticamente ejecutando `python .github/scripts/setup_project_complete.py`

---

## 4. Gestión de Sprints y Milestones

Es común confundir estos dos conceptos en GitHub. Aquí los diferenciamos así:

### 4.1 🔄 Iteration (Sprint)

- **Qué es:** Un bloque de tiempo de 2 semanas.
- **Uso:** Planificación táctica del equipo.
- **Configuración:** Campo `Iteration` en Project V2 (debe configurarse manualmente en la UI).
- **Ejemplo:** "Sprint 1 (Ene 1-15)", "Sprint 2 (Ene 16-31)".

### 4.2 🚩 Milestone (Hito)

- **Qué es:** Un entregable tangible o versión del software.
- **Uso:** Agrupación lógica de issues para un objetivo. Puede abarcar varios sprints.
- **Configuración:** Pestaña `Milestones` del Repo (creados automáticamente por `setup_project_complete.py`).
- **Ejemplo:** "Sprint 1: IDESCAT Integration", "Dashboard & Visualization".

> **Regla de Oro:** Una issue siempre pertenece a un Milestone (Objetivo), y temporalmente se asigna a una Iteration (Cuándo se hará).

### 4.3 Crear Issues de Sprint

Para crear issues preconfiguradas de un sprint:

```bash
# Crear issues del Sprint 1
python .github/scripts/create_sprint_issues.py

# Verificar issues creadas
gh issue list --label sprint-1
```

---

## 5. Rituales y Vistas del Tablero

Para no perderse en el mar de tareas, utilizamos las Vistas Automatizadas del Proyecto.

### 5.1 Daily Standup (Vista: "Sprint Board")

- **Frecuencia:** Diaria (15 min).
- **Foco:** Columna "In Progress" y "Blocked".
- **Pregunta:** ¿Qué impide mover esta tarjeta a la derecha hoy?
- **Acción:** Identificar bloqueadores y actualizar `Estado DQC` si aplica.

### 5.2 Sprint Planning (Vista: "Backlog Planning")

- **Frecuencia:** Cada 2 semanas (Inicio de Sprint).
- **Acción:** Arrastrar items de "Backlog" a "Ready".
- **Filtro:** Ordenar por `Impact: High` y `Confidence: High`.
- **Checklist:**
  - [ ] Issues tienen Owner asignado
  - [ ] Campo "Sprint" configurado
  - [ ] Campo "KPI Objetivo" completado
  - [ ] Labels de sprint aplicados

### 5.3 Stakeholder Review (Vista: "Roadmap")

- **Frecuencia:** Mensual.
- **Foco:** Vista de Timeline (Gantt).
- **Objetivo:** Ver progreso macro de los Milestones.
- **Métricas:** Completitud por Milestone, velocidad del equipo.

### 5.4 Quality Tracking (Vista: "DQC Dashboard")

- **Frecuencia:** Antes de cada release.
- **Filtro:** `Estado DQC = "Pending" OR "Failed"`.
- **Acción:** Resolver todos los items con DQC Failed antes de release.

> **Configuración:** Estas vistas deben crearse manualmente en la UI del proyecto. Ver instrucciones en `.github/scripts/README_SETUP.md`.

---

## 6. Automatización (No hagas el trabajo sucio)

Nuestro repositorio utiliza **GitHub Actions** y **Project Workflows** para reducir la burocracia.

### 6.1 Movimiento Automático

- **Issue abierta con label `roadmap`** → Se añade automáticamente al proyecto en "Backlog"
- **PR creado vinculado a issue** → Issue se mueve a "In Progress"
- **PR mergeado** → Issue se mueve a "Done" automáticamente
- **Issue cerrada** → Tarjeta se mueve a "Done" (si no está ya)

> **Workflow:** `.github/workflows/project-automation.yml`

### 6.2 Validación de Calidad (DQC)

- **No marques manualmente** el campo `Estado DQC`.
- El CI/CD ejecutará los tests de datos automáticamente.
- Si pasan → Bot actualiza el campo a `Passed`.
- Si fallan → Bot actualiza el campo a `Failed` y notifica.

> **Workflow:** `.github/workflows/data-quality.yml`

### 6.3 Sincronización de Issues con Proyecto

Para sincronizar una issue existente con el proyecto:

```bash
# Sincronizar con auto-detección de campos
python .github/scripts/project_automation.py --issue 24 --auto-detect

# Sincronizar con campos específicos
python .github/scripts/project_automation.py \
  --issue 24 \
  --impact High \
  --fuente IDESCAT \
  --sprint "Sprint 1" \
  --kpi-objetivo "Cobertura ≥80%"
```

### 6.4 Infraestructura como Código

- **No crees labels o milestones manualmente en la UI.**
- Edita `.github/scripts/setup_project_complete.py` y ejecuta:
  ```bash
  python .github/scripts/setup_project_complete.py
  ```
- Mantén la configuración versionada en el repositorio.

---

## 7. Checklist de "Definition of Done" (DoD)

Antes de cerrar cualquier issue, verifica:

### 7.1 Checklist General

- [ ] Código subido a `main` mediante Pull Request.
- [ ] Tests unitarios creados y pasando (Cobertura > 80%).
- [ ] Documentación actualizada (Docstrings o README).
- [ ] Issue cerrada y vinculada al PR (usando `Closes #XX`).

### 7.2 Checklist para Proyectos de Datos

- [ ] Dataset generado tiene su diccionario de datos actualizado.
- [ ] Check de nulos y duplicados verificado.
- [ ] Campo `Estado DQC = "Passed"`.
- [ ] Datos validados contra esquema de base de datos.
- [ ] Scripts de ETL documentados.

### 7.3 Checklist para Features de Dashboard

- [ ] Componente renderiza correctamente en Streamlit.
- [ ] Filtros funcionan correctamente.
- [ ] Visualizaciones son responsivas.
- [ ] Documentación de uso actualizada.

> **Automatización:** El workflow `data-quality.yml` verifica automáticamente algunos de estos criterios.

---

## 8. Gestión de Pull Requests (PRs)

### 8.1 Tamaño y Estructura

- **Tamaño:** PRs pequeños (< 400 líneas). "Divide y vencerás".
- **Título:** Usa [Conventional Commits](https://www.conventionalcommits.org/).
  - ✅ `feat(etl): añadir extractor idescat`
  - ✅ `fix(database): corregir migración de esquema`
  - ✅ `docs: actualizar guía de setup`
  - ❌ `Cambios varios`

### 8.2 Vinculación con Issues

Usa palabras clave en la descripción del PR para cerrar issues automáticamente:

- `Closes #12` - Cierra la issue #12
- `Fixes #45` - Marca como resuelta la issue #45
- `Relates to #67` - Vincula sin cerrar

### 8.3 Template de PR

```markdown
## Descripción
[Qué cambia este PR]

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Refactor
- [ ] Documentación

## Checklist
- [ ] Tests pasando
- [ ] Documentación actualizada
- [ ] Sin breaking changes (o documentados)

## Issue Relacionada
Closes #XX
```

---

## 9. Métricas y Reportes

### 9.1 Generar Métricas del Proyecto

Para obtener un reporte de métricas del proyecto:

```bash
# Ver métricas en consola
python .github/scripts/project_metrics.py

# Exportar a JSON
python .github/scripts/project_metrics.py --export-json metrics.json
```

### 9.2 KPIs a Monitorear

- **Velocidad del equipo:** Issues completadas por sprint
- **Lead Time:** Tiempo desde Backlog hasta Done
- **Tasa de DQC Passed:** % de issues con `Estado DQC = Passed`
- **Cobertura de fuentes:** Issues por `Fuente de Datos`

---

## 10. Setup Inicial del Proyecto

### 10.1 Configuración Completa

Para configurar el proyecto desde cero:

```bash
# 1. Configurar token
export GITHUB_TOKEN="ghp_xxx"

# 2. Ejecutar setup completo
python .github/scripts/setup_project_complete.py

# 3. Crear issues del Sprint 1
python .github/scripts/create_sprint_issues.py

# 4. Sincronizar issues con proyecto
python .github/scripts/project_automation.py --issue <NUM> --auto-detect
```

### 10.2 Verificación

Después del setup, verifica:

- [ ] Labels creados (30+)
- [ ] Milestones creados (7)
- [ ] Campos personalizados configurados en Project V2
- [ ] Campo "Iteration" configurado manualmente en la UI
- [ ] Vistas del proyecto creadas
- [ ] Workflows de GitHub Actions activos

> **Documentación completa:** Ver `.github/scripts/README_SETUP.md`

---

## 11. Troubleshooting

### 11.1 Issue no se añade al proyecto

**Problema:** Issue creada pero no aparece en el tablero.

**Solución:**
```bash
# Sincronizar manualmente
python .github/scripts/project_automation.py --issue <NUM> --auto-detect
```

### 11.2 Campo personalizado no existe

**Problema:** Error al actualizar campo personalizado.

**Solución:**
1. Verificar que el campo existe en Project Settings
2. Ejecutar `setup_project_complete.py` para crear campos faltantes
3. Verificar nombre exacto del campo (case-sensitive)

### 11.3 Workflow no se ejecuta

**Problema:** GitHub Actions no mueve issues automáticamente.

**Solución:**
1. Verificar que el workflow está activo en `.github/workflows/`
2. Verificar permisos del token (necesita `project` scope)
3. Revisar logs en Actions tab

---

## 12. Referencias

- [GitHub Projects v2 Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Project Management Playbook](./PROJECT_MANAGEMENT.md)
- [Setup Scripts README](../.github/scripts/README_SETUP.md)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Documento generado automáticamente para el proyecto Barcelona Housing Demographics Analyzer.**  
**Mantener actualizado según evolucione el flujo de trabajo del equipo.**

