"""
Script para consolidar las dos bases de datos SQLite en una sola fuente de verdad.

Consolida:
- data/database.db (datos avanzados de scripts especializados)
- data/processed/database.db (datos del ETL completo)

En:
- data/master.db (base de datos consolidada)
"""
import sqlite3
import logging
from pathlib import Path
import shutil

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def consolidate_databases():
    """Consolida las dos bases de datos en master.db"""
    
    db1 = Path("data/database.db")
    db2 = Path("data/processed/database.db")
    master_db = Path("data/master.db")
    
    # Verificar que existen las bases de datos
    if not db1.exists():
        logger.error(f"{db1} no existe")
        return
    if not db2.exists():
        logger.error(f"{db2} no existe")
        return
    
    logger.info("=== Consolidando Bases de Datos ===")
    logger.info(f"Fuente 1: {db1}")
    logger.info(f"Fuente 2: {db2}")
    logger.info(f"Destino: {master_db}")
    
    # Backup si ya existe
    if master_db.exists():
        backup = Path(f"data/master_backup_{Path(master_db).stat().st_mtime:.0f}.db")
        logger.info(f"Creando backup: {backup}")
        shutil.copy(master_db, backup)
        master_db.unlink()
    
    # Copiar db1 como base
    logger.info(f"\n1. Copiando {db1} como base...")
    shutil.copy(db1, master_db)
    
    # Conectar a master
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()
    
    # Attach db2
    logger.info(f"2. Adjuntando {db2}...")
    cursor.execute(f"ATTACH DATABASE '{db2}' AS db2")
    
    # Obtener tablas de db2
    cursor.execute("SELECT name FROM db2.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables_db2 = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"\n3. Copiando datos de {len(tables_db2)} tablas...")
    
    # Tablas a copiar completamente (sobrescribir)
    tables_to_replace = [
        'fact_precios',
        'fact_renta', 
        'fact_housing_master',
        'fact_demografia',
        'fact_regulacion',
        'fact_presion_turistica',
        'fact_seguridad',
        'fact_ruido'
    ]
    
    # Tablas a mergear (combinar datos únicos)
    tables_to_merge = [
        'fact_renta_avanzada',
        'fact_catastro_avanzado',
        'fact_hogares_avanzado'
    ]
    
    stats = {}
    
    for table in tables_db2:
        try:
            # Contar filas en db2
            cursor.execute(f"SELECT COUNT(*) FROM db2.{table}")
            count_db2 = cursor.fetchone()[0]
            
            if count_db2 == 0:
                logger.debug(f"  ⊘ {table}: 0 filas en db2, saltando")
                continue
            
            # Verificar si la tabla existe en master
            cursor.execute(f"SELECT name FROM main.sqlite_master WHERE type='table' AND name='{table}'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Crear tabla copiando esquema de db2
                logger.info(f"  + {table}: Creando tabla y copiando {count_db2} filas")
                cursor.execute(f"CREATE TABLE main.{table} AS SELECT * FROM db2.{table}")
                stats[table] = {'action': 'created', 'count': count_db2}
                continue
            
            # Contar filas en master
            cursor.execute(f"SELECT COUNT(*) FROM main.{table}")
            count_master = cursor.fetchone()[0]
            
            if table in tables_to_replace:
                # Reemplazar completamente
                logger.info(f"  ↻ {table}: Reemplazando {count_master} → {count_db2} filas")
                cursor.execute(f"DELETE FROM main.{table}")
                try:
                    cursor.execute(f"INSERT INTO main.{table} SELECT * FROM db2.{table}")
                    stats[table] = {'action': 'replaced', 'before': count_master, 'after': count_db2}
                except sqlite3.OperationalError as e:
                    if "columns" in str(e):
                        logger.warning(f"    Schema mismatch, recreando tabla...")
                        cursor.execute(f"DROP TABLE main.{table}")
                        cursor.execute(f"CREATE TABLE main.{table} AS SELECT * FROM db2.{table}")
                        stats[table] = {'action': 'recreated', 'count': count_db2}
                    else:
                        raise
                
            elif table in tables_to_merge:
                # Mergear (INSERT OR IGNORE para evitar duplicados)
                logger.info(f"  ⊕ {table}: Mergeando {count_master} + {count_db2} filas")
                try:
                    cursor.execute(f"INSERT OR IGNORE INTO main.{table} SELECT * FROM db2.{table}")
                    cursor.execute(f"SELECT COUNT(*) FROM main.{table}")
                    count_final = cursor.fetchone()[0]
                    stats[table] = {'action': 'merged', 'before': count_master, 'db2': count_db2, 'after': count_final}
                except sqlite3.OperationalError as e:
                    if "columns" in str(e):
                        logger.warning(f"    Schema mismatch, usando datos de db2...")
                        cursor.execute(f"DROP TABLE main.{table}")
                        cursor.execute(f"CREATE TABLE main.{table} AS SELECT * FROM db2.{table}")
                        stats[table] = {'action': 'recreated', 'count': count_db2}
                    else:
                        raise
                
            elif count_master == 0 and count_db2 > 0:
                # Copiar si master está vacío
                logger.info(f"  → {table}: Copiando {count_db2} filas (master vacío)")
                try:
                    cursor.execute(f"INSERT INTO main.{table} SELECT * FROM db2.{table}")
                    stats[table] = {'action': 'copied', 'before': 0, 'after': count_db2}
                except sqlite3.OperationalError as e:
                    if "columns" in str(e):
                        logger.warning(f"    Schema mismatch, recreando tabla...")
                        cursor.execute(f"DROP TABLE main.{table}")
                        cursor.execute(f"CREATE TABLE main.{table} AS SELECT * FROM db2.{table}")
                        stats[table] = {'action': 'recreated', 'count': count_db2}
                    else:
                        raise
                
            else:
                # Mantener master
                logger.debug(f"  ✓ {table}: Manteniendo {count_master} filas de master")
                stats[table] = {'action': 'kept', 'count': count_master}
                
        except Exception as e:
            logger.error(f"  ✗ {table}: Error - {e}")
            stats[table] = {'action': 'error', 'error': str(e)}
            # Continuar con la siguiente tabla en caso de error
            conn.rollback()
    
    # Commit antes de detach
    conn.commit()
    
    # Detach db2
    cursor.execute("DETACH DATABASE db2")
    
    # Commit y cerrar
    conn.commit()
    conn.close()
    
    # Resumen
    logger.info("\n=== Resumen de Consolidación ===")
    for table, info in sorted(stats.items()):
        if info['action'] == 'replaced':
            logger.info(f"  {table}: {info['before']} → {info['after']} (reemplazado)")
        elif info['action'] == 'merged':
            logger.info(f"  {table}: {info['before']} + {info['db2']} → {info['after']} (mergeado)")
        elif info['action'] == 'copied':
            logger.info(f"  {table}: {info['after']} (copiado)")
        elif info['action'] == 'kept':
            logger.info(f"  {table}: {info['count']} (mantenido)")
        elif info['action'] == 'error':
            logger.error(f"  {table}: ERROR - {info['error']}")
    
    # Verificar resultado final
    logger.info("\n=== Verificación Final ===")
    conn = sqlite3.connect(master_db)
    cursor = conn.cursor()
    
    important_tables = [
        'dim_barrios', 'dim_tiempo',
        'fact_renta_avanzada', 'fact_catastro_avanzado', 'fact_hogares_avanzado',
        'fact_precios', 'fact_renta', 'fact_housing_master'
    ]
    
    for table in important_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"  {table}: {count:,} filas")
        except Exception as e:
            logger.warning(f"  {table}: No existe o error - {e}")
    
    conn.close()
    
    logger.info(f"\n✅ Consolidación completada: {master_db}")
    logger.info(f"   Tamaño: {master_db.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    consolidate_databases()
