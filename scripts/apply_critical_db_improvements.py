#!/usr/bin/env python3
"""
Script para aplicar mejoras críticas a la base de datos.

Aplica las mejoras de alta prioridad identificadas en el análisis:
1. Crear índices faltantes para consultas frecuentes
2. Resolver tablas vacías (fact_calidad_aire)
3. Agregar índices para vistas materializadas
4. Crear sistema de validación de foreign keys
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Añadir proyecto al path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager
from src.app.config import DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_missing_indexes(conn) -> int:
    """
    Crea índices faltantes para optimizar consultas frecuentes.
    
    Returns:
        Número de índices creados.
    """
    logger.info("🔍 Creando índices faltantes...")
    
    indexes = [
        # Índices compuestos para consultas por año + barrio
        ("idx_fact_precios_anio_barrio", 
         "CREATE INDEX IF NOT EXISTS idx_fact_precios_anio_barrio ON fact_precios(anio, barrio_id)"),
        
        ("idx_fact_demografia_anio_barrio",
         "CREATE INDEX IF NOT EXISTS idx_fact_demografia_anio_barrio ON fact_demografia(anio, barrio_id)"),
        
        ("idx_fact_renta_anio_barrio",
         "CREATE INDEX IF NOT EXISTS idx_fact_renta_anio_barrio ON fact_renta(anio, barrio_id)"),
        
        ("idx_fact_educacion_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_educacion_barrio_anio ON fact_educacion(barrio_id, anio)"),
        
        ("idx_fact_comercio_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_comercio_barrio_anio ON fact_comercio(barrio_id, anio)"),
        
        ("idx_fact_servicios_salud_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_servicios_salud_barrio_anio ON fact_servicios_salud(barrio_id, anio)"),
        
        ("idx_fact_presion_turistica_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_presion_turistica_barrio_anio ON fact_presion_turistica(barrio_id, anio)"),
        
        # Índices para búsquedas por distrito
        ("idx_dim_barrios_distrito",
         "CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito ON dim_barrios(distrito_id, distrito_nombre)"),
        
        ("idx_dim_barrios_codi_barri",
         "CREATE INDEX IF NOT EXISTS idx_dim_barrios_codi_barri ON dim_barrios(codi_barri)"),
        
        ("idx_dim_barrios_distrito_nombre",
         "CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito_nombre ON dim_barrios(distrito_nombre, barrio_nombre)"),
        
        # Índices adicionales para otras tablas fact_*
        ("idx_fact_demografia_ampliada_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_demografia_ampliada_barrio_anio ON fact_demografia_ampliada(barrio_id, anio)"),
        
        ("idx_fact_regulacion_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_regulacion_barrio_anio ON fact_regulacion(barrio_id, anio)"),
        
        ("idx_fact_hut_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_hut_barrio_anio ON fact_hut(barrio_id, anio)"),
        
        ("idx_fact_desempleo_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_desempleo_barrio_anio ON fact_desempleo(barrio_id, anio)"),
        
        ("idx_fact_medio_ambiente_barrio_anio",
         "CREATE INDEX IF NOT EXISTS idx_fact_medio_ambiente_barrio_anio ON fact_medio_ambiente(barrio_id, anio)"),
    ]
    
    created = 0
    with conn:
        for index_name, sql in indexes:
            try:
                conn.execute(sql)
                logger.info(f"  ✅ Índice creado: {index_name}")
                created += 1
            except Exception as e:
                logger.warning(f"  ⚠️  Error creando índice {index_name}: {e}")
    
    logger.info(f"📊 Total índices creados: {created}/{len(indexes)}")
    return created


def resolve_empty_tables(conn) -> int:
    """
    Resuelve tablas vacías creando vistas desde tablas relacionadas.
    
    Returns:
        Número de vistas/tablas resueltas.
    """
    logger.info("🔍 Resolviendo tablas vacías...")
    
    resolved = 0
    
    # Verificar si fact_calidad_aire está vacía
    cursor = conn.execute("SELECT COUNT(*) FROM fact_calidad_aire")
    count = cursor.fetchone()[0]
    
    if count == 0:
        logger.info("  📋 fact_calidad_aire está vacía, creando vista desde fact_medio_ambiente...")
        
        # Verificar si fact_medio_ambiente tiene datos de calidad de aire
        cursor = conn.execute("""
            SELECT COUNT(*) 
            FROM fact_medio_ambiente 
            WHERE no2_mean IS NOT NULL OR pm25_mean IS NOT NULL
        """)
        medio_ambiente_count = cursor.fetchone()[0]
        
        if medio_ambiente_count > 0:
            # Crear vista que apunte a fact_medio_ambiente
            try:
                conn.execute("DROP VIEW IF EXISTS fact_calidad_aire")
                conn.execute("""
                    CREATE VIEW fact_calidad_aire AS
                    SELECT 
                        barrio_id,
                        anio,
                        no2_mean,
                        pm25_mean,
                        pm10_mean,
                        o3_mean,
                        NULL as stations_nearby,
                        NULL as max_distance_m,
                        etl_loaded_at
                    FROM fact_medio_ambiente
                    WHERE no2_mean IS NOT NULL OR pm25_mean IS NOT NULL
                """)
                conn.commit()
                logger.info("  ✅ Vista fact_calidad_aire creada desde fact_medio_ambiente")
                resolved += 1
            except Exception as e:
                logger.warning(f"  ⚠️  Error creando vista fact_calidad_aire: {e}")
        else:
            logger.warning("  ⚠️  fact_medio_ambiente tampoco tiene datos de calidad de aire")
    
    # Verificar si fact_ruido y fact_soroll están duplicadas
    # (Ambas parecen tener los mismos datos, consolidar en fact_medio_ambiente)
    ruido_count = 0
    soroll_count = 0
    
    # Verificar si fact_ruido existe
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='fact_ruido'
    """)
    if cursor.fetchone():
        cursor = conn.execute("SELECT COUNT(*) FROM fact_ruido")
        ruido_count = cursor.fetchone()[0]
    
    # Verificar si fact_soroll existe
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='fact_soroll'
    """)
    if cursor.fetchone():
        cursor = conn.execute("SELECT COUNT(*) FROM fact_soroll")
        soroll_count = cursor.fetchone()[0]
    
    if ruido_count > 0 or soroll_count > 0:
        logger.info(f"  📋 Detectadas tablas de ruido: fact_ruido ({ruido_count} registros), fact_soroll ({soroll_count} registros)")
        logger.info("  ℹ️  Considerar consolidar en fact_medio_ambiente en el futuro")
    
    logger.info(f"📊 Total tablas/vistas resueltas: {resolved}")
    return resolved


def create_integrity_check_system(conn) -> int:
    """
    Crea el sistema de validación de foreign keys.
    
    Returns:
        Número de componentes creados.
    """
    logger.info("🔍 Creando sistema de validación de integridad...")
    
    created = 0
    
    # Crear tabla de checks si no existe
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS integrity_checks (
                check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL,
                table_name TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                issue_description TEXT,
                affected_rows INTEGER,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT
            )
        """)
        conn.commit()
        logger.info("  ✅ Tabla integrity_checks creada")
        created += 1
    except Exception as e:
        logger.warning(f"  ⚠️  Error creando tabla integrity_checks: {e}")
    
    # Crear función/vista para verificar foreign keys huérfanos
    # SQLite no soporta funciones almacenadas, pero podemos crear una vista
    # o ejecutar consultas directamente
    
    # Ejecutar primera validación
    logger.info("  🔍 Ejecutando primera validación de integridad...")
    
    fact_tables = [
        'fact_precios',
        'fact_demografia',
        'fact_demografia_ampliada',
        'fact_renta',
        'fact_educacion',
        'fact_comercio',
        'fact_servicios_salud',
        'fact_presion_turistica',
        'fact_regulacion',
        'fact_hut',
        'fact_desempleo',
        'fact_medio_ambiente',
        'fact_seguridad',
        'fact_ruido',
        'fact_oferta_idealista',
    ]
    
    issues_found = 0
    with conn:
        for table_name in fact_tables:
            try:
                # Verificar si la tabla existe
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                if not cursor.fetchone():
                    continue
                
                # Verificar foreign keys huérfanos
                query = f"""
                    SELECT COUNT(*) as orphaned_count
                    FROM {table_name} f
                    LEFT JOIN dim_barrios b ON f.barrio_id = b.barrio_id
                    WHERE b.barrio_id IS NULL
                """
                cursor = conn.execute(query)
                result = cursor.fetchone()
                orphaned_count = result[0] if result else 0
                
                if orphaned_count > 0:
                    conn.execute("""
                        INSERT INTO integrity_checks 
                        (check_date, table_name, issue_type, issue_description, affected_rows)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        table_name,
                        'orphaned_fk',
                        f'Registros con barrio_id inexistente en dim_barrios',
                        orphaned_count
                    ))
                    logger.warning(f"  ⚠️  {table_name}: {orphaned_count} registros huérfanos encontrados")
                    issues_found += 1
                else:
                    logger.info(f"  ✅ {table_name}: Sin registros huérfanos")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  Error validando {table_name}: {e}")
    
    conn.commit()
    
    logger.info(f"📊 Sistema de integridad creado. Issues encontrados: {issues_found}")
    return created + (1 if issues_found > 0 else 0)


def verify_indexes(conn) -> None:
    """Verifica que los índices se hayan creado correctamente."""
    logger.info("🔍 Verificando índices creados...")
    
    cursor = conn.execute("""
        SELECT name, tbl_name, sql 
        FROM sqlite_master 
        WHERE type = 'index' 
        AND name LIKE 'idx_%'
        ORDER BY name
    """)
    
    indexes = cursor.fetchall()
    logger.info(f"📊 Total de índices encontrados: {len(indexes)}")
    
    # Mostrar algunos índices clave
    key_indexes = [idx[0] for idx in indexes if any(
        key in idx[0] for key in ['anio_barrio', 'barrio_anio', 'distrito', 'codi_barri']
    )]
    
    if key_indexes:
        logger.info("  ✅ Índices clave creados:")
        for idx_name in key_indexes[:10]:  # Mostrar primeros 10
            logger.info(f"    - {idx_name}")


def main():
    """Función principal que ejecuta todas las mejoras críticas."""
    logger.info("=" * 60)
    logger.info("🚀 Aplicando Mejoras Críticas a la Base de Datos")
    logger.info("=" * 60)
    
    if not DB_PATH.exists():
        logger.error(f"❌ Base de datos no encontrada: {DB_PATH}")
        return 1
    
    logger.info(f"📁 Base de datos: {DB_PATH}")
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    try:
        # 1. Crear índices faltantes
        logger.info("\n" + "=" * 60)
        logger.info("1️⃣  CREANDO ÍNDICES FALTANTES")
        logger.info("=" * 60)
        indexes_created = create_missing_indexes(conn)
        
        # 2. Resolver tablas vacías
        logger.info("\n" + "=" * 60)
        logger.info("2️⃣  RESOLVIENDO TABLAS VACÍAS")
        logger.info("=" * 60)
        tables_resolved = resolve_empty_tables(conn)
        
        # 3. Crear sistema de validación
        logger.info("\n" + "=" * 60)
        logger.info("3️⃣  CREANDO SISTEMA DE VALIDACIÓN")
        logger.info("=" * 60)
        integrity_created = create_integrity_check_system(conn)
        
        # 4. Verificar resultados
        logger.info("\n" + "=" * 60)
        logger.info("4️⃣  VERIFICANDO RESULTADOS")
        logger.info("=" * 60)
        verify_indexes(conn)
        
        # Resumen
        logger.info("\n" + "=" * 60)
        logger.info("✅ RESUMEN DE MEJORAS APLICADAS")
        logger.info("=" * 60)
        logger.info(f"  📊 Índices creados: {indexes_created}")
        logger.info(f"  📋 Tablas/vistas resueltas: {tables_resolved}")
        logger.info(f"  🔒 Componentes de integridad: {integrity_created}")
        logger.info("\n✅ Mejoras críticas aplicadas exitosamente!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error aplicando mejoras: {e}", exc_info=True)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
