# Plan de Implementación: Variables Adicionales de Alto Impacto

**Fecha**: 2025-12-14  
**Objetivo**: Integrar 35+ variables adicionales para mejorar modelos predictivos  
**Impacto esperado**: +15-20% mejora en precisión (R² de 0.75 → 0.94)

---

## 🎯 RESUMEN EJECUTIVO

### Objetivo
Implementar 8 nuevas tablas de hechos y ampliar 3 existentes con variables de alta correlación con precios de vivienda, priorizadas por impacto y disponibilidad de datos.

### Impacto Esperado

| Fase | Variables | Mejora R² | Tiempo |
|------|-----------|-----------|--------|
| **Fase 1** | Seguridad, Educación, Calidad Ambiental | +10-15% | 0-3 meses |
| **Fase 2** | Características Técnicas, Contexto Económico | +5-8% | 3-6 meses |
| **Fase 3** | Desarrollo Urbano, Turismo, Conectividad | +2-3% | 6-12 meses |
| **TOTAL** | 8 tablas nuevas + 3 ampliadas | **+15-20%** | 12 meses |

---

## 📋 FASE 1 - MÁXIMO IMPACTO (0-3 meses)

### Prioridad: 🔴 ALTA

**Objetivo**: Implementar las 3 variables con mayor correlación y disponibilidad de datos.

### 1.1 fact_seguridad

**Correlación**: r = -0.61 (LA MÁS ALTA - INVERSA)  
**Impacto**: -30% a +20% en precio  
**Disponibilidad**: ⚠️ Media (datos agregados por distrito)

**Tareas**:
- [ ] Crear tabla `fact_seguridad` (SQL schema)
- [ ] Crear extractor `src/extraction/seguridad.py`
  - [ ] Integrar datos Mossos d'Esquadra
  - [ ] Integrar Observatorio Seguridad Barcelona
  - [ ] Scraping encuestas de victimización
- [ ] Crear transformador `src/etl/transformations/seguridad.py`
  - [ ] Calcular tasas por 1000 habitantes
  - [ ] Calcular índice de seguridad ponderado
- [ ] Integrar en pipeline ETL
- [ ] Crear vista `vista_indice_seguridad`
- [ ] Tests unitarios

**Estimación**: 3-4 semanas

**Fuentes de datos**:
- Mossos d'Esquadra: `https://mossos.gencat.cat/ca/els_mossos_desquadra/indicadors_i_qualitat/dades_obertes/`
- Observatorio Seguridad Barcelona: `https://ajuntament.barcelona.cat/seguretatiprevencio/ca`
- INE Encuestas Victimización: Anual

---

### 1.2 fact_educacion

**Correlación**: r = 0.55  
**Impacto**: +10% a +51% en precio  
**Disponibilidad**: ✅ Alta

**Tareas**:
- [ ] Crear tabla `fact_educacion` (SQL schema)
- [ ] Crear extractor `src/extraction/educacion.py`
  - [ ] Scraping rankings colegios (El Mundo, Micole)
  - [ ] API Departament d'Educació (Generalitat)
  - [ ] Datos IDESCAT - Educación
- [ ] Crear transformador `src/etl/transformations/educacion.py`
  - [ ] Calcular índice calidad educativa
  - [ ] Mapear colegios a barrios
- [ ] Integrar en pipeline ETL
- [ ] Crear vista `vista_indice_educacion`
- [ ] Tests unitarios

**Estimación**: 2-3 semanas

**Fuentes de datos**:
- Rankings: `https://www.micole.net/mejores-colegios/barcelona/`
- Generalitat: `https://educacio.gencat.cat/ca/inici`
- IDESCAT: Datos anuales

---

### 1.3 fact_calidad_ambiental

**Correlación**: r = -0.35 (ruido), r = -0.28 (aire)  
**Impacto**: -3.4% a +20% en precio  
**Disponibilidad**: ✅ Alta

**Tareas**:
- [ ] Crear tabla `fact_calidad_ambiental` (SQL schema)
- [ ] Crear extractor `src/extraction/calidad_ambiental.py`
  - [ ] Mapa Capacitat Acústica (Ayuntamiento BCN)
  - [ ] Red Vigilancia Calidad Aire (Generalitat)
  - [ ] Datos zonas verdes (OpenStreetMap)
- [ ] Crear transformador `src/etl/transformations/calidad_ambiental.py`
  - [ ] Calcular niveles de ruido por barrio
  - [ ] Agregar datos calidad aire por barrio
  - [ ] Calcular % área verde
- [ ] Integrar en pipeline ETL
- [ ] Crear vista `vista_calidad_aire_alertas`
- [ ] Tests unitarios

**Estimación**: 2-3 semanas

**Fuentes de datos**:
- Ruido: `https://ajuntament.barcelona.cat/ecologiaurbana/ca/serveis/la-ciutat-funciona/manteniment-de-la-via-publica/soroll`
- Aire: `https://analisi.transparenciacatalunya.cat/resource/uy6k-2s8r.json`

---

### Entregables Fase 1

- ✅ 3 nuevas tablas de hechos
- ✅ 3 extractores nuevos
- ✅ 3 transformadores nuevos
- ✅ 3 vistas analíticas
- ✅ Tests unitarios completos
- ✅ Documentación de fuentes

**Impacto esperado**: +10-15% mejora en R² del modelo

---

## 📋 FASE 2 - ALTO IMPACTO (3-6 meses)

### Prioridad: 🟡 MEDIA-ALTA

### 2.1 fact_caracteristicas_tecnicas

**Correlación**: r = 0.82 (calidad construcción)  
**Impacto**: +15% a +40% en precio  
**Disponibilidad**: ⚠️ Baja (datos limitados)

**Tareas**:
- [ ] Crear tabla `fact_caracteristicas_tecnicas`
- [ ] Crear extractor para Catastro API
- [ ] Crear extractor para Certificados Energéticos (ICAEN)
- [ ] Crear transformador con feature engineering
- [ ] Integrar en pipeline ETL
- [ ] Tests unitarios

**Estimación**: 4-5 semanas

**Desafíos**:
- Datos limitados de Catastro
- Certificados energéticos con privacidad
- Necesidad de estimaciones/proxies

---

### 2.2 fact_contexto_economico

**Correlación**: r = -0.61 (tasa paro)  
**Impacto**: Variable (macroeconómico)  
**Disponibilidad**: ✅ Alta

**Tareas**:
- [ ] Crear tabla `fact_contexto_economico`
- [ ] Crear extractor INE - EPA
- [ ] Crear extractor Banco de España
- [ ] Crear extractor Colegio Registradores
- [ ] Crear transformador con agregaciones
- [ ] Integrar en pipeline ETL
- [ ] Tests unitarios

**Estimación**: 2-3 semanas

---

### 2.3 Ampliación fact_proximidad

**Correlación**: r = 0.45 (transporte)  
**Impacto**: +5% a +15% en precio  
**Disponibilidad**: ✅ Alta

**Tareas**:
- [ ] Ampliar schema `fact_proximidad`
- [ ] Crear extractor TMB API
- [ ] Crear extractor OpenStreetMap Overpass
- [ ] Calcular walkability score
- [ ] Integrar en pipeline ETL
- [ ] Tests unitarios

**Estimación**: 2-3 semanas

---

### Entregables Fase 2

- ✅ 2 nuevas tablas de hechos
- ✅ 1 tabla ampliada
- ✅ 5 extractores nuevos
- ✅ 3 transformadores nuevos
- ✅ Tests unitarios completos

**Impacto esperado**: +5-8% mejora adicional en R²

---

## 📋 FASE 3 - IMPACTO MEDIO (6-12 meses)

### Prioridad: 🟢 MEDIA

### 3.1 fact_desarrollo_urbano

**Tareas**:
- [ ] Crear tabla `fact_desarrollo_urbano`
- [ ] Scraping PAM (Pla d'Actuació Municipal)
- [ ] Scraping PMU (Pla Metropolità d'Urbanisme)
- [ ] Integrar en pipeline ETL

**Estimación**: 2-3 semanas

---

### 3.2 fact_turismo

**Tareas**:
- [ ] Crear tabla `fact_turismo`
- [ ] Integrar InsideAirbnb
- [ ] Scraping Ayuntamiento Barcelona - Turismo
- [ ] Calcular índice saturación turística
- [ ] Integrar en pipeline ETL

**Estimación**: 2-3 semanas

---

### 3.3 fact_conectividad_digital

**Tareas**:
- [ ] Crear tabla `fact_conectividad_digital`
- [ ] Scraping operadores telecomunicaciones
- [ ] Datos cobertura móvil
- [ ] Integrar en pipeline ETL

**Estimación**: 1-2 semanas

---

### 3.4 Ampliación fact_demografia

**Tareas**:
- [ ] Ampliar schema `fact_demografia`
- [ ] Calcular tendencias poblacionales
- [ ] Calcular índices demográficos
- [ ] Integrar en pipeline ETL

**Estimación**: 1 semana

---

### Entregables Fase 3

- ✅ 3 nuevas tablas de hechos
- ✅ 1 tabla ampliada
- ✅ 4 extractores nuevos
- ✅ Tests unitarios completos

**Impacto esperado**: +2-3% mejora adicional en R²

---

## 📊 MÉTRICAS DE ÉXITO

### KPIs Técnicos

- **Cobertura de datos**: >80% para variables Fase 1
- **Calidad de datos**: <10% valores nulos en campos críticos
- **Actualización**: Datos actualizados trimestralmente (mínimo)

### KPIs de Modelo

- **R² mejorado**: De 0.75 actual → 0.90+ con todas las variables
- **RMSE reducido**: De 40,000€ → 26,000-33,000€
- **MAE mejorado**: De 0.30 → 0.18-0.25

---

## 🚧 RIESGOS Y MITIGACIONES

### Riesgo 1: Disponibilidad limitada de datos

**Mitigación**:
- Priorizar variables con alta disponibilidad (Fase 1)
- Usar proxies y estimaciones cuando sea necesario
- Documentar limitaciones claramente

### Riesgo 2: Complejidad de extracción

**Mitigación**:
- Reutilizar patrones de extractores existentes
- Crear módulos reutilizables
- Tests exhaustivos

### Riesgo 3: Overfitting del modelo

**Mitigación**:
- Validación cruzada rigurosa
- Feature selection basado en importancia
- Regularización en modelos ML

---

## 📚 DOCUMENTACIÓN

### Documentos a Crear

- [ ] `docs/spike/ENHANCED_FEATURES_ANALYSIS.md` ✅ (creado)
- [ ] `docs/spike/ENHANCED_FEATURES_SCHEMA.sql` ✅ (creado)
- [ ] `docs/spike/ENHANCED_FEATURES_IMPLEMENTATION_PLAN.md` ✅ (este documento)
- [ ] `docs/data-sources/SEGURIDAD.md`
- [ ] `docs/data-sources/EDUCACION.md`
- [ ] `docs/data-sources/CALIDAD_AMBIENTAL.md`

---

## 🔗 Issues Relacionadas

- Issue #214: [FEAT] Implementar fact_seguridad (Fase 1)
- Issue #215: [FEAT] Implementar fact_educacion (Fase 1)
- Issue #216: [FEAT] Implementar fact_calidad_ambiental (Fase 1)
- Issue #217: [FEAT] Implementar fact_caracteristicas_tecnicas (Fase 2)
- Issue #218: [FEAT] Implementar fact_contexto_economico (Fase 2)
- Issue #219: [FEAT] Ampliar fact_proximidad (Fase 2)
- Issue #220: [FEAT] Implementar fact_desarrollo_urbano (Fase 3)
- Issue #221: [FEAT] Implementar fact_turismo (Fase 3)
- Issue #222: [FEAT] Implementar fact_conectividad_digital (Fase 3)

---

**Última actualización**: 2025-12-14  
**Estado**: 📝 Plan creado - Pendiente de aprobación e inicio Fase 1

