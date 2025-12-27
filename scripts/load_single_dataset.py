"""
Script ultra-optimizado para cargar catastro y hogares con chunks muy pequeños.
Procesa un dataset a la vez para minimizar uso de memoria.
"""
import gc
import logging
from pathlib import Path
import pandas as pd

from src.database_setup import create_connection, create_database_schema
from src.etl.batch_processor import insert_dataframe_in_batches, optimize_dataframe_memory
from src.etl.transformations.advanced_analysis import (
    prepare_fact_catastro_avanzado,
    prepare_fact_hogares_avanzado,
)
from src import data_processing
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw/opendatabcn")

def load_single_dataset_ultra_light(dataset_type='catastro'):
    """
    Carga un solo tipo de dataset con máxima optimización de memoria.
    
    Args:
        dataset_type: 'catastro' o 'hogares'
    """
    logger.info(f"=== Carga Ultra-Optimizada: {dataset_type.upper()} ===")
    
    # Conectar a base de datos
    db_path = Path("data/database.db")
    conn = create_connection(db_path)
    
    reference_time = datetime.utcnow()
    
    # Cargar dim_barrios
    logger.info("Cargando dim_barrios...")
    dim_barrios = pd.read_sql("SELECT * FROM dim_barrios", conn)
    
    if dim_barrios.empty:
        logger.error("dim_barrios está vacía. Ejecuta load_advanced_only.py primero.")
        return
    
    logger.info(f"✓ dim_barrios cargada: {len(dim_barrios)} barrios")
    
    # Definir patrones según tipo
    if dataset_type == 'catastro':
        file_patterns = {
            'est-cadastre-habitatges-any-const': 'cadastre_year_const',
            'est-cadastre-carrecs-tipus-propietari': 'cadastre_owner_type',
            'est-cadastre-habitatges-superficie-mitjana': 'cadastre_avg_surface',
            'est-cadastre-locals-prop': 'cadastre_owner_nationality',
        }
        table_name = 'fact_catastro_avanzado'
        prepare_func = prepare_fact_catastro_avanzado
    else:  # hogares
        file_patterns = {
            'pad_dom_mdbas_n-persones': 'household_crowding',
            'pad_dom_mdbas_nacionalitat': 'household_nationality',
            'pad_dom_mdbas_edat-0018': 'household_minors',
            'pad_dom_mdbas_dones': 'household_women',
        }
        table_name = 'fact_hogares_avanzado'
        prepare_func = prepare_fact_hogares_avanzado
    
    # Descubrir y cargar archivos UNO POR UNO
    logger.info(f"\n=== Descubriendo Archivos de {dataset_type.upper()} ===")
    
    dataset_files = {}
    
    for csv_file in RAW_DIR.glob("*.csv"):
        for pattern, key in file_patterns.items():
            if pattern in csv_file.name and '2020_2024' in csv_file.name:
                logger.info(f"  ✓ {key}: {csv_file.name}")
                
                # Leer SOLO 1 chunk (25k filas máximo)
                chunks = []
                try:
                    for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=25000, low_memory=False)):
                        chunks.append(chunk)
                        if i >= 0:  # Solo 1 chunk = 25k filas
                            logger.info(f"    Limitado a 25,000 filas para evitar OOM")
                            break
                    
                    if chunks:
                        df = pd.concat(chunks, ignore_index=True)
                        logger.info(f"    Cargadas {len(df):,} filas")
                        del chunks
                        gc.collect()
                        
                        dataset_files[key] = df
                    
                except Exception as e:
                    logger.warning(f"  ⚠ Error leyendo {key}: {e}")
                
                break
    
    if not dataset_files:
        logger.warning(f"No se encontraron archivos para {dataset_type}")
        return
    
    # Procesar y cargar
    logger.info(f"\n=== Procesando {table_name} ===")
    
    try:
        result_df = prepare_func(dataset_files, dim_barrios, reference_time)
        
        if result_df is not None and not result_df.empty:
            logger.info(f"Transformación completada: {len(result_df):,} filas")
            
            # Optimizar memoria
            result_df = optimize_dataframe_memory(result_df)
            
            # Insertar
            rows = insert_dataframe_in_batches(
                result_df, table_name, conn,
                batch_size=500,  # Lotes muy pequeños
                clear_first=True
            )
            
            logger.info(f"✅ {table_name}: {rows:,} filas insertadas exitosamente")
            
            del result_df
            gc.collect()
        else:
            logger.warning(f"No se generaron datos para {table_name}")
        
        # Limpiar archivos cargados
        del dataset_files
        gc.collect()
        
    except Exception as e:
        logger.error(f"❌ Error procesando {table_name}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()
    
    logger.info(f"\n✅ Carga de {dataset_type} completada")

if __name__ == "__main__":
    import sys
    
    # Permitir especificar qué dataset cargar
    dataset_type = sys.argv[1] if len(sys.argv) > 1 else 'catastro'
    
    if dataset_type not in ['catastro', 'hogares']:
        print("Uso: python3 -m scripts.load_single_dataset [catastro|hogares]")
        sys.exit(1)
    
    load_single_dataset_ultra_light(dataset_type)
