# Variables del Modelo Hedónico - Precios de Vivienda Barcelona

**Última actualización:** Diciembre 2025  
**Fuente:** Análisis de variables que afectan precios de vivienda en Barcelona  
**Referencia:** `data/reference/variables_precio_vivienda_barcelona.csv`

---

## Resumen Ejecutivo

Este documento cataloga todas las variables identificadas que afectan los precios de vivienda en Barcelona, clasificadas por categoría, impacto y disponibilidad en el proyecto actual.

**Variables Totales:** 33  
**Disponibles Actualmente:** 12 (36%)  
**Parcialmente Disponibles:** 4 (12%)  
**No Disponibles:** 17 (52%)

---

## Clasificación por Categorías

### 1. Demográficas (5 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Crecimiento poblacional | Positivo | Alta | ✅ Sí | `fact_demografia` (2015-2023) |
| Estructura de edad | Variable | Media-Alta | ⚠️ Parcial | `fact_demografia_ampliada` (2025) |
| Composición de hogares | Variable | Media | ✅ Sí | Portal Dades |
| Población extranjera | Positivo | Media-Alta | ✅ Sí | `fact_demografia_ampliada` |
| Movilidad interna | Variable | Media | ❌ No | Pendiente integración |

**Evidencia Barcelona:**
- 2021-2023: +1M habitantes en España; Barcelona líder absoluto
- Jóvenes 18-34 alta demanda alquiler; mayores +65 menor rotación
- Población extranjera impulsa demanda; compradores internacionales activos

---

### 2. Económicas (4 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Renta disponible familiar | Positivo | **Muy Alta** | ⚠️ Parcial | `fact_renta` (2022, necesita histórico) |
| Tasa de desempleo | Negativo | Alta | ❌ No | Pendiente Open Data BCN |
| Salario medio | Positivo | Alta | ❌ No | Requiere integración |
| Nivel educativo | Positivo | Media | ⚠️ Parcial | Open Data BCN |

**Evidencia Barcelona:**
- Renta disponible determina capacidad de pago; relación precio/renta 7.3x
- Barrios con alto desempleo menor demanda y precios más bajos
- Salario medio 27,000€; insuficiente para acceso vivienda >200,000€
- Nivel universitario correlaciona con barrios de precios altos

**⚠️ CRÍTICO:** Renta disponible tiene magnitud "Muy Alta" pero solo tenemos datos de 2022. Necesitamos histórico.

---

### 3. Oferta y Demanda (4 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Stock de vivienda disponible | Negativo (precio) | **Muy Alta** | ✅ Implícito | `fact_precios` |
| Nuevas construcciones (visados) | Negativo (precio) | Alta | ❌ No | Requiere nuevos extractores |
| Días en mercado | Indicador demanda | Media | ❌ No | Requiere Idealista API |
| Ratio oferta/demanda | Mixto | Alta | ✅ Calculable | Con datos existentes |

**Evidencia Barcelona:**
- Escasez crítica oferta vs demanda; construcción no cubre formación hogares
- 2024: visados +14.4% pero insuficiente (114.7k vs 208k hogares nuevos)
- Mercado dinámico; rotación alta en barrios centrales
- Desajuste estructural: demanda supera oferta sistemáticamente

---

### 4. Ubicación y Características (5 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Distrito/Barrio | Crítico | **Muy Alta** | ✅ Sí | `dim_barrios` con geometría |
| Proximidad al centro | Positivo | Alta | ✅ Calculable | Con GeoJSON |
| Accesibilidad (transporte) | Positivo | Alta | ⚠️ Parcial | Datos TMB disponibles |
| Densidad urbana | Variable | Media | ✅ Sí | Calculado en `fact_demografia` |
| Proximidad a servicios | Positivo | Alta | ❌ No | Requiere integración |

**Evidencia Barcelona:**
- Ciutat Vella, Eixample, Gràcia precios más altos; periferia más bajo
- Cada km desde Plaza Catalunya reduce precio
- Metro, buses, cercanías aumentan valor; TMB esencial
- Alta densidad presiona precios al alza en distritos centrales

**✅ DISPONIBLE:** Distrito/Barrio es crítico y está disponible con geometría completa.

---

### 5. Turismo y Vivienda Turística (3 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Viviendas uso turístico (HUT) | Negativo (residentes) | Alta | ❌ No | Requiere extractor HUT/Airbnb |
| Airbnb y alquileres cortos | Negativo (residentes) | Alta | ❌ No | Disponible InsideAirbnb |
| Presión turística | Negativo (residentes) | Alta | ❌ No | Requiere integración |

**Evidencia Barcelona:**
- 2023: 10,000+ HUTs registrados; reducen oferta residencial
- Fuerte impacto: trasvase oferta residencial a turística durante COVID
- Barrios turísticos (Ciutat Vella) precios residenciales más altos

**⚠️ PRIORIDAD ALTA:** Estas variables tienen impacto "Alta" pero no están disponibles. Considerar para v2.1+.

---

### 6. Regulación y Políticas (4 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Control de precios alquiler | Complejo | Alta | ⚠️ Observable | Efectos en `fact_precios` |
| Reserva suelo vivienda protegida | Mixto | Media | ❌ No | Requiere fuentes INCASOL |
| Stock vivienda pública | Negativo (precio) | Media | ❌ No | Requiere registro vivienda pública |
| Ley de Vivienda | Complejo | Media-Alta | ⚠️ Conocida | Regulación conocida, impacto por medir |

**Evidencia Barcelona:**
- Ley Control Alquiler 2024: caída -4.9% Barcelona; efectos mixtos
- 40% suelo urbanizable reservado; incrementa costes desarrollo
- España solo 2% vivienda social vs 20-30% Europa; insuficiente

---

### 7. Características de Vivienda (4 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Superficie (m²) | Positivo | Alta | ✅ Implícito | En precios |
| Eficiencia energética | Positivo | Creciente | ❌ No | Requiere certificados energéticos |
| Estado conservación | Positivo | Media-Alta | ⚠️ Parcial | Proxy: edad media edificios |
| Antigüedad edificio | Variable | Media | ✅ Sí | Proxy en `fact_demografia` |

**Evidencia Barcelona:**
- m² crítico para precio final; Barcelona media 71m²
- Calificación A/B: +9.7% valor vs F/G; 2022: +18.3%
- Viviendas rehabilitadas premium valoradas; antiguas menor valor

---

### 8. Financieras (2 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Tipos de interés (Euribor) | Negativo (demanda) | **Muy Alta** | ⚠️ Observable | En series `fact_precios` |
| Condiciones hipotecarias | Crítico | **Muy Alta** | ⚠️ Observable | En tendencias mercado |

**Evidencia Barcelona:**
- 2023-2024: tipos altos frenaron demanda; 2025: bajada reactiva mercado
- Acceso hipoteca condiciona compra vs alquiler; requisitos estrictos

**⚠️ CRÍTICO:** Tipos de interés tienen magnitud "Muy Alta" y son observables en series temporales.

---

### 9. Ambientales (2 variables)

| Variable | Impacto | Magnitud | Disponible | Tabla/Fuente |
|----------|---------|----------|------------|--------------|
| Calidad del aire | Positivo | Media | ❌ No | Requiere datos ambientales |
| Zonas verdes | Positivo | Media | ❌ No | Requiere Ajuntament Barcelona |

**Evidencia Barcelona:**
- Barrios contaminados menor valor; aire limpio valorado positivamente
- m²/hab de zonas verdes correlaciona con precios más altos

---

## Priorización de Variables Faltantes

### Muy Alta Prioridad (Magnitud: Muy Alta)

1. **Renta disponible familiar** - Disponible parcialmente (solo 2022)
   - **Acción:** Extraer histórico completo
   - **Epic:** ETL-006
   - **Target Release:** v2.1

2. **Tipos de interés (Euribor)** - Observable en series
   - **Acción:** Integrar datos Euribor históricos
   - **Epic:** ETL-007
   - **Target Release:** v2.1

3. **Stock de vivienda disponible** - Implícito en fact_precios
   - **Acción:** Calcular métrica derivada
   - **Epic:** DATA-005
   - **Target Release:** v2.0

### Alta Prioridad (Magnitud: Alta)

4. **Nuevas construcciones (visados)** - Requiere extractor
   - **Acción:** Crear extractor de visados
   - **Epic:** ETL-008
   - **Target Release:** v2.1

5. **Viviendas uso turístico (HUT)** - Requiere extractor
   - **Acción:** Integrar datos HUT/Airbnb
   - **Epic:** ETL-009
   - **Target Release:** v2.2

6. **Eficiencia energética** - Requiere certificados
   - **Acción:** Extraer certificados energéticos
   - **Epic:** ETL-010
   - **Target Release:** v2.2

7. **Tasa de desempleo** - Pendiente Open Data BCN
   - **Acción:** Extraer datos desempleo por barrio
   - **Epic:** ETL-011
   - **Target Release:** v2.1

8. **Salario medio** - Requiere integración
   - **Acción:** Identificar fuente y extraer
   - **Epic:** ETL-012
   - **Target Release:** v2.2

---

## Mapeo a Schema Actual

### Variables Disponibles en Schema

| Variable | Tabla | Campo | Notas |
|----------|-------|-------|-------|
| Crecimiento poblacional | `fact_demografia` | `poblacion`, `anio` | Calcular tasa crecimiento |
| Composición de hogares | Portal Dades | `hogares_unipersonales` | Via extractor |
| Población extranjera | `fact_demografia_ampliada` | `poblacion_extranjera` | Disponible 2025 |
| Distrito/Barrio | `dim_barrios` | `barrio_id`, `nombre`, `distrito` | Con geometría |
| Proximidad al centro | `dim_barrios` | `geometry_json` | Calcular distancia |
| Densidad urbana | `fact_demografia` | `densidad_poblacion` | Calculado |
| Antigüedad edificio | `fact_demografia` | `ano_construccion` | Proxy disponible |
| Tipos de interés | `fact_precios` | Series temporales | Observable indirectamente |

### Variables a Agregar al Schema

**Nuevas tablas propuestas:**

1. `fact_renta_historica`
   - Campos: `barrio_id`, `anio`, `renta_media`, `renta_mediana`
   - Fuente: INE, Portal de Dades

2. `fact_euribor`
   - Campos: `fecha`, `euribor_3m`, `euribor_12m`
   - Fuente: Banco de España

3. `fact_construccion`
   - Campos: `barrio_id`, `anio`, `visados`, `viviendas_construidas`
   - Fuente: Ayuntamiento Barcelona

4. `fact_hut`
   - Campos: `barrio_id`, `fecha`, `num_hut`, `num_airbnb`
   - Fuente: Registro HUT, InsideAirbnb

---

## Plan de Integración

### Fase 1: v2.0 (Foundation)
**Variables base del modelo:**
- ✅ Superficie (m²)
- ✅ Antigüedad edificio
- ✅ Distrito/Barrio
- ✅ Proximidad al centro (calculable)
- ✅ Densidad urbana

**R² Esperado:** 0.55-0.60

### Fase 2: v2.1 (Enhanced Analytics)
**Variables adicionales:**
- Renta disponible (histórico completo)
- Tipos de interés (Euribor)
- Tasa de desempleo
- Nuevas construcciones

**R² Esperado:** 0.60-0.70

### Fase 3: v2.2+ (Advanced Features)
**Variables avanzadas:**
- HUT/Airbnb
- Eficiencia energética
- Proximidad a servicios
- Calidad del aire

**R² Esperado:** 0.70+

---

## Referencias

- **CSV Original:** `data/reference/variables_precio_vivienda_barcelona.csv`
- **Model Specification:** `docs/modeling/MODEL_SPECIFICATION_V2.md`
- **Database Schema:** `docs/architecture/DATABASE_SCHEMA_V2.md`

---

**Última actualización:** Diciembre 2025

