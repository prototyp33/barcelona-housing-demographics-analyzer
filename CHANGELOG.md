# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Estructura organizativa IT Project Management
- Templates de issues mejorados (bug, feature, epic)
- Workflows de GitHub Actions (CI, ETL, data-quality)
- Sistema de labels estratificado por sprint y área
- Script de tracking de milestones

### Changed
- Reorganización de documentación en subdirectorios

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
[Unreleased]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/prototyp33/barcelona-housing-demographics-analyzer/releases/tag/v0.0.1

