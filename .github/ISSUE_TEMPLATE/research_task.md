---
name: Research Task
about: Investigación técnica o exploración de datos
title: '[RESEARCH] '
labels: ['type:research', 'status:needs-triage']
assignees: ''
---

## 🔍 Objetivo de la Investigación

<!-- Describe en 1-2 frases QUÉ necesitas investigar y POR QUÉ. -->
<!-- Ejemplo: "Investigar API de IDESCAT para determinar si podemos obtener renta histórica 2015-2023 por barrio" -->

Contexto:

<!-- ¿Por qué es necesaria esta investigación? ¿Qué decisión depende de ella (GO/NO-GO de una feature, elegir fuente de datos, etc.)? -->

Alcance:

<!-- ¿Qué está dentro y fuera del scope? Sé explícito para evitar rabbit holes. -->

---

## ❓ Preguntas a Responder

<!-- Lista las preguntas específicas que esta investigación debe resolver. Deben ser respondibles con Sí/No o datos concretos. -->

Pregunta principal:

<!-- Ej: ¿La API de IDESCAT ofrece datos de renta por barrio? -->

Preguntas secundarias:

- [ ] ¿Qué granularidad temporal tiene? (anual/mensual/trimestral)
- [ ] ¿Qué cobertura histórica ofrece? (años disponibles)
- [ ] ¿Requiere autenticación/API key?
- [ ] ¿Tiene rate limits? ¿Cuáles?
- [ ] ¿Formato de respuesta? (JSON/XML/CSV)

Preguntas técnicas adicionales:

<!-- Complejidad de integración, dependencias nuevas, licencias, limitaciones de uso, etc. -->

---

## 📚 Fuentes a Investigar

<!-- Lista todos los recursos que revisarás. Cuanto más concreto, mejor. -->

**APIs y Servicios**

- URL de API/servicio: __________________________
- Documentación oficial: ________________________
- Endpoints relevantes: _________________________

**Datasets y Portales de Datos**

- Portal de datos: _____________________________
- IDs de datasets: _____________________________
- Formato de archivos (CSV/JSON/Parquet): ______

**Documentación Técnica**

- Papers/artículos: ____________________________
- Ejemplos de código: __________________________
- Repositorios similares: ______________________

**Contactos (si aplica)**

- ¿Hay expertos/mantenedores a consultar?: _____

---

## 🧪 Metodología de Investigación

<!-- Describe CÓMO investigarás (pasos a seguir). -->

Exploración inicial:

<!-- Ej: Revisar documentación oficial, buscar ejemplos en GitHub, leer issues de otros proyectos. -->

Pruebas técnicas:

<!-- Ej: Ejecutar endpoints de prueba, descargar datasets de muestra, probar scraping controlado. -->

```bash
# Comando ejemplo
curl -X GET "https://api.example.com/v1/data" | jq
```

Análisis de viabilidad:

<!-- Ej: Evaluar complejidad de integración, estimar tiempo de implementación, riesgos técnicos. -->

Documentación de hallazgos:

<!-- Ej: Crear notebook exploratorio, escribir informe en Markdown en docs/research/. -->

---

## ✅ Criterios de Éxito

<!-- Define qué significa que la investigación está completa. -->

La investigación está completa cuando:

- [ ] Todas las preguntas clave tienen respuesta (Sí/No/Depende con justificación)
- [ ] Hay evidencia documentada (screenshots, logs, código de prueba, enlaces)
- [ ] Se ha tomado una decisión clara (continuar / descartar / buscar alternativa)
- [ ] El entregable final está publicado (ver sección siguiente)

Decisión esperada:

<!-- Ej: "GO: Implementar extractor IDESCAT" o "NO-GO: Buscar fuente alternativa en Open Data BCN" -->

---

## ⏱️ Time-Box

<!-- Límite de tiempo para evitar sobre-investigación. -->

Tiempo máximo asignado: _____ horas  
<!-- Recomendado: 2-8 horas para research tasks. -->

Deadline: YYYY-MM-DD  
<!-- Fecha límite para completar la investigación. -->

Si se excede el time-box:

- [ ] Reportar hallazgos parciales en esta issue
- [ ] Solicitar extensión con justificación
- [ ] Tomar decisión con la información disponible hasta el momento

---

## 📊 Entregable Esperado

<!-- Marca el tipo de output que generarás. -->

- [ ] Documento Markdown (`docs/research/YYYYMMDD-topic.md`)
- [ ] Notebook Jupyter (`notebooks/research/topic_exploration.ipynb`)
- [ ] Informe de Decisión (comentario en esta issue con template)
- [ ] Código de Prueba (`scripts/research/test_api.py`)
- [ ] Dataset de Muestra (`data/raw/research/sample.csv`)
- [ ] Otro: __________________________

### Template de Informe de Decisión

```markdown
## 🎯 Hallazgos Principales

- Hallazgo 1
- Hallazgo 2
- Hallazgo 3


## ✅ Respuestas a Preguntas Clave

1. Pregunta 1: Respuesta + evidencia
2. Pregunta 2: Respuesta + evidencia


## 🚦 Decisión: GO / NO-GO / ALTERNATIVA

**Recomendación**: [Tu recomendación aquí]

**Justificación**: [Por qué]

**Próximos pasos**: [Si GO, qué issue crear; si NO-GO, qué alternativa]


## 📎 Evidencia

- Links, screenshots, código de prueba
```

---

## 🔗 Issues Relacionadas

<!-- ¿Qué issues dependen de esta investigación? -->

Bloquea a:

<!-- Ej: #25 (pipeline renta histórica necesita saber si API funciona) -->

Parte de:

<!-- Ej: Milestone "v0.2: Data Expansion" -->

Relacionada con:

<!-- Otras research tasks similares -->

---

## 📝 Notas y Referencias

<!-- Cualquier información extra que ayude a entender el contexto. -->

Referencias útiles:

- Link 1: Documentación oficial
- Link 2: Ejemplo similar en otro proyecto
- Link 3: Discussion relevante

Restricciones conocidas:

<!-- Ej: "No podemos pagar por API keys", "Debe funcionar sin autenticación" -->

Riesgos identificados:

<!-- Ej: "API puede estar deprecated", "Datos podrían no tener calidad suficiente" -->

---

## 💡 Ejemplos de Research Tasks Pasadas

Ejemplo 1: Investigar API de IDESCAT  
Objetivo: Determinar viabilidad de extracción de renta histórica  
Resultado: GO - API funciona, datos disponibles 2015-2022  
Entregable: `docs/research/20251201-idescat-api.md`  
Tiempo: 4 horas

Ejemplo 2: Evaluar servicios de deployment  
Objetivo: Comparar Streamlit Cloud vs Heroku vs Railway  
Resultado: Decisión: Streamlit Cloud (free tier + fácil setup)  
Entregable: Notebook comparativo + tabla de decisión  
Tiempo: 3 horas

---

📚 Recursos Útiles

- [Project Docs](../../project-docs/index.md) - Contexto del proyecto  
- [Data Sources](../../docs/sources/idescat.md) - Fuentes conocidas (ejemplo)  
- [Tech Stack](../../docs/architecture/tech_stack.md) - Tecnologías actuales  

<!-- Research tasks NO producen código directamente en producción. Si de la investigación sale código estable, crea una Feature Request separada. -->
