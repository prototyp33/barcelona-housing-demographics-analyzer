# Plan de Implementación - Arquitectura v2.0 Expansion

**Fecha:** Diciembre 2025  
**Duración Total:** 12 semanas  
**Esfuerzo Total:** 446 horas  
**Equipo:** 4 developers en paralelo

---

## Resumen Ejecutivo

Este plan implementa la expansión de arquitectura para capturar 33 variables adicionales que afectan precios de vivienda en Barcelona, organizadas en 8 nuevas tablas fact y 2 nuevas tablas dimension.

**Objetivo:** Expandir de 12 a 45+ variables analizables (+375%)

---

## Milestones y Fases

### Milestone 1: Spike Validation (Dec 16-20, 2025)

**Duración:** 5 días  
**Objetivo:** Validar viabilidad del modelo hedónico

**Entregables:**
- Reporte de viabilidad (Go/No-Go)
- Decision record
- PRD actualizado

**Estado:** ✅ En progreso

---

### Milestone 2: Fase 1 - Database Infrastructure (Semanas 1-2)

**Due Date:** 2026-01-10  
**Duración:** 2 semanas  
**Esfuerzo:** 22 horas

**Tareas:**
- [ ] Crear 8 tablas fact nuevas
- [ ] Crear 2 tablas dimension nuevas
- [ ] Establecer índices únicos y constraints FK
- [ ] Actualizar schema.sql y migraciones reversibles
- [ ] Validar integridad referencial

**Tablas a crear:**
1. `fact_hogares`
2. `fact_socioeconomic`
3. `fact_construccion`
4. `fact_movilidad`
5. `fact_turismo`
6. `fact_regulacion`
7. `fact_eficiencia`
8. `fact_financiera`
9. `dim_barrios_metricas`
10. `dim_barrios_ambiente`

**Criterios de Aceptación:**
- ✅ Todas las 10 tablas creadas y testeadas
- ✅ Constraints FK verificados
- ✅ Migrations reversibles documentadas
- ✅ Schema versionado

---

### Milestone 3: Fase 2 - Critical Extractors (Semanas 3-6)

**Due Date:** 2026-02-07  
**Duración:** 4 semanas  
**Esfuerzo:** 170 horas

**Extractores a implementar:**

1. **DesempleoExtractor** (40h)
   - Fuente: SEPE
   - Datos: Tasa paro, parados totales
   - Cobertura: 2008-2025
   - Tabla: `fact_socioeconomic`

2. **EducacionExtractor** (40h)
   - Fuente: Open Data BCN
   - Datos: Nivel educativo %
   - Cobertura: 2015-2025
   - Tabla: `fact_socioeconomic`

3. **HUTExtractor** (35h)
   - Fuente: Ajuntament Barcelona
   - Datos: Viviendas turísticas
   - Cobertura: 2016-2025
   - Tabla: `fact_turismo`

4. **AirbnbExtractor** (35h)
   - Fuente: Inside Airbnb
   - Datos: Listados, ocupación
   - Cobertura: 2015-2025
   - Tabla: `fact_turismo`

5. **Tests e Integración** (20h)

**Criterios de Aceptación:**
- ✅ 4 extractores implementados y en producción
- ✅ 400k+ registros cargados con validación
- ✅ Cobertura 2015-2025 completa
- ✅ Tests unitarios 80%+ cobertura

**Impacto:** +4 tablas, ~400k registros nuevos, 80% del valor

---

### Milestone 4: Fase 3 - Complementary Extractors (Semanas 7-10)

**Due Date:** 2026-03-14  
**Duración:** 4 semanas  
**Esfuerzo:** 170 horas

**Extractores a implementar:**

1. **VisadosExtractor** (50h)
   - Fuente: Colegio Arquitectos
   - Datos: Visados obra nueva
   - Tabla: `fact_construccion`

2. **ControlAlquilerExtractor** (50h)
   - Fuente: Generalitat
   - Datos: Zonas tensionadas
   - Tabla: `fact_regulacion`

3. **CentralidadExtractor** (40h)
   - Fuente: Cálculo geométrico
   - Datos: Distancia a centro
   - Tabla: `dim_barrios_metricas`

4. **AccesibilidadExtractor** (40h)
   - Fuente: TMB/GTFS
   - Datos: Transporte público
   - Tabla: `dim_barrios_metricas`

5. **EficienciaEnergeticaExtractor** (50h)
   - Fuente: Portal Dades/Catastro
   - Datos: EPC A-G
   - Tabla: `fact_eficiencia`

6. **AmbienteExtractor** (Incluido)
   - Fuente: Ajuntament
   - Datos: Aire, ruido, zonas verdes
   - Tabla: `dim_barrios_ambiente`

7. **Tests Integración** (30h)

**Criterios de Aceptación:**
- ✅ 6 extractores complementarios operacionales
- ✅ 300k+ registros adicionales
- ✅ Dimensiones geométricas validadas
- ✅ Performance queries <1s para 73 barrios

**Impacto:** +6 tablas, ~300k registros adicionales, análisis territorial completo

---

### Milestone 5: Fase 4 - Integration & Production (Semanas 11-12)

**Due Date:** 2026-03-28  
**Duración:** 2 semanas  
**Esfuerzo:** 84 horas

**Tareas:**

1. **Pipeline ETL v3.0** (40h)
   - Integrar 18 extractores en pipeline
   - Automatización completa
   - Error handling robusto

2. **Validación Multivariante** (24h)
   - Validación de calidad multivariante
   - Reglas de negocio
   - SLA: 99% de registros válidos

3. **Performance Testing** (20h)
   - Load testing
   - Query optimization
   - Index tuning

4. **Documentación** (20h)
   - Documentación técnica completa
   - User guide
   - API documentation (si aplica)

**Criterios de Aceptación:**
- ✅ Pipeline ETL v3.0 ejecutable end-to-end
- ✅ Validación multivariante automática
- ✅ SLA: 99% de registros válidos
- ✅ Dashboard actualizado con nuevas métricas
- ✅ Documentación completa

---

## Timeline Visual

```
Dec 2025    Jan 2026         Feb 2026         Mar 2026
   │           │                │                │
   ▼           ▼                ▼                ▼
SPIKE ───> FASE 1 ───────> FASE 2 ───────> FASE 3 ───────> FASE 4
Dec 16-20   Jan 6-10        Jan 13-Feb 7    Feb 10-Mar 14  Mar 17-28
├─────┤   ├──────────┤    ├──────────┤    ├──────────┤    ├──────────┤
5 days     2 weeks         4 weeks         4 weeks         2 weeks
           22h             170h            170h            84h
```

---

## Recursos y Equipo

### Equipo Recomendado

| Role | Semanas | Horas/semana | Total horas |
|------|---------|--------------|-------------|
| DBA/Dev Senior | 1-2 | 10h | 20h |
| Backend Dev 1 | 3-10 | 40h | 280h |
| Backend Dev 2 | 3-10 | 40h | 280h |
| QA/Testing | 6-12 | 8h | 50h |
| Tech Writer | 11-12 | 10h | 20h |
| Dev Lead | 1-12 | 4h | 48h |

**Total:** 446 horas

---

## Métricas de Éxito

### Fase 1
- ✅ 10 tablas creadas
- ✅ Constraints verificados
- ✅ Migrations documentadas

### Fase 2
- ✅ 4 extractores operacionales
- ✅ 400k+ registros cargados
- ✅ Tests 80%+ cobertura

### Fase 3
- ✅ 6 extractores operacionales
- ✅ 300k+ registros adicionales
- ✅ Performance <1s queries

### Fase 4
- ✅ Pipeline ETL v3.0 funcional
- ✅ SLA 99% datos válidos
- ✅ Documentación completa

---

## Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| APIs cambian estructura | Media (40%) | Alto | Monitoreo semanal, API mocking |
| Datos incompletos | Media (50%) | Medio | Validación + imputación |
| Personal no disponible | Baja (20%) | Alto | Buffer de 2 semanas |
| Cambios esquema rompen código | Baja (10%) | Alto | Migraciones reversibles |
| Performance queries lenta | Baja (15%) | Medio | Load testing Fase 4 |

---

## Referencias

- **Arquitectura Completa:** `docs/architecture/ARQUITECTURA_DATOS_VARIABLES.md`
- **Resumen Ejecutivo:** `docs/RESUMEN_EJECUTIVO_ARQUITECTURA.md`
- **Mapeo de Variables:** `data/reference/mapeo_variables_extractores.csv`

---

**Última actualización:** Diciembre 2025

