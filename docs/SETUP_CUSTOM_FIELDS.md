# 🔧 Guía: Configurar Campos Personalizados en GitHub Projects

**Proyecto:** Data Expansion Roadmap  
**Tiempo estimado:** 5-7 minutos

Esta guía te lleva paso a paso para crear los 6 campos personalizados necesarios según el [Project Management Playbook](PROJECT_MANAGEMENT.md).

---

## 📍 Paso 1: Acceder a la Configuración del Proyecto

1. Ve a tu tablero **"Data Expansion Roadmap"** en GitHub.
2. Haz clic en el botón **"..."** (tres puntos) en la esquina superior derecha del tablero.
3. Selecciona **"Settings"** (Configuración).

---

## 🏷️ Paso 2: Crear Campos Personalizados

En la sección **"Fields"** (Campos), haz clic en **"+ Add field"** para cada uno de los siguientes:

---

### Campo 1: Impacto (Single select)

1. **Tipo:** Selecciona **"Single select"**.
2. **Nombre del campo:** `Impacto`
3. **Opciones:** Haz clic en **"+ Add option"** y añade:
   - `High` (color: Rojo `#EB5757`)
   - `Medium` (color: Naranja `#F2994A`)
   - `Low` (color: Verde `#27AE60`)
4. Haz clic en **"Save"**.

**Uso:** Prioriza según objetivos de asequibilidad.

---

### Campo 2: Fuente de Datos (Single select)

1. **Tipo:** Selecciona **"Single select"**.
2. **Nombre del campo:** `Fuente de Datos`
3. **Opciones:** Añade:
   - `IDESCAT` (color: Azul `#2F80ED`)
   - `Incasòl` (color: Púrpura `#9B51E0`)
   - `OpenData BCN` (color: Verde `#27AE60`)
   - `Portal Dades` (color: Naranja `#F2994A`)
   - `Internal` (color: Gris `#95A5A6`)
4. Haz clic en **"Save"**.

**Uso:** Trazabilidad y filtros por fuente de datos.

---

### Campo 3: Sprint (Iterations o Single select)

**Opción A: Usar Iterations (Recomendado si GitHub lo permite)**

1. **Tipo:** Selecciona **"Iterations"** (si está disponible).
2. **Nombre del campo:** `Sprint`
3. **Duración:** 2 semanas
4. **Crear iteraciones:**
   - Sprint 0 (ya completado)
   - Sprint 1 (Semanas 2-4)
   - Sprint 2 (Semanas 5-7)
   - Sprint 3 (Semanas 8-9)
   - Sprint 4 (Semana 10)
5. Haz clic en **"Save"**.

**Opción B: Usar Single select (Si Iterations no está disponible)**

1. **Tipo:** Selecciona **"Single select"**.
2. **Nombre del campo:** `Sprint`
3. **Opciones:** Añade:
   - `Sprint 0` (color: Gris `#95A5A6`)
   - `Sprint 1` (color: Azul `#2F80ED`)
   - `Sprint 2` (color: Verde `#27AE60`)
   - `Sprint 3` (color: Naranja `#F2994A`)
   - `Sprint 4` (color: Púrpura `#9B51E0`)
4. Haz clic en **"Save"**.

**Uso:** Refleja S0…S8 del roadmap.

---

### Campo 4: Estado DQC (Single select)

1. **Tipo:** Selecciona **"Single select"**.
2. **Nombre del campo:** `Estado DQC`
3. **Opciones:** Añade:
   - `Pending` (color: Amarillo `#F2C94C`)
   - `Passed` (color: Verde `#27AE60`)
   - `Failed` (color: Rojo `#EB5757`)
4. Haz clic en **"Save"**.

**Uso:** Garantiza calidad antes de cerrar (Data Quality Check).

---

### Campo 5: Owner (Text)

1. **Tipo:** Selecciona **"Text"**.
2. **Nombre del campo:** `Owner`
3. Haz clic en **"Save"**.

**Uso:** Rol responsable (DE = Data Engineer, DA = Data Analyst, PM = Product Manager).

---

### Campo 6: KPI objetivo (Text)

1. **Tipo:** Selecciona **"Text"** (o **"Number"** si prefieres solo números).
2. **Nombre del campo:** `KPI objetivo`
3. Haz clic en **"Save"**.

**Uso:** Documenta el resultado que impulsa la tarjeta (ej. "Extractor funcional con tests pasando").

---

## ✅ Paso 3: Verificar que los Campos Funcionan

1. Cierra la configuración y vuelve al tablero.
2. Haz clic en cualquier tarjeta (issue) del tablero.
3. En el panel lateral derecho, deberías ver todos los campos personalizados que acabas de crear.
4. Prueba a completar un campo (ej. selecciona `High` en "Impacto" para la Issue #24).

---

## 🎯 Paso 4: Completar Campos para Sprint 1

Ahora que los campos están creados, completa los valores para las issues del Sprint 1:

### Issue #24: [S1] Implementar IDESCATExtractor + tests

- **Impacto:** `High`
- **Fuente de Datos:** `IDESCAT`
- **Sprint:** `Sprint 1` (o la iteración correspondiente)
- **Estado DQC:** `Pending` (por defecto)
- **Owner:** `DE` (Data Engineer)
- **KPI objetivo:** `Extractor funcional con tests pasando`

### Issue #25: [S2] Pipeline renta histórica

- **Impacto:** `High`
- **Fuente de Datos:** `IDESCAT`
- **Sprint:** `Sprint 1`
- **Estado DQC:** `Pending`
- **Owner:** `DE`
- **KPI objetivo:** `Tabla fact_renta_hist con >=80% cobertura 2015-2023`

---

## 🔄 Paso 5: Configurar Automatización Básica

1. En la configuración del proyecto, ve a la sección **"Workflows"** (Flujos de trabajo).
2. Busca el workflow **"When an issue is closed"**.
3. Actívalo y configura:
   - **Action:** `Set status to Done`
   - **Status field:** Selecciona el campo de estado del proyecto (no el campo personalizado, sino el estado nativo de la columna).

Esto hará que cuando cierres un issue, la tarjeta se mueva automáticamente a la columna "Done".

---

## ✅ Checklist Final

- [ ] Campo "Impacto" creado con 3 opciones (High, Medium, Low)
- [ ] Campo "Fuente de Datos" creado con 5 opciones
- [ ] Campo "Sprint" creado (Iterations o Single select)
- [ ] Campo "Estado DQC" creado con 3 opciones
- [ ] Campo "Owner" creado (Text)
- [ ] Campo "KPI objetivo" creado (Text)
- [ ] Campos completados para Issues #24 y #25
- [ ] Automatización "Auto-mover a Done" activada

---

**¡Listo!** Una vez completado este checklist, tu tablero estará 100% configurado y listo para empezar el Sprint 1. 🚀

**Próximo paso:** Comenzar con la Issue #24 ([S1] IDESCATExtractor).

