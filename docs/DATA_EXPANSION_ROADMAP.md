# 📊 Roadmap de Ampliación de Datos - Barcelona Housing Analytics

## Estado Actual (Noviembre 2025)

### Inventario de Datos

| Tabla | Registros | Cobertura | Estado |
|-------|-----------|-----------|--------|
| `dim_barrios` | 73 | 100% (73/73 barrios) | ✅ Completo |
| `fact_precios` | 6,358 | 2012-2025 (14 años) | ✅ Bueno |
| `fact_demografia` | 657 | 2015-2023 (9 años) | ✅ Bueno |
| `fact_demografia_ampliada` | 2,256 | 2025 (desglose edad/sexo/nacionalidad) | ⚠️ Solo 1 año |
| `fact_renta` | 73 | 2022 (1 año) | ❌ Crítico |
| `fact_oferta_idealista` | 0 | Vacía | ❌ Sin datos |

### Gaps Críticos Identificados

1. **Renta histórica**: Solo tenemos datos de 2022. No podemos analizar evolución de asequibilidad.
2. **Alquiler escaso**: Solo ~70 registros/año vs ~420 de venta.
3. **Oferta actual vacía**: Sin datos de Idealista (requiere API key).
4. **Sin datos de transacciones reales**: Solo precios medios, no volumen de operaciones.

---

## 🎯 Roadmap de Sprints (S0-S8)

### PRIORIDAD ALTA: Métricas de Asequibilidad

## S1: Implementar Extractor de Renta Histórica (IDESCAT)

**Objetivo**: Extraer y almacenar datos históricos de renta familiar disponible bruta desde IDESCAT para calcular métricas de asequibilidad (esfuerzo de compra, esfuerzo de alquiler, tendencias de asequibilidad).

**Fuente**: IDESCAT - [Renda familiar disponible bruta](https://www.idescat.cat/pub/?id=aec&n=893)

**KPI**: Cobertura de 2015-2022 (8 años) con datos a nivel municipal y, cuando sea posible, por distrito. Tabla `fact_renta` con ≥80% de registros completos para el período.

**Entregables**:
- Crear `IDESCATExtractor` en `src/extraction/idescat.py` heredando de `BaseExtractor`
- Implementar método `extract_renta_familiar(year_start, year_end)` usando API de IDESCAT
- Migrar schema: `ALTER TABLE fact_renta ADD COLUMN anio INTEGER` y columnas necesarias para años históricos
- Actualizar pipeline ETL en `src/data_processing.py` para procesar nuevos datos
- Crear tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`
- Crear KPI "Índice de Asequibilidad" en dashboard Streamlit

**Indicador**: Renta familiar disponible bruta per cápita  
**Cobertura**: 2015-2022 (municipal, algunos años por distrito)  
**Granularidad**: Municipal → Distritos → Barrios (interpolación)

**Impacto**: Permitiría calcular:
- **Esfuerzo de compra histórico**: `(Precio vivienda 70m²) / (Renta anual * años)`
- **Esfuerzo de alquiler**: `(Alquiler mensual) / (Renta mensual)`
- **Tendencia de asequibilidad**: ¿Está mejorando o empeorando?

---

## S2: Implementar Extractor de Precios de Alquiler (Incasòl)

**Objetivo**: Enriquecer `fact_precios` con datos de alquiler más granulares desde Incasòl para llenar el gap actual (solo 13.6% de registros son de alquiler).

**Fuente**: Incasòl - [Observatori de l'Habitatge](https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/)

**KPI**: Aumentar registros de alquiler de 866 a 3,000+ registros. Cobertura trimestral 2014-2024 a nivel barrio.

**Entregables**:
- Añadir dataset Incasòl a `OpenDataBCNExtractor` o crear extractor específico `IncasolExtractor`
- Enriquecer `fact_precios` con datos de alquiler más granulares (precio medio €/m² y €/mes)
- Actualizar visualizaciones de alquiler en dashboard
- Tests unitarios con ≥80% coverage
- Documentar fuente en `docs/DATA_SOURCES.md`

**Indicador**: Precio medio alquiler €/m² y €/mes  
**Cobertura**: 2014-2024 (trimestral)  
**Granularidad**: Municipio → Distrito → Barrio

**Impacto**: Llenar el gap de datos de alquiler (actualmente solo 13.6% de fact_precios).

---

### PRIORIDAD MEDIA: Contexto Socioeconómico

## S3: Implementar Extractor de Tasa de Paro por Barrio

**Objetivo**: Extraer datos de paro registrado por barrio para correlacionar con precios y identificar barrios vulnerables.

**Fuente**: Barcelona Economia - [Atur registrat](https://ajuntament.barcelona.cat/estadistica/catala/Estadistiques_per_territori/Barris/Treball_i_Trets_economics/Atur/index.htm)

**KPI**: Cobertura mensual 2012-2024 a nivel barrio. Nueva tabla `fact_socioeconomico` con columna `tasa_paro`.

**Entregables**:
- Crear nueva tabla `fact_socioeconomico` en `src/database_setup.py` (paro, educación, hogares)
- Crear extractor para datos de Barcelona Economia o integrar en `OpenDataBCNExtractor`
- Extraer datos de paro registrado mensual por barrio
- Crear tab "Vulnerabilidad" en dashboard Streamlit
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Personas en paro registrado  
**Cobertura**: 2012-2024 (mensual)  
**Granularidad**: Barrio

**Impacto**: Correlacionar paro con precios → identificar barrios vulnerables.

---

## S4: Implementar Extractor de Nivel de Estudios

**Objetivo**: Extraer datos de población por nivel educativo para analizar correlación con precios y detectar gentrificación educativa.

**Fuente**: Open Data BCN - [Nivell d'estudis](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/est-padro-nivell-estudis)

**KPI**: Cobertura 2015-2023 a nivel barrio. Datos desglosados por nivel (primaria, secundaria, universitario).

**Entregables**:
- Añadir columna `nivel_estudios` a `fact_socioeconomico` o crear tabla específica
- Integrar dataset en `OpenDataBCNExtractor` usando CKAN API
- Extraer datos de población por nivel educativo por barrio
- Actualizar visualizaciones en dashboard (correlación educación-precios)
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Población por nivel educativo (primaria, secundaria, universitario)  
**Cobertura**: 2015-2023  
**Granularidad**: Barrio

**Impacto**: Correlacionar educación con precios → gentrificación educativa.

---

## S5: Implementar Extractor de Estructura de Hogares

**Objetivo**: Extraer datos de hogares por tamaño para analizar demanda de tipología de vivienda (estudios vs pisos grandes).

**Fuente**: Open Data BCN - [Llars segons grandària](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/est-padro-llars-grandaria)

**KPI**: Cobertura 2015-2023 a nivel barrio. Datos desglosados por tamaño (1, 2, 3, 4+ personas).

**Entregables**:
- Añadir columna `estructura_hogares` a `fact_socioeconomico` o crear tabla específica
- Integrar dataset en `OpenDataBCNExtractor` usando CKAN API
- Extraer datos de hogares por tamaño por barrio
- Actualizar visualizaciones en dashboard (demanda por tipología)
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Hogares por tamaño (1, 2, 3, 4+ personas)  
**Cobertura**: 2015-2023  
**Granularidad**: Barrio

**Impacto**: Demanda de tipología de vivienda (estudios vs pisos grandes).

---

### PRIORIDAD BAJA: Enriquecimiento Avanzado

## S6: Implementar Extractor de Transacciones Inmobiliarias (Registradores)

**Objetivo**: Extraer datos de compraventas reales desde el Colegio de Registradores para analizar volumen de mercado, no solo precios.

**Fuente**: Colegio de Registradores - [Estadística Registral](https://www.registradores.org/actualidad/portal-estadistico-registral/estadisticas-de-propiedad)

**KPI**: Cobertura trimestral 2007-2024 a nivel municipio (Barcelona ciudad). Nueva tabla `fact_transacciones` con número de compraventas, precio medio, superficie.

**Entregables**:
- Crear nueva tabla `fact_transacciones` en `src/database_setup.py`
- Crear extractor `RegistradoresExtractor` para datos del Colegio de Registradores
- Extraer datos trimestrales de compraventas (número, precio medio, superficie)
- Actualizar visualizaciones en dashboard (volumen de mercado)
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Número de compraventas, precio medio, superficie  
**Cobertura**: 2007-2024 (trimestral)  
**Granularidad**: Provincia → Municipio (Barcelona ciudad)

**Impacto**: Volumen de mercado, no solo precios.

---

## S7: Implementar Extractor de Licencias de Obra / Rehabilitación

**Objetivo**: Extraer datos de licencias urbanísticas para predecir oferta futura y detectar gentrificación.

**Fuente**: Open Data BCN - [Llicències urbanístiques](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/llicencies-urbanistiques)

**KPI**: Cobertura 2010-2024 a nivel barrio. Datos desglosados por tipo (obra nueva, rehabilitación, cambio de uso).

**Entregables**:
- Crear nueva tabla `fact_licencias` en `src/database_setup.py`
- Integrar dataset en `OpenDataBCNExtractor` usando CKAN API
- Extraer datos de licencias por tipo y barrio
- Actualizar visualizaciones en dashboard (predictor de oferta futura)
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Licencias de obra nueva, rehabilitación, cambio de uso  
**Cobertura**: 2010-2024  
**Granularidad**: Barrio

**Impacto**: Predictor de oferta futura y gentrificación.

---

## S8: Implementar Extractor de Pisos Turísticos (HUT)

**Objetivo**: Extraer datos de Habitaciones de Uso Turístico (HUT) para analizar presión turística sobre mercado residencial.

**Fuente**: Open Data BCN - [Habitatges d'ús turístic](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/habitatges-us-turistic)

**KPI**: Cobertura 2016-2024 a nivel barrio con coordenadas. Nueva tabla `fact_hut` con número de HUTs por barrio.

**Entregables**:
- Crear nueva tabla `fact_hut` en `src/database_setup.py`
- Integrar dataset en `OpenDataBCNExtractor` usando CKAN API
- Extraer datos de HUTs por barrio (con coordenadas si están disponibles)
- Actualizar visualizaciones en dashboard (presión turística)
- Tests unitarios con ≥80% coverage
- Documentar en `docs/DATA_SOURCES.md`

**Indicador**: Número de HUTs por barrio  
**Cobertura**: 2016-2024  
**Granularidad**: Barrio (con coordenadas)

**Impacto**: Presión turística sobre mercado residencial.

---

## S0: Setup Inicial y Preparación

**Objetivo**: Preparar infraestructura y documentación base para los sprints de ampliación de datos.

**Fuente**: Internal

**KPI**: Documentación completa, estructura de base de datos preparada, tests de integración pasando.

**Entregables**:
- Revisar y actualizar `docs/DATA_EXPANSION_ROADMAP.md` con formato de sprints
- Verificar que `src/database_setup.py` soporte nuevas tablas
- Crear estructura base para nuevos extractores en `src/extraction/`
- Documentar proceso de creación de extractores en `docs/DEVELOPMENT.md`
- Configurar CI/CD para validar nuevos extractores
- Crear template de issue para nuevos sprints

---

## 📈 Nuevos Análisis Posibles

### Con Datos Actuales (Ya implementables)

| Análisis | Datos Necesarios | Estado |
|----------|------------------|--------|
| Mapa de precios por barrio | `fact_precios` | ✅ Implementado |
| Evolución temporal de precios | `fact_precios` | ✅ Implementado |
| Correlación precio-envejecimiento | `fact_precios` + `fact_demografia` | ✅ Implementado |
| Ranking de barrios más caros | `fact_precios` | ✅ Implementado |
| Yield bruto (rentabilidad alquiler) | `fact_precios` (venta + alquiler) | ✅ Implementado |

### Con Ampliación Prioridad Alta

| Análisis | Datos Necesarios | Impacto Ciudadano |
|----------|------------------|-------------------|
| **Índice de Asequibilidad** | Renta histórica + Precios | ⭐⭐⭐⭐⭐ |
| Años de salario para comprar | Renta + Precio venta | ⭐⭐⭐⭐⭐ |
| % de renta destinado a alquiler | Renta + Alquiler | ⭐⭐⭐⭐⭐ |
| Mapa de "zonas de exclusión" | Asequibilidad < 30% | ⭐⭐⭐⭐⭐ |
| Tendencia de gentrificación | Precios + Renta + Educación | ⭐⭐⭐⭐ |

### Con Ampliación Prioridad Media

| Análisis | Datos Necesarios | Impacto Ciudadano |
|----------|------------------|-------------------|
| Correlación paro-precios | Tasa paro + Precios | ⭐⭐⭐⭐ |
| Demanda por tipología | Estructura hogares + Oferta | ⭐⭐⭐ |
| Mapa de vulnerabilidad | Paro + Renta + Precios | ⭐⭐⭐⭐⭐ |

---

## 🛠️ Plan de Implementación Técnica

### Sprint 0: Setup Inicial (1 semana)
- Preparar infraestructura y documentación base
- Verificar estructura de base de datos
- Configurar CI/CD para nuevos extractores

### Sprint 1: Renta Histórica IDESCAT (1-2 semanas)
- Crear `IDESCATExtractor` con API de IDESCAT
- Migrar schema: `ALTER TABLE fact_renta ADD COLUMN ...` para años históricos
- Actualizar pipeline ETL para procesar nuevos datos
- Crear KPI "Índice de Asequibilidad" en dashboard

### Sprint 2: Alquiler Incasòl (1 semana)
- Añadir dataset Incasòl a `OpenDataBCNExtractor` o crear extractor específico
- Enriquecer `fact_precios` con datos de alquiler más granulares
- Actualizar visualizaciones de alquiler

### Sprints 3-5: Contexto Socioeconómico (2-3 semanas)
- Crear nueva tabla `fact_socioeconomico` (paro, educación, hogares)
- Extraer datos de Open Data BCN para paro, estudios y estructura de hogares
- Crear tab "Vulnerabilidad" en dashboard

### Sprints 6-8: Enriquecimiento Avanzado (3-4 semanas)
- Crear tablas `fact_transacciones`, `fact_licencias`, `fact_hut`
- Extraer datos de Registradores, licencias urbanísticas y HUTs
- Actualizar visualizaciones con nuevos indicadores

---

## 📊 Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Años de renta disponible | 1 | 8+ |
| Registros de alquiler | 866 | 3,000+ |
| Indicadores socioeconómicos | 0 | 5+ |
| Análisis de asequibilidad | No | Sí |
| Mapa de vulnerabilidad | No | Sí |

---

## 🔗 URLs de Fuentes

### Open Data BCN (CKAN API)
- Base: `https://opendata-ajuntament.barcelona.cat/data/api/3/action/`
- Datasets vivienda: `/package_search?q=habitatge`
- Datasets demografía: `/package_search?q=padro`

### Portal de Dades Barcelona
- Base: `https://portaldades.ajuntament.barcelona.cat`
- API: `/services/backend/rest/search?thesaurus=Habitatge`

### IDESCAT
- Base: `https://www.idescat.cat`
- API: `https://api.idescat.cat/` (requiere registro)

### Incasòl (Generalitat)
- Portal: `https://habitatge.gencat.cat/ca/dades/`
- Datos abiertos: `https://analisi.transparenciacatalunya.cat/`

---

*Documento generado: Noviembre 2025*
*Próxima revisión: Enero 2026*

