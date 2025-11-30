# Investigación: Indicadores de Renta en IDESCAT API

**Fecha:** 30 de Noviembre 2025  
**Issue:** #24.1  
**Estado:** 🔄 En progreso

---

## 🎯 Objetivo

Identificar el ID del indicador de renta disponible en la API de IDESCAT para extraer datos de renta histórica por barrio (2015-2023).

---

## 📊 Resultados de la Búsqueda

### Indicadores Encontrados

Se encontraron **9 indicadores** relacionados con renta/ingresos:

| ID | Contenido | Descripción | Ruta |
|----|-----------|-------------|------|
| **m10409** | **Renta anual** | **Renta media neta por persona** | Condiciones de vida / Mercado de la vivienda |
| m10410 | Índice de Gini | Grado de desigualdad en la renta | Condiciones de vida / Mercado de la vivienda |
| m16768 | Ingresos y consumo de los hogares | (Sin descripción) | Ingresos y consumo de los hogares |
| m10372 | Enseñanza privada no universitaria | Ingresos | Educación |
| m10971 | Renta garantizada de ciudadanía | Número medio de prestaciones | Protección social |
| m10418 | Edificios destinados a vivienda familiar | Número de edificios | Parque de viviendas |
| m10540 | Suministro agua | Agua disponible potabilizada | Medio ambiente |

### ⭐ Indicador Principal: m10409

**"Renta anual" - "Renta media neta por persona"**

- **ID:** `m10409`
- **Descripción:** Renta media neta por persona
- **Rutas:**
  - Condiciones de vida > Renta anual
  - Mercado de la vivienda > Renta anual
- **Fecha última actualización:** 2025-02-13

**Este es el indicador más prometedor** ya que:
- ✅ Se relaciona directamente con renta
- ✅ Aparece en "Mercado de la vivienda" (relevante para nuestro proyecto)
- ✅ Es "renta media neta por persona" (métrica útil)

---

## 🔍 Pruebas del Indicador m10409

### Endpoint de Datos

```
https://api.idescat.cat/indicadors/v1/dades.json?i=m10409&lang=es
```

### Resultados de Pruebas

**1. Indicador sin parámetro geo:**
- ✅ Indicador existe y tiene datos
- ✅ Descripción: "Renta media neta por persona"
- ✅ Unidad: € (euros)
- ✅ Fuente: "INE. Encuesta de condiciones de vida"
- ⚠️ Nivel: "Indicadores básicos de Cataluña" (nivel agregado)
- ⚠️ Año disponible: 2024 (último año)

**2. Indicador con geo=080193 (Barcelona):**
- ✅ Misma estructura de respuesta
- ⚠️ Parece ser a nivel municipal, no por barrio
- ⚠️ No se observa desagregación por barrios en la respuesta

### Estructura de Respuesta

```json
{
  "indicadors": {
    "i": {
      "id": "m10409",
      "c": "Renta anual",
      "d": "Renta media neta por persona",
      "v": "16546",  // Valor actual (€)
      "ts": "14170,14159,14692,15830,16546",  // Serie temporal
      "r": {"title": "2024", "content": "2024"},
      "t": {"i": "b", "content": "Indicadores básicos de Cataluña"}
    }
  }
}
```

### ⚠️ Limitaciones Identificadas

1. **Nivel de desagregación:** El indicador m10409 parece ser a nivel de Cataluña o municipio, no por barrio
2. **Cobertura temporal:** Solo muestra 2024, no hay serie histórica 2015-2023 visible directamente
3. **Necesidad de investigación adicional:** Puede requerir:
   - Parámetros adicionales para desagregar por barrio
   - Otro indicador específico para barrios
   - Estrategias alternativas (web scraping, archivos públicos)

---

## 📝 Próximos Pasos

1. **Probar endpoint con datos de Barcelona:**
   ```bash
   curl "https://api.idescat.cat/indicadors/v1/dades.json?i=m10409&geo=080193&lang=es"
   ```

2. **Verificar cobertura temporal:**
   - ¿Qué años están disponibles?
   - ¿Cubre 2015-2023?

3. **Verificar cobertura geográfica:**
   - ¿Hay datos por barrio?
   - ¿Qué nivel de desagregación tiene?

4. **Probar otros indicadores si m10409 no funciona:**
   - m10410 (Índice de Gini)
   - m16768 (Ingresos y consumo de los hogares)

5. **Actualizar extractor:**
   - Si m10409 funciona, actualizar `_try_api_indicators()`
   - Probar extracción real
   - Validar datos

---

## 🔍 Resultados de Pruebas de Parámetros

Se probaron **8 combinaciones diferentes** de parámetros de la API:

| Parámetros | Resultado |
|------------|-----------|
| Sin parámetros | ✅ Datos a nivel de Cataluña |
| `geo=080193` (Barcelona) | ✅ Mismos datos (no desagrega) |
| `t=b` (tipo barrio) | ✅ Mismos datos (no desagrega) |
| `geo=080193&t=b` | ✅ Mismos datos (no desagrega) |
| `p=geo/080193` | ✅ Mismos datos (no desagrega) |
| `p=geo/080193;t/b` | ⚠️ Devuelve otro indicador |
| `max=100` | ✅ Mismos datos (no desagrega) |
| `geo=080193&max=100` | ✅ Mismos datos (no desagrega) |

### ⚠️ Conclusión de Pruebas

**La API de IDESCAT NO proporciona datos de renta desagregados por barrio.**

- Todos los tests devuelven datos a nivel de **"Indicadores básicos de Cataluña"**
- El parámetro `geo` no parece afectar la desagregación
- El indicador m10409 solo tiene datos agregados a nivel autonómico/municipal

---

## 💡 Alternativa Identificada: Open Data BCN

**¡Buenas noticias!** Ya existe una fuente alternativa que SÍ tiene datos de renta por barrio:

### Datasets de Open Data BCN (Ya implementados)

1. **`renda-disponible-llars-bcn`**
   - "Renda disponible de les llars per càpita(€)"
   - ✅ Tiene `Codi_Barri`, `Nom_Barri`, `Seccio_Censal`
   - ✅ Se puede agregar por barrio

2. **`atles-renda-bruta-per-llar`**
   - "Renda tributària bruta mitjana per llar (€)"
   - ✅ Tiene `Codi_Barri`, `Nom_Barri`

3. **`atles-renda-bruta-per-persona`**
   - "Renda tributària bruta mitjana per persona (€)"
   - ✅ Tiene `Codi_Barri`, `Nom_Barri`

### Extractor Existente

Ya existe un `RentaExtractor` en `scripts/extract_priority_sources.py` que:
- ✅ Extrae datos de Open Data BCN
- ✅ Tiene datasets conocidos y confirmados
- ✅ Puede agregar datos por barrio

---

## 🎯 Recomendación Final

**Opción A (Recomendada):** Usar Open Data BCN como fuente principal
- Ya tenemos extractor implementado
- Datos confirmados por barrio
- Mejor cobertura geográfica

**Opción B:** Mantener IDESCAT como fuente secundaria
- Solo para datos agregados a nivel municipal/autonómico
- Útil para validación o comparación

**Opción C:** Combinar ambas fuentes
- Open Data BCN para datos por barrio
- IDESCAT para contexto regional

---

## 📚 Referencias

- [API IDESCAT v1](https://www.idescat.cat/dev/api/v1/?lang=es)
- [Documentación de indicadores](https://www.idescat.cat/dev/api/indicadors/?lang=es)
- [Extractor implementado](src/extraction/idescat.py)
- [Script de búsqueda](scripts/search_idescat_renta.py)

---

## 📊 Archivos Generados

- `data/raw/idescat/indicadores_renta_encontrados.json` - Lista completa de indicadores encontrados
- `scripts/search_idescat_renta.py` - Script para buscar indicadores

---

**Última actualización:** 30 de Noviembre 2025

