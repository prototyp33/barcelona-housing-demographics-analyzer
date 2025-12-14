#!/usr/bin/env python3
"""
Script para crear las issues restantes del roadmap (Sprints 2-4).

Uso:
    python scripts/create_remaining_issues.py [--dry-run] [--sprint N]

Requiere:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh cli
    - pip install requests

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/create_remaining_issues.py --dry-run  # Verificar
    python scripts/create_remaining_issues.py            # Crear todas
    python scripts/create_remaining_issues.py --sprint 2   # Solo Sprint 2
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

# Configuración
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Intentar obtener token de gh cli si no hay variable de entorno
if not GITHUB_TOKEN:
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            GITHUB_TOKEN = result.stdout.strip()
    except Exception:
        pass

REPO_OWNER = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
API_BASE = "https://api.github.com"

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================================================================
# DEFINICIÓN DE ISSUES RESTANTES (Sprints 2-4)
# ==============================================================================
REMAINING_ISSUES = [
    {
        "title": "[FEATURE-07] POI Analysis con OpenStreetMap",
        "body": """## 🎯 Objetivo

Enriquecer cada barrio con análisis de densidad de Puntos de Interés (POI) usando datos de OpenStreetMap, calculando scores de conveniencia y calidad de vida.

## 📋 Contexto

**Feature ID:** #07 del análisis comparativo
**Sprint:** Sprint 2 (Semanas 3-4) - Analytics Avanzado
**Esfuerzo estimado:** 38 horas (3-4 semanas)
**Dependencias:** Ninguna

Los POIs (supermercados, farmacias, parques, colegios) son factores críticos en decisiones de compra/alquiler. OSM proporciona datos gratuitos y actualizados vía Overpass API.

## ✨ Features

- [ ] Extractor OSM con Overpass API (`src/extraction/osm_extractor.py`)
- [ ] Cálculo de densidad POI por barrio (POIs/km²)
- [ ] Score de conveniencia (0-100) ponderado por tipo
- [ ] Nueva tabla `fact_infraestructura` en SQLite
- [ ] Widget en dashboard con heatmap de POIs

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/extraction/osm_extractor.py` - Cliente Overpass API
- `src/analytics/poi_scoring.py` - Cálculo de scores
- `src/app/components/poi_widget.py` - Visualización Streamlit

**Modificaciones:**
- `src/database_setup.py` - Nueva tabla fact_infraestructura
- `src/etl/pipeline.py` - Integrar extractor OSM
- `tests/test_poi_analysis.py` - Tests unitarios

## 📊 Categorías de POI

1. **Esenciales** (peso 40%): Supermercados, farmacias, cajeros
2. **Educación** (peso 25%): Colegios, bibliotecas, guarderías
3. **Salud** (peso 20%): CAPs, hospitales, clínicas
4. **Ocio** (peso 10%): Restaurantes, gimnasios, cines
5. **Espacios Verdes** (peso 5%): Parques, zonas deportivas

## ✅ Criterios de Aceptación

- [ ] Extractor funcional con rate limiting (1 req/5s)
- [ ] 73 barrios con scores calculados
- [ ] Heatmap interactivo en dashboard
- [ ] Tests con cobertura >80%
- [ ] Documentación en `docs/features/feature-07-poi-analysis.md`
- [ ] Tiempo ejecución <5 min para 73 barrios

## 📈 KPIs

- **Cobertura:** 100% de barrios con al menos 3 categorías
- **Accuracy:** Validación manual de 5 barrios (±10% error)
- **Performance:** <5 minutos ejecución completa

## 🔗 Recursos

- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [GeoPandas Docs](https://geopandas.org/en/stable/)
- Ejemplo query: [POI Density BCN](https://overpass-turbo.eu/)

## 🚧 Riesgos

- **Rate limiting OSM:** Mitigado con delays y caching
- **Calidad datos OSM:** Algunas zonas pueden tener gaps → Validar manualmente""",
        "labels": ["sprint-2", "priority-high", "type-feature", "area-analytics", "area-etl", "good-first-issue"],
        "milestone": 1,  # Quick Wins Foundation
    },
    {
        "title": "[FEATURE-24] Sistema de Temas Light/Dark",
        "body": """## 🎯 Objetivo

Implementar sistema de temas claro/oscuro en el dashboard Streamlit para mejorar UX y accesibilidad.

## 📋 Contexto

**Feature ID:** #24 del análisis comparativo
**Sprint:** Sprint 2 (Semanas 3-4) - Analytics Avanzado
**Esfuerzo estimado:** 14 horas (1-2 semanas)
**Dependencias:** Ninguna

## ✨ Features

- [ ] Toggle de tema en sidebar (Light/Dark/Auto)
- [ ] Persistencia de preferencia en session_state
- [ ] Paleta de colores optimizada para ambos temas
- [ ] Compatibilidad con todos los componentes existentes

## 🏗️ Componentes Técnicos

**Modificaciones:**
- `.streamlit/config.toml` - Configuración de temas
- `src/app/utils/theme_manager.py` - Lógica de cambio de tema
- `src/app/pages/*.py` - Actualizar componentes para soportar temas

## ✅ Criterios de Aceptación

- [ ] Toggle funcional en todas las páginas
- [ ] Persistencia entre sesiones
- [ ] Sin regresiones visuales
- [ ] Tests de UI básicos

## 📈 KPIs

- **Adopción:** >30% usuarios usan dark mode
- **Performance:** Sin impacto en tiempo de carga""",
        "labels": ["sprint-2", "priority-low", "type-feature", "area-ui", "good-first-issue"],
        "milestone": 1,  # Quick Wins Foundation
    },
    {
        "title": "[FEATURE-01] Motor de Predicción de Precios con ML",
        "body": """## 🎯 Objetivo

Desarrollar modelo de Machine Learning para predecir precios de vivienda por barrio con intervalos de confianza.

## 📋 Contexto

**Feature ID:** #01 del análisis comparativo
**Sprint:** Sprint 3 (Semanas 5-6) - ML Core
**Esfuerzo estimado:** 56 horas (5-6 semanas)
**Dependencias:** Datos históricos completos (fact_precios)

## ✨ Features

- [ ] Pipeline de feature engineering
- [ ] Entrenamiento de modelos (Linear, XGBoost, Random Forest)
- [ ] Cross-validation y hyperparameter tuning
- [ ] UI de predicciones en Streamlit
- [ ] Backtesting con datos históricos
- [ ] Model versioning básico

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/ml/feature_engineering.py` - Pipeline de features
- `src/ml/models.py` - Modelos ML
- `src/ml/predictor.py` - API de predicción
- `src/app/pages/ml_predictions.py` - UI Streamlit
- `tests/test_ml_predictor.py` - Tests unitarios

**Modificaciones:**
- `requirements.txt` - Añadir scikit-learn, xgboost, mlflow

## ✅ Criterios de Aceptación

- [ ] Modelo con MAE < 15% en precio medio
- [ ] Predicciones para los 73 barrios
- [ ] Visualización de intervalos de confianza
- [ ] Documentación de metodología
- [ ] Tests con cobertura >80%

## 📈 KPIs

- **Accuracy:** MAE < 15% del precio medio
- **Coverage:** 100% de barrios con predicción
- **Performance:** <2s tiempo de predicción

## 🔗 Recursos

- [Scikit-learn Docs](https://scikit-learn.org/)
- [XGBoost Docs](https://xgboost.readthedocs.io/)""",
        "labels": ["sprint-3", "priority-critical", "type-feature", "area-ml", "epic"],
        "milestone": 2,  # Core ML Engine
    },
    {
        "title": "[FEATURE-11] Análisis de Ciclos con Series Temporales",
        "body": """## 🎯 Objetivo

Implementar análisis de tendencias y ciclos estacionales en precios usando técnicas de series temporales.

## 📋 Contexto

**Feature ID:** #11 del análisis comparativo
**Sprint:** Sprint 3 (Semanas 5-6) - ML Core
**Esfuerzo estimado:** 56 horas (5-6 semanas)
**Dependencias:** Datos históricos completos (fact_precios)

## ✨ Features

- [ ] Descomposición de series temporales (tendencia, estacionalidad, residual)
- [ ] Detección de puntos de inflexión
- [ ] Predicción con ARIMA/SARIMA
- [ ] Visualización de ciclos en dashboard

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/ml/time_series.py` - Análisis de series temporales
- `src/app/pages/time_series_analysis.py` - UI Streamlit
- `tests/test_time_series.py` - Tests unitarios

**Modificaciones:**
- `requirements.txt` - Añadir statsmodels, prophet (opcional)

## ✅ Criterios de Aceptación

- [ ] Descomposición funcional para 73 barrios
- [ ] Detección de tendencias significativas
- [ ] Visualización interactiva de ciclos
- [ ] Tests con cobertura >80%

## 📈 KPIs

- **Accuracy:** RMSE < 20% en predicciones
- **Coverage:** 100% de barrios con análisis""",
        "labels": ["sprint-3", "priority-high", "type-feature", "area-ml", "area-analytics"],
        "milestone": 2,  # Core ML Engine
    },
    {
        "title": "[FEATURE-06] Métricas de Accesibilidad y Transporte",
        "body": """## 🎯 Objetivo

Calcular métricas de accesibilidad por barrio basadas en proximidad a transporte público y conectividad.

## 📋 Contexto

**Feature ID:** #06 del análisis comparativo
**Sprint:** Sprint 4 (Semanas 7-8) - Data Expansion
**Esfuerzo estimado:** 44 horas (4-5 semanas)
**Dependencias:** Datos de transporte público (TMB, Renfe)

## ✨ Features

- [ ] Extractor de datos de transporte (TMB API, OpenStreetMap)
- [ ] Cálculo de distancia a estaciones de metro/bus
- [ ] Score de accesibilidad (0-100)
- [ ] Visualización en mapa interactivo

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/extraction/transport_extractor.py` - Extracción de datos transporte
- `src/analytics/accessibility_scoring.py` - Cálculo de scores
- `src/app/components/accessibility_map.py` - Visualización

**Modificaciones:**
- `src/database_setup.py` - Nueva tabla fact_accesibilidad
- `src/etl/pipeline.py` - Integrar extractor transporte

## ✅ Criterios de Aceptación

- [ ] 73 barrios con métricas calculadas
- [ ] Mapa interactivo con estaciones
- [ ] Tests con cobertura >80%
- [ ] Documentación completa

## 📈 KPIs

- **Cobertura:** 100% de barrios con métricas
- **Accuracy:** Validación manual de 5 barrios""",
        "labels": ["sprint-4", "priority-high", "type-feature", "area-analytics", "area-etl"],
        "milestone": 3,  # Data Expansion
    },
    {
        "title": "[FEATURE-19] Índice de Calidad Ambiental",
        "body": """## 🎯 Objetivo

Desarrollar índice compuesto de calidad ambiental por barrio basado en ruido, calidad del aire y espacios verdes.

## 📋 Contexto

**Feature ID:** #19 del análisis comparativo
**Sprint:** Sprint 4 (Semanas 7-8) - Data Expansion
**Esfuerzo estimado:** 38 horas (3-4 semanas)
**Dependencias:** Datos ambientales (Open Data BCN)

## ✨ Features

- [ ] Extractor de datos ambientales (ruido, calidad aire)
- [ ] Cálculo de índice compuesto (0-100)
- [ ] Visualización en dashboard
- [ ] Correlación con precios

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/extraction/environmental_extractor.py` - Extracción datos ambientales
- `src/analytics/environmental_index.py` - Cálculo de índice
- `src/app/components/environmental_widget.py` - Visualización

**Modificaciones:**
- `src/database_setup.py` - Nueva tabla fact_ambiental
- `src/etl/pipeline.py` - Integrar extractor ambiental

## ✅ Criterios de Aceptación

- [ ] 73 barrios con índice calculado
- [ ] Visualización interactiva
- [ ] Tests con cobertura >80%
- [ ] Documentación completa

## 📈 KPIs

- **Cobertura:** 100% de barrios con índice
- **Accuracy:** Validación con datos oficiales""",
        "labels": ["sprint-4", "priority-medium", "type-feature", "area-analytics", "area-etl"],
        "milestone": 3,  # Data Expansion
    },
    {
        "title": "[FEATURE-03] Índice Multi-dimensional de Gentrificación",
        "body": """## 🎯 Objetivo

Desarrollar índice compuesto que mide el riesgo/potencial de gentrificación por barrio usando múltiples indicadores.

## 📋 Contexto

**Feature ID:** #03 del análisis comparativo
**Sprint:** Sprint 4 (Semanas 7-8) - Data Expansion
**Esfuerzo estimado:** 38 horas (4 semanas)
**Dependencias:** Datos demográficos y de precios históricos

## ✨ Features

- [ ] Definición de indicadores (precio, renta, demografía, POI)
- [ ] Cálculo del índice compuesto (0-100)
- [ ] Visualización de "heatmap de riesgo"
- [ ] Comparativa temporal (2015-2025)

## 🏗️ Componentes Técnicos

**Nuevos archivos:**
- `src/analytics/gentrification_index.py` - Cálculo del índice
- `src/app/pages/gentrification_analysis.py` - UI Streamlit
- `tests/test_gentrification.py` - Tests unitarios

**Modificaciones:**
- `src/database_setup.py` - Nueva tabla fact_gentrificacion
- `src/etl/pipeline.py` - Integrar cálculo de índice

## ✅ Criterios de Aceptación

- [ ] Índice calculado para 73 barrios
- [ ] Heatmap interactivo en dashboard
- [ ] Análisis temporal funcional
- [ ] Tests con cobertura >80%
- [ ] Documentación metodológica completa

## 📈 KPIs

- **Cobertura:** 100% de barrios con índice
- **Accuracy:** Validación con estudios académicos
- **Performance:** <3s cálculo completo

## 🔗 Recursos

- [Estudios gentrificación Barcelona](https://www.ub.edu/geocrit/b3w-1095.htm)
- [Metodología índices compuestos](https://www.sciencedirect.com/topics/social-sciences/composite-index)""",
        "labels": ["sprint-4", "priority-high", "type-feature", "area-analytics", "epic"],
        "milestone": 3,  # Data Expansion
    },
]


def get_headers() -> Dict[str, str]:
    """
    Genera headers para la API de GitHub.

    Returns:
        Dict con headers de autorización.

    Raises:
        ValueError: Si GITHUB_TOKEN no está configurado.
    """
    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN no configurado. "
            "Exporta la variable: export GITHUB_TOKEN='ghp_xxxx' "
            "o autentícate con: gh auth login"
        )
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_milestone_number(milestone_id: int) -> Optional[int]:
    """
    Obtiene el número del milestone por su ID interno.

    Args:
        milestone_id: ID interno (1=Quick Wins, 2=Core ML, 3=Data Expansion, 4=Showcase).

    Returns:
        Número del milestone en GitHub o None si no existe.
    """
    milestone_titles = {
        1: "Quick Wins Foundation",
        2: "Core ML Engine",
        3: "Data Expansion",
        4: "Differentiation Showcase",
    }

    title = milestone_titles.get(milestone_id)
    if not title:
        return None

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones"
    params = {"state": "all", "per_page": 100}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        milestones = response.json()
        for milestone in milestones:
            if milestone["title"].lower() == title.lower():
                return milestone["number"]
        return None
    except requests.RequestException as e:
        logger.error(f"Error al obtener milestones: {e}")
        return None


def create_issue(issue_data: Dict, dry_run: bool = False) -> Optional[int]:
    """
    Crea una nueva issue en el repositorio.

    Args:
        issue_data: Datos de la issue.
        dry_run: Si True, solo simula la operación.

    Returns:
        Número de la issue creada o None si falló.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía issue: {issue_data['title']}")
        logger.info(f"  Labels: {', '.join(issue_data['labels'])}")
        if issue_data.get('milestone'):
            logger.info(f"  Milestone: {issue_data['milestone']}")
        return None

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    data = {
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": issue_data["labels"],
    }

    # Añadir milestone si está especificado
    if "milestone" in issue_data and issue_data["milestone"]:
        milestone_number = get_milestone_number(issue_data["milestone"])
        if milestone_number:
            data["milestone"] = milestone_number
        else:
            logger.warning(f"Milestone #{issue_data['milestone']} no encontrado, creando issue sin milestone")

    try:
        response = requests.post(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        issue = response.json()
        logger.info(f"✅ Issue creada: {issue_data['title']} (#{issue['number']})")
        logger.info(f"   URL: {issue['html_url']}")
        return issue["number"]
    except requests.RequestException as e:
        logger.error(f"❌ Error al crear issue {issue_data['title']}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"   Respuesta: {e.response.text}")
        return None


def create_all_issues(dry_run: bool = False, sprint_filter: Optional[int] = None) -> None:
    """
    Crea todas las issues restantes.

    Args:
        dry_run: Si True, solo simula la operación.
        sprint_filter: Si se especifica, solo crea issues de ese sprint (2, 3, o 4).
    """
    created = 0
    failed = 0
    skipped = 0

    for issue_data in REMAINING_ISSUES:
        # Filtrar por sprint si se especifica
        if sprint_filter:
            sprint_label = f"sprint-{sprint_filter}"
            if sprint_label not in issue_data["labels"]:
                skipped += 1
                continue

        issue_number = create_issue(issue_data, dry_run)
        if issue_number:
            created += 1
        else:
            if not dry_run:
                failed += 1

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE CREACIÓN")
    print("=" * 50)
    print(f"✅ Issues creadas: {created}")
    if skipped > 0:
        print(f"⏭️ Issues omitidas: {skipped}")
    if failed > 0:
        print(f"❌ Issues fallidas: {failed}")
    print("=" * 50)

    if dry_run:
        print("\n⚠️ Modo DRY-RUN: No se crearon issues reales.")
        print("   Ejecuta sin --dry-run para crear las issues.")


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Crea las issues restantes del roadmap (Sprints 2-4)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular cambios sin aplicarlos"
    )
    parser.add_argument(
        "--sprint",
        type=int,
        choices=[2, 3, 4],
        help="Crear solo issues de un sprint específico"
    )

    args = parser.parse_args()

    try:
        create_all_issues(dry_run=args.dry_run, sprint_filter=args.sprint)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

