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

## 🎯 Propuestas de Ampliación por Impacto

### PRIORIDAD ALTA: Métricas de Asequibilidad

#### 1. Renta Histórica (IDESCAT / INE)
**Fuente**: [IDESCAT - Renda familiar disponible bruta](https://www.idescat.cat/pub/?id=aec&n=893)

```
Indicador: Renta familiar disponible bruta per cápita
Cobertura: 2015-2022 (municipal, algunos años por distrito)
Granularidad: Municipal → Distritos → Barrios (interpolación)
```

**Impacto**: Permitiría calcular:
- **Esfuerzo de compra histórico**: `(Precio vivienda 70m²) / (Renta anual * años)`
- **Esfuerzo de alquiler**: `(Alquiler mensual) / (Renta mensual)`
- **Tendencia de asequibilidad**: ¿Está mejorando o empeorando?

#### 2. Índice de Precios de Alquiler (Incasòl)
**Fuente**: [Incasòl - Observatori de l'Habitatge](https://habitatge.gencat.cat/ca/dades/indicadors_estadistiques/)

```
Indicador: Precio medio alquiler €/m² y €/mes
Cobertura: 2014-2024 (trimestral)
Granularidad: Municipio → Distrito → Barrio
```

**Impacto**: Llenar el gap de datos de alquiler (actualmente solo 13.6% de fact_precios).

---

### PRIORIDAD MEDIA: Contexto Socioeconómico

#### 3. Tasa de Paro por Barrio
**Fuente**: [Barcelona Economia - Atur registrat](https://ajuntament.barcelona.cat/estadistica/catala/Estadistiques_per_territori/Barris/Treball_i_Trets_economics/Atur/index.htm)

```
Indicador: Personas en paro registrado
Cobertura: 2012-2024 (mensual)
Granularidad: Barrio
```

**Impacto**: Correlacionar paro con precios → identificar barrios vulnerables.

#### 4. Nivel de Estudios
**Fuente**: [Open Data BCN - Nivell d'estudis](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/est-padro-nivell-estudis)

```
Indicador: Población por nivel educativo (primaria, secundaria, universitario)
Cobertura: 2015-2023
Granularidad: Barrio
```

**Impacto**: Correlacionar educación con precios → gentrificación educativa.

#### 5. Estructura de Hogares
**Fuente**: [Open Data BCN - Llars segons grandària](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/est-padro-llars-grandaria)

```
Indicador: Hogares por tamaño (1, 2, 3, 4+ personas)
Cobertura: 2015-2023
Granularidad: Barrio
```

**Impacto**: Demanda de tipología de vivienda (estudios vs pisos grandes).

---

### PRIORIDAD BAJA: Enriquecimiento Avanzado

#### 6. Transacciones Inmobiliarias (Registradores)
**Fuente**: [Colegio de Registradores - Estadística Registral](https://www.registradores.org/actualidad/portal-estadistico-registral/estadisticas-de-propiedad)

```
Indicador: Número de compraventas, precio medio, superficie
Cobertura: 2007-2024 (trimestral)
Granularidad: Provincia → Municipio (Barcelona ciudad)
```

**Impacto**: Volumen de mercado, no solo precios.

#### 7. Licencias de Obra / Rehabilitación
**Fuente**: [Open Data BCN - Llicències urbanístiques](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/llicencies-urbanistiques)

```
Indicador: Licencias de obra nueva, rehabilitación, cambio de uso
Cobertura: 2010-2024
Granularidad: Barrio
```

**Impacto**: Predictor de oferta futura y gentrificación.

#### 8. Pisos Turísticos (HUT)
**Fuente**: [Open Data BCN - Habitatges d'ús turístic](https://opendata-ajuntament.barcelona.cat/data/ca/dataset/habitatges-us-turistic)

```
Indicador: Número de HUTs por barrio
Cobertura: 2016-2024
Granularidad: Barrio (con coordenadas)
```

**Impacto**: Presión turística sobre mercado residencial.

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

### Fase 1: Renta Histórica (1-2 semanas)

```python
# Nuevo extractor: src/extraction/idescat.py
class IDESCATExtractor(BaseExtractor):
    """Extractor para datos de IDESCAT (Institut d'Estadística de Catalunya)."""
    
    def extract_renta_familiar(self, year_start: int, year_end: int):
        """Extrae renta familiar disponible bruta."""
        pass
```

**Tareas**:
1. Crear `IDESCATExtractor` con API de IDESCAT
2. Migrar schema: `ALTER TABLE fact_renta ADD COLUMN ...` para años históricos
3. Actualizar pipeline ETL para procesar nuevos datos
4. Crear KPI "Índice de Asequibilidad" en dashboard

### Fase 2: Alquiler Incasòl (1 semana)

**Tareas**:
1. Añadir dataset Incasòl a `OpenDataBCNExtractor` o crear extractor específico
2. Enriquecer `fact_precios` con datos de alquiler más granulares
3. Actualizar visualizaciones de alquiler

### Fase 3: Contexto Socioeconómico (2 semanas)

**Tareas**:
1. Crear nueva tabla `fact_socioeconomico` (paro, educación, hogares)
2. Extraer datos de Open Data BCN
3. Crear tab "Vulnerabilidad" en dashboard

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

