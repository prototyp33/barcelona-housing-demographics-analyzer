# 🎯 Próximos Pasos - Plan Consolidado

**Fecha**: 2026-01-10  
**Estado Actual**: ✅ Mejoras en tabla maestra completadas  
**Última acción**: Implementación de detección de anomalías y validación de calidad

---

## 📊 Estado Actual

### ✅ Completado Recientemente

1. ✅ **Tabla Maestra Mejorada**
   - 16 nuevas columnas de calidad agregadas
   - Detección automática de anomalías
   - Flags de datos faltantes
   - Scripts de validación creados

2. ✅ **EDA Completo**
   - Notebook `05_eda_master_table.ipynb` creado
   - Análisis de cobertura temporal
   - Detección de cambios significativos
   - Análisis de correlaciones
   - Líneas temporales multi-variable

3. ✅ **Investigación de Anomalías**
   - Scripts de análisis creados
   - Reportes CSV generados
   - Documentación completa

---

## 🚀 Próximos Pasos Priorizados

### 🔴 PRIORIDAD ALTA (Esta Semana)

#### 1. Investigar Cambios Extremos en Datos Fuente

**Objetivo**: Validar si los cambios >100% son errores o cambios reales

**Tareas**:
- [ ] Revisar datos fuente para Baró de Viver (2015: +239.8%)
- [ ] Revisar datos fuente para la Marina del Prat Vermell (2015: +135%, 2022 alquiler: +238.3%)
- [ ] Verificar cambios metodológicos en recolección de datos
- [ ] Documentar hallazgos en `docs/VALIDACION_CAMBIOS_EXTREMOS.md`

**Comandos**:
```bash
# Revisar datos fuente en PostgreSQL
psql -d barcelona_housing -c "
SELECT barrio_id, anio, precio_m2_venta, source, dataset_id 
FROM fact_precios 
WHERE barrio_id IN (
    SELECT barrio_id FROM dim_barrios WHERE barrio_nombre LIKE '%Baró de Viver%'
) AND anio BETWEEN 2014 AND 2016
ORDER BY anio;
"
```

**Estimación**: 2-3 horas

---

#### 2. Completar Lagunas de Datos para Barrios Problemáticos

**Objetivo**: Reducir gaps de datos identificados

**Barrios prioritarios**:
- la Clota (2 años faltantes + 2 años con precios nulos)
- Can Peguera (2 años faltantes + 1 año con precios nulos)
- la Marina del Prat Vermell (2 años faltantes)

**Tareas**:
- [ ] Identificar fuentes alternativas para años faltantes
- [ ] Considerar interpolación para gaps pequeños (1-2 años)
- [ ] Documentar años que no pueden completarse
- [ ] Actualizar tabla maestra con datos completados

**Estimación**: 4-6 horas

---

#### 3. Actualizar Visualizaciones en Notebook para Usar Flags de Calidad

**Objetivo**: Mejorar visualizaciones para mostrar datos faltantes claramente

**Tareas**:
- [ ] Actualizar gráficos para usar líneas discontinuas cuando `precio_venta_faltante = 1`
- [ ] Agregar tooltips con información de completitud
- [ ] Crear visualización de calidad de datos por barrio
- [ ] Usar datos suavizados para líneas temporales principales

**Archivo**: `notebooks/05_eda_master_table.ipynb`

**Estimación**: 2-3 horas

---

### 🟠 PRIORIDAD MEDIA (Próximas 2 Semanas)

#### 4. Crear Dashboard de Calidad de Datos

**Objetivo**: Visualización interactiva del estado de calidad de datos

**Tareas**:
- [ ] Crear vista en Streamlit o Looker Studio
- [ ] Mostrar métricas de completitud por barrio/año
- [ ] Alertas para anomalías detectadas
- [ ] Gráficos de evolución de calidad temporal

**Estimación**: 4-6 horas

---

#### 5. Implementar Interpolación para Gaps Pequeños

**Objetivo**: Completar automáticamente gaps de 1-2 años usando interpolación

**Tareas**:
- [ ] Crear función de interpolación lineal para precios
- [ ] Validar que interpolación es razonable (comparar con años adyacentes)
- [ ] Agregar flag `dato_interpolado` para transparencia
- [ ] Documentar metodología de interpolación

**Estimación**: 3-4 horas

---

#### 6. Mejorar Validación en Carga de Datos Fuente

**Objetivo**: Detectar problemas antes de que lleguen a la tabla maestra

**Tareas**:
- [ ] Agregar validación de cambios extremos en `fact_precios`
- [ ] Validar rangos razonables de precios por barrio
- [ ] Alertar sobre cambios >50% año a año durante carga
- [ ] Generar reporte de calidad en cada carga ETL

**Estimación**: 4-5 horas

---

### 🟡 PRIORIDAD BAJA (Backlog)

#### 7. Crear Alertas Automáticas para Nuevos Cambios Extremos

**Objetivo**: Detectar automáticamente nuevos problemas en datos

**Tareas**:
- [ ] Integrar validación en pipeline ETL
- [ ] Enviar alertas cuando se detecten cambios extremos
- [ ] Crear dashboard de monitoreo

**Estimación**: 6-8 horas

---

#### 8. Mejorar Estructura de Agregación (Opcional)

**Objetivo**: Evitar CROSS JOIN problemático

**Tareas**:
- [ ] Evaluar alternativas a CROSS JOIN
- [ ] Implementar solo años con datos válidos (sin CROSS JOIN)
- [ ] Mantener compatibilidad con visualizaciones existentes

**Estimación**: 4-6 horas

---

## 📋 Plan de Acción Inmediato (Esta Semana)

### Día 1-2: Investigación
- [ ] Investigar cambios extremos en datos fuente
- [ ] Documentar hallazgos
- [ ] Decidir si son errores o cambios reales

### Día 3-4: Completar Datos
- [ ] Identificar fuentes para años faltantes
- [ ] Completar lagunas donde sea posible
- [ ] Actualizar tabla maestra

### Día 5: Mejoras en Visualización
- [ ] Actualizar notebook con flags de calidad
- [ ] Mejorar visualizaciones para mostrar gaps
- [ ] Probar datos suavizados

---

## 🛠️ Comandos Útiles

### Regenerar Tabla Maestra
```bash
python scripts/create_master_table_for_looker.py
```

### Validar Calidad
```bash
python scripts/validate_master_table_quality.py
```

### Investigar Anomalías
```bash
python scripts/investigate_data_anomalies.py
```

### Generar Datos Suavizados
```bash
python scripts/add_smoothed_data_to_master.py
```

### Ejecutar EDA Completo
```bash
jupyter notebook notebooks/05_eda_master_table.ipynb
```

---

## 📊 Métricas de Éxito

### Corto Plazo (1 semana)
- ✅ Cambios extremos investigados y documentados
- ✅ Lagunas de datos reducidas en 50%
- ✅ Visualizaciones mejoradas con flags de calidad

### Mediano Plazo (1 mes)
- ✅ Dashboard de calidad creado
- ✅ Interpolación implementada para gaps pequeños
- ✅ Validación en carga de datos implementada

### Largo Plazo (3 meses)
- ✅ Alertas automáticas funcionando
- ✅ Cobertura de datos >90% para todos los barrios
- ✅ Sistema de monitoreo de calidad establecido

---

## 🎯 Recomendación Inmediata

**Empezar con**: Investigación de cambios extremos (Prioridad Alta #1)

**Razón**: 
- Es la acción más crítica para validar calidad de datos
- Requiere menos tiempo (2-3 horas)
- Proporciona información valiosa para decisiones futuras
- Puede revelar problemas sistémicos en recolección de datos

**Siguiente paso**: Completar lagunas de datos una vez validados los cambios extremos

---

## 📚 Documentación de Referencia

- `docs/DATA_ANOMALIES_REPORT.md` - Reporte completo de anomalías
- `docs/MASTER_TABLE_IMPROVEMENTS.md` - Detalles técnicos de mejoras
- `docs/IMPLEMENTATION_SUMMARY.md` - Resumen de implementación
- `data/exports/anomalies/README.md` - Guía de reportes de anomalías

---

**Última actualización**: 2026-01-10  
**Próxima revisión**: Después de completar investigación de cambios extremos
