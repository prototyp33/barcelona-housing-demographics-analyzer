#!/usr/bin/env python3
"""
Crea issues desde docs/DATA_EXPANSION_ROADMAP.md (S0-S8) con CLI avanzada:
- Filtrado por sprint (--sprint S1) o todos (--all)
- Dry-run, force (recrear si existe), verbose
- Export resumen a JSON (issues creadas/omitidas)
- Progress bar con tqdm (si está instalado)

Requisitos:
  - PyGithub
  - pyyaml (opcional si se usa template externo)
  - tqdm (opcional para progress bar)
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from github import Auth, Github, GithubException

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


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


# ---------------- Parsing helpers ---------------- #

def parse_roadmap(filepath: Path) -> List[Dict[str, Any]]:
    """
    Parsea DATA_EXPANSION_ROADMAP.md y extrae sprints con formato "## S{n}:".
    
    Busca secciones que empiecen con "## S{n}:" (ej: "## S1: Implementar IDESCATExtractor")
    y extrae:
    - Título (después de "S{n}:")
    - Objetivo (sección "**Objetivo:**")
    - Entregables (lista de items bajo "**Entregables:**")
    - KPI objetivo (sección "**KPI:**")
    - Fuente de datos (inferir del contexto: IDESCAT, Incasòl, etc.)

    Returns:
        Lista de dicts: num, title, body, objetivo, kpi, entregables, fuente
    """
    text = filepath.read_text(encoding="utf-8")
    sections = []
    
    # Buscar secciones con formato "## S{n}:" (ej: "## S1: Título")
    pattern = re.compile(r"^##\s+S(?P<num>\d+):\s*(?P<title>.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    
    if not matches:
        logging.warning("No se encontraron secciones con formato '## S{n}:' en el roadmap.")
        logging.info("Formato esperado: '## S1: Título del Sprint'")
        return sections
    
    for i, m in enumerate(matches):
        start = m.end()
        # Buscar siguiente sprint o fin del documento
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end]
        
        num = m.group("num")
        title = m.group("title").strip()
        
        # Extraer información del chunk
        objetivo = extract_field(chunk, "Objetivo")
        kpi = extract_field(chunk, "KPI")
        entregables = extract_entregables(chunk)
        fuente = extract_field(chunk, "Fuente") or infer_fuente(chunk + title)
        
        # Si no hay objetivo explícito, usar el título como objetivo
        if not objetivo:
            objetivo = f"Implementar {title}"
        
        # Si no hay KPI explícito, intentar extraerlo del contexto
        if not kpi:
            kpi = extract_kpi_from_chunk(chunk) or "Completar KPI objetivo"
        
        sections.append(
            {
                "num": num,
                "title": title,
                "body": chunk,
                "objetivo": objetivo,
                "kpi": kpi,
                "entregables": entregables,
                "fuente": fuente,
            }
        )
    
    return sections


def extract_impacto_text(chunk: str) -> str:
    """Extrae texto de impacto desde '**Impacto**:' o lista de puntos."""
    lines = chunk.splitlines()
    collecting = False
    impact_lines = []
    for line in lines:
        if "**Impacto**" in line or "**Impacto:**" in line:
            collecting = True
            # Extraer texto después de "Impacto:"
            after_colon = line.split(":", 1)[-1].strip()
            if after_colon:
                impact_lines.append(after_colon)
            continue
        if collecting:
            if line.strip().startswith("-") or line.strip().startswith("*"):
                impact_lines.append(line.strip().lstrip("-*").strip())
            elif line.strip() == "":
                continue
            elif line.strip().startswith("**"):
                break
    return " ".join(impact_lines) if impact_lines else ""


def extract_kpi_from_chunk(chunk: str) -> str:
    """Extrae KPI desde bloque de código o métricas."""
    # Buscar en bloque de código: "Cobertura: 2015-2022"
    cobertura_match = re.search(r"Cobertura:\s*([^\n]+)", chunk)
    if cobertura_match:
        return f"Cobertura: {cobertura_match.group(1).strip()}"
    
    # Buscar indicador
    indicador_match = re.search(r"Indicador:\s*([^\n]+)", chunk)
    if indicador_match:
        return f"Indicador: {indicador_match.group(1).strip()}"
    
    return "Completar KPI objetivo"


def extract_entregables_from_plan(full_text: str, propuesta_num: str) -> List[str]:
    """Busca entregables en sección 'Plan de Implementación Técnica'."""
    plan_match = re.search(r"## 🛠️ Plan de Implementación Técnica(.*?)(?=##|$)", full_text, re.DOTALL)
    if not plan_match:
        return []
    
    plan_section = plan_match.group(1)
    # Buscar "Fase {num}" que corresponda a la propuesta
    # Mapeo aproximado: propuesta 1-2 -> Fase 1, propuesta 3-5 -> Fase 3, etc.
    fase_num = int(propuesta_num) if propuesta_num.isdigit() else 0
    fase_pattern = re.compile(rf"### Fase {fase_num}:(.*?)(?=### Fase|$)", re.DOTALL)
    fase_match = fase_pattern.search(plan_section)
    
    if not fase_match:
        return []
    
    fase_text = fase_match.group(1)
    entregables = []
    # Buscar lista de tareas numeradas o con "-"
    for line in fase_text.splitlines():
        line = line.strip()
        if line.startswith(("1.", "2.", "3.", "4.", "5.")) or (line.startswith("-") and len(line) > 3):
            entregables.append(line.lstrip("1234567890.-*").strip())
    
    return entregables


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
                continue
            else:
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


def build_body(s: Dict[str, Any]) -> str:
    n = s["num"]
    objetivo = s.get("objetivo") or "(pendiente)"
    kpi = s.get("kpi") or "(pendiente)"
    fuente = s.get("fuente") or "Internal"
    entregables = s.get("entregables") or []
    checklist = "\n".join([f"- [ ] {e}" for e in entregables]) if entregables else "- [ ] Definir entregables"
    dep_prev = f"S{int(n)-1}" if n.isdigit() and int(n) > 0 else "previo"
    dep_next = f"S{int(n)+1}" if n.isdigit() else "siguiente"

    return f"""## Objetivo
{objetivo}

## Pasos para Implementar
{checklist}

## Definition of Done
- [ ] Código implementado y testeado
- [ ] Tests pasando (≥80% coverage)
- [ ] Estado DQC = Passed
- [ ] Documentación actualizada
- [ ] KPI objetivo alcanzado: {kpi}

## Impacto/KPI
- **KPI:** {kpi}
- **Fuente:** {fuente}
- **Bloquea:** (completar)

## Issues Relacionadas
- Depende de: (issue de {dep_prev})
- Bloquea: (issue de {dep_next})

## Riesgos/Bloqueos
- (Completar)

## Enlaces Relevantes
- [Roadmap](docs/DATA_EXPANSION_ROADMAP.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
"""


# ---------------- GitHub helpers ---------------- #

def ensure_milestone(repo, sprint_num: str) -> Optional[int]:
    """Busca milestone cuyo título empiece con 'Sprint {n}:'."""
    title_prefix = f"Sprint {int(sprint_num)}:" if sprint_num.isdigit() else f"Sprint {sprint_num}:"
    for ms in repo.get_milestones(state="all"):
        if ms.title.startswith(title_prefix):
            return ms.number
    logging.warning("Milestone no encontrado para prefijo %s", title_prefix)
    return None


def issue_exists(repo, title: str) -> bool:
    for issue in repo.get_issues(state="all"):
        if issue.title == title:
            return True
    return False


def create_github_issue(repo, sprint_data: Dict[str, Any], assignee: str, force: bool, dry_run: bool) -> Dict[str, Any]:
    """
    Crea issue en GitHub (o simula en dry-run).
    Returns dict with status and title.
    """
    n = sprint_data["num"]
    issue_title = f"[S{n}] {sprint_data['title']}"
    labels = [f"sprint-{n}", "roadmap", "domain:etl", "type:feature"]

    if issue_exists(repo, issue_title) and not force:
        logging.info("⏭️  Issue ya existe: %s", issue_title)
        return {"title": issue_title, "status": "skipped_exists"}

    milestone_num = ensure_milestone(repo, n)
    milestone_obj = repo.get_milestone(number=milestone_num) if milestone_num else None
    body = build_body(sprint_data)

    if dry_run:
        logging.info("[dry-run] Crearía issue: %s | Labels: %s | Milestone: %s | Assignee: %s", issue_title, labels, milestone_num, assignee)
        return {"title": issue_title, "status": "dry-run"}

    try:
        kwargs = {
            "title": issue_title,
            "body": body,
            "labels": labels,
        }
        if assignee:
            kwargs["assignees"] = [assignee]
        if milestone_obj:
            kwargs["milestone"] = milestone_obj

        issue = repo.create_issue(**kwargs)
        logging.info("✅ Creada issue #%s: %s", issue.number, issue.title)
        return {"title": issue_title, "status": "created", "number": issue.number}
    except GithubException as e:
        logging.error("Error creando issue %s: %s", issue_title, e.data.get("message", e))
        return {"title": issue_title, "status": "error", "error": str(e)}


# ---------------- Main ---------------- #

def main():
    owner, repo_name = detect_repo()

    parser = argparse.ArgumentParser(description="Crear issues desde DATA_EXPANSION_ROADMAP.md")
    parser.add_argument("--roadmap", default="docs/DATA_EXPANSION_ROADMAP.md", help="Ruta al roadmap markdown")
    parser.add_argument("--repo", default=f"{owner}/{repo_name}", help="owner/repo (auto)")
    parser.add_argument("--assignee", default=None, help="Asignar a este usuario (default: owner)")
    parser.add_argument("--sprint", help="Sprint específico (ej: S1, S2)")
    parser.add_argument("--all", action="store_true", help="Procesar todos los sprints")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar sin crear")
    parser.add_argument("--force", action="store_true", help="Recrear incluso si ya existe")
    parser.add_argument("--export-json", help="Ruta para exportar resumen en JSON")
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

    sections = parse_roadmap(roadmap_path)
    if not sections:
        logging.error("No se encontraron secciones S{n} en el roadmap.")
        sys.exit(1)

    # Filtrar sprints
    target_nums = set()
    if args.all:
        target_nums = {s["num"] for s in sections}
    elif args.sprint:
        target_nums = {args.sprint.lstrip("S").strip()}
    else:
        logging.error("Debes indicar --sprint S{n} o --all")
        sys.exit(1)

    sections = [s for s in sections if s["num"] in target_nums]
    if not sections:
        logging.error("No hay sprints que coincidan con el filtro: %s", target_nums)
        sys.exit(1)

    try:
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(args.repo)
    except GithubException as e:
        logging.error("No se pudo acceder al repo %s: %s", args.repo, e.data.get("message", e))
        sys.exit(1)

    assignee = args.assignee or owner
    summary = {"created": [], "skipped": [], "errors": []}

    iterator = sections
    if tqdm:
        iterator = tqdm(sections, desc="Procesando sprints")

    for sec in iterator:
        result = create_github_issue(
            repo,
            sec,
            assignee=assignee,
            force=args.force,
            dry_run=args.dry_run,
        )
        if result["status"] == "created":
            summary["created"].append(result["title"])
        elif result["status"] in ("dry-run", "skipped_exists"):
            summary["skipped"].append(result["title"])
        else:
            summary["errors"].append(result["title"])

    logging.info("Resumen: created=%d, skipped=%d, errors=%d",
                 len(summary["created"]), len(summary["skipped"]), len(summary["errors"]))

    if args.export_json:
        out = Path(args.export_json)
        out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logging.info("Resumen exportado a %s", out)


if __name__ == "__main__":
    main()

