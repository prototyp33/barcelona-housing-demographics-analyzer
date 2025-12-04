# Mejores Prácticas para GitHub Issues

Este documento describe las mejores prácticas para crear y gestionar GitHub Issues en el proyecto Barcelona Housing Demographics Analyzer.

---

## 📋 Estructura de una Issue

### Título
- **Formato:** `[TIPO] Descripción breve y específica`
- **Tipos:** `BUG`, `FEATURE`, `QUALITY`, `DATA`, `TEST`, `DOCS`, `REFACTOR`
- **Ejemplos:**
  - ✅ `[BUG] SQL Injection potencial: falta validación de tabla blanca en data_loader.py`
  - ✅ `[FEATURE] Completar implementación de INEExtractor`
  - ❌ `Bug en data_loader.py` (muy vago)
  - ❌ `Arreglar cosas` (no descriptivo)

### Descripción (Body)

Seguir el template estándar del proyecto con estas secciones:

#### 1. 📌 Objetivo
- **Qué:** Descripción clara y concisa del objetivo
- **Por qué:** Contexto breve sobre la importancia
- **1-2 párrafos máximo**

#### 2. 🔍 Descripción del Problema
- **Estado actual:** Qué ocurre ahora
- **Estado deseado:** Qué debería ocurrir
- **Impacto:** Cómo afecta al proyecto
- **Archivos afectados:** Lista específica con líneas si aplica
- **Ejemplos de código:** Mostrar código problemático y solución propuesta

#### 3. 📝 Pasos para Reproducir / Implementar
- **Para bugs:** Pasos numerados y reproducibles
- **Para features:** Plan de implementación por fases
- **Incluir comandos:** Ejemplos de código y comandos bash
- **Sub-issues:** Si la tarea es grande, dividir en sub-issues

#### 4. ✅ Definición de Hecho (Definition of Done)
- **Específico y medible:** No "código funciona", sino "tests pasan con cobertura >80%"
- **Checkboxes:** Usar listas con checkboxes `- [ ]`
- **Criterios claros:** Cada criterio debe ser verificable
- **Ejemplos:**
  - ✅ `- [ ] Validación implementada con test que verifica rechazo de tablas no permitidas`
  - ❌ `- [ ] Código funciona` (muy vago)

#### 5. 🎯 Impacto & KPI
- **KPI técnico:** Métrica específica (ej: "Reducción de código duplicado de 2000 a 0 líneas")
- **Objetivo:** Meta cuantificable
- **Métrica de éxito:** Cómo medir que está completado
- **Fuente de datos:** Si aplica

#### 6. 🔗 Issues Relacionadas
- **Depende de:** Issues que deben completarse antes
- **Bloquea:** Issues que no pueden avanzar sin esta
- **Relacionada con:** Issues relacionadas pero no bloqueantes
- **Sub-issues:** Lista de sub-issues si aplica
- **Formato:** Usar `#número` para vincular

#### 7. 🚧 Riesgos / Bloqueos
- **Riesgos:** Identificar riesgos potenciales y su severidad
- **Mitigación:** Cómo abordar cada riesgo
- **Dependencias externas:** APIs, servicios externos
- **Accesos/credenciales pendientes:** Si aplica
- **Datos faltantes:** Si aplica

#### 8. 📚 Enlaces Relevantes
- Documentación relacionada
- Archivos de código afectados
- Issues relacionadas
- Sub-issues

#### 9. 💡 Notas de Implementación (Opcional pero recomendado)
- **Estimación:** Tiempo estimado en horas
- **Prioridad:** 🔴 Crítica, 🟡 Alta, 🟢 Media, ⚪ Baja
- **Sprint recomendado:** En qué sprint abordar
- **Complejidad:** Baja, Media, Alta
- **Riesgo:** Bajo, Medio, Alto

---

## 🎯 Mejores Prácticas Específicas

### 1. Dividir Issues Grandes en Sub-issues

**Cuándo dividir:**
- Issue estimada en >8 horas
- Tiene múltiples fases claramente separables
- Requiere trabajo de diferentes personas/equipos

**Cómo dividir:**
- Crear issue principal con visión general
- Crear sub-issues numeradas: `[SUB-ISSUE #XX] Descripción`
- Vincular sub-issues en la issue principal
- Cada sub-issue debe ser completable independientemente

**Ejemplo:**
```
Issue #62: Eliminar código duplicado
  ├─ Sub-issue #79: Auditar referencias
  ├─ Sub-issue #80: Migrar scripts
  └─ Sub-issue #XX: Eliminar código legacy
```

### 2. Incluir Ejemplos de Código

**Siempre incluir:**
- Código problemático actual (con comentarios `# ❌`)
- Código de solución propuesta (con comentarios `# ✅`)
- Ejemplos de uso si aplica

**Formato:**
````markdown
**Código problemático:**
```python
# ❌ Problema
df = pd.read_sql(f"SELECT * FROM {table}", conn)
```

**Solución propuesta:**
```python
# ✅ Solución
ALLOWED_TABLES = ["fact_precios", "fact_demografia"]
if table not in ALLOWED_TABLES:
    raise ValueError(f"Tabla no permitida: {table}")
df = pd.read_sql(f"SELECT * FROM {table}", conn)
```
````

### 3. Criterios de Aceptación Específicos

**Buenos criterios:**
- ✅ `- [ ] Validación implementada con test que verifica rechazo de tablas no permitidas`
- ✅ `- [ ] Cobertura de tests >80% para funciones modificadas`
- ✅ `- [ ] 0 imports de data_extraction en código activo (verificado con grep)`

**Malos criterios:**
- ❌ `- [ ] Código funciona`
- ❌ `- [ ] Tests pasan` (sin especificar qué tests)
- ❌ `- [ ] Documentación actualizada` (sin especificar qué documentación)

### 4. Estimaciones Realistas

**Usar escala de tiempo:**
- **Quick wins:** <30 minutos
- **Pequeñas:** 30 min - 2 horas
- **Medianas:** 2-4 horas
- **Grandes:** 4-8 horas
- **Muy grandes:** >8 horas (dividir en sub-issues)

**Incluir desglose:**
```
Estimación: 2-3 horas total
  - Implementación: 1 hora
  - Tests: 1 hora
  - Documentación: 30 min
```

### 5. Priorización Clara

**Usar emojis para prioridad:**
- 🔴 **Crítica:** Bloquea desarrollo o afecta seguridad
- 🟡 **Alta:** Importante pero no bloqueante
- 🟢 **Media:** Mejora deseable
- ⚪ **Baja:** Nice to have

**Criterios de prioridad crítica:**
- Bugs de seguridad
- Bugs que bloquean funcionalidad core
- Issues que afectan integridad de datos
- Issues que bloquean otras issues importantes

### 6. Labels Apropiados

**Labels estándar del proyecto:**
- `bug` - Algo no funciona
- `enhancement` - Nueva funcionalidad o mejora
- `task` - Tarea a realizar
- `documentation` - Mejoras de documentación
- `testing` - Tests y QA
- `etl` - Pipeline ETL
- `data-extraction` - Extracción de datos
- `database` - Base de datos
- `streamlit` - Dashboard Streamlit
- `quality-assurance` - Aseguramiento de calidad

**Usar múltiples labels cuando aplique:**
- `bug`, `database`, `etl` - Bug en ETL relacionado con base de datos
- `enhancement`, `data-extraction`, `task` - Feature de extracción de datos

### 7. Vincular Issues Correctamente

**Tipos de relaciones:**
- **Depende de:** Issue que debe completarse antes
- **Bloquea:** Issue que no puede avanzar sin esta
- **Relacionada con:** Issue relacionada pero no bloqueante
- **Sub-issue de:** Issue principal de la cual es sub-issue

**Formato:**
```markdown
## 🔗 Issues Relacionadas
- **Depende de:** #42, #43
- **Bloquea:** #50
- **Sub-issues:**
  - #79: Auditar referencias
  - #80: Migrar scripts
- **Relacionada con:** #38
```

### 8. Documentar Riesgos y Mitigaciones

**Siempre incluir:**
- Riesgos identificados con severidad
- Estrategias de mitigación
- Dependencias externas
- Accesos/credenciales necesarios

**Ejemplo:**
```markdown
## 🚧 Riesgos / Bloqueos
- **Riesgo Alto:** Algunos scripts pueden usar código legacy
- **Mitigación:** 
  - Buscar exhaustivamente todas las referencias
  - Crear sub-issues para migración gradual
  - Mantener código deprecated durante 1 sprint
- **Dependencias externas:** RapidAPI Idealista
- **Accesos/credenciales pendientes:** IDEALISTA_API_KEY
```

### 9. Incluir Comandos y Ejemplos Ejecutables

**Para bugs:**
- Comandos para reproducir el problema
- Output esperado vs actual

**Para features:**
- Comandos para probar la implementación
- Ejemplos de uso

**Ejemplo:**
```markdown
## 📝 Pasos para Reproducir
1. Ejecutar:
   ```bash
   python scripts/extract_data.py
   ```
2. Verificar output:
   ```bash
   grep -r "data_extraction" .
   ```
3. Resultado esperado: 0 resultados
4. Resultado actual: 5 archivos encontrados
```

### 10. Actualizar Issues Durante el Desarrollo

**Cuándo actualizar:**
- Cuando se descubren nuevos detalles
- Cuando cambian las dependencias
- Cuando se completan sub-issues
- Cuando se identifican nuevos riesgos

**Qué actualizar:**
- Añadir notas en comentarios
- Actualizar lista de sub-issues completadas
- Documentar decisiones tomadas
- Actualizar estimaciones si cambian significativamente

---

## 📊 Checklist para Crear una Issue

Antes de crear una issue, verificar:

- [ ] **Título:** Claro, específico, con tipo `[BUG]`, `[FEATURE]`, etc.
- [ ] **Objetivo:** Descripción clara del qué y por qué
- [ ] **Problema:** Estado actual y deseado bien descritos
- [ ] **Pasos:** Reproducibles o implementables paso a paso
- [ ] **Criterios de aceptación:** Específicos, medibles, verificables
- [ ] **Impacto:** KPI técnico y métrica de éxito definidos
- [ ] **Issues relacionadas:** Vinculadas correctamente
- [ ] **Riesgos:** Identificados con mitigaciones
- [ ] **Ejemplos de código:** Incluidos cuando aplica
- [ ] **Estimación:** Tiempo estimado incluido
- [ ] **Prioridad:** Claramente marcada
- [ ] **Labels:** Apropiados y múltiples si aplica
- [ ] **Enlaces:** Documentación y código relacionado

---

## 🎓 Ejemplos de Buenas Issues

### Ejemplo 1: Bug con Ejemplo de Código
Ver: [#65](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/65)

**Características destacadas:**
- Título claro con tipo
- Ejemplo de código problemático y solución
- Pasos específicos numerados
- Criterios de aceptación verificables
- Estimación realista (5 min)

### Ejemplo 2: Issue Grande con Sub-issues
Ver: [#62](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/62)

**Características destacadas:**
- Dividida en fases claras
- Sub-issues vinculadas
- Estimación desglosada
- Riesgos y mitigaciones documentados
- Enlaces a sub-issues

### Ejemplo 3: Feature con Dependencias Externas
Ver: [#76](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/76)

**Características destacadas:**
- Limitaciones claramente documentadas (límite de API)
- Sub-issues para pasos complejos
- Comandos ejecutables incluidos
- Validaciones específicas
- Notas de implementación detalladas

---

## 🔄 Workflow de Issues

### 1. Crear Issue
- Seguir template del proyecto
- Incluir toda la información relevante
- Asignar labels apropiados

### 2. Planificación
- Revisar en planning meeting
- Asignar a sprint si aplica
- Vincular con milestones

### 3. Desarrollo
- Actualizar issue con progreso
- Comentar decisiones importantes
- Marcar sub-issues completadas

### 4. Revisión
- Verificar criterios de aceptación
- Añadir comentarios de revisión
- Cerrar issue cuando completa

### 5. Cierre
- Verificar todos los criterios cumplidos
- Añadir comentario de cierre con resumen
- Cerrar issue con commit que la referencia

---

## 📝 Plantilla Rápida

```markdown
## 📌 Objetivo
[Qué se quiere lograr y por qué es importante]

## 🔍 Descripción del Problema
**Estado actual:**
[Qué ocurre ahora]

**Estado deseado:**
[Qué debería ocurrir]

**Archivos afectados:**
- `ruta/archivo.py:línea`

## 📝 Pasos para Reproducir / Implementar
1. Paso 1
2. Paso 2
3. ...

## ✅ Definición de Hecho (Definition of Done)
- [ ] Criterio específico y medible 1
- [ ] Criterio específico y medible 2
- [ ] Tests pasan
- [ ] Documentación actualizada

## 🎯 Impacto & KPI
- **KPI técnico:** [Métrica específica]
- **Objetivo:** [Meta cuantificable]
- **Fuente de datos:** [Si aplica]

## 🔗 Issues Relacionadas
- Depende de: #
- Bloquea: #
- Relacionada con: #

## 🚧 Riesgos / Bloqueos
- **Riesgo:** [Descripción]
- **Mitigación:** [Cómo abordarlo]

## 📚 Enlaces Relevantes
- [Documentación](link)
- [Código](link)

## 💡 Notas de Implementación
- **Estimación:** X horas
- **Prioridad:** 🔴/🟡/🟢/⚪
- **Sprint recomendado:** Sprint X
```

---

**Última actualización:** 2025-12-02  
**Mantenedor:** Equipo de desarrollo

