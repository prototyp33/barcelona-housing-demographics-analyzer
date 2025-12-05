---
name: Bug Report
about: Reportar error o comportamiento inesperado
title: '[BUG] '
labels: ['type:bug', 'priority:high', 'status:needs-triage']
assignees: ''
---

## 🐛 Descripción del Bug

<!-- Describe en 1-2 frases qué está fallando. Sé específico. -->
<!-- Ejemplo bueno: "Error al mapear barrio 'el Raval' en IDESCATExtractor (KeyError en mapeo de codi_barri)" -->
<!-- Ejemplo malo: "No funciona el extractor" -->

Resumen:

<!-- Tu descripción aquí -->

---

## 🚨 Severidad

<!-- Ayúdanos a priorizar marcando UNA opción (deja solo la que aplica en [x]). -->

- [ ] Crítica - Sistema completamente roto, no se puede usar
- [ ] Alta - Funcionalidad principal afectada, workaround difícil
- [ ] Media - Funcionalidad secundaria afectada, workaround posible
- [ ] Baja - Problema cosmético o edge case

Impacto:

<!-- ¿A cuántos usuarios/casos afecta? ¿Bloquea algo crítico (ETL diario, dashboard principal, etc.)? -->

---

## 🏗️ Área Afectada

<!-- Marca todas las que apliquen. -->

- [ ] area:data - Extracción de datos (scrapers, APIs, extractors)
- [ ] area:backend - Pipeline ETL (processing, database, queries)
- [ ] area:frontend - Dashboard (Streamlit, visualizaciones)
- [ ] area:docs - Documentación
- [ ] area:infra - CI/CD, tests, deployment

Módulo/archivo específico:

<!-- Ej: src/extraction/idescat_extractor.py, src/etl/pipeline.py, src/app/pages/market_cockpit.py -->

---

## 📋 Pasos para Reproducir

<!-- Describe paso a paso cómo reproducir el error. Incluye comandos exactos, inputs y acciones en UI. -->

Setup inicial:

<!-- Ej: "database.db generado con scripts/process_and_load.py el 2025-12-01", "navegador Chrome" -->

Ejecutar:

```bash
# Ejemplo
python scripts/extract_data.py --source idescat
```

Observar:

<!-- Qué pasa cuando ejecutas el paso anterior (mensaje de error, gráfico vacío, etc.). -->

Error aparece en:

<!-- Ej: línea X del log, pantalla Y del dashboard, traza de error en consola, etc. -->

Frecuencia:

<!-- Siempre / A veces / Solo en condiciones específicas (describe cuáles). -->

---

## ✅ Comportamiento Esperado

<!-- ¿Qué debería pasar? -->
<!-- Ej: "El barrio 'el Raval' debe mapearse a barrio_id=39 y aparecer en fact_demografia sin errores de FK" -->


## ❌ Comportamiento Actual

<!-- ¿Qué pasa realmente? -->
<!-- Ej: "Lanza KeyError: 'el Raval' no encontrado en mapeo" o "El gráfico de precios aparece vacío" -->

---

## 🖼️ Logs, Screenshots y Error Messages

<!-- Adjunta evidencia del error: stack trace completo, logs relevantes y/o capturas de pantalla. -->

Stack trace / Error completo:

```text
# Pega aquí el error completo.
# Incluye al menos ~10 líneas antes del error para contexto.
```

Screenshots (si aplica):

<!-- Arrastra imágenes aquí. Útil para errores de UI/dashboard (Streamlit). -->

Logs relevantes:

```text
# Pega aquí líneas relevantes de data/logs/*.log
# Ej: grep -i "ERROR" data/logs/data_extraction_20251201.log | head -20
```

---

## 🌍 Contexto Técnico

<!-- Completa toda la información que puedas sobre tu entorno. -->

Sistema Operativo:

- [ ] macOS (versión: ____________)
- [ ] Ubuntu/Linux (versión: ____________)
- [ ] Windows (versión: ____________)

Python:

```bash
python --version
# Resultado:
```

Dependencias clave:

```bash
pip list | grep -E "(pandas|streamlit|scrapy|playwright|sqlalchemy)"
# Resultado:
```

Branch/Commit:

<!-- Ej: main, feature/investment-calculator, commit abc123 -->

Database:

```bash
sqlite3 data/processed/database.db ".schema" | head -20
# ¿Qué tablas existen? ¿Se ve algo inusual?
```

Estado del entorno:

- [ ] Entorno virtual activado
- [ ] `data/processed/database.db` existe y tiene datos
- [ ] Ejecutado desde raíz del proyecto
- [ ] `.env` configurado (si aplica)

---

## 🔧 Intentos de Solución

<!-- ¿Qué has probado para resolver el error? Ayuda a evitar sugerir lo mismo. -->

- [ ] Reiniciar script/dashboard
- [ ] Limpiar database y re-ejecutar ETL
- [ ] Actualizar dependencias (`pip install -r requirements.txt`)
- [ ] Revisar logs en `data/logs/`
- [ ] Buscar errores similares en issues cerradas
- [ ] Otro: _______________________

Resultado de intentos:

<!-- ¿Alguno funcionó parcialmente? ¿Qué cambió? -->

---

## 🔗 Issues Relacionadas

<!-- ¿Hay issues relacionadas o duplicadas? -->

Posible duplicado de: #___

Relacionado con: #___

Aparece también en: #___

---

## 🚑 Ayuda Rápida

Bugs críticos: menciona a @prototyp33 en comentarios para atención prioritaria.

Recursos útiles:

- Logs de ejecución: `data/logs/`
- Esquema de base de datos: `docs/DATABASE_SCHEMA.md`
- Troubleshooting ETL: `docs/DEBUGGING_DATASETS.md`

<!-- ¿Encontraste la solución? Añade un comentario explicando el fix para ayudar a futuros contribuidores. -->
