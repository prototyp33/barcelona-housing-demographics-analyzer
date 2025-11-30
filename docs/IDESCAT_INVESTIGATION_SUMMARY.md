# Resumen de Investigación: IDESCAT API - Indicador de Renta

**Fecha:** 30 de Noviembre 2025  
**Issue:** #24.1  
**Estado:** 🔄 En progreso - Requiere investigación adicional

---

## ✅ Lo que hemos encontrado

### 1. Indicador Principal Identificado

**ID:** `m10409`  
**Nombre:** "Renta anual"  
**Descripción:** "Renta media neta por persona"  
**Unidad:** € (euros)  
**Fuente:** INE. Encuesta de condiciones de vida

### 2. Estructura de la API

- ✅ API accesible y funcional
- ✅ Endpoint: `https://api.idescat.cat/indicadors/v1/dades.json?i=m10409&lang=es`
- ✅ Respuesta en formato JSON válido
- ✅ Datos disponibles para 2024

### 3. Limitaciones Identificadas

- ⚠️ **Nivel de desagregación:** El indicador parece ser a nivel de Cataluña/municipio, no por barrio
- ⚠️ **Cobertura temporal:** Solo muestra el último año (2024), no serie histórica visible
- ⚠️ **Parámetros desconocidos:** No está claro cómo obtener datos por barrio o serie histórica

---

## 🔍 Próximos Pasos Recomendados

### Opción A: Investigar más la API (2-4 horas)

1. **Explorar documentación de parámetros:**
   - Revisar documentación completa de la API
   - Buscar ejemplos de desagregación por barrio
   - Probar diferentes combinaciones de parámetros

2. **Probar otros indicadores:**
   - m10410 (Índice de Gini) - puede tener más desagregación
   - m16768 (Ingresos y consumo de los hogares)
   - Buscar indicadores específicos de "barrios" o "secciones censales"

3. **Contactar con IDESCAT:**
   - Consultar si hay datos de renta por barrio disponibles
   - Preguntar por el formato correcto de parámetros

### Opción B: Activar Estrategias Alternativas (1-2 días)

Si la API no proporciona datos por barrio:

1. **Web Scraping:**
   - Investigar sitio web de IDESCAT
   - Buscar tablas de renta por barrio
   - Implementar scraping específico

2. **Archivos Públicos:**
   - Buscar CSV/Excel en portal de datos abiertos
   - Anuari Estadístic de Barcelona
   - Datos del Ayuntamiento de Barcelona

3. **Fuentes Alternativas:**
   - Portal de Dades de Barcelona (ya tenemos extractor)
   - Open Data BCN (ya tenemos extractor)
   - Verificar si tienen datos de renta

---

## 📊 Archivos Generados

- ✅ `scripts/search_idescat_renta.py` - Script para buscar indicadores
- ✅ `data/raw/idescat/indicadores_renta_encontrados.json` - 9 indicadores encontrados
- ✅ `docs/IDESCAT_RENTA_INVESTIGATION.md` - Documentación detallada
- ✅ `docs/GITHUB_ISSUES_S1_READY.md` - Issues listas para GitHub

---

## 🎯 Recomendación

**Siguiente acción inmediata:**

1. ✅ **Crear Issue #24.1 en GitHub** con los hallazgos actuales
2. 🔄 **Continuar investigación** (2-4 horas más):
   - Probar diferentes parámetros de la API
   - Explorar documentación completa
   - Probar otros indicadores
3. ⏱️ **Si no se encuentra solución en 4 horas:**
   - Activar Issue #24.2 (estrategias alternativas)
   - Considerar web scraping o archivos públicos

---

## 📝 Notas para la Issue #24.1

**Comentario a agregar en GitHub:**

```
✅ Indicador m10409 identificado ("Renta anual")
✅ API funcional y accesible
⚠️ Limitación: Parece ser a nivel municipal, no por barrio
🔍 Próximo paso: Investigar parámetros para desagregación por barrio
📊 Archivos: Ver docs/IDESCAT_RENTA_INVESTIGATION.md
```

---

**Última actualización:** 30 de Noviembre 2025 - 15:45

