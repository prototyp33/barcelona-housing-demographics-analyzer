# Validación de Cambios Extremos en Datos

**Fecha**: 2026-01-10  
**Objetivo**: Determinar si los cambios >100% son errores de datos o cambios reales del mercado

---

## Resumen Ejecutivo

Se investigaron **4 cambios extremos** (>100%) en precios de venta. Los hallazgos indican que la mayoría son **cambios reales del mercado**, pero **Baró de Viver (2015)** muestra señales de posible error de datos.

---

## Casos Investigados

### 1. 🔴 Baró de Viver (2015) - +239.8% - **POSIBLE ERROR**

**Datos fuente**:
- **2014**: 3 registros, todos con 438.5 €/m² (sin variación)
- **2015**: 5 registros con valores muy diferentes:
  - 3 registros: ~634-665 €/m² (similar a 2014)
  - 2 registros: 2,758 €/m² (6x más alto)
- **2016**: 5 registros con valores mixtos:
  - 3 registros: ~661 €/m²
  - 2 registros: 3,112 €/m²

**Análisis**:
- ✅ **Alta variabilidad en 2015**: CV = 77.7% (coeficiente de variación)
- ✅ **Dos grupos distintos de valores**: Parece haber dos tipos de propiedades mezclados
- ✅ **Mismo dataset_id para valores altos**: `u25rr7oxh6` y `cq4causxvu` tienen valores >2000€/m²
- ✅ **Mismo dataset_id para valores bajos**: `mrslyp5pcq`, `bxtvnxvukh`, `idjhkx1ruj` tienen valores ~600€/m²

**Conclusión**: 
🔴 **PROBABLE ERROR DE DATOS**
- Los valores de 2,758 €/m² en 2015 parecen ser outliers o datos de otro tipo de propiedad
- La alta variabilidad (CV=77.7%) sugiere datos inconsistentes
- El promedio de 1,490 €/m² está sesgado por los valores extremos

**Recomendación**:
- Usar mediana en lugar de promedio para este barrio en 2015
- O filtrar valores >2000€/m² como outliers
- Investigar si los dataset_ids `u25rr7oxh6` y `cq4causxvu` tienen datos correctos

---

### 2. 🟡 la Marina del Prat Vermell (2015) - +135.0% - **CAMBIO REAL POSIBLE**

**Datos fuente**:
- **2014**: 6 registros, promedio 611 €/m² (rango: 557-684)
- **2015**: 4 registros, todos con 1,436 €/m² (sin variación)
- **2016**: 6 registros, promedio 1,106 €/m² (rango: 1,089-1,152)

**Análisis**:
- ✅ Baja variabilidad en todos los años
- ✅ Cambio consistente entre años
- ✅ Valores en 2016 confirman nivel más alto que 2014

**Conclusión**: 
🟡 **CAMBIO REAL POSIBLE**
- El cambio parece ser real, pero requiere validación con datos externos
- Podría ser desarrollo inmobiliario nuevo o cambio en metodología de recolección

**Recomendación**:
- Validar con datos del Ayuntamiento de Barcelona
- Verificar si hubo desarrollo inmobiliario importante en 2015

---

### 3. 🟡 Vallvidrera (2016) - +117.6% - **CAMBIO REAL POSIBLE**

**Datos fuente**:
- **2015**: 3 registros, promedio 1,731 €/m²
- **2016**: 5 registros, promedio 3,767 €/m² (alta variabilidad: CV=13.3%)
- **2017**: 5 registros, promedio 2,507 €/m² (baja a nivel intermedio)

**Análisis**:
- ✅ Barrio de lujo (Vallvidrera es zona alta)
- ✅ Valores en 2017 confirman nivel más alto que 2015
- ⚠️ Alta variabilidad en 2016 sugiere posible mezcla de tipos de propiedad

**Conclusión**: 
🟡 **CAMBIO REAL POSIBLE**
- Podría ser real debido a características del barrio (zona de lujo)
- La corrección en 2017 sugiere que 2016 pudo tener valores atípicos incluidos

**Recomendación**:
- Validar con datos oficiales
- Considerar usar mediana en lugar de promedio para 2016

---

### 4. 🟠 Torre Baró (2019) - +174.7% - **REQUIERE VALIDACIÓN**

**Datos fuente**:
- **2018**: 4 registros, promedio 753 €/m²
- **2019**: 4 registros, promedio 2,070 €/m² (alta variabilidad: CV=29.8%)
- **2020**: 5 registros, promedio 1,072 €/m² (corrección significativa)

**Análisis**:
- ⚠️ Cambio muy extremo seguido de corrección en 2020
- ⚠️ Alta variabilidad en 2019 sugiere posibles outliers
- ⚠️ El precio en 2020 vuelve a niveles más razonables

**Conclusión**: 
🟠 **CAMBIO MUY EXTREMO - REQUIERE VALIDACIÓN**
- El patrón (subida extrema seguida de corrección) sugiere posible error
- O podría ser desarrollo inmobiliario específico en 2019

**Recomendación**:
- Investigar datos fuente individuales para 2019
- Validar con datos externos
- Considerar filtrar como outlier si no se puede validar

---

## Recomendaciones Generales

### Inmediatas

1. **Para Baró de Viver (2015)**:
   - ✅ Usar mediana en lugar de promedio (mediana ≈ 634€/m² vs promedio 1,490€/m²)
   - ✅ Filtrar valores >2000€/m² como outliers
   - ✅ Investigar dataset_ids `u25rr7oxh6` y `cq4causxvu`

2. **Para Torre Baró (2019)**:
   - ⚠️ Validar datos fuente individuales
   - ⚠️ Considerar filtrar como outlier si no se valida

### Mediano Plazo

3. **Mejorar agregación**:
   - Usar mediana en lugar de promedio para barrios con alta variabilidad
   - Detectar y filtrar outliers antes de calcular promedios
   - Agregar flag `usa_mediana` cuando CV > 50%

4. **Validación en carga**:
   - Detectar valores >3 desviaciones estándar durante carga ETL
   - Alertar sobre cambios >100% año a año
   - Requerir validación manual para cambios extremos

---

## Archivos Generados

- `data/exports/anomalies/extreme_changes_investigation.json` - Investigación detallada
- `data/exports/anomalies/extreme_changes_summary.md` - Resumen ejecutivo

---

## Próximos Pasos

1. ✅ Investigación completada
2. ⏳ Implementar uso de mediana para Baró de Viver (2015)
3. ⏳ Validar cambios con datos externos (Ayuntamiento de Barcelona)
4. ⏳ Mejorar agregación para manejar alta variabilidad

---

**Estado**: ✅ Investigación completada  
**Acción requerida**: Implementar correcciones para Baró de Viver
