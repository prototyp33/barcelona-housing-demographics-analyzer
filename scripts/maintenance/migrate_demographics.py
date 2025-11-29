"""
Script de migración para añadir columnas demográficas faltantes a fact_demografia.

Añade las siguientes columnas calculables desde los datos raw:
- pct_mayores_65: Porcentaje de población mayor de 65 años
- pct_menores_15: Porcentaje de población menor de 15 años
- indice_envejecimiento: (Población 65+ / Población 0-14) * 100

Nota: tasa_natalidad y tasa_mortalidad NO se añaden porque no hay datos
disponibles en las fuentes actuales.
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "database.db"
DEFAULT_PROCESSED_DIR = Path("data/processed")

# Columnas a añadir con sus tipos SQLite
NEW_COLUMNS = [
    ("pct_mayores_65", "REAL"),
    ("pct_menores_15", "REAL"),
    ("indice_envejecimiento", "REAL"),
]


def create_backup(db_path: Path) -> Path:
    """
    Crea un backup con timestamp de la base de datos.

    Args:
        db_path: Ruta al archivo de base de datos

    Returns:
        Ruta al archivo de backup

    Raises:
        FileNotFoundError: Si la base de datos no existe
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}.db"

    logger.info("Creando backup: %s", backup_path)
    shutil.copy2(db_path, backup_path)
    logger.info("Backup creado exitosamente")

    return backup_path


def get_existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    """
    Obtiene los nombres de columnas existentes en una tabla.

    Args:
        conn: Conexión a la base de datos
        table_name: Nombre de la tabla

    Returns:
        Set de nombres de columnas
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def migrate_demographics_schema(
    db_path: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    create_backup_flag: bool = True,
) -> bool:
    """
    Migra el esquema de fact_demografia añadiendo columnas demográficas.

    Args:
        db_path: Ruta al archivo de base de datos
        processed_dir: Directorio de datos procesados
        create_backup_flag: Si crear backup antes de migrar

    Returns:
        True si la migración fue exitosa
    """
    if processed_dir is None:
        processed_dir = DEFAULT_PROCESSED_DIR

    if db_path is None:
        db_path = processed_dir / DEFAULT_DB_NAME
    else:
        db_path = Path(db_path)
        if not db_path.is_absolute():
            db_path = processed_dir / db_path

    logger.info("Iniciando migración de esquema demográfico: %s", db_path)

    if not db_path.exists():
        logger.error("Base de datos no encontrada: %s", db_path)
        return False

    # Crear backup
    backup_path = None
    if create_backup_flag:
        try:
            backup_path = create_backup(db_path)
        except Exception as e:
            logger.error("Error creando backup: %s", e)
            return False

    conn = sqlite3.connect(db_path)

    try:
        existing_cols = get_existing_columns(conn, "fact_demografia")
        logger.info("Columnas existentes: %s", sorted(existing_cols))

        # Añadir columnas faltantes
        columns_added = []
        for col_name, col_type in NEW_COLUMNS:
            if col_name in existing_cols:
                logger.info("Columna '%s' ya existe, omitiendo", col_name)
                continue

            logger.info("Añadiendo columna: %s (%s)", col_name, col_type)
            conn.execute(
                f"ALTER TABLE fact_demografia ADD COLUMN {col_name} {col_type}"
            )
            columns_added.append(col_name)

        if columns_added:
            conn.commit()
            logger.info("Columnas añadidas exitosamente: %s", columns_added)
        else:
            logger.info("No se añadieron columnas nuevas")

        # Verificar
        final_cols = get_existing_columns(conn, "fact_demografia")
        logger.info("Columnas finales: %s", sorted(final_cols))

        return True

    except sqlite3.Error as e:
        logger.error("Error de base de datos: %s", e, exc_info=True)
        if backup_path:
            logger.info("Restaurar desde backup: %s", backup_path)
        return False

    finally:
        conn.close()


def main() -> None:
    """Punto de entrada principal para el script de migración."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migra fact_demografia añadiendo columnas demográficas"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Ruta a la base de datos",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Directorio de datos procesados",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Omitir creación de backup",
    )

    args = parser.parse_args()

    success = migrate_demographics_schema(
        db_path=args.db_path,
        processed_dir=args.processed_dir,
        create_backup_flag=not args.no_backup,
    )

    if success:
        logger.info("✅ Migración completada exitosamente")
        exit(0)
    else:
        logger.error("❌ Migración fallida")
        exit(1)


if __name__ == "__main__":
    main()

