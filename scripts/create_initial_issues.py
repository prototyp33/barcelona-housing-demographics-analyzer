#!/usr/bin/env python3
"""
Script para crear las issues iniciales del Sprint 1 usando el template epic.

Uso:
    python scripts/create_initial_issues.py [--dry-run]

Requiere:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh cli
    - pip install requests

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/create_initial_issues.py --dry-run  # Verificar
    python scripts/create_initial_issues.py            # Crear
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import Optional

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
# DEFINICIÓN DE ISSUES INICIALES (SPRINT 1)
# ==============================================================================
INITIAL_ISSUES = [
    {
        "title": "[FEATURE-02] Calculadora de Viabilidad de Inversión",
        "body": """## 🎯 Contexto
**Feature ID:** #02 del análisis comparativo
**Sprint:** Sprint 1 (Semanas 1-4) - Quick Wins
**Esfuerzo estimado:** 15-20 horas
**Dependencias:** Ninguna

## 📝 Descripción
Herramienta interactiva para evaluar la rentabilidad de inversiones inmobiliarias en Barcelona. Permitirá a los usuarios calcular ROI, Cash Flow y métricas clave considerando la fiscalidad local (ITP, AJD, IBI).

## 🔧 Componentes Técnicos
- [ ] `src/analytics/investment_calculator.py` - Lógica financiera (TIR, VAN, Amortización)
- [ ] `src/app/pages/investment_simulator.py` - Interfaz de usuario en Streamlit
- [ ] `tests/test_investment_calculator.py` - Tests unitarios de fórmulas financieras
- [ ] Actualizar `requirements.txt` con: `numpy-financial>=1.0.0`

## ✅ Criterios de Aceptación
- [ ] Cash flow mensual calculado correctamente
- [ ] Simulación de 3 escenarios (pesimista, base, optimista)
- [ ] Integración de impuestos (ITP, AJD) y gastos de comunidad
- [ ] Visualización gráfica de retorno acumulado a 10 años
- [ ] Tests unitarios con >80% cobertura
- [ ] Documentación en `docs/features/feature-02-calculator.md`

## 🧪 Plan de Testing
- [ ] Tests unitarios en `tests/test_investment_calculator.py`
- [ ] Test manual con datos reales de Barcelona
- [ ] Validación visual en Streamlit local

## 📊 Métricas de Éxito
- KPI: Tiempo de cálculo
- Target: < 500ms
- KPI: Precisión cálculos
- Target: ±0.01%

## 📚 Referencias
- [Documentación Feature #02](docs/features/feature-02-calculator.md)
- [NumPy Financial Docs](https://numpy.org/numpy-financial/)""",
        "labels": ["sprint-1", "priority-high", "type-feature", "area-analytics", "epic"],
        "milestone": 1,  # Quick Wins Foundation
    },
    {
        "title": "[FEATURE-13] Segmentación Automática de Barrios con K-Means",
        "body": """## 🎯 Contexto
**Feature ID:** #13 del análisis comparativo
**Sprint:** Sprint 1 (Semanas 1-4) - Quick Wins
**Esfuerzo estimado:** 15-18 horas
**Dependencias:** Ninguna

## 📝 Descripción
Implementación de algoritmo K-Means para agrupar los 73 barrios de Barcelona en clusters según similitud demográfica y de mercado (ej: "Alto standing", "Familiar asequible", "Oportunidad inversión").

## 🔧 Componentes Técnicos
- [ ] `src/analytics/segmentation.py` - Pipeline de preprocesamiento y modelo K-Means
- [ ] `src/app/pages/segmentation_analysis.py` - Visualización de clusters (Radar Charts)
- [ ] Base de datos: Nueva tabla `dim_segmento_barrio`
- [ ] Actualizar `requirements.txt` con: `scikit-learn>=1.0.0`

## ✅ Criterios de Aceptación
- [ ] 5-8 clusters identificados y caracterizados
- [ ] Radar charts comparativos por cluster
- [ ] Persistencia de resultados en SQLite
- [ ] Análisis de "Codo" (Elbow method) documentado para elección de K
- [ ] Tests unitarios con >80% cobertura

## 🧪 Plan de Testing
- [ ] Tests unitarios en `tests/test_segmentation.py`
- [ ] Validación de clusters con datos conocidos
- [ ] Test visual de radar charts en Streamlit

## 📊 Métricas de Éxito
- KPI: Silhouette score
- Target: > 0.5
- KPI: Número de clusters
- Target: 5-8 clusters interpretables

## 📚 Referencias
- [Scikit-learn K-Means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)""",
        "labels": ["sprint-1", "priority-high", "type-feature", "area-ml", "epic"],
        "milestone": 1,  # Quick Wins Foundation
    },
    {
        "title": "[FEATURE-05] Sistema de Notificaciones con Change Detection",
        "body": """## 🎯 Contexto
**Feature ID:** #05 del análisis comparativo
**Sprint:** Sprint 1 (Semanas 1-4) - Quick Wins
**Esfuerzo estimado:** 12-15 horas
**Dependencias:** ETL pipeline estable

## 📝 Descripción
Sistema automatizado que monitorea los datos ingresados diariamente y detecta cambios significativos (anomalías, bajadas de precio >X%, nuevos datos disponibles) enviando alertas por email.

## 🔧 Componentes Técnicos
- [ ] `src/monitoring/change_detector.py` - Lógica de detección de cambios
- [ ] `src/monitoring/alerting.py` - Sistema de envío (Email/Telegram opcional)
- [ ] GitHub Actions: Actualizar workflow diario `.github/workflows/etl_schedule.yml`
- [ ] Tabla `etl_alerts` en base de datos

## ✅ Criterios de Aceptación
- [ ] Detecta cambios >5% en precios medios por barrio
- [ ] Email enviado en <5min desde detección en pipeline
- [ ] Log de alertas persistido en base de datos
- [ ] Configuración de umbrales vía archivo config
- [ ] Tests unitarios con >80% cobertura

## 🧪 Plan de Testing
- [ ] Tests unitarios en `tests/test_change_detector.py`
- [ ] Test de integración con datos simulados
- [ ] Validación de envío de email en staging

## 📊 Métricas de Éxito
- KPI: Tiempo de detección
- Target: < 5 minutos desde cambio
- KPI: False positives
- Target: < 5% de alertas

## 📚 Referencias
- [GitHub Actions Schedule](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)""",
        "labels": ["sprint-1", "priority-medium", "type-feature", "area-etl", "epic"],
        "milestone": 1,  # Quick Wins Foundation
    },
]


def get_headers() -> dict[str, str]:
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


def get_milestone_number(title: str) -> Optional[int]:
    """
    Obtiene el número del milestone por su título.

    Args:
        title: Título del milestone.

    Returns:
        Número del milestone o None si no existe.
    """
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


def create_issue(issue_data: dict, dry_run: bool = False) -> Optional[int]:
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
        return None

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    data = {
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": issue_data["labels"],
    }

    # Añadir milestone si está especificado
    if "milestone" in issue_data and issue_data["milestone"]:
        milestone_title = "Quick Wins Foundation"  # Por ahora solo Sprint 1
        milestone_number = get_milestone_number(milestone_title)
        if milestone_number:
            data["milestone"] = milestone_number
        else:
            logger.warning(f"Milestone '{milestone_title}' no encontrado, creando issue sin milestone")

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


def create_all_issues(dry_run: bool = False) -> None:
    """
    Crea todas las issues iniciales.

    Args:
        dry_run: Si True, solo simula la operación.
    """
    created = 0
    failed = 0

    for issue_data in INITIAL_ISSUES:
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
    if failed > 0:
        print(f"❌ Issues fallidas: {failed}")
    print("=" * 50)

    if dry_run:
        print("\n⚠️ Modo DRY-RUN: No se crearon issues reales.")
        print("   Ejecuta sin --dry-run para crear las issues.")


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Crea las issues iniciales del Sprint 1"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular cambios sin aplicarlos"
    )

    args = parser.parse_args()

    try:
        create_all_issues(dry_run=args.dry_run)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

