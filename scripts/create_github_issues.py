#!/usr/bin/env python3
"""
Script para crear issues de GitHub desde docs/ISSUES_TO_CREATE.md

Usa la CLI de GitHub (gh) para crear issues automáticamente.
"""

import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def parse_issues_markdown(md_file: Path) -> list[dict]:
    """
    Parsea el archivo markdown y extrae información de issues.
    
    Args:
        md_file: Ruta al archivo markdown.
    
    Returns:
        Lista de diccionarios con información de cada issue.
    """
    content = md_file.read_text(encoding="utf-8")
    issues = []
    
    # Patrón para encontrar secciones de issues
    # Busca títulos como "### 1. Fix: ..." o "### 2. Feature: ..."
    pattern = r'### (\d+)\.\s+(\w+):\s+(.+?)\n\*\*Labels\*\*:\s*(.+?)\s+\n\*\*Prioridad\*\*:\s*(\w+)(?:\s+\n\*\*Milestone\*\*:\s*(.+?))?\n\n\*\*Descripción\*\*:\n(.+?)\n\n\*\*Tareas\*\*:\n(.+?)\n\n\*\*Aceptación\*\*:\n(.+?)(?=\n---|\n###|\Z)'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        issue_num = match.group(1)
        issue_type = match.group(2)  # Fix, Feature, Task, Improvement
        title = match.group(3).strip()
        labels_str = match.group(4).strip()
        priority = match.group(5).strip()
        milestone = match.group(6).strip() if match.group(6) else None
        description = match.group(7).strip()
        tasks = match.group(8).strip()
        acceptance = match.group(9).strip()
        
        # Parsear labels
        labels = [label.strip() for label in labels_str.split(',')]
        
        # Determinar prioridad para GitHub
        if priority.lower() == "high":
            github_priority = "🔴 Alta"
        elif priority.lower() == "medium":
            github_priority = "🟡 Media"
        else:
            github_priority = "🟢 Baja"
        
        issues.append({
            "number": issue_num,
            "type": issue_type,
            "title": title,
            "labels": labels,
            "priority": priority,
            "github_priority": github_priority,
            "milestone": milestone,
            "description": description,
            "tasks": tasks,
            "acceptance": acceptance,
        })
    
    return issues


def create_github_issue(issue: dict, dry_run: bool = False) -> bool:
    """
    Crea un issue en GitHub usando la CLI.
    
    Args:
        issue: Diccionario con información del issue.
        dry_run: Si True, solo muestra lo que se haría sin crear el issue.
    
    Returns:
        True si se creó exitosamente, False en caso contrario.
    """
    # Construir el body del issue
    body_parts = [
        f"**Prioridad:** {issue['github_priority']}",
        "",
        f"## Descripción",
        issue['description'],
        "",
        "## Tareas",
        issue['tasks'],
        "",
        "## Criterios de Aceptación",
        issue['acceptance'],
    ]
    
    if issue['milestone']:
        body_parts.insert(2, f"**Milestone:** {issue['milestone']}")
        body_parts.insert(3, "")
    
    body = "\n".join(body_parts)
    
    # Construir comando gh
    labels_str = ",".join(issue['labels'])
    title = f"{issue['type']}: {issue['title']}"
    
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", labels_str,
    ]
    
    if issue['priority'].lower() == "high":
        cmd.extend(["--label", "priority:high"])
    elif issue['priority'].lower() == "medium":
        cmd.extend(["--label", "priority:medium"])
    else:
        cmd.extend(["--label", "priority:low"])
    
    if dry_run:
        print(f"[DRY RUN] Would create issue:")
        print(f"  Title: {title}")
        print(f"  Labels: {labels_str}")
        print(f"  Command: {' '.join(cmd)}")
        return True
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        issue_url = result.stdout.strip()
        print(f"✅ Created issue #{issue['number']}: {title}")
        print(f"   URL: {issue_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating issue #{issue['number']}: {e.stderr}", file=sys.stderr)
        return False


def main() -> int:
    """Función principal."""
    md_file = PROJECT_ROOT / "docs" / "ISSUES_TO_CREATE.md"
    
    if not md_file.exists():
        print(f"❌ File not found: {md_file}", file=sys.stderr)
        return 1
    
    # Verificar que gh está autenticado
    try:
        subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI not authenticated. Run 'gh auth login' first.", file=sys.stderr)
        return 1
    
    # Parsear issues
    print(f"📖 Parsing {md_file}...")
    issues = parse_issues_markdown(md_file)
    
    if not issues:
        print("⚠️  No issues found in markdown file.")
        return 1
    
    print(f"📋 Found {len(issues)} issues to create.\n")
    
    # Crear issues
    success_count = 0
    for issue in issues:
        if create_github_issue(issue, dry_run=False):
            success_count += 1
        print()  # Línea en blanco entre issues
    
    print(f"\n✅ Successfully created {success_count}/{len(issues)} issues.")
    
    return 0 if success_count == len(issues) else 1


if __name__ == "__main__":
    sys.exit(main())
