## Fuente: Generalitat de Catalunya - Índice de Referencia de Alquileres

### Descripción general

La Generalitat de Catalunya publica el **índice de referencia de precios de alquiler**
para viviendas, con el objetivo de ofrecer una referencia objetiva de precios y apoyar
las políticas de regulación del mercado del alquiler.

En este proyecto, estos datos se utilizan para construir la tabla de hechos
`fact_regulacion`, que resume el nivel de tensión del mercado del alquiler por barrio
(`barrio_id`) y año (`anio`).

### Cobertura y granularidad

- **Ámbito geográfico**: Barcelona ciudad, nivel barrio (`codi_barri`).
- **Frecuencia temporal**: anual.
- **Variables clave**:
  - Índice de referencia en €/m²/mes.
  - Códigos territoriales de la Generalitat (`codi_barri`).

### Mapeo de columnas

Esquema simplificado desde los datos originales de la Generalitat hacia `fact_regulacion`:

- Origen → Destino
  - `codi_barri` → `dim_barrios.codi_barri` → `fact_regulacion.barrio_id`
  - `any` / `anio` / `year` → `fact_regulacion.anio`
  - `indice_referencia` / `index_referencia` / `preu_ref_m2` →
    `fact_regulacion.indice_referencia_alquiler`

### Esquema `fact_regulacion`

Columnas principales:

- `barrio_id` (INTEGER, FK a `dim_barrios.barrio_id`)
- `anio` (INTEGER)
- `zona_tensionada` (BOOLEAN)
- `nivel_tension` (TEXT: `'alta' | 'media' | 'baja'`)
- `indice_referencia_alquiler` (REAL, €/m²/mes)
- `num_licencias_vut` (INTEGER, reservado para integración futura)
- `derecho_tanteo` (BOOLEAN, reservado para integración futura)

### Reglas de derivación de tensión

En esta primera versión, el nivel de tensión se estima usando terciles del índice
de referencia dentro del conjunto de datos disponible:

- Se calculan los cuantiles \(q_{0.33}\) y \(q_{0.66}\) de `indice_referencia_alquiler`.
- Para cada registro:
  - Si el valor es `NaN` → `nivel_tension = 'baja'`.
  - Si `valor >= q_{0.66}` → `nivel_tension = 'alta'`.
  - Si `q_{0.33} <= valor < q_{0.66}` → `nivel_tension = 'media'`.
  - Si `valor < q_{0.33}` → `nivel_tension = 'baja'`.
- `zona_tensionada` se define como `nivel_tension` en `{'alta', 'media'}`.

Estas reglas son **heurísticas** y están diseñadas para poder ajustarse en futuras
iteraciones cuando se disponga de la normativa y umbrales oficiales completos.

### Validaciones clave

El script `scripts/validate_regulacion.py` aplica las siguientes comprobaciones
sobre la tabla `fact_regulacion`:

- **Cobertura de barrios**: `COUNT(DISTINCT barrio_id) = 73`.
- **Cobertura temporal mínima**: presencia de los años 2024 y 2025.
- **Completitud del índice**:
  - \( \\geq 95\\% \) de los registros con `indice_referencia_alquiler` no nulo.

Si alguna de estas condiciones no se cumple, el script devuelve un código de salida
no cero para facilitar su integración en CI/CD.


