# 📋 Guía Rápida: Organización del Tablero

**Fecha:** Noviembre 2025  
**Proyecto:** Data Expansion Roadmap

Esta guía te ayuda a organizar las issues en el tablero de GitHub Projects según el plan de sprints.

---

## 🎯 Estado Actual del Sprint 0

**Issue #23: [S0] Setup operativo + Baseline KPIs**

✅ **Completado:**
- [x] Backup DB creado: `data/processed/database_backup_baseline.db`
- [x] Baseline report: `docs/reports/baseline_2025Q4.md`
- [x] Project Charter enlazado en README

**Acción:** Mover esta tarjeta a la columna **"Done"** en el tablero.

---

## 🚀 Sprint 1: Renta Histórica (Semanas 2-4)

**Objetivo:** Implementar extractor IDESCAT y pipeline de renta histórica.

### Issues del Sprint 1:

1. **Issue #24: [S1] Implementar IDESCATExtractor + tests**
   - **Columna:** `Ready (Sprint 1)` → `In Progress` (cuando empieces a trabajar)
   - **Etiquetas:** `sprint-1`, `roadmap`, `data-extraction`

2. **Issue #25: [S2] Pipeline renta histórica**
   - **Columna:** `Ready (Sprint 1)` (depende de S1)
   - **Etiquetas:** `sprint-1`, `roadmap`, `etl`, `database`

**Acción:** Arrastra ambas tarjetas a la columna **"Ready (Sprint 1)"** en el tablero.

---

## 📦 Sprint 2: Alquiler y Dashboard (Semanas 5-7)

**Objetivo:** Integrar datos de alquiler Incasòl y visualizar asequibilidad.

### Issues del Sprint 2:

1. **Issue #26: [S3] Dashboard Índice de Asequibilidad**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-2`, `dashboard`, `streamlit`

2. **Issue #27: [S4] Integrar datos de alquiler Incasòl**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-2`, `roadmap`, `data-extraction`

3. **Issue #28: [S5] Enriquecer fact_precios con Incasòl**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-2`, `dashboard`, `etl`

**Acción:** Deja estas tarjetas en **"Backlog"** por ahora.

---

## 🔍 Sprint 3: Contexto Socioeconómico (Semanas 8-9)

**Objetivo:** Añadir paro, estudios y estructura de hogares.

### Issues del Sprint 3:

1. **Issue #29: [S6] fact_socioeconomico (paro, estudios, hogares)**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-3`, `roadmap`, `data-extraction`, `etl`

2. **Issue #30: [S7] Dashboard Vulnerabilidad**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-3`, `dashboard`, `streamlit`

**Acción:** Deja estas tarjetas en **"Backlog"**.

---

## 📚 Sprint 4: Documentación (Semana 10)

**Objetivo:** Storytelling y documentación final.

### Issues del Sprint 4:

1. **Issue #31: [S8] Storytelling y documentación**
   - **Columna:** `Backlog`
   - **Etiquetas:** `sprint-4`, `documentation`

**Acción:** Deja esta tarjeta en **"Backlog"**.

---

## 🎨 Cómo Organizar el Tablero (Pasos Visuales)

1. **Abre tu tablero "Data Expansion Roadmap"** en GitHub.

2. **Filtra por etiqueta:**
   - Haz clic en el filtro de la parte superior.
   - Selecciona `sprint-0` → Mueve la tarjeta a **"Done"**.
   - Selecciona `sprint-1` → Mueve ambas tarjetas a **"Ready (Sprint 1)"**.

3. **Agrupa por Sprint (Opcional):**
   - En la vista de tabla, agrega un agrupamiento por campo personalizado `Sprint`.
   - Esto te permitirá ver todas las issues del Sprint 1 juntas.

4. **Configura campos personalizados:**
   - Para cada tarjeta en `Ready (Sprint 1)`, completa:
     - **Impacto:** `High` (ambas son críticas para el roadmap)
     - **Fuente de Datos:** `IDESCAT` (para S1 y S2)
     - **Sprint:** `Sprint 1` (si tienes el campo de iteración configurado)
     - **KPI objetivo:** 
       - S1: "Extractor funcional con tests pasando"
       - S2: "Tabla fact_renta_hist con >=80% cobertura 2015-2023"

---

## ✅ Checklist de Organización

- [ ] Issue #23 movida a **"Done"**
- [ ] Issues #24 y #25 movidas a **"Ready (Sprint 1)"**
- [ ] Issues #26, #27, #28 en **"Backlog"** (Sprint 2)
- [ ] Issues #29, #30 en **"Backlog"** (Sprint 3)
- [ ] Issue #31 en **"Backlog"** (Sprint 4)
- [ ] Campos personalizados completados para Sprint 1

---

**Próximo paso:** Una vez organizado el tablero, procede con el **Sprint 1** comenzando por la Issue #24 (IDESCATExtractor).

