# ✅ Investigación de Cambios Extremos - Completada

**Fecha**: 2026-01-10  
**Estado**: ✅ Completado

---

## Resumen de Hallazgos

### 🔴 Caso Crítico: Baró de Viver (2015) - **ERROR DE DATOS CONFIRMADO**

**Problema identificado**:
- **Cambio detectado**: +239.8% (de 438€/m² a 1,490€/m²)
- **Causa raíz**: Mezcla de dos grupos distintos de valores en el mismo año
  - **Grupo 1** (3 registros): ~634-665 €/m² (valores normales, consistentes con años adyacentes)
  - **Grupo 2** (2 registros): 2,758 €/m² (valores extremos, 6x más altos)
- **Dataset IDs problemáticos**: `u25rr7oxh6` y `cq4causxvu` tienen valores >2000€/m²
- **CV (Coeficiente de Variabilidad)**: 77.7% (muy alto, indica datos inconsistentes)

**Solución implementada**:
- ✅ Script creado para corregir agregación usando mediana filtrada
- ✅ Precio corregido: ~634 €/m² (mediana después de filtrar outliers)
- ✅ Esto reduce el cambio de +239.8% a ~+44.7% (más razonable)

**Archivo corregido**: `master_table_barcelona_housing_corrected.csv`

---

### 🟡 Casos que Requieren Validación Externa

#### 1. la Marina del Prat Vermell (2015) - +135.0%
- **Evaluación**: Cambio real posible
- **Evidencia**: Baja variabilidad, valores consistentes
- **Acción**: Validar con datos del Ayuntamiento

#### 2. Vallvidrera (2016) - +117.6%
- **Evaluación**: Cambio real posible (barrio de lujo)
- **Evidencia**: Valores altos consistentes con características del barrio
- **Acción**: Validar con datos oficiales

#### 3. Torre Baró (2019) - +174.7%
- **Evaluación**: Cambio muy extremo, requiere validación
- **Evidencia**: Patrón sospechoso (subida extrema seguida de corrección)
- **Acción**: Investigar datos fuente individuales

---

## Archivos Generados

1. ✅ `scripts/investigate_extreme_changes.py` - Script de investigación
2. ✅ `scripts/fix_barrio_viver_aggregation.py` - Corrección de Baró de Viver
3. ✅ `data/exports/anomalies/extreme_changes_investigation.json` - Datos detallados
4. ✅ `data/exports/anomalies/extreme_changes_summary.md` - Resumen
5. ✅ `docs/VALIDACION_CAMBIOS_EXTREMOS.md` - Documentación completa
6. ✅ `data/exports/looker_studio/master_table_barcelona_housing_corrected.csv` - Tabla corregida

---

## Próximos Pasos Recomendados

### Inmediatos

1. ✅ **Completado**: Investigar cambios extremos
2. ✅ **Completado**: Corregir Baró de Viver usando mediana
3. ⏳ **Pendiente**: Validar otros cambios extremos con datos externos
4. ⏳ **Pendiente**: Implementar uso de mediana automático para CV > 50%

### Mediano Plazo

5. ⏳ Mejorar agregación en `create_master_table_for_looker.py`:
   - Detectar alta variabilidad (CV > 50%)
   - Usar mediana automáticamente cuando CV > 50%
   - Agregar flag `usa_mediana` para transparencia

6. ⏳ Validación en carga ETL:
   - Alertar sobre cambios >100% durante carga
   - Requerir validación manual para cambios extremos

---

## Lecciones Aprendidas

1. **Promedio vs Mediana**: 
   - Promedio puede estar sesgado por outliers
   - Mediana es más robusta para datos con alta variabilidad
   - CV > 50% indica necesidad de usar mediana

2. **Validación de Datos**:
   - Cambios >100% siempre requieren investigación
   - Alta variabilidad (CV > 50%) sugiere posibles errores
   - Patrones de corrección posteriores indican posibles problemas

3. **Agregación Mejorada**:
   - Filtrar outliers antes de agregar
   - Usar mediana cuando hay alta variabilidad
   - Documentar metodología de agregación

---

**Estado**: ✅ Investigación completada  
**Acción siguiente**: Implementar agregación mejorada con detección automática de alta variabilidad
