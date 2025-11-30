# Investigación Final: IDESCAT API vs Open Data BCN para Renta por Barrio

**Fecha:** 30 de Noviembre 2025  
**Issue:** #32  
**Estado:** ✅ Completada

---

## 📊 Resumen Ejecutivo

### Conclusión Principal

**La API de IDESCAT NO proporciona datos de renta desagregados por barrio.**  
**Open Data BCN SÍ tiene datos de renta por barrio y ya está implementado.**

---

## 🔍 Investigación de IDESCAT API

### Indicador Identificado

- **ID:** `m10409`
- **Nombre:** "Renta anual"
- **Descripción:** "Renta media neta por persona"
- **Unidad:** € (euros)
- **Fuente:** INE. Encuesta de condiciones de vida

### Pruebas Realizadas

Se probaron **8 combinaciones diferentes** de parámetros:

1. ✅ Sin parámetros → Datos a nivel de Cataluña
2. ✅ `geo=080193` (Barcelona) → Mismos datos (no desagrega)
3. ✅ `t=b` (tipo barrio) → Mismos datos (no desagrega)
4. ✅ `geo=080193&t=b` → Mismos datos (no desagrega)
5. ✅ `p=geo/080193` → Mismos datos (no desagrega)
6. ⚠️ `p=geo/080193;t/b` → Devuelve otro indicador
7. ✅ `max=100` → Mismos datos (no desagrega)
8. ✅ `geo=080193&max=100` → Mismos datos (no desagrega)

### Resultado

**Todos los tests devuelven datos a nivel de "Indicadores básicos de Cataluña"**  
**No hay desagregación por barrio disponible en la API.**

---

## ✅ Alternativa: Open Data BCN

### Datasets Disponibles

Ya existen **3 datasets confirmados** en Open Data BCN con datos de renta por barrio:

1. **`renda-disponible-llars-bcn`**
   - Título: "Renda disponible de les llars per càpita(€)"
   - Columnas: `Codi_Barri`, `Nom_Barri`, `Seccio_Censal`, `Import_Euros`
   - ✅ Datos por sección censal que se pueden agregar por barrio

2. **`atles-renda-bruta-per-llar`**
   - Título: "Renda tributària bruta mitjana per llar (€)"
   - Columnas: `Codi_Barri`, `Nom_Barri`, `Seccio_Censal`, `Import_Renda_Bruta_€`
   - ✅ Datos por sección censal que se pueden agregar por barrio

3. **`atles-renda-bruta-per-persona`**
   - Título: "Renda tributària bruta mitjana per persona (€)"
   - Columnas: `Codi_Barri`, `Nom_Barri`, `Seccio_Censal`
   - ✅ Datos por sección censal que se pueden agregar por barrio

### Extractor Existente

**Ya existe un `RentaExtractor` implementado** en:
- `scripts/extract_priority_sources.py` (líneas 749-847+)
- Usa `OpenDataBCNExtractor` como base
- Tiene IDs de datasets conocidos y confirmados
- Puede agregar datos por barrio usando `groupby` en `Codi_Barri`

---

## 🎯 Recomendación Estratégica

### Opción Recomendada: Usar Open Data BCN

**Ventajas:**
- ✅ Datos confirmados por barrio
- ✅ Extractor ya implementado
- ✅ Múltiples datasets disponibles
- ✅ Datos por sección censal (más granular)
- ✅ Se puede agregar fácilmente por barrio

**Acción:**
1. Usar `RentaExtractor` existente o integrarlo en `IDESCATExtractor`
2. Actualizar `IDESCATExtractor._try_public_files()` para usar Open Data BCN
3. O mejor: usar directamente `OpenDataBCNExtractor` con los datasets de renta

### Opción Secundaria: Mantener IDESCAT

**Uso:**
- Solo para datos agregados a nivel municipal/autonómico
- Validación o comparación con datos regionales
- Contexto adicional (no como fuente principal)

---

## 📝 Próximos Pasos

### Para Issue #32

1. ✅ **Completado:** Investigación de API IDESCAT
2. ✅ **Completado:** Identificación de alternativa (Open Data BCN)
3. ⏳ **Pendiente:** Actualizar `IDESCATExtractor` para usar Open Data BCN
4. ⏳ **Pendiente:** Probar extracción real con datos de Open Data BCN
5. ⏳ **Pendiente:** Validar cobertura temporal (2015-2023)

### Para Issue #34 (Estrategias Alternativas)

**Ya no es necesario activar** - Open Data BCN es la solución, no una alternativa.

---

## 📊 Archivos Generados

- ✅ `scripts/search_idescat_renta.py` - Búsqueda de indicadores
- ✅ `scripts/test_idescat_api_params.py` - Pruebas de parámetros
- ✅ `data/raw/idescat/indicadores_renta_encontrados.json` - 9 indicadores
- ✅ `data/raw/idescat/api_params_test_results.json` - Resultados de pruebas
- ✅ `docs/IDESCAT_RENTA_INVESTIGATION.md` - Documentación detallada
- ✅ `docs/IDESCAT_INVESTIGATION_SUMMARY.md` - Resumen inicial
- ✅ `docs/IDESCAT_INVESTIGATION_FINAL.md` - Este documento

---

## 🔗 Referencias

- [API IDESCAT v1](https://www.idescat.cat/dev/api/v1/?lang=es)
- [Open Data BCN - Renta](https://opendata-ajuntament.barcelona.cat/data/es/dataset)
- [RentaExtractor existente](scripts/extract_priority_sources.py)
- [OpenDataBCNExtractor](src/extraction/opendata.py)

---

**Conclusión:** ✅ **Investigación completada** - Open Data BCN es la fuente correcta para datos de renta por barrio.

**Última actualización:** 30 de Noviembre 2025

