# Resumen: Propuesta de Reorganización del Proyecto

**Fecha**: 2025-12-19  
**Estado**: Propuesta lista para revisión

---

## 📋 Documentos Creados

1. **`docs/PROJECT_STRUCTURE_PROPOSAL.md`** ⭐
   - Análisis de estructura actual
   - Propuesta de reorganización por feature/componente
   - Plan de migración gradual (4 fases)
   - Checklist de implementación

2. **`docs/architecture/DEPENDENCIES.md`** ⭐
   - Reglas explícitas de dependencias entre módulos
   - Ejemplos de buenas y malas prácticas
   - Checklist de revisión antes de crear imports

3. **`spikes/README.md`** ⭐
   - Guía de qué es un spike y cómo usarlo
   - Ciclo de vida de un spike
   - Cuándo migrar código a producción

4. **`CONTRIBUTING.md`** (actualizado)
   - Añadidas reglas de estructura y dependencias

---

## 🎯 Problemas Identificados

1. **Scripts dispersos**: 71 archivos en `scripts/` sin organización clara
2. **Documentación dispersa**: 50+ archivos en `docs/` sin estructura
3. **Spike como subproyecto**: `spike-data-validation/` confunde qué es oficial vs temporal
4. **Dependencias no claras**: Sin documentación de qué puede importar qué

---

## ✅ Soluciones Propuestas

### Estructura por Feature/Componente
- Agrupar scripts por funcionalidad (`scripts/etl/`, `scripts/analysis/`)
- Organizar documentación por tipo (`docs/architecture/`, `docs/guides/`)
- Separar spikes de producción (`spikes/` vs `src/`)

### Reglas de Dependencias Explícitas
- `src/` → Código de producción (no importa de scripts/spikes)
- `scripts/` → Puede usar `src/` pero no otros scripts
- `spikes/` → Puede usar `src/` pero no scripts/
- Evitar ciclos entre módulos

### Migración Gradual
- Fase 1: Reorganizar scripts (bajo riesgo)
- Fase 2: Consolidar código reutilizable (medio riesgo)
- Fase 3: Reorganizar documentación (bajo riesgo)
- Fase 4: Validar dependencias (alto impacto)

---

## 🚀 Próximos Pasos Recomendados

### Inmediato (Sin Romper Código)
1. ✅ Revisar propuesta en `docs/PROJECT_STRUCTURE_PROPOSAL.md`
2. ✅ Aplicar reglas de dependencias en código nuevo
3. ✅ Documentar estructura oficial en `README.md`

### Corto Plazo (1-2 semanas)
1. Reorganizar `scripts/` por feature (Fase 1)
2. Reorganizar `docs/` por tipo (Fase 3)
3. Crear `spikes/README.md` y mover `spike-data-validation/` → `spikes/data-validation/`

### Medio Plazo (1 mes)
1. Consolidar código reutilizable de spike a `src/` (Fase 2)
2. Implementar validación de dependencias (Fase 4)

---

## 📊 Impacto Esperado

### Beneficios
- ✅ Navegación más rápida (encontrar código por feature)
- ✅ Onboarding más fácil (estructura predecible)
- ✅ Menos acoplamiento (límites claros)
- ✅ Reutilización (código del spike disponible para producción)

### Riesgos
- ⚠️ Migración requiere tiempo y cuidado
- ⚠️ Puede romper imports existentes si no se hace gradualmente
- ⚠️ Requiere disciplina del equipo para mantener estructura

---

## 🔗 Referencias

- Propuesta completa: [`docs/PROJECT_STRUCTURE_PROPOSAL.md`](./PROJECT_STRUCTURE_PROPOSAL.md)
- Reglas de dependencias: [`docs/architecture/DEPENDENCIES.md`](./architecture/DEPENDENCIES.md)
- Guía de spikes: [`spikes/README.md`](../spikes/README.md)

---

**Próxima acción**: Revisar propuesta y decidir qué fases implementar primero.

