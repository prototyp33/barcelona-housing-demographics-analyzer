#!/usr/bin/env python3
"""
Script para crear todas las issues del Sprint 1 desde archivos markdown.

Uso:
    python scripts/project_management/create_sprint1_issues.py [--dry-run]

Requiere:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh cli
    - pip install requests pyyaml frontmatter

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/project_management/create_sprint1_issues.py --dry-run
    python scripts/project_management/create_sprint1_issues.py
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml no está instalado. Ejecuta: pip install pyyaml")
    sys.exit(1)

# Configuración
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
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
ISSUES_DIR = Path(__file__).parent.parent.parent / "issues" / "created"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """
    Parsea frontmatter YAML y contenido markdown.
    
    Args:
        content: Contenido completo del archivo markdown
    
    Returns:
        Tuple (frontmatter_dict, body_markdown)
    """
    if not content.startswith("---"):
        return {}, content
    
    # Encontrar fin del frontmatter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
        return frontmatter, body
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML frontmatter: {e}")
        return {}, body


def read_issue_file(file_path: Path) -> Optional[Dict]:
    """
    Lee un archivo de issue y parsea frontmatter + body.
    
    Args:
        file_path: Path al archivo markdown
    
    Returns:
        Dict con title, body, labels, milestone, assignees o None si error
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)
        
        return {
            "title": frontmatter.get("title", file_path.stem),
            "body": body,
            "labels": frontmatter.get("labels", []),
            "milestone": frontmatter.get("milestone"),
            "assignees": frontmatter.get("assignees", []),
        }
    except Exception as e:
        logger.error(f"Error leyendo {file_path}: {e}")
        return None


def get_headers() -> Dict[str, str]:
    """Genera headers para la API de GitHub."""
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
    """Obtiene el número del milestone por título."""
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
    """Crea una issue en GitHub."""
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía issue: {issue_data['title']}")
        logger.info(f"  Labels: {', '.join(issue_data.get('labels', []))}")
        return None
    
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    data = {
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": issue_data.get("labels", []),
    }
    
    # Añadir milestone
    if issue_data.get("milestone"):
        milestone_number = get_milestone_number(issue_data["milestone"])
        if milestone_number:
            data["milestone"] = milestone_number
        else:
            logger.warning(f"Milestone '{issue_data['milestone']}' no encontrado")
    
    # Añadir assignees
    if issue_data.get("assignees"):
        data["assignees"] = issue_data["assignees"]
    
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


def create_all_sprint1_issues(dry_run: bool = False) -> None:
    """Crea todas las issues del Sprint 1 desde archivos markdown."""
    # Archivos de issues del Sprint 1
    issue_files = [
        ISSUES_DIR / "issue-01-setup-project-board.md",
        ISSUES_DIR / "issue-02-setup-cicd.md",
        ISSUES_DIR / "issue-02-investment-calculator-core.md",
        ISSUES_DIR / "issue-04-investment-calculator-ui.md",
        ISSUES_DIR / "issue-05-investment-calculator-tests.md",
        ISSUES_DIR / "issue-06-docs-analytics.md",
    ]
    
    created = 0
    failed = 0
    skipped = 0
    
    for file_path in issue_files:
        if not file_path.exists():
            logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
            skipped += 1
            continue
        
        issue_data = read_issue_file(file_path)
        if not issue_data:
            failed += 1
            continue
        
        issue_number = create_issue(issue_data, dry_run)
        if issue_number:
            created += 1
        else:
            if not dry_run:
                failed += 1
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE CREACIÓN (SPRINT 1)")
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
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Crea todas las issues del Sprint 1 desde archivos markdown"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular cambios sin aplicarlos"
    )
    
    args = parser.parse_args()
    
    try:
        create_all_sprint1_issues(dry_run=args.dry_run)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

