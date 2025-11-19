# Guía de Extracción de Nuevas Fuentes de Datos

Esta guía detalla los aspectos críticos a considerar al integrar nuevas fuentes de datos en el proyecto.

## 1. Consideraciones Históricas y Temporales

### Rango Temporal
- **Años disponibles**: Verificar desde qué año hay datos y hasta cuándo se actualiza
- **Frecuencia de actualización**: Diaria, mensual, trimestral, anual
- **Retroactividad**: ¿Se pueden obtener datos históricos o solo desde la fecha de publicación?
- **Lag de publicación**: ¿Cuánto tiempo pasa entre el periodo de referencia y la publicación?

**Ejemplo**:
```python
# En el extractor, documentar:
# - Años disponibles: 2015-2024
# - Actualización: Mensual (publicación con 2 meses de lag)
# - Datos históricos: Disponibles desde 2010 en archivos legacy
```

### Consistencia Temporal
- **Cambios de metodología**: ¿Hubo cambios en cómo se miden los datos?
- **Brechas temporales**: Identificar años o periodos sin datos
- **Cambios de formato**: ¿El formato cambió en algún momento histórico?

**Checklist**:
- [ ] Documentar rango completo de años disponibles
- [ ] Identificar y documentar brechas temporales
- [ ] Notar cambios metodológicos en metadatos
- [ ] Validar que los años extraídos coinciden con el rango solicitado

---

## 2. Estructura de Datos

### Granularidad Geográfica
- **Nivel disponible**: Barrio, distrito, municipio, sección censal
- **Cobertura**: ¿Todos los barrios o solo algunos?
- **Identificadores**: ¿Qué códigos usan? (Codi_Barri, códigos INE, nombres)

**Ejemplo de mapeo necesario**:
```python
# Si la fuente usa códigos diferentes:
TERRITORY_MAPPING = {
    "08019": "Barcelona",  # Código INE
    "barri_01": 1,  # Código interno vs barrio_id
}
```

### Granularidad Temporal
- **Periodo base**: Año, trimestre, mes, día
- **Agregación**: ¿Necesitamos agregar o desagregar?
- **Periodos especiales**: ¿Hay datos por trimestre que debemos consolidar a año?

### Estructura de Columnas
- **Nombres de columnas**: ¿Son consistentes? ¿En qué idioma?
- **Tipos de datos**: Numéricos, texto, fechas, categorías
- **Valores especiales**: ¿Cómo representan nulos? ("N.D.", "No consta", "", NULL)
- **Codificaciones**: ¿Usan códigos numéricos que requieren diccionarios?

**Checklist**:
- [ ] Documentar todas las columnas disponibles
- [ ] Identificar columnas clave para el análisis
- [ ] Mapear valores especiales a NULL/NA
- [ ] Crear diccionarios de códigos si aplica
- [ ] Validar tipos de datos esperados

---

## 3. Calidad y Validación de Datos

### Valores Nulos y Faltantes
- **Patrones de nulos**: ¿Son aleatorios o sistemáticos?
- **Razones documentadas**: ¿La fuente explica por qué faltan datos?
- **Estrategia de manejo**: ¿Imputar, excluir, o marcar explícitamente?

**Ejemplo de validación**:
```python
def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Valida calidad de datos extraídos."""
    return {
        "total_rows": len(df),
        "null_percentage": df.isnull().sum() / len(df) * 100,
        "duplicate_rows": df.duplicated().sum(),
        "outliers": detect_outliers(df),
    }
```

### Valores Atípicos (Outliers)
- **Rangos esperados**: Definir límites razonables por métrica
- **Detección**: Usar percentiles, IQR, o reglas de dominio
- **Documentación**: Registrar outliers detectados para revisión

**Ejemplo**:
```python
# Para precios de vivienda:
PRECIO_M2_MIN = 100  # €/m² mínimo razonable
PRECIO_M2_MAX = 30000  # €/m² máximo razonable

outliers = df[
    (df["precio_m2"] < PRECIO_M2_MIN) | 
    (df["precio_m2"] > PRECIO_M2_MAX)
]
```

### Consistencia Interna
- **Sumas y totales**: ¿Los agregados coinciden con los desgloses?
- **Relaciones lógicas**: ¿Población = hombres + mujeres? ¿Hogares <= Población?
- **Tendencias temporales**: ¿Los cambios año a año son plausibles?

**Checklist**:
- [ ] Validar que sumas parciales = totales
- [ ] Verificar relaciones lógicas entre campos
- [ ] Detectar saltos anómalos en series temporales
- [ ] Comparar con datos de otras fuentes cuando sea posible

---

## 4. Aspectos Técnicos de Extracción

### APIs y Endpoints
- **Autenticación**: ¿Requiere API key, OAuth, tokens?
- **Rate limits**: ¿Cuántas peticiones por minuto/hora?
- **Paginación**: ¿Cómo manejar grandes volúmenes?
- **Formato de respuesta**: JSON, XML, CSV, otros

**Ejemplo de manejo de rate limits**:
```python
import time
from functools import wraps

def rate_limit(max_calls=60, period=60):
    """Decorador para limitar llamadas a API."""
    def decorator(func):
        calls = []
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [c for c in calls if c > now - period]
            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                time.sleep(sleep_time)
            calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Archivos Estáticos
- **Ubicación**: URLs fijas, FTP, repositorios
- **Nomenclatura**: ¿Siguen un patrón? (ej: `datos_YYYY.csv`)
- **Versionado**: ¿Cómo identificar la versión más reciente?
- **Encoding**: UTF-8, Latin-1, ISO-8859-1, otros

### Web Scraping
- **Términos de uso**: ¿Permite scraping? ¿Requiere robots.txt?
- **Estructura HTML**: ¿Es estable o cambia frecuentemente?
- **JavaScript**: ¿Requiere renderizado dinámico (Selenium/Playwright)?
- **Ética**: Respetar rate limits, no sobrecargar servidores

**Checklist**:
- [ ] Revisar términos de uso y robots.txt
- [ ] Implementar manejo de errores y reintentos
- [ ] Guardar raw data antes de procesar
- [ ] Registrar metadatos de extracción (fecha, versión, parámetros)

---

## 5. Integración con Esquema Existente

### Mapeo a Tablas Existentes
- **fact_demografia**: ¿Qué campos nuevos podemos agregar?
- **fact_precios**: ¿Cómo se integran con los existentes?
- **dim_barrios**: ¿Necesitamos nuevas dimensiones?

**Ejemplo de decisión**:
```python
# Si la fuente tiene datos que no encajan en tablas existentes:
# Opción 1: Crear nueva tabla fact_*
# Opción 2: Agregar columnas a tabla existente
# Opción 3: Crear tabla de staging y luego merge

# Para renta familiar:
# - No encaja en fact_demografia (no es demografía)
# - No encaja en fact_precios (no es precio)
# → Crear fact_socioeconomia
```

### Identificadores y Claves Foráneas
- **barrio_id**: ¿Cómo mapeamos territorios de la nueva fuente?
- **Consistencia**: ¿Usar el mismo sistema de normalización?
- **Casos especiales**: ¿Hay territorios que no existen en dim_barrios?

**Reutilizar funciones existentes**:
```python
from src.data_processing import _normalize_text, _map_territorio_to_barrio_id

# Usar normalización consistente
territorio_norm = _normalize_text(nombre_territorio)
barrio_id = _map_territorio_to_barrio_id(nombre, tipo, dim_barrios)
```

### Metadatos y Trazabilidad
- **source**: Identificador único de la fuente
- **dataset_id**: ID específico del dataset dentro de la fuente
- **etl_loaded_at**: Timestamp de carga
- **coverage**: Años y territorios cubiertos

**Checklist**:
- [ ] Definir valores de `source` y `dataset_id` consistentes
- [ ] Asegurar que todos los registros tienen `barrio_id` válido
- [ ] Documentar transformaciones aplicadas
- [ ] Guardar metadatos de extracción en archivo JSON

---

## 6. Procesamiento y Transformación

### Normalización de Datos
- **Unidades**: ¿Están en las unidades correctas? (€ vs miles de €, m² vs km²)
- **Escalas**: ¿Necesitamos convertir? (ej: porcentajes de 0-100 vs 0-1)
- **Formato de fechas**: ¿Consistente con el resto del sistema?

**Ejemplo**:
```python
def normalize_precio(valor: str) -> float:
    """Normaliza precios que pueden venir en diferentes formatos."""
    if pd.isna(valor):
        return pd.NA
    # Remover separadores de miles
    valor = str(valor).replace(".", "").replace(",", ".")
    return float(valor)
```

### Agregación y Desagregación
- **Nivel de detalle**: ¿La fuente tiene más o menos detalle del necesario?
- **Agregación temporal**: ¿Agrupar por año si viene mensual?
- **Agregación geográfica**: ¿Distribuir datos de distrito a barrios?

**Ejemplo de distribución**:
```python
# Si tenemos datos a nivel distrito pero necesitamos barrios:
def distribute_by_population(
    distrito_data: float,
    barrios_in_distrito: List[int],
    population_by_barrio: Dict[int, float]
) -> Dict[int, float]:
    """Distribuye valor de distrito proporcionalmente a población."""
    total_pop = sum(population_by_barrio[b] for b in barrios_in_distrito)
    return {
        barrio_id: distrito_data * (population_by_barrio[barrio_id] / total_pop)
        for barrio_id in barrios_in_distrito
    }
```

### Deduplicación
- **Claves únicas**: ¿Qué combinación identifica un registro único?
- **Estrategia**: ¿Mantener todos, priorizar por fuente, o promediar?
- **Conflicto de fuentes**: ¿Qué hacer si dos fuentes tienen valores diferentes?

**Ejemplo**:
```python
# Para fact_precios, ya tenemos lógica de deduplicación:
# - Clave: (barrio_id, anio, trimestre, dataset_id, source)
# - Estrategia: Mantener todos (preservar diversidad de indicadores)
```

---

## 7. Testing y Validación

### Datos de Prueba
- **Subconjunto pequeño**: Probar con 1-2 años primero
- **Casos edge**: Incluir barrios con nombres especiales, años límite
- **Validación manual**: Comparar resultados con fuente original

**Checklist de testing**:
- [ ] Extraer muestra pequeña (1 año, 5 barrios)
- [ ] Validar mapeo de territorios
- [ ] Verificar que no hay pérdida de datos
- [ ] Comparar estadísticas con fuente original
- [ ] Probar casos edge (nulos, outliers, nombres especiales)

### Validación Post-ETL
- **Conteos**: ¿El número de registros es razonable?
- **Rangos**: ¿Los valores están en rangos esperados?
- **Completitud**: ¿Qué porcentaje de barrios/años tiene datos?
- **Consistencia**: ¿Los datos se relacionan correctamente con otras tablas?

**Ejemplo de validación automática**:
```python
def validate_etl_output(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Valida resultados del ETL."""
    results = {}
    
    # Validar fact_demografia
    df_demo = pd.read_sql("SELECT * FROM fact_demografia", conn)
    results["demografia"] = {
        "total_rows": len(df_demo),
        "null_hogares": df_demo["hogares_totales"].isna().sum(),
        "hogares_range": (df_demo["hogares_totales"].min(), df_demo["hogares_totales"].max()),
    }
    
    # Validar integridad referencial
    orphaned = pd.read_sql("""
        SELECT f.barrio_id 
        FROM fact_demografia f
        LEFT JOIN dim_barrios d ON f.barrio_id = d.barrio_id
        WHERE d.barrio_id IS NULL
    """, conn)
    results["orphaned_records"] = len(orphaned)
    
    return results
```

---

## 8. Documentación

### Metadatos de Extracción
Guardar en `data/raw/extraction_metadata_YYYYMMDD_HHMMSS.json`:

```json
{
    "extraction_date": "2025-11-13T15:00:00",
    "source": "nueva_fuente",
    "dataset_id": "dataset_especifico",
    "year_range": {"start": 2015, "end": 2024},
    "parameters": {
        "api_key_used": false,
        "rate_limit_applied": true
    },
    "coverage": {
        "total_records": 1000,
        "years_covered": [2015, 2016, ..., 2024],
        "barrios_covered": 73,
        "missing_years": [],
        "missing_barrios": []
    },
    "data_quality": {
        "null_percentage": 2.5,
        "outliers_detected": 15,
        "validation_passed": true
    }
}
```

### Actualizar Documentación del Proyecto
- **DATA_STRUCTURE.md**: Agregar nuevas tablas/campos
- **PROJECT_STATUS.md**: Actualizar estado de fuentes
- **FUENTES_PENDIENTES.md**: Marcar como completado
- **README.md**: Si la fuente es importante, mencionarla

---

## 9. Checklist Completo de Integración

### Fase 1: Investigación
- [ ] Identificar URL/API/endpoint de la fuente
- [ ] Revisar términos de uso y licencia
- [ ] Documentar estructura de datos (columnas, formatos)
- [ ] Verificar rango temporal disponible
- [ ] Identificar granularidad geográfica y temporal

### Fase 2: Desarrollo
- [ ] Crear clase extractor siguiendo patrón existente
- [ ] Implementar manejo de errores y reintentos
- [ ] Implementar rate limiting si aplica
- [ ] Crear funciones de normalización/transformación
- [ ] Implementar mapeo de territorios a barrio_id
- [ ] Agregar validaciones de calidad

### Fase 3: Testing
- [ ] Probar extracción con muestra pequeña
- [ ] Validar mapeo de territorios
- [ ] Verificar calidad de datos extraídos
- [ ] Comparar con fuente original
- [ ] Probar casos edge

### Fase 4: Integración
- [ ] Agregar a `extract_all_sources()` si aplica
- [ ] Crear función de preparación en `data_processing.py`
- [ ] Integrar en `run_etl()` del pipeline
- [ ] Actualizar esquema de base de datos si necesario
- [ ] Probar ETL completo

### Fase 5: Documentación
- [ ] Guardar metadatos de extracción
- [ ] Actualizar `DATA_STRUCTURE.md`
- [ ] Actualizar `PROJECT_STATUS.md`
- [ ] Marcar en `FUENTES_PENDIENTES.md`
- [ ] Documentar decisiones de diseño (por qué se hizo así)

---

## 10. Ejemplos de Patrones Comunes

### Patrón 1: API REST con Autenticación
```python
import requests
from typing import Dict, Any

class APIFuenteExtractor:
    def __init__(self, api_key: str, output_dir: Path):
        self.api_key = api_key
        self.output_dir = output_dir
        self.base_url = "https://api.ejemplo.com"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def extract_data(self, year_start: int, year_end: int):
        all_data = []
        for year in range(year_start, year_end + 1):
            response = self.session.get(f"{self.base_url}/data/{year}")
            response.raise_for_status()
            all_data.append(response.json())
        
        df = pd.DataFrame(all_data)
        # Guardar y retornar
        return df, metadata
```

### Patrón 2: Archivos CSV con Nomenclatura
```python
class CSVFuenteExtractor:
    def __init__(self, base_url: str, output_dir: Path):
        self.base_url = base_url
        self.output_dir = output_dir
    
    def extract_data(self, year_start: int, year_end: int):
        dfs = []
        for year in range(year_start, year_end + 1):
            url = f"{self.base_url}/datos_{year}.csv"
            df = pd.read_csv(url, encoding='latin-1')
            df['anio'] = year
            dfs.append(df)
        
        combined = pd.concat(dfs, ignore_index=True)
        return combined, metadata
```

### Patrón 3: Web Scraping con Selenium
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

class ScrapingFuenteExtractor:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
    
    def extract_data(self, year_start: int, year_end: int):
        driver = webdriver.Chrome()
        try:
            # Navegar y extraer datos
            data = []
            for year in range(year_start, year_end + 1):
                driver.get(f"https://ejemplo.com/datos/{year}")
                # Extraer datos de la página
                rows = driver.find_elements(By.CSS_SELECTOR, ".data-row")
                for row in rows:
                    data.append(parse_row(row))
            
            df = pd.DataFrame(data)
            return df, metadata
        finally:
            driver.quit()
```

---

## 11. Consideraciones Especiales por Tipo de Fuente

### Datos Oficiales (INE, Ajuntament)
- **Ventaja**: Alta calidad, bien documentados
- **Desafío**: Pueden tener formatos complejos, cambios de metodología
- **Acción**: Revisar documentación metodológica, validar contra otras fuentes oficiales

### APIs de Terceros (Idealista, etc.)
- **Ventaja**: Datos actualizados, bien estructurados
- **Desafío**: Rate limits, posibles cambios en API, costos
- **Acción**: Implementar caching, manejar versiones de API

### Web Scraping
- **Ventaja**: Acceso a datos no disponibles vía API
- **Desafío**: Fragilidad (cambios en HTML), aspectos legales/éticos
- **Acción**: Respetar robots.txt, implementar robustez ante cambios

### Datos Agregados vs Desagregados
- **Agregados**: Más fáciles de procesar pero menos flexibles
- **Desagregados**: Más trabajo pero permiten análisis más detallados
- **Decisión**: Priorizar desagregados si están disponibles

---

*Última actualización: 2025-11-13*

