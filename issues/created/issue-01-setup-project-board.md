---
title: [SETUP] Configurar GitHub Project Board completo
labels: ["sprint-1", "priority-critical", "type-infra", "effort-s"]
milestone: "Quick Wins Foundation"
assignees: ["prototyp33"]
---

## 🎯 Contexto

**Sprint:** Sprint 1 (Semanas 1-4)  
**Milestone:** Quick Wins Foundation  
**Esfuerzo estimado:** 2 horas  
**Fecha límite:** 2025-12-10  

**Dependencias:**
- Ninguna (setup inicial)

**Bloqueadores:**
- Ninguno conocido

**Documentación relacionada:**
- 📄 [Label Management](docs/LABEL_MANAGEMENT.md)
- 📄 [Project Management](docs/PROJECT_MANAGEMENT.md)
- 📄 [Sprint Planning](docs/SPRINT_PLANNING_COMPLETE.md)

---

## 📝 Descripción

Crear estructura completa de Project Management en GitHub siguiendo best practices para proyectos solo-developer. Esto incluye configurar el Project Board, verificar labels, y documentar el proceso.

**Valor de Negocio:**
Establece la base organizativa para gestionar eficientemente las 80 issues del roadmap de 24 semanas. Esencial para tracking y showcase profesional.

**User Story:**
> Como desarrollador, necesito un sistema organizado de gestión de proyecto en GitHub para trackear progreso y mantener disciplina de desarrollo.

---

## 🔧 Componentes Técnicos

### Tareas

- [ ] Crear Project Board "Barcelona Housing Roadmap 2025"
- [ ] Configurar 6 columnas (Backlog, To Do, In Progress, Review, Done, Blocked)
- [ ] Verificar que todos los labels estén creados (50+ labels)
- [ ] Configurar milestones (ya creados, verificar fechas)
- [ ] Añadir las 10 issues existentes al board
- [ ] Configurar vistas adicionales (Timeline, por Componente)
- [ ] Documentar proceso en `docs/PROJECT_MANAGEMENT.md`

### Columnas del Board

| Columna | Descripción | WIP Limit |
|---------|-------------|-----------|
| **Backlog** | Features no priorizadas | - |
| **To Do (Sprint Actual)** | Issues del sprint en curso | 8 |
| **In Progress** | En desarrollo activo | 2 |
| **Review** | Completado, pendiente QA | 3 |
| **Done** | Merged a `main` | - |
| **Blocked** | Dependencias externas | - |

### Vistas Adicionales

1. **Timeline por Sprint**
   - Group by: `sprint-X` label
   - Sort by: Priority

2. **Por Componente**
   - Group by: `area-*` label
   - Sort by: Status

---

## ✅ Criterios de Aceptación

- [ ] Project Board visible con estructura completa
- [ ] 6 columnas configuradas con WIP limits
- [ ] Labels aplicadas a issues existentes
- [ ] Milestones con due dates correctas (verificar fechas)
- [ ] 10 issues añadidas al board
- [ ] Vistas adicionales configuradas
- [ ] Documentación actualizada en `docs/PROJECT_MANAGEMENT.md`

---

## 🧪 Plan de Testing

### Validación Manual

1. Verificar que el board es accesible públicamente
2. Verificar que las columnas tienen los nombres correctos
3. Verificar que los WIP limits están configurados
4. Verificar que las issues se pueden mover entre columnas
5. Verificar que las vistas adicionales funcionan

---

## 📊 Métricas de Éxito

| KPI | Target | Medición |
|-----|--------|----------|
| **Tiempo de setup** | < 2 horas | Tracking manual |
| **Issues en board** | 10 issues | Verificación visual |
| **Columnas configuradas** | 6 columnas | Verificación visual |

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Limitaciones de GitHub Projects API | Media | Medio | Configuración manual si es necesario |
| Labels no sincronizados | Baja | Bajo | Ejecutar `update_labels_extended.py sync` primero |

---

## 📚 Referencias

- [GitHub Projects Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Label Management Guide](docs/LABEL_MANAGEMENT.md)
- [Project Setup Complete](docs/PROJECT_SETUP_COMPLETE.md)

---

## 🔗 Issues Relacionadas

- #86: [FEATURE-02] Calculadora de Inversión (añadir al board)
- #87: [FEATURE-13] Clustering de Barrios (añadir al board)
- #88: [FEATURE-05] Sistema de Alertas (añadir al board)

---

## 📝 Notas de Implementación

### Orden de Ejecución

1. **Paso 1:** Verificar que labels están sincronizados
   ```bash
   python scripts/project_management/update_labels_extended.py list
   ```

2. **Paso 2:** Crear Project Board desde GitHub UI
   - Settings del repo > Projects > New project
   - Template: Board (Kanban style)
   - Nombre: "Barcelona Housing Roadmap 2025"

3. **Paso 3:** Configurar columnas manualmente
   - Añadir las 6 columnas en orden
   - Configurar WIP limits

4. **Paso 4:** Añadir issues al board
   - Buscar issues #86, #87, #88, #89, #90, #91, #92, #93, #94, #95
   - Añadir a columna "To Do (Sprint Actual)"

5. **Paso 5:** Configurar vistas adicionales
   - Timeline por Sprint
   - Por Componente

6. **Paso 6:** Documentar proceso

---

**Creado:** 2025-12-03  
**Última actualización:** 2025-12-03

