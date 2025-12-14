#!/usr/bin/env python3
"""
Script para generar reportes semanales usando GitHub GraphQL API.

VERSIÓN MEJORADA: Usa GraphQL en lugar de REST API para:
- Menos peticiones (una sola query para issues con todos los detalles)
- Mejor rendimiento (menos round-trips)
- Soporte nativo para Projects v2
- Consultas más complejas y eficientes

Uso:
    python scripts/weekly_report_graphql.py [--output markdown|json]

Requiere:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh CLI
    - pip install requests
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Importar el módulo GraphQL
try:
    from scripts.github_graphql import GitHubGraphQL, get_repo_owner_and_name
except ImportError:
    print("Error: No se pudo importar github_graphql.py")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_week_boundaries() -> tuple:
    """
    Calcula las fechas de inicio y fin de la semana actual.
    
    Returns:
        Tuple (inicio_semana, fin_semana) como datetime objects.
    """
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    return (
        start_of_week.replace(hour=0, minute=0, second=0),
        end_of_week.replace(hour=23, minute=59, second=59)
    )


def get_recent_commits_graphql(
    gh: GitHubGraphQL,
    owner: str,
    repo: str,
    since: datetime,
    until: datetime
) -> List[Dict[str, Any]]:
    """
    Obtiene commits del período especificado usando GraphQL.
    
    Args:
        gh: Cliente GraphQL.
        owner: Owner del repositorio.
        repo: Nombre del repositorio.
        since: Fecha de inicio.
        until: Fecha de fin.
    
    Returns:
        Lista de commits.
    """
    query = """
    query($owner: String!, $repo: String!, $since: GitTimestamp!, $until: GitTimestamp!) {
        repository(owner: $owner, name: $repo) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(since: $since, until: $until, first: 50) {
                            nodes {
                                oid
                                messageHeadline
                                message
                                committedDate
                                author {
                                    name
                                    email
                                }
                                url
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {
        "owner": owner,
        "repo": repo,
        "since": since.isoformat() + "Z",
        "until": until.isoformat() + "Z"
    }
    
    try:
        data = gh.execute_query(query, variables)
        repository = data.get("repository", {})
        default_branch = repository.get("defaultBranchRef", {})
        target = default_branch.get("target", {})
        history = target.get("history", {})
        commits = history.get("nodes", [])
        
        # Normalizar formato para compatibilidad
        normalized = []
        for commit in commits:
            normalized.append({
                "sha": commit.get("oid", "")[:7],
                "commit": {
                    "message": commit.get("message", ""),
                    "author": {
                        "name": commit.get("author", {}).get("name", ""),
                        "email": commit.get("author", {}).get("email", "")
                    }
                },
                "html_url": commit.get("url", "")
            })
        
        return normalized
    except Exception as e:
        logger.error(f"Error al obtener commits con GraphQL: {e}")
        return []


def get_issues_by_date_range(
    gh: GitHubGraphQL,
    owner: str,
    repo: str,
    state: str,
    since: datetime
) -> List[Dict[str, Any]]:
    """
    Obtiene issues filtradas por fecha usando GraphQL.
    
    Args:
        gh: Cliente GraphQL.
        owner: Owner del repositorio.
        repo: Nombre del repositorio.
        state: Estado (OPEN, CLOSED).
        since: Fecha mínima de actualización.
    
    Returns:
        Lista de issues.
    """
    # GraphQL permite filtrar por fecha directamente en la query
    query = """
    query($owner: String!, $repo: String!, $state: [IssueState!]!, $since: DateTime!) {
        repository(owner: $owner, name: $repo) {
            issues(
                states: $state
                first: 100
                filterBy: {since: $since}
                orderBy: {field: UPDATED_AT, direction: DESC}
            ) {
                nodes {
                    number
                    title
                    body
                    state
                    createdAt
                    updatedAt
                    closedAt
                    url
                    labels(first: 20) {
                        nodes {
                            name
                            color
                        }
                    }
                    milestone {
                        title
                        number
                    }
                    assignees(first: 10) {
                        nodes {
                            login
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {
        "owner": owner,
        "repo": repo,
        "state": [state],
        "since": since.isoformat() + "Z"
    }
    
    try:
        data = gh.execute_query(query, variables)
        repository = data.get("repository", {})
        issues_data = repository.get("issues", {})
        return issues_data.get("nodes", [])
    except Exception as e:
        logger.error(f"Error al obtener issues con GraphQL: {e}")
        return []


def get_database_stats() -> Dict[str, Any]:
    """Obtiene estadísticas de la base de datos del proyecto."""
    if not DB_PATH.exists():
        return {"error": "Base de datos no encontrada"}
    
    stats = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tables = ["dim_barrios", "fact_precios", "fact_demografia"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[f"{table}_count"] = "N/A"
        
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
    """Obtiene estadísticas del código fuente."""
    stats = {
        "python_files": 0,
        "total_lines": 0,
        "test_files": 0,
    }
    
    src_path = PROJECT_ROOT / "src"
    tests_path = PROJECT_ROOT / "tests"
    
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            stats["python_files"] += 1
            try:
                stats["total_lines"] += sum(1 for _ in py_file.open())
            except IOError:
                pass
    
    for test_file in tests_path.glob("test_*.py"):
        stats["test_files"] += 1
    
    return stats


def format_markdown_report(data: Dict[str, Any]) -> str:
    """Genera el reporte en formato Markdown."""
    report = []
    
    report.append(f"# 📊 Reporte Semanal - Barcelona Housing Analyzer (GraphQL)\n")
    report.append(f"**Período:** {data['period']['start'].strftime('%Y-%m-%d')} → {data['period']['end'].strftime('%Y-%m-%d')}")
    report.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    report.append("## 🎯 Resumen Ejecutivo\n")
    report.append(f"- **Commits esta semana:** {len(data['commits'])}")
    report.append(f"- **Issues cerradas:** {len(data['closed_issues'])}")
    report.append(f"- **Issues abiertas:** {len(data['open_issues'])}")
    report.append("")
    
    if data['closed_issues']:
        report.append("## ✅ Issues Completadas\n")
        for issue in data['closed_issues'][:10]:
            labels = [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
            report.append(f"- #{issue['number']} {issue['title']}")
            if labels:
                report.append(f"  - Labels: `{', '.join(labels)}`")
        report.append("")
    
    in_progress = [
        i for i in data['open_issues']
        if any(l["name"] == "status-in-progress" for l in i.get("labels", {}).get("nodes", []))
    ]
    if in_progress:
        report.append("## 🔄 En Progreso\n")
        for issue in in_progress[:5]:
            report.append(f"- #{issue['number']} {issue['title']}")
        report.append("")
    
    if data['commits']:
        report.append("## 📝 Commits Recientes\n")
        for commit in data['commits'][:10]:
            sha = commit.get('sha', '')[:7]
            message = commit.get('commit', {}).get('message', '').split('\n')[0][:60]
            report.append(f"- `{sha}` {message}")
        report.append("")
    
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
    
    report.append("## 💻 Métricas de Código\n")
    code_stats = data['code_stats']
    report.append(f"- **Archivos Python:** {code_stats['python_files']}")
    report.append(f"- **Líneas de código:** {code_stats['total_lines']:,}")
    report.append(f"- **Archivos de test:** {code_stats['test_files']}")
    report.append("")
    
    report.append("## 📋 Próximos Pasos\n")
    high_priority = [
        i for i in data['open_issues']
        if any(
            l["name"] in ["priority-high", "priority-critical"]
            for l in i.get("labels", {}).get("nodes", [])
        )
    ]
    if high_priority:
        for issue in high_priority[:5]:
            report.append(f"- [ ] #{issue['number']} {issue['title']}")
    else:
        report.append("- Sin issues de alta prioridad pendientes")
    
    return "\n".join(report)


def format_json_report(data: Dict[str, Any]) -> str:
    """Genera el reporte en formato JSON."""
    simplified = {
        "generated_at": datetime.now().isoformat(),
        "period": {
            "start": data["period"]["start"].isoformat(),
            "end": data["period"]["end"].isoformat()
        },
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
        description="Genera reportes semanales usando GraphQL API"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["markdown", "json"],
        default="markdown",
        help="Formato de salida (default: markdown)"
    )
    
    args = parser.parse_args()
    
    # Obtener owner/repo
    owner, repo = get_repo_owner_and_name()
    
    # Inicializar cliente GraphQL
    try:
        gh = GitHubGraphQL()
    except ValueError as e:
        logger.error(f"Error inicializando GraphQL: {e}")
        sys.exit(1)
    
    # Obtener fechas de la semana
    start_date, end_date = get_week_boundaries()
    
    # Recopilar datos usando GraphQL
    logger.info("Recopilando datos del proyecto con GraphQL...")
    
    # Obtener issues cerradas (actualizadas desde inicio de semana)
    closed_issues = get_issues_by_date_range(
        gh, owner, repo, "CLOSED", start_date
    )
    
    # Obtener issues abiertas (todas)
    open_issues = gh.get_all_issues_paginated(
        owner=owner,
        repo=repo,
        state="OPEN"
    )
    
    # Obtener commits
    commits = get_recent_commits_graphql(
        gh, owner, repo, start_date, end_date
    )
    
    data = {
        "period": {"start": start_date, "end": end_date},
        "commits": commits,
        "closed_issues": closed_issues,
        "open_issues": open_issues,
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

