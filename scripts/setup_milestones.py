#!/usr/bin/env python3
"""
Script para crear milestones en GitHub según el roadmap del proyecto.

Uso:
    python scripts/setup_milestones.py [--dry-run]

Requiere:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh cli
    - pip install requests

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/setup_milestones.py --dry-run  # Verificar
    python scripts/setup_milestones.py            # Crear
"""

import argparse
import logging
import os
import subprocess
import sys
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
    sys.exit(1)

# Configuración
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Intentar obtener token de gh cli si no hay variable de entorno
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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================================================================
# DEFINICIÓN DE MILESTONES
# ==============================================================================
MILESTONES = [
    {
        "title": "Quick Wins Foundation",
        "description": "Dashboard con 3 features funcionales para showcase inmediato.\n\nFeatures:\n- #02 Calculadora de Inversión\n- #13 Clustering de Barrios\n- #05 Sistema de Alertas",
        "due_on": "2025-01-31T23:59:59Z",
        "state": "open"
    },
    {
        "title": "Core ML Engine",
        "description": "Modelo predictivo en producción con tracking de accuracy.\n\nFeatures:\n- #01 Predicción ML de Precios",
        "due_on": "2025-02-28T23:59:59Z",
        "state": "open"
    },
    {
        "title": "Data Expansion",
        "description": "Enriquecimiento de datos + infraestructura escalable.\n\nFeatures:\n- #07 Análisis POI (OpenStreetMap)\n- #28 API REST (FastAPI)",
        "due_on": "2025-04-04T23:59:59Z",
        "state": "open"
    },
    {
        "title": "Differentiation Showcase",
        "description": "Features visuales + distribución multicanal.\n\nFeatures:\n- #03 Índice de Gentrificación\n- #27 Chrome Extension",
        "due_on": "2025-05-16T23:59:59Z",
        "state": "open"
    },
]


def get_headers() -> Dict[str, str]:
    """
    Genera headers para la API de GitHub.

    Returns:
        Dict con headers de autorización.

    Raises:
        ValueError: Si GITHUB_TOKEN no está configurado.
    """
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


def get_existing_milestones() -> List[Dict]:
    """
    Obtiene los milestones existentes en el repositorio.

    Returns:
        Lista de milestones existentes.
    """
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones"
    params = {"state": "all", "per_page": 100}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener milestones: {e}")
        return []


def create_milestone(milestone_data: Dict, dry_run: bool = False) -> bool:
    """
    Crea un nuevo milestone en el repositorio.

    Args:
        milestone_data: Datos del milestone.
        dry_run: Si True, solo simula la operación.

    Returns:
        True si se creó exitosamente.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía milestone: {milestone_data['title']}")
        logger.info(f"  Due: {milestone_data['due_on']}")
        return True

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones"
    data = {
        "title": milestone_data["title"],
        "description": milestone_data["description"],
        "due_on": milestone_data["due_on"],
        "state": milestone_data.get("state", "open"),
    }

    try:
        response = requests.post(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        milestone = response.json()
        logger.info(f"✅ Milestone creado: {milestone_data['title']} (#{milestone['number']})")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al crear milestone {milestone_data['title']}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"   Respuesta: {e.response.text}")
        return False


def update_milestone(milestone_number: int, milestone_data: Dict, dry_run: bool = False) -> bool:
    """
    Actualiza un milestone existente.

    Args:
        milestone_number: Número del milestone.
        milestone_data: Nuevos datos.
        dry_run: Si True, solo simula la operación.

    Returns:
        True si se actualizó exitosamente.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Actualizaría milestone #{milestone_number}: {milestone_data['title']}")
        return True

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/milestones/{milestone_number}"
    data = {
        "title": milestone_data["title"],
        "description": milestone_data["description"],
        "due_on": milestone_data["due_on"],
        "state": milestone_data.get("state", "open"),
    }

    try:
        response = requests.patch(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"🔄 Milestone actualizado: {milestone_data['title']} (#{milestone_number})")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al actualizar milestone #{milestone_number}: {e}")
        return False


def sync_milestones(dry_run: bool = False) -> None:
    """
    Sincroniza los milestones del repositorio con la configuración definida.

    Args:
        dry_run: Si True, solo muestra los cambios sin aplicarlos.
    """
    existing = get_existing_milestones()
    existing_titles = {m["title"].lower(): m for m in existing}

    created = 0
    updated = 0
    skipped = 0

    for milestone_data in MILESTONES:
        title_lower = milestone_data["title"].lower()

        if title_lower in existing_titles:
            # Verificar si necesita actualización
            existing_milestone = existing_titles[title_lower]
            needs_update = (
                existing_milestone.get("description", "") != milestone_data["description"] or
                existing_milestone.get("due_on") != milestone_data["due_on"] or
                existing_milestone.get("state") != milestone_data.get("state", "open")
            )

            if needs_update:
                if update_milestone(
                    existing_milestone["number"],
                    milestone_data,
                    dry_run
                ):
                    updated += 1
            else:
                skipped += 1
                logger.debug(f"⏭️ Milestone sin cambios: {milestone_data['title']}")
        else:
            if create_milestone(milestone_data, dry_run):
                created += 1

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 50)
    print(f"✅ Milestones creados:     {created}")
    print(f"🔄 Milestones actualizados: {updated}")
    print(f"⏭️ Milestones sin cambios:  {skipped}")
    print("=" * 50)

    if dry_run:
        print("\n⚠️ Modo DRY-RUN: No se aplicaron cambios reales.")
        print("   Ejecuta sin --dry-run para crear los milestones.")


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Crea milestones en GitHub según el roadmap del proyecto"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular cambios sin aplicarlos"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar milestones definidos y salir"
    )

    args = parser.parse_args()

    # Mostrar lista de milestones si se solicita
    if args.list:
        print("\n📋 MILESTONES DEFINIDOS\n")
        for i, m in enumerate(MILESTONES, 1):
            print(f"{i}. {m['title']}")
            print(f"   Due: {m['due_on'][:10]}")
            print(f"   {m['description'].split(chr(10))[0]}")
            print()
        return

    try:
        sync_milestones(dry_run=args.dry_run)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

