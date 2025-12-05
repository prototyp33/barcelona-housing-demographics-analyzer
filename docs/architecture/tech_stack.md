# 🛠️ Tech Stack - Barcelona Housing Demographics Analyzer

## Visión General

Este documento describe las tecnologías utilizadas en el proyecto, sus versiones, y las razones de su elección.

## Stack Principal

### Lenguaje

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.11+ | Lenguaje principal del proyecto |

**Justificación:** Python es el estándar para análisis de datos, con excelente soporte para pandas, ML, y visualización.

### Data Processing

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **pandas** | 2.x | Manipulación y análisis de datos |
| **NumPy** | 1.x | Operaciones numéricas |
| **GeoPandas** | 0.14+ | Datos geoespaciales y GeoJSON |

### Database

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **SQLite** | 3.x | Base de datos embebida |

**Justificación:** 
- Zero-config: No requiere servidor separado
- Portabilidad: Un archivo `.db` fácil de distribuir
- Suficiente para el volumen de datos (~100K registros)
- Soporte nativo en Python

### Visualization & Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Streamlit** | 1.29+ | Dashboard interactivo |
| **Plotly** | 5.x | Gráficos interactivos |
| **Folium** | 0.15+ | Mapas interactivos |

**Justificación de Streamlit sobre Dash:**
- Menor curva de aprendizaje
- Deployment gratuito en Streamlit Cloud
- Mejor para prototyping rápido
- Comunidad activa

### Machine Learning (Planificado)

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **scikit-learn** | 1.x | Clustering, regresión |
| **XGBoost** | 2.x | Predicción de precios |

### Testing & Quality

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **pytest** | 7.x | Framework de testing |
| **pytest-cov** | 4.x | Coverage de código |
| **ruff** | 0.1+ | Linting y formatting |
| **mypy** | 1.x | Type checking |

### DevOps & CI/CD

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **GitHub Actions** | - | CI/CD pipelines |
| **Docker** | - | Containerización |
| **Streamlit Cloud** | - | Hosting del dashboard |

## Arquitectura de Dependencias

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Streamlit  │  │   Plotly    │  │   Folium    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      ANALYTICS                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  pandas     │  │ scikit-learn│  │  XGBoost    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   SQLite    │  │  GeoPandas  │  │   NumPy     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Versiones Pinneadas

Ver `requirements.txt` para versiones exactas. Política de actualización:

- **Major versions**: Evaluar breaking changes, actualizar en sprints de mantenimiento
- **Minor versions**: Actualizar mensualmente via Dependabot
- **Patch versions**: Actualizar inmediatamente (seguridad)

## Alternativas Consideradas

### SQLite vs PostgreSQL

| Criterio | SQLite | PostgreSQL |
|----------|--------|------------|
| Setup | ✅ Zero-config | ❌ Servidor requerido |
| Concurrencia | ❌ Limitada | ✅ Excelente |
| Portabilidad | ✅ Archivo único | ❌ Requiere instalación |
| Volumen | ✅ OK para <1M filas | ✅ Ilimitado |
| **Decisión** | **Elegido** | Considerar si escala |

### Streamlit vs Dash

| Criterio | Streamlit | Dash |
|----------|-----------|------|
| Curva aprendizaje | ✅ Muy baja | ❌ Moderada |
| Flexibilidad UI | ❌ Limitada | ✅ Alta |
| Hosting gratuito | ✅ Streamlit Cloud | ❌ Heroku (limitado) |
| Comunidad | ✅ Muy activa | ✅ Activa |
| **Decisión** | **Elegido** | Buena alternativa |

## Actualizaciones Futuras

### Q1 2025
- [ ] Evaluar FastAPI para API REST (Feature #28)
- [ ] Considerar Redis para caching si hay problemas de performance

### Q2 2025
- [ ] Evaluar mlflow para tracking de modelos ML
- [ ] Considerar Apache Airflow si ETL se complejiza

