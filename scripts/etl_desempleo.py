"""
Transformación y carga de datos de desempleo (atur registrat).

Este script:
1. Extrae datos de desempleo de Open Data BCN
2. Transforma y normaliza los datos
3. Mapea barrios a IDs
4. Calcula tasa de desempleo estimada
5. Carga los datos en fact_desempleo

Autor: Barcelona Housing Demographics Analyzer
Fecha: 2026-01-05
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.database import DatabaseManager
from src.extraction.desempleo_extractor import DesempleoExtractor


def map_barrios_to_ids(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mapea nombres de barrios a IDs usando la tabla dim_barrios.
    
    Args:
        df: DataFrame con columna 'barrio_nombre'.
    
    Returns:
        DataFrame con columna 'barrio_id' añadida.
    """
    print("  • Mapeando barrios a IDs...")
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    # Obtener mapeo de barrios
    barrios_df = pd.read_sql("""
        SELECT barrio_id, barrio_nombre, barrio_nombre_normalizado
        FROM dim_barrios
    """, conn)
    
    conn.close()
    
    # Normalizar nombres para mejor matching
    df['barrio_nombre_norm'] = df['barrio_nombre'].str.lower().str.strip()
    barrios_df['barrio_nombre_norm'] = barrios_df['barrio_nombre'].str.lower().str.strip()
    
    # Merge
    df = df.merge(
        barrios_df[['barrio_id', 'barrio_nombre_norm']],
        on='barrio_nombre_norm',
        how='left'
    )
    
    # Limpiar columna temporal
    df = df.drop(columns=['barrio_nombre_norm'])
    
    return df


def transform_desempleo_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforma datos de desempleo.
    
    Args:
        df: DataFrame con datos crudos de desempleo.
    
    Returns:
        DataFrame transformado listo para cargar.
    """
    print("\n📊 Transformando datos de desempleo...")
    
    if df.empty:
        print("❌ DataFrame vacío, no hay nada que transformar")
        return pd.DataFrame()
    
    # 1. Mapear barrios a IDs
    df = map_barrios_to_ids(df)
    
    # Verificar mapeo
    unmapped = df[df['barrio_id'].isna()]
    if not unmapped.empty:
        print(f"  ⚠️  {len(unmapped)} registros sin mapear:")
        print(f"     Barrios: {unmapped['barrio_nombre'].unique()[:5]}")
    
    # Eliminar registros sin barrio_id
    df = df[df['barrio_id'].notna()]
    print(f"  • Registros después de mapeo: {len(df):,}")
    
    # 2. Calcular tasa de desempleo estimada si no existe
    if 'tasa_desempleo' not in df.columns or df['tasa_desempleo'].isna().all():
        print("  • Calculando tasa de desempleo estimada...")
        
        # Obtener población activa por barrio (aproximación)
        # Usaremos población total * 0.65 (tasa de actividad aproximada)
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        
        poblacion_df = pd.read_sql("""
            SELECT barrio_id, poblacion_total
            FROM fact_demografia
            WHERE anio = (SELECT MAX(anio) FROM fact_demografia)
        """, conn)
        
        conn.close()
        
        # Merge con población
        df = df.merge(poblacion_df, on='barrio_id', how='left')
        
        # Calcular tasa (desempleados / población activa * 100)
        df['poblacion_activa'] = df['poblacion_total'] * 0.65
        df['tasa_desempleo_estimada'] = (
            df['num_desempleados'] / df['poblacion_activa'] * 100
        ).round(2)
        
        # Limpiar columnas temporales
        df = df.drop(columns=['poblacion_total', 'poblacion_activa'], errors='ignore')
        
        print(f"     Tasa promedio: {df['tasa_desempleo_estimada'].mean():.2f}%")
    
    # 3. Seleccionar y ordenar columnas finales
    final_columns = [
        'barrio_id',
        'anio',
        'mes',
        'num_desempleados',
        'tasa_desempleo_estimada',
        'dataset_id',
        'source',
        'etl_loaded_at'
    ]
    
    # Añadir columnas faltantes
    for col in final_columns:
        if col not in df.columns:
            if col == 'dataset_id':
                df[col] = 'opendata_bcn_atur'
            elif col == 'source':
                df[col] = 'opendata_bcn_desempleo'
            elif col == 'mes':
                df[col] = None  # Puede ser None si solo hay datos anuales
            else:
                df[col] = None
    
    # Seleccionar solo columnas finales
    df = df[final_columns]
    
    # 4. Convertir tipos
    df['barrio_id'] = df['barrio_id'].astype(int)
    df['anio'] = df['anio'].astype(int)
    
    if df['mes'].notna().any():
        df['mes'] = df['mes'].fillna(0).astype(int)
    
    df['num_desempleados'] = df['num_desempleados'].astype(int)
    
    print(f"✅ Transformación completada: {len(df):,} registros")
    
    return df


def load_desempleo_data(df: pd.DataFrame) -> int:
    """
    Carga datos de desempleo en la base de datos.
    
    Args:
        df: DataFrame con datos transformados.
    
    Returns:
        Número de registros insertados.
    """
    print("\n💾 Cargando datos en fact_desempleo...")
    
    if df.empty:
        print("❌ No hay datos para cargar")
        return 0
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Insertar datos
        inserted = 0
        
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO fact_desempleo (
                        barrio_id, anio, mes, num_desempleados,
                        tasa_desempleo_estimada, dataset_id, source, etl_loaded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['barrio_id'],
                    row['anio'],
                    row['mes'] if pd.notna(row['mes']) else None,
                    row['num_desempleados'],
                    row['tasa_desempleo_estimada'] if pd.notna(row['tasa_desempleo_estimada']) else None,
                    row['dataset_id'],
                    row['source'],
                    row['etl_loaded_at']
                ))
                inserted += 1
                
            except Exception as e:
                print(f"  ⚠️  Error insertando registro: {e}")
                print(f"     Barrio: {row['barrio_id']}, Año: {row['anio']}")
                continue
        
        conn.commit()
        print(f"✅ Insertados {inserted:,} registros en fact_desempleo")
        
        # Verificar carga
        cursor.execute("SELECT COUNT(*) FROM fact_desempleo")
        total = cursor.fetchone()[0]
        print(f"📊 Total registros en fact_desempleo: {total:,}")
        
        return inserted
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante la carga: {e}")
        raise
    finally:
        conn.close()


def main():
    """Función principal del ETL de desempleo."""
    print("=" * 80)
    print("ETL DE DESEMPLEO (ATUR REGISTRAT)")
    print("=" * 80)
    
    try:
        # 1. Extracción
        print("\n📥 FASE 1: EXTRACCIÓN")
        print("-" * 80)
        
        extractor = DesempleoExtractor()
        df_raw, metadata = extractor.extract_all()
        
        if df_raw.empty:
            print("\n❌ No se pudieron extraer datos de desempleo")
            print("\n💡 Posibles soluciones:")
            print("  1. Verificar conexión a internet")
            print("  2. Verificar que el dataset existe en Open Data BCN")
            print("  3. Revisar logs para más detalles")
            return
        
        print(f"\n✅ Extracción completada:")
        print(f"  • Registros extraídos: {len(df_raw):,}")
        print(f"  • Columnas: {list(df_raw.columns)}")
        
        if 'anio' in df_raw.columns:
            print(f"  • Años: {sorted(df_raw['anio'].unique())}")
        
        if 'barrio_nombre' in df_raw.columns:
            print(f"  • Barrios únicos: {df_raw['barrio_nombre'].nunique()}")
        
        # 2. Transformación
        print("\n🔄 FASE 2: TRANSFORMACIÓN")
        print("-" * 80)
        
        df_transformed = transform_desempleo_data(df_raw)
        
        if df_transformed.empty:
            print("\n❌ La transformación no produjo datos válidos")
            return
        
        # 3. Carga
        print("\n💾 FASE 3: CARGA")
        print("-" * 80)
        
        inserted = load_desempleo_data(df_transformed)
        
        # 4. Resumen final
        print("\n" + "=" * 80)
        print("✅ ETL COMPLETADO")
        print("=" * 80)
        print(f"\n📊 Resumen:")
        print(f"  • Registros extraídos: {len(df_raw):,}")
        print(f"  • Registros transformados: {len(df_transformed):,}")
        print(f"  • Registros insertados: {inserted:,}")
        
        if inserted > 0:
            print(f"\n🎯 Próximos pasos:")
            print(f"  1. Verificar datos: python scripts/schema_health_cli.py current")
            print(f"  2. Crear snapshot: python scripts/schema_health_cli.py snapshot")
            print(f"  3. Ver tabla: python scripts/schema_health_cli.py table fact_desempleo")
        
    except Exception as e:
        print(f"\n❌ Error durante el ETL: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
