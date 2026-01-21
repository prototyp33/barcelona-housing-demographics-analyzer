# Plan de Consolidación e Integridad de Datos - Fase 2

## 📝 Visión General
Este documento detalla el plan de acción para resolver las brechas de datos identificadas en la inspección del esquema del 2026-01-04 y restaurar la funcionalidad completa de las vistas analíticas.

## 🎯 Objetivos Principales
1.  **Limpieza de Deuda Técnica**: Reparar las vistas rotas y eliminar redundancias.
2.  **Cierre de Gaps de Datos**: Integrar las 5 fuentes críticas que aún están vacías.
3.  **Verificación de Anomalías**: Corregir errores temporales en tablas de movilidad.

---

## 🛠️ Acción 1: Reparación de Infraestructura (Vistas)
*Prioridad: Alta | Tiempo estimado: 2 horas*

| Vista | Error Detectado | Solución |
| :--- | :--- | :--- |
| `fact_accesibilidad` | Columna `tiempo_medio_centro_minutos` inexistente | Re-mapear con columnas de `fact_movilidad`. |
| `fact_airbnb` | Columna `etl_loaded_at` inexistente | Actualizar DDL para incluir metadatos de carga. |
| `fact_control_alquiler` | Columna `etl_loaded_at` inexistente | Sincronizar con `fact_regulacion`. |
| `vw_gentrification_risk` | Columna `pct_universitarios` faltante | Verificar nombre en `fact_educacion` (ej: `pct_estudios_univ`). |

---

## 🔍 Acción 2: Investigación de Anomalías
*Prioridad: Media | Tiempo estimado: 1 hora*

*   **Caso Movilidad 2026**: Investigar por qué `fact_movilidad` registra el año 2026.
    *   *Posibles causas*: Error en el script `process_movilidad_data.py` o uso de proyecciones futuras.
    *   *Acción*: Ejecutar `scripts/db_status.py` filtrado por movilidad y corregir a 2024/2025.

---

## 🚀 Acción 3: Integración de Fuentes Pendientes (Gaps)
*Prioridad: Alta | Tiempo estimado: 8-10 horas*

| Tabla | Fuente Identificada | Estado |
| :--- | :--- | :--- |
| `fact_calidad_aire` | Open Data BCN (Mapas de inmisión) | **En progreso** (Extractor base creado). |
| `fact_hut` | Registro de Turismo de Cataluña | **Pendiente** (Búsqueda de API Socrata). |
| `fact_desempleo` | IDESCAT (Demanda de ocupación) | **Pendiente** (Integrar en `idescat.py`). |
| `fact_turismo_intensidad` | Open Data BCN | **Pendiente**. |
| `fact_visados` | COAC (Colegio de Arquitectos) | **Pendiente**. |

---

## 🧹 Acción 4: Consolidación y Limpieza
*Prioridad: Baja | Tiempo estimado: 1 hora*

*   **Unificación de Ruido**: 
    *   Mover cualquier dato remanente de `fact_soroll` a `fact_ruido`.
    *   Eliminar la tabla `fact_soroll` para evitar confusión entre desarrolladores.
*   **Normalización de Nombres**: Asegurar que todas las tablas `fact_` usen `anio` y no `year`.

---

## 📅 Roadmap de Ejecución

### Semana 1: Saneamiento
*   Día 1: Ejecutar script de corrección de vistas SQL.
*   Día 2: Corregir anomalía de movilidad y consolidar tablas de ruido.
*   Día 3: Finalizar e integrar `fact_calidad_aire`.

### Semana 2: Expansión
*   Día 4: Implementación de Extractor HUT y Desempleo.
*   Día 5: Carga de Visados y Turismo.
*   Día 6: Auditoría final de 100% de cobertura.

---

## 📊 KPIs de Éxito
*   ✅ **Cobertura de Tablas**: 25/25 tablas con datos (100%).
*   ✅ **Integridad de Vistas**: 15/15 vistas funcionales sin errores de columna.
*   ✅ **Consistencia Temporal**: Todos los datos dentro del rango 2012-2025.

