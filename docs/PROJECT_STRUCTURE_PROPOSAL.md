# Propuesta de Reorganización: Estructura del Proyecto

**Fecha**: 2025-12-19  
**Contexto**: Proyecto Python (ETL + Análisis + Dashboard) con múltiples componentes  
**Objetivo**: Estructura escalable, predecible y fácil de navegar

---

## 📊 Análisis de la Estructura Actual

### Stack Identificado
- **Lenguaje**: Python 3.9+
- **Componentes principales**:
  - ETL Pipeline (extracción, transformación, carga)
  - Análisis de datos (Jupyter notebooks)
  - Dashboard Streamlit
  - Spike de validación (temporal pero extenso)

### Problemas Identificados

1. **Scripts dispersos**: 
   - `scripts/` tiene 71 archivos (difícil navegar)
   - `spike-data-validation/scripts/` tiene 33 archivos
   - Sin organización clara por feature/componente

2. **Documentación dispersa**:
   - `docs/` tiene 50+ archivos sin estructura clara
   - Mezcla de planning, arquitectura, guías, reports

3. **Spike como subproyecto**:
   - `spike-data-validation/` es temporal pero tiene estructura completa
   - Puede confundir qué es código "oficial" vs "spike"

4. **Dependencias no claras**:
   - Scripts que importan de `src/` y viceversa
   - Sin documentación de dependencias entre módulos

---

## 🎯 Propuesta: Estructura por Feature/Componente

### Principios de Diseño

1. **Separación clara**: Código de producción vs scripts temporales vs spikes
2. **Feature-based**: Agrupar por funcionalidad (Catastro, Portal Dades, etc.)
3. **Límites explícitos**: Documentar qué módulos pueden importar qué
4. **Escalabilidad**: Fácil añadir nuevas features sin desorganizar

### Estructura Propuesta

```
barcelona-housing-demographics-analyzer/
├── src/                          # Código de producción (módulos reutilizables)
│   ├── extraction/              # Extractores por fuente de datos
│   │   ├── __init__.py
│   │   ├── base.py              # BaseExtractor (público)
│   │   ├── catastro/            # Feature: Catastro
│   │   │   ├── __init__.py
│   │   │   ├── soap_client.py   # Cliente SOAP oficial
│   │   │   ├── oficial_client.py # Cliente consulta masiva
│   │   │   └── parsers.py       # Parsers XML (público)
│   │   ├── portaldades/         # Feature: Portal Dades
│   │   │   ├── __init__.py
│   │   │   └── extractor.py
│   │   └── ...                  # Otras fuentes
│   ├── etl/                     # Pipeline ETL
│   │   ├── __init__.py
│   │   ├── pipeline.py          # Orquestador principal
│   │   ├── transformations/     # Transformaciones por dominio
│   │   │   ├── __init__.py
│   │   │   ├── precios.py
│   │   │   └── demografia.py
│   │   └── validators.py        # Validaciones (público)
│   ├── database/                # Acceso a base de datos
│   │   ├── __init__.py
│   │   ├── schema.py            # Definición de schema
│   │   └── repository.py       # Repositorios tipados (público)
│   ├── analysis/                # Funciones analíticas
│   │   ├── __init__.py
│   │   └── models.py            # Modelos ML/estadísticos
│   └── app/                     # Dashboard Streamlit
│       ├── __init__.py
│       ├── main.py
│       └── pages/
│
├── scripts/                     # Scripts ejecutables (CLI tools)
│   ├── etl/                     # Scripts ETL por feature
│   │   ├── run_full_etl.py
│   │   └── extract_catastro.py
│   ├── analysis/                # Scripts de análisis
│   │   └── train_models.py
│   ├── maintenance/             # Scripts de mantenimiento
│   │   ├── validate_data.py
│   │   └── cleanup.py
│   └── utils/                   # Utilidades compartidas
│       └── setup_logging.py
│
├── spikes/                      # Spikes temporales (experimentación)
│   ├── data-validation/         # Spike actual
│   │   ├── scripts/             # Scripts específicos del spike
│   │   ├── notebooks/           # Notebooks del spike
│   │   ├── data/                # Datos del spike
│   │   └── docs/                # Documentación del spike
│   └── README.md                # Guía: qué es un spike, cuándo migrar
│
├── notebooks/                   # Notebooks de análisis (producción)
│   ├── 01_eda.ipynb
│   └── 02_analysis.ipynb
│
├── tests/                       # Tests organizados por feature
│   ├── unit/
│   │   ├── extraction/
│   │   ├── etl/
│   │   └── database/
│   ├── integration/
│   └── fixtures/
│
├── docs/                        # Documentación organizada
│   ├── architecture/            # Decisiones de arquitectura
│   ├── guides/                  # Guías de uso
│   ├── api/                     # Documentación de APIs
│   ├── planning/                # Planning y roadmaps
│   └── spikes/                  # Documentación de spikes
│
├── data/                        # Datos (sin cambios)
│   ├── raw/
│   └── processed/
│
└── README.md                    # Actualizar con estructura oficial
```

---

## 🔄 Plan de Migración Gradual

### Fase 1: Reorganizar Scripts (Impacto Bajo)

**Objetivo**: Agrupar scripts por feature sin romper imports.

**Acciones**:
1. Crear estructura `scripts/etl/`, `scripts/analysis/`, `scripts/maintenance/`
2. Mover scripts relacionados con Catastro a `scripts/etl/catastro/`
3. Mover scripts de análisis/modelos a `scripts/analysis/`
4. Actualizar imports en scripts movidos
5. Documentar nueva estructura en `docs/guides/SCRIPTS_ORGANIZATION.md`

**Scripts a mover**:
- `scripts/extract_*.py` → `scripts/etl/extraction/`
- `scripts/train_*.py` → `scripts/analysis/`
- `scripts/validate_*.py` → `scripts/maintenance/`

**Riesgo**: Bajo (solo scripts ejecutables, no módulos importados)

---

### Fase 2: Consolidar Código de Catastro (Impacto Medio)

**Objetivo**: Mover código reutilizable de `spike-data-validation/scripts/` a `src/extraction/catastro/`.

**Código candidato**:
- `catastro_soap_client.py` → `src/extraction/catastro/soap_client.py`
- `catastro_oficial_client.py` → `src/extraction/catastro/oficial_client.py`
- `parse_catastro_masivo_output.py` → `src/extraction/catastro/parsers.py`

**Acciones**:
1. Crear `src/extraction/catastro/`
2. Mover clientes y parsers
3. Actualizar imports en scripts del spike
4. Mantener scripts del spike en `spikes/data-validation/scripts/` que importen de `src/`

**Beneficio**: Código reutilizable disponible para producción

---

### Fase 3: Reorganizar Documentación (Impacto Bajo)

**Objetivo**: Estructura clara de documentación.

**Acciones**:
1. Crear `docs/architecture/`, `docs/guides/`, `docs/planning/`
2. Mover ADRs a `docs/architecture/adrs/`
3. Mover guías de uso a `docs/guides/`
4. Mover planning/roadmaps a `docs/planning/`
5. Crear `docs/README.md` con índice

**Archivos a mover**:
- `docs/BEST_PRACTICES_*.md` → `docs/guides/`
- `docs/PROJECT_*.md` → `docs/planning/`
- `docs/architecture/*.md` → Ya está bien ubicado

---

### Fase 4: Clarificar Dependencias (Impacto Alto)

**Objetivo**: Documentar y hacer cumplir límites de dependencias.

**Reglas propuestas**:

```
src/                    → Puede importar: stdlib, third-party, src/* (sin ciclos)
scripts/                → Puede importar: stdlib, third-party, src/*
spikes/*/scripts/       → Puede importar: stdlib, third-party, src/* (NO scripts/)
notebooks/              → Puede importar: stdlib, third-party, src/*
tests/                  → Puede importar: stdlib, third-party, src/*, tests/fixtures/
```

**Acciones**:
1. Crear `docs/architecture/DEPENDENCIES.md` con reglas explícitas
2. Añadir validación en CI/CD (opcional, con `import-linter` o similar)
3. Documentar en `CONTRIBUTING.md`

---

## 📋 Checklist de Implementación

### Inmediato (Sin Romper Código)
- [ ] Crear `docs/PROJECT_STRUCTURE.md` con estructura oficial
- [ ] Documentar reglas de dependencias en `docs/architecture/DEPENDENCIES.md`
- [ ] Crear `spikes/README.md` explicando qué es un spike y cuándo migrar código

### Corto Plazo (1-2 semanas)
- [ ] Reorganizar `scripts/` por feature (Fase 1)
- [ ] Reorganizar `docs/` por tipo (Fase 3)
- [ ] Actualizar `README.md` con estructura oficial

### Medio Plazo (1 mes)
- [ ] Consolidar código reutilizable de spike a `src/` (Fase 2)
- [ ] Implementar validación de dependencias (Fase 4)
- [ ] Migrar scripts del spike a usar módulos de `src/`

---

## 🎯 Beneficios Esperados

1. **Navegación más rápida**: Encontrar código por feature en lugar de buscar en 71 archivos
2. **Onboarding más fácil**: Estructura predecible para nuevos desarrolladores
3. **Menos acoplamiento**: Límites claros evitan dependencias cíclicas
4. **Reutilización**: Código del spike disponible para producción
5. **Mantenibilidad**: Cambios en una feature no afectan otras

---

## ⚠️ Consideraciones

### No Mover (Por Ahora)
- `data/` - Estructura actual es clara
- `tests/` - Estructura actual funciona bien
- `notebooks/` - Ubicación actual es adecuada

### Migración Gradual
- No hacer grandes movimientos de una vez
- Migrar por feature/componente
- Mantener compatibilidad durante transición
- Documentar cambios en `CHANGELOG.md`

### Spikes
- Mantener `spikes/` separado de producción
- Documentar cuándo migrar código de spike a producción
- Limpiar spikes completados periódicamente

---

## 📚 Referencias

- [Python Project Structure Best Practices](https://docs.python-guide.org/writing/structure/)
- [Modularization Guide](https://www.linkedin.com/pulse/modularization-android-projects-kotlin-how-structure-your-levindo-8ipmf)
- [Large Codebase Organization](https://graphite.com/guides/how-to-organize-large-codebases-efficient-reviews)

---

**Próximos pasos**: Revisar esta propuesta y decidir qué fases implementar primero.

