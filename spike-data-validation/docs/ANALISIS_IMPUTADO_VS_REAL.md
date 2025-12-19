# Análisis: Catastro imputado vs Catastro real (Issue #200)

## Contexto

Actualmente los servicios SOAP `Consulta_DNPRC` y `Consulta_DNPLOC` del Catastro están devolviendo el error:

> `código 12: LA PROVINCIA NO EXISTE`

Esto bloquea la extracción directa de atributos (superficie, año, plantas) por referencia/dirección.

Como workaround, el spike usa `Consulta_RCCOOR` (por coordenadas), que devuelve:

- referencia catastral (PC1+PC2, 14 chars)
- coordenadas
- dirección

Pero **no devuelve** superficie/año/uso.

## Objetivo de este documento

Comparar el dataset imputado (Fase 1) con el dataset real (Fase 2) cuando se obtenga vía consulta masiva oficial.

- Validar si la imputación fue un buen checkpoint para arquitectura.
- Medir cuánto mejora el modelo hedonic al pasar de imputado a real.

## Archivos

- Imputado (Fase 1): `spike-data-validation/data/processed/catastro_gracia_imputado.csv`
- Real (Fase 2): `spike-data-validation/data/processed/catastro_gracia_real.csv`
- Merged (Issue #201):
  - v0.1 (imputado): `spike-data-validation/data/processed/gracia_merged.csv`
  - v1.0 (real): `spike-data-validation/data/processed/gracia_merged_v2.csv`

## Checks recomendados

### 1) Cobertura

- % de edificios con superficie/año/plantas no nulos
- # barrios representados (ideal: 5 barrios de Gràcia)

### 2) Distribuciones

- Histograma `superficie_m2` imputado vs real
- Histograma `ano_construccion` imputado vs real
- `plantas` imputado vs real

### 3) Error por edificio

- `abs(superficie_imputada - superficie_real)`
- `abs(ano_imputado - ano_real)`

### 4) Impacto en modelo

Comparar (v0.1 imputado) vs (v1.0 real):

- R²
- RMSE
- estabilidad de importancias

## Resultados

Este documento se puede generar/actualizar automáticamente al ejecutar:

- `spike-data-validation/scripts/compare_imputed_vs_real.py`

Nota:

- Si aún no existe `catastro_gracia_real.csv` con atributos reales (superficie/año/plantas),
  las métricas aparecerán como “no disponible”.

