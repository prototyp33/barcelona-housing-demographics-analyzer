# RESUMEN EJECUTIVO: Arquitectura de Datos para Variables de Precios de Vivienda

## Propuesta de Implementación - Barcelona Housing Demographics Analyzer

**Documento:** Arquitectura de Datos v2.0  
**Fecha:** Diciembre 2025  
**Versión:** Final Ejecutiva  
**Estado:** Listo para aprobación y ejecución

---

## 📊 DIMENSIÓN DEL PROYECTO

```
SITUACIÓN ACTUAL:
├── Tablas Fact: 5 (factprecios, factdemografia, factdemografiaampliada, factrenta, factofertaidealista)
├── Tablas Dimension: 1 (dimbarrios)
├── Variables capturadas: 12
├── Cobertura temporal: 2015-2025
└── Extractores: 6

SITUACIÓN PROPUESTA:
├── Tablas Fact: 13 (+8)
│   ├── fact_hogares (composición)
│   ├── fact_socioeconomic (desempleo, educación, salarios)
│   ├── fact_construccion (visados, nuevas viviendas)
│   ├── fact_movilidad (flujos poblacionales)
│   ├── fact_turismo (HUTs, Airbnb, turismo)
│   ├── fact_regulacion (control alquileres, vivienda pública)
│   ├── fact_eficiencia (energética, conservación)
│   └── fact_financiera (Euribor, hipotecas)
├── Tablas Dimension: 3 (+2)
│   ├── dim_barrios_metricas (centralidad, accesibilidad, equipamientos)
│   └── dim_barrios_ambiente (aire, ruido, zonas verdes)
├── Variables capturadas: 45+ (+33)
├── Cobertura temporal: 2010-2025 (+5 años)
└── Extractores: 18 (+12)
```

---

## 🎯 IMPACTO ANALÍTICO

**Capacidades que se desbloquean:**

| Análisis | Anterior | Propuesto | Mejora |
|----------|----------|-----------|--------|
| Elasticidad precio-demanda | NO | SÍ (multivariable) | 🟢 |
| Gentrificación (5+ indicadores) | Parcial | Completo | 🟢 |
| Análisis regulatorio | NO | SÍ (post-2024) | 🟢 |
| Turismo vs residencia | NO | SÍ (2014-2025) | 🟢 |
| Eficiencia energética | NO | SÍ (EPC A-G) | 🟢 |
| Proyecciones de precios | 2-3 vars | 15+ vars | 🟢 |
| Segmentación barrios | Básica | Avanzada (10+vars) | 🟢 |

---

## 🏗️ ARQUITECTURA PROPUESTA

### A. Mapeo de Variables a Tablas

**33 variables identificadas → 8 tablas nuevas + 2 dimensiones**

```
DEMOGRÁFICAS (5 vars)
├── Crecimiento poblacional → fact_demografia (existente)
├── Estructura edad → fact_demografia_ampliada (existente)
├── Composición hogares → fact_hogares (NUEVA)
├── Población extranjera → fact_demografia_ampliada (existente)
└── Movilidad interna → fact_movilidad (NUEVA)

ECONÓMICAS (4 vars)
├── Renta disponible → fact_renta (ampliar histórico)
├── Tasa desempleo → fact_socioeconomic (NUEVA)
├── Salario medio → fact_socioeconomic (NUEVA)
└── Nivel educativo → fact_socioeconomic (NUEVA)

OFERTA Y DEMANDA (4 vars)
├── Stock vivienda → fact_construccion (NUEVA)
├── Nuevas construcciones → fact_construccion (NUEVA)
├── Días mercado → fact_precios (enriquecer)
└── Ratio oferta/demanda → [CALCULADO]

UBICACIÓN Y CARACTERÍSTICAS (5 vars)
├── Distrito/Barrio → dim_barrios (existente)
├── Proximidad centro → dim_barrios_metricas (NUEVA)
├── Accesibilidad transporte → dim_barrios_metricas (NUEVA)
├── Densidad urbana → fact_demografia (derivado)
└── Proximidad servicios → dim_barrios_metricas (NUEVA)

TURISMO (3 vars)
├── Viviendas turísticas → fact_turismo (NUEVA)
├── Airbnb → fact_turismo (NUEVA)
└── Presión turística → fact_turismo (NUEVA)

REGULACIÓN (4 vars)
├── Control precios alquiler → fact_regulacion (NUEVA)
├── Suelo protegido → fact_regulacion (NUEVA)
├── Stock vivienda pública → fact_regulacion (NUEVA)
└── Ley Vivienda → fact_regulacion (NUEVA)

CARACTERÍSTICAS VIVIENDA (4 vars)
├── Superficie m² → fact_precios (existente)
├── Eficiencia energética → fact_eficiencia (NUEVA)
├── Estado conservación → fact_eficiencia (NUEVA)
└── Antigüedad edificios → fact_demografia_ampliada (existente)

FINANCIERAS (2 vars)
├── Tipos de interés → fact_financiera (NUEVA)
└── Hipotecas → fact_financiera (NUEVA)

AMBIENTALES (2 vars)
├── Calidad aire → dim_barrios_ambiente (NUEVA)
└── Zonas verdes → dim_barrios_ambiente (NUEVA)
```

---

## 🔧 EXTRACTORES A IMPLEMENTAR

### Fase 1: Infraestructura (Semanas 1-2)

**Tareas de base de datos:**
- Crear 8 tablas fact nuevas
- Crear 2 tablas dimension nuevas
- Establecer índices únicos y constraints FK
- Actualizar schema.sql y migraciones

**Horas:** 22h | **Recurso:** DBA/Dev

### Fase 2: Extractores Críticos (Semanas 3-6)

| Extractor | Fuente | Datos | Prioridad | Semana |
|-----------|--------|-------|-----------|---------|
| **DesempleoExtractor** | SEPE | Tasa paro, parados totales | 🔴 Muy Alta | 3 |
| **EducacionExtractor** | Open Data BCN | Nivel educativo % | 🔴 Muy Alta | 4 |
| **HUTExtractor** | Ajuntament BCN | Viviendas turísticas | 🔴 Muy Alta | 5 |
| **AirbnbExtractor** | Inside Airbnb | Listados, ocupación | 🔴 Muy Alta | 5 |

**Impacto:** +4 tablas, ~400k registros nuevos  
**Horas:** 170h | **Recurso:** 2 devs

### Fase 3: Extractores Complementarios (Semanas 7-10)

| Extractor | Fuente | Datos | Prioridad | Semana |
|-----------|--------|-------|-----------|---------|
| **VisadosExtractor** | Colegio Arquitectos | Visados obra | 🟠 Alta | 7 |
| **ControlAlquilerExtractor** | Generalitat | Zonas tensionadas | 🟠 Alta | 7 |
| **CentralidadExtractor** | Cálculo geométrico | Distancia a centro | 🟡 Media | 8 |
| **AccesibilidadExtractor** | TMB/GTFS | Transporte público | 🟡 Media | 8 |
| **EficienciaEnergeticaExtractor** | Portal Dades | EPC A-G | 🟠 Alta | 9 |
| **AmbienteExtractor** | Ajuntament | Aire, ruido, verdes | 🟡 Media | 9 |

**Impacto:** +6 tablas, ~300k registros nuevos  
**Horas:** 170h | **Recurso:** 2 devs

### Fase 4: Integración (Semanas 11-12)

**Tareas:**
- Integrar 18 extractores en ETL pipeline
- Validación multivariante (reglas negocio)
- Performance testing (load, query)
- Documentación técnica y user guide

**Horas:** 84h | **Recurso:** Dev Lead + QA + Writer

---

## 📈 PLAN TEMPORAL

```
SEMANA      FASE    TAREAS PRINCIPAL                          ESTADO
─────────────────────────────────────────────────────────────────────
  1-2       FASE 1  Base de datos: 8+2 tablas                 [████████]
  3         FASE 2  DesempleoExtractor                        
  4         FASE 2  EducacionExtractor                        
  5         FASE 2  HUTExtractor + AirbnbExtractor            
  6         FASE 2  Tests + integración Fase 2                [████████]
  7         FASE 3  VisadosExtractor + ControlAlquiler        
  8         FASE 3  CentralidadExtractor + Accesibilidad      
  9         FASE 3  EficienciaEnergetica + Ambiente           
  10        FASE 3  Tests + integración Fase 3                [████████]
  11        FASE 4  Pipeline ETL v3.0                         
  11-12     FASE 4  Validación + documentación                [████████]

TOTAL: 12 semanas | 446 horas | 4 devs (11 h/semana) + QA + Writer
```

---

## 💾 CAMBIOS AL ESQUEMA DE BASE DE DATOS

### Nuevas Tablas Fact (8)

```sql
fact_hogares
  ├── barrioid, anio, tamanio_hogar (1-5+)
  ├── numero_hogares, porcentaje_total
  └── Registros esperados: 500

fact_socioeconomic
  ├── barrioid, anio, tasa_desempleo, numero_parados
  ├── salario_medio, nivel_educativo, porcentaje
  └── Registros esperados: 2,000-3,000

fact_construccion
  ├── barrioid, anio, visados_vivienda, nuevas_viviendas
  ├── rehabilitaciones, cambios_uso
  └── Registros esperados: 600

fact_movilidad
  ├── barrioid_origen, barrioid_destino, anio
  ├── numero_traslados, razon_movimiento
  └── Registros esperados: 5,000-10,000

fact_turismo
  ├── barrioid, anio, mes, huts_registradas
  ├── airbnb_listadas, plazas_totales, ocupacion_media
  └── Registros esperados: 3,000-4,000

fact_regulacion
  ├── barrioid, anio, zona_tensionada
  ├── suelo_protegido_m2, stock_vivienda_pública
  └── Registros esperados: 500

fact_eficiencia
  ├── barrioid, anio, viviendas_clase_a-g (%)
  ├── prima_energetica, edad_promedio_edificios
  └── Registros esperados: 500

fact_financiera
  ├── barrioid, anio, mes, euribor_12m
  ├── tipos_hipotecarios, hipotecas_nuevas
  └── Registros esperados: 1,000-1,500
```

### Nuevas Tablas Dimension (2)

```sql
dim_barrios_metricas
  ├── barrioid, distancia_plaza_catalunya_km
  ├── tiempo_metro, estaciones_metro, estaciones_bus
  ├── frecuencia_transporte, numero_equipamientos
  └── densidad_urbana, m2_zona_verde_per_capita

dim_barrios_ambiente
  ├── barrioid, indice_calidad_aire, no2, pm10, pm25
  ├── dias_aire_malo, nivel_ruido_diurno/nocturno
  ├── area_verde_m2, parques_jardines
  └── distancia_parque_medio
```

---

## 🔗 FUENTES DE DATOS (16+)

| Categoría | Fuente | Cobertura | API/Manual | Estado |
|-----------|--------|-----------|-----------|--------|
| Demográfica | INE/Open Data BCN/Portal Dades | 2015-2025 | API CKAN | ✅ Mayormente disponible |
| Económica | SEPE/INE EPA/IDESCAT | 2008-2025 | Web/API | ✅ Requiere scraping |
| Oferta | Colegio Arquitectos/Catastro | 2015-2025 | Web | ⚠️ Requiere acuerdos |
| Turismo | Ajuntament/Inside Airbnb | 2014-2025 | API/CSV | ✅ Disponible |
| Regulación | Generalitat/BOE | 2015-2025 | Web | ⚠️ Parcial |
| Eficiencia | Portal Dades/Catastro | 2019-2025 | CSV/API | ⚠️ Limitado |
| Ambiente | Ajuntament Barcelona | 2015-2025 | API/CSV | ⚠️ Incompleto |
| Financiera | BCE/Banco España | 2008-2025 | API | ✅ Disponible |

---

## 📊 IMPACTO CUANTIFICADO

### Cobertura de Datos

| Aspecto | Actual | Propuesto | Mejora |
|---------|--------|-----------|--------|
| Variables analizables | 12 | 45+ | **375%** |
| Registros en BD | 14,500 | ~30,000 | **207%** |
| Barrios con datos | 73/73 (100%) | 73/73 (100%) | Mantenida |
| Años cubiertos | 10 (2015-2025) | 15 (2010-2025) | +50% |
| Granularidad temporal | Anual | Anual + Mensual | + Mensual |
| Dimensiones analíticas | 2 | 4 | +100% |

### Capacidades Analíticas

**Antes:**
- Análisis de precios vs población
- Correlaciones simples
- Mapas de precios

**Después:**
- Modelado multivariable (15+ variables)
- Análisis de causalidad
- Segmentación avanzada
- Proyecciones de precios
- Análisis de gentrificación
- Evaluación impacto regulatorio
- Cuantificación efectos turísticos
- Valoración eficiencia energética

---

## 💰 PRESUPUESTO Y RECURSOS

### Estimación de Esfuerzo

| Componente | Horas | Costo (€50/h) | Duración |
|-----------|-------|---------------|----------|
| Fase 1: Infraestructura | 22 | €1,100 | 2 sem |
| Fase 2: Extractores críticos | 170 | €8,500 | 4 sem |
| Fase 3: Extractores comp. | 170 | €8,500 | 4 sem |
| Fase 4: Integración | 84 | €4,200 | 2 sem |
| **TOTAL** | **446** | **€22,300** | **12 sem** |

### Equipo Recomendado

- **1 DBA/Dev Senior:** Infraestructura + overseer (22h inicial)
- **2 Backend Devs:** Extractores paralelo (340h distribuido)
- **1 QA/Testing:** Validación y pruebas (50h distribuido)
- **1 Tech Writer:** Documentación (20h)
- **1 Dev Lead/Architect:** Coordinación + integración (40h)

**Total person-weeks:** 2.8 semanas de 4 devs en paralelo

---

## ✅ CRITERIOS DE ACEPTACIÓN

### Fase 1
- [ ] Todas las 10 tablas (8 fact + 2 dim) creadas y testeadas
- [ ] Constraints FK verificados
- [ ] Migrations reversibles documentadas

### Fase 2
- [ ] 4 extractores implementados y en producción
- [ ] 400k+ registros cargados con validación ✅
- [ ] Cobertura 2015-2025 completa
- [ ] Tests unitarios 80%+ cobertura

### Fase 3
- [ ] 6 extractores complementarios operacionales
- [ ] 300k+ registros adicionales
- [ ] Dimensiones geométricas validadas
- [ ] Performance queries <1s para 73 barrios

### Fase 4
- [ ] Pipeline ETL v3.0 ejecutable end-to-end
- [ ] Validación multivariante automática
- [ ] SLA: 99% de registros válidos
- [ ] Dashboard actualizado con nuevas métricas

---

## 🚀 PRÓXIMOS PASOS

1. **APROBACIÓN** (Día 1)
   - Review arquitectura con stakeholders
   - Validar recursos disponibles
   - Firmar acuerdos de acceso a datos

2. **INICIO FASE 1** (Semana 1)
   - Setup base de datos
   - Migrations + versionado
   - Testing scripts

3. **MONITOREO** (Semanal)
   - Reuniones de status
   - Identificar blockers
   - Ajustes de timeline

4. **DELIVERY** (Semana 12)
   - Release pipeline ETL v3.0
   - Documentación completa
   - Transferencia a equipo de operaciones

---

## 📚 ARCHIVOS ENTREGABLES

✅ **ARQUITECTURA_DATOS_VARIABLES.md** - Documento técnico completo (40+ páginas)
✅ **mapeo_variables_extractores.csv** - Matriz 33x5 variables a extractores
✅ **plan_implementacion_fases.csv** - Cronograma 12 semanas detallado
✅ **Este documento** - Resumen ejecutivo

---

## 🎓 CONCLUSIONES

**La propuesta de arquitectura de datos permite:**

1. ✅ Capturar **todas las 33 variables** identificadas en análisis de precios
2. ✅ Mantener **compatibilidad** con esquema actual (star schema)
3. ✅ Escalar a **45+ variables** futuras sin rediseño
4. ✅ Cumplir en **12 semanas** con equipo de 4 devs
5. ✅ Desbloquear **análisis avanzados** (modelado, proyecciones, causalidad)
6. ✅ Crear **base sólida** para BI/ML futuro

**Inversión:** €22,300 + 446 horas  
**ROI esperado:** +375% en capacidades analíticas, múltiples análisis de negocio nuevos

---

**Recomendación: APROBAR para iniciar Fase 1 en semana del 16 de diciembre 2025**

