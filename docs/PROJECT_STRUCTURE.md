# Estructura Oficial del Proyecto

**Última actualización**: 2025-12-19  
**Estado**: Estructura oficial documentada

---

## 📐 Estructura de Directorios

```
barcelona-housing-demographics-analyzer/
├── src/                    # Código de producción (módulos reutilizables)
│   ├── extraction/         # Extractores por fuente de datos
│   │   ├── base.py         # BaseExtractor (público)
│   │   ├── opendata.py     # OpenDataBCNExtractor
│   │   ├── idealista.py    # IdealistaExtractor
│   │   ├── portaldades.py  # PortalDadesExtractor
│   │   └── ...             # INE, IDESCAT, Incasol
│   ├── etl/                # Pipeline ETL
│   │   ├── pipeline.py     # Orquestador principal
│   │   ├── transformations/ # Transformaciones por dominio
│   │   └── validators.py   # Validaciones (público)
│   ├── database/           # Acceso a base de datos
│   │   ├── schema.py       # Definición de schema
│   │   └── repository.py   # Repositorios tipados (público)
│   ├── analysis/           # Funciones analíticas
│   │   └── models.py       # Modelos ML/estadísticos
│   └── app/                # Dashboard Streamlit
│       ├── main.py
│       └── pages/
│
├── scripts/                # Scripts ejecutables (CLI tools)
│   ├── etl/                # Scripts ETL por feature
│   │   ├── extract_catastro.py
│   │   └── run_full_etl.py
│   ├── analysis/           # Scripts de análisis
│   │   └── train_models.py
│   ├── maintenance/        # Scripts de mantenimiento
│   │   ├── validate_data.py
│   │   └── cleanup.py
│   └── utils/              # Utilidades compartidas
│       └── setup_logging.py
│
├── spikes/                 # Spikes temporales (experimentación)
│   ├── data-validation/   # Spike actual (Issue #198-#204)
│   │   ├── scripts/        # Scripts específicos del spike
│   │   ├── notebooks/       # Notebooks del spike
│   │   ├── data/          # Datos del spike
│   │   └── docs/          # Documentación del spike
│   └── README.md          # Guía de spikes
│
├── notebooks/              # Notebooks de análisis (producción)
│   ├── 01_eda.ipynb
│   └── 02_analysis.ipynb
│
├── tests/                  # Tests organizados por feature
│   ├── unit/
│   │   ├── extraction/
│   │   ├── etl/
│   │   └── database/
│   ├── integration/
│   └── fixtures/
│
├── docs/                   # Documentación organizada
│   ├── architecture/       # Decisiones de arquitectura
│   │   ├── DEPENDENCIES.md # Reglas de dependencias
│   │   └── adrs/          # Architecture Decision Records
│   ├── guides/            # Guías de uso
│   ├── planning/          # Planning y roadmaps
│   └── spikes/            # Documentación de spikes
│
└── data/                   # Datos (inmutable)
    ├── raw/               # Datos brutos de fuentes (NUNCA modificar)
    └── processed/         # Datos transformados + database.db
```

---

## 🎯 Principios de Organización

### 1. Separación por Responsabilidad

- **`src/`**: Código de producción, módulos reutilizables
- **`scripts/`**: Scripts ejecutables, herramientas CLI
- **`spikes/`**: Investigaciones temporales, experimentación
- **`notebooks/`**: Análisis exploratorio de producción
- **`tests/`**: Tests automatizados
- **`docs/`**: Documentación organizada por tipo

### 2. Organización por Feature

Los scripts y módulos se agrupan por funcionalidad:
- `scripts/etl/catastro/` - Scripts relacionados con Catastro
- `scripts/etl/portaldades/` - Scripts relacionados con Portal Dades
- `src/extraction/catastro/` - Módulos de extracción de Catastro

### 3. Límites Explícitos

Cada directorio tiene reglas claras de qué puede importar:
- Ver [`docs/architecture/DEPENDENCIES.md`](architecture/DEPENDENCIES.md) para reglas completas

---

## 📋 Convenciones de Nombres

### Archivos Python
- **Módulos**: `snake_case.py` (ej: `catastro_soap_client.py`)
- **Clases**: `PascalCase` (ej: `CatastroSOAPClient`)
- **Funciones**: `snake_case` (ej: `parse_xml()`)

### Directorios
- **Features**: `snake_case` (ej: `data-validation/`)
- **Módulos**: `snake_case` (ej: `extraction/`, `etl/`)

### Scripts Ejecutables
- Prefijo descriptivo: `extract_`, `train_`, `validate_`
- Ejemplos: `extract_catastro.py`, `train_macro_baseline.py`

---

## 🔄 Flujo de Código

### De Spike a Producción

1. **Código en spike** → Desarrollar y validar en `spikes/data-validation/`
2. **Validación** → Verificar que es reutilizable y bien testeado
3. **Migración** → Mover código reutilizable a `src/`
4. **Actualización** → Scripts del spike importan de `src/`
5. **Limpieza** → Eliminar código duplicado del spike

Ver [`spikes/README.md`](../../spikes/README.md) para guía completa.

---

## 📚 Documentación Relacionada

- **Propuesta de reorganización**: [`PROJECT_STRUCTURE_PROPOSAL.md`](./PROJECT_STRUCTURE_PROPOSAL.md)
- **Reglas de dependencias**: [`architecture/DEPENDENCIES.md`](./architecture/DEPENDENCIES.md)
- **Guía de spikes**: [`../../spikes/README.md`](../../spikes/README.md)
- **Guía de contribución**: [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md)

---

## ✅ Checklist para Nuevos Archivos

Antes de crear un nuevo archivo, verificar:

- [ ] ¿Está en el directorio correcto según su propósito?
- [ ] ¿Sigue las convenciones de nombres?
- [ ] ¿Los imports respetan las reglas de dependencias?
- [ ] ¿Está documentado (docstrings, comentarios)?

---

**Última actualización**: 2025-12-19

