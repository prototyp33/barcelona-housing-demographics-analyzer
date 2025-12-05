#!/usr/bin/env python3
"""
Script maestro para configurar completamente el proyecto GitHub:
- Labels
- Milestones
- Issues (Sprint 1)
- Issues (Sprints 2-4)

Uso:
    python scripts/project_management/setup_complete.py [--dry-run] [--skip-labels] [--skip-milestones] [--skip-issues]

Requisitos:
    - GITHUB_TOKEN configurado
    - pip install requests
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Obtener token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            GITHUB_TOKEN = result.stdout.strip()
    except Exception:
        pass

if not GITHUB_TOKEN:
    logger.error("GITHUB_TOKEN no configurado. Exporta la variable o usa: gh auth login")
    sys.exit(1)

# Directorio del script
SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str, args: list = None, dry_run: bool = False) -> bool:
    """
    Ejecuta un script Python del directorio project_management.

    Args:
        script_name: Nombre del script (sin .py)
        args: Argumentos adicionales para el script
        dry_run: Si True, añade --dry-run

    Returns:
        True si se ejecutó exitosamente, False en caso contrario.
    """
    script_path = SCRIPT_DIR / f"{script_name}.py"
    if not script_path.exists():
        logger.error(f"Script no encontrado: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if dry_run:
        cmd.append("--dry-run")
    if args:
        cmd.extend(args)

    logger.info(f"Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        logger.info(f"✅ {script_name} completado exitosamente")
        return True
    else:
        logger.error(f"❌ {script_name} falló con código {result.returncode}")
        return False


def main() -> None:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Configuración completa del proyecto GitHub"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular todos los cambios sin aplicarlos"
    )
    parser.add_argument(
        "--skip-labels",
        action="store_true",
        help="Omitir configuración de labels"
    )
    parser.add_argument(
        "--skip-milestones",
        action="store_true",
        help="Omitir creación de milestones"
    )
    parser.add_argument(
        "--skip-issues",
        action="store_true",
        help="Omitir creación de issues"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("🚀 CONFIGURACIÓN COMPLETA DEL PROYECTO GITHUB")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("⚠️  MODO DRY-RUN: No se aplicarán cambios reales")
        logger.info("")

    results = {}

    # 1. Configurar Labels
    if not args.skip_labels:
        logger.info("📋 Paso 1/4: Configurando labels...")
        results["labels"] = run_script("setup_labels", dry_run=args.dry_run)
        logger.info("")
    else:
        logger.info("⏭️  Omitiendo configuración de labels")
        results["labels"] = None

    # 2. Crear Milestones
    if not args.skip_milestones:
        logger.info("🎯 Paso 2/4: Creando milestones...")
        results["milestones"] = run_script("setup_milestones", dry_run=args.dry_run)
        logger.info("")
    else:
        logger.info("⏭️  Omitiendo creación de milestones")
        results["milestones"] = None

    # 3. Crear Issues Sprint 1
    if not args.skip_issues:
        logger.info("📝 Paso 3/4: Creando issues del Sprint 1...")
        results["issues_sprint1"] = run_script("create_initial_issues", dry_run=args.dry_run)
        logger.info("")
    else:
        logger.info("⏭️  Omitiendo creación de issues")
        results["issues_sprint1"] = None

    # 4. Crear Issues Sprints 2-4
    if not args.skip_issues:
        logger.info("📝 Paso 4/4: Creando issues de Sprints 2-4...")
        results["issues_remaining"] = run_script("create_remaining_issues", dry_run=args.dry_run)
        logger.info("")
    else:
        results["issues_remaining"] = None

    # Resumen final
    logger.info("=" * 60)
    logger.info("📊 RESUMEN FINAL")
    logger.info("=" * 60)

    for step, success in results.items():
        if success is None:
            status = "⏭️  Omitido"
        elif success:
            status = "✅ Completado"
        else:
            status = "❌ Fallido"

        logger.info(f"{step:20s}: {status}")

    logger.info("=" * 60)

    if args.dry_run:
        logger.info("")
        logger.info("⚠️  MODO DRY-RUN: No se aplicaron cambios reales.")
        logger.info("   Ejecuta sin --dry-run para aplicar la configuración completa.")
    else:
        logger.info("")
        logger.info("🎉 Configuración completada!")
        logger.info("")
        logger.info("📋 Próximos pasos:")
        logger.info("   1. Revisar issues creadas en GitHub")
        logger.info("   2. Configurar Project Board manualmente (GitHub UI)")
        logger.info("   3. Añadir issues al Project Board")
        logger.info("   4. Comenzar desarrollo del Sprint 1")


if __name__ == "__main__":
    main()

