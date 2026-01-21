#!/usr/bin/env python3
"""
Script para poblar fact_demografia desde fact_demografia_ampliada.

Cuando fact_demografia está vacía pero fact_demografia_ampliada tiene datos,
este script agrega los datos ampliados para crear registros en fact_demografia.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def main():
    """Poblar fact_demografia desde fact_demografia_ampliada."""
    if not DB_PATH.exists():
        print(f"❌ Base de datos no encontrada: {DB_PATH}")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Verificar si fact_demografia ya tiene datos
        count_existing = pd.read_sql(
            "SELECT COUNT(*) as cnt FROM fact_demografia",
            conn
        )["cnt"].iloc[0]
        
        if count_existing > 0:
            print(f"✅ fact_demografia ya tiene {count_existing} registros")
            print("   No es necesario poblar desde fact_demografia_ampliada")
            return 0
        
        # Verificar si fact_demografia_ampliada tiene datos
        count_ampliada = pd.read_sql(
            "SELECT COUNT(*) as cnt FROM fact_demografia_ampliada",
            conn
        )["cnt"].iloc[0]
        
        if count_ampliada == 0:
            print("❌ fact_demografia_ampliada también está vacía")
            print("   Necesitas ejecutar el ETL primero para cargar datos demográficos")
            return 1
        
        print(f"📊 fact_demografia_ampliada tiene {count_ampliada} registros")
        print("   Agregando datos para crear fact_demografia...")
        
        # Agregar datos desde fact_demografia_ampliada usando pandas para mejor control
        # En fact_demografia_ampliada:
        # - sexo puede ser 'hombre', 'mujer', o 'desconocido'
        # - grupo_edad puede ser '18-34', '35-49', '50-64', '65+', o NULL
        # - nacionalidad puede ser 'Española', 'Extranjera', etc.
        
        print("   Cargando datos desde fact_demografia_ampliada...")
        df_ampliada = pd.read_sql(
            "SELECT * FROM fact_demografia_ampliada WHERE poblacion IS NOT NULL",
            conn
        )
        
        if df_ampliada.empty:
            print("❌ No hay registros válidos en fact_demografia_ampliada")
            return 1
        
        print(f"   Procesando {len(df_ampliada)} registros...")
        
        # Agregar por barrio y año (ignorando dataset_id y source para evitar duplicados)
        aggregated = df_ampliada.groupby(['barrio_id', 'anio']).agg({
            'poblacion': 'sum',
            'dataset_id': 'first',  # Tomar el primero
            'source': 'first',
            'etl_loaded_at': 'first'
        }).reset_index()
        
        # Calcular poblacion_hombres y poblacion_mujeres
        hombres = df_ampliada[df_ampliada['sexo'] == 'hombre'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
        hombres.columns = ['barrio_id', 'anio', 'poblacion_hombres']
        
        mujeres = df_ampliada[df_ampliada['sexo'] == 'mujer'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
        mujeres.columns = ['barrio_id', 'anio', 'poblacion_mujeres']
        
        # Calcular pct_mayores_65
        mayores_65 = df_ampliada[df_ampliada['grupo_edad'] == '65+'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
        mayores_65.columns = ['barrio_id', 'anio', 'poblacion_mayores_65']
        
        # Merge todos los datos
        fact = aggregated.merge(hombres, on=['barrio_id', 'anio'], how='left')
        fact = fact.merge(mujeres, on=['barrio_id', 'anio'], how='left')
        fact = fact.merge(mayores_65, on=['barrio_id', 'anio'], how='left')
        
        # Renombrar y calcular campos
        fact = fact.rename(columns={'poblacion': 'poblacion_total'})
        fact['poblacion_hombres'] = fact['poblacion_hombres'].fillna(0).astype(int)
        fact['poblacion_mujeres'] = fact['poblacion_mujeres'].fillna(0).astype(int)
        fact['poblacion_total'] = fact['poblacion_total'].fillna(0).astype(int)
        
        # Calcular porcentajes
        fact['pct_mayores_65'] = (
            fact.apply(
                lambda row: (row['poblacion_mayores_65'] * 100.0 / row['poblacion_total'])
                if row['poblacion_total'] > 0 and pd.notna(row['poblacion_mayores_65'])
                else None,
                axis=1
            )
        )
        
        # Campos que no podemos calcular desde fact_demografia_ampliada
        fact['hogares_totales'] = None
        fact['edad_media'] = None
        fact['porc_inmigracion'] = None
        fact['densidad_hab_km2'] = None
        fact['pct_menores_15'] = None
        fact['indice_envejecimiento'] = None
        fact['etl_loaded_at'] = datetime.now().isoformat()
        
        # Eliminar columna temporal que no es parte del esquema
        fact = fact.drop(columns=['poblacion_mayores_65'], errors='ignore')
        
        # Seleccionar columnas en el orden correcto
        fact = fact[[
            'barrio_id', 'anio', 'poblacion_total', 'poblacion_hombres', 'poblacion_mujeres',
            'hogares_totales', 'edad_media', 'porc_inmigracion', 'densidad_hab_km2',
            'pct_mayores_65', 'pct_menores_15', 'indice_envejecimiento',
            'dataset_id', 'source', 'etl_loaded_at'
        ]]
        
        # Insertar en la base de datos usando INSERT OR REPLACE para manejar el índice único
        print(f"   Insertando {len(fact)} registros en fact_demografia...")
        cursor = conn.cursor()
        
        for _, row in fact.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO fact_demografia 
                (barrio_id, anio, poblacion_total, poblacion_hombres, poblacion_mujeres,
                 hogares_totales, edad_media, porc_inmigracion, densidad_hab_km2,
                 pct_mayores_65, pct_menores_15, indice_envejecimiento,
                 dataset_id, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['barrio_id']),
                int(row['anio']),
                int(row['poblacion_total']) if pd.notna(row['poblacion_total']) else None,
                int(row['poblacion_hombres']) if pd.notna(row['poblacion_hombres']) else None,
                int(row['poblacion_mujeres']) if pd.notna(row['poblacion_mujeres']) else None,
                int(row['hogares_totales']) if pd.notna(row['hogares_totales']) else None,
                float(row['edad_media']) if pd.notna(row['edad_media']) else None,
                float(row['porc_inmigracion']) if pd.notna(row['porc_inmigracion']) else None,
                float(row['densidad_hab_km2']) if pd.notna(row['densidad_hab_km2']) else None,
                float(row['pct_mayores_65']) if pd.notna(row['pct_mayores_65']) else None,
                float(row['pct_menores_15']) if pd.notna(row['pct_menores_15']) else None,
                float(row['indice_envejecimiento']) if pd.notna(row['indice_envejecimiento']) else None,
                str(row['dataset_id']) if pd.notna(row['dataset_id']) else None,
                str(row['source']) if pd.notna(row['source']) else None,
                str(row['etl_loaded_at']) if pd.notna(row['etl_loaded_at']) else None,
            ))
        
        conn.commit()
        rows_inserted = len(fact)
        
        if rows_inserted > 0:
            print(f"✅ {rows_inserted} registros insertados en fact_demografia")
            
            # Verificar resultado
            final_count = pd.read_sql(
                "SELECT COUNT(*) as cnt FROM fact_demografia",
                conn
            )["cnt"].iloc[0]
            
            print(f"✅ fact_demografia ahora tiene {final_count} registros")
            return 0
        else:
            print("⚠️  No se insertaron registros")
            print("   Puede que los datos en fact_demografia_ampliada no tengan el formato esperado")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
