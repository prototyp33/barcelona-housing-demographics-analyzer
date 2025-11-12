# Issues para Crear en GitHub

## 🔴 Prioridad Alta

### 1. Fix: Deduplicación agresiva en fact_precios
**Labels**: `bug`, `data-processing`, `etl`, `database`  
**Prioridad**: `high`

**Descripción**:
Se procesaron 65,644 registros de venta y 11,955 de alquiler del Portal de Dades, pero solo se cargaron 1,119 en la base de datos. La lógica de `drop_duplicates` elimina registros válidos cuando hay múltiples indicadores para el mismo barrio/año.

**Tareas**:
- [ ] Incluir `dataset_id` en la clave de deduplicación
- [ ] O crear una tabla de agregación que preserve múltiples fuentes
- [ ] O implementar una estrategia de "mejor fuente" por año/barrio
- [ ] Actualizar tests

**Aceptación**:
- Todos los registros válidos se cargan en la base de datos
- No se pierden datos de diferentes indicadores

---

### 2. Feature: Completar campos demográficos faltantes
**Labels**: `enhancement`, `data-processing`, `etl`  
**Prioridad**: `high`

**Descripción**:
Varios campos en `fact_demografia` están NULL: `hogares_totales`, `edad_media`, `porc_inmigracion`, `densidad_hab_km2`. Los datos actuales de Open Data BCN solo incluyen población por sexo.

**Tareas**:
- [ ] Buscar datasets adicionales en Portal de Dades
- [ ] Integrar datos de INE si están disponibles
- [ ] Calcular densidad (requiere superficie)
- [ ] Actualizar pipeline ETL

**Aceptación**:
- Al menos 2 de los 4 campos tienen datos
- Datos validados y consistentes

---

## 🟡 Prioridad Media

### 3. Improvement: Mejorar mapeo de territorios Portal de Dades
**Labels**: `enhancement`, `data-processing`, `quality-assurance`  
**Prioridad**: `medium`

**Descripción**:
Algunos territorios del Portal de Dades no se mapean correctamente a `barrio_id`. Se registran warnings pero el proceso continúa.

**Tareas**:
- [ ] Crear diccionario de mapeo manual para casos especiales
- [ ] Implementar fuzzy matching para nombres similares
- [ ] Mejorar logging de no mapeados
- [ ] Documentar casos especiales

**Aceptación**:
- >95% de territorios mapeados correctamente
- Logging detallado de casos no mapeados

---

### 4. Feature: Integrar geometrías de barrios
**Labels**: `enhancement`, `database`, `visualization`  
**Prioridad**: `medium`

**Descripción**:
`geometry_json` en `dim_barrios` está NULL. No se pueden hacer visualizaciones geográficas.

**Tareas**:
- [ ] Obtener GeoJSON de barrios de Open Data BCN
- [ ] Cargar en `geometry_json`
- [ ] Validar geometrías
- [ ] Actualizar ETL

**Aceptación**:
- Todos los barrios tienen geometría
- Geometrías validadas

---

### 5. Task: EDA Inicial - Análisis Exploratorio
**Labels**: `task`, `analysis`, `notebook`  
**Prioridad**: `medium`  
**Milestone**: Milestone 2

**Descripción**:
Completar notebook `01-eda-initial.ipynb` con análisis de datos cargados.

**Tareas**:
- [ ] Análisis exploratorio de datos cargados
- [ ] Visualizaciones básicas
- [ ] Identificar patrones y outliers
- [ ] Documentar hallazgos

**Aceptación**:
- Notebook completo con análisis
- Visualizaciones claras
- Hallazgos documentados

---

### 6. Feature: Implementar funciones de análisis
**Labels**: `enhancement`, `analysis`  
**Prioridad**: `medium`  
**Milestone**: Milestone 3

**Descripción**:
Crear funciones en `src/analysis.py` para correlaciones y estadísticas.

**Tareas**:
- [ ] Funciones de correlación demografía-precios
- [ ] Estadísticas por barrio/distrito
- [ ] Tendencias temporales
- [ ] Tests unitarios

**Aceptación**:
- Funciones documentadas
- Tests pasando
- Ejemplos de uso

---

## 🟢 Prioridad Baja

### 7. Feature: Dashboard Streamlit
**Labels**: `enhancement`, `dashboard`, `streamlit`, `visualization`  
**Prioridad**: `low`  
**Milestone**: Milestone 4

**Descripción**:
Implementar dashboard interactivo con visualizaciones.

**Tareas**:
- [ ] Implementar `src/app.py`
- [ ] Visualizaciones interactivas
- [ ] Filtros por barrio, año, etc.
- [ ] Diseño responsive

**Aceptación**:
- Dashboard funcional
- Visualizaciones claras
- UX intuitiva

---

### 8. Task: Testing - Unit e Integration Tests
**Labels**: `task`, `testing`, `quality-assurance`  
**Prioridad**: `low`  
**Milestone**: Milestone 5

**Descripción**:
Crear suite de tests para funciones críticas.

**Tareas**:
- [ ] Unit tests para funciones críticas
- [ ] Integration tests para pipeline ETL
- [ ] Code coverage >80%
- [ ] CI/CD integration

**Aceptación**:
- Tests pasando
- Coverage >80%
- CI/CD configurado

---

### 9. Task: Implementar extractor INE completo
**Labels**: `task`, `data-extraction`, `ine`  
**Prioridad**: `low`

**Descripción**:
Completar implementación de `INEExtractor`.

**Tareas**:
- [ ] Investigar API INE
- [ ] Implementar extracción
- [ ] Integrar en pipeline
- [ ] Tests

**Aceptación**:
- Extractor funcional
- Datos cargados en base de datos

---

### 10. Task: Evaluar viabilidad de Idealista
**Labels**: `task`, `data-extraction`, `idealista`  
**Prioridad**: `low`

**Descripción**:
Evaluar aspectos legales/éticos y viabilidad técnica.

**Tareas**:
- [ ] Revisar términos de servicio
- [ ] Evaluar aspectos legales
- [ ] Implementar scraping ético si viable
- [ ] Documentar decisión

**Aceptación**:
- Decisión documentada
- Si viable, implementación básica

