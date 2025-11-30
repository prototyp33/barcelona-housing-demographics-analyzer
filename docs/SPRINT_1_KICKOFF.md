# 🚀 Sprint 1 Kickoff: Renta Histórica (Semanas 2-4)

**Fecha de Inicio:** Noviembre 2025  
**Duración:** 2-3 semanas  
**Objetivo:** Implementar extractor IDESCAT y pipeline de renta histórica (2015-2023)

---

## 📋 Contexto del Sprint

**Sprint 0 Completado ✅:**
- Backup DB creado
- Baseline report documentado
- Issues organizadas en el tablero
- Proyecto configurado

**Sprint 1 Objetivo:**
Obtener datos históricos de renta (2015-2023) desde IDESCAT para calcular el **Índice de Asequibilidad**, una métrica crítica que permitirá a los ciudadanos saber "¿Puedo permitirme vivir en este barrio?"

---

## 🎯 Issues del Sprint 1

### Issue #24: [S1] Implementar IDESCATExtractor + tests
**Prioridad:** 🔴 Alta  
**Estimación:** 1-1.5 semanas  
**Owner:** DE (Data Engineer)

**Entregables:**
- [ ] Extractor funcional en `src/extraction/idescat.py`
- [ ] Tests unitarios con respuestas mock
- [ ] Integración con sistema de manifest
- [ ] Documentación en `docs/sources/idescat.md`

### Issue #25: [S2] Pipeline renta histórica
**Prioridad:** 🔴 Alta  
**Estimación:** 1-1.5 semanas  
**Owner:** DE (Data Engineer)  
**Depende de:** Issue #24

**Entregables:**
- [ ] Migración SQLite (tabla `fact_renta_hist`)
- [ ] Pipeline ETL con validaciones (cobertura >=80%)
- [ ] Notebook QA (`notebooks/renta_historica.ipynb`)
- [ ] Actualización de `data_loader.py` para exponer datos

---

## 🔍 Fase 1: Investigación Técnica (Issue #24 - Día 1-2)

### Objetivo
Entender cómo funciona la API de IDESCAT y diseñar el extractor.

### Tareas

1. **Investigar API de IDESCAT:**
   - [ ] Identificar endpoints disponibles
   - [ ] Verificar formato de respuesta (JSON/CSV/XML)
   - [ ] Documentar rate limits y autenticación
   - [ ] Identificar el dataset específico de "Renta disponible por barrio"
   - [ ] Verificar cobertura temporal (¿2015-2023 disponible?)

2. **Diseñar arquitectura del extractor:**
   - [ ] Revisar `src/extraction/base.py` para entender el patrón
   - [ ] Definir estructura de datos esperada
   - [ ] Planificar manejo de errores y reintentos
   - [ ] Decidir estrategia de almacenamiento (CSV + manifest)

### Recursos
- **IDESCAT API:** https://www.idescat.cat/
- **Documentación:** Buscar "API" o "Dades obertes" en el sitio
- **Referencia:** Revisar `src/extraction/opendata.py` como ejemplo de extractor similar

### Criterio de Éxito
- Documento con endpoints, formato y limitaciones identificadas
- Diseño del extractor documentado (pseudocódigo o diagrama)

---

## 💻 Fase 2: Implementación del Extractor (Issue #24 - Día 3-7)

### Objetivo
Crear `IDESCATExtractor` funcional siguiendo el patrón de `BaseExtractor`.

### Tareas

1. **Crear `src/extraction/idescat.py`:**
   ```python
   from .base import BaseExtractor
   
   class IDESCATExtractor(BaseExtractor):
       """Extractor para datos del Institut d'Estadística de Catalunya (IDESCAT)."""
       
       BASE_URL = "https://www.idescat.cat"
       # ... implementación
   ```

2. **Implementar métodos clave:**
   - [ ] `__init__()`: Configurar rate limits y headers
   - [ ] `get_renta_by_barrio()`: Método principal de extracción
   - [ ] `_normalize_barrio_name()`: Mapear nombres IDESCAT → `codi_barri`
   - [ ] `_save_raw_data()`: Usar método heredado con `data_type="renta_historica"`

3. **Integrar con manifest:**
   - [ ] Asegurar que `_save_raw_data` registra en `manifest.json`
   - [ ] Verificar que `data_type` es correcto

4. **Tests unitarios (`tests/test_idescat.py`):**
   - [ ] Mock de respuestas API
   - [ ] Test de normalización de nombres
   - [ ] Test de guardado en manifest
   - [ ] Test de manejo de errores

### Criterio de Éxito
- Extractor ejecuta sin errores
- Tests pasan: `pytest tests/test_idescat.py -v`
- Datos guardados en `data/raw/idescat/` con entrada en `manifest.json`

---

## 🗄️ Fase 3: Pipeline ETL (Issue #25 - Día 8-12)

### Objetivo
Crear tabla `fact_renta_hist` y pipeline para cargar datos históricos.

### Tareas

1. **Migración de esquema (`scripts/maintenance/migrate_renta_hist.py`):**
   ```sql
   CREATE TABLE fact_renta_hist (
       renta_hist_id INTEGER PRIMARY KEY AUTOINCREMENT,
       barrio_id INTEGER NOT NULL,
       anio INTEGER NOT NULL,
       renta_media REAL,
       renta_mediana REAL,
       dataset_id TEXT,
       source TEXT DEFAULT 'idescat',
       etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id),
       UNIQUE(barrio_id, anio, dataset_id, source)
   );
   ```

2. **Función de procesamiento (`src/data_processing.py`):**
   - [ ] `prepare_fact_renta_hist()`: Limpiar y normalizar datos raw
   - [ ] Validar mapeo `barrio_id` (73 barrios)
   - [ ] Calcular cobertura temporal (debe ser >=80% para 2015-2023)

3. **Integración en pipeline (`src/etl/pipeline.py`):**
   - [ ] Cargar datos desde manifest (`data_type="renta_historica"`)
   - [ ] Llamar a `prepare_fact_renta_hist()`
   - [ ] Insertar en `fact_renta_hist` con validación de foreign keys

4. **Notebook QA (`notebooks/renta_historica.ipynb`):**
   - [ ] Visualizar cobertura temporal (gráfico de barras por año)
   - [ ] Verificar distribución de valores (boxplot, histograma)
   - [ ] Comparar con `fact_renta` (2022) para validar consistencia

5. **Actualizar `src/app/data_loader.py`:**
   - [ ] Función `load_renta_historica(year: int) -> pd.DataFrame`
   - [ ] Cache con `@st.cache_data`

### Criterio de Éxito
- Tabla `fact_renta_hist` creada con >=80% cobertura 2015-2023
- Pipeline ejecuta sin errores: `python scripts/process_and_load.py`
- Notebook QA muestra datos consistentes
- Dashboard puede cargar datos históricos

---

## ✅ Definition of Done (Sprint 1)

Para considerar el Sprint 1 completado:

- [ ] Issue #24 cerrada:
  - [ ] Extractor funcional con tests pasando
  - [ ] Datos raw guardados en `data/raw/idescat/`
  - [ ] Documentación en `docs/sources/idescat.md`

- [ ] Issue #25 cerrada:
  - [ ] Tabla `fact_renta_hist` con >=80% cobertura 2015-2023
  - [ ] Pipeline ETL ejecuta sin errores
  - [ ] Notebook QA completado
  - [ ] `data_loader.py` actualizado

- [ ] KPIs verificados:
  - [ ] Años de renta disponibles: 8+ (2015-2023)
  - [ ] Cobertura geográfica: 73/73 barrios
  - [ ] Tests pasando: `pytest tests/ -v`

---

## 🚧 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| API de IDESCAT requiere autenticación | Media | Alto | Investigar alternativas (scraping, CSV público) |
| Datos no disponibles para todos los años | Alta | Medio | Aceptar >=80% cobertura, documentar gaps |
| Mapeo barrios IDESCAT → codi_barri complejo | Media | Medio | Crear tabla de mapeo persistente, validar con QA |

---

## 📚 Recursos y Referencias

- **IDESCAT:** https://www.idescat.cat/
- **Patrón BaseExtractor:** `src/extraction/base.py`
- **Ejemplo de extractor:** `src/extraction/opendata.py`
- **Pipeline ETL:** `src/etl/pipeline.py`
- **Roadmap completo:** `docs/DATA_EXPANSION_ROADMAP.md`

---

## 🎯 Próximo Paso Inmediato

**Comienza con la Fase 1 (Investigación Técnica):**

1. Abre el navegador y visita https://www.idescat.cat/
2. Busca "API" o "Dades obertes" o "Renta disponible"
3. Documenta endpoints, formato y limitaciones
4. Comparte los hallazgos antes de implementar

**Prompt para el asistente de IA:**
> "Necesito investigar la API de IDESCAT para extraer datos de renta disponible por barrio de Barcelona (2015-2023). Ayúdame a identificar los endpoints disponibles, el formato de respuesta, y cualquier limitación de rate limit o autenticación. Si no hay API pública, identifica alternativas (scraping, descarga de CSV, etc.)."

---

**¡Éxito en el Sprint 1! 🚀**

