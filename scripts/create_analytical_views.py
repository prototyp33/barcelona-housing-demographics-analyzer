#!/usr/bin/env python3
"""
Script para crear vistas analíticas en la base de datos.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection
from src.database_views import create_analytical_views, list_views

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def main() -> int:
    """Función principal."""
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return 1
    
    try:
        conn = create_connection(DB_PATH)
        
        try:
            logger.info("Creando vistas analíticas...")
            results = create_analytical_views(conn)
            
            # Verificar resultados
            created = sum(1 for v in results.values() if v)
            total = len(results)
            
            logger.info("=" * 80)
            logger.info(f"✅ Vistas creadas: {created}/{total}")
            
            for view_name, success in results.items():
                status = "✓" if success else "✗"
                logger.info(f"  {status} {view_name}")
            
            # Listar vistas existentes
            existing_views = list_views(conn)
            logger.info(f"\nTotal vistas en BD: {len(existing_views)}")
            
            logger.info("=" * 80)
            return 0 if created == total else 1
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.exception(f"Error al crear vistas: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

