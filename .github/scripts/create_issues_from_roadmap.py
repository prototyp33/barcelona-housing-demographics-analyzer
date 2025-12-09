#!/usr/bin/env python3
"""
Crea issues a partir de docs/DATA_EXPANSION_ROADMAP.md (S0-S8).

- Parsea secciones "## S{n}: <título>"
- Extrae Objetivo, Entregables, KPI
- Genera body con checklist DoD
- Crea issues en GitHub con labels y milestone
- Soporta dry-run
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from github import Github, GithubException


def detect_repo() -> Tuple[str, str]:
    """Detecta owner/repo desde git remote."""
    try:
        import subprocess

        url = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        clean = (
            url.replace(".git", "")
            .replace("git@github.com:", "")
            .replace("https://github.com/", "")
        )
        if "/" in clean:
            owner, repo = clean.split("/")[-2:]
            return owner, repo
    except Exception:
        pass
    return "prototyp33", "barcelona-housing-demographics-analyzer"


def read_sections(text: str) -> List[Dict[str, str]]:
    """Extrae secciones S{n} del markdown."""
    sections = []
    pattern = re.compile(r"^##\s*S(?P<num>\d+):\s*(?P<title>.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]
        sections.append(
            {
                "num": m.group("num"),
                "title": m.group("title").strip(),
                "body": chunk,
            }
        )
    return sections


def extract_field(chunk: str, field: str) -> str:
    """Extrae contenido tras '**Field:**' en el bloque."""
    regex = re.compile(rf"\*\*{re.escape(field)}:\*\*\s*(.+)", re.IGNORECASE)
    m = regex.search(chunk)
    return m.group(1).strip() if m else ""


def extract_entregables(chunk: str) -> List[str]:
    """Extrae lista de entregables debajo de '**Entregables:**'."""
    lines = chunk.splitlines()
    entregables = []
    collecting = False
    for line in lines:
        if "**Entregables:**" in line:
            collecting = True
            continue
        if collecting:
            if line.strip().startswith("-"):
                entregables.append(line.strip().lstrip("-").strip())
            elif line.strip() == "":
                # permitir líneas en blanco
                continue
            else:
                # fin de bloque
                break
    return entregables


def infer_fuente(texto: str) -> str:
    lower = texto.lower()
    if "idescat" in lower:
        return "IDESCAT"
    if "incas" in lower:
        return "Incasòl"
    if "opendata" in lower or "open data" in lower:
        return "OpenData BCN"
    if "portal" in lower and "dades" in lower:
        return "Portal Dades"
    return "Internal"


def build_body(objetivo: str, entregables: List[str], kpi: str, fuente: str, sprint_num: str) -> str:
    checklist = "\n".join([f"- [ ] {e}" for e in entregables]) if entregables else "- [ ] Definir entregables"
    return f"""## Objetivo
{objetivo or '(pendiente)'}

## Pasos para Implementar
{checklist}

## Definition of Done
- [ ] Código implementado y testeado
- [ ] Tests pasando (≥80% coverage)
- [ ] Estado DQC = Passed
- [ ] Documentación actualizada
- [ ] KPI objetivo alcanzado: {kpi or '(pendiente)'}

## Impacto/KPI
- **KPI:** {kpi or '(pendiente)'}
- **Fuente:** {fuente}
- **Bloquea:** (completar)

## Issues Relacionadas
- Depende de: (issue de S{int(sprint_num)-1 if sprint_num.isdigit() and int(sprint_num)>0 else 'previo'})
- Bloquea: (issue de S{int(sprint_num)+1 if sprint_num.isdigit() else 'siguiente'})

## Riesgos/Bloqueos
- (Completar)

## Enlaces Relevantes
- [Roadmap](docs/DATA_EXPANSION_ROADMAP.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
"""


def ensure_milestone(repo, sprint_num: str, dry: bool) -> Optional[int]:
    """Busca milestone que comience con 'Sprint {n}'."""
    title_prefix = f"Sprint {int(sprint_num)}" if sprint_num.isdigit() else f"Sprint {sprint_num}"
    for ms in repo.get_milestones(state="all"):
        if ms.title.startswith(title_prefix):
            return ms.number
    logging.warning("Milestone no encontrado para %s", title_prefix)
    return None


def issue_exists(repo, title: str) -> bool:
    for issue in repo.get_issues(state="all"):
        if issue.title == title:
            return True
    return False


def main():
    owner, repo_name = detect_repo()

    parser = argparse.ArgumentParser(description="Crear issues desde DATA_EXPANSION_ROADMAP.md")
    parser.add_argument("--roadmap", default="docs/DATA_EXPANSION_ROADMAP.md", help="Ruta al roadmap markdown")
    parser.add_argument("--repo", default=f"{owner}/{repo_name}", help="owner/repo (auto)")
    parser.add_argument("--assignee", default=None, help="Asignar a este usuario (default: owner)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar sin crear")
    parser.add_argument("--verbose", action="store_true", help="Log DEBUG")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logging.error("GITHUB_TOKEN no encontrado")
        sys.exit(1)

    roadmap_path = Path(args.roadmap)
    if not roadmap_path.exists():
        logging.error("Roadmap no encontrado: %s", roadmap_path)
        sys.exit(1)

    text = roadmap_path.read_text(encoding="utf-8")
    sections = read_sections(text)
    if not sections:
        logging.error("No se encontraron secciones S{n} en el roadmap.")
        sys.exit(1)

    try:
        gh = Github(token)
        repo = gh.get_repo(args.repo)
    except GithubException as e:
        logging.error("No se pudo acceder al repo %s: %s", args.repo, e.data.get("message", e))
        sys.exit(1)

    assignee = args.assignee or owner

    for sec in sections:
        n = sec["num"]
        titulo = sec["title"]
        cuerpo = sec["body"]
        objetivo = extract_field(cuerpo, "Objetivo")
        kpi = extract_field(cuerpo, "KPI")
        entregables = extract_entregables(cuerpo)
        fuente = infer_fuente(cuerpo)

        issue_title = f"[S{n}] {titulo}"
        if issue_exists(repo, issue_title):
            logging.info("⏭️  Issue ya existe: %s", issue_title)
            continue

        body = build_body(objetivo, entregables, kpi, fuente, n)
        milestone_num = ensure_milestone(repo, n, dry=args.dry_run)

        labels = [f"sprint-{n}", "roadmap", "domain:etl", "type:feature"]

        if args.dry_run:
            logging.info("[dry-run] Crearía issue: %s", issue_title)
            logging.info("          Labels: %s | Milestone: %s | Assignee: %s", labels, milestone_num, assignee)
            continue

        try:
            issue = repo.create_issue(
                title=issue_title,
                body=body,
                labels=labels,
                milestone=repo.get_milestone(number=milestone_num) if milestone_num else None,
                assignees=[assignee] if assignee else None,
            )
            logging.info("✅ Creada issue #%s: %s", issue.number, issue.title)
        except GithubException as e:
            logging.error("Error creando issue %s: %s", issue_title, e.data.get("message", e))


if __name__ == "__main__":
    main()

