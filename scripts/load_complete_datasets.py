"""
Script para cargar datasets completos sin límite de filas.

Carga todos los datos disponibles de:
- fact_catastro_avanzado
- fact_hogares_avanzado
- fact_renta_avanzada (ya completo)

Sin restricción de chunk size.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import gc

from src.etl.transformations.advanced_analysis import (
    prepare_fact_catastro_avanzado,
    prepare_fact_hogares_avanzado,
    prepare_fact_renta_avanzada
)
from src.etl.batch_processor import insert_dataframe_in_batches

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_complete_datasets():
    """Carga datasets completos sin límite de filas"""
    
    db_path = Path("data/database.db")
    raw_data_dir = Path("data/raw/opendatabcn")
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    reference_time = datetime.utcnow()
    
    # Cargar dim_barrios
    logger.info("Cargando dim_barrios...")
    dim_barrios = pd.read_sql("SELECT * FROM dim_barrios", conn)
    logger.info(f"✓ dim_barrios cargada: {len(dim_barrios)} barrios")
    
    # =================================================================
    # 1. CATASTRO COMPLETO
    # =================================================================
    logger.info("\n" + "="*80)
    logger.info("1. CARGANDO CATASTRO COMPLETO (SIN LÍMITE)")
    logger.info("="*80)
    
    cadastre_files = {
        'cadastre_owner_type': 'opendatabcn_est-cadastre-carrecs-tipus-propietari_2020_2024_20251227_161618_557820.csv',
        'cadastre_owner_nationality': 'opendatabcn_est-cadastre-locals-prop_2020_2024_20251227_161636_616393.csv',
        'cadastre_avg_surface': 'opendatabcn_est-cadastre-habitatges-superficie-mitjana_2020_2024_20251227_161627_412631.csv',
        'cadastre_year_const': 'opendatabcn_est-cadastre-habitatges-any-const_2020_2024_20251227_161609_521294.csv',
    }
    
    cadastre_dfs = {}
    total_rows = 0
    
    for key, filename in cadastre_files.items():
        file_path = raw_data_dir / filename
        if file_path.exists():
            logger.info(f"  Cargando {key}: {filename}")
            df = pd.read_csv(file_path)
            cadastre_dfs[key] = df
            total_rows += len(df)
            logger.info(f"    ✓ {len(df):,} filas cargadas")
        else:
            logger.warning(f"  ✗ No encontrado: {filename}")
    
    logger.info(f"\nTotal filas cargadas: {total_rows:,}")
    
    # Transformar
    logger.info("\nTransformando datos de catastro...")
    catastro_df = prepare_fact_catastro_avanzado(cadastre_dfs, dim_barrios, reference_time)
    
    if not catastro_df.empty:
        logger.info(f"✓ Transformación completada: {len(catastro_df)} filas")
        
        # Borrar datos anteriores (deshabilitar foreign keys)
        logger.info("Borrando datos anteriores de fact_catastro_avanzado...")
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("DELETE FROM fact_catastro_avanzado")
        conn.commit()
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Insertar nuevos datos
        logger.info("Insertando datos completos...")
        insert_dataframe_in_batches(
            catastro_df,
            'fact_catastro_avanzado',
            conn,
            batch_size=1000
        )
        logger.info("✅ fact_catastro_avanzado completado")
        
        # Estadísticas
        logger.info("\nEstadísticas de catastro:")
        logger.info(f"  Total filas: {len(catastro_df):,}")
        logger.info(f"  Años: {catastro_df['anio'].min()} - {catastro_df['anio'].max()}")
        logger.info(f"  Barrios: {catastro_df['barrio_id'].nunique()}")
        
        if 'superficie_media_m2' in catastro_df.columns:
            logger.info(f"  Superficie media: {catastro_df['superficie_media_m2'].mean():.1f} m²")
        if 'antiguedad_media_bloque' in catastro_df.columns:
            logger.info(f"  Antigüedad media: {catastro_df['antiguedad_media_bloque'].mean():.1f} años")
        if 'pct_propietarios_extranjeros' in catastro_df.columns:
            logger.info(f"  % Propietarios extranjeros: {catastro_df['pct_propietarios_extranjeros'].mean():.1f}%")
    else:
        logger.error("✗ No se generaron datos de catastro")
    
    # Liberar memoria
    del cadastre_dfs, catastro_df
    gc.collect()
    
    # =================================================================
    # 2. HOGARES COMPLETO
    # =================================================================
    logger.info("\n" + "="*80)
    logger.info("2. CARGANDO HOGARES COMPLETO (SIN LÍMITE)")
    logger.info("="*80)
    
    household_files = {
        'household_minors': 'opendatabcn_pad_dom_mdbas_edat-0018_2020_2024_20251227_161705_194660.csv',
        'household_crowding': 'opendatabcn_pad_dom_mdbas_n-persones_2020_2024_20251227_161647_203814.csv',
        'household_women': 'opendatabcn_pad_dom_mdbas_dones_2020_2024_20251227_161714_231951.csv',
        'household_nationality': 'opendatabcn_pad_dom_mdbas_nacionalitat_2020_2024_20251227_161656_129978.csv',
    }
    
    household_dfs = {}
    total_rows = 0
    
    for key, filename in household_files.items():
        file_path = raw_data_dir / filename
        if file_path.exists():
            logger.info(f"  Cargando {key}: {filename}")
            df = pd.read_csv(file_path)
            household_dfs[key] = df
            total_rows += len(df)
            logger.info(f"    ✓ {len(df):,} filas cargadas")
        else:
            logger.warning(f"  ✗ No encontrado: {filename}")
    
    logger.info(f"\nTotal filas cargadas: {total_rows:,}")
    
    # Transformar
    logger.info("\nTransformando datos de hogares...")
    hogares_df = prepare_fact_hogares_avanzado(household_dfs, dim_barrios, reference_time)
    
    if not hogares_df.empty:
        logger.info(f"✓ Transformación completada: {len(hogares_df)} filas")
        
        # Borrar datos anteriores (deshabilitar foreign keys)
        logger.info("Borrando datos anteriores de fact_hogares_avanzado...")
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("DELETE FROM fact_hogares_avanzado")
        conn.commit()
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Insertar nuevos datos
        logger.info("Insertando datos completos...")
        insert_dataframe_in_batches(
            hogares_df,
            'fact_hogares_avanzado',
            conn,
            batch_size=1000
        )
        logger.info("✅ fact_hogares_avanzado completado")
        
        # Estadísticas
        logger.info("\nEstadísticas de hogares:")
        logger.info(f"  Total filas: {len(hogares_df):,}")
        logger.info(f"  Años: {hogares_df['anio'].min()} - {hogares_df['anio'].max()}")
        logger.info(f"  Barrios: {hogares_df['barrio_id'].nunique()}")
        
        if 'promedio_personas_por_hogar' in hogares_df.columns:
            non_null = hogares_df['promedio_personas_por_hogar'].dropna()
            if len(non_null) > 0:
                logger.info(f"  Promedio personas/hogar: {non_null.mean():.2f}")
        if 'pct_hogares_nacionalidad_extranjera' in hogares_df.columns:
            non_null = hogares_df['pct_hogares_nacionalidad_extranjera'].dropna()
            if len(non_null) > 0:
                logger.info(f"  % Hogares extranjeros: {non_null.mean():.1f}%")
    else:
        logger.error("✗ No se generaron datos de hogares")
    
    # Liberar memoria
    del household_dfs, hogares_df
    gc.collect()
    
    conn.close()
    
    # =================================================================
    # 3. COPIAR A MASTER.DB
    # =================================================================
    logger.info("\n" + "="*80)
    logger.info("3. COPIANDO A MASTER.DB")
    logger.info("="*80)
    
    master_db = Path("data/master.db")
    if master_db.exists():
        logger.info("Actualizando master.db...")
        
        conn_src = sqlite3.connect(db_path)
        conn_dst = sqlite3.connect(master_db)
        
        for table in ['fact_catastro_avanzado', 'fact_hogares_avanzado']:
            logger.info(f"\n  Copiando {table}...")
            
            # Borrar datos anteriores
            conn_dst.execute(f"DELETE FROM {table}")
            conn_dst.commit()
            
            # Copiar nuevos datos
            df = pd.read_sql(f"SELECT * FROM {table}", conn_src)
            if not df.empty:
                df.to_sql(table, conn_dst, if_exists='append', index=False)
                logger.info(f"    ✓ {len(df):,} filas copiadas")
            else:
                logger.warning(f"    ⚠️  Tabla vacía")
        
        conn_src.close()
        conn_dst.close()
        
        logger.info("\n✅ master.db actualizado")
    else:
        logger.warning("master.db no encontrado, saltando actualización")
    
    # =================================================================
    # RESUMEN FINAL
    # =================================================================
    logger.info("\n" + "="*80)
    logger.info("RESUMEN FINAL")
    logger.info("="*80)
    
    conn = sqlite3.connect(db_path)
    
    for table in ['fact_catastro_avanzado', 'fact_hogares_avanzado', 'fact_renta_avanzada']:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
            years = pd.read_sql(f"SELECT MIN(anio) as min, MAX(anio) as max FROM {table}", conn).iloc[0]
            barrios = pd.read_sql(f"SELECT COUNT(DISTINCT barrio_id) as count FROM {table}", conn).iloc[0]['count']
            
            logger.info(f"\n{table}:")
            logger.info(f"  Filas: {count:,}")
            logger.info(f"  Años: {int(years['min'])} - {int(years['max'])}")
            logger.info(f"  Barrios: {int(barrios)}")
        except Exception as e:
            logger.error(f"{table}: Error - {e}")
    
    conn.close()
    
    logger.info("\n✅ Carga completa finalizada")

if __name__ == "__main__":
    load_complete_datasets()
