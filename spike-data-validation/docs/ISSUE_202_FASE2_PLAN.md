# Issue #202 - Fase 2: Modelo Hedonic Pricing MICRO (Gràcia)

## 🎯 Objetivo

Pasar de un baseline **MACRO** (barrio×año×dataset) a un modelo **MICRO** (edificio individual) para el barrio de Gràcia, integrando:

- Catastro **real** (descarga masiva oficial) con atributos físicos por edificio.
- Precios de mercado **Idealista** (anuncios recientes de venta/alquiler).
- Matching edificio-a-edificio (referencia catastral / dirección fuzzy).

Target de performance:

- **R² ≥ 0.75**
- **RMSE ≤ 250 €/m²**
- **Sesgo |mean_residual| < 100 €/m²**

## 🧱 Dependencias

- Fase 1 completada (Issues #199–#204, baseline macro v0.1).
- Scripts existentes:
  - `spike-data-validation/scripts/catastro_oficial_client.py`
  - `spike-data-validation/scripts/parse_catastro_masivo_output.py`
  - `spike-data-validation/scripts/filter_gracia_real.py`
  - `spike-data-validation/scripts/compare_imputed_vs_real.py`

Fase 2 trabajará encima de estos, pero con una estructura más clara en `spike-data-validation/scripts/fase2/`.

## 🗂️ Estructura Fase 2 (scripts)

```text
spike-data-validation/scripts/fase2/
  __init__.py
  download_catastro_massive.py      # Descarga XML masivo Catastro Barcelona
  parse_catastro_xml.py             # Parser iterativo XML -> CSV catastro_barcelona.csv
  scrape_idealista.py               # Scraper controlado Idealista (Gràcia)
  match_catastro_idealista.py       # Matching edificio-a-edificio (RC/dirección)
  train_micro_hedonic.py            # Entrenamiento modelo MICRO (hedónico)
```

## 🧩 Tareas Fase 2

### 1. Descarga Masiva Catastro Barcelona ✅ **EN PROGRESO**

**Script**: `fase2/download_catastro_massive.py`

**Estado actual (19 Dic 2025)**:
- ✅ **XML de entrada generado**: `consulta_masiva_entrada.xml` con formato correcto (`<LISTADATOS>`)
- ✅ **Enviado a Sede Electrónica**: Consulta "CONSULTA DE EDIFICIOS BARCELONA"
- ✅ **Fichero sistema**: `ECLTI250200147801.XML` (2,974 bytes)
- ✅ **Fecha envío**: 19/12/2025
- ⏳ **Pendiente**: Respuesta de la Sede (plazo estimado ≤24 horas según Sede)

**Inputs**:
- Seed de referencias catastrales: `gracia_refs_seed.csv` (60 referencias, 14 caracteres)
- Formato XML según Anexo 1 (versión 1.5/1.6): `<LISTADATOS>` con `<FEC>`, `<FIN>`, bloques `<DAT><RC>`

**Outputs esperados**:
- XML de salida de la Sede: `ECLTI250200147801.XML` (o nombre asignado por sistema)
- Guardar en: `spike-data-validation/data/raw/catastro_oficial/`

**Puntos clave**:
- ✅ Formato XML corregido según documentación oficial (resuelto error de esquema)
- ⏳ Procesamiento asíncrono por la Sede (1-2 horas típicamente)
- 📋 Próximo paso: Parsear XML de salida cuando esté disponible

**Documentación relacionada**:
- `docs/XML_VARIANTS_TESTING.md` - Proceso de debugging del formato XML
- `scripts/catastro_oficial_client.py` - Cliente que genera el XML correcto

### 2. Parser XML → CSV (Catastro Barcelona) ⏳ **PENDIENTE**

**Script**: `fase2/parse_catastro_xml.py`

**Estado**: Script placeholder creado, pendiente de implementación cuando llegue el XML de salida.

**Inputs**:
- XML de salida de la Sede: `ECLTI250200147801.XML` (o nombre asignado por sistema)
- Ubicación: `spike-data-validation/data/raw/catastro_oficial/`

**Outputs**:
- `spike-data-validation/data/processed/fase2/catastro_barcelona_parsed.csv`
  - Columnas mínimas: `referencia_catastral`, `superficie_m2`, `ano_construccion`, `plantas`, `uso_principal`, `direccion_normalizada`.

**Requisitos técnicos**:
- Parser iterativo (no cargar todo el XML en memoria).
- Manejar namespaces reales de Catastro (no idealizados).
- Script base existente: `scripts/parse_catastro_masivo_output.py` (usar como referencia)

**Nota**: La implementación se realizará una vez que tengamos el XML de salida real para adaptar el parser al formato exacto.

### 3. Scraping Idealista (Gràcia)

**Script**: `scrape_idealista.py`

**Inputs**:
- URL(s) de búsqueda Idealista para Gràcia (venta y/o alquiler).

**Outputs**:
- `spike-data-validation/data/processed/fase2/idealista_gracia_micro.csv`
  - Columnas mínimas: `direccion`, `precio`, `superficie_m2`, `precio_m2`, `lat`, `lon` (si se pueden obtener), `tipo_operacion`.

**Restricciones**:
- Scraping **controlado** (pocas páginas, sin agresividad).
- Documentar limitaciones legales/técnicas (solo para uso interno del spike).

### 4. Matching Catastro ↔ Idealista

**Script**: `match_catastro_idealista.py`

**Inputs**:
- `catastro_barcelona_parsed.csv` (filtrado a Gràcia).
- `idealista_gracia_micro.csv`.

**Outputs**:
- `spike-data-validation/data/processed/fase2/gracia_micro_matched.csv`
  - Nivel fila: **edificio/anuncio**.
  - Columnas: atributos Catastro + precio/precio_m2 Idealista + campos de calidad de match (`match_method`, score).

**Métodos de matching**:
- Nivel 1: Referencia catastral (si se dispone).
- Nivel 2: Fuzzy por dirección + barrio.
- Nivel 3: Coordenadas (distancia geográfica pequeña).

**Métricas**:
- Match rate global y por método.
- Porcentaje de matches “seguros” (ej. score > umbral).

### 5. Entrenamiento modelo MICRO hedónico

**Script**: `train_micro_hedonic.py`

**Inputs**:
- `gracia_micro_matched.csv`.

**Outputs**:
- Modelo entrenado (pickle o similar, opcional).
- CSV de predicciones:
  - `spike-data-validation/data/processed/fase2/micro_hedonic_predictions_202.csv`
- JSON de métricas:
  - `spike-data-validation/data/logs/micro_hedonic_model_202.json`

**Features esperadas**:
- `superficie_m2` individual.
- `ano_construccion`, `plantas`.
- Dummies de uso/estado (`luso`, `reformado`, etc. si existen).
- Dummy de operación (venta/alquiler).

**Targets**:
- `precio_m2` Idealista (log-precio opcional para estabilizar).

**Evaluación**:
- Split temporal (si hay suficiente rango) o cross-validation.
- Métricas:
  - R², RMSE, MAE.
  - Sesgo (mean_residual).

**Criterios de éxito**:
- R² ≥ 0.75.
- RMSE ≤ 250 €/m².
- |mean_residual| < 100 €/m².

## ✅ Criterio Go/No-Go Fase 2

Se considera que Fase 2 tiene **éxito suficiente** si:

1. Se obtiene un dataset `gracia_micro_matched.csv` con:
   - ≥ 50 matches “seguros” edificio↔anuncio.
   - Variabilidad real en `superficie_m2` y `ano_construccion` **dentro de cada barrio**.
2. El modelo MICRO v1.0 cumple al menos **2 de 3**:
   - R² ≥ 0.75.
   - RMSE ≤ 250 €/m².
   - |mean_residual| < 100 €/m².
3. Las mejoras frente al baseline MACRO v0.1 son claras:
   - ΔR² ≥ +0.04.
   - ΔRMSE ≤ −70 €/m².

Si estos criterios NO se cumplen, se documentará el motivo (datos insuficientes, match rate bajo, etc.) y se considerará mantener MACRO v0.1 como baseline operativo.


