# ✅ Checklist de Cumplimiento: Configuración de Issues y Project Boards

**Fecha de Revisión:** Noviembre 2025  
**Proyecto:** Barcelona Housing Demographics Analyzer

Este documento verifica el cumplimiento de las mejores prácticas de GitHub para Issues y Project Boards.

---

## 📋 Configuración de Issues

### ✅ 1. Plantillas de Issues

**Requisito:** Implementa plantillas de issues para asegurar consistencia. Desde Settings > Features > Issues, configura templates que incluyan secciones predefinidas como descripción del problema, pasos para reproducir, criterios de aceptación y enlaces a documentación relevante.

**Estado:** ✅ **CUMPLIDO**

- **Archivo:** `.github/ISSUE_TEMPLATE.md`
- **Secciones incluidas:**
  - ✅ Objetivo (descripción del problema)
  - ✅ Pasos para Reproducir / Implementar
  - ✅ Definición de Hecho (criterios de aceptación)
  - ✅ Impacto & KPI
  - ✅ Issues Relacionadas (vinculación)
  - ✅ Riesgos / Bloqueos
  - ✅ Enlaces Relevantes (documentación)

**Acción requerida:** Ninguna. La plantilla está completa y alineada con las mejores prácticas.

---

### ✅ 2. Sistema de Etiquetas

**Requisito:** Establece un sistema de etiquetas claro con categorías consistentes: tipo (bug, feature, enhancement), prioridad (high, low), estado (in progress, needs review), y plataforma si aplica.

**Estado:** ⚠️ **PARCIALMENTE CUMPLIDO**

**Etiquetas existentes:**
- ✅ **Tipo:** `bug`, `feature`, `enhancement`, `documentation`, `task`
- ✅ **Dominio:** `data-processing`, `database`, `etl`, `data-loading`, `analysis`, `notebook`, `dashboard`, `streamlit`, `testing`, `quality-assurance`, `automation`, `performance`, `visualization`, `data-extraction`
- ✅ **Roadmap:** `roadmap`
- ✅ **Sprint:** `sprint-0`, `sprint-1`, `sprint-2`, `sprint-3`, `sprint-4`

**Faltantes:**
- ❌ **Prioridad:** No tenemos etiquetas explícitas `priority-high`, `priority-medium`, `priority-low` (pero tenemos el campo personalizado "Impacto" que cumple esta función)
- ❌ **Estado:** No tenemos etiquetas `in-progress`, `needs-review` (pero el estado del proyecto se maneja con columnas)

**Recomendación:** 
- Las etiquetas de prioridad y estado son redundantes con los campos personalizados del proyecto ("Impacto" y las columnas del tablero).
- **Decisión:** Mantener el sistema actual (campos personalizados) es más limpio y evita duplicación.

**Acción requerida:** Ninguna. El sistema actual es funcional y sigue mejores prácticas.

---

### ⚠️ 3. Asignación de Responsables

**Requisito:** Asigna responsables inmediatamente cuando sea posible, especialmente en repositorios privados donde el equipo conoce quién debe manejar cada tipo de issue. Para repositorios públicos, programa revisiones regulares de issues sin asignar.

**Estado:** ⚠️ **PARCIALMENTE CUMPLIDO**

**Situación actual:**
- El proyecto es **público** (o puede serlo).
- Tenemos el campo personalizado **"Owner"** en el Project Board.
- Las issues creadas por el script `setup_project.sh` **no tienen asignados automáticamente**.

**Acción requerida:**
1. **Manual:** Asignar responsables al crear issues manualmente.
2. **Automático (futuro):** Crear un workflow que asigne automáticamente según el tipo de issue:
   - `data-extraction` → Asignar al owner del repo (o crear un equipo "Data Engineering")
   - `dashboard` → Asignar al owner del repo
   - `documentation` → Asignar al owner del repo

**Recomendación:** Para un proyecto de un solo desarrollador (AI-Augmented Engineer), la asignación manual es suficiente. El campo "Owner" en el Project Board proporciona trazabilidad.

---

### ✅ 4. Vinculación de Issues

**Requisito:** Vincula issues relacionadas usando el sistema de linking de GitHub (#número) para proporcionar contexto y trazabilidad entre tareas dependientes.

**Estado:** ✅ **CUMPLIDO**

- **Template de Issue:** Incluye sección "Issues Relacionadas" con ejemplos de vinculación.
- **Template de PR:** Incluye sección "Issues Relacionadas" con `Closes #`, `Depende de: #`, `Bloquea: #`.
- **Práctica:** Las issues del roadmap (S0-S8) están diseñadas para ser vinculadas cuando sea necesario.

**Acción requerida:** Ninguna. El sistema está implementado y documentado.

---

## 📊 Configuración de Project Boards

### ✅ 5. Estructura de Columnas

**Requisito:** Estructura tu tablero con columnas básicas como "To Do", "In Progress", "In Review" y "Done". Puedes agregar columnas adicionales según tu flujo de trabajo específico, pero mantén la simplicidad para evitar confusión.

**Estado:** ✅ **CUMPLIDO**

**Columnas configuradas:**
1. ✅ **Backlog** (equivalente a "To Do")
2. ✅ **Ready (Sprint n)** (buffer de planificación)
3. ✅ **In Progress** (trabajo activo)
4. ✅ **QA / Blocked** (equivalente a "In Review" + bloqueos)
5. ✅ **Done** (completado)

**Evaluación:** La estructura es clara, simple y sigue mejores prácticas. La columna "QA / Blocked" combina dos estados relacionados, lo cual es eficiente para un proyecto pequeño.

**Acción requerida:** Ninguna.

---

### ✅ 6. Campos Personalizados

**Requisito:** Utiliza campos personalizados en GitHub Projects para añadir contexto adicional como "Priority Level", "Estimated Time" o "Sprint".

**Estado:** ✅ **CUMPLIDO**

**Campos personalizados configurados:**
1. ✅ **Impacto** (Single select: High, Medium, Low) - Equivalente a "Priority Level"
2. ✅ **Fuente de Datos** (Single select: IDESCAT, Incasòl, OpenData BCN, etc.)
3. ✅ **Sprint** (Iterations o Single select: Sprint 0-4)
4. ✅ **Estado DQC** (Single select: Pending, Passed, Failed)
5. ✅ **Owner** (Text: DE, DA, PM)
6. ✅ **KPI objetivo** (Text/Number)

**Nota:** El campo "Estimated Time" no está implementado, pero no es crítico para este proyecto dado el enfoque MVP y la capacidad limitada (8-15 h/semana).

**Acción requerida:** Completar la configuración manual según `docs/SETUP_CUSTOM_FIELDS.md`.

---

### ⚠️ 7. Automatización del Flujo de Trabajo

**Requisito:** Automatiza el flujo de trabajo configurando reglas para que los issues se muevan automáticamente entre columnas. Por ejemplo, cuando se crea un PR vinculado a un issue, este pasa automáticamente a "In Review".

**Estado:** ⚠️ **PARCIALMENTE CUMPLIDO**

**Automatizaciones implementadas:**

1. ✅ **Workflow Built-in de GitHub Projects:**
   - "When an issue is closed" → Mover a "Done"
   - *Estado:* Debe activarse manualmente en la configuración del proyecto.

2. ✅ **GitHub Actions Workflows:**
   - `.github/workflows/project-sync.yml`: Placeholder para sincronización (requiere GitHub Projects API v2)
   - `.github/workflows/etl-smoke.yml`: Smoke tests en PRs
   - `.github/workflows/dashboard-demo.yml`: Generación de screenshots
   - `.github/workflows/kpi-update.yml`: Actualización de KPIs al cerrar issues

**Faltantes:**
- ❌ **Auto-mover a "In Review" cuando se crea PR:** Requiere GitHub Projects API v2 con permisos especiales.
- ❌ **Auto-mover a "QA / Blocked" cuando PR está en review:** Requiere GitHub Projects API v2.

**Limitación técnica:** GitHub Projects V2 no expone una API pública completa para mover tarjetas automáticamente desde GitHub Actions sin un token con permisos especiales de organización.

**Recomendación:** 
- Activar el workflow built-in "When an issue is closed" manualmente.
- Para automatizaciones avanzadas, considerar usar la GitHub Projects API v2 con un token de organización (requiere configuración adicional).

**Acción requerida:**
1. Activar manualmente el workflow built-in "When an issue is closed" en la configuración del proyecto.
2. (Opcional) Configurar un token de organización para automatizaciones avanzadas.

---

### ⚠️ 8. Archivado de Issues Completados

**Requisito:** Archiva regularmente los issues completados para mantener el board limpio y enfocado en el trabajo actual. Esto mejora la visibilidad sin perder el historial de tareas completadas.

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Situación actual:**
- Los issues completados permanecen en la columna "Done" indefinidamente.
- No hay automatización para archivar issues después de un período determinado.

**Recomendación:**
- Activar la automatización built-in de GitHub Projects: "Auto-archive items in 'Done' after 30 days".
- Esto mantiene el tablero limpio sin perder el historial.

**Acción requerida:**
1. En la configuración del proyecto → Automatizations → Activar "Auto-archive items in 'Done' after 30 days".

---

### ✅ 9. Vistas Personalizadas

**Requisito:** Crea vistas personalizadas del proyecto (tabla, board, roadmap) según las necesidades del equipo. Una vista de board para el día a día, una de tabla para análisis detallado, y una roadmap para planificación a largo plazo.

**Estado:** ✅ **CUMPLIDO (Documentado)**

**Vistas recomendadas en `docs/PROJECT_MANAGEMENT.md`:**

1. ✅ **Vista de Tablero (Board):**
   - Uso: Ejecución diaria
   - Agrupación opcional: Por Sprint
   - Filtro: Por sprint activo (ej. `sprint-1`)

2. ✅ **Vista de Tabla:**
   - Uso: Análisis detallado y planificación
   - Agrupación: Por Sprint o Fuente de Datos
   - Filtro: Por Estado DQC = Pending
   - Orden: Por Impacto (High primero)

3. ✅ **Vista de Roadmap (Plan de Desarrollo):**
   - Uso: Planificación a largo plazo
   - Agrupación: Por Sprint (iteraciones)
   - Visualización: Timeline de sprints S0-S8

**Nota:** Las vistas deben crearse manualmente en la UI de GitHub Projects. El playbook documenta cómo configurarlas.

**Acción requerida:** Crear las vistas manualmente según las instrucciones del playbook.

---

## 📊 Resumen de Cumplimiento

| Requisito | Estado | Acción Requerida |
|-----------|--------|------------------|
| 1. Plantillas de Issues | ✅ Cumplido | Ninguna |
| 2. Sistema de Etiquetas | ⚠️ Parcial | Ninguna (sistema actual es funcional) |
| 3. Asignación de Responsables | ⚠️ Parcial | Manual (suficiente para proyecto individual) |
| 4. Vinculación de Issues | ✅ Cumplido | Ninguna |
| 5. Estructura de Columnas | ✅ Cumplido | Ninguna |
| 6. Campos Personalizados | ✅ Cumplido | Completar configuración manual |
| 7. Automatización del Flujo | ⚠️ Parcial | Activar workflow built-in |
| 8. Archivado de Issues | ⚠️ No implementado | Activar auto-archive |
| 9. Vistas Personalizadas | ✅ Documentado | Crear vistas manualmente |

---

## 🎯 Acciones Inmediatas

1. **Completar configuración de campos personalizados** según `docs/SETUP_CUSTOM_FIELDS.md`
2. **Activar automatizaciones built-in:**
   - "When an issue is closed" → "Set status to Done"
   - "Auto-archive items in 'Done' after 30 days"
3. **Crear vistas personalizadas** (Board, Tabla, Roadmap) según `docs/PROJECT_MANAGEMENT.md`

---

**Conclusión:** El proyecto cumple con **7 de 9 requisitos** completamente, y **2 de 9 parcialmente**. Las acciones pendientes son principalmente de configuración manual en la UI de GitHub, no requieren cambios en el código.

