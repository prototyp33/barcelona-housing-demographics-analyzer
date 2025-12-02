from __future__ import annotations

"""
Script diario de auditoría automática con IA para el repositorio.

Este script se ejecuta desde GitHub Actions y:
- Resume la actividad reciente (commits) del repositorio.
- Obtiene información básica de issues abiertas.
- Envía el contexto a un modelo de lenguaje (OpenAI u otro compatible).
- Publica un comentario de auditoría diaria en una issue dedicada.
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


GITHUB_API_URL = "https://api.github.com"
AUDIT_ISSUE_TITLE = "Continuous Management - Daily AI Audit"


def run_command(cmd: List[str]) -> str:
    """
    Ejecuta un comando de shell y devuelve su salida como texto.

    Args:
        cmd: Lista con el comando y sus argumentos.

    Returns:
        Salida estándar del comando como string.

    Raises:
        RuntimeError: Si el comando devuelve un código de salida distinto de 0.
    """
    logger.debug("Ejecutando comando: %s", " ".join(cmd))
    result = subprocess.run(
        cmd, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        logger.error(
            "Comando falló (%s): %s", result.returncode, result.stderr.strip()
        )
        raise RuntimeError(
            f"Error ejecutando comando {' '.join(cmd)}: {result.stderr}"
        )
    return result.stdout


def get_recent_commits(hours: int = 24) -> str:
    """
    Obtiene un resumen de commits recientes.

    Args:
        hours: Número de horas hacia atrás a considerar.

    Returns:
        Texto con el log de commits recientes.
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    try:
        output = run_command(
            [
                "git",
                "log",
                f'--since="{since}"',
                "--pretty=format:%h %an %ad %s",
                "--date=short",
            ]
        )
    except RuntimeError:
        return "No se pudo obtener el log de git."

    if not output.strip():
        return "Sin commits en las últimas 24 horas."

    return output.strip()


def github_api_request(
    method: str,
    path: str,
    token: str,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Realiza una petición a la API de GitHub.

    Args:
        method: Verbo HTTP (GET, POST, PATCH, etc.).
        path: Ruta relativa de la API (ej. '/repos/{owner}/{repo}/issues').
        token: Token de autenticación de GitHub.
        params: Parámetros de consulta opcionales.
        body: Cuerpo JSON opcional.

    Returns:
        Objeto JSON decodificado de la respuesta.

    Raises:
        RuntimeError: Si la petición no es exitosa.
    """
    url = f"{GITHUB_API_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=body,
        timeout=30,
    )
    if response.status_code >= 300:
        logger.error(
            "Error en llamada GitHub API %s %s: %s - %s",
            method,
            path,
            response.status_code,
            response.text,
        )
        raise RuntimeError(
            f"GitHub API error {response.status_code}: {response.text}"
        )
    if not response.text:
        return None
    return response.json()


def find_or_create_audit_issue(
    repo: str, token: str
) -> int:
    """
    Busca la issue de auditoría diaria o la crea si no existe.

    Args:
        repo: Repositorio en formato 'owner/name'.
        token: Token de GitHub.

    Returns:
        Número de la issue de auditoría.
    """
    logger.info("Buscando issue de auditoría diaria...")
    issues = github_api_request(
        "GET",
        f"/repos/{repo}/issues",
        token,
        params={"state": "all", "per_page": 100},
    )
    for issue in issues:
        if issue.get("title") == AUDIT_ISSUE_TITLE:
            logger.info("Issue de auditoría encontrada: #%s", issue["number"])
            return int(issue["number"])

    logger.info("Creando nueva issue de auditoría diaria...")
    new_issue = github_api_request(
        "POST",
        f"/repos/{repo}/issues",
        token,
        body={
            "title": AUDIT_ISSUE_TITLE,
            "body": (
                "Issue dedicada a comentarios diarios de auditoría automática "
                "generados por la IA (Continuous Management)."
            ),
            "labels": ["documentation"],
        },
    )
    return int(new_issue["number"])


def get_open_issues_summary(repo: str, token: str, limit: int = 10) -> str:
    """
    Obtiene un resumen breve de issues abiertas recientes.

    Args:
        repo: Repositorio en formato 'owner/name'.
        token: Token de GitHub.
        limit: Máximo de issues a incluir.

    Returns:
        Texto con un listado resumido de issues.
    """
    issues = github_api_request(
        "GET",
        f"/repos/{repo}/issues",
        token,
        params={"state": "open", "per_page": limit},
    )
    if not issues:
        return "No hay issues abiertas."

    lines: List[str] = []
    for issue in issues:
        # Excluir PRs
        if "pull_request" in issue:
            continue
        number = issue.get("number")
        title = issue.get("title", "").strip()
        labels = [lbl.get("name") for lbl in issue.get("labels", [])]
        lines.append(
            f"- #{number} {title} (labels: {', '.join(labels) if labels else 'sin labels'})"
        )

    return "\n".join(lines) if lines else "No hay issues abiertas (solo PRs)."


def build_ai_prompt(
    repo: str, commits_summary: str, issues_summary: str
) -> str:
    """
    Construye el prompt que se enviará al modelo de lenguaje.

    Args:
        repo: Repositorio analizado.
        commits_summary: Resumen de commits recientes.
        issues_summary: Resumen de issues abiertas.

    Returns:
        Prompt completo en formato texto.
    """
    return (
        "Actúas como un Senior Technical Project Manager + DevOps para el "
        "repositorio de análisis de vivienda y demografía de Barcelona.\n\n"
        "Tu tarea es generar una auditoría diaria breve en español que ayude "
        "al owner a gestionar el proyecto con enfoque de 'Continuous Management'.\n\n"
        "Contexto del repositorio:\n"
        "- Proyecto: Barcelona Housing Demographics Analyzer\n"
        "- Lenguaje principal: Python\n"
        "- Sprint actual centrado en integridad de datos (fact_precios, dim_barrios, "
        "fact_demografia) y consolidación de ETL.\n\n"
        "=== Commits en las últimas 24h ===\n"
        f"{commits_summary}\n\n"
        "=== Issues abiertas (resumen) ===\n"
        f"{issues_summary}\n\n"
        "Con este contexto, genera un informe breve con la siguiente estructura "
        "(máximo ~400 palabras):\n\n"
        "## 📊 Resumen del Día\n"
        "- Lista de 2-4 bullets sobre lo más relevante del día.\n\n"
        "## ⚠️ Riesgos y Bloqueos\n"
        "- Riesgos detectados a partir de cambios recientes e issues abiertas.\n\n"
        "## 🎯 Prioridades para Mañana\n"
        "- 3 acciones concretas y priorizadas, referenciando issues por número (#XX) "
        "cuando sea posible.\n\n"
        "## 🧪 Calidad Técnica\n"
        "- Comentario breve sobre calidad del código/proceso (tests, ETL, documentación) "
        "en base a la información disponible.\n\n"
        "No inventes datos ni estados de issues: si algo no se puede inferir con claridad, "
        "menciónalo como hipótesis o duda abierta."
    )


def call_openai_api(prompt: str) -> str:
    """
    Llama a la API de OpenAI (o compatible) para obtener el informe de auditoría.

    Usa las variables de entorno OPENAI_API_KEY y OPENAI_MODEL.

    Args:
        prompt: Prompt a enviar al modelo.

    Returns:
        Texto devuelto por el modelo.

    Raises:
        RuntimeError: Si falta configuración o la llamada falla.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise RuntimeError(
            "Falta la variable de entorno OPENAI_API_KEY para llamar a la IA."
        )

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Eres un asistente experto en gestión técnica de proyectos de datos.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    response = requests.post(
        url, headers=headers, data=json.dumps(body), timeout=60
    )
    if response.status_code >= 300:
        logger.error(
            "Error en llamada OpenAI API: %s - %s",
            response.status_code,
            response.text,
        )
        raise RuntimeError(
            f"OpenAI API error {response.status_code}: {response.text}"
        )

    data = response.json()
    choices: List[Dict[str, Any]] = data.get("choices", [])
    if not choices:
        raise RuntimeError("Respuesta de OpenAI sin 'choices'.")
    content = choices[0]["message"]["content"]
    return content.strip()


def post_audit_comment(repo: str, issue_number: int, token: str, body: str) -> None:
    """
    Publica un comentario de auditoría diaria en la issue de Continuous Management.

    Args:
        repo: Repositorio en formato 'owner/name'.
        issue_number: Número de la issue donde comentar.
        token: Token de GitHub.
        body: Contenido markdown del comentario.
    """
    logger.info(
        "Publicando comentario de auditoría en issue #%s...", issue_number
    )
    github_api_request(
        "POST",
        f"/repos/{repo}/issues/{issue_number}/comments",
        token,
        body={"body": body},
    )


def main() -> None:
    """
    Punto de entrada principal del script.

    Orquesta la recogida de contexto, llamada a la IA y publicación del informe.
    """
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")

    if not repo or not token:
        raise RuntimeError(
            "GITHUB_REPOSITORY y/o GITHUB_TOKEN no están definidos en el entorno."
        )

    logger.info("Iniciando auditoría diaria para el repositorio %s", repo)

    commits_summary = get_recent_commits(hours=24)
    issues_summary = get_open_issues_summary(repo, token, limit=10)

    prompt = build_ai_prompt(repo, commits_summary, issues_summary)
    try:
        ai_report = call_openai_api(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error al llamar a la IA: %s", exc)
        ai_report = (
            "No se pudo generar el informe automático de la IA.\n\n"
            f"Error: {exc}\n\n"
            "Contexto disponible:\n\n"
            "### Commits recientes\n"
            f"{commits_summary}\n\n"
            "### Issues abiertas\n"
            f"{issues_summary}"
        )

    audit_issue_number = find_or_create_audit_issue(repo, token)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    comment_body = f"## 🗓️ Auditoría diaria - {today}\n\n{ai_report}"

    post_audit_comment(repo, audit_issue_number, token, comment_body)

    logger.info("Auditoría diaria completada correctamente.")


if __name__ == "__main__":
    main()


