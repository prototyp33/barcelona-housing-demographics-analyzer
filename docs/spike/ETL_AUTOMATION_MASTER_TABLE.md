# Automatización de Carga del Master Table en Pipeline ETL

**Fecha**: 2025-12-14  
**Estado**: ✅ Implementado

---

## 📋 Resumen

La carga del Master Table (`fact_housing_master`) ahora está **automatizada** en el pipeline ETL principal. El pipeline detecta automáticamente si existe el CSV del Master Table y lo carga en la base de datos.

---

## 🔄 Flujo Automatizado

### 1. Generación del Master Table (Manual)

El Master Table se genera ejecutando:

```bash
python scripts/merge_datasets.py
```

**Output**: `data/processed/barcelona_housing_master_table.csv`

**Dependencias**:
- `data/raw/official_prices_2015_2024.csv`
- `data/raw/socioeconomics_renta_2015_2023.csv`
- `data/raw/barrio_structural_attributes.csv`
- `data/raw/advanced_attributes.csv`

### 2. Pipeline ETL (Automático)

Cuando se ejecuta el pipeline ETL:

```bash
python scripts/process_and_load.py
# o
python -m src.etl.pipeline
```

**El pipeline ahora**:
1. ✅ Carga todas las tablas tradicionales (`fact_precios`, `fact_renta`, etc.)
2. ✅ **Verifica automáticamente** si existe `barcelona_housing_master_table.csv`
3. ✅ **Carga automáticamente** el Master Table si existe
4. ✅ Registra estadísticas en `etl_runs`

---

## 🏗️ Arquitectura

### Módulo Reutilizable

**Archivo**: `src/etl/load_master_table.py`

**Funciones principales**:

1. **`create_master_table_schema(conn)`**
   - Crea la tabla `fact_housing_master` y sus índices
   - Idempotente (no falla si ya existe)

2. **`load_master_table_from_csv(conn, csv_path, truncate=True)`**
   - Carga datos del CSV a la tabla
   - Valida integridad referencial
   - Carga en chunks para evitar límites de SQLite

3. **`load_master_table_if_exists(conn, processed_dir)`**
   - Función de alto nivel para uso en pipeline
   - Retorna `(loaded: bool, count: int)`
   - No falla si el CSV no existe (solo retorna `False`)

### Integración en Pipeline

**Archivo**: `src/etl/pipeline.py`

**Ubicación**: Después de cargar todas las tablas tradicionales, antes de registrar el ETL run.

```python
# Cargar Master Table si existe (opcional)
logger.info("Verificando si existe Master Table para cargar")
master_loaded, master_count = load_master_table_if_exists(
    conn, processed_dir
)
if master_loaded:
    logger.info(
        f"✓ Master Table cargado: {master_count:,} registros en fact_housing_master"
    )
    params["fact_housing_master_rows"] = master_count
else:
    logger.debug(
        "Master Table CSV no encontrado. "
        "Ejecute scripts/merge_datasets.py para generarlo."
    )
    params["fact_housing_master_rows"] = 0
```

---

## 📊 Orden de Ejecución

```
1. Extracción (E) - scripts/extract_*.py
   ↓
2. Generación Master Table (Manual) - scripts/merge_datasets.py
   ↓
3. Pipeline ETL (T+L) - scripts/process_and_load.py
   ├─ Carga dim_barrios
   ├─ Carga fact_precios
   ├─ Carga fact_renta
   ├─ Carga fact_demografia
   ├─ Carga fact_oferta_idealista
   └─ ✅ Carga fact_housing_master (automático si existe)
   ↓
4. Registro en etl_runs
```

---

## ✅ Ventajas de la Automatización

### 1. **Sin Pasos Manuales Adicionales**
- ✅ El pipeline detecta y carga automáticamente
- ✅ No requiere ejecutar `load_master_table_to_db.py` manualmente

### 2. **Robusto y Opcional**
- ✅ No falla si el CSV no existe
- ✅ Solo carga si el archivo está presente
- ✅ Logs claros sobre el estado

### 3. **Trazabilidad**
- ✅ Estadísticas registradas en `etl_runs`
- ✅ Parámetro `fact_housing_master_rows` en metadata

### 4. **Reutilizable**
- ✅ Módulo independiente (`src/etl/load_master_table.py`)
- ✅ Puede usarse en otros contextos
- ✅ Script standalone actualizado para usar el módulo

---

## 🔧 Uso Manual (Opcional)

Si necesitas cargar el Master Table manualmente (sin ejecutar todo el pipeline):

```bash
python scripts/load_master_table_to_db.py
```

**Nota**: Este script ahora usa el mismo módulo que el pipeline, garantizando consistencia.

---

## 📝 Logs y Trazabilidad

### Durante la Ejecución

```
INFO - Verificando si existe Master Table para cargar
INFO - Creando esquema de fact_housing_master
INFO - ✓ Esquema de fact_housing_master creado exitosamente
INFO - Leyendo Master Table desde data/processed/barcelona_housing_master_table.csv
INFO - Cargando 2,742 registros a fact_housing_master
INFO - ✓ 2,742 registros cargados exitosamente en fact_housing_master
INFO - ✓ Master Table cargado: 2,742 registros en fact_housing_master
```

### Si el CSV no existe

```
DEBUG - Master Table CSV no encontrado en data/processed/barcelona_housing_master_table.csv. 
        Omitiendo carga de fact_housing_master.
DEBUG - Master Table CSV no encontrado. Ejecute scripts/merge_datasets.py para generarlo.
```

### En etl_runs

```json
{
  "fact_housing_master_rows": 2742,
  "fact_precios_rows": 6358,
  "fact_renta_rows": 657,
  ...
}
```

---

## ⚠️ Consideraciones

### 1. **Orden de Dependencias**
- ✅ El Master Table se carga **después** de `dim_barrios`
- ✅ Valida que todos los `barrio_id` existan en `dim_barrios`
- ✅ Filtra automáticamente barrios inválidos

### 2. **Truncado de Tabla**
- ✅ Por defecto, la tabla se trunca antes de cargar (`truncate=True`)
- ✅ Esto asegura que no haya duplicados
- ⚠️ Si necesitas preservar datos existentes, modifica el parámetro

### 3. **Generación del CSV**
- ⚠️ El pipeline **NO genera** el CSV automáticamente
- ⚠️ Debes ejecutar `scripts/merge_datasets.py` primero
- ✅ El pipeline solo **carga** el CSV si existe

---

## 🔄 Flujo Completo Recomendado

### Opción 1: Pipeline Completo (Recomendado)

```bash
# 1. Extraer datos
python scripts/extract_official_prices.py
python scripts/export_socioeconomics_renta.py
# ... otros extractores

# 2. Generar Master Table
python scripts/merge_datasets.py

# 3. Ejecutar pipeline ETL (carga todo incluyendo Master Table)
python scripts/process_and_load.py
```

### Opción 2: Solo Master Table

```bash
# Si solo quieres actualizar el Master Table
python scripts/merge_datasets.py
python scripts/load_master_table_to_db.py
```

---

## 🧪 Testing

Para verificar que la automatización funciona:

```bash
# 1. Asegurar que el CSV existe
ls data/processed/barcelona_housing_master_table.csv

# 2. Ejecutar pipeline
python scripts/process_and_load.py

# 3. Verificar carga
python scripts/verify_database_state.py | grep fact_housing_master
```

---

## 📚 Referencias

- **Módulo**: `src/etl/load_master_table.py`
- **Pipeline**: `src/etl/pipeline.py`
- **Script standalone**: `scripts/load_master_table_to_db.py`
- **Generación Master Table**: `scripts/merge_datasets.py`
- **Verificación**: `scripts/verify_database_state.py`

---

## 📅 Historial

- **2025-12-14**: Automatización implementada
  - Módulo reutilizable creado
  - Integración en pipeline ETL
  - Script standalone actualizado
  - Documentación creada

