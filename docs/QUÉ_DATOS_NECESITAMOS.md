# ¿Qué Datos Necesitamos? (Lenguaje Natural)

Este documento explica en términos claros qué información necesitamos para entender mejor la relación entre demografía y precios de vivienda en Barcelona.

---

## 1. Conocer la Población Real de Barcelona

### ¿Qué queremos saber?
- **Cuántas personas viven en cada barrio** (no solo estimaciones)
- **Cómo ha cambiado la población año a año** (¿aumenta o disminuye?)
- **La estructura por edades real** (no la edad de los edificios, sino de las personas)

### ¿Por qué es importante?
- Si un barrio tiene mucha población joven, puede haber más demanda de alquiler
- Si la población está envejeciendo, puede haber menos movimiento de vivienda
- Los cambios bruscos de población pueden explicar cambios en precios

### Requisitos Específicos:

#### Población Total
- **Granularidad temporal**: Año completo (1 de enero de cada año)
- **Rango necesario**: 2015-2024 (mínimo), idealmente 2010-2024 para ver tendencias
- **Granularidad geográfica**: Por barrio (73 barrios de Barcelona)
- **Valor exacto**: Número total de personas empadronadas/residentes
- **Fuente preferida**: Padrón Municipal (INE) o datos oficiales del Ajuntament
- **Formato**: CSV o API con columnas: `barrio_id`, `anio`, `poblacion_total`

#### Estructura por Edades
- **Granularidad temporal**: Año completo
- **Rango necesario**: 2015-2024
- **Grupos de edad requeridos**: 
  - 0-17 años (menores)
  - 18-34 años (jóvenes adultos)
  - 35-49 años (adultos)
  - 50-64 años (maduros)
  - 65+ años (mayores)
- **Formato**: CSV con columnas: `barrio_id`, `anio`, `edad_grupo`, `poblacion`
- **Alternativa aceptable**: Edad media real (no proxy de edificios)

#### Población por Sexo
- **Estado actual**: Ya tenemos parcialmente (hombres/mujeres)
- **Necesitamos validar**: Que los datos sean oficiales y completos
- **Rango**: 2015-2024

**NO nos vale**:
- ❌ Solo un año (necesitamos serie temporal)
- ❌ Solo a nivel distrito (necesitamos barrio)
- ❌ Estimaciones o proyecciones sin datos reales
- ❌ Datos trimestrales o mensuales (solo anual)

---

## 2. Entender la Estructura de los Hogares

### ¿Qué queremos saber?
- **Cuántos hogares hay en cada barrio** (ya lo tenemos, pero queremos validarlo)
- **Cuántas personas viven en cada hogar** (hogares unipersonales vs familias grandes)
- **Tipo de hogar** (parejas con hijos, personas solas, compartido, etc.)

### ¿Por qué es importante?
- Los hogares unipersonales suelen buscar pisos más pequeños
- Las familias necesitan más espacio, lo que afecta la demanda
- El tamaño del hogar influye en la capacidad de pago

### Requisitos Específicos:

#### Número Total de Hogares
- **Estado actual**: Ya tenemos (calculado desde Portal de Dades)
- **Necesitamos validar**: Comparar con datos oficiales del Censo/INE
- **Rango**: 2015-2024
- **Granularidad**: Por barrio y año

#### Desglose por Tamaño de Hogar
- **Categorías necesarias**:
  - 1 persona (unipersonal)
  - 2 personas (pareja sin hijos)
  - 3 personas
  - 4 personas
  - 5+ personas
- **Granularidad temporal**: Año completo
- **Rango**: 2015-2024 (mínimo), idealmente desde 2010
- **Formato**: CSV con columnas: `barrio_id`, `anio`, `tamano_hogar`, `numero_hogares`
- **Fuente**: Censo de Población y Viviendas (INE) o Portal de Dades equivalente

#### Tipo de Hogar (Opcional pero deseable)
- **Categorías**: 
  - Unipersonal
  - Pareja sin hijos
  - Pareja con hijos
  - Monoparental
  - Otros (compartido, etc.)
- **Prioridad**: Media (no crítica pero útil)

**NO nos vale**:
- ❌ Solo el total sin desglose (ya lo tenemos)
- ❌ Solo a nivel distrito
- ❌ Datos de un solo año

---

## 3. Conocer el Origen y Movilidad de la Población

### ¿Qué queremos saber?
- **De dónde viene la gente que compra vivienda** (españoles vs extranjeros)
- **Cuánta población inmigrante hay en cada barrio**
- **Movimientos migratorios internos** (¿la gente se muda entre barrios?)

### ¿Por qué es importante?
- La compra de vivienda por extranjeros puede afectar los precios
- Los barrios con más diversidad pueden tener dinámicas diferentes
- La movilidad interna muestra qué barrios son más atractivos

### Requisitos Específicos:

#### Población Extranjera
- **¿Qué necesitamos exactamente?**
  - **Número de personas extranjeras** por barrio (no solo porcentaje)
  - **Porcentaje de población extranjera** sobre total
  - **Población nacida fuera de España** (puede incluir españoles nacidos fuera)
  
- **Granularidad temporal**: Año completo (1 de enero)
- **Rango necesario**: 2015-2024
- **Granularidad geográfica**: Por barrio
- **Fuente**: Padrón Municipal (INE), Portal de Dades

- **Estado actual**: Ya tenemos proxy desde compras de vivienda, pero necesitamos datos oficiales de población

- **Formato**: CSV con columnas: `barrio_id`, `anio`, `poblacion_extranjera`, `porc_extranjeros`, `poblacion_nacida_extranjero`

#### Nacionalidad de Compradores (Ya tenemos parcialmente)
- **Estado**: Ya tenemos datos de compras por nacionalidad desde Portal de Dades
- **Necesitamos validar**: Que los datos sean completos y consistentes
- **Mejora deseable**: Desglose por país de origen (no solo español/extranjero)

#### Movilidad Interna (Cambios de Residencia)
- **¿Qué necesitamos?**
  - **Flujos de entrada** (personas que se mudan a cada barrio desde otro barrio)
  - **Flujos de salida** (personas que se mudan desde cada barrio a otro)
  - **Saldo migratorio interno** (entradas - salidas)
  
- **Granularidad temporal**: Año
- **Rango**: 2015-2024
- **Fuente**: Padrón Municipal (cambios de residencia), Ajuntament

**NO nos vale**:
- ❌ Solo porcentaje sin número absoluto
- ❌ Solo un año (necesitamos evolución)
- ❌ Solo a nivel distrito

---

## 4. Entender la Situación Económica de los Barrios

### ¿Qué queremos saber?
- **Cuánto dinero gana la gente en cada barrio** (renta disponible)
- **Cuántas personas están en paro**
- **Nivel educativo de la población**

### ¿Por qué es importante?
- La renta determina qué pueden pagar por vivienda
- Barrios con más paro pueden tener menos demanda
- El nivel educativo se relaciona con ingresos y preferencias de vivienda

### Requisitos Específicos:

#### Renta Familiar Disponible
- **¿Qué necesitamos exactamente?**
  - **Renta disponible media por hogar** (después de impuestos)
  - **Renta disponible mediana** (más robusta que la media)
  - **Renta per cápita** (renta total / número de personas)
  
- **Granularidad temporal**: Año completo
- **Rango necesario**: 2015-2024 (mínimo), idealmente desde 2010
- **Granularidad geográfica**: Por barrio (73 barrios)
- **Unidad**: Euros anuales
- **Fuente preferida**: 
  - Ajuntament (Renta Familiar Disponible)
  - INE (Encuesta de Condiciones de Vida)
  - Generalitat (datos fiscales agregados)

- **Formato**: CSV con columnas: `barrio_id`, `anio`, `renta_media_hogar`, `renta_mediana_hogar`, `renta_per_capita`

**NO nos vale**:
- ❌ Solo un año (necesitamos serie temporal)
- ❌ Solo a nivel distrito
- ❌ Renta bruta sin descontar impuestos
- ❌ Solo percentiles sin media/mediana

#### Tasa de Paro
- **¿Qué necesitamos?**
  - **Tasa de paro** (porcentaje de población activa en paro)
  - **Número de parados** (absoluto)
  - **Población activa** (ocupados + parados)
  
- **Granularidad temporal**: 
  - **Mínimo**: Año (promedio anual)
  - **Ideal**: Trimestral para ver tendencias
- **Rango**: 2015-2024
- **Granularidad geográfica**: Por barrio
- **Fuente**: SEPE (Servicio Público de Empleo Estatal) o INE

#### Nivel Educativo
- **Categorías necesarias**:
  - Sin estudios / Primaria incompleta
  - Primaria completa
  - Secundaria (ESO)
  - Bachillerato / FP
  - Universitaria (grado)
  - Universitaria (postgrado)
- **Granularidad temporal**: Año (puede ser cada 2-3 años, cambia poco)
- **Rango**: 2015-2024
- **Formato**: Porcentaje de población por nivel educativo
- **Fuente**: Censo, Encuesta de Población Activa (EPA)

---

## 5. Conocer el Mercado Inmobiliario en Tiempo Real

### ¿Qué queremos saber?
- **Qué pisos están en venta ahora** (oferta actual)
- **Cuánto tiempo tardan en venderse** (días en mercado)
- **Precios de oferta vs precios de venta real** (¿hay negociación?)

### ¿Por qué es importante?
- La oferta actual muestra la disponibilidad real
- El tiempo en mercado indica si hay mucha o poca demanda
- La diferencia entre oferta y venta muestra la presión del mercado

### Requisitos Específicos:

#### Oferta de Vivienda en Venta
- **¿Qué necesitamos exactamente?**
  - **Número de anuncios activos** por barrio (snapshot mensual o trimestral)
  - **Precio medio de oferta** por m²
  - **Precio medio de oferta total** (para viviendas completas)
  - **Tipología**: Estudio, 1 hab, 2 hab, 3 hab, 4+ hab
  - **Superficie media** de las viviendas en oferta
  
- **Granularidad temporal**: 
  - **Mínimo**: Mensual (último día del mes)
  - **Ideal**: Semanal para ver cambios rápidos
  - **Rango necesario**: 2020-2024 (mínimo), idealmente desde 2015
  
- **Granularidad geográfica**: Por barrio

- **Fuentes posibles**:
  - Idealista API (si está disponible)
  - Fotocasa (scraping si es legal)
  - Portal Inmobiliario (datos agregados)

- **Formato**: CSV con columnas: `barrio_id`, `fecha` (año-mes), `num_anuncios`, `precio_m2_media`, `precio_total_media`, `superficie_media`, `tipologia`

**NO nos vale**:
- ❌ Solo datos de un día (necesitamos serie temporal)
- ❌ Solo precio sin número de anuncios
- ❌ Solo a nivel distrito

#### Tiempo en Mercado
- **¿Qué necesitamos?**
  - **Días medio en mercado** (desde publicación hasta venta)
  - **Tasa de rotación** (anuncios vendidos / anuncios publicados)
  
- **Granularidad temporal**: Mensual o trimestral
- **Rango**: 2020-2024
- **Fuente**: Idealista, portales inmobiliarios

#### Precio de Oferta vs Venta Real
- **¿Qué necesitamos?**
  - **Diferencia porcentual** entre precio de oferta y precio de venta
  - **Ratio oferta/venta** por barrio
- **Granularidad temporal**: Trimestral o anual
- **Rango**: 2015-2024
- **Fuente**: Comparar datos de portales (oferta) con registros notariales (venta real)

---

## 6. Entender la Oferta de Vivienda Pública y Protegida

### ¿Qué queremos saber?
- **Cuánta vivienda protegida hay en cada barrio**
- **Cuántos contratos de alquiler social se firman**
- **Qué barrios tienen más vivienda pública**

### ¿Por qué es importante?
- La vivienda protegida afecta los precios del mercado libre
- Muestra políticas públicas de acceso a vivienda
- Puede explicar diferencias de precios entre barrios similares

### Requisitos Específicos:

#### Stock de Vivienda Protegida
- **¿Qué necesitamos exactamente?**
  - **Número total de viviendas protegidas** por barrio (stock acumulado)
  - **Viviendas de Protección Oficial (VPO)** vs **Vivienda de Alquiler Social**
  - **Viviendas nuevas** añadidas cada año
  
- **Granularidad temporal**: 
  - **Stock**: Año (valor acumulado a 31 de diciembre)
  - **Nuevas viviendas**: Año (viviendas entregadas ese año)
- **Rango necesario**: 2015-2024
- **Granularidad geográfica**: Por barrio
- **Fuente**: INCASÒL, Generalitat, Ajuntament (registro de vivienda protegida)

- **Formato**: CSV con columnas: `barrio_id`, `anio`, `stock_vpo`, `stock_alquiler_social`, `nuevas_vpo_anio`, `nuevas_alquiler_social_anio`

#### Contratos de Alquiler Social
- **¿Qué necesitamos?**
  - **Contratos nuevos firmados** cada año por barrio
  - **Contratos activos** (total acumulado)
  - **Precio medio del alquiler social** (para comparar con mercado libre)
  
- **Granularidad temporal**: Año
- **Rango**: 2015-2024
- **Fuente**: INCASÒL, Ajuntament

**NO nos vale**:
- ❌ Solo datos de un año (necesitamos evolución)
- ❌ Solo a nivel distrito
- ❌ Solo número total sin distinguir VPO vs alquiler social

---

## 7. Conocer la Presión Turística y Movilidad

### ¿Qué queremos saber?
- **Cuántos turistas hay en cada barrio** (plazas hoteleras, Airbnb)
- **Cuánta gente se desplaza diariamente** (movilidad laboral)
- **Accesibilidad** (metro, buses, tiempo al centro)

### ¿Por qué es importante?
- El turismo puede desplazar residentes (efecto Airbnb)
- La movilidad afecta la demanda de vivienda (¿dónde quiere vivir la gente que trabaja en X?)
- La accesibilidad influye en el precio

### Requisitos Específicos:

#### Alojamientos Airbnb
- **¿Qué necesitamos exactamente?**
  - **Número de propiedades listadas** por barrio (no solo las activas)
  - **Propiedades operativas todo el año** (más de 180 días/año) vs estacionales
  - **Número de plazas/camas** disponibles
  - **Ocupación media anual** (días ocupados / días disponibles)
  
- **Granularidad temporal**: 
  - **Mínimo**: Año completo (promedio anual)
  - **Ideal**: Mensual para ver estacionalidad
  - **Rango necesario**: 2015-2024 (mínimo), idealmente desde 2010
  
- **Granularidad geográfica**: Por barrio (73 barrios)

- **Datos críticos**:
  - **Propiedades de uso turístico exclusivo** (no vivienda habitual del propietario)
  - **Propiedades que operan >180 días/año** (indican uso turístico intensivo)
  - **Distinguir**: Vivienda completa vs habitación compartida

- **Fuentes posibles**:
  - InsideAirbnb (datos agregados por barrio)
  - Datos del Ajuntament (registro de viviendas turísticas)
  - Scraping de Airbnb (si es legal y ético)

- **Formato esperado**: CSV con columnas: `barrio_id`, `anio`, `mes` (opcional), `propiedades_total`, `propiedades_operativas_anual`, `plazas_totales`, `ocupacion_media`

**NO nos vale**:
- ❌ Solo número total sin distinguir uso anual vs estacional
- ❌ Solo datos de un mes o temporada (necesitamos anual)
- ❌ Solo a nivel distrito (necesitamos barrio)
- ❌ Datos que no distingan vivienda turística de vivienda habitual

#### Hoteles y Alojamientos Regulados
- **Datos necesarios**:
  - Número de establecimientos por barrio
  - Plazas hoteleras totales
  - Ocupación media anual
- **Rango**: 2015-2024
- **Fuente**: Ajuntament (registro de establecimientos turísticos)

#### Movilidad Diaria
- **¿Qué necesitamos?**
  - Flujos origen-destino por barrio (¿de dónde viene y a dónde va la gente que trabaja?)
  - Modo de transporte (coche, transporte público, bici, a pie)
  - Tiempo medio de desplazamiento
- **Granularidad temporal**: Año (promedio anual)
- **Rango**: 2015-2024
- **Fuente**: Encuesta de Movilidad (Ajuntament) o datos de transporte público

#### Accesibilidad
- **Datos necesarios**:
  - Tiempo medio al centro (Plaza Catalunya) en transporte público
  - Número de estaciones de metro/bus por barrio
  - Frecuencia de transporte público
- **Granularidad temporal**: Puede ser estático (cambia poco año a año)
- **Fuente**: TMB, Ajuntament

---

## 8. Entender la Calidad del Entorno

### ¿Qué queremos saber?
- **Cómo es de contaminado cada barrio** (calidad del aire)
- **Cuánto ruido hay** (contaminación acústica)
- **Cuántas zonas verdes hay** (parques, jardines)

### ¿Por qué es importante?
- La calidad ambiental afecta el precio de vivienda
- Barrios más verdes suelen ser más caros
- La contaminación puede hacer que la gente se vaya

### Requisitos Específicos:

#### Calidad del Aire
- **¿Qué necesitamos exactamente?**
  - **Índice de calidad del aire** (ICA) o **concentración de NO2, PM10, PM2.5**
  - **Valor medio anual** (no solo picos)
  - **Días con calidad del aire "mala" o "muy mala"** por año
  
- **Granularidad temporal**: 
  - **Mínimo**: Año (promedio anual)
  - **Ideal**: Mensual para ver estacionalidad
- **Rango**: 2015-2024
- **Granularidad geográfica**: Por barrio (puede requerir interpolación desde estaciones)
- **Fuente**: Ajuntament (Xarxa de Vigilància i Previsió de la Contaminació Atmosfèrica), Agencia de Salut Pública

- **Formato**: CSV con columnas: `barrio_id`, `anio`, `ica_medio`, `no2_medio`, `pm10_medio`, `dias_calidad_mala`

#### Contaminación Acústica
- **¿Qué necesitamos?**
  - **Nivel de ruido medio** (decibelios, dB)
  - **Ruido diurno** (7h-23h) vs **ruido nocturno** (23h-7h)
  - **Superación de límites legales** (días/año)
  
- **Granularidad temporal**: Año (promedio anual)
- **Rango**: 2015-2024
- **Fuente**: Ajuntament (mapa de ruido)

#### Zonas Verdes
- **¿Qué necesitamos?**
  - **Superficie de zonas verdes** (m²) por barrio
  - **Superficie por habitante** (m²/hab)
  - **Número de parques/jardines** por barrio
  - **Accesibilidad** (distancia media desde viviendas al parque más cercano)
  
- **Granularidad temporal**: Puede ser estático (cambia poco año a año)
- **Fuente**: Ajuntament (catálogo de zonas verdes)

**NO nos vale**:
- ❌ Solo datos puntuales sin promedio anual
- ❌ Solo a nivel distrito
- ❌ Solo índices sin valores absolutos (NO2, PM10)

---

## 9. Conocer la Estructura Física de los Barrios

### ¿Qué queremos saber?
- **Cómo son los edificios** (antigüedad, estado, altura)
- **Cuánto espacio hay** (superficie construida, densidad)
- **Qué servicios hay** (escuelas, hospitales, comercios)

### ¿Por qué es importante?
- Edificios antiguos pueden ser más baratos pero requieren más mantenimiento
- La densidad afecta la calidad de vida
- Los servicios cercanos aumentan el valor

### ¿Qué datos específicos necesitamos?
- Edad media de edificios (ya tenemos proxy)
- Estado de conservación de edificios
- Superficie construida vs superficie de suelo (ya tenemos parcialmente)
- Equipamientos por barrio (escuelas, centros de salud, etc.)

---

## 10. Tener Información Geográfica Visual

### ¿Qué queremos saber?
- **Dónde están exactamente los barrios** (mapas, límites)
- **Cómo se relacionan espacialmente** (barrios vecinos)
- **Distancia entre barrios** (no solo administrativa, sino real)

### ¿Por qué es importante?
- Permite hacer mapas y visualizaciones
- Muestra patrones espaciales (¿barrios caros están juntos?)
- Facilita análisis geográficos avanzados

### Requisitos Específicos:

#### GeoJSON de Barrios
- **¿Qué necesitamos exactamente?**
  - **Límites geográficos** de cada uno de los 73 barrios (polígonos)
  - **Formato**: GeoJSON estándar (WGS84, EPSG:4326)
  - **Precisión**: Suficiente para visualización a nivel ciudad (no necesita precisión de cm)
  
- **Estructura requerida**:
  ```json
  {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "properties": {
          "barrio_id": 1,
          "barrio_nombre": "el Raval",
          "distrito_id": 1,
          "distrito_nombre": "Ciutat Vella"
        },
        "geometry": {
          "type": "Polygon",
          "coordinates": [[[lon, lat], [lon, lat], ...]]
        }
      }
    ]
  }
  ```

- **Datos adicionales deseables**:
  - **Centroide** (punto central) de cada barrio
  - **Superficie real** en km² (calculable desde el polígono)
  - **Relaciones de vecindad** (qué barrios comparten frontera)

- **Fuentes posibles**:
  - Open Data BCN (CartoBCN)
  - Ajuntament (servicios de mapas)
  - IDESCAT (si tiene datos geográficos)
  - OpenStreetMap (extraer límites administrativos)

- **Actualización**: Puede ser estático (los límites de barrios cambian muy poco)

**NO nos vale**:
- ❌ Solo coordenadas de centroide sin límites
- ❌ Formato diferente a GeoJSON (Shapefile es aceptable si se convierte)
- ❌ Solo algunos barrios (necesitamos los 73)
- ❌ Sistema de coordenadas diferente sin conversión

---

## Resumen: ¿Para Qué Queremos Todo Esto?

### Preguntas que queremos responder:

1. **¿Por qué algunos barrios son más caros que otros?**
   - ¿Es por la renta de sus habitantes?
   - ¿Es por la calidad del entorno?
   - ¿Es por la presión turística?

2. **¿Cómo ha cambiado Barcelona en los últimos años?**
   - ¿Qué barrios han subido más de precio?
   - ¿Dónde se ha concentrado la población?
   - ¿Hay gentrificación? ¿Dónde?

3. **¿Qué factores predicen mejor el precio de vivienda?**
   - ¿La renta?
   - ¿La demografía?
   - ¿La accesibilidad?
   - ¿La calidad ambiental?

4. **¿Qué barrios son más vulnerables a cambios de precio?**
   - ¿Dónde hay más presión turística?
   - ¿Dónde hay más población en riesgo?
   - ¿Dónde hay menos vivienda protegida?

### Con estos datos podremos:

- **Entender mejor** la relación entre demografía y precios
- **Predecir tendencias** de precios basándose en cambios demográficos
- **Identificar barrios** con riesgo de gentrificación o abandono
- **Informar políticas públicas** sobre vivienda y urbanismo
- **Ayudar a ciudadanos** a tomar decisiones informadas sobre dónde vivir

---

## Priorización: ¿Por Dónde Empezar?

### 🔴 Prioridad Máxima (Ya tenemos parcialmente)
1. **Censo y población real** - Base fundamental
2. **GeoJSON de barrios** - Necesario para visualizaciones
3. **Renta por barrio** - Explica mucho de los precios

### 🟡 Prioridad Alta (Muy útiles)
4. **Oferta inmobiliaria actual** - Muestra el mercado real
5. **Presión turística** - Factor importante en Barcelona
6. **Vivienda protegida** - Contexto de políticas públicas

### 🟢 Prioridad Media (Complementarios)
7. **Calidad ambiental** - Factor de calidad de vida
8. **Movilidad** - Explica preferencias de ubicación
9. **Equipamientos** - Afecta el valor percibido

---

*Última actualización: 2025-11-13*

