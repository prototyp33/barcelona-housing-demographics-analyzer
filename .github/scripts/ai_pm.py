from __future__ import annotations

"""
AI Project Manager v3 (Hybrid/Fusion Version)

Combina la eficiencia de contexto de la v2 (File Tree + Límites seguros)
con la robustez operativa de la v1 (Reportes de error y progreso detallados).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from github import Auth, Github
from groq import Groq


# --- CONFIGURACIÓN OPTIMIZADA (v2 limits) ---
MAX_TOTAL_CHARS = 9_000       # Zona segura para evitar error 413
MAX_FILE_CHARS = 1_500        # Leer solo cabeceras/lógica principal
SLEEP_BETWEEN_CALLS = 15      # Prevención robusta de error 429
MODEL_NAME = "llama-3.3-70b-versatile"
TARGET_LABELS = {"enhancement", "bug"}  # Auditamos features y bugs


# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_repo() -> Any:
    """Conexión segura a GitHub."""

    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo_name:
        raise RuntimeError("Faltan variables de entorno GITHUB_TOKEN o GITHUB_REPOSITORY.")
    auth = Auth.Token(token)
    gh = Github(auth=auth)
    return gh.get_repo(repo_name)


def get_file_tree(root: Path) -> str:
    """
    (De la v2) Genera un mapa visual de archivos.
    Permite a la IA saber qué existe sin gastar tokens leyendo todo el contenido.
    """

    ignore = {".git", ".github", "__pycache__", "venv", ".venv", "env", "data", "logs", "node_modules"}
    tree_str: List[str] = []

    for path in sorted(root.rglob("*")):
        if any(part in ignore or part.startswith(".") for part in path.parts):
            continue

        level = len(path.relative_to(root).parts)
        indent = "    " * (level - 1)
        if path.is_file() and path.suffix in [".py", ".md", ".yml", ".yaml", ".json"]:
            tree_str.append(f"{indent}📄 {path.name}")
        elif path.is_dir():
            tree_str.append(f"{indent}📁 {path.name}/")

    return "\n".join(tree_str)


def build_code_context(root: Path) -> str:
    """
    Construye el contexto priorizando la estructura y limitando el contenido.
    """

    ignore_dirs = {".git", ".github", "env", "venv", ".venv", "__pycache__", "data", "logs"}

    # 1. Estrategia v2: Primero el Mapa
    tree = get_file_tree(root)
    context_parts: List[str] = [f"=== ESTRUCTURA DE ARCHIVOS (File Tree) ===\n{tree}\n"]

    total_chars = len(context_parts[0])
    truncated = False

    # 2. Estrategia v2: Contenido limitado
    for path in root.rglob("*.py"):
        if any(part in ignore_dirs for part in path.parts):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo leer %s: %s", path, exc)
            continue

        snippet = text[:MAX_FILE_CHARS]
        if len(text) > MAX_FILE_CHARS:
            snippet += "\n... [truncado]"

        rel = str(path.relative_to(root))
        block = f"--- ARCHIVO: {rel} ---\n```python\n{snippet}\n```"

        if total_chars + len(block) > MAX_TOTAL_CHARS:
            truncated = True
            break

        context_parts.append(block)
        total_chars += len(block)

    if truncated:
        context_parts.append(
            "\n[SISTEMA: Se han omitido más archivos para asegurar la estabilidad de la API]\n"
        )

    return "\n\n".join(context_parts)


def call_groq(prompt: str) -> Dict[str, Any]:
    """Llamada a Groq con manejo de errores básico."""

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GROQ_API_KEY")

    client = Groq(api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un Tech Lead Senior. Responde SOLO con un JSON válido "
                        "siguiendo el esquema solicitado."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error API Groq: %s", exc)
        raise


def process_issue(issue: Any, code_context: str) -> None:
    """
    Procesa la issue con la lógica híbrida:
    - Usa el prompt estructurado de la v2.
    - Usa el sistema de reporte completo de la v1 (comments + recommendations).
    """

    logger.info("--- Auditando Issue #%s: %s ---", issue.number, issue.title)

    # Prompt v2 (Contexto Estructural) + Output v1 (JSON Rico)
    prompt = (
        "Actúa como un AI Project Manager. Audita esta tarea basándote en la "
        "ESTRUCTURA y CÓDIGO del proyecto.\n\n"
        f"=== TAREA ===\nTITULO: {issue.title}\nDESCRIPCIÓN:\n{issue.body or ''}\n\n"
        f"=== CONTEXTO DEL PROYECTO ===\n{code_context}\n\n"
        "INSTRUCCIONES DE ANÁLISIS:\n"
        "1. Revisa la 'ESTRUCTURA DE ARCHIVOS'. ¿Existen los archivos necesarios? "
        "(Esto es indicativo fuerte de progreso).\n"
        "2. Revisa los fragmentos de código. ¿Existe la lógica implementada?\n"
        "3. Sé estricto. Solo marca 'completed' si ves evidencia clara.\n\n"
        "FORMATO JSON OBLIGATORIO:\n"
        "{\n"
        '  "status": "completed" | "in_progress" | "not_started",\n'
        '  "confidence": 0.0-1.0,\n'
        '  "summary": "Resumen técnico de 1 linea",\n'
        '  "reasoning": "Explicación técnica (menciona archivos vistos en el árbol o código)",\n'
        '  "recommendations": ["Paso 1 sugerido", "Paso 2 sugerido"]\n'
        "}"
    )

    try:
        result = call_groq(prompt)

        status = result.get("status", "not_started")
        confidence = float(result.get("confidence", 0.0))
        reasoning = result.get("reasoning", "")
        recommendations = result.get("recommendations", [])

        logger.info("Resultado: %s (Confianza: %.2f)", status, confidence)

        # Construcción del mensaje (Restaurado de v1 para visibilidad)
        comment_lines: List[str] = [
            f"### 🤖 AI Audit Report (Confianza: {confidence:.2f})",
            f"**Estado detectado:** `{status}`",
            "",
            f"**Análisis:** {reasoning}",
        ]
        if recommendations:
            comment_lines.append("")
            comment_lines.append("**Siguientes pasos sugeridos:**")
            for rec in recommendations:
                comment_lines.append(f"- {rec}")

        final_comment = "\n".join(comment_lines)

        # Caso A: Completado con alta seguridad -> Cerrar
        if status == "completed" and confidence >= 0.75:
            issue.create_comment(f"{final_comment}\n\n✅ **Cerrando issue automáticamente.**")
            issue.edit(state="closed")
            logger.info("--> ISSUE CERRADA")

        # Caso B: Progreso visible -> Comentar (Restaurado de v1)
        elif status == "in_progress" and confidence >= 0.6:
            last_comment: Optional[Any] = None
            try:
                if issue.comments > 0:
                    last_comment = list(issue.get_comments())[-1]
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "No se pudo obtener el último comentario de la issue #%s: %s",
                    issue.number,
                    exc,
                )

            if last_comment and "AI Audit Report" in getattr(last_comment, "body", ""):
                logger.info(
                    "--> Progreso detectado, pero ya se comentó recientemente. Saltando spam."
                )
            else:
                issue.create_comment(
                    f"{final_comment}\n\n🚧 **Progreso detectado.** La mantendré abierta."
                )
                logger.info("--> COMENTARIO DE PROGRESO AÑADIDO")

    except Exception as exc:  # noqa: BLE001
        # Manejo de errores visible
        logger.error("Fallo al procesar issue #%s: %s", issue.number, exc)
        try:
            issue.create_comment(
                f"⚠️ **AI Audit Error:** No pude completar el análisis.\n`{str(exc)}`"
            )
        except Exception:
            pass


def main() -> None:
    """Punto de entrada principal del AI Project Manager."""

    repo = get_repo()

    # Filtrar issues relevantes (Features y Bugs)
    issues = repo.get_issues(state="open")
    target_issues = [i for i in issues if any(l.name in TARGET_LABELS for l in i.labels)]

    if not target_issues:
        logger.info("No hay issues abiertas con etiquetas %s.", TARGET_LABELS)
        return

    logger.info("Generando contexto (Límite: %s chars)...", MAX_TOTAL_CHARS)
    code_context = build_code_context(Path(os.getcwd()))

    logger.info("Comenzando auditoría de %s issues...", len(target_issues))

    for issue in target_issues:
        process_issue(issue, code_context)
        # Pausa de seguridad
        logger.info("Durmiendo %s segundos para respetar rate limits...", SLEEP_BETWEEN_CALLS)
        time.sleep(SLEEP_BETWEEN_CALLS)


if __name__ == "__main__":
    main()



