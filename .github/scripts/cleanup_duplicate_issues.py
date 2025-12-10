#!/usr/bin/env python3
"""
Limpia issues duplicadas migrando contenido relevante y cerrando con etiqueta duplicate.

Características:
- Usa PyGithub con autenticación Auth.Token
- Dry-run opcional
- Copia body y comentarios del issue antiguo al nuevo (como comentario)
- Cierra el issue antiguo con state_reason=not_planned y label duplicate
"""

import argparse
import logging
import os
import sys
from textwrap import shorten
from typing import Dict, List

from github import Auth, Github, GithubException, Issue

# Mapeo de duplicados: OLD -> NEW (lista)
DUPLICATES: Dict[int, List[int]] = {
    24: [122],
    25: [122],
    27: [123],
    29: [124, 125, 126],
}


def detect_repo() -> str:
    """
    Detecta owner/repo desde git config o variables de entorno.

    Returns:
        Cadena owner/repo.
    """
    env_repo = os.environ.get("REPO")
    if env_repo:
        return env_repo
    try:
        import subprocess

        url = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL,
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
            return f"{owner}/{repo}"
    except Exception:
        pass
    return "prototyp33/barcelona-housing-demographics-analyzer"


def ensure_label(repo, name: str) -> None:
    """
    Asegura que exista el label dado; si no, lo crea en gris.
    """
    for lbl in repo.get_labels():
        if lbl.name == name:
            return
    repo.create_label(name=name, color="cfd3d7", description="Issue duplicado")
    logging.info("Creado label faltante: %s", name)


def build_migrated_comment(old_issue: Issue.Issue) -> str:
    """
    Construye el texto a copiar al issue nuevo con resumen del body y comentarios.
    """
    body = old_issue.body or ""
    comments = list(old_issue.get_comments())
    comments_text = "\n".join(
        f"- {c.user.login}: {shorten(c.body or '', width=300, placeholder='...')}"
        for c in comments
    )

    body_excerpt = shorten(body, width=800, placeholder="...")
    comment = (
        f"Información migrada de issue #{old_issue.number}:\n\n"
        f"**Body original (resumen):**\n{body_excerpt if body_excerpt else '(sin contenido)'}\n\n"
        f"**Comentarios (resumen):**\n{comments_text if comments_text else '(sin comentarios)'}"
    )
    return comment


def copy_to_new(repo, old_issue: Issue.Issue, targets: List[int], dry_run: bool) -> None:
    """
    Copia contenido relevante (body + comentarios) al/los issue(s) nuevo(s).
    """
    comment = build_migrated_comment(old_issue)
    for target_num in targets:
        try:
            new_issue = repo.get_issue(number=target_num)
            if dry_run:
                logging.info("[dry-run] Añadir comentario a #%s desde #%s", target_num, old_issue.number)
                continue
            new_issue.create_comment(comment)
            logging.info("✓ Comentario añadido a #%s desde #%s", target_num, old_issue.number)
        except GithubException as e:
            logging.error("Error copiando a #%s: %s", target_num, e.data.get("message", e))


def close_duplicate(
    repo,
    old_issue: Issue.Issue,
    targets: List[int],
    dry_run: bool,
) -> None:
    """
    Cierra el issue antiguo como duplicado y etiqueta.
    """
    target_str = ", ".join(f"#{n}" for n in targets)
    comment = f"Duplicada de {target_str} (nueva estructura del proyecto)."

    if dry_run:
        logging.info("[dry-run] Cerrar #%s como duplicado de %s", old_issue.number, target_str)
        return

    # Añadir label duplicate si falta
    existing_labels = [lbl.name for lbl in old_issue.labels]
    if "duplicate" not in existing_labels:
        old_issue.add_to_labels("duplicate")

    # Añadir comentario de cierre
    old_issue.create_comment(comment)

    # Cerrar con reason not_planned (PyGithub admite state_reason)
    old_issue.edit(state="closed", state_reason="not_planned")
    logging.info("✓ Cerrado #%s como duplicado de %s", old_issue.number, target_str)


def main():
    parser = argparse.ArgumentParser(description="Cierra issues duplicadas migrando contenido.")
    parser.add_argument("--repo", default=detect_repo(), help="owner/repo")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar acciones")
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

    try:
        gh = Github(auth=Auth.Token(token))
        repo = gh.get_repo(args.repo)
    except GithubException as e:
        logging.error("No se pudo acceder al repo %s: %s", args.repo, e.data.get("message", e))
        sys.exit(1)

    try:
        ensure_label(repo, "duplicate")
    except GithubException as e:
        logging.error("No se pudo asegurar el label duplicate: %s", e.data.get("message", e))
        sys.exit(1)

    for old_num, targets in DUPLICATES.items():
        try:
            old_issue = repo.get_issue(number=old_num)
        except GithubException as e:
            logging.error("No se pudo obtener issue #%s: %s", old_num, e.data.get("message", e))
            continue

        logging.info("Procesando #%s -> %s", old_num, targets)
        copy_to_new(repo, old_issue, targets, dry_run=args.dry_run)
        close_duplicate(repo, old_issue, targets, dry_run=args.dry_run)

    logging.info("Finalizado (dry_run=%s)", args.dry_run)


if __name__ == "__main__":
    main()

