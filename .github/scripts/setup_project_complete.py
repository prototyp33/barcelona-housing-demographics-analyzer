#!/usr/bin/env python3
"""
Setup de labels y milestones desde YAML (idempotente, con dry-run y verificación).

Requisitos:
  - PyGithub y PyYAML instalados
  - GITHUB_TOKEN con scope repo (y project si usas Projects)

Uso:
  python .github/scripts/setup_project_complete.py --dry-run
  python .github/scripts/setup_project_complete.py --labels .github/config/labels.yml --milestones .github/config/milestones.yml
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from github import Auth, Github, GithubException

DEFAULT_LABELS_PATH = ".github/config/labels.yml"
DEFAULT_MILESTONES_PATH = ".github/config/milestones.yml"


def detect_repo() -> Tuple[str, str]:
    """Detecta owner y repo desde git config (SSH/HTTPS)."""
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


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_due(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def sync_labels(repo, labels_cfg: List[Dict[str, Any]], dry: bool, verify: bool) -> None:
    existing = {lbl.name: lbl for lbl in repo.get_labels()}
    to_create, to_update = [], []

    for cfg in labels_cfg:
        name = cfg["name"]
        color = cfg.get("color", "ffffff").lstrip("#")
        desc = cfg.get("description", "")
        if name in existing:
            lbl = existing[name]
            if lbl.color != color or (lbl.description or "") != desc:
                to_update.append((lbl, color, desc))
        else:
            to_create.append((name, color, desc))

    logging.info(
        "Labels existentes: %d | Crear: %d | Actualizar: %d",
        len(existing),
        len(to_create),
        len(to_update),
    )

    if verify or dry:
        if to_create:
            logging.info("[dry-run] Crear: %s", [n for n, _, _ in to_create])
        if to_update:
            logging.info("[dry-run] Actualizar: %s", [l.name for l, _, _ in to_update])
        return

    for name, color, desc in to_create:
        try:
            repo.create_label(name=name, color=color, description=desc)
            logging.info("✓ Creado label: %s", name)
        except GithubException as e:
            logging.error("Error creando label %s: %s", name, e.data.get("message", e))

    for lbl, color, desc in to_update:
        try:
            lbl.edit(name=lbl.name, color=color, description=desc)
            logging.info("✓ Actualizado label: %s", lbl.name)
        except GithubException as e:
            logging.error("Error actualizando label %s: %s", lbl.name, e.data.get("message", e))


def sync_milestones(repo, ms_cfg: List[Dict[str, Any]], dry: bool, verify: bool) -> None:
    existing = {ms.title: ms for ms in repo.get_milestones(state="all")}
    to_create, to_update = [], []

    for cfg in ms_cfg:
        title = cfg["title"]
        desc = cfg.get("description", "")
        due_raw = cfg.get("due_on")
        due_on = parse_due(due_raw) if due_raw else None
        desired_state = cfg.get("state")  # "open" o "closed"

        if title in existing:
            ms = existing[title]
            state_differs = desired_state and ms.state.lower() != desired_state.lower()
            if (ms.description or "") != desc or (ms.due_on != due_on) or state_differs:
                to_update.append((ms, desc, due_on, desired_state))
        else:
            to_create.append((title, desc, due_on, desired_state))

    logging.info(
        "Milestones existentes: %d | Crear: %d | Actualizar: %d",
        len(existing),
        len(to_create),
        len(to_update),
    )

    if verify or dry:
        if to_create:
            logging.info("[dry-run] Crear milestones: %s", [t for t, _, _, _ in to_create])
        if to_update:
            logging.info("[dry-run] Actualizar milestones: %s", [ms.title for ms, _, _, _ in to_update])
        return

    for title, desc, due_on, desired_state in to_create:
        try:
            repo.create_milestone(title=title, description=desc, due_on=due_on, state=desired_state or "open")
            logging.info("✓ Creado milestone: %s", title)
        except GithubException as e:
            logging.error("Error creando milestone %s: %s", title, e.data.get("message", e))

    for ms, desc, due_on, desired_state in to_update:
        try:
            kwargs = {"title": ms.title, "description": desc, "due_on": due_on}
            if desired_state and desired_state.lower() in ("open", "closed"):
                kwargs["state"] = desired_state.lower()
            ms.edit(**kwargs)
            logging.info("✓ Actualizado milestone: %s%s",
                         ms.title,
                         f" (state -> {kwargs.get('state')})" if "state" in kwargs else "")
        except GithubException as e:
            logging.error("Error actualizando milestone %s: %s", ms.title, e.data.get("message", e))


def main():
    owner, repo_name = detect_repo()

    parser = argparse.ArgumentParser(description="Setup de labels y milestones desde YAML")
    parser.add_argument("--labels", default=DEFAULT_LABELS_PATH, help="Ruta al YAML de labels")
    parser.add_argument("--milestones", default=DEFAULT_MILESTONES_PATH, help="Ruta al YAML de milestones")
    parser.add_argument("--repo", default=f"{owner}/{repo_name}", help="owner/repo (auto-detectado)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar acciones sin aplicar cambios")
    parser.add_argument("--verify", action="store_true", help="Solo verificar diferencias")
    parser.add_argument("--verbose", action="store_true", help="Log nivel DEBUG")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logging.error("GITHUB_TOKEN no encontrado. Exporta un token con scope repo.")
        sys.exit(1)

    try:
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(args.repo)
        logging.info("Repositorio: %s", repo.full_name)
    except GithubException as e:
        logging.error("No se pudo acceder al repo %s: %s", args.repo, e.data.get("message", e))
        sys.exit(1)

    labels_path = Path(args.labels)
    milestones_path = Path(args.milestones)

    if not labels_path.exists():
        logging.error("Archivo de labels no encontrado: %s", labels_path)
        sys.exit(1)
    if not milestones_path.exists():
        logging.error("Archivo de milestones no encontrado: %s", milestones_path)
        sys.exit(1)

    labels_yaml = load_yaml(labels_path) or {}
    ms_yaml = load_yaml(milestones_path) or {}

    # Extraer listas desde las llaves raíz
    if isinstance(labels_yaml, dict):
        labels_cfg = labels_yaml.get("labels", [])
    else:
        labels_cfg = labels_yaml or []

    if isinstance(ms_yaml, dict):
        ms_cfg = ms_yaml.get("milestones", [])
    else:
        ms_cfg = ms_yaml or []

    logging.info("Iniciando sincronización (dry_run=%s, verify=%s)", args.dry_run, args.verify)
    sync_labels(repo, labels_cfg, dry=args.dry_run, verify=args.verify)
    sync_milestones(repo, ms_cfg, dry=args.dry_run, verify=args.verify)
    logging.info("Finalizado")


if __name__ == "__main__":
    main()

