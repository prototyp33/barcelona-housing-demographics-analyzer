# Territory Mapping Overrides

Este documento detalla la lógica adicional aplicada al mapear los territorios del Portal de Dades a `barrio_id` dentro del ETL.

## Heurísticas activas

1. **Normalización exhaustiva**: se usan minúsculas, sin acentos ni caracteres especiales.
2. **Alias manuales**: casos donde el nombre del portal omite artículos (`la`, `l'`) u otras partículas.
3. **Búsqueda difusa (`difflib.get_close_matches`)**: último recurso con `cutoff=0.82`.
4. **Territorios agregados**:
   - `Districte`: no se asigna directamente; los enriquecimientos distribuyen el valor entre los barrios del distrito ponderando por población.
   - `Municipi`: idem, se reparte entre todos los barrios.

## Alias manuales

| Alias normalizado | Barrio destino |
| ----------------- | -------------- |
| `antigaesquerraeixample` | `l'Antiga Esquerra de l'Eixample` |
| `novaesquerraeixample` | `la Nova Esquerra de l'Eixample` |
| `vilaolimpicadelpoblenou` | `la Vila Olímpica del Poblenou` |
| `fontdenfargues` | `la Font d'en Fargues` |
| `bordeta` | `la Bordeta` |
| `marinadeport` | `la Marina de Port` |
| `marinadelpratvermell` | `la Marina del Prat Vermell` |
| `trinitatnova` | `la Trinitat Nova` |
| `trinitatvella` | `la Trinitat Vella` |
| `guineueta` | `la Guineueta` |

> Los alias se añaden en `BARRIO_ALIAS_OVERRIDES` (`src/data_processing.py`). Cualquier nueva excepción debe documentarse aquí.

## Distribución de agregados

Los enriquecimientos demográficos (`enrich_fact_demografia`) usan los indicadores:

- Hogares (`hd7u1b68qj`)
- Edad media edificaciones (`ydtnyd6qhm`)
- Compras extranjeras (`uuxbxa7onv`)
- Superficie catastral (`wjnmk82jd9`)

Cuando el indicador llega a nivel distrito/municipio:

1. Se identifican los barrios del ámbito mediante `_normalize_text`.
2. Se calculan pesos según la población observada en `fact_demografia`.  
   Si no hay datos para el año, se usa la media histórica del barrio; si sigue faltando, se reparte en partes iguales.

Esta metodología preserva la trazabilidad de cada métrica sin introducir sesgos por asignaciones arbitrarias.


