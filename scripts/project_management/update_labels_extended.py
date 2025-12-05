#!/usr/bin/env python3
"""
Script para gestión completa de labels del proyecto Barcelona Housing.

Uso:
    python scripts/project_management/update_labels_extended.py sync [--dry-run]
    python scripts/project_management/update_labels_extended.py list
    python scripts/project_management/update_labels_extended.py export [--output FILE]
    python scripts/project_management/update_labels_extended.py clean [--dry-run]
    python scripts/project_management/update_labels_extended.py stats

Requisitos:
    - Variable de entorno GITHUB_TOKEN o autenticación con gh cli
    - pip install requests
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Dict, List

try:
    import requests
except ImportError:
    print("Error: requests no está instalado. Ejecuta: pip install requests")
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

# Rate limiting para API de GitHub (5000 req/hora)
# Delay de 200ms entre requests = ~18,000 req/hora (bien dentro del límite)
REQUEST_DELAY = 0.2  # 200ms entre requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==============================================================================
# RATE LIMITING DECORATOR
# ==============================================================================

def rate_limited(func):
    """Decorator para añadir rate limiting a funciones de API."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep(REQUEST_DELAY)
        return func(*args, **kwargs)
    return wrapper

# ==============================================================================
# DEFINICIÓN COMPLETA DE LABELS
# ==============================================================================

# Sprint labels
SPRINT_LABELS: Dict[str, Dict[str, str]] = {
    "sprint-1": {
        "color": "0E8A16",
        "description": "Semanas 1-4: Quick Wins Foundation"
    },
    "sprint-2": {
        "color": "1D76DB",
        "description": "Semanas 5-10: Core ML Engine"
    },
    "sprint-3": {
        "color": "5319E7",
        "description": "Semanas 11-18: Data Expansion"
    },
    "sprint-4": {
        "color": "D93F0B",
        "description": "Semanas 19-24: Differentiation Showcase"
    },
    "sprint-backlog": {
        "color": "CCCCCC",
        "description": "Post-v1.0.0 features"
    },
    "sprint-blocked": {
        "color": "B60205",
        "description": "Bloqueado por dependencias externas"
    },
}

# Priority labels
PRIORITY_LABELS: Dict[str, Dict[str, str]] = {
    "priority-critical": {
        "color": "B60205",
        "description": "🔥 Bloqueante para milestone, resolver inmediatamente"
    },
    "priority-high": {
        "color": "D93F0B",
        "description": "⬆️ Alta prioridad, completar en sprint actual"
    },
    "priority-medium": {
        "color": "FBCA04",
        "description": "➡️ Media prioridad, planificar para siguiente sprint"
    },
    "priority-low": {
        "color": "0E8A16",
        "description": "⬇️ Baja prioridad, nice-to-have"
    },
}

# Type labels
TYPE_LABELS: Dict[str, Dict[str, str]] = {
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
        "description": "♻️ Mejora técnica sin cambio funcional"
    },
    "type-docs": {
        "color": "0075CA",
        "description": "📝 Documentación"
    },
    "type-test": {
        "color": "BFDADC",
        "description": "🧪 Testing y QA"
    },
    "type-infra": {
        "color": "E99695",
        "description": "⚙️ Infraestructura y DevOps"
    },
    "type-research": {
        "color": "FEF2C0",
        "description": "🔬 Spike/investigación técnica"
    },
}

# Area labels
AREA_LABELS: Dict[str, Dict[str, str]] = {
    "area-etl": {
        "color": "D4C5F9",
        "description": "📊 Pipeline de extracción y carga"
    },
    "area-ml": {
        "color": "C2E0C6",
        "description": "🤖 Machine Learning y modelos"
    },
    "area-analytics": {
        "color": "BFD4F2",
        "description": "📈 Lógica de negocio y cálculos"
    },
    "area-ui": {
        "color": "FEF2C0",
        "description": "🎨 Interfaz Streamlit"
    },
    "area-api": {
        "color": "D1ECFA",
        "description": "🔌 API REST FastAPI"
    },
    "area-database": {
        "color": "E3F2EA",
        "description": "💾 Esquema y queries SQLite"
    },
    "area-geospatial": {
        "color": "FFE5CC",
        "description": "🗺️ Datos geo-espaciales y mapas"
    },
    "area-monitoring": {
        "color": "FFDDCC",
        "description": "🔔 Alertas y observabilidad"
    },
    "area-extension": {
        "color": "F9D0C4",
        "description": "🧩 Chrome Extension"
    },
}

# Status labels
STATUS_LABELS: Dict[str, Dict[str, str]] = {
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
        "description": "👀 Listo para code review"
    },
    "status-testing": {
        "color": "BFD4F2",
        "description": "🧪 En fase de testing"
    },
    "status-ready-to-merge": {
        "color": "0E8A16",
        "description": "✅ Aprobado, listo para merge"
    },
}

# Effort labels (t-shirt sizes)
EFFORT_LABELS: Dict[str, Dict[str, str]] = {
    "effort-xs": {
        "color": "E1F5E1",
        "description": "⏱️ <2 horas"
    },
    "effort-s": {
        "color": "C2E0C6",
        "description": "⏱️ 2-5 horas"
    },
    "effort-m": {
        "color": "A4D3A6",
        "description": "⏱️ 5-10 horas"
    },
    "effort-l": {
        "color": "7FBC7F",
        "description": "⏱️ 10-20 horas"
    },
    "effort-xl": {
        "color": "5AA05A",
        "description": "⏱️ >20 horas (considerar dividir)"
    },
}

# Special labels
SPECIAL_LABELS: Dict[str, Dict[str, str]] = {
    "good-first-issue": {
        "color": "7057FF",
        "description": "👍 Ideal para comenzar (aunque solo-dev)"
    },
    "help-wanted": {
        "color": "008672",
        "description": "🙋 Necesita input externo o investigación"
    },
    "breaking-change": {
        "color": "D73A4A",
        "description": "💥 Rompe compatibilidad con versiones previas"
    },
    "tech-debt": {
        "color": "E99695",
        "description": "🏗️ Deuda técnica a refactorizar"
    },
    "duplicate": {
        "color": "CFD3D7",
        "description": "👥 Duplicado de otro issue"
    },
    "wontfix": {
        "color": "FFFFFF",
        "description": "❌ No se implementará (razonado)"
    },
    "future-v2": {
        "color": "EDEDED",
        "description": "🔮 Post-v1.0.0, considerar para v2"
    },
    "epic": {
        "color": "5319E7",
        "description": "🎯 Feature principal del roadmap"
    },
    "sub-issue": {
        "color": "EDEDED",
        "description": "📌 Sub-tarea de una epic"
    },
}

# Tech labels
TECH_LABELS: Dict[str, Dict[str, str]] = {
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

# Combinar todos los labels
ALL_LABELS: Dict[str, Dict[str, str]] = {
    **SPRINT_LABELS,
    **PRIORITY_LABELS,
    **TYPE_LABELS,
    **AREA_LABELS,
    **STATUS_LABELS,
    **EFFORT_LABELS,
    **SPECIAL_LABELS,
    **TECH_LABELS,
}

# Labels obsoletos a eliminar
OBSOLETE_LABELS = [
    "bug",  # Reemplazado por type-bug
    "enhancement",  # Reemplazado por type-feature
    "documentation",  # Reemplazado por type-docs
    "wip",  # Reemplazado por status-in-progress
]


# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def validate_repo_context() -> None:
    """Valida que el script se ejecuta desde el repo correcto."""
    cwd = Path.cwd()
    
    # Verificar que existe .git
    if not (cwd / ".git").exists():
        raise RuntimeError("No estás en un repositorio Git")
    
    # Verificar que es el repo correcto (opcional)
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        if REPO_NAME not in remote_url:
            logger.warning(f"⚠️ Repo remoto no coincide: {remote_url}")
            response = input("¿Continuar de todos modos? (s/N): ")
            if response.lower() != "s":
                sys.exit(0)
    except subprocess.CalledProcessError:
        logger.warning("No se pudo verificar el remote origin")


def validate_color(color: str) -> bool:
    """Valida que el color sea un hex válido de 6 caracteres."""
    return bool(re.match(r'^[0-9A-Fa-f]{6}$', color))


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


def get_existing_labels() -> Dict[str, Dict]:
    """Obtiene los labels existentes en el repositorio."""
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels"
    params = {"per_page": 100}
    
    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=30)
        response.raise_for_status()
        return {label["name"].lower(): label for label in response.json()}
    except requests.RequestException as e:
        logger.error(f"Error al obtener labels: {e}")
        return {}


# ==============================================================================
# OPERACIONES CON LABELS
# ==============================================================================

@rate_limited
def create_label(name: str, color: str, description: str, dry_run: bool = False) -> bool:
    """Crea un nuevo label."""
    if dry_run:
        logger.info(f"[DRY-RUN] Crearía label: {name} (#{color})")
        return True
    
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels"
    data = {"name": name, "color": color, "description": description}
    
    try:
        response = requests.post(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"✅ Label creado: {name}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al crear label {name}: {e}")
        return False


@rate_limited
def update_label(name: str, color: str, description: str, dry_run: bool = False) -> bool:
    """Actualiza un label existente."""
    if dry_run:
        logger.info(f"[DRY-RUN] Actualizaría label: {name} (#{color})")
        return True
    
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{name}"
    data = {"color": color, "description": description}
    
    try:
        response = requests.patch(url, headers=get_headers(), json=data, timeout=30)
        response.raise_for_status()
        logger.info(f"🔄 Label actualizado: {name}")
        return True
    except requests.RequestException as e:
        logger.error(f"❌ Error al actualizar label {name}: {e}")
        return False


def sync_all_labels(dry_run: bool = False) -> None:
    """Sincroniza todos los labels definidos."""
    existing = get_existing_labels()
    created = 0
    updated = 0
    skipped = 0
    errors = 0
    
    for name, config in ALL_LABELS.items():
        # Validar color
        if not validate_color(config["color"]):
            logger.error(f"❌ Color inválido para {name}: {config['color']}")
            errors += 1
            continue
        
        name_lower = name.lower()
        
        if name_lower in existing:
            existing_label = existing[name_lower]
            if (existing_label["color"].lower() != config["color"].lower() or
                existing_label.get("description", "") != config["description"]):
                if update_label(name, config["color"], config["description"], dry_run):
                    updated += 1
            else:
                skipped += 1
        else:
            if create_label(name, config["color"], config["description"], dry_run):
                created += 1
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 50)
    print(f"✅ Labels creados:     {created}")
    print(f"🔄 Labels actualizados: {updated}")
    print(f"⏭️ Labels sin cambios:  {skipped}")
    if errors > 0:
        print(f"❌ Errores:            {errors}")
    print("=" * 50)
    
    if dry_run:
        print("\n⚠️ Modo DRY-RUN: No se aplicaron cambios reales.")
        print("   Ejecuta sin --dry-run para aplicar los cambios.")


def list_current_labels() -> None:
    """Lista todos los labels actuales en el repositorio."""
    existing = get_existing_labels()
    
    print("\n" + "=" * 50)
    print(f"📋 LABELS ACTUALES EN {REPO_OWNER}/{REPO_NAME}")
    print("=" * 50)
    
    for name, label in sorted(existing.items()):
        color = label["color"]
        desc = label.get("description", "Sin descripción")
        print(f"  • {name:<30} #{color} - {desc}")
    
    print("=" * 50)
    print(f"Total: {len(existing)} labels")


def delete_obsolete_labels(dry_run: bool = False) -> None:
    """Elimina labels que ya no se usan."""
    existing = get_existing_labels()
    deleted = 0
    
    for name in OBSOLETE_LABELS:
        name_lower = name.lower()
        if name_lower in existing:
            if dry_run:
                logger.info(f"[DRY-RUN] Eliminaría label obsoleto: {name}")
                deleted += 1
            else:
                url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/labels/{name}"
                try:
                    response = requests.delete(url, headers=get_headers(), timeout=30)
                    response.raise_for_status()
                    logger.info(f"🗑️ Label eliminado: {name}")
                    deleted += 1
                except requests.RequestException as e:
                    logger.error(f"❌ Error al eliminar label {name}: {e}")
    
    if deleted > 0:
        print(f"\n🗑️ Labels obsoletos eliminados: {deleted}")
    else:
        print("\n✅ No hay labels obsoletos para eliminar")


def show_label_statistics() -> None:
    """Muestra estadísticas sobre los labels del repo."""
    existing = get_existing_labels()
    
    # Contar por categorías
    categories = {
        "Sprint": 0,
        "Priority": 0,
        "Type": 0,
        "Area": 0,
        "Status": 0,
        "Effort": 0,
        "Special": 0,
        "Tech": 0,
        "Unknown": 0,
    }
    
    for name in existing.keys():
        if name.startswith("sprint-"):
            categories["Sprint"] += 1
        elif name.startswith("priority-"):
            categories["Priority"] += 1
        elif name.startswith("type-"):
            categories["Type"] += 1
        elif name.startswith("area-"):
            categories["Area"] += 1
        elif name.startswith("status-"):
            categories["Status"] += 1
        elif name.startswith("effort-"):
            categories["Effort"] += 1
        elif name in [k.lower() for k in SPECIAL_LABELS.keys()]:
            categories["Special"] += 1
        elif name in [k.lower() for k in TECH_LABELS.keys()]:
            categories["Tech"] += 1
        else:
            categories["Unknown"] += 1
    
    print("\n" + "=" * 50)
    print("📊 ESTADÍSTICAS DE LABELS")
    print("=" * 50)
    for category, count in sorted(categories.items()):
        if count > 0:
            print(f"  {category:<12}: {count:>3}")
    print("=" * 50)
    print(f"  {'TOTAL':<12}: {len(existing):>3}")
    print("=" * 50)


def export_labels_to_markdown(output_file: str = "docs/labels.md") -> None:
    """Exporta los labels a un archivo markdown para documentación."""
    categories = {
        "Sprint": SPRINT_LABELS,
        "Priority": PRIORITY_LABELS,
        "Type": TYPE_LABELS,
        "Area": AREA_LABELS,
        "Status": STATUS_LABELS,
        "Effort": EFFORT_LABELS,
        "Special": SPECIAL_LABELS,
        "Tech": TECH_LABELS,
    }
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# GitHub Labels Documentation\n\n")
        f.write("Generado automáticamente. No editar manualmente.\n\n")
        f.write(f"**Total de labels:** {len(ALL_LABELS)}\n\n")
        
        for category, labels in categories.items():
            f.write(f"## {category} Labels\n\n")
            f.write("| Label | Color | Description |\n")
            f.write("|-------|-------|-------------|\n")
            
            for name, config in sorted(labels.items()):
                color = config["color"]
                desc = config["description"]
                f.write(f"| `{name}` | ![#{color}](https://via.placeholder.com/15/{color}/000000?text=+) `#{color}` | {desc} |\n")
            
            f.write("\n")
    
    logger.info(f"✅ Labels exportados a {output_path}")


# ==============================================================================
# MAIN
# ==============================================================================

def main() -> None:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Gestión completa de labels del proyecto Barcelona Housing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Ver labels actuales
  python scripts/project_management/update_labels_extended.py list

  # Sincronizar (dry-run primero)
  python scripts/project_management/update_labels_extended.py sync --dry-run
  python scripts/project_management/update_labels_extended.py sync

  # Exportar documentación
  python scripts/project_management/update_labels_extended.py export

  # Ver estadísticas
  python scripts/project_management/update_labels_extended.py stats

  # Limpiar labels obsoletos
  python scripts/project_management/update_labels_extended.py clean --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Subcomando: sync
    sync_parser = subparsers.add_parser("sync", help="Sincronizar todos los labels")
    sync_parser.add_argument("--dry-run", action="store_true", help="Simular cambios sin aplicarlos")
    
    # Subcomando: list
    subparsers.add_parser("list", help="Listar todos los labels actuales")
    
    # Subcomando: export
    export_parser = subparsers.add_parser("export", help="Exportar labels a markdown")
    export_parser.add_argument(
        "--output",
        default="docs/labels.md",
        help="Archivo de salida (default: docs/labels.md)"
    )
    
    # Subcomando: clean
    clean_parser = subparsers.add_parser("clean", help="Eliminar labels obsoletos")
    clean_parser.add_argument("--dry-run", action="store_true", help="Simular cambios sin aplicarlos")
    
    # Subcomando: stats
    subparsers.add_parser("stats", help="Mostrar estadísticas de labels")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Validar contexto del repo
    try:
        validate_repo_context()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    try:
        if args.command == "sync":
            sync_all_labels(dry_run=args.dry_run)
        elif args.command == "list":
            list_current_labels()
        elif args.command == "export":
            export_labels_to_markdown(output_file=args.output)
        elif args.command == "clean":
            delete_obsolete_labels(dry_run=args.dry_run)
        elif args.command == "stats":
            show_label_statistics()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operación cancelada por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()
