# Mejoras Implementadas en el Módulo de Extracción

Este documento describe las mejoras implementadas en el módulo `data_extraction.py` según las recomendaciones recibidas.

## 1. Sistema de Logging Avanzado

### Implementación
- **Logs en archivo**: Los logs se guardan automáticamente en `logs/data_extraction_YYYYMMDD.log`
- **Rotación diaria**: Los archivos de log se rotan diariamente
- **Retención**: Se mantienen 30 días de logs históricos
- **Tamaño máximo**: 10MB por archivo antes de rotar
- **Encoding UTF-8**: Soporte completo para caracteres especiales

### Uso
```python
from src.data_extraction import setup_logging

# Configurar logging (ya está configurado por defecto)
logger = setup_logging(log_to_file=True, log_level=logging.INFO)
```

### Ubicación de Logs
- Consola: Output en tiempo real
- Archivo: `logs/data_extraction_YYYYMMDD.log`

## 2. Control de Errores por Fuente

### Implementación
- **Continuación automática**: Si una fuente falla, el proceso continúa con las demás
- **Reporte detallado**: Cada error se registra con stack trace completo
- **Metadata de errores**: Los errores se incluyen en el metadata de cobertura
- **Opción fail-fast**: Se puede abortar toda la ejecución si una fuente falla

### Ejemplo
```python
# Continuar aunque una fuente falle (default)
results, metadata = extract_all_sources(
    year_start=2015,
    year_end=2025,
    continue_on_error=True
)

# Abortar si cualquier fuente falla
results, metadata = extract_all_sources(
    year_start=2015,
    year_end=2025,
    continue_on_error=False
)
```

### Metadata de Errores
```json
{
  "sources_failed": ["ine", "idealista"],
  "coverage_by_source": {
    "ine": {
      "error": "Connection timeout",
      "success": false
    }
  }
}
```

## 3. Timestamps Únicos en Archivos

### Implementación
- **Microsegundos**: Timestamp incluye microsegundos para garantizar unicidad
- **Rango de años**: Los nombres de archivo incluyen el rango de años extraídos
- **Formato**: `{filename}_{year_start}_{year_end}_{YYYYMMDD_HHMMSS_ffffff}.{ext}`

### Ejemplo de Nombres
```
ine_demographics_2015_2025_20250115_143022_123456.csv
opendatabcn_demografia-per-barris_2020_2024_20250115_143025_789012.csv
```

### Ventajas
- **Sin sobreescritura**: Cada ejecución genera archivos únicos
- **Trazabilidad**: Fácil identificar cuándo se extrajeron los datos
- **Historial**: Se mantiene historial completo de extracciones

## 4. Validación de Cobertura Temporal

### Implementación
- **Análisis automático**: Se analiza la cobertura temporal de cada fuente
- **Años faltantes**: Identifica qué años no están disponibles
- **Porcentaje de cobertura**: Calcula el porcentaje de cobertura del rango solicitado
- **Reportes en logs**: Advertencias automáticas si la cobertura es incompleta

### Metadata de Cobertura
```json
{
  "coverage_by_source": {
    "ine": {
      "requested_range": {"start": 2015, "end": 2025},
      "years_extracted": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
      "years_failed": [2024, 2025],
      "coverage_percentage": 81.8
    },
    "opendatabcn_demographics": {
      "available_years": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
      "missing_years": [2025],
      "coverage_percentage": 90.9
    }
  }
}
```

### Salida en Logs
```
=== Validación de Cobertura Temporal ===
⚠ ine: Cobertura 81.8% - Años faltantes: [2024, 2025]
✓ opendatabcn_demographics: Cobertura completa (100%)
```

## 5. Preparación para Paralelización (Futuro)

### Estructura Preparada
- **Parámetro `parallel`**: Ya incluido en la función (aunque no implementado aún)
- **Documentación**: Comentarios sobre cómo implementar paralelización
- **Consideraciones**: Rate limits y control de concurrencia

### Implementación Futura Sugerida
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore

def extract_all_sources_parallel(year_start, year_end, sources):
    """Ejemplo de implementación paralela futura."""
    results = {}
    semaphore = Semaphore(3)  # Máximo 3 fuentes simultáneas
    
    def extract_with_limit(source):
        semaphore.acquire()
        try:
            return extract_source(source, year_start, year_end)
        finally:
            semaphore.release()
    
    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {executor.submit(extract_with_limit, s): s for s in sources}
        for future in as_completed(futures):
            source = futures[future]
            try:
                results[source] = future.result()
            except Exception as e:
                logger.error(f"Error en {source}: {e}")
    
    return results
```

### Consideraciones para Paralelización
1. **Rate Limits**: Respetar límites de cada fuente
2. **Semáforos**: Controlar concurrencia por fuente
3. **Thread-safe logging**: El logging ya es thread-safe
4. **Recursos compartidos**: Evitar conflictos en escritura de archivos

## Resumen de Cambios

### Archivos Modificados
- `src/data_extraction.py`: Implementación principal de mejoras
- `scripts/extract_data.py`: Actualizado para usar nueva API
- `.gitignore`: Agregado directorio `logs/`

### Nuevos Archivos
- `logs/`: Directorio para archivos de log (creado automáticamente)
- `docs/EXTRACTION_IMPROVEMENTS.md`: Esta documentación

### Nuevas Funcionalidades
1. ✅ Logging automático en archivo con rotación
2. ✅ Control de errores por fuente (continuar o abortar)
3. ✅ Timestamps únicos con microsegundos y años
4. ✅ Validación de cobertura temporal automática
5. ✅ Estructura preparada para paralelización futura

### Uso Mejorado

```python
# Extracción básica (con todas las mejoras automáticas)
results, metadata = extract_all_sources(year_start=2015, year_end=2025)

# Verificar cobertura
for source, cov_meta in metadata["coverage_by_source"].items():
    if "coverage_percentage" in cov_meta:
        print(f"{source}: {cov_meta['coverage_percentage']:.1f}%")

# Revisar logs
# Los logs están en: logs/data_extraction_YYYYMMDD.log
```

### Beneficios
- **Debugging**: Logs detallados facilitan identificar problemas
- **Robustez**: El sistema no falla completamente si una fuente tiene problemas
- **Trazabilidad**: Historial completo de extracciones con timestamps únicos
- **Calidad**: Validación automática de cobertura temporal
- **Escalabilidad**: Preparado para paralelización cuando sea necesario

