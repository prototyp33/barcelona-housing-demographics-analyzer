---
name: 🔬 Spike / PoC Validation
about: Template para spikes de validación de viabilidad técnica o de datos
title: "[SPIKE] "
labels: spike
assignees: ''
---

## 📌 Objetivo del Spike
Describe claramente qué se está validando en este spike. ¿Qué pregunta técnica o de viabilidad se está respondiendo?

**Duración estimada:** [X días/semanas]  
**Barrio/Ámbito piloto:** [Ej: Gràcia, Barcelona completa]

## 🎯 Criterios de Éxito (Go/No-Go)
Define los criterios cuantitativos y cualitativos que determinarán si el spike es exitoso:

- [ ] **Criterio 1:** [Descripción] - Objetivo: [valor umbral]
- [ ] **Criterio 2:** [Descripción] - Objetivo: [valor umbral]
- [ ] **Criterio 3:** [Descripción] - Objetivo: [valor umbral]

**Ejemplo:**
- Match Rate ≥70%
- R² Ajustado ≥0.55
- Sample Size ≥100
- 4/5 OLS Assumptions Pass
- Coeficientes económicamente plausibles

## 📊 Metodología
Describe el enfoque técnico que se seguirá:

1. **Fuentes de datos:**
   - [Fuente 1]: [Descripción]
   - [Fuente 2]: [Descripción]

2. **Proceso:**
   - Paso 1: [Descripción]
   - Paso 2: [Descripción]
   - Paso 3: [Descripción]

3. **Herramientas/Modelos:**
   - [Herramienta/Modelo 1]
   - [Herramienta/Modelo 2]

## 📁 Entregables
- [ ] Notebook de análisis (`spike-[nombre]/notebooks/`)
- [ ] Datos raw y procesados (`spike-[nombre]/data/`)
- [ ] Reporte de viabilidad (`spike-[nombre]/outputs/reports/VIABILITY_REPORT.pdf`)
- [ ] Decision Record (`spike-[nombre]/outputs/reports/DECISION_RECORD.md`)
- [ ] Visualizaciones clave (`spike-[nombre]/outputs/visualizations/`)

## 📅 Timeline
| Día/Fecha | Tarea | Estado |
|-----------|-------|--------|
| Día 1 | [Tarea] | ⏳ |
| Día 2 | [Tarea] | ⏳ |
| Día 3 | [Tarea] | ⏳ |

## 🔗 Issues Relacionadas
- Depende de: #
- Bloquea: #
- Relacionada con: #

## 🚧 Riesgos / Bloqueos Conocidos
- **Riesgo 1:** [Descripción] - Mitigación: [Acción]
- **Riesgo 2:** [Descripción] - Mitigación: [Acción]

## 📚 Enlaces Relevantes
- [README del Spike](spike-[nombre]/README.md)
- [Documentación relacionada](link)
- [Roadmap](docs/DATA_EXPANSION_ROADMAP.md)

## ✅ Resultado Final
**Estado:** [PENDING / IN PROGRESS / GO / NO-GO]

**Decisión:** [Se completará al final del spike]

**Próximos pasos si GO:**
- [ ] Issue de implementación creada: #
- [ ] Lecciones aprendidas documentadas
- [ ] Código/notebooks movidos a producción

**Razón si NO-GO:**
- [Descripción de por qué no es viable y qué alternativas se consideraron]

