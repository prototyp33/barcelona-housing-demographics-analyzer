#!/usr/bin/env python3
"""
Script para aplicar mejoras de prioridad media a la base de datos.

Aplica las mejoras de prioridad media identificadas en el análisis:
1. Crear vistas de particionamiento temporal
2. Actualizar estadísticas ANALYZE
3. Documentar mejoras adicionales
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


def create_temporal_partitioning_views(conn) -> int:
    """
    Crea vistas de particionamiento temporal para datos recientes vs históricos.
    
    Returns:
        Número de vistas creadas.
    """
    logger.info("🔍 Creando vistas de particionamiento temporal...")
    
    # Tablas principales que se beneficiarían del particionamiento
    fact_tables = [
        'fact_precios',
        'fact_demografia',
        'fact_demografia_ampliada',
        'fact_renta',
        'fact_educacion',
        'fact_comercio',
        'fact_servicios_salud',
        'fact_presion_turistica',
    ]
    
    created = 0
    
    with conn:
        for table_name in fact_tables:
            # Verificar si la tabla existe y tiene columna 'anio'
            try:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'anio' not in columns:
                    logger.debug(f"  ⏭️  {table_name}: No tiene columna 'anio', saltando")
                    continue
                
                # Verificar si hay datos
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    logger.debug(f"  ⏭️  {table_name}: Vacía, saltando")
                    continue
                
                # Obtener año máximo
                cursor = conn.execute(f"SELECT MAX(anio) FROM {table_name}")
                max_year = cursor.fetchone()[0]
                
                if max_year is None:
                    logger.debug(f"  ⏭️  {table_name}: Sin años, saltando")
                    continue
                
                # Crear vista para datos recientes (últimos 3 años)
                view_recent = f"{table_name}_recent"
                try:
                    conn.execute(f"DROP VIEW IF EXISTS {view_recent}")
                    conn.execute(f"""
                        CREATE VIEW {view_recent} AS
                        SELECT * FROM {table_name}
                        WHERE anio >= {max_year - 2}
                    """)
                    logger.info(f"  ✅ Vista creada: {view_recent} (años {max_year - 2}-{max_year})")
                    created += 1
                except Exception as e:
                    logger.warning(f"  ⚠️  Error creando vista {view_recent}: {e}")
                
                # Crear vista para datos históricos (antes de los últimos 3 años)
                view_historical = f"{table_name}_historical"
                try:
                    conn.execute(f"DROP VIEW IF EXISTS {view_historical}")
                    conn.execute(f"""
                        CREATE VIEW {view_historical} AS
                        SELECT * FROM {table_name}
                        WHERE anio < {max_year - 2}
                    """)
                    logger.info(f"  ✅ Vista creada: {view_historical} (años < {max_year - 2})")
                    created += 1
                except Exception as e:
                    logger.warning(f"  ⚠️  Error creando vista {view_historical}: {e}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️  Error procesando {table_name}: {e}")
    
    conn.commit()
    logger.info(f"📊 Total vistas de particionamiento creadas: {created}")
    return created


def update_statistics(conn) -> None:
    """
    Actualiza las estadísticas del optimizador de consultas SQLite.
    """
    logger.info("🔍 Actualizando estadísticas del optimizador...")
    
    # Tablas principales para analizar
    tables_to_analyze = [
        'dim_barrios',
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
        'fact_oferta_idealista',
    ]
    
    analyzed = 0
    
    with conn:
        for table_name in tables_to_analyze:
            try:
                # Verificar si la tabla existe
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                if not cursor.fetchone():
                    continue
                
                # Ejecutar ANALYZE en la tabla
                conn.execute(f"ANALYZE {table_name}")
                logger.debug(f"  ✅ Estadísticas actualizadas: {table_name}")
                analyzed += 1
                
            except Exception as e:
                logger.warning(f"  ⚠️  Error analizando {table_name}: {e}")
        
        # Analizar toda la base de datos
        try:
            conn.execute("ANALYZE")
            logger.info(f"  ✅ ANALYZE general ejecutado")
        except Exception as e:
            logger.warning(f"  ⚠️  Error en ANALYZE general: {e}")
    
    logger.info(f"📊 Total tablas analizadas: {analyzed}")


def create_query_performance_views(conn) -> int:
    """
    Crea vistas optimizadas para consultas comunes del dashboard.
    
    Returns:
        Número de vistas creadas.
    """
    logger.info("🔍 Creando vistas optimizadas para consultas comunes...")
    
    created = 0
    
    with conn:
        # Vista: KPIs agregados por barrio y año (para dashboard)
        try:
            conn.execute("DROP VIEW IF EXISTS vw_kpis_por_barrio_anio")
            conn.execute("""
                CREATE VIEW vw_kpis_por_barrio_anio AS
                SELECT 
                    b.barrio_id,
                    b.barrio_nombre,
                    b.distrito_nombre,
                    p.anio,
                    p.precio_m2_venta,
                    p.precio_mes_alquiler,
                    d.poblacion_total,
                    d.hogares_totales,
                    d.densidad_hab_km2,
                    r.renta_promedio,
                    e.total_centros_educativos,
                    c.densidad_comercial_por_1000hab,
                    s.densidad_servicios_por_1000hab
                FROM dim_barrios b
                LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id
                LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND p.anio = d.anio
                LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND p.anio = r.anio
                LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id AND p.anio = e.anio
                LEFT JOIN fact_comercio c ON b.barrio_id = c.barrio_id AND p.anio = c.anio
                LEFT JOIN fact_servicios_salud s ON b.barrio_id = s.barrio_id AND p.anio = s.anio
                WHERE p.anio IS NOT NULL
            """)
            logger.info("  ✅ Vista creada: vw_kpis_por_barrio_anio")
            created += 1
        except Exception as e:
            logger.warning(f"  ⚠️  Error creando vw_kpis_por_barrio_anio: {e}")
        
        # Vista: Resumen por distrito (para filtros del dashboard)
        try:
            conn.execute("DROP VIEW IF EXISTS vw_resumen_por_distrito")
            conn.execute("""
                CREATE VIEW vw_resumen_por_distrito AS
                SELECT 
                    b.distrito_nombre,
                    b.distrito_id,
                    COUNT(DISTINCT b.barrio_id) as num_barrios,
                    AVG(p.precio_m2_venta) as precio_m2_promedio,
                    SUM(d.poblacion_total) as poblacion_total,
                    AVG(r.renta_promedio) as renta_promedio
                FROM dim_barrios b
                LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id
                LEFT JOIN fact_demografia d ON b.barrio_id = d.barrio_id AND p.anio = d.anio
                LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND p.anio = r.anio
                WHERE p.anio = (SELECT MAX(anio) FROM fact_precios)
                GROUP BY b.distrito_nombre, b.distrito_id
            """)
            logger.info("  ✅ Vista creada: vw_resumen_por_distrito")
            created += 1
        except Exception as e:
            logger.warning(f"  ⚠️  Error creando vw_resumen_por_distrito: {e}")
    
    conn.commit()
    logger.info(f"📊 Total vistas optimizadas creadas: {created}")
    return created


def verify_views(conn) -> None:
    """Verifica que las vistas se hayan creado correctamente."""
    logger.info("🔍 Verificando vistas creadas...")
    
    cursor = conn.execute("""
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type = 'view' 
        AND (name LIKE '%_recent' OR name LIKE '%_historical' OR name LIKE 'vw_%')
        ORDER BY name
    """)
    
    views = cursor.fetchall()
    logger.info(f"📊 Total de vistas encontradas: {len(views)}")
    
    if views:
        logger.info("  ✅ Vistas creadas:")
        for view_name, _ in views[:10]:  # Mostrar primeras 10
            logger.info(f"    - {view_name}")


def main():
    """Función principal que ejecuta todas las mejoras de prioridad media."""
    logger.info("=" * 60)
    logger.info("🚀 Aplicando Mejoras de Prioridad Media a la Base de Datos")
    logger.info("=" * 60)
    
    if not DB_PATH.exists():
        logger.error(f"❌ Base de datos no encontrada: {DB_PATH}")
        return 1
    
    logger.info(f"📁 Base de datos: {DB_PATH}")
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    try:
        # 1. Crear vistas de particionamiento temporal
        logger.info("\n" + "=" * 60)
        logger.info("1️⃣  CREANDO VISTAS DE PARTICIONAMIENTO TEMPORAL")
        logger.info("=" * 60)
        views_created = create_temporal_partitioning_views(conn)
        
        # 2. Crear vistas optimizadas para consultas comunes
        logger.info("\n" + "=" * 60)
        logger.info("2️⃣  CREANDO VISTAS OPTIMIZADAS")
        logger.info("=" * 60)
        optimized_views = create_query_performance_views(conn)
        
        # 3. Actualizar estadísticas
        logger.info("\n" + "=" * 60)
        logger.info("3️⃣  ACTUALIZANDO ESTADÍSTICAS")
        logger.info("=" * 60)
        update_statistics(conn)
        
        # 4. Verificar resultados
        logger.info("\n" + "=" * 60)
        logger.info("4️⃣  VERIFICANDO RESULTADOS")
        logger.info("=" * 60)
        verify_views(conn)
        
        # Resumen
        logger.info("\n" + "=" * 60)
        logger.info("✅ RESUMEN DE MEJORAS APLICADAS")
        logger.info("=" * 60)
        logger.info(f"  📊 Vistas de particionamiento: {views_created}")
        logger.info(f"  📋 Vistas optimizadas: {optimized_views}")
        logger.info(f"  📈 Estadísticas actualizadas: ✅")
        logger.info("\n✅ Mejoras de prioridad media aplicadas exitosamente!")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error aplicando mejoras: {e}", exc_info=True)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
