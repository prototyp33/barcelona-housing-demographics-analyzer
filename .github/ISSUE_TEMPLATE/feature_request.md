---
name: Feature Request
about: Proponer nueva funcionalidad para el proyecto
title: '[FEAT] '
labels: ['type:feature', 'status:needs-triage']
assignees: ''
---

## 📋 Descripción de la Feature

<!-- Describe la funcionalidad en 2-3 frases claras. -->
<!-- Ejemplo bueno: "Dashboard interactivo que permita comparar asequibilidad entre barrios usando un mapa de calor" -->
<!-- Ejemplo malo: "Hacer algo con precios" -->

Resumen de la feature:

<!-- Tu descripción aquí -->

---

## 🎯 Objetivo y Valor

### ¿Qué problema resuelve?

<!-- Explica el problema actual o necesidad que motiva esta feature. -->
<!-- Ejemplo: "Actualmente no existe una forma unificada de ver precios, renta y demografía por barrio en un solo dashboard" -->


### ¿Qué valor aporta al proyecto?

<!-- Para usuarios: ¿cómo mejora su experiencia? -->
<!-- Para análisis: ¿qué insights nuevos permite? -->
<!-- Para datos: ¿qué información nueva integra? -->

Para usuarios:

<!-- Ej: "Permite a cualquiera comparar barrios de Barcelona sin saber SQL ni Python" -->

Para análisis:

<!-- Ej: "Permite analizar correlaciones entre renta, precios y densidad por barrio" -->

Para datos:

<!-- Ej: "Integra una nueva fuente de datos de alquiler histórico por distrito" -->

---

## 📊 Datos y Fuentes Necesarias

<!-- Marca las que apliquen editando los checkboxes. -->

- [ ] Requiere nueva fuente de datos (especificar cuál)
- [ ] Usa datos existentes en `data/processed/database.db`
- [ ] Requiere nueva tabla en SQLite
- [ ] Requiere enriquecer tabla existente

Fuentes identificadas:

<!-- Ej: IDESCAT API, Open Data BCN dataset xyz, web scraping de Idealista (solo metadata, no contenido protegido) -->

Granularidad requerida:

<!-- Nivel: barrio / distrito / municipio -->
<!-- Frecuencia: anual / trimestral / mensual / tiempo real -->

Consideraciones de calidad de datos:

<!-- ¿Hay gaps, valores nulos, problemas de mapeo de barrios, etc.? -->

---

## 🏗️ Área Técnica Afectada

<!-- Marca todas las que apliquen. -->

- [ ] area:data - Extracción de datos (nuevo scraper/API)
- [ ] area:backend - Pipeline ETL (procesamiento, database)
- [ ] area:frontend - Dashboard Streamlit (UI, visualizaciones)
- [ ] area:docs - Documentación
- [ ] area:infra - CI/CD, deployment

Módulos/archivos potencialmente afectados:

<!-- Ej: src/extraction/idescat.py, src/etl/pipeline.py, src/app/pages/market_cockpit.py -->

---

## ✅ Criterios de Aceptación

<!-- Define qué debe cumplir la feature para considerarse completa. Sé específico y medible. -->

**Funcionalidad:**

- [ ] [Descripción del comportamiento esperado]
<!-- Ej: "El usuario puede seleccionar 3 barrios y ver su evolución de precios 2015-2025 en un gráfico" -->

**Datos:**

- [ ] [Qué datos debe mostrar/procesar]
<!-- Ej: "Debe usar fact_precios y fact_demografia filtrando por codi_barri" -->

**UI/UX (si aplica):**

- [ ] [Cómo se ve/interactúa]
<!-- Ej: "Mapa de Barcelona con tooltip mostrando precio medio, renta y densidad" -->

**Tests:**

- [ ] [Qué casos de prueba debe pasar]
<!-- Ej: "Tests unitarios para cálculos + test de integración del endpoint/ETL" -->

**Documentación:**

- [ ] [Qué debe documentarse]
<!-- Ej: "Actualizar docs/features/feature-XX.md y README si aplica" -->

**Performance (si aplica):**

- [ ] [Restricciones de rendimiento]
<!-- Ej: "Tiempo de respuesta < 2s para consultas a 73 barrios" -->

Ejemplo de uso:

<!-- Describe un caso de uso real. -->
<!-- Ejemplo: "Como analista, quiero poder filtrar barrios por rentabilidad y ver un ranking top 10" -->

---

## 💡 Propuesta Técnica (Opcional)

<!-- Si tienes ideas de cómo implementarlo, compártelas aquí. No es obligatorio. -->

Módulos/archivos afectados (propuesto):

<!-- Ej: src/analytics/affordability.py, src/app/pages/affordability_dashboard.py -->

Librerías/herramientas sugeridas:

<!-- Ej: plotly para gráficos interactivos, pandas para procesamiento, geopandas para mapas -->

Notas técnicas:

<!-- Cualquier detalle técnico relevante (constraints de la API, límites de SQLite, etc.). -->

---

## 🔗 Issues Relacionadas

<!-- Menciona issues que dependen de esta o de las que esta depende. Usa formato #numero para auto-link. -->

Depende de:

<!-- Ej: #24 (necesita datos de renta histórica) -->

Bloquea a:

<!-- Ej: #30 (dashboard vulnerabilidad necesita esta métrica) -->

Relacionada con:

<!-- Ej: #26 (misma área: asequibilidad) -->

---

## 📝 Notas Adicionales

<!-- Cualquier información extra: mockups, referencias, enlaces. -->

Referencias:

<!-- Links a diseños, papers, ejemplos similares, documentación externa. -->

Mockups/Wireframes:

<!-- Adjunta imágenes o links a Figma/Excalidraw/Draw.io. -->

Deadline (si aplica):

<!-- Si tiene fecha límite, menciónala en formato YYYY-MM-DD. -->

---

## 📚 Recursos Útiles

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guía de contribución  
- [Project Board](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/projects) - Ver roadmap  
- [Database Schema](../../docs/DATABASE_SCHEMA.md) - Estructura de datos actual  
- [Project Docs](../../project-docs/index.md) - Documentación general del proyecto  

<!-- ¿Primera vez contribuyendo? Lee nuestra guía de setup en README.md. -->
