# Guía de Debugging de Datasets CKAN

Este documento explica cómo usar el script de debugging para investigar y encontrar los IDs correctos de datasets en Open Data Barcelona.

## 📋 Script de Debugging

### Uso Básico

```bash
# Ejecutar el script completo
python scripts/debug_datasets.py

# Guardar salida en archivo
python scripts/debug_datasets.py > debug_output.txt
```

### Qué hace el script

1. **Analiza el dataset de venta** (`habitatges-2na-ma`)
   - Muestra todos los recursos disponibles
   - Detecta años en nombres de archivos
   - Explica por qué solo se descargó cierto año

2. **Busca datasets de alquiler**
   - Busca por palabra clave "lloguer"
   - Muestra IDs encontrados
   - Investiga el primer resultado

3. **Busca datasets de mercado inmobiliario**
   - Busca por "mercat immobiliari"
   - Muestra resultados relevantes

4. **Busca datasets de vivienda y precios**
   - Búsquedas adicionales para encontrar datasets relacionados

## 🔍 Resultados del Debugging

### Dataset de Venta

**ID**: `habitatges-2na-ma` ✅

**Años disponibles**: 2009-2015

**Nota**: Solo se descarga 2015 si el rango solicitado es 2015-2023, porque:
- El dataset solo tiene datos hasta 2015
- El filtrado funciona correctamente

### Dataset de Alquiler

**ID esperado**: `est-mercat-immobiliari-lloguer-mitja-mensual` ❌ (404)

**Estado**: El dataset con este ID no existe en Open Data Barcelona.

**Solución**: El código ahora:
1. Prueba múltiples IDs posibles
2. Busca automáticamente datasets alternativos
3. Usa palabras clave: "lloguer", "alquiler", "rent", "renta"

## 🛠️ Cómo encontrar un dataset

### Método 1: Usar el script de debugging

```bash
python scripts/debug_datasets.py
```

### Método 2: Búsqueda manual en Python

```python
from src.data_extraction import OpenDataBCNExtractor

extractor = OpenDataBCNExtractor()

# Buscar por palabra clave
datasets = extractor.search_datasets_by_keyword("lloguer")
print(datasets)

# Investigar un dataset específico
resources = extractor.get_dataset_resources_ckan("dataset-id")
print(resources)
```

### Método 3: Usar la API CKAN directamente

```python
import requests

CKAN_API = "https://opendata-ajuntament.barcelona.cat/data/api/3/action"

# Buscar
response = requests.get(
    f"{CKAN_API}/package_search",
    params={"q": "lloguer", "rows": 10}
)
data = response.json()

for dataset in data['result']['results']:
    print(f"{dataset['name']}: {dataset['title']}")
```

## 📝 Actualizar IDs en el código

Una vez encontrado el ID correcto:

1. Editar `src/data_extraction.py`
2. Actualizar `DATASETS` en `OpenDataBCNExtractor`:

```python
DATASETS = {
    "housing_alquiler": "nuevo-id-encontrado",  # Actualizar aquí
    # ...
}
```

3. Ejecutar la extracción nuevamente

## ✅ Verificación

Después de actualizar un ID:

```bash
# Probar extracción solo de alquiler
python scripts/extract_data.py \
    --sources opendatabcn \
    --year-start 2015 \
    --year-end 2023 \
    --verbose
```

## 🔗 Recursos

- [Open Data Barcelona](https://opendata-ajuntament.barcelona.cat/)
- [CKAN API Documentation](https://docs.ckan.org/en/2.9/api/)
- [API Usage Guide](./API_usage.md)

