#!/usr/bin/env python3
"""
Barcelona Housing Analytics - Dashboard Opener

Script Python para abrir el dashboard en el navegador y verificar su estado.
Útil para automatización o integración con otros scripts.
"""

import sys
import time
import webbrowser
import requests
from pathlib import Path

# Añadir proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_URL = "http://localhost:8501"
MAX_RETRIES = 30
RETRY_DELAY = 1  # segundos


def check_dashboard_running(url: str = DASHBOARD_URL) -> bool:
    """
    Verifica si el dashboard está corriendo.
    
    Args:
        url: URL del dashboard
        
    Returns:
        True si el dashboard está respondiendo
    """
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False


def wait_for_dashboard(url: str = DASHBOARD_URL, max_retries: int = MAX_RETRIES) -> bool:
    """
    Espera a que el dashboard esté disponible.
    
    Args:
        url: URL del dashboard
        max_retries: Número máximo de intentos
        
    Returns:
        True si el dashboard está disponible, False si timeout
    """
    print(f"⏳ Esperando a que el dashboard esté disponible en {url}...")
    
    for i in range(max_retries):
        if check_dashboard_running(url):
            print(f"✅ Dashboard disponible después de {i + 1} intento(s)")
            return True
        time.sleep(RETRY_DELAY)
        if (i + 1) % 5 == 0:
            print(f"   ... aún esperando ({i + 1}/{max_retries})")
    
    print(f"❌ Timeout: El dashboard no está disponible después de {max_retries} intentos")
    return False


def open_dashboard(url: str = DASHBOARD_URL, wait: bool = True) -> None:
    """
    Abre el dashboard en el navegador.
    
    Args:
        url: URL del dashboard
        wait: Si True, espera a que el dashboard esté disponible antes de abrir
    """
    if wait:
        if not wait_for_dashboard(url):
            print("\n⚠️  El dashboard no está corriendo.")
            print("   Inicia el dashboard primero con:")
            print("   ./scripts/dashboard/run_dashboard.sh")
            sys.exit(1)
    
    print(f"🌐 Abriendo dashboard en navegador: {url}")
    webbrowser.open(url)
    print("✅ Dashboard abierto en el navegador")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Abre el dashboard de Barcelona Housing Analytics en el navegador"
    )
    parser.add_argument(
        "--url",
        default=DASHBOARD_URL,
        help=f"URL del dashboard (default: {DASHBOARD_URL})"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="No esperar a que el dashboard esté disponible"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Solo verificar si el dashboard está corriendo, no abrir navegador"
    )
    
    args = parser.parse_args()
    
    if args.check_only:
        if check_dashboard_running(args.url):
            print(f"✅ Dashboard está corriendo en {args.url}")
            sys.exit(0)
        else:
            print(f"❌ Dashboard no está corriendo en {args.url}")
            sys.exit(1)
    else:
        open_dashboard(args.url, wait=not args.no_wait)


if __name__ == "__main__":
    main()
