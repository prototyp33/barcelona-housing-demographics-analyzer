#!/usr/bin/env python3
"""
Script para generar reportes de progreso de milestones en GitHub.

Uso:
    python scripts/milestone_progress.py [--milestone N] [--format json|table|markdown]

Requiere:
    - Variable de entorno GITHUB_TOKEN con permisos de lectura de repo
    - pip install requests tabulate

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/milestone_progress.py --milestone 1 --format markdown
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None  # Fallback a formato simple

# Configuración
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "prototyp33"
REPO_NAME = "barcelona-housing-demographics-analyzer"
API_BASE = "https://api.github.com"

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_headers() -> Dict[str, str]:
    """
    Genera headers para la API de GitHub.

    Returns:
        Dict con headers de autorización y versión de API.

    Raises:
        ValueError: Si GITHUB_TOKEN no está configurado.
    """
    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN no configurado. "
            "Exporta la variable: export GITHUB_TOKEN='ghp_xxxx'"
        )
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_milestones() -> List[Dict[str, Any]]:
    """
    Obtiene todos los milestones del repositorio.

    Returns:
        Lista de milestones con sus datos.
    """
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones"
    params = {"state": "all", "sort": "due_on", "direction": "asc"}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener milestones: {e}")
        return []


def get_milestone_details(milestone_number: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene detalles de un milestone específico.

    Args:
        milestone_number: Número del milestone en GitHub.

    Returns:
        Dict con datos del milestone o None si no existe.
    """
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones/{milestone_number}"

    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener milestone {milestone_number}: {e}")
        return None


def get_milestone_issues(milestone_number: int) -> List[Dict[str, Any]]:
    """
    Obtiene todas las issues de un milestone.

    Args:
        milestone_number: Número del milestone.

    Returns:
        Lista de issues del milestone.
    """
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {
        "milestone": milestone_number,
        "state": "all",
        "per_page": 100,
    }

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener issues del milestone {milestone_number}: {e}")
        return []


def calculate_progress(milestone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula métricas de progreso de un milestone.

    Args:
        milestone: Datos del milestone de la API.

    Returns:
        Dict con métricas calculadas.
    """
    open_issues = milestone.get("open_issues", 0)
    closed_issues = milestone.get("closed_issues", 0)
    total = open_issues + closed_issues

    percentage = (closed_issues / total * 100) if total > 0 else 0

    # Calcular días restantes
    due_on = milestone.get("due_on")
    days_remaining = None
    if due_on:
        due_date = datetime.fromisoformat(due_on.replace("Z", "+00:00"))
        now = datetime.now(due_date.tzinfo)
        days_remaining = (due_date - now).days

    return {
        "title": milestone.get("title", "Sin título"),
        "number": milestone.get("number"),
        "state": milestone.get("state", "unknown"),
        "open_issues": open_issues,
        "closed_issues": closed_issues,
        "total_issues": total,
        "percentage": round(percentage, 1),
        "due_on": due_on,
        "days_remaining": days_remaining,
        "description": milestone.get("description", ""),
    }


def format_progress_bar(percentage: float, width: int = 20) -> str:
    """
    Genera una barra de progreso ASCII.

    Args:
        percentage: Porcentaje completado (0-100).
        width: Ancho de la barra en caracteres.

    Returns:
        String con la barra de progreso.
    """
    filled = int(width * percentage / 100)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percentage:.1f}%"


def print_table_format(milestones: List[Dict[str, Any]]) -> None:
    """Imprime milestones en formato tabla."""
    if tabulate:
        headers = ["#", "Milestone", "Progreso", "Issues", "Estado", "Días Rest."]
        rows = []
        for m in milestones:
            progress = calculate_progress(m)
            rows.append([
                progress["number"],
                progress["title"][:30],
                format_progress_bar(progress["percentage"], 15),
                f"{progress['closed_issues']}/{progress['total_issues']}",
                progress["state"],
                progress["days_remaining"] if progress["days_remaining"] else "N/A",
            ])
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        # Fallback sin tabulate
        for m in milestones:
            progress = calculate_progress(m)
            print(f"\n#{progress['number']} - {progress['title']}")
            print(f"   {format_progress_bar(progress['percentage'])}")
            print(f"   Issues: {progress['closed_issues']}/{progress['total_issues']}")


def print_markdown_format(milestones: List[Dict[str, Any]]) -> None:
    """Imprime milestones en formato Markdown."""
    print("# 📊 Progreso de Milestones\n")
    print(f"*Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    for m in milestones:
        progress = calculate_progress(m)
        status_emoji = "✅" if progress["state"] == "closed" else "🔄"

        print(f"## {status_emoji} Milestone #{progress['number']}: {progress['title']}\n")

        if progress["description"]:
            print(f"> {progress['description']}\n")

        print(f"| Métrica | Valor |")
        print(f"|---------|-------|")
        print(f"| **Progreso** | {progress['percentage']:.1f}% |")
        print(f"| **Issues Completadas** | {progress['closed_issues']}/{progress['total_issues']} |")
        print(f"| **Estado** | {progress['state']} |")

        if progress["days_remaining"] is not None:
            if progress["days_remaining"] > 0:
                print(f"| **Días Restantes** | {progress['days_remaining']} días |")
            elif progress["days_remaining"] == 0:
                print(f"| **Días Restantes** | ⚠️ Vence hoy |")
            else:
                print(f"| **Días Restantes** | ❌ Vencido hace {abs(progress['days_remaining'])} días |")

        print()


def print_json_format(milestones: List[Dict[str, Any]]) -> None:
    """Imprime milestones en formato JSON."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "repository": f"{REPO_OWNER}/{REPO_NAME}",
        "milestones": [calculate_progress(m) for m in milestones],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Genera reportes de progreso de milestones de GitHub"
    )
    parser.add_argument(
        "--milestone", "-m",
        type=int,
        help="Número de milestone específico (opcional, por defecto muestra todos)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["table", "markdown", "json"],
        default="table",
        help="Formato de salida (default: table)"
    )

    args = parser.parse_args()

    try:
        if args.milestone:
            # Obtener milestone específico
            milestone = get_milestone_details(args.milestone)
            if not milestone:
                logger.error(f"Milestone #{args.milestone} no encontrado")
                sys.exit(1)
            milestones = [milestone]
        else:
            # Obtener todos los milestones
            milestones = get_milestones()

        if not milestones:
            logger.warning("No se encontraron milestones")
            sys.exit(0)

        # Imprimir en el formato solicitado
        if args.format == "table":
            print_table_format(milestones)
        elif args.format == "markdown":
            print_markdown_format(milestones)
        elif args.format == "json":
            print_json_format(milestones)

    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

