# Búsqueda Manual de Datasets de Prioridad Máxima

**Fecha**: 2025-11-15  
**Objetivo**: Encontrar los 3 datasets de prioridad máxima en Open Data BCN según la guía proporcionada.

---

## 🔴 Prioridad 1: Censo y Población Real por Barrio y Edad Quinquenal

### Búsqueda Realizada
- **Términos probados**: 
  - `Padró edat quinquennal barris`
  - `padró barri edat`
  - `població barri`
  - `mdb barri`
  - `pad barri`

### Resultados
✅ **ENCONTRADO**: Dataset de población por continente de nacimiento, sexe y edad quinquenal **POR BARRIO**

**Dataset encontrado**:
- **ID**: `pad_mdb_lloc-naix-continent_edat-q_sexe`
- **Título**: "Població per continent de naixement, sexe i edat quinquennal"
- **Descripción**: Población de Barcelona agregada por continente de nacimiento, sexe y edad en grupos de cinco años según el registro del Padrón Municipal de Habitantes
- **URL**: https://opendata-ajuntament.barcelona.cat/data/ca/dataset/pad_mdb_lloc-naix-continent_edat-q_sexe

**⚠️ IMPORTANTE**: Aunque la descripción dice "agregada", el dataset **SÍ tiene desglose por barrio**.

**Estructura de datos** (verificado en CSV):
- `Codi_Districte`, `Nom_Districte`: Código y nombre del distrito
- `Codi_Barri`, `Nom_Barri`: **Código y nombre del barrio** ✅
- `Valor`: Población
- `LLOC_NAIX_CONTINENT`: Continente de nacimiento (1=España, 2=Europa, 3=África, 4=América, 5=Asia, 6=Oceanía)
- `EDAT_Q`: **Edad quinquenal** (0=0-4, 1=5-9, 2=10-14, ..., 18=90+) ✅
- `SEXE`: Sexo (1=Hombre, 2=Mujer)
- `Data_Referencia`: Fecha de referencia (1 de enero de cada año)

**Recursos disponibles**:
- CSV y JSON por año (2025, 2024, 2023, etc.)
- Datos históricos disponibles

**Uso**:
- ✅ **Edad quinquenal por barrio**: Se puede sumar grupos quinquenales para crear grupos personalizados (18-34, 35-49, etc.)
- ✅ **Nacionalidad/Origen por barrio**: El continente de nacimiento puede usarse como proxy de nacionalidad
- ✅ **Sexo por barrio**: Datos desglosados por sexo

### Otros Datasets Relacionados (pero agregados a nivel Barcelona)
- `pad_mdb_nacionalitat-contintent_edat-q_sexe`: Población por continente de nacionalidad, sexe y edad quinquenal (agregado Barcelona)
- `pad_mdbas_sexe`: Población por sexe (agregado Barcelona)

---

## 🟢 Prioridad 2: GeoJSON de Barrios

### Búsqueda Realizada
- **Términos probados**: 
  - `limits barris`
  - `20170706-districtes-barris` (ID conocido)

### Resultados
✅ **ENCONTRADO**: Dataset de unidades administrativas de Barcelona

**Dataset**:
- **ID**: `20170706_Districtes_Barris` (también funciona `20170706-districtes-barris`)
- **Título**: "Unitats administratives de la ciutat de Barcelona"
- **Descripción**: Detalle de las unidades administrativas: distritos, barrios, área interés, áreas estadísticas básicas (AEB) y secciones censales
- **URL**: https://opendata-ajuntament.barcelona.cat/data/ca/dataset/20170706-districtes-barris

**⚠️ IMPORTANTE - Actualización 7/6/2023**:
Desde el 7 de junio de 2023 se publican nuevos recursos con geometría incorporada en ETRS89 y WGS84. El recurso antiguo `Unitats_Administratives_BCN.csv` fue reemplazado por `BarcelonaCiutat_Barris.csv` y se dio de baja el 30/6/2023.

**Recursos GeoJSON encontrados** (ordenados por prioridad):

1. **✅ PRIORIDAD MÁXIMA: Nuevos recursos BarcelonaCiutat_Barris** (desde 7/6/2023):
   - **JSON de barrios** (recomendado):
     - **Nombre**: `BarcelonaCiutat_Barris.json`
     - **Resource ID**: `75197dfe-0306-4c5e-9643-34948af07fb6`
     - **Formato**: JSON con geometría incorporada
     - **Geometría**: Incluye polígonos en ETRS89 y WGS84
     - **Estructura**: `codi_districte, nom_districte, codi_barri, nom_barri, aeb, codi_seccio_censal, geometria_etrs89, geometria_wgs84`
   
   - **CSV de barrios** (alternativa con geometría):
     - **Nombre**: `BarcelonaCiutat_Barris.csv`
     - **Resource ID**: `b21fa550-56ea-4f4c-9adc-b8009381896e`
     - **Formato**: CSV con geometría en columnas `geometria_etrs89` y `geometria_wgs84`
     - **Estructura**: Misma que el JSON pero en formato CSV

2. **⚠️ FORMATO ANTIGUO** (mantenido por compatibilidad):
   - **GeoJSON principal**:
     - **Nombre**: `Unitats_Administratives_BCN.geojson`
     - **Resource ID**: `cd800462-f326-429f-a67a-c69b7fc4c50a`
     - **Formato**: GeoJSON estándar
     - **Fecha creación**: 2019-12-12
     - **Nota**: Aunque sigue disponible, los nuevos recursos son preferibles

**Otros recursos disponibles**:
- `BarcelonaCiutat_Districtes.csv/json`: Datos de distritos con geometría
- `BarcelonaCiutat_AreesEstadistiquesBasiques.csv/json`: Áreas estadísticas básicas
- `BarcelonaCiutat_SeccionsCensals.csv/json`: Secciones censales
- Formatos adicionales: SHP, KMZ, WMS, etc.

**Estructura de los nuevos recursos CSV/JSON**:
- `codi_districte`: Código del distrito
- `nom_districte`: Nombre del distrito
- `codi_barri`: Código del barrio (si aplica)
- `nom_barri`: Nombre del barrio (si aplica)
- `aeb`: Área estadística básica (si aplica)
- `codi_seccio_censal`: Código de la sección censal (si aplica)
- `geometria_etrs89`: Polígono de la unidad administrativa en ETRS89
- `geometria_wgs84`: Polígono de la unidad administrativa en WGS84

**Códigos oficiales**:
- Los códigos y nombres oficiales de los 10 distritos y 73 barrios fueron aprobados el 22/12/2006 y publicados en la Gaceta Municipal el 28/02/2007.

### Estado
✅ **COMPLETADO**: El código está configurado para priorizar los nuevos recursos `BarcelonaCiutat_Barris` (desde 7/6/2023) sobre el formato antiguo. Se actualizó con los resource IDs específicos y la priorización correcta.

---

## 🟡 Prioridad 3: Renta Familiar Disponible por Barrio

### Búsqueda Realizada
- **Términos probados**: 
  - `Renda Familiar Disponible per barri`
  - `renda barri`
  - `renda familiar disponible barri`
  - `indicadors renda barri`

### Resultados
✅ **ENCONTRADO**: Se encontraron múltiples datasets de renta que **SÍ tienen datos por barrio**.

**⚠️ IMPORTANTE**: Aunque los datos están a nivel de sección censal, **todos incluyen `Codi_Barri` y `Nom_Barri`**, por lo que se pueden agregar fácilmente por barrio.

**Datasets encontrados**:

1. **Renta Disponible por Persona** (Prioridad recomendada):
   - **ID**: `renda-disponible-llars-bcn`
   - **Título**: "Renda disponible de les llars per càpita(€) a la ciutat de Barcelona"
   - **Descripción**: Estimación de la Renta Disponible de los hogares por persona (€) a la ciudad de Barcelona
   - **URL**: https://opendata-ajuntament.barcelona.cat/data/ca/dataset/renda-disponible-llars-bcn
   - **Estructura**: `Any, Codi_Districte, Nom_Districte, Codi_Barri, Nom_Barri, Seccio_Censal, Import_Euros`
   - **Recursos**: CSV por año (2022, 2021, 2020, 2019, 2018)

2. **Renta Bruta por Hogar**:
   - **ID**: `atles-renda-bruta-per-llar`
   - **Título**: "Renda tributària bruta mitjana per llar (€) a la ciutat de Barcelona"
   - **URL**: https://opendata-ajuntament.barcelona.cat/data/ca/dataset/atles-renda-bruta-per-llar
   - **Estructura**: `Any, Codi_Districte, Nom_Districte, Codi_Barri, Nom_Barri, Seccio_Censal, Import_Renda_Bruta_€`
   - **Recursos**: CSV por año (2023, 2022, 2021, 2020, 2019, etc.)

3. **Renta Bruta por Persona**:
   - **ID**: `atles-renda-bruta-per-persona`
   - **Título**: "Renda tributària bruta mitjana per persona (€) a la ciutat de Barcelona"
   - **URL**: https://opendata-ajuntament.barcelona.cat/data/ca/dataset/atles-renda-bruta-per-persona
   - **Estructura**: Similar a los anteriores con `Codi_Barri` y `Nom_Barri`
   - **Recursos**: CSV por año (2023, 2022, 2021, 2020, 2019, etc.)

**Agregación por Barrio**:
- Todos estos datasets tienen `Codi_Barri` y `Nom_Barri` en cada fila
- Se puede agregar fácilmente usando `groupby` en pandas: `df.groupby(['Any', 'Codi_Barri', 'Nom_Barri'])['Import_Euros'].mean()` o `.sum()` según corresponda
- No se necesita el dataset de unidades administrativas para la agregación (ya está incluido en cada fila)

### Recomendaciones
1. ✅ **Usar `renda-disponible-llars-bcn`**: Renta disponible por persona (más relevante para análisis de vivienda)
2. ✅ **Agregar por barrio**: Usar `groupby` en `Codi_Barri` para obtener renta promedio o mediana por barrio
3. **Alternativas**: Los otros datasets (`atles-renda-bruta-per-llar`, `atles-renda-bruta-per-persona`) pueden usarse como complemento

---

## 📊 Resumen de Hallazgos

| Prioridad | Dataset | Estado | ID/Resource ID |
|-----------|---------|--------|----------------|
| 1. Población por barrio y edad quinquenal | ✅ Encontrado | `pad_mdb_lloc-naix-continent_edat-q_sexe` | - |
| 2. GeoJSON de barrios | ✅ Encontrado | `20170706_Districtes_Barris` | Resource: `cd800462-f326-429f-a67a-c69b7fc4c50a` |
| 3. Renta por barrio | ✅ Encontrado (con Codi_Barri) | `renda-disponible-llars-bcn`, `atles-renda-bruta-per-llar`, `atles-renda-bruta-per-persona` | - |

---

## 🔧 Actualizaciones Realizadas en el Código

### 1. GeoJSONExtractor
- ✅ Actualizado `KNOWN_DATASET_IDS` con el ID correcto: `20170706_Districtes_Barris`
- ✅ Agregado `KNOWN_GEOJSON_RESOURCE_IDS` con los resource IDs específicos:
  - **Prioridad máxima**: `BarcelonaCiutat_Barris.json` y `BarcelonaCiutat_Barris.csv` (nuevos recursos desde 7/6/2023)
  - **Formato antiguo**: `Unitats_Administratives_BCN.geojson` (mantenido por compatibilidad)
- ✅ Actualizada la priorización de recursos para usar primero los nuevos recursos `BarcelonaCiutat_Barris`
- ✅ Los nuevos recursos incluyen geometría en ETRS89 y WGS84 incorporada

### 2. RentaExtractor
- ✅ Actualizado `KNOWN_DATASET_IDS` con los 3 datasets encontrados que tienen `Codi_Barri` y `Nom_Barri`
- ✅ Agregados como prioridad máxima: `renda-disponible-llars-bcn`, `atles-renda-bruta-per-llar`, `atles-renda-bruta-per-persona`
- ✅ Nota: Aunque los datos están por sección censal, incluyen `Codi_Barri` y `Nom_Barri`, por lo que se pueden agregar fácilmente por barrio
- ⚠️ Pendiente: Implementar función de agregación por barrio usando `groupby` en pandas

### 3. DemografiaAmpliadaExtractor
- ✅ Actualizado `KNOWN_DATASET_IDS` con el dataset encontrado: `pad_mdb_lloc-naix-continent_edat-q_sexe`
- ✅ Agregado como prioridad máxima para "edad_quinquenal" y "nacionalidad"
- ✅ Dataset confirmado con datos por barrio, edad quinquenal, sexo y continente de nacimiento

---

## 📝 Estado de Implementación

1. **GeoJSON**: ✅ COMPLETADO
   - Extracción funcionando (73 features)
   - Conversión WKT a GeoJSON implementada
   - Integración en `dim_barrios` con carga automática de geometrías
   - 73 barrios con geometrías completas

2. **Población por barrio y edad quinquenal**: ✅ COMPLETADO
   - Dataset encontrado y configurado: `pad_mdb_lloc-naix-continent_edat-q_sexe`
   - Procesamiento implementado: `prepare_demografia_ampliada()`
   - Agrupa edades quinquenales en grupos personalizados (18-34, 35-49, 50-64, 65+)
   - Mapea continente de nacimiento a categorías de nacionalidad
   - Tabla `fact_demografia_ampliada` creada y funcionando

3. **Renta**: ✅ COMPLETADO
   - Datasets encontrados con `Codi_Barri` y `Nom_Barri`
   - Función de agregación por barrio implementada: `prepare_renta_barrio()`
   - Calcula promedio, mediana, min, max y número de secciones censales
   - Usa `renda-disponible-llars-bcn` como fuente principal
   - Tabla `fact_renta` creada y funcionando

## 🎯 Próximos Pasos

Todas las prioridades 1, 2 y 3 están completadas. Las siguientes tareas según `FUENTES_PENDIENTES.md`:

- **Prioridad 4**: Mercado Inmobiliario Privado (Idealista API)
- **Prioridad 5**: Datos de Vivienda Pública (INCASÒL)
- **Prioridad 6**: Indicadores de Movilidad y Turismo (InsideAirbnb)

---

## 🔗 Referencias

- [Open Data BCN - Portal](https://opendata-ajuntament.barcelona.cat/)
- [Open Data BCN - API CKAN](https://opendata-ajuntament.barcelona.cat/data/api/3/action)
- [Dataset: Unidades Administrativas](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/20170706-districtes-barris)
- [Dataset: Renta Disponible](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/renda-disponible-llars-bcn)

