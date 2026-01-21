# Reporte de Anomalías en Datos - Tabla Maestra

**Fecha**: 2026-01-10  
**Análisis**: Investigación de valores raros y caídas en gráficos

## Resumen Ejecutivo

Se detectaron **anomalías significativas** en la tabla maestra que explican las "caídas" observadas en los gráficos. Los problemas principales son:

1. **Cambios abruptos** en precios (>50% año a año)
2. **Lagunas de datos** (años faltantes o precios nulos)
3. **Problema estructural** en la agregación de datos

## Hallazgos Principales

### 1. Cambios Abruptos Detectados

#### Precio de Venta (12 casos)
- **Baró de Viver** (2015): +239.8% - **MUY SOSPECHOSO**
- **Torre Baró** (2019): +174.7%
- **la Marina del Prat Vermell** (2015): +135.0%
- **Vallvidrera** (2016): +117.6%
- **la Clota** (2016): -65.4% (caída)

#### Precio de Alquiler (6 casos)
- **la Marina del Prat Vermell** (2022): +238.3% - **MUY SOSPECHOSO**
- **Baró de Viver** (2017): +111.8%

**Interpretación**: Cambios >100% son extremadamente raros en mercados inmobiliarios y probablemente indican:
- Errores en la fuente de datos
- Cambios en metodología de recolección
- Valores atípicos no filtrados

### 2. Lagunas de Datos Identificadas

**5 barrios con problemas de cobertura**:

1. **la Clota**: 2 años faltantes + 2 años con precios nulos
2. **Can Peguera**: 2 años faltantes + 1 año con precios nulos
3. **la Marina del Prat Vermell**: 2 años faltantes
4. **Vallbona**: 1 año faltante
5. **Baró de Viver**: 1 año faltante + 1 año con precio sospechosamente bajo

**Problema Estructural**: El script `create_master_table_for_looker.py` usa:
```sql
CROSS JOIN (SELECT DISTINCT anio FROM fact_precios) years
LEFT JOIN precios_agg p ON b.barrio_id = p.barrio_id AND years.anio = p.anio
WHERE p.anio IS NOT NULL
```

Esto crea filas para **todos los barrios × todos los años**, pero luego filtra solo los que tienen precios. Si un barrio tiene datos en 2012, 2013, 2015 pero **no en 2014**, ese año simplemente no aparece, creando una "caída" visual en los gráficos.

### 3. Outliers Estadísticos

**4 outliers detectados** (Z-score > 3):
- **Pedralbes** (2020): 7,152 €/m² (Z-score: +3.42)
- **Diagonal Mar** (2015): 5,099 €/m² (Z-score: +3.09)
- **Sarrià** (2012): 4,500 €/m² (Z-score: +3.07)
- **Pedralbes** (2015): 5,039 €/m² (Z-score: +3.02)

Estos pueden ser valores reales (barrios de lujo) o errores de datos.

## Causas Raíz Identificadas

### 1. Estructura de Datos Fuente

La tabla `fact_precios` puede tener:
- **Datos faltantes por año** para algunos barrios
- **Múltiples fuentes** con metodologías diferentes
- **Cambios en cobertura temporal** (algunos años tienen más datos que otros)

### 2. Agregación Problemática

El `CROSS JOIN` + `LEFT JOIN` + `WHERE p.anio IS NOT NULL` crea un patrón donde:
- ✅ Se incluyen años con datos
- ❌ Se excluyen años sin datos (aparecen como "caídas")
- ⚠️ No hay distinción entre "dato faltante" y "precio real de 0"

### 3. Falta de Validación

No hay validación de:
- Cambios extremos año a año
- Valores fuera de rangos esperados
- Consistencia entre fuentes de datos

## Recomendaciones

### Inmediatas

1. **Investigar cambios abruptos >100%**:
   - Verificar datos fuente para Baró de Viver (2015), la Marina del Prat Vermell (2015, 2022)
   - Validar si son errores o cambios reales

2. **Completar lagunas de datos**:
   - Identificar por qué faltan años para la Clota, Can Peguera, etc.
   - Considerar interpolación o marcado explícito de datos faltantes

3. **Mejorar visualizaciones**:
   - Mostrar explícitamente cuando faltan datos (líneas discontinuas, marcadores diferentes)
   - Agregar notas sobre años con datos limitados

### Mediano Plazo

4. **Mejorar script de agregación**:
   ```sql
   -- Opción 1: Incluir todos los años pero marcar datos faltantes
   SELECT 
       ...,
       CASE WHEN p.anio IS NULL THEN 1 ELSE 0 END AS datos_faltantes
   
   -- Opción 2: Solo incluir años con datos válidos (sin CROSS JOIN)
   SELECT ...
   FROM precios_agg p
   JOIN dim_barrios b ON p.barrio_id = b.barrio_id
   ```

5. **Agregar validaciones**:
   - Detectar cambios >50% año a año automáticamente
   - Marcar outliers antes de exportar
   - Generar reporte de calidad de datos

6. **Suavizar datos para visualización**:
   - Usar medias móviles de 3 años para reducir ruido
   - Mostrar tanto datos brutos como suavizados

### Largo Plazo

7. **Mejorar calidad de datos fuente**:
   - Validar datos al momento de carga
   - Documentar cambios en metodología
   - Mantener historial de fuentes de datos

8. **Crear vista de datos limpios**:
   - Vista SQL que filtre outliers conocidos
   - Vista que complete lagunas con interpolación
   - Vista que marque datos estimados vs. reales

## Archivos Generados

- `scripts/investigate_data_anomalies.py` - Script de análisis de anomalías
- `data/exports/anomalies/abrupt_changes_venta.csv` - Cambios abruptos en venta
- `data/exports/anomalies/abrupt_changes_alquiler.csv` - Cambios abruptos en alquiler
- `data/exports/anomalies/outliers.csv` - Outliers estadísticos

## Uso del Script de Investigación

```bash
python scripts/investigate_data_anomalies.py
```

Este script genera:
- Lista de cambios abruptos
- Análisis de lagunas de datos
- Detección de outliers
- Estadísticas de distribución por año

## Próximos Pasos

1. ✅ Ejecutar análisis de anomalías (completado)
2. ✅ Implementar flags de calidad de datos (completado)
3. ✅ Agregar detección automática de anomalías (completado)
4. ✅ Crear script de validación (completado)
5. ✅ Generar datos suavizados (completado)
6. ⏳ Revisar datos fuente para cambios abruptos >100%
7. ⏳ Decidir estrategia para manejar lagunas (interpolación vs. marcado explícito)
8. ⏳ Actualizar visualizaciones para mostrar datos faltantes claramente

## Mejoras Implementadas

Ver `docs/MASTER_TABLE_IMPROVEMENTS.md` para detalles completos de las mejoras implementadas.

**Resumen**:
- ✅ 16 nuevas columnas de calidad y validación agregadas
- ✅ Detección automática de anomalías integrada
- ✅ Scripts de validación y suavizado creados
- ✅ Tabla maestra mejorada con flags de calidad

---

**Nota**: Las "caídas" en los gráficos son principalmente **datos faltantes**, no caídas reales de precios. Es importante distinguir entre ambos casos para interpretar correctamente las visualizaciones. Las nuevas columnas de calidad permiten identificar y filtrar estos casos automáticamente.
