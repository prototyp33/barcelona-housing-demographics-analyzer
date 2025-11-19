# Notas sobre Extracción de Demografía Ampliada

## 📋 Resumen

El script `extract_priority_sources.py` ha sido actualizado para buscar específicamente los datasets del **Padrón Municipal** publicados por Open Data BCN, que ya están agregados por barrio. Esto evita la complejidad de mapear desde secciones censales (INE) a los 73 barrios.

## 🎯 Datasets Específicos Buscados

### 1. Población por Edad Quinquenal
- **Búsqueda**: "Població de Barcelona per edat quinquennal i sexe per barris"
- **Palabras clave**: `edat quinquennal`, `edad quinquenal`, `poblacio per edat`, `padro edat`
- **Valor**: Datos en grupos de 5 años (0-4, 5-9, ... 85+), mucho más útil que edad media

### 2. Población por Nacionalidad
- **Búsqueda**: "Població de Barcelona per nacionalitat i sexe per barris"
- **Palabras clave**: `nacionalitat`, `nacionalidad`, `poblacio per nacionalitat`
- **Valor**: Desglose por países o grandes grupos (UE, Resto de Europa, América del Sur, etc.)

### 3. Composición de Hogares
- **Búsqueda**: "Llars per tipus i nombre de membres per barris"
- **Palabras clave**: `llars per tipus`, `hogares por tipo`, `llars per nombre de membres`
- **Valor**: Hogares unipersonales, parejas con/sin hijos, etc. por barrio

## ⚠️ Problema Crítico: Normalización de Nombres de Barrios

### El Reto

Los datasets de Open Data BCN pueden tener nombres de barrios con variaciones que impiden hacer JOIN directo con `dim_barrios`:

**Ejemplos de variaciones:**
- `"la Maternitat i Sant Ramon"` vs `"La Maternitat i Sant Ramon"` (mayúsculas)
- `"el Camp d'en Grassot i Gràcia Nova"` vs `"El Camp d'en Grassot i Gràcia Nova"`
- `"Sant Antoni"` vs `"sant antoni"` (case)
- Diferencias en acentos, espacios, guiones

### Solución Implementada

El script ya usa la función `_normalize_text()` de `data_processing.py` que:

1. **Convierte a minúsculas**
2. **Normaliza Unicode** (NFKD)
3. **Elimina acentos y caracteres especiales**
4. **Elimina espacios extra**

**Ejemplo:**
```python
from src.data_processing import _normalize_text

# Ambos se normalizan a lo mismo:
_normalize_text("La Maternitat i Sant Ramon")  # → "lamaternitatisantramon"
_normalize_text("la Maternitat i Sant Ramon")  # → "lamaternitatisantramon"
```

### ⚠️ Acción Requerida Después de la Extracción

**IMPORTANTE**: Después de extraer los datos, necesitarás:

1. **Validar el mapeo**: Verificar que todos los barrios se mapean correctamente
2. **Revisar registros sin mapear**: Si hay barrios que no se mapean, agregar alias en `BARRIO_ALIAS_OVERRIDES` (ver `TERRITORY_MAPPING_OVERRIDES.md`)
3. **Procesar en `data_processing.py`**: Usar `_map_territorio_to_barrio_id()` para hacer el JOIN

**Ejemplo de procesamiento:**
```python
from src.data_processing import _map_territorio_to_barrio_id

# En tu función de procesamiento:
df['barrio_id'] = df.apply(
    lambda row: _map_territorio_to_barrio_id(
        row['Nom_Barri'],  # o la columna que tenga el nombre
        'Barri',
        dim_barrios
    ),
    axis=1
)

# Verificar registros sin mapear
unmatched = df[df['barrio_id'].isna()]
if not unmatched.empty:
    logger.warning(f"{len(unmatched)} registros sin mapear")
    logger.warning(f"Barrios: {unmatched['Nom_Barri'].unique()}")
```

## 🔍 Validación de Columnas

El script valida automáticamente:

1. **Columnas de barrio**: Busca `barrio`, `barri`, `Nom_Barri`, `Codi_Barri`, `barrio_id`, `Barris`
2. **Columnas específicas por tipo**:
   - **Edad quinquenal**: Columnas con `edat`, `edad`, `quinquennal`
   - **Nacionalidad**: Columnas con `nacionalitat`, `nacionalidad`, `pais`
   - **Hogares**: Columnas con `llar`, `hogar`, `membre`, `miembro`

Si no encuentra las columnas esperadas, muestra una advertencia pero continúa.

## 📊 Estructura de Resultados

El script genera:

```
results = {
    "demografia_edad_quinquenal": DataFrame,
    "demografia_nacionalidad": DataFrame,
    "demografia_hogares": DataFrame,
    "geojson": GeoJSON dict,
    "renta": DataFrame,
}

metadata = {
    "demografia_edad_quinquenal": {
        "success": bool,
        "dataset_id": str,
        "records": int,
        "columns": list,
        "barrio_column": str,  # Si se encontró
        "warning": str,  # Si hay problemas
        ...
    },
    ...
}
```

## 🚀 Uso

```bash
# Extraer todas las fuentes
python scripts/extract_priority_sources.py

# Solo demografía ampliada
python scripts/extract_priority_sources.py --sources demografia

# Solo un tipo específico (requiere modificar el código)
python scripts/extract_priority_sources.py --sources demografia --year-start 2015 --year-end 2024
```

## 📝 Próximos Pasos

1. **Ejecutar el script** y revisar los datasets encontrados
2. **Validar la estructura** de los DataFrames extraídos
3. **Crear funciones de procesamiento** en `data_processing.py` para:
   - Mapear nombres de barrios a `barrio_id`
   - Transformar datos de edad quinquenal a grupos de edad deseados
   - Agregar datos de nacionalidad a `fact_demografia`
   - Agregar datos de hogares a `fact_demografia` o crear nueva tabla `fact_hogares`
4. **Integrar en el ETL pipeline** (`src/etl/pipeline.py`)

## 🔗 Referencias

- `src/data_processing.py::_normalize_text()` - Función de normalización
- `src/data_processing.py::_map_territorio_to_barrio_id()` - Función de mapeo
- `docs/TERRITORY_MAPPING_OVERRIDES.md` - Alias manuales para barrios
- `docs/QUÉ_DATOS_NECESITAMOS.md` - Requisitos específicos de datos

---

*Última actualización: 2025-11-13*

