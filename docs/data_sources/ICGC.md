## Fuente: ICGC - Seguridad y Criminalidad

### Descripción general

El **Institut Català de Gestió Criminal (ICGC)** es el organismo responsable de la gestión y análisis de datos de criminalidad en Cataluña. Los datos de criminalidad son fundamentales para entender la seguridad pública y su relación con el mercado de vivienda.

En este proyecto, estos datos se utilizan para construir la tabla de hechos `fact_seguridad`, que mide la incidencia delictiva por barrio (`barrio_id`), año (`anio`) y trimestre (`trimestre`).

**URL del visor**: http://www.icgc.cat/es/Herramientas-y-visores/Visores/Mapa-delincuencial

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (73 barrios objetivo, mínimo 50 aceptable).
- **Frecuencia temporal**: Trimestral (objetivo: 2015-2024, mínimo: 2020-2024).
- **Variables clave**:
  - Delitos contra el patrimonio (robos, hurtos, estafas)
  - Delitos contra la seguridad personal (agresiones, violencia, lesiones)
  - Tasa de criminalidad por 1000 habitantes
  - Percepción de inseguridad (si está disponible)

### Fuentes de datos

El ICGC no proporciona una API pública directa, por lo que este módulo implementa múltiples estrategias de obtención de datos:

#### 1. Open Data BCN (Preferido)

Si hay datasets de seguridad/criminalidad disponibles en Open Data BCN, el extractor los buscará automáticamente usando el `OpenDataBCNExtractor`.

**Datasets potenciales**:
- `seguretat-ciutadana`
- `delictes`
- `criminalitat`
- `seguretat`

#### 2. Scraping del visor ICGC

El visor web del ICGC (Mapa Delincuencial) puede ser scrapeado, aunque requiere análisis de la estructura HTML/JavaScript y posiblemente herramientas como Selenium o Playwright.

**Estado**: Placeholder implementado, requiere desarrollo adicional.

#### 3. Archivos CSV manuales (Fallback)

Si no hay acceso directo a datos, se pueden preparar archivos CSV manualmente y colocarlos en `data/raw/icgc/`.

**Formato esperado**:
```csv
barrio,anio,trimestre,robos,hurtos,agresiones,percepcion_inseguridad
Barrio 1,2024,1,10,15,3,5.2
Barrio 2,2024,1,5,10,2,4.8
```

**Patrones de nombre de archivo aceptados**:
- `icgc_criminalidad_*.csv`
- `icgc_delitos_*.csv`
- `seguridad_*.csv`

### Esquema `fact_seguridad`

Columnas principales:

- `barrio_id` (INTEGER, FK a `dim_barrios.barrio_id`)
- `anio` (INTEGER)
- `trimestre` (INTEGER, 1-4)
- `delitos_patrimonio` (INTEGER): Suma de robos, hurtos, estafas
- `delitos_seguridad_personal` (INTEGER): Suma de agresiones, violencia, lesiones
- `tasa_criminalidad_1000hab` (REAL): `(total_delitos / poblacion_total) * 1000`
- `percepcion_inseguridad` (REAL, opcional): Escala 0-10

### Procesamiento de datos

#### 1. Extracción

El extractor `ICGCExtractor` intenta múltiples métodos en orden:

```python
from src.extraction.icgc_extractor import ICGCExtractor

extractor = ICGCExtractor(output_dir=Path("data/raw/icgc"))
df, metadata = extractor.extract_criminalidad_barrio(anio_inicio=2020, anio_fin=2024)
```

#### 2. Mapeo de barrios

Los datos se mapean a `barrio_id` usando:
- Nombre de barrio normalizado (si está disponible)
- `codi_barri` (si está disponible)

#### 3. Clasificación de delitos

El procesador identifica automáticamente columnas de delitos usando palabras clave:

- **Delitos contra el patrimonio**: "robo", "hurto", "estafa", "patrimonio", "sustraccion"
- **Delitos contra la seguridad personal**: "agresion", "violencia", "lesion", "personal", "fisica"

#### 4. Cálculo de tasas

La tasa de criminalidad por 1000 habitantes se calcula usando datos de población desde `fact_demografia`:

```python
tasa_criminalidad_1000hab = (total_delitos / poblacion_total) * 1000
```

#### 5. Agregación temporal

Los datos se agregan por `(barrio_id, anio, trimestre)`:
- `delitos_patrimonio`: `SUM(robos + hurtos + estafas)`
- `delitos_seguridad_personal`: `SUM(agresiones + violencia + lesiones)`
- `tasa_criminalidad_1000hab`: Calculada después de la agregación
- `percepcion_inseguridad`: `AVG(percepcion)` si está disponible

### Validaciones clave

El script `scripts/validate_seguridad.py` aplica las siguientes comprobaciones:

- **Cobertura de barrios**: `COUNT(DISTINCT barrio_id) >= 50` (≥68% de los 73 barrios)
- **Cobertura temporal mínima**: Presencia de años 2020 y 2024
- **Completitud**: ≥70% de registros con `delitos_patrimonio > 0` o `delitos_seguridad_personal > 0`

Si alguna de estas condiciones no se cumple, el script devuelve un código de salida no cero.

### Limitaciones conocidas

1. **Acceso a datos**: El ICGC no proporciona una API pública directa. Los datos pueden requerir:
   - Scraping del visor web (complejidad media-alta)
   - Solicitud formal a Mossos d'Esquadra / Ajuntament
   - Preparación manual de archivos CSV desde informes públicos

2. **Granularidad**: Los datos pueden estar disponibles solo a nivel distrito en lugar de barrio, requiriendo interpolación o asignación proporcional.

3. **Cobertura temporal**: Los datos históricos pueden ser limitados. El objetivo es 2015-2024, pero el mínimo aceptable es 2020-2024.

4. **Clasificación de delitos**: La clasificación automática por palabras clave puede no capturar todos los tipos de delitos. Se recomienda revisar y ajustar según los datos reales disponibles.

### Preparación de datos manuales

Si necesitas preparar archivos CSV manualmente:

1. Crear directorio: `data/raw/icgc/`
2. Preparar CSV con columnas mínimas:
   - `barrio` o `barrio_id` o `codi_barri`
   - `anio` o `any`
   - `trimestre` (opcional, por defecto 1)
   - Columnas de delitos (ej: `robos`, `hurtos`, `agresiones`)
3. Nombrar el archivo con patrón: `icgc_criminalidad_*.csv`
4. Ejecutar el ETL: `python -m src.etl.pipeline`

### Referencias

- **ICGC**: http://www.icgc.cat/
- **Mapa Delincuencial**: http://www.icgc.cat/es/Herramientas-y-visores/Visores/Mapa-delincuencial
- **Mossos d'Esquadra**: https://mossos.gencat.cat/
- **Ajuntament Barcelona - Seguretat**: https://ajuntament.barcelona.cat/seguretat/

