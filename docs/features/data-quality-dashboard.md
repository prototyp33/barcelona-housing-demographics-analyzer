# 🔍 Data Quality Monitoring Dashboard

**Feature:** Dashboard de monitoreo de calidad de datos en tiempo real  
**Issue:** #97  
**Estado:** ✅ Implementado  
**Fecha:** 2025-12-04

---

## 📋 Descripción

Dashboard interactivo en Streamlit que visualiza métricas de calidad de datos en tiempo real, permitiendo la detección temprana de problemas y el seguimiento de KPIs de calidad.

## 🎯 Funcionalidades

### Métricas Principales

1. **Completeness (Completitud)**
   - Porcentaje de campos no nulos en tablas principales
   - Objetivo: ≥95%
   - Calculado desde: `fact_precios`, `fact_demografia`, `fact_renta`

2. **Validity (Validez)**
   - Porcentaje de datos dentro de rangos esperados
   - Objetivo: ≥98%
   - Validaciones:
     - Precios: 0 < precio_m2 < 20,000 €/m²
     - Población: 0 < poblacion < 200,000 por barrio
     - Años: 2015 ≤ anio ≤ 2025

3. **Consistency (Consistencia)**
   - Coherencia entre fuentes (barrios presentes en todas las tablas)
   - Objetivo: ≥95%
   - Calculado como intersección de barrios entre tablas

4. **Timeliness (Actualidad)**
   - Antigüedad del dato más reciente en días
   - Objetivo: < 90 días
   - Basado en el año máximo encontrado en las tablas

### Visualizaciones

- **Gráfico de Evolución Temporal**: Muestra evolución de métricas en últimos 24 meses
- **Tabla de Issues Detectados**: Lista problemas encontrados con severidad
- **Validación Manual**: Botón para ejecutar `verify_integrity.py` desde el dashboard

## 📁 Archivos Creados/Modificados

### Nuevos Archivos

- `src/app/data_quality_metrics.py` - Módulo de cálculo de métricas
- `src/app/views/data_quality.py` - Vista del dashboard
- `tests/test_data_quality_metrics.py` - Tests unitarios

### Archivos Modificados

- `src/app/main.py` - Integración de la nueva pestaña
- `src/app/views/__init__.py` - Exportación del módulo
- `scripts/verify_integrity.py` - Mejora para retornar datos estructurados

## 🚀 Uso

### Desde el Dashboard

1. Iniciar dashboard:
   ```bash
   streamlit run src/app/main.py
   ```

2. Navegar a la pestaña "Calidad de Datos"

3. Ver métricas en tiempo real y ejecutar validaciones

### Desde Código

```python
from src.app.data_quality_metrics import (
    calculate_completeness,
    calculate_validity,
    calculate_consistency,
    calculate_timeliness,
    detect_quality_issues
)

# Calcular métricas
completeness = calculate_completeness()  # 96.2%
validity = calculate_validity()          # 98.5%
consistency = calculate_consistency()    # 94.8%
timeliness = calculate_timeliness()      # 2 días

# Detectar issues
issues_df = detect_quality_issues()
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/test_data_quality_metrics.py -v

# Con coverage
pytest tests/test_data_quality_metrics.py --cov=src.app.data_quality_metrics
```

## 📊 Métricas de Rendimiento

- **Cache TTL**: 5 minutos (300 segundos)
- **Tiempo de cálculo**: < 1 segundo por métrica
- **Queries optimizadas**: Uso de índices y agregaciones

## 🔧 Configuración

Las métricas se calculan automáticamente desde la base de datos en `data/processed/database.db`.

Para ajustar objetivos:

```python
# En src/app/views/data_quality.py
COMPLETENESS_TARGET = 95.0
VALIDITY_TARGET = 98.0
CONSISTENCY_TARGET = 95.0
TIMELINESS_TARGET_DAYS = 90
```

## 📈 Próximas Mejoras

- [ ] Guardar métricas históricas en tabla `etl_quality_metrics`
- [ ] Alertas automáticas cuando métricas < umbrales
- [ ] Exportación de reportes de calidad
- [ ] Comparación entre diferentes ejecuciones ETL
- [ ] Dashboard de tendencias por barrio

## 🔗 Referencias

- [Issue #97](https://github.com/prototyp33/barcelona-housing-demographics-analyzer/issues/97)
- [Script de Validación](scripts/verify_integrity.py)
- [Documentación Streamlit](https://docs.streamlit.io/)

---

**Última actualización:** 2025-12-04

