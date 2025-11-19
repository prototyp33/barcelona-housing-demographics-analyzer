# URLs y Endpoints para Extracción de Datos

Este documento recopila las URLs directas y endpoints de API identificados para mejorar la eficiencia de la extracción de datos.

## 1. GeoJSON de Barrios/Distritos

### URLs Directas (Open Data BCN)
- **Barrios**: `https://opendata-ajuntament.barcelona.cat/resources/barrios.geojson`
- **Distritos**: `https://opendata-ajuntament.barcelona.cat/resources/distritos.geojson`

### Datasets CKAN (fallback)
- `20170706-districtes-barris`: "Administrative units of the city of Barcelona"
- `limits-municipals-districtes`: "Municipal and district limits"
- `barrios`: Dataset de barrios
- `distritos`: Dataset de distritos

**Nota**: Las URLs directas son más eficientes que buscar por API CKAN. El script intenta estas URLs primero.

---

## 2. Demografía Ampliada

### Open Data BCN (Padrón Municipal)
- **Portal**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/padro-municipal`
- **Datasets prioritarios**:
  - `pad_mdb_nacionalitat-contintent_edat-q_sexe`: Población por continente de nacionalidad, edad quinquenal y sexo
  - `pad_mdb_nacionalitat-g_edat-q_sexe`: Población por nacionalidad (España/UE/Resto), edad quinquenal y sexo
  - `pad_dom_mdbas_nacionalitat`: Hogares por nacionalidad

### IDESCAT API (Alternativa)
- **Portal principal**: `https://www.idescat.cat/tema/xifpo?lang=en`
- **API REST Base**: `https://api.idescat.cat/pob/v1/`
- **Documentación**: `https://www.idescat.cat/dev/api/pob/?lang=en`
- **Endpoint barrios Barcelona**:
  ```
  https://api.idescat.cat/pob/v1/barri?date=2023&id=080193&lang=es
  ```
  - `date=YYYY`: Año de referencia
  - `id=080193`: Código de Barcelona
  - `lang=es|ca|en`: Idioma

**Nota**: IDESCAT es útil como fuente alternativa o complementaria a Open Data BCN.

---

## 3. Renta Familiar Disponible

### Open Data BCN
- **Portal**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/renta-familiar-disponible`
- **URLs directas CSV** (si están disponibles):
  - `https://opendata-ajuntament.barcelona.cat/resources/rfd/rfd_municipi.csv`
  - `https://opendata-ajuntament.barcelona.cat/resources/rfd/rfd_barri.csv`
- **Datasets prioritarios**:
  - `renda-disponible-llars-bcn`: Renta disponible per cápita (€)
  - `atles-renda-mitjana`: Renta media por unidad de consumo
  - `atles-renda-mediana`: Renta mediana por unidad de consumo
  - `atles-renda-bruta-per-llar`: Renta bruta media por hogar

### INE (Alternativa)
- **Portal**: `https://www.ine.es/dyngs/INEbase/es/categoria.htm?c=Estadistica_P&cid=1254735573206`
- Encuesta de Condiciones de Vida (nacional y por zonas)

---

## 3.1. Tasa de Paro y Población Activa

### SEPE (Servicio Público de Empleo Estatal)
- **Portal Open Data**: `https://datos.gob.es/es/catalogo/ea0010401-paro-registrado`
- **Descarga**: CSV por municipio (filtrar luego por barrios)
- **Nota**: Requiere agregación a nivel barrio

### INE EPA (Encuesta de Población Activa)
- **Portal**: `https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176918&menu=resultados&secc=1254736194715&idp=1254735976595`
- Datos trimestrales y anuales

### Ajuntament (Movilidad/Empleo)
- **Portal**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/enquesta-mobilitat`
- Encuesta de movilidad (incluye datos de empleo)

---

## 3.2. Nivel Educativo

### IDESCAT Educación
- **Portal**: `https://www.idescat.cat/tema/educa?lang=en`
- **Datos por barrio/sección censal**: `https://www.idescat.cat/pub/?id=aec&n=115`
- **Descarga**: Excel/CSV por zona y año

### INE Educación
- **Portal**: `https://www.ine.es/jaxiT3/Datos.htm?t=22570`
- Datos por municipios

---

## 4. Oferta Inmobiliaria Actual

### Idealista API
- **Registro y docs**: `https://developers.idealista.com/`
- **Documentación API**: `https://developers.idealista.com/access-to-api`
- **Nota**: ⚠️ Requiere token de autenticación y registro previo
- **Endpoints**: Consultar documentación para parámetros de barrio, fecha, tipología, superficie

### Fotocasa Estadísticas
- **Portal**: `https://www.fotocasa.es/estadisticas/`
- Ofertas agregadas y análisis
- **Nota**: Puede requerir scraping o no tener API pública

---

## 5. Presión Turística (Airbnb)

### InsideAirbnb
- **Descarga directa**: `http://insideairbnb.com/get-the-data.html`
- Datos por ciudad y barrio (CSV): listings, calendar, reviews

### Registro Oficial (Ajuntament)
- **Portal**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/registre_habitatge_us_turistic`
- Registro oficial de viviendas de uso turístico

---

## 6. Vivienda Protegida

### INCASÒL
- **Portal**: `https://incasol.gencat.cat/ca/serveis/catalegdades/#`
- **Descarga**: Excel/CSV por segmento, año y zona
- Inventario y catálogo de vivienda protegida

### OHB (Observatori Metropolità de l'Habitatge)
- **Portal**: `https://www.ohb.cat/portal/es/dades/`
- Datos agregados de vivienda social por barrio

---

## 7. Calidad Ambiental

### Open Data BCN
- **Calidad del aire**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/qualitat-aire`
- **Mapa de ruido**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/mapa-ruido`
- **Zonas verdes**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/zones-verdes`

---

## 8. Movilidad

### ATM (Autoritat del Transport Metropolità)
- **Portal**: `https://www.atm.cat/web/ca/dades-obertes.php`
- Datasets sobre movilidad, uso de transporte y aforos

### Encuestas de Movilidad (Ajuntament)
- **Portal**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/enquesta-mobilitat`

---

## 9. Equipamientos y Servicios Urbanos

### Open Data BCN
- **Centros educativos**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/centres-educatius`
- **Centros de salud**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/centres-sanitaris`
- **Parques y jardines**: `https://opendata-ajuntament.barcelona.cat/data/es/dataset/parcs-i-jardins`

---

## Estrategia de Extracción

### Prioridad 1: URLs Directas
Siempre intentar URLs directas primero (más rápidas, menos llamadas API).

### Prioridad 2: IDs de Datasets Conocidos
Si las URLs directas fallan, usar IDs de datasets confirmados.

### Prioridad 3: Búsqueda por API
Solo como último recurso, buscar por palabras clave (limitado para evitar tiempos excesivos).

---

## Mejoras Implementadas

1. **GeoJSON**: URLs directas añadidas (`barrios.geojson`, `distritos.geojson`)
2. **IDESCAT API**: Extractor creado para datos demográficos alternativos
3. **Validación mejorada**: Verificación de formato GeoJSON antes de guardar
4. **Logging detallado**: Método usado (direct_url vs ckan_api) registrado en metadata

---

## 10. Estructura Física (Catastro)

### Catastro
- **Portal consulta web**: `https://www.sedecatastro.gob.es/`
- **Descarga de parcelas y superficie**: Petición formal o datos abiertos si los hay
- **Nota**: ⚠️ Puede requerir proceso formal de solicitud

---

## Próximos Pasos

### Implementados
- [x] URLs directas de GeoJSON
- [x] Extractor IDESCAT API
- [x] Documentación completa de URLs

### Pendientes (Prioridad Alta)
- [ ] Integrar extractor de InsideAirbnb (descarga directa)
- [ ] Probar URLs directas de renta (`rfd_barri.csv`, `rfd_municipi.csv`)
- [ ] Agregar extractores para Open Data BCN adicionales (calidad ambiental, equipamientos)

### Pendientes (Prioridad Media)
- [ ] Extractor para datos de paro (SEPE/INE)
- [ ] Extractor para nivel educativo (IDESCAT/INE)
- [ ] Integrar datos de vivienda protegida (INCASÒL/OHB)

### Pendientes (Requieren Autenticación/Proceso Especial)
- [ ] Idealista API (requiere token)
- [ ] Catastro (puede requerir solicitud formal)
- [ ] Documentar estructura de respuesta de IDESCAT API

