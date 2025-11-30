# Issues Listas para Crear en GitHub - Sprint 1

**Fecha:** 30 de Noviembre 2025  
**Estado:** Listas para copiar/pegar en GitHub

---

## 📋 Issue #24.1: [S1] Investigar ID del indicador de renta en API IDESCAT

**Labels:** `sprint-1`, `investigation`, `data-extraction`, `idescat`, `priority-high`  
**Milestone:** Sprint 1  
**Asignado a:** @tu_usuario  
**Estado inicial:** 🔄 In Progress

---

### 📌 Objetivo

Identificar el ID específico del indicador de renta disponible en la API de IDESCAT para poder extraer datos reales de renta histórica por barrio (2015-2023).

### 🔍 Descripción del Problema

El `IDESCATExtractor` está implementado y funcional con tests pasando, pero requiere identificar el ID específico del indicador de renta disponible en la API de IDESCAT para poder extraer datos reales.

**Contexto:**
- ✅ Extractor base implementado con 3 estrategias (API, web scraping, archivos públicos)
- ✅ Tests unitarios completos (12/12 pasando)
- ✅ Integración con manifest lista
- ⏳ **Falta:** ID del indicador específico de renta

### 📝 Pasos para Implementar

1. Explorar API de indicadores: `https://api.idescat.cat/indicadors/v1/nodes.json?lang=es`
2. Buscar indicadores relacionados con "renta", "renda", "income", "disponible"
3. Identificar estructura de respuesta de la API
4. Probar endpoint `dades.json` con el ID encontrado
5. Verificar cobertura temporal (2015-2023)
6. Verificar cobertura geográfica (barrios de Barcelona)
7. Documentar hallazgos en `docs/sources/idescat.md`
8. Actualizar `_try_api_indicators()` con el ID encontrado

### ✅ Definición de Hecho (Definition of Done)

- [ ] ID del indicador identificado y documentado
- [ ] Endpoint funcional probado con datos reales
- [ ] Documentación actualizada en `docs/sources/idescat.md`
- [ ] Código actualizado para usar el ID correcto
- [ ] Tests actualizados si es necesario
- [ ] Datos de prueba extraídos y guardados en `data/raw/idescat/`

### 🎯 Impacto & KPI

- **KPI afectado:** Años de renta disponibles (objetivo: 8+ años, 2015-2023)
- **Fuente de datos:** IDESCAT API
- **Bloquea:** Issue #25 (Pipeline renta histórica)

### 🔗 Issues Relacionadas

- **Depende de:** #24 (parcialmente completada)
- **Bloquea:** #25
- **Relacionada con:** #24.2, #24.3

### 🚧 Riesgos / Bloqueos

- **Dependencias externas:** API de IDESCAT puede no tener datos de renta por barrio
- **Accesos/credenciales:** Ninguno requerido (API pública)
- **Datos faltantes:** Si no hay datos en API, activar Issue #24.2 (estrategias alternativas)

### 📚 Enlaces Relevantes

- [Documentación API IDESCAT](https://www.idescat.cat/dev/api/v1/?lang=es)
- [Explorador de indicadores](https://api.idescat.cat/indicadors/v1/nodes.json?lang=es)
- [Extractor implementado](src/extraction/idescat.py)
- [Progreso Sprint 1](docs/SPRINT_1_PROGRESS.md)

### ⏱️ Tiempo Estimado

**2-4 horas**

---

## 📋 Issue #24.3: [S1] Documentar IDESCATExtractor

**Labels:** `sprint-1`, `documentation`, `idescat`, `priority-medium`  
**Milestone:** Sprint 1  
**Asignado a:** @tu_usuario  
**Estado inicial:** 📋 Backlog

---

### 📌 Objetivo

Crear documentación completa del extractor de IDESCAT siguiendo el formato de otras fuentes de datos del proyecto.

### 🔍 Descripción del Problema

El `IDESCATExtractor` está implementado pero falta documentación detallada que explique cómo funciona, qué endpoints usa, y cómo se integra con el resto del sistema.

### 📝 Pasos para Implementar

1. Crear `docs/sources/idescat.md`
2. Documentar endpoints y estructura de la API
3. Documentar estrategias de extracción (API, web scraping, archivos públicos)
4. Incluir ejemplos de uso
5. Documentar limitaciones y rate limits
6. Agregar diagramas de flujo si aplica
7. Referenciar en README principal

### ✅ Definición de Hecho (Definition of Done)

- [ ] Documentación completa en `docs/sources/idescat.md`
- [ ] Ejemplos de uso incluidos
- [ ] Referencias actualizadas en README
- [ ] Diagramas o ejemplos visuales si aplica
- [ ] Documentación revisada y sin errores

### 🎯 Impacto & KPI

- **KPI afectado:** Calidad de documentación del proyecto
- **Fuente de datos:** IDESCAT
- **Facilita:** Onboarding de nuevos desarrolladores

### 🔗 Issues Relacionadas

- **Depende de:** #24.1 (completada con datos reales)
- **Relacionada con:** #24

### 🚧 Riesgos / Bloqueos

- **Dependencias:** Requiere que Issue #24.1 esté completada para documentar datos reales
- **Accesos/credenciales:** Ninguno

### 📚 Enlaces Relevantes

- [Extractor implementado](src/extraction/idescat.py)
- [Progreso Sprint 1](docs/SPRINT_1_PROGRESS.md)
- [Otras fuentes documentadas](docs/sources/)

### ⏱️ Tiempo Estimado

**1-2 horas**

---

## 📋 Issue #24.2: [S1] Completar estrategias alternativas IDESCATExtractor

**Labels:** `sprint-1`, `feature`, `data-extraction`, `web-scraping`, `priority-medium`  
**Milestone:** Sprint 1  
**Asignado a:** @tu_usuario  
**Estado inicial:** 📋 Backlog (solo activar si API falla)

---

### 📌 Objetivo

Si la API de IDESCAT no proporciona datos de renta directamente, completar las estrategias alternativas (web scraping y archivos públicos) para obtener los datos necesarios.

### 🔍 Descripción del Problema

El `IDESCATExtractor` tiene 3 estrategias implementadas, pero las estrategias 2 y 3 (web scraping y archivos públicos) están solo como estructura base. Si la API no funciona, necesitamos estas alternativas.

### 📝 Pasos para Implementar

1. Investigar estructura del sitio web de IDESCAT para datos de renta
2. Implementar scraping específico en `_try_web_scraping()`
3. Identificar URLs de archivos CSV/Excel públicos
4. Implementar descarga y parsing en `_try_public_files()`
5. Probar con datos reales (2015-2023)
6. Validar mapeo de barrios
7. Actualizar tests con casos reales

### ✅ Definición de Hecho (Definition of Done)

- [ ] Al menos una estrategia alternativa funcional
- [ ] Datos extraídos y guardados en `data/raw/idescat/`
- [ ] Cobertura >=80% para 2015-2023
- [ ] Tests actualizados
- [ ] Documentación actualizada

### 🎯 Impacto & KPI

- **KPI afectado:** Años de renta disponibles (objetivo: 8+ años, 2015-2023)
- **Fuente de datos:** IDESCAT (web scraping o archivos públicos)
- **Plan B:** Solo si Issue #24.1 falla

### 🔗 Issues Relacionadas

- **Depende de:** #24.1 (solo activar si falla)
- **Relacionada con:** #24, #24.3

### 🚧 Riesgos / Bloqueos

- **Dependencias externas:** Sitio web puede cambiar estructura
- **Accesos/credenciales:** Ninguno requerido
- **Datos faltantes:** URLs de archivos públicos pueden no estar disponibles

### 📚 Enlaces Relevantes

- [Extractor implementado](src/extraction/idescat.py)
- [Progreso Sprint 1](docs/SPRINT_1_PROGRESS.md)
- [Sitio web IDESCAT](https://www.idescat.cat/dades/?lang=es)

### ⏱️ Tiempo Estimado

**1-2 días**

---

## 📋 Instrucciones para Crear en GitHub

1. Ve a tu repositorio en GitHub
2. Click en la pestaña **Issues**
3. Click en **New Issue**
4. Para cada issue:
   - Copia el título y descripción completa
   - Asigna los labels indicados
   - Asocia con el milestone "Sprint 1"
   - Asigna a ti mismo
   - Mueve al estado inicial indicado en el Project Board

### Orden de Creación Recomendado

1. **Issue #24.1** → Crear primero, mover a "In Progress"
2. **Issue #24.3** → Crear segundo, dejar en "Backlog"
3. **Issue #24.2** → Crear tercero, dejar en "Backlog" (solo activar si #24.1 falla)

### Project Board - Columnas Sugeridas

```
📋 Backlog → 🔄 In Progress → 👀 In Review → ✅ Done
```

**Ubicación inicial:**
- Issue #24.1 → 🔄 In Progress
- Issue #24.3 → 📋 Backlog
- Issue #24.2 → 📋 Backlog

---

**Nota:** No crear Issue #25 todavía - está bloqueada hasta completar #24.1

