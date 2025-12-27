"""
Script simplificado para cargar SOLO los datasets avanzados usando batch processing.
Evita cargar todos los datos legacy que causan OOM.
"""
import gc
import logging
from pathlib import Path
import pandas as pd
import sqlite3

from src.database_setup import create_connection, create_database_schema
from src.etl.batch_processor import insert_dataframe_in_batches, optimize_dataframe_memory
from src.etl.transformations.advanced_analysis import (
    prepare_fact_renta_avanzada,
    prepare_fact_catastro_avanzado,
    prepare_fact_hogares_avanzado,
    prepare_fact_turismo_intensidad,
)
from src import data_processing
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/opendatabcn")

def load_advanced_datasets_only():
    """Carga solo los datasets avanzados para evitar OOM."""
    
    logger.info("=== ETL Simplificado: Solo Datasets Avanzados ===")
    
    # Crear/conectar a base de datos
    db_path = Path("data/database.db")
    conn = create_connection(db_path)
    create_database_schema(conn)
    
    reference_time = datetime.utcnow()
    
    # Cargar dim_barrios - si está vacía, crearla desde demographics
    logger.info("Verificando dim_barrios...")
    dim_barrios = pd.read_sql("SELECT * FROM dim_barrios", conn)
    
    if dim_barrios.empty:
        logger.info("dim_barrios vacía. Creando desde datos demográficos...")
        
        # Buscar archivo de demografía más reciente
        demo_files = list(RAW_DIR.glob("opendatabcn_demographics_*.csv"))
        if not demo_files:
            demo_files = list(RAW_DIR.glob("opendatabcn_pad_mdbas_sexe_*.csv"))
        
        if demo_files:
            demo_file = max(demo_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"  Usando: {demo_file.name}")
            
            # Leer solo las primeras 10k filas para crear dim_barrios
            dem_df = pd.read_csv(demo_file, nrows=10000, low_memory=False)
            
            # Crear dim_barrios
            dim_barrios = data_processing.prepare_dim_barrios(
                dem_df,
                dataset_id="pad_mdbas_sexe",
                reference_time=reference_time
            )
            
            # Guardar en base de datos
            dim_barrios.to_sql("dim_barrios", conn, if_exists="replace", index=False)
            logger.info(f"✓ dim_barrios creada con {len(dim_barrios)} barrios")
            
            del dem_df
            gc.collect()
        else:
            logger.error("No se encontraron archivos de demografía. No se puede crear dim_barrios.")
            return
    else:
        logger.info(f"✓ dim_barrios cargada: {len(dim_barrios)} barrios")
    
    # Descubrir archivos avanzados
    logger.info("\n=== Descubriendo Datasets Avanzados ===")
    
    renta_files = {}
    catastro_files = {}
    hogares_files = {}
    
    # Mapeo de patrones de archivo a keys
    file_patterns = {
        'atles-renda-bruta-per-llar': 'income_gross_household',
        'atles-renda-index-gini': 'income_gini',
        'atles-renda-p80-p20': 'income_p80_p20',
        'est-cadastre-habitatges-any-const': 'cadastre_year_const',
        'est-cadastre-carrecs-tipus-propietari': 'cadastre_owner_type',
        'est-cadastre-habitatges-superficie-mitjana': 'cadastre_avg_surface',
        'est-cadastre-locals-prop': 'cadastre_owner_nationality',
        'pad_dom_mdbas_n-persones': 'household_crowding',
        'pad_dom_mdbas_nacionalitat': 'household_nationality',
        'pad_dom_mdbas_edat-0018': 'household_minors',
        'pad_dom_mdbas_dones': 'household_women',
    }
    
    for csv_file in RAW_DIR.glob("*.csv"):
        for pattern, key in file_patterns.items():
            if pattern in csv_file.name and '2020_2024' in csv_file.name:
                logger.info(f"  ✓ {key}: {csv_file.name}")
                
                # Leer CSV en chunks para evitar OOM
                chunks = []
                try:
                    for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=50000, low_memory=False)):
                        chunks.append(chunk)
                        if i >= 5:  # Máximo 250k filas (5 chunks de 50k)
                            break
                    
                    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
                    del chunks
                    gc.collect()
                    
                    # Asignar a diccionario correspondiente
                    if 'income' in key:
                        renta_files[key] = df
                    elif 'cadastre' in key:
                        catastro_files[key] = df
                    elif 'household' in key:
                        hogares_files[key] = df
                    
                except Exception as e:
                    logger.warning(f"  ⚠ Error leyendo {key}: {e}")
                
                break
    
    # Procesar y cargar cada tabla
    logger.info("\n=== Procesando y Cargando Datasets ===")
    
    try:
        # 1. Renta Avanzada
        if renta_files:
            logger.info("📊 Procesando fact_renta_avanzada...")
            fact_renta = prepare_fact_renta_avanzada(renta_files, dim_barrios, reference_time)
            if fact_renta is not None and not fact_renta.empty:
                fact_renta = optimize_dataframe_memory(fact_renta)
                rows = insert_dataframe_in_batches(
                    fact_renta, "fact_renta_avanzada", conn,
                    batch_size=1000, clear_first=True
                )
                logger.info(f"  ✅ {rows:,} filas insertadas")
            del fact_renta, renta_files
            gc.collect()
        
        # 2. Catastro Avanzado
        if catastro_files:
            logger.info("📊 Procesando fact_catastro_avanzado...")
            fact_catastro = prepare_fact_catastro_avanzado(catastro_files, dim_barrios, reference_time)
            if fact_catastro is not None and not fact_catastro.empty:
                fact_catastro = optimize_dataframe_memory(fact_catastro)
                rows = insert_dataframe_in_batches(
                    fact_catastro, "fact_catastro_avanzado", conn,
                    batch_size=1000, clear_first=True
                )
                logger.info(f"  ✅ {rows:,} filas insertadas")
            del fact_catastro, catastro_files
            gc.collect()
        
        # 3. Hogares Avanzado
        if hogares_files:
            logger.info("📊 Procesando fact_hogares_avanzado...")
            fact_hogares = prepare_fact_hogares_avanzado(hogares_files, dim_barrios, reference_time)
            if fact_hogares is not None and not fact_hogares.empty:
                fact_hogares = optimize_dataframe_memory(fact_hogares)
                rows = insert_dataframe_in_batches(
                    fact_hogares, "fact_hogares_avanzado", conn,
                    batch_size=1000, clear_first=True
                )
                logger.info(f"  ✅ {rows:,} filas insertadas")
            del fact_hogares, hogares_files
            gc.collect()
        
        logger.info("\n✅ ETL de datasets avanzados completado exitosamente")
        
        # Verificar resultados
        logger.info("\n=== Verificación Final ===")
        for table in ['fact_renta_avanzada', 'fact_catastro_avanzado', 'fact_hogares_avanzado']:
            try:
                count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
                logger.info(f"  {table}: {count:,} filas")
            except Exception as e:
                logger.warning(f"  {table}: Error - {e}")
        
    except Exception as e:
        logger.error(f"❌ Error durante ETL: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    load_advanced_datasets_only()
