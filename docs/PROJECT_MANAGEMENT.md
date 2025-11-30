# Project Management Playbook

Este documento describe cómo estructurar y operar el GitHub Project "Data Expansion Roadmap" en línea con el [Project Charter](PROJECT_CHARTER.md) y el roadmap técnico (`docs/DATA_EXPANSION_ROADMAP.md`).

## 1. Tablero

- **Plantilla**: GitHub Projects (Board).
- **Columnas**: `Backlog` → `Ready (Sprint n)` → `In Progress` → `QA / Blocked` → `Done`.
- **Swimlanes / vistas**: Agrupar por `Fuente de Datos` o `Sprint` para evaluar cobertura.
- **WIP rule**: máximo 2 tarjetas en `In Progress` (respeta la capacidad de 8-15 h/semana del AI-Augmented Engineer).

## 2. Campos Personalizados

| Campo | Tipo | Uso |
|-------|------|-----|
| `Impacto` | Single select (`High`, `Medium`, `Low`) | Prioriza según objetivos de asequibilidad. |
| `Fuente de Datos` | Single select (`IDESCAT`, `Incasòl`, `OpenData BCN`, `Portal Dades`, `Internal`) | Trazabilidad y filtros. |
| `Sprint` | Iterations (2 semanas) | Refleja S0…S8 del roadmap. |
| `Estado DQC` | Single select (`Pending`, `Passed`, `Failed`) | Garantiza calidad antes de cerrar. |
| `Owner` | Text | Rol responsable (DE, DA, PM). |
| `KPI objetivo` | Text/Number | Documenta el resultado que impulsa la tarjeta. |

> Al mover una tarjeta a `Ready (Sprint n)` se debe completar Impacto, Fuente, Sprint y KPI objetivo.

## 3. Automatizaciones y Jerarquía

### Automatizaciones
1. **Auto-mover a Done** cuando el issue se cierre.
2. **Escalamiento**: si una tarjeta lleva 7 días en `In Progress`, mover a `QA / Blocked` y añadir comentario solicitando revisión.
3. **Checklist automático** al entrar en `In Progress` (Código, DQC, Tests, Docs, Demo) para asegurar DoD consistente.

### Jerarquía de Trabajo (Sub-issues)
Para mantener el tablero limpio y manejable, usamos **Sub-issues** para tareas complejas que superan los 2-3 días de trabajo.

- **Nivel 1 (Epic/Feature):** La Issue principal en el Board (ej. `[S6] fact_socioeconomico`).
- **Nivel 2 (Task):** Si un checklist item es complejo (ej. "Extractor Paro"), conviértelo en Issue hija.
  - *Cómo:* En la issue padre, hover sobre el checklist item → botón "Convert to issue".
  - *Beneficio:* Permite trazar PRs específicos y discusiones técnicas sin ensuciar la issue principal.

## 4. Métricas y Reportes (Insights)

El proyecto utiliza las herramientas nativas de GitHub para seguimiento visual:

1. **Insights (Gráficos):**
   - **Burn-up Chart:** Progreso acumulado vs. Alcance total. Revisar en cada demo quincenal.
   - **Velocity:** Items completados por iteración. Ayuda a calibrar la carga del "Ready".

2. **Status Updates:**
   - Usar la función nativa "Status updates" del proyecto para reportes quincenales.
   - **Formato:** "On Track" / "At Risk" / "Off Track".
   - **Contenido:** Resumen ejecutivo, KPIs logrados y blockers. Sustituye reportes manuales en markdown dispersos.

## 5. Workflows (GitHub Actions)

- `project-sync.yml`: cuando una PR etiquetada `roadmap` se fusiona → mover tarjeta a `QA / Blocked` para ejecutar DQCs finales.
- `etl-smoke.yml`: correr `pytest`, `tests/test_pipeline.py` y `scripts/process_and_load.py --dry-run` en cada push a una rama con tarjeta en QA.
- `dashboard-demo.yml`: `workflow_dispatch` para generar screenshot/GIF del dashboard e incluirlo en la issue.
- `kpi-update.yml`: actualiza `data/kpi_progress.json` con los KPI logrados al cerrar una issue.

*(Los workflows pueden añadirse progresivamente; este documento actúa como guía.)*

## 6. Plantillas y Estándares

- **Issue Template** (`.github/ISSUE_TEMPLATE.md`): incluida en el repo. Obliga a detallar objetivo, DoD, KPI y riesgos.
- **PR Template** (`.github/PULL_REQUEST_TEMPLATE.md`): resume cambios, impacto, DQC y checklist.
- **Script `setup_project.sh`**: crea issues masivas (sin vincular a Projects) para acelerar la planificación.

## 7. Rituales

| Ritmo | Actividad | Objetivo |
|-------|-----------|----------|
| Semanal | Revisión de Insights | Verificar velocidad y cuellos de botella. |
| Quincenal | Status Update | Publicar actualización oficial en la UI del Proyecto. |
| Mensual | Retro de Calidad | Revisar métricas de DQC y cobertura de tests. |

## 8. KPIs de Gobernanza

- % de issues con `Estado DQC = Passed` → objetivo 100%.
- Lead Time (Backlog → Done) ≤ 4 semanas.
- Cobertura de fuentes: todas las fuentes prioritarias (IDESCAT, Incasòl, OpenData BCN) con al menos una entrega en el trimestre.

## 9. Uso del Board

1. **Crear issue** usando el template (`gh issue create` o UI).
2. **Agregar al board** vía `+ Add item → Issue` en la columna `Backlog`.
3. **Refinar**: mover a `Ready (Sprint n)` y completar campos obligatorios.
4. **Trabajar**: mover a `In Progress`. Si es complejo, **crear sub-issues**.
5. **Cerrar**: tras DQCs y demo, cerrar issue → tarjeta pasa a `Done` automáticamente.

Este playbook asegura que el GitHub Project refleje la visión de un desarrollador aumentado por IA, manteniendo transparencia, calidad y enfoque en los KPIs del Mapa de Rentabilidad.
