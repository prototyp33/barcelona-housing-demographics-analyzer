# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (Próximas mejoras en Phase 6)

---

## [1.0.0] - 2026-02-24

### Added

#### Modelo y Analytics
- **Phase 5**: Integración de Social ESG features y optimización de fairness (R²=0.81, MAE≈318€/m²)
- **Fairness A/B Harness**: Comparación de versiones de modelo para equidad (IPR gate 0.8–1.8)
- **XGBoost Valuation Model**: Predicciones de precios con penalizaciones topográficas y de accesibilidad
- **Price Predictor**: Panel interactivo de forecasting con simulador de factores
- **Market Cockpit**: KPIs reales de mercado inmobiliario
- **Market Intelligence**: Gap de negociación y semáforo de gentrificación

#### API y Backend
- **FastAPI Backend**: REST API con documentación Swagger (`/docs`)
- **Endpoints**: Predicciones XGBoost, recomendaciones de inversión, estadísticas por barrio
- **Landing page**: Documentación integrada en la API

#### ETL y Datos
- **Renta histórica**: 2015–2023 (IDESCAT/Open Data BCN)
- **Extensión renta 2024–2025**: Script forward-fill cuando no hay datos oficiales
- **Backfill demografía ampliada**: 2015–2025 desde fact_demografia
- **20+ datasets avanzados**: Educación, salud, movilidad, zonas verdes, catastro, hogares
- **Presión turística y regulación**: Datos reales integrados
- **Ruido y seguridad**: Contaminación acústica, criminalidad Mossos
- **Schema v2.0**: 8 capas fact + 2 dim, dim_tiempo, vistas analíticas
- **Tabla maestra Looker**: Export consolidado para BI

#### Dashboard y UI
- **Design System centralizado**: Paleta, tipografía, espaciado unificados
- **Vistas**: Overview, Demografía, Mapas, Inversión, ESG, Correlaciones, Data Quality
- **Accesibilidad**: Mejoras de contraste y navegación

#### Infraestructura
- **DatabaseManager**: Conexiones centralizadas, métricas de calidad
- **GitHub Actions**: CI, ETL, data-quality workflows
- **Reporte de consistencia**: Script `generate_data_consistency_report.py`
- **Documentación nulos**: `DATA_NULL_COLUMNS_DOCUMENTATION.md`

### Changed
- Migración de sistema de extracción a patrón BaseExtractor
- Mejoras en deduplicación de fact_precios
- Vistas analíticas optimizadas con CTEs
- Consolidación de bases de datos

### Fixed
- Corrección de FK violations en fact_demografia
- Fix de geometrías GeoJSON para 73 barrios
- Resolución de imports (PROFESSIONAL_COLORS, use_container_width)
- Endpoints de inversión y errores de API
- Deprecation warnings (pandas concat, Streamlit width)

### Security
- Queries parametrizadas para prevenir SQL injection

---

## [0.1.0] - 2025-11-01

### Added
- **ETL Pipeline**: Extractores para Open Data BCN, Portal de Dades, IDESCAT
- **Database**: Schema SQLite con dim_barrios, fact_precios, fact_demografia
- **Dashboard**: Aplicación Streamlit con visualizaciones interactivas
- **Data Quality**: Validadores de FK y tests de integridad
- **Notebooks**: EDA inicial y análisis de caso de estudio

### Changed
- Migración de sistema de extracción legacy a patrón BaseExtractor
- Mejoras en deduplicación de fact_precios

### Fixed
- Corrección de FK violations en fact_demografia
- Fix de geometrías GeoJSON para 73 barrios

### Security
- Implementación de queries parametrizadas para prevenir SQL injection

---

## [0.0.1] - 2025-10-15

### Added
- Estructura inicial del proyecto
- Configuración de entorno de desarrollo
- Documentación base (README, docs/)
- Primeros tests unitarios

---

<!-- Links de versiones -->
[Unreleased]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/releases/tag/v0.0.1

