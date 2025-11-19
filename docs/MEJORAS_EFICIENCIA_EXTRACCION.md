# Mejoras de Eficiencia y Eficacia para Extractores

## 📊 Información Conocida que Puede Mejorar el Script

### 1. IDs de Datasets Confirmados y Funcionales

#### Datasets de Demografía (Open Data BCN)
```python
KNOWN_DATASET_IDS = {
    # Población por sexo (YA CONFIRMADO - funciona)
    "poblacion_sexo": "pad_mdbas_sexe",
    
    # Población por edad (VERIFICAR - puede no existir)
    "poblacion_edad": "est-padro-edat-any-a-any",  # ⚠️ Devuelve 404 según código existente
    
    # IDs a probar en orden de prioridad:
    "poblacion_general": "poblacio-per-barris",
    "padro_municipal": "padro-municipal",
}
```

**Beneficio**: Probar primero estos IDs antes de buscar por palabras clave ahorra tiempo y peticiones API.

### 2. Estructuras de Columnas Conocidas

#### Patrones de Nombres de Columnas en Open Data BCN

**Columnas de Barrio (en orden de probabilidad):**
```python
BARRIO_COLUMN_PATTERNS = [
    "Nom_Barri",      # Más común
    "Codi_Barri",     # Código numérico
    "Barris",         # Nombre alternativo
    "barrio",         # Español
    "barri",          # Catalán
    "barrio_id",      # Menos común
]
```

**Columnas de Año:**
```python
YEAR_COLUMN_PATTERNS = [
    "Any",            # Catalán
    "Año",            # Español
    "year",           # Inglés
    "anio",           # Sin tilde
]
```

**Columnas de Demografía:**
```python
DEMOGRAPHY_COLUMN_PATTERNS = {
    "edad_quinquenal": [
        "Edat", "Edad", "Grups d'edat", "Grupos de edad",
        "0-4", "5-9", "10-14", ...  # Rangos directos
    ],
    "nacionalidad": [
        "Nacionalitat", "Nacionalidad", "Pais", "País",
        "Espanya", "Estranger", "UE", "Resto Europa"
    ],
    "hogares": [
        "Llars", "Hogares", "Tipus de llar", "Tipo de hogar",
        "1 persona", "2 persones", "3 persones", ...
    ],
}
```

**Beneficio**: Validación más rápida y precisa de columnas sin inspeccionar todo el DataFrame.

### 3. Cobertura Temporal Conocida

```python
KNOWN_TEMPORAL_COVERAGE = {
    "pad_mdbas_sexe": {
        "years_available": [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023],
        "update_frequency": "anual",
        "lag_months": 3,  # Datos publicados ~3 meses después del año de referencia
    },
    # Agregar más según se descubran
}
```

**Beneficio**: Evitar intentar descargar años que no existen.

### 4. Formatos de Recursos Disponibles

```python
PREFERRED_RESOURCE_FORMATS = {
    "demografia": ["CSV", "csv"],  # CSV es más común y fácil de procesar
    "geojson": ["GeoJSON", "geojson", "JSON", "json"],
    "renta": ["CSV", "csv", "Excel", "xlsx"],
}
```

**Beneficio**: Priorizar formatos que sabemos que funcionan.

### 5. Rate Limits y Mejores Prácticas

```python
RATE_LIMITS = {
    "opendatabcn": {
        "requests_per_minute": 30,
        "requests_per_hour": 1000,
        "recommended_delay": 1.5,  # segundos entre peticiones
    },
    "portaldades": {
        "requests_per_minute": 20,
        "recommended_delay": 2.0,
    },
}
```

**Beneficio**: Optimizar delays sin sobrecargar servidores.

### 6. Cacheo de Resultados de Búsqueda

**Estrategia**: Guardar resultados de búsqueda en archivo JSON para reutilizar:

```python
CACHE_FILE = "data/raw/.dataset_search_cache.json"

# Estructura del cache:
{
    "last_updated": "2025-11-13T10:00:00",
    "searches": {
        "edat quinquennal": {
            "datasets": ["dataset_id_1", "dataset_id_2"],
            "timestamp": "2025-11-13T10:00:00"
        },
        ...
    },
    "dataset_info": {
        "dataset_id_1": {
            "title": "...",
            "resources": [...],
            "timestamp": "2025-11-13T10:00:00"
        }
    }
}
```

**Beneficio**: Evitar búsquedas repetidas en la misma sesión o entre ejecuciones cercanas.

### 7. Validación Temprana de Datos

**Checks rápidos antes de procesar todo:**

```python
QUICK_VALIDATION_CHECKS = {
    "min_rows": 10,  # Mínimo de filas esperadas
    "required_columns": ["barrio", "año"],  # Columnas críticas
    "expected_year_range": (2015, 2024),  # Rango esperado
}
```

**Beneficio**: Detectar problemas antes de procesar datasets grandes.

### 8. Mapeo de Nombres de Barrios Conocidos

**Variaciones comunes detectadas:**

```python
BARRIO_NAME_VARIATIONS = {
    "lamaternitatisantramon": [
        "La Maternitat i Sant Ramon",
        "la Maternitat i Sant Ramon",
        "Maternitat i Sant Ramon",
    ],
    "elcampdengrassotigracianova": [
        "el Camp d'en Grassot i Gràcia Nova",
        "El Camp d'en Grassot i Gràcia Nova",
        "Camp d'en Grassot i Gràcia Nova",
    ],
    # Agregar más según se descubran
}
```

**Beneficio**: Mapeo más rápido sin necesidad de fuzzy matching.

### 9. Información sobre Recursos por Dataset

**Estructura típica de recursos en Open Data BCN:**

```python
TYPICAL_RESOURCE_STRUCTURE = {
    "pad_mdbas_sexe": {
        "resources": [
            {
                "format": "CSV",
                "name_pattern": "pad_mdbas_sexe_{YEAR}.csv",
                "url_pattern": "https://opendata-ajuntament.barcelona.cat/data/dataset/.../{YEAR}.csv"
            }
        ],
        "year_extraction": "from_filename",  # o "from_column"
    }
}
```

**Beneficio**: Descargar recursos específicos sin listar todos.

### 10. Errores Comunes y Soluciones

```python
COMMON_ERRORS_AND_FIXES = {
    "404": {
        "cause": "Dataset ID incorrecto o dataset eliminado",
        "action": "Intentar búsqueda por palabras clave",
    },
    "empty_dataframe": {
        "cause": "Filtros de año muy restrictivos o datos no disponibles",
        "action": "Verificar años disponibles en metadata",
    },
    "encoding_error": {
        "cause": "Encoding incorrecto (UTF-8 vs Latin-1)",
        "action": "Probar múltiples encodings automáticamente",
    },
}
```

**Beneficio**: Manejo automático de errores comunes.

## 🚀 Implementación Recomendada

### Prioridad Alta

1. **IDs de datasets confirmados**: Agregar lista prioritaria
2. **Patrones de columnas**: Validación más inteligente
3. **Cacheo de búsquedas**: Evitar búsquedas repetidas

### Prioridad Media

4. **Cobertura temporal conocida**: Validar años antes de descargar
5. **Mapeo de nombres**: Agregar variaciones conocidas
6. **Validación temprana**: Checks rápidos antes de procesar

### Prioridad Baja

7. **Rate limits optimizados**: Ajustar delays según fuente
8. **Estructura de recursos**: Descargar recursos específicos
9. **Manejo de errores**: Auto-recuperación de errores comunes

## 📝 Notas

- Esta información debe actualizarse conforme se descubren nuevos datasets
- Mantener un archivo de configuración JSON con esta información
- Validar periódicamente que los IDs siguen funcionando

---

*Última actualización: 2025-11-13*

