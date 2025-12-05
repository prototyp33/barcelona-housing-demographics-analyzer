#!/usr/bin/env python3
"""
Script para configurar labels de GitHub según la estrategia del proyecto.

Uso:
    python scripts/setup_labels.py [--dry-run] [--delete-existing]

Requiere:
    - Variable de entorno GITHUB_TOKEN con permisos de repo
    - pip install requests

Ejemplo:
    export GITHUB_TOKEN="ghp_xxxx"
    python scripts/setup_labels.py --dry-run  # Ver cambios sin aplicar
    python scripts/setup_labels.py            # Aplicar cambios
"""

import argparse
import logging
import os
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
        import subprocess
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            GITHUB_TOKEN = result.stdout.strip()
            # logging.info("Usando token de GitHub CLI (gh)")
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
# DEFINICIÓN DE LABELS
# ==============================================================================
# Estructura: {"nombre": {"color": "hex", "description": "desc"}}

LABELS: Dict[str, Dict[str, str]] = {
    # Sprint Labels
    "sprint-1": {
        "color": "0E8A16",
        "description": "🏃 Sprint 1: Quick Wins (Semanas 1-4)"
    },
    "sprint-2": {
        "color": "1D76DB",
        "description": "🏃 Sprint 2: Core ML (Semanas 5-10)"
    },
    "sprint-3": {
        "color": "5319E7",
        "description": "🏃 Sprint 3: Data Expansion (Semanas 11-18)"
    },
    "sprint-4": {
        "color": "D93F0B",
        "description": "🏃 Sprint 4: Showcase (Semanas 19-24)"
    },

    # Priority Labels
    "priority-critical": {
        "color": "B60205",
        "description": "🔴 Crítico - Bloqueante"
    },
    "priority-high": {
        "color": "D93F0B",
        "description": "🟠 Alta prioridad"
    },
    "priority-medium": {
        "color": "FBCA04",
        "description": "🟡 Media prioridad"
    },
    "priority-low": {
        "color": "0E8A16",
        "description": "🟢 Baja prioridad"
    },

    # Type Labels
    "type-feature": {
        "color": "1D76DB",
        "description": "✨ Nueva funcionalidad"
    },
    "type-bug": {
        "color": "D73A4A",
        "description": "🐛 Error a corregir"
    },
    "type-refactor": {
        "color": "C5DEF5",
        "description": "♻️ Mejora técnica / refactoring"
    },
    "type-docs": {
        "color": "0075CA",
        "description": "📚 Documentación"
    },
    "type-test": {
        "color": "BFD4F2",
        "description": "🧪 Tests y cobertura"
    },
    "type-chore": {
        "color": "FEF2C0",
        "description": "🔧 Mantenimiento / configuración"
    },

    # Status Labels
    "status-blocked": {
        "color": "B60205",
        "description": "🚫 Bloqueado por dependencia"
    },
    "status-in-progress": {
        "color": "FBCA04",
        "description": "🔄 En desarrollo activo"
    },
    "status-review": {
        "color": "A2EEEF",
        "description": "👀 Listo para revisión"
    },
    "status-ready": {
        "color": "0E8A16",
        "description": "✅ Listo para merge"
    },

    # Area Labels
    "area-etl": {
        "color": "D4C5F9",
        "description": "📦 Pipeline ETL y extracción de datos"
    },
    "area-ml": {
        "color": "C2E0C6",
        "description": "🤖 Machine Learning y predicciones"
    },
    "area-ui": {
        "color": "FEF2C0",
        "description": "🎨 Interfaz Streamlit / frontend"
    },
    "area-analytics": {
        "color": "BFD4F2",
        "description": "📊 Lógica de negocio y análisis"
    },
    "area-database": {
        "color": "E99695",
        "description": "🗄️ Base de datos SQLite"
    },
    "area-api": {
        "color": "C5DEF5",
        "description": "🔌 API REST (Feature #28)"
    },

    # Special Labels
    "epic": {
        "color": "5319E7",
        "description": "🎯 Feature principal del roadmap"
    },
    "sub-issue": {
        "color": "EDEDED",
        "description": "📌 Sub-tarea de una epic"
    },
    "good-first-issue": {
        "color": "7057FF",
        "description": "👋 Buen punto de entrada para nuevos contributors"
    },
    "help-wanted": {
        "color": "008672",
        "description": "🆘 Se necesita ayuda o input"
    },
    "wontfix": {
        "color": "FFFFFF",
        "description": "🚫 No se implementará"
    },
    "duplicate": {
        "color": "CFD3D7",
        "description": "♊ Duplicado de otra issue"
    },

    # Dependency Labels
    "dependencies": {
        "color": "0366D6",
        "description": "📦 Actualizaciones de dependencias"
    },
    "python": {
        "color": "3572A5",
        "description": "🐍 Relacionado con Python"
    },
    "github-actions": {
        "color": "2088FF",
        "description": "⚙️ GitHub Actions / CI-CD"
    },
    "docker": {
        "color": "2496ED",
        "description": "🐳 Docker y contenedores"
    },
}


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
            "Exporta la variable: export GITHUB_TOKEN='ghp_xxxx'"
        )
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_existing_labels() -> List[Dict[str, str]]:
    """
    Obtiene los labels existentes en el repositorio.

    Returns:
        Lista de labels existentes.
    """
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels"
    params = {"per_page": 100}

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error al obtener labels: {e}")
        return []


def create_label(name: str, color: str, description: str, dry_run: bool = False) -> bool:
    """
    Crea un nuevo label en el repositorio.

    Args:
        name: Nombre del label.
        color: Color en hexadecimal (sin #).
        description: Descripción del label.
        dry_run: Si True, solo simula la operación.

    Returns:
        True si se creó exitosamente, False en caso de error.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía label: {name} (#{color})")
        return True

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels"
    data = {
        "name": name,
        "color": color,
        "description": description,
    }

    try:
        response = requests.post(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"✅ Label creado: {name}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al crear label {name}: {e}")
        return False


def update_label(name: str, color: str, description: str, dry_run: bool = False) -> bool:
    """
    Actualiza un label existente.

    Args:
        name: Nombre del label.
        color: Nuevo color.
        description: Nueva descripción.
        dry_run: Si True, solo simula la operación.

    Returns:
        True si se actualizó exitosamente.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Actualizaría label: {name} (#{color})")
        return True

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{name}"
    data = {
        "color": color,
        "description": description,
    }

    try:
        response = requests.patch(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"🔄 Label actualizado: {name}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al actualizar label {name}: {e}")
        return False


def delete_label(name: str, dry_run: bool = False) -> bool:
    """
    Elimina un label del repositorio.

    Args:
        name: Nombre del label a eliminar.
        dry_run: Si True, solo simula la operación.

    Returns:
        True si se eliminó exitosamente.
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Eliminaría label: {name}")
        return True

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{name}"

    try:
        response = requests.delete(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        logger.info(f"🗑️ Label eliminado: {name}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al eliminar label {name}: {e}")
        return False


def sync_labels(dry_run: bool = False, delete_existing: bool = False) -> None:
    """
    Sincroniza los labels del repositorio con la configuración definida.

    Args:
        dry_run: Si True, solo muestra los cambios sin aplicarlos.
        delete_existing: Si True, elimina labels que no están en la configuración.
    """
    existing = get_existing_labels()
    existing_names = {label["name"].lower(): label for label in existing}

    created = 0
    updated = 0
    deleted = 0
    skipped = 0

    # Crear o actualizar labels definidos
    for name, config in LABELS.items():
        name_lower = name.lower()

        if name_lower in existing_names:
            # Verificar si necesita actualización
            existing_label = existing_names[name_lower]
            if (existing_label["color"].lower() != config["color"].lower() or
                existing_label.get("description", "") != config["description"]):
                if update_label(name, config["color"], config["description"], dry_run):
                    updated += 1
            else:
                skipped += 1
                logger.debug(f"⏭️ Label sin cambios: {name}")
        else:
            if create_label(name, config["color"], config["description"], dry_run):
                created += 1

    # Eliminar labels que no están en la configuración
    if delete_existing:
        defined_names = {name.lower() for name in LABELS.keys()}
        for existing_name in existing_names:
            if existing_name not in defined_names:
                if delete_label(existing_name, dry_run):
                    deleted += 1

    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 50)
    print(f"✅ Labels creados:     {created}")
    print(f"🔄 Labels actualizados: {updated}")
    print(f"⏭️ Labels sin cambios:  {skipped}")
    if delete_existing:
        print(f"🗑️ Labels eliminados:   {deleted}")
    print("=" * 50)

    if dry_run:
        print("\n⚠️ Modo DRY-RUN: No se aplicaron cambios reales.")
        print("   Ejecuta sin --dry-run para aplicar los cambios.")


def main() -> None:
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Configura labels de GitHub según la estrategia del proyecto"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular cambios sin aplicarlos"
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Eliminar labels que no están en la configuración"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar labels definidos y salir"
    )

    args = parser.parse_args()

    # Mostrar lista de labels si se solicita
    if args.list:
        print("\n📋 LABELS DEFINIDOS\n")
        for category in ["sprint", "priority", "type", "status", "area"]:
            print(f"\n### {category.upper()} ###")
            for name, config in LABELS.items():
                if name.startswith(category) or (category == "area" and "area" in name):
                    print(f"  • {name}: {config['description']} (#{config['color']})")
        return

    try:
        sync_labels(dry_run=args.dry_run, delete_existing=args.delete_existing)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()

