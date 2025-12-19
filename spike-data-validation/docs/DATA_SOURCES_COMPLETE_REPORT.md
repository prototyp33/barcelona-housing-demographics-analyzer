# 📑 Reporte Técnico Completo: Fuentes de Datos para Spike Gràcia

**Fecha**: 17 Diciembre 2025  
**Objetivo**: Caracterizar técnica y funcionalmente todas las fuentes de datos necesarias para el modelo de precios hedonic y validación del spike de Gràcia.

**Enfoque**: Soluciones 100% gratuitas, oficiales y sin dependencias externas para garantizar sostenibilidad y coste cero.

**Issues relacionados**: #199, #200, #201

---

## 1. Catastro (Fuente Primaria: Características Físicas)

### A. API Oficial SOAP (Sede Electrónica) - **⭐ RECOMENDADA (OFICIAL Y GRATUITA)**

Servicio oficial del Ministerio de Hacienda. Permite consultar datos físicos (no protegidos) de cualquier inmueble sin coste ni registro.

**Nombre**: Servicio de Consulta de Datos No Protegidos

**URL Endpoint**: `http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx`

**Método**: SOAP / POST XML (o GET con parámetros)

**Coste**: **Gratis** (Público, sin registro ni API Key)

**Librería Python**: `requests` (XML manual) o `zeep` (Cliente SOAP)

**Funcionamiento**:
1. **Input**: Referencia Catastral (RC)
2. **Operación**: `Consulta_DNPRC` (Datos No Protegidos)
3. **Output**: XML con superficie, año construcción, uso, y geometría

**Ejemplo de Respuesta (XML simplificado)**:
```xml
<bico>
  <bi>
    <idbi>...</idbi>
    <dt>
      <locat>
         <cmc>019</cmc> <!-- Municipio Barcelona -->
      </locat>
    </dt>
    <debi>
      <luso>V</luso> <!-- Uso: Vivienda -->
      <sfc>120</sfc> <!-- Superficie -->
      <ant>1975</ant> <!-- Año Construcción -->
    </debi>
  </bi>
</bico>
```

**Ventajas**:
- ✅ **Coste Cero**: No hay suscripciones ni freemiums limitados
- ✅ **Sostenibilidad**: Fuente oficial que no desaparecerá
- ✅ **Independencia**: No depende de wrappers de terceros
- ✅ **Legalidad**: Cumple con condiciones de uso de datos públicos

**Implementación en Proyecto**:
- ⚠️ **Pendiente**: Crear cliente SOAP oficial (reemplazar `catastro_client.py`)
- Script principal: `spike-data-validation/scripts/extract_catastro_gracia.py` (actualizar)

---

### B. WFS INSPIRE (Geometrías Masivas) - **PARA GEOMETRÍAS**

Para descargar geometrías de parcelas y edificios (Shapefiles/GML) sin atributos detallados.

Servicio oficial del Ministerio de Hacienda. Estándar OGC.

**URL**: `http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx`

**Método**: WFS (Web Feature Service) 2.0.0

**Formato**: GML (Geography Markup Language) / XML

**Autenticación**: Ninguna (Público)

**Dataset**: `CP.Building` (Edificios)

**Detalles de Extracción**:
- Requiere librería `OWSLib` o `GeoPandas` para parsear GML
- Se consulta por *Bounding Box* (coordenadas geográficas)
- **Ventaja**: Descarga masiva de geometrías
- **Desventaja**: A veces omite atributos como "Año Construcción" en la capa INSPIRE estándar, limitándose a geometría
- **Uso**: Visualización en mapas o cruce espacial

---

### C. Consulta Masiva Oficial (D.G. del Catastro) - **ALTERNATIVA OFICIAL (ASÍNCRONA)**

Servicio oficial de consulta masiva de datos NO protegidos.

**URL**: `https://www1.sedecatastro.gob.es`

**Método**: Consulta masiva asíncrona (XML entrada/salida)

**Formato**: XML según especificación oficial

**Autenticación**: Registro en Sede Electrónica (no requiere certificado digital para datos NO protegidos)

**Procesamiento**: Asíncrono (1-2 horas)

**Implementación en Proyecto**:
- Cliente: `spike-data-validation/scripts/catastro_oficial_client.py`
- Generador XML: `spike-data-validation/scripts/generate_catastro_xml.py`
- Documentación: `spike-data-validation/docs/CATASTRO_DATA_SOURCES.md`

---

## 2. Portal Dades Barcelona (Fuente Secundaria: Validación)

Plataforma oficial de datos abiertos del Ayuntamiento. Útil para validar distribuciones agregadas.

### A. Dataset: Edificios por Año de Construcción (Agregado)

**ID**: `est-cadastre-edificacions-any-const` (o `ohwxchendm` en API interna)

**URL**: https://opendata-ajuntament.barcelona.cat/data/dataset/est-cadastre-edificacions-any-const

**Formato**: CSV (Codificación: UTF-8 o ISO-8859-1)

**Método de Extracción**:
- Directo: `pandas.read_csv(URL)`
- API CKAN: `GET /data/api/action/datastore_search?resource_id=...`

**Estructura**:
- `Nom_Districte`: "Gràcia"
- `Nom_Barri`: "la Vila de Gràcia"
- `Any_Construccio`: Año (ej. 1980)
- `Nombre_Edificacions`: Conteo (ej. 45) — **⚠️ DATO AGREGADO**

**Uso**: Validar que los datos obtenidos vía SOAP tengan una distribución de edades coherente con la realidad oficial del barrio. Comparar histograma de años de tu muestra vs. histograma oficial.

---

### B. Dataset: Parcelario (CartoBCN) - **⭐ SEED CRÍTICO**

Base gráfica de la ciudad. Contiene las referencias catastrales georreferenciadas. **Fundamental para generar la lista semilla (seed) de edificios a consultar**.

**ID**: `parcelari`

**URL**: https://opendata-ajuntament.barcelona.cat/data/dataset/parcelari

**Formatos**: SHP (Shapefile), CSV

**Acceso**: Descarga directa desde Open Data BCN

**Contenido Clave**:
- Geometría (Polígonos de parcelas)
- `REF_CATASTR`: La clave primaria para cruzar con todo lo demás
- `DISTRITO` / `BARRIO`: Códigos administrativos

**Estrategia de Uso**:
1. Descargar CSV/SHP del parcelario completo
2. Filtrar por `Distrito=06` (Gràcia)
3. Extraer lista de Referencias Catastrales
4. Usar esa lista para consultar la API SOAP del Catastro una a una

**Uso en Proyecto**: Generar seed CSV de referencias catastrales para Gràcia

---

### C. Dataset: Precios de Vivienda (Portal Dades)

**Indicador Principal**: `bxtvnxvukh` (Precio medio €/m² transmisiones)

**URL API**: `https://portaldades.ajuntament.barcelona.cat/services/backend/rest/statistic/export`

**Método**: REST API con `X-IBM-Client-Id`

**Formato**: CSV

**Implementación en Proyecto**:
- Extractor: `src/extraction/portaldades.py`
- Transformación: `src/etl/transformations/enrichment.py`
- Script spike: `spike-data-validation/scripts/extract_precios_gracia.py`
- Notebook: `notebooks/spike_gracia_portaldades_alquiler.ipynb`

**Estructura**:
- `barrio_id`: ID del barrio (28-32 para Gràcia)
- `anio`: Año (2020-2025)
- `trimestre`: Trimestre (opcional)
- `precio_m2`: Precio por m² en euros
- `dataset_id`: ID del dataset fuente
- `source`: Fuente de datos

---

## 3. Idealista (Fuente: Mercado / Oferta)

### A. API Oficial

**Estado**: Acceso muy restringido (Partners B2B)

**Autenticación**: OAuth2 (`Bearer Token`)

**Método**: `POST /3.5/es/search`

**Parámetros**: `center` (lat,lon), `distance` (metros), `operation` (sale/rent)

**Nota**: No viable para scraping masivo sin contrato

**Limitación en Proyecto**: 
- **150 calls/mes** según reglas del proyecto
- Uso reservado para validación puntual, no para extracción masiva

---

### B. Extracción Alternativa (Scraping Controlado)

**Estrategia**:
- Parseo HTML (`BeautifulSoup` / `Playwright`)
- Extracción de: Precio, m², Habitaciones, Planta, Descripción

**⚠️ Reto**: Idealista tiene medidas anti-bot muy agresivas (WAF, Captchas)

**Recomendación**: 
- Usar datasets ya extraídos o servicios de terceros para el spike
- Realizar scraping muy lento y distribuido si es necesario
- **NO recomendado para spike de validación**

---

## 4. Fuentes Complementarias (Contexto Demográfico)

### A. Idescat API (Instituto de Estadística de Cataluña) - **GRATUITO Y PÚBLICO**

**URL**: `https://api.idescat.cat/pob/v1/cerca.json`

**Dataset**: Población por sexo y edad (sección censal)

**Método**: GET REST

**Estructura**: JSON anidado

**Acceso**: Gratuito y público

**Uso**: Variables de contexto (densidad, envejecimiento). Validar densidad de población en zonas de precios altos.

**Limitación**: Datos a nivel municipal, censo cada 5 años

---

### B. Incasòl (Fianzas de Alquiler) - **OPEN DATA GENERALITAT**

**Dataset**: Registre de fiances de lloguer

**URL**: https://analisi.transparenciacatalunya.cat/

**Acceso**: Open Data Generalitat (gratuito)

**Formato**: CSV trimestral agregado

**Valor**: Precios reales de cierre de alquiler (no oferta). "Ground truth" para calibrar modelos de precios.

**Limitación**: Agregado por municipio o zonas grandes, trimestral. Granularidad menor (barrio/distrito) que el anuncio individual.

**Uso Potencial**: Validar precios de alquiler reales vs oferta

---

### C. Agencia Tributaria (Renta)

**Dataset**: Renta media por código postal/barrio

**Uso**: Variable explicativa potente para el modelo de precios (Proxy de nivel socioeconómico)

**Disponibilidad**: Datos agregados, acceso público limitado

---

## ⚙️ Resumen Técnico para Implementación (Stack Gratuito y Oficial)

| Paso | Fuente Oficial | Herramienta Python | Acción | Estado |
| :-- | :-- | :-- | :-- | :-- |
| **1. Seed** | **Open Data BCN** (Parcelari) | `pandas` / `geopandas` | Descargar CSV, filtrar Gràcia, extraer lista de Refs. Catastrales | ✅ Implementado |
| **2. Enriquecer** | **Catastro SOAP** (Oficial) | `requests` + `xml.etree` o `zeep` | Iterar lista, pedir `Consulta_DNPRC`, parsear XML (Superficie/Año) | 🔄 Pendiente actualizar |
| **3. Validar** | **Portal Dades** (Edificios) | `pandas` | Comparar histograma de años de tu muestra vs. histograma oficial | ✅ Implementado |
| **4. Precios** | **Portal Dades** (Precios) | API REST + CSV | Obtener variable precio (2020-2025) | ✅ Implementado |
| **5. Contexto** | **Idescat API** | `requests` | Población por sección censal | 🔄 Pendiente |
| **6. Validación Alquiler** | **Incasòl** | `pandas` | Precios reales de cierre (CSV trimestral) | 🔄 Pendiente |

### Fuentes por Categoría

| Fuente | Uso en Proyecto | Método Preferido | Key Input | Key Output | Coste |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **CartoBCN** | Generar "Seed" (Lista de Edificios) | Descarga CSV/SHP | Bbox Gràcia | Lista `REF_CATASTR` | ✅ Gratis |
| **Catastro SOAP** | Enriquecer atributos físicos | SOAP XML (oficial) | `REF_CATASTR` | `m2`, `año`, `plantas` | ✅ Gratis |
| **Portal Dades** | Precios y validación | API REST + CSV | ID Dataset | `precio_m2`, `anio`, `barrio_id` | ✅ Gratis |
| **Idescat** | Contexto demográfico | API REST | Código postal | Población, edad | ✅ Gratis |
| **Incasòl** | Validación alquiler | CSV descarga | Municipio | Precios reales | ✅ Gratis |
| **Idealista** | Variable dependiente (Precio) | *Scraping* / Mock Data | Barrio | `Precio`, `m2`, `Hab` | ⚠️ Limitado (150 calls/mes) |

---

## 🎯 Ruta Recomendada para Spike (100% Gratuita y Oficial)

**Ruta viable confirmada**: 

**CartoBCN (Seed) → Catastro SOAP Oficial (Enriquecimiento) → Portal Dades (Validación)**

### Ventajas de este enfoque:
1. ✅ **Coste Cero**: No hay suscripciones ni freemiums limitados
2. ✅ **Sostenibilidad**: Usas fuentes oficiales que no van a desaparecer mañana
3. ✅ **Independencia**: No dependes de que un wrapper de terceros (`catastro-api.es`) cambie su política o caiga
4. ✅ **Legalidad**: Cumples con las condiciones de uso de datos públicos

### Flujo Implementado:

1. **Issue #199**: Extracción de precios Portal Dades
   - ✅ 1,268 registros extraídos (2020-2025, 5 barrios Gràcia)
   - ✅ Script: `extract_precios_gracia.py`
   - ✅ Notebook: `spike_gracia_portaldades_alquiler.ipynb`

2. **Issue #200**: Extracción atributos Catastro
   - ✅ Seed CSV generado: `gracia_refs_seed.csv` (60 referencias)
   - 🔄 Script actual: `extract_catastro_gracia.py` (usa catastro-api.es - **NO RECOMENDADO**)
   - 🔄 **Pendiente**: Actualizar para usar API SOAP oficial (gratuita)
   - ✅ Alternativa asíncrona: `catastro_oficial_client.py` (consulta masiva oficial)
   - ⚠️ **Recomendación**: Implementar cliente SOAP oficial para reemplazar dependencia de terceros

3. **Issue #201**: Linking y Cleaning
   - 🔄 Pendiente: Ejecutar tras completar Issue #200
   - Script: `link_and_clean_gracia.py`

---

## 📚 Referencias y Documentación

### Documentación Oficial

- **Catastro API**: https://catastro-api.es
- **Sede Electrónica Catastro**: https://www1.sedecatastro.gob.es
- **Portal Dades Barcelona**: https://opendata-ajuntament.barcelona.cat
- **Open Data BCN API**: https://opendata-ajuntament.barcelona.cat/es/desenvolupadors
- **Idescat API**: https://www.idescat.cat/dev/api/pob/?lang=en

### Documentación del Proyecto

- **Fuentes Catastro**: `spike-data-validation/docs/CATASTRO_DATA_SOURCES.md`
- **Cierre Issue #199**: `spike-data-validation/docs/ISSUE_199_CLOSURE_SUMMARY.md`
- **Scripts de Extracción**: `spike-data-validation/scripts/`

### Artículos y Referencias

- [Granada 2006 - Catastro](https://tig.age-geografia.es/wp-content/uploads/2021/09/Granada2006r.pdf)
- [Papers 66 - Metropoli](https://www.institutmetropoli.cat/wp-content/uploads/2024/05/Revista_Papers_66.pdf)
- [IEB Report 2024](https://ieb.ub.edu/wp-content/uploads/2025/04/DIG_IEB_Report_01-04_2024_ENG-CAS-CAT.pdf)

---

## 🔍 Validación de Accesos

### Endpoints Verificados

- ✅ Portal Dades API: Funcional (requiere `PORTALDADES_CLIENT_ID`)
- ✅ Catastro API (catastro-api.es): Funcional (requiere `CATASTRO_API_KEY`)
- ✅ Open Data BCN: Funcional (público)
- ⚠️ Idealista API: Restringido (requiere contrato B2B)
- ⚠️ Idescat API: Funcional (público, limitaciones de rate)

### Rate Limits Conocidos

- **Portal Dades**: 10 req/segundo
- **Catastro API**: ~1 req/segundo (tier gratuito: 100-500 calls/día)
- **Idealista**: 150 calls/mes (según reglas del proyecto)
- **Idescat**: Sin límite documentado (uso razonable)

---

**Última actualización**: 2025-12-17  
**Autor**: Equipo A - Data Infrastructure  
**Revisión**: Basado en investigación técnica y validación de endpoints

