#!/usr/bin/env python3
"""
Script para generar reportes semanales de progreso del proyecto.

Uso:
    python scripts/weekly_report.py [--output markdown|json|html]

Genera un resumen de:
- Issues completadas esta semana
- Issues en progreso
- Commits recientes
- Métricas del proyecto

Requiere:
    - Variable de entorno GITHUB_TOKEN con permisos de lectura
    - pip install requests

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/weekly_report.py --output markdown > weekly_report.md
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

# Configuración
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
API_BASE = "https://api.github.com"
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_headers() -> Dict[str, str]:
    """Genera headers para la API de GitHub."""
    if not GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN no configurado. Algunas funciones no estarán disponibles.")
        return {}
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_week_boundaries() -> tuple:
    """
    Calcula las fechas de inicio y fin de la semana actual.

    Returns:
        Tuple (inicio_semana, fin_semana) como strings ISO.
    """
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    return (
        start_of_week.replace(hour=0, minute=0, second=0).isoformat() + "Z",
        end_of_week.replace(hour=23, minute=59, second=59).isoformat() + "Z"
    )


def get_recent_commits(since: str, until: str) -> List[Dict[str, Any]]:
    """
    Obtiene commits del período especificado.

    Args:
        since: Fecha de inicio ISO.
        until: Fecha de fin ISO.

    Returns:
        Lista de commits.
    """
    if not GITHUB_TOKEN:
        return []

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    params = {"since": since, "until": until, "per_page": 50}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener commits: {e}")
        return []


def get_closed_issues(since: str) -> List[Dict[str, Any]]:
    """
    Obtiene issues cerradas desde la fecha especificada.

    Args:
        since: Fecha de inicio ISO.

    Returns:
        Lista de issues cerradas.
    """
    if not GITHUB_TOKEN:
        return []

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {
        "state": "closed",
        "since": since,
        "per_page": 50,
        "sort": "updated",
        "direction": "desc"
    }

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return [issue for issue in response.json() if "pull_request" not in issue]
    except requests.RequestException as e:
        logger.error(f"Error al obtener issues: {e}")
        return []


def get_open_issues() -> List[Dict[str, Any]]:
    """
    Obtiene todas las issues abiertas.

    Returns:
        Lista de issues abiertas.
    """
    if not GITHUB_TOKEN:
        return []

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {"state": "open", "per_page": 100}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return [issue for issue in response.json() if "pull_request" not in issue]
    except requests.RequestException as e:
        logger.error(f"Error al obtener issues abiertas: {e}")
        return []


def get_database_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de la base de datos del proyecto.

    Returns:
        Dict con métricas de la base de datos.
    """
    if not DB_PATH.exists():
        return {"error": "Base de datos no encontrada"}

    stats = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Contar registros en tablas principales
        tables = ["dim_barrios", "fact_precios", "fact_demografia"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[f"{table}_count"] = "N/A"

        # Última actualización de fact_precios
        try:
            cursor.execute(
                "SELECT MAX(fecha_actualizacion) FROM etl_runs WHERE status = 'success'"
            )
            result = cursor.fetchone()
            stats["last_etl_run"] = result[0] if result and result[0] else "N/A"
        except sqlite3.OperationalError:
            stats["last_etl_run"] = "N/A"

        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Error al acceder a la base de datos: {e}")
        stats["error"] = str(e)

    return stats


def get_code_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas del código fuente.

    Returns:
        Dict con métricas de código.
    """
    stats = {
        "python_files": 0,
        "total_lines": 0,
        "test_files": 0,
    }

    src_path = PROJECT_ROOT / "src"
    tests_path = PROJECT_ROOT / "tests"

    # Contar archivos Python en src/
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            stats["python_files"] += 1
            try:
                stats["total_lines"] += sum(1 for _ in py_file.open())
            except IOError:
                pass

    # Contar archivos de test
    for test_file in tests_path.glob("test_*.py"):
        stats["test_files"] += 1

    return stats


def format_markdown_report(data: Dict[str, Any]) -> str:
    """
    Genera el reporte en formato Markdown.

    Args:
        data: Datos recopilados del proyecto.

    Returns:
        String con el reporte en Markdown.
    """
    report = []

    report.append(f"# 📊 Reporte Semanal - Barcelona Housing Analyzer\n")
    report.append(f"**Período:** {data['period']['start'][:10]} → {data['period']['end'][:10]}")
    report.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Resumen ejecutivo
    report.append("## 🎯 Resumen Ejecutivo\n")
    report.append(f"- **Commits esta semana:** {len(data['commits'])}")
    report.append(f"- **Issues cerradas:** {len(data['closed_issues'])}")
    report.append(f"- **Issues abiertas:** {len(data['open_issues'])}")
    report.append("")

    # Issues completadas
    if data['closed_issues']:
        report.append("## ✅ Issues Completadas\n")
        for issue in data['closed_issues'][:10]:
            labels = ", ".join([l["name"] for l in issue.get("labels", [])])
            report.append(f"- #{issue['number']} {issue['title']}")
            if labels:
                report.append(f"  - Labels: `{labels}`")
        report.append("")

    # Issues en progreso
    in_progress = [
        i for i in data['open_issues']
        if any(l["name"] == "status-in-progress" for l in i.get("labels", []))
    ]
    if in_progress:
        report.append("## 🔄 En Progreso\n")
        for issue in in_progress[:5]:
            report.append(f"- #{issue['number']} {issue['title']}")
        report.append("")

    # Commits recientes
    if data['commits']:
        report.append("## 📝 Commits Recientes\n")
        for commit in data['commits'][:10]:
            sha = commit['sha'][:7]
            message = commit['commit']['message'].split('\n')[0][:60]
            report.append(f"- `{sha}` {message}")
        report.append("")

    # Métricas de base de datos
    report.append("## 🗄️ Estado de la Base de Datos\n")
    db_stats = data['database_stats']
    if "error" not in db_stats:
        report.append("| Tabla | Registros |")
        report.append("|-------|-----------|")
        report.append(f"| dim_barrios | {db_stats.get('dim_barrios_count', 'N/A')} |")
        report.append(f"| fact_precios | {db_stats.get('fact_precios_count', 'N/A')} |")
        report.append(f"| fact_demografia | {db_stats.get('fact_demografia_count', 'N/A')} |")
        report.append(f"\n**Último ETL:** {db_stats.get('last_etl_run', 'N/A')}")
    else:
        report.append(f"⚠️ Error: {db_stats['error']}")
    report.append("")

    # Métricas de código
    report.append("## 💻 Métricas de Código\n")
    code_stats = data['code_stats']
    report.append(f"- **Archivos Python:** {code_stats['python_files']}")
    report.append(f"- **Líneas de código:** {code_stats['total_lines']:,}")
    report.append(f"- **Archivos de test:** {code_stats['test_files']}")
    report.append("")

    # Próximos pasos
    report.append("## 📋 Próximos Pasos\n")
    high_priority = [
        i for i in data['open_issues']
        if any(l["name"] in ["priority-high", "priority-critical"] for l in i.get("labels", []))
    ]
    if high_priority:
        for issue in high_priority[:5]:
            report.append(f"- [ ] #{issue['number']} {issue['title']}")
    else:
        report.append("- Sin issues de alta prioridad pendientes")

    return "\n".join(report)


def format_json_report(data: Dict[str, Any]) -> str:
    """
    Genera el reporte en formato JSON.

    Args:
        data: Datos recopilados del proyecto.

    Returns:
        String JSON formateado.
    """
    # Simplificar datos para JSON
    simplified = {
        "generated_at": datetime.now().isoformat(),
        "period": data["period"],
        "summary": {
            "commits_count": len(data["commits"]),
            "closed_issues_count": len(data["closed_issues"]),
            "open_issues_count": len(data["open_issues"]),
        },
        "closed_issues": [
            {"number": i["number"], "title": i["title"]}
            for i in data["closed_issues"][:20]
        ],
        "open_issues": [
            {"number": i["number"], "title": i["title"]}
            for i in data["open_issues"][:20]
        ],
        "database_stats": data["database_stats"],
        "code_stats": data["code_stats"],
    }
    return json.dumps(simplified, indent=2, ensure_ascii=False)


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Genera reportes semanales del proyecto"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["markdown", "json"],
        default="markdown",
        help="Formato de salida (default: markdown)"
    )

    args = parser.parse_args()

    # Obtener fechas de la semana
    start_date, end_date = get_week_boundaries()

    # Recopilar datos
    logger.info("Recopilando datos del proyecto...")

    data = {
        "period": {"start": start_date, "end": end_date},
        "commits": get_recent_commits(start_date, end_date),
        "closed_issues": get_closed_issues(start_date),
        "open_issues": get_open_issues(),
        "database_stats": get_database_stats(),
        "code_stats": get_code_stats(),
    }

    # Generar reporte
    if args.output == "markdown":
        print(format_markdown_report(data))
    elif args.output == "json":
        print(format_json_report(data))

    logger.info("Reporte generado correctamente")


if __name__ == "__main__":
    main()

