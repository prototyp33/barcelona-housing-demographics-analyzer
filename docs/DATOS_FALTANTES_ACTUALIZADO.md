# 📊 Análisis de Datos Faltantes - Actualizado

**Fecha**: Diciembre 2025  
**Análisis**: Estado actual de la base de datos

---

## 🔴 DATOS CRÍTICOS FALTANTES

### 1. **Precios de Alquiler en `fact_precios`** ❌ CRÍTICO

**Estado Actual**:
- **Total registros con precio de venta**: 5,492
- **Registros con precio de alquiler REAL**: **0 (0.0%)**
- **FALTAN**: 5,492 registros de alquiler

**Impacto en el Reporte**:
- ❌ No se puede calcular ratio de asequibilidad real
- ❌ No se puede calcular yield bruto real
- ❌ Secciones de "Barrios Más Asequibles" y "Potencial de Inversión" muestran datos estimados o N/A

**Fuentes Disponibles para Obtenerlos**:

1. **Incasòl (Generalitat)** ✅ EXTRACTOR DISPONIBLE
   - Dataset: Registre de fiances de lloguer
   - URL: https://analisi.transparenciacatalunya.cat/
   - **Ventaja**: Precios reales de cierre (no oferta)
   - **Limitación**: Agregado por municipio/distrito, no por barrio individual
   - **Extractor**: `src/extraction/incasol.py` (IncasolSocrataExtractor)
   - **Estado**: Implementado pero no ejecutado

2. **Idealista API** ⚠️ LIMITADO
   - **Estado actual**: `fact_oferta_idealista` tiene 949 registros de "rent" (alquiler)
   - **Cobertura**: 73 barrios, año 2025
   - **Limitación**: Límite de 150 calls/mes en RapidAPI
   - **Extractor**: `src/extraction/idealista.py` (IdealistaExtractor)
   - **Nota**: Ya hay datos en la tabla pero no están conectados a `fact_precios.precio_mes_alquiler`

3. **Portal de Dades** 🔄 POR VERIFICAR
   - Verificar si hay datasets de alquiler que no se hayan extraído
   - **Extractor**: `src/extraction/portaldades.py` (PortalDadesExtractor)

**Acción Recomendada**:
1. **Prioridad Alta**: Conectar datos de `fact_oferta_idealista` (operacion='rent') a `fact_precios.precio_mes_alquiler`
2. **Prioridad Media**: Ejecutar extractor de Incasòl para validar precios reales de cierre
3. **Prioridad Baja**: Buscar más fuentes de datos de alquiler en Portal de Dades

---

### 2. **Datos de Vivienda Pública** ❌ TABLA VACÍA

**Estado Actual**:
- **Tabla**: `fact_vivienda_publica`
- **Registros**: **0**
- **Cobertura**: 0/73 barrios

**Impacto**:
- No se puede analizar el impacto de vivienda pública en el mercado
- No se puede calcular ratio de vivienda pública por barrio

**Fuente Disponible**:
- **Extractor**: `src/extraction/vivienda_publica_extractor.py` (ViviendaPublicaExtractor)
- **Estado**: Implementado pero no ejecutado

**Acción Recomendada**:
- Ejecutar extractor de vivienda pública para poblar la tabla

---

## ⚠️ DATOS INCOMPLETOS O CON COBERTURA LIMITADA

### 3. **Servicios de Salud** ⚠️ FALTAN 4 BARRIOS

**Estado Actual**:
- **Registros**: 69/73 barrios (94.5%)
- **Año más reciente**: 2025
- **Faltan**: 4 barrios sin datos

**Barrios faltantes**: Verificar con:
```sql
SELECT db.barrio_nombre 
FROM dim_barrios db
LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id
WHERE fs.barrio_id IS NULL;
```

**Acción Recomendada**:
- Verificar si los 4 barrios faltantes tienen datos disponibles en la fuente
- Re-ejecutar extractor si es necesario

---

### 4. **Comercio** ⚠️ FALTAN 3 BARRIOS

**Estado Actual**:
- **Registros**: 70/73 barrios (95.9%)
- **Año más reciente**: 2025
- **Faltan**: 3 barrios sin datos

**Acción Recomendada**:
- Verificar y completar datos faltantes

---

### 5. **Medio Ambiente** ⚠️ FALTAN 3 BARRIOS

**Estado Actual**:
- **Registros**: 70/73 barrios (95.9%)
- **Año más reciente**: 2025
- **Faltan**: 3 barrios sin datos

**Acción Recomendada**:
- Verificar y completar datos faltantes

---

### 6. **Presión Turística** ⚠️ FALTAN 2 BARRIOS

**Estado Actual**:
- **Registros**: 71/73 barrios (97.3%)
- **Año más reciente**: 2025
- **Faltan**: 2 barrios sin datos

**Acción Recomendada**:
- Verificar y completar datos faltantes

---

### 7. **Movilidad** ⚠️ COBERTURA MUY LIMITADA

**Estado Actual**:
- **Registros**: 3 registros totales
- **Cobertura**: Muy limitada

**Acción Recomendada**:
- Revisar extractores de movilidad (`BicingExtractor`, `ATMExtractor`)
- Ejecutar extracción completa si es necesario

---

## ✅ DATOS COMPLETOS

### Tablas con Cobertura Completa (73/73 barrios):

1. ✅ **dim_barrios**: 73/73 (100%)
2. ✅ **fact_educacion**: 73/73 (100%)
3. ✅ **fact_seguridad**: 73/73 (100%)
4. ✅ **fact_regulacion**: 73/73 (100%)
5. ✅ **fact_renta**: 73/73 (100%) - ⚠️ Pero solo 1 año de datos
6. ✅ **fact_ruido**: 73/73 (100%)
7. ✅ **fact_demografia**: 657 registros (múltiples años)

---

## 📋 PLAN DE ACCIÓN PRIORIZADO

### Prioridad CRÍTICA 🔴 (Esta Semana)

1. **Conectar datos de alquiler de Idealista a fact_precios**
   - **Tarea**: Crear script de migración/actualización
   - **Archivo**: `scripts/connect_idealista_rental_to_precios.py` (crear)
   - **Impacto**: Resolvería el problema crítico de datos de alquiler
   - **Tiempo estimado**: 2-3 horas

2. **Ejecutar extractor de Incasòl**
   - **Tarea**: Ejecutar `IncasolSocrataExtractor` para obtener precios reales de cierre
   - **Impacto**: Validación de precios de alquiler reales
   - **Tiempo estimado**: 1-2 horas

### Prioridad ALTA 🟡 (Próximas 2 Semanas)

3. **Completar datos faltantes de servicios**
   - Servicios de salud: 4 barrios
   - Comercio: 3 barrios
   - Medio ambiente: 3 barrios
   - Presión turística: 2 barrios
   - **Tiempo estimado**: 2-3 horas

4. **Ejecutar extractor de vivienda pública**
   - **Tarea**: Ejecutar `ViviendaPublicaExtractor`
   - **Impacto**: Añadir análisis de vivienda pública
   - **Tiempo estimado**: 1-2 horas

### Prioridad MEDIA 🟢 (Próximo Mes)

5. **Expandir datos históricos de renta**
   - **Tarea**: Extraer datos de renta para múltiples años (2015-2025)
   - **Impacto**: Análisis temporal de renta vs precios
   - **Tiempo estimado**: 2-3 horas

6. **Completar datos de movilidad**
   - **Tarea**: Revisar y ejecutar extractores de movilidad
   - **Tiempo estimado**: 3-4 horas

---

## 🔍 VERIFICACIÓN RÁPIDA

Para verificar qué datos faltan en tiempo real:

```bash
cd /Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer
source .venv/bin/activate
python scripts/check_missing_data.py  # Crear este script si no existe
```

O ejecutar directamente:

```python
import sqlite3
from pathlib import Path

db_path = Path('data/processed/database.db')
conn = sqlite3.connect(str(db_path))

# Verificar datos de alquiler
cursor = conn.cursor()
cursor.execute('''
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN precio_mes_alquiler IS NOT NULL THEN 1 ELSE 0 END) as con_alquiler
    FROM fact_precios
    WHERE precio_m2_venta IS NOT NULL
''')
result = cursor.fetchone()
print(f"Precios de alquiler: {result[1]}/{result[0]} ({result[1]/result[0]*100:.1f}%)")
```

---

## 📊 RESUMEN EJECUTIVO

| Categoría | Estado | Registros Faltantes | Prioridad |
|-----------|--------|---------------------|-----------|
| **Precios de Alquiler** | ❌ Crítico | 5,492 | 🔴 ALTA |
| **Vivienda Pública** | ❌ Vacío | 73 barrios | 🟡 MEDIA |
| **Servicios Salud** | ⚠️ Incompleto | 4 barrios | 🟡 MEDIA |
| **Comercio** | ⚠️ Incompleto | 3 barrios | 🟢 BAJA |
| **Medio Ambiente** | ⚠️ Incompleto | 3 barrios | 🟢 BAJA |
| **Presión Turística** | ⚠️ Incompleto | 2 barrios | 🟢 BAJA |
| **Movilidad** | ⚠️ Muy limitado | ~70 barrios | 🟢 BAJA |

---

## 🎯 CONCLUSIÓN

**El problema más crítico es la falta de datos de alquiler en `fact_precios`**. 

**Solución inmediata**: Conectar los datos existentes en `fact_oferta_idealista` (operacion='rent') a `fact_precios.precio_mes_alquiler`. Esto resolvería el 100% del problema crítico ya que tenemos 949 registros de alquiler de Idealista para 73 barrios en 2025.

