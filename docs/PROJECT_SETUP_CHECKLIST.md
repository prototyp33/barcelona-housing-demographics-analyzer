# ✅ Checklist de Configuración del Proyecto

**Proyecto:** Data Expansion Roadmap  
**Fecha de Verificación:** Noviembre 2025

Este checklist asegura que el tablero de GitHub Projects está completamente configurado según el [Project Management Playbook](PROJECT_MANAGEMENT.md).

---

## 📋 Columnas del Tablero

Verifica que tienes estas **5 columnas** en este orden:

- [ ] **Backlog** - Tareas planificadas, ordenadas por prioridad
- [ ] **Ready (Sprint n)** - Tarjetas comprometidas para el sprint actual (se actualiza quincenalmente)
- [ ] **In Progress** - Trabajo activo (máximo WIP = 2)
- [ ] **QA / Blocked** - Tareas esperando validación, datos o dependencias
- [ ] **Done** - Entregables completados (mantener histórico del trimestre)

**Nota:** Si tienes una columna genérica "Todo" o "To do", puedes renombrarla a "Backlog" o eliminarla si no la usas.

---

## 🏷️ Campos Personalizados

Verifica que tienes estos **6 campos personalizados** configurados:

### 1. Impacto (Single select)
- [ ] Valores: `High`, `Medium`, `Low`
- [ ] Uso: Prioriza según objetivos de asequibilidad

### 2. Fuente de Datos (Single select)
- [ ] Valores: `IDESCAT`, `Incasòl`, `OpenData BCN`, `Portal Dades`, `Internal`
- [ ] Uso: Trazabilidad y filtros

### 3. Sprint (Iterations - Opcional, o Single select)
- [ ] Si usas Iterations: Configura sprints de 2 semanas (Sprint 1, Sprint 2, etc.)
- [ ] Si usas Single select: Valores `Sprint 0`, `Sprint 1`, `Sprint 2`, `Sprint 3`, `Sprint 4`
- [ ] Uso: Refleja S0…S8 del roadmap

### 4. Estado DQC (Single select)
- [ ] Valores: `Pending`, `Passed`, `Failed`
- [ ] Uso: Garantiza calidad antes de cerrar

### 5. Owner (Text)
- [ ] Uso: Rol responsable (DE, DA, PM)

### 6. KPI objetivo (Text o Number)
- [ ] Uso: Documenta el resultado que impulsa la tarjeta

**Cómo verificar:** En cualquier tarjeta del tablero, haz clic en ella y verifica que aparecen estos campos en el panel lateral.

---

## 🔄 Automatizaciones (Built-in Workflows)

Verifica que tienes estas automatizaciones activas:

- [ ] **Auto-mover a Done:** Cuando un issue se cierra, la tarjeta se mueve automáticamente a "Done"
  - *Cómo activar:* En la configuración del proyecto → Automatizations → Activar "When an issue is closed, set status to Done"

- [ ] **Auto-archivar:** (Opcional) Archivar elementos en "Done" después de 30 días
  - *Cómo activar:* Configuración → Auto-archive items in "Done" after 30 days

**Nota:** La automatización de "Escalamiento" (mover a QA/Blocked después de 7 días) requiere GitHub Actions personalizado (ver `.github/workflows/`).

---

## 📊 Vistas y Agrupaciones

### Vista de Tabla (Recomendada para planificación)
- [ ] Agrupar por: `Sprint` o `Fuente de Datos`
- [ ] Filtrar por: `Estado DQC = Pending` (para ver qué necesita revisión)
- [ ] Ordenar por: `Impacto` (High primero)

### Vista de Tablero (Recomendada para ejecución)
- [ ] Agrupar por: `Sprint` (opcional, para ver swimlanes)
- [ ] Filtrar por: `sprint-1` (cuando trabajas en Sprint 1)

---

## 🎯 Organización Inicial de Issues

Verifica que las issues están organizadas así:

- [ ] **Issue #23 ([S0])** → Columna: **"Done"**
- [ ] **Issues #24, #25 ([S1], [S2])** → Columna: **"Ready (Sprint 1)"**
- [ ] **Issues #26, #27, #28 ([S3], [S4], [S5])** → Columna: **"Backlog"**
- [ ] **Issues #29, #30 ([S6], [S7])** → Columna: **"Backlog"**
- [ ] **Issue #31 ([S8])** → Columna: **"Backlog"**

---

## 📝 Campos Completados en Sprint 1

Para las tarjetas en "Ready (Sprint 1)", verifica que tienen:

- [ ] **Impacto:** `High`
- [ ] **Fuente de Datos:** `IDESCAT`
- [ ] **Sprint:** `Sprint 1` (o etiqueta `sprint-1`)
- [ ] **KPI objetivo:** 
  - S1: "Extractor funcional con tests pasando"
  - S2: "Tabla fact_renta_hist con >=80% cobertura 2015-2023"

---

## 🔗 Enlaces y Documentación

- [ ] README del proyecto configurado (ver `docs/PROJECT_MANAGEMENT.md` sección README)
- [ ] Enlaces a documentación:
  - [Project Charter](PROJECT_CHARTER.md)
  - [Roadmap Técnico](DATA_EXPANSION_ROADMAP.md)
  - [Playbook de Gestión](PROJECT_MANAGEMENT.md)

---

## ✅ Verificación Final

- [ ] Todas las columnas están en el orden correcto
- [ ] Todos los campos personalizados están creados y funcionando
- [ ] Las automatizaciones básicas están activas
- [ ] Las issues están organizadas según el plan de sprints
- [ ] Los campos están completados para Sprint 1

---

**Si todos los items están marcados, tu tablero está 100% configurado y listo para empezar el Sprint 1.** 🚀

**Próximo paso:** Comenzar con la Issue #24 ([S1] IDESCATExtractor).

