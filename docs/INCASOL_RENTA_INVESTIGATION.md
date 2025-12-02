## Investigación técnica: Incasòl / Dades Obertes Catalunya – Mercado de alquiler

**Objetivo:**  
Identificar y documentar una fuente robusta de datos históricos de alquiler por barrio en Barcelona, adecuada para integrarse en el pipeline ETL del proyecto (serie 2015–202x).

---

### 1. Resumen ejecutivo

- **Fuente operativa real:** Portal de datos abiertos de la Generalitat  
  `Dades Obertes Catalunya` (plataforma Socrata), no la web pública del Incasòl.
- **Tipo de dato:** Mercado de alquiler de vivienda basado en **fianzas depositadas** en Incasòl.
- **Granularidad confirmada:**  
  - Territorio: **barrios de Barcelona** (o, en su defecto, nivel municipio/distrito con posible mapeo).  
  - Tiempo: **trimestre** (t + año).
- **Formato:** JSON y CSV nativos de Socrata (API REST).
- **Ventaja clave:** El histórico suele estar en **un único dataset largo** o en pocos recursos anuales muy limpios → mucho más simple que rascar Excels dispersos.

Conclusión: es viable diseñar un extractor tipo `IncasolSocrataExtractor` que proporcione una serie histórica de alquiler (precio medio, €/m², nº contratos) por barrio y trimestre.

---

### 2. Fuente de datos: Dades Obertes Catalunya (Socrata)

#### 2.1. Plataforma

- **Portal:** Dades Obertes Catalunya (Generalitat)  
- **Tecnología:** Socrata (endpoint estándar tipo `resource/{ID}.json`).
- **Endpoint base API:**

  ```text
  https://analisi.transparenciacatalunya.cat/resource/{DATASET_ID}.json
  ```

  Opcionalmente, se puede usar exportación CSV:

  ```text
  https://analisi.transparenciacatalunya.cat/resource/{DATASET_ID}.csv
  ```

#### 2.2. Dataset objetivo (conceptual)

- **Nombre funcional:**  
  «Mercat de lloguer d'habitatge per barris de Barcelona» (o variante muy próxima).
- **Origen lógico:**  
  Datos de fianzas de alquiler depositadas en **Incasòl**, agregadas por:
  - Barrio o código territorial equivalente (p. ej. `codi_barri`, `codi_ine`, `codi_territorial`).
  - Trimestre (p. ej. `any`, `trimestre`).

> Nota: El identificador concreto `{DATASET_ID}` debe confirmarse manualmente en el portal de Dades Obertes, filtrando por palabras clave como *lloguer*, *habitatge*, *barri*, *Barcelona*, *Incasòl*.

---

### 3. Estructura esperada del dataset

#### 3.1. Claves de dimensión

- **Barrio / territorio:**
  - `Codi_Barri`, `codi_barri` o campo equivalente.
  - `Nom_Barri` (nombre del barrio).
  - Alternativamente, puede haber nivel municipio/distrito (`codi_municipi`, `nom_municipi`, `codi_districte`).

- **Tiempo:**
  - `any` (año).
  - `trimestre` (1–4) o un campo combinando ambos (p. ej. `any_trimestre`).

#### 3.2. Métricas clave

Campos típicos (nombres aproximados, sujetos a confirmación):

- **Precio absoluto:**
  - `lloguer_mitja_mensual` – alquiler medio mensual en euros.

- **Precio relativo (intensidad):**
  - `lloguer_mitja_per_superficie` – alquiler medio por m².

- **Volumen / fiabilidad:**
  - `nombre_contractes` – número de contratos de alquiler registrados en el periodo.

Estos tres campos son esenciales:

- Permiten comparar barrios con diferente tamaño (€/m²).
- Permiten filtrar periodos/barrio con **muy pocos contratos**, que podrían ser ruidosos.

---

### 4. Cobertura temporal y granularidad

#### 4.1. Cobertura temporal esperada

Basado en la práctica habitual de este tipo de series:

- Inicio probable: entre **2013 y 2015** (hay estudios públicos con series largas).
- Final: **T-1 o T-2** respecto al año actual (desfase de validación de datos).

Para el proyecto:

- **Target mínimo razonable:** 2015–2023 (alineado con renta disponible y otros datos).
- Si existen datos posteriores (2024, trimestres de 2025), se pueden usar como “early signal”, pero sin la misma robustez que los años cerrados.

#### 4.2. Granularidad temporal

- Periodicidad: **trimestral**.
- Posible existencia de:
  - Campos adicionales tipo `mes` (si hay mayor detalle).
  - Agregaciones anuales pre-calculadas.

El extractor debería:

- Trabajar internamente con **nivel trimestral**.
- Ofrecer una opción para agregar a **nivel anual** en la capa de transformación / modeling.

---

### 5. Uso de la API de Socrata

#### 5.1. Endpoint básico

Ejemplo genérico (JSON):

```text
GET https://analisi.transparenciacatalunya.cat/resource/{DATASET_ID}.json
```

Parámetros útiles (estándar Socrata / SoQL):

- `$select` – selección y agregación de columnas.
- `$where` – filtros (por año, barrio, nº contratos, etc.).
- `$limit` – número máximo de registros (importante para paginar).
- `$offset` – desplazamiento para paginación manual.

#### 5.2. Filtro por años

Filtro típico para rango de años:

```text
$where=any >= 2015 AND any <= 2023
```

Si el campo de año se llama distinto (`any`, `year`, `any_contracte`, etc.) habrá que adaptarlo.

#### 5.3. Consideraciones técnicas

- **Paginación:**  
  Socrata suele tener límites por request (p. ej. 50k filas). El extractor debería:
  - Detectar el límite de filas.
  - Hacer requests paginadas usando `$limit` + `$offset`.

- **Rate limiting:**  
  Seguir el mismo patrón que otros extractores (`rate_limit_delay` configurable).

- **Autenticación:**  
  Muchos datasets públicos de Socrata son accesibles sin token, pero:
  - Es recomendable soportar un **App Token** opcional (cabecera `X-App-Token`) por si se endurecen límites en el futuro.

---

### 6. Riesgos y puntos de atención

- **Cambios de esquema:**  
  - Posibles renombrados de columnas (ej. `lloguer_mitja_mensual` → `lloguer_mitja`).
  - Nuevas columnas que no existían en años antiguos.

- **Cambios territoriales:**  
  - Algún ajuste de límites de barrio o códigos a lo largo de los años.
  - Es importante mapear todo a la tabla estándar `dim_barrios` usando `codi_barri`.

- **Datos con pocos contratos:**  
  - Trimestres o barrios con `nombre_contractes` muy bajo pueden dar precios inestables.
  - Se recomienda definir un **umbral mínimo de contratos** (p. ej. `>= 5`) y:
    - Marcar los puntos por debajo de ese umbral como menos fiables, o
    - Excluirlos de ciertos análisis agregados.

---

### 7. Diseño propuesto del extractor

#### 7.1. Nombre y ubicación

- Módulo: `src/extraction/incasol.py`
- Clase principal: `IncasolSocrataExtractor` (o `IncasolExtractor`).
- Hereda de: `BaseExtractor` (mismo patrón que `OpenDataBCNExtractor` e `IDESCATExtractor`).

#### 7.2. API pública propuesta

Firma principal:

```python
from typing import Dict, Tuple

import pandas as pd

from src.extraction.base import BaseExtractor


class IncasolSocrataExtractor(BaseExtractor):
    """
    Extractor de datos de alquiler (mercado de lloguer) desde Dades Obertes Catalunya.
    
    Usa la API Socrata de la Generalitat para obtener series históricas basadas
    en fianzas de alquiler gestionadas por Incasòl.
    """
    
    def get_rent_by_neighborhood_quarter(
        self,
        year_start: int,
        year_end: int,
        min_contracts: int = 0
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Obtiene la serie histórica de alquiler por barrio y trimestre.
        
        Args:
            year_start: Año inicial (inclusive).
            year_end: Año final (inclusive).
            min_contracts: Umbral mínimo de contratos por punto de datos. 
                Si es > 0, se pueden filtrar o marcar los registros con
                menos contratos que este valor.
        
        Returns:
            Tupla (df, metadata) donde:
                - df: DataFrame con columnas al menos:
                    - barrio_id o Codi_Barri
                    - Nom_Barri
                    - anio
                    - trimestre
                    - rent_month (lloguer_mitja_mensual)
                    - rent_m2 (lloguer_mitja_per_superficie)
                    - contracts (nombre_contractes)
                - metadata: dict con información de cobertura y estrategia usada.
        """
```

Características clave del método:

- Usa el endpoint Socrata con filtros `$where` por año.
- Normaliza nombres de columnas a un esquema interno coherente:
  - `anio`, `quarter`, `rent_month`, `rent_m2`, `contracts`, `barrio_id` / `Codi_Barri`, `Nom_Barri`.
- Integra con:
  - `_save_raw_data` para guardar el CSV/JSON descargado en `data/raw/incasol/`.
  - `manifest.json` para registrar cada extracción con rango de años y timestamp.

#### 7.3. Metadata recomendada

El `metadata` devuelto debería incluir al menos:

- `source`: `"dades_obertes_catalunya_incasol"`
- `strategy_used`: `"socrata_api"`
- `success`: `True/False`
- `requested_range`: `{ "start": year_start, "end": year_end }`
- `available_years`: lista de años efectivamente presentes en los datos.
- `records`: número total de filas.
- `min_contracts_applied`: valor usado para el filtro de `min_contracts`.

---

### 8. Integración futura en el pipeline

Una vez implementado `IncasolSocrataExtractor`, los pasos lógicos serán:

1. **ETL – Extract:**
   - Ejecutar `get_rent_by_neighborhood_quarter(2015, 2023, min_contracts=0)` y guardar raw.

2. **Transform:**
   - Normalizar `Codi_Barri` → `barrio_id` usando `dim_barrios`.
   - Opcional: agregar de trimestral a anual si la tabla de hechos lo requiere.

3. **Load:**
   - Poblar tabla de hechos de alquiler histórico (`fact_precios_alquiler` o similar).
   - Alinear claves con `fact_precios` (venta) y renta disponible.

Con esto, el proyecto tendrá las tres patas fundamentales:

- **Renta disponible** (Open Data BCN, ya implementado vía `IDESCATExtractor`).
- **Precios de venta** (Open Data BCN).
- **Precios de alquiler** (Incasòl vía Dades Obertes Catalunya / Socrata).

Esto habilita directamente análisis de:

- Esfuerzo de alquiler por renta disponible.
- Dinámicas de gentrificación por barrio y periodo.
- Comparación entre venta vs alquiler a lo largo del tiempo.


