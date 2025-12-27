from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .utils import cleaner, logger

def prepare_fact_renta_avanzada(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Combina datasets de renta (Gini, P80/P20, Bruta) en fact_renta_avanzada.
    """
    combined_df = pd.DataFrame()
    
    # Mapeo de columnas esperadas en OpenData BCN para estos datasets
    # Normalmente: Codi_Barri, Nom_Barri, Any, Valor
    
    for key, df in dfs.items():
        if df is None or df.empty:
            continue
            
        logger.info(f"Procesando componente de renta avanzada: {key}")
        df = df.copy()
        
        # Normalizar columnas
        df.columns = [c.strip() for c in df.columns]
        
        # Identificar columna de valor (suele ser 'Valor' o 'Import_Euros')
        valor_col = None
        for c in ['Valor', 'Import_Euros', 'Renda_Bruta_Llar', 'Index_Gini', 'Ratio_P80_P20']:
            if c in df.columns:
                valor_col = c
                break
        
        if not valor_col:
            # Buscar la primera columna numérica que no sea Codi_Barri ni Any
            cols = [c for c in df.columns if c not in ['Codi_Barri', 'Any', 'Nom_Barri', 'Codi_Districte', 'Nom_Districte']]
            if cols: valor_col = cols[0]
            
        if not valor_col:
            logger.warning(f"No se encontró columna de valor en {key}")
            continue

        # Renombrar según el dataset
        target_col = None
        if 'bruta' in key.lower() or 'gross' in key.lower():
            target_col = 'renta_bruta_llar'
        elif 'gini' in key.lower():
            target_col = 'indice_gini'
        elif 'p80' in key.lower():
            target_col = 'ratio_p80_p20'
            
        if not target_col:
            continue
            
        df = df.rename(columns={valor_col: target_col})
        
        # Identificar año robustamente
        if 'Any' not in df.columns:
            if 'Data_Referencia' in df.columns:
                df['Any'] = pd.to_datetime(df['Data_Referencia'], errors='coerce').dt.year
            elif 'Año' in df.columns:
                df = df.rename(columns={'Año': 'Any'})
            elif 'Anio' in df.columns:
                df = df.rename(columns={'Anio': 'Any'})
        
        # Identificar Codi_Barri robustamente
        if 'Codi_Barri' not in df.columns:
            if 'codi_barri' in df.columns:
                df = df.rename(columns={'codi_barri': 'Codi_Barri'})
            elif 'BARRIO_ID' in df.columns:
                df = df.rename(columns={'BARRIO_ID': 'Codi_Barri'})
        
        # Asegurar Any y Codi_Barri son numéricos
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        # Mergear con la base
        if combined_df.empty:
            combined_df = df[['Any', 'Codi_Barri', target_col]]
        else:
            # Asegurar tipos antes del merge
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df[['Any', 'Codi_Barri', target_col]], on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty:
        return pd.DataFrame()

    # Mapear barrio_id
    # Asegurar tipos antes del merge con dim_barrios
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(
        combined_df,
        dim_barrios_clean[['codi_barri_num', 'barrio_id']],
        left_on='Codi_Barri',
        right_on='codi_barri_num',
        how='inner'
    )
    
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    return combined_df[['barrio_id', 'anio', 'renta_bruta_llar', 'indice_gini', 'ratio_p80_p20', 'etl_loaded_at']]

def prepare_fact_catastro_avanzado(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Combina datasets de catastro en fact_catastro_avanzado.
    """
    combined_df = pd.DataFrame()
    
    for key, df in dfs.items():
        if df is None or df.empty:
            continue
            
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]
        
        # Identificar métricas
        if 'owner_type' in key:
            # Tipus_Propietari: 'Persona física', 'Persona jurídica'
            if 'Tipus_Propietari' in df.columns:
                p_fisica = df[df['Tipus_Propietari'] == 'Persona física'].groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                p_juridica = df[df['Tipus_Propietari'] == 'Persona jurídica'].groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                p_fisica = p_fisica.rename(columns={'Valor': 'num_propietarios_fisica'})
                p_juridica = p_juridica.rename(columns={'Valor': 'num_propietarios_juridica'})
                df = pd.merge(p_fisica, p_juridica, on=['Any', 'Codi_Barri'], how='outer')
        elif 'avg_surface' in key:
            df = df.rename(columns={'Valor': 'superficie_media_m2'})
        elif 'floors' in key:
            df = df.rename(columns={'Valor': 'num_plantas_avg'})
        elif 'year_const' in key:
            df = df.rename(columns={'Valor': 'antiguedad_media_bloque'})
        elif 'owner_nationality' in key:
            # Ejemplo: % extranjeros
            if 'Nacionalitat' in df.columns:
                extranjeros = df[df['Nacionalitat'] == 'Estrangera'].groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                total = df.groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                df = pd.merge(extranjeros, total, on=['Any', 'Codi_Barri'], suffixes=('_ext', '_total'))
                df['pct_propietarios_extranjeros'] = (df['Valor_ext'] / df['Valor_total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_propietarios_extranjeros']]
            else: continue
        else: continue

        # Asegurar tipos antes del merge
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        # Mergear
        if combined_df.empty:
            combined_df = df
        else:
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty: return pd.DataFrame()

    # Mapear barrio_id
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(
        combined_df, 
        dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
        left_on='Codi_Barri', 
        right_on='codi_barri_num', 
        how='inner'
    )
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    cols = ['barrio_id', 'anio', 'num_propietarios_fisica', 'num_propietarios_juridica', 
            'pct_propietarios_extranjeros', 'superficie_media_m2', 'num_plantas_avg', 
            'antiguedad_media_bloque', 'etl_loaded_at']
    return combined_df[[c for c in cols if c in combined_df.columns]]

def prepare_fact_hogares_avanzado(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Combina datasets de hogares en fact_hogares_avanzado.
    """
    combined_df = pd.DataFrame()
    
    for key, df in dfs.items():
        if df is None or df.empty: continue
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]

        # 1. Identificar año robustamente (AL PRINCIPIO)
        if 'Any' not in df.columns:
            if 'Data_Referencia' in df.columns:
                df['Any'] = pd.to_datetime(df['Data_Referencia'], errors='coerce').dt.year
            elif 'Año' in df.columns:
                df = df.rename(columns={'Año': 'Any'})
            elif 'Anio' in df.columns:
                df = df.rename(columns={'Anio': 'Any'})
        
        # 2. Identificar Codi_Barri robustamente (AL PRINCIPIO)
        if 'Codi_Barri' not in df.columns:
            if 'codi_barri' in df.columns:
                df = df.rename(columns={'codi_barri': 'Codi_Barri'})
            elif 'BARRIO_ID' in df.columns:
                df = df.rename(columns={'BARRIO_ID': 'Codi_Barri'})

        # 3. Procesamiento específico
        if 'crowding' in key:
            # Personas por hogar
            df = df.rename(columns={'Valor': 'promedio_personas_por_hogar'})
        elif 'minors' in key:
            df = df.rename(columns={'Valor': 'num_hogares_con_menores'})
        elif 'women' in key:
            df = df.rename(columns={'Valor': 'pct_presencia_mujeres'})
        elif 'nationality' in key:
            if 'Nacionalitat' in df.columns and 'Any' in df.columns and 'Codi_Barri' in df.columns:
                extranjeros = df[df['Nacionalitat'] == 'Estrangera'].groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                total = df.groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                df = pd.merge(extranjeros, total, on=['Any', 'Codi_Barri'], suffixes=('_ext', '_total'))
                df['pct_hogares_nacionalidad_extranjera'] = (df['Valor_ext'] / df['Valor_total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_hogares_nacionalidad_extranjera']]
            else: continue
        else: continue

        # Asegurar tipos antes del merge
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        if combined_df.empty: combined_df = df
        else: 
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty: return pd.DataFrame()

    # Mapear barrio_id
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(
        combined_df, 
        dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
        left_on='Codi_Barri', 
        right_on='codi_barri_num', 
        how='inner'
    )
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    cols = ['barrio_id', 'anio', 'promedio_personas_por_hogar', 'pct_hogares_unipersonales',
            'num_hogares_con_menores', 'pct_hogares_nacionalidad_extranjera', 
            'pct_presencia_mujeres', 'etl_loaded_at']
    return combined_df[[c for c in cols if c in combined_df.columns]]

def prepare_fact_turismo_intensidad(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    combined_df = pd.DataFrame()
    for key, df in dfs.items():
        if df is None or df.empty: continue
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]
        
        # 1. Identificar año robustamente
        if 'Any' not in df.columns:
            if 'Data_Referencia' in df.columns:
                df['Any'] = pd.to_datetime(df['Data_Referencia'], errors='coerce').dt.year
            elif 'Año' in df.columns:
                df = df.rename(columns={'Año': 'Any'})
            elif 'Anio' in df.columns:
                df = df.rename(columns={'Anio': 'Any'})
        
        # 2. Identificar Codi_Barri robustamente
        if 'Codi_Barri' not in df.columns:
            if 'codi_barri' in df.columns:
                df = df.rename(columns={'codi_barri': 'Codi_Barri'})

        # 3. Procesamiento específico
        if 'intensity' in key:
            df = df.rename(columns={'Valor': 'indice_intensidad_turistica'})
        elif 'hut' in key:
            df = df.rename(columns={'Valor': 'num_establecimientos_turisticos'})
        else: continue
        
        # Asegurar tipos antes del merge
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        if combined_df.empty: combined_df = df
        else: 
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty: return pd.DataFrame()

    # Mapear barrio_id
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(
        combined_df, 
        dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
        left_on='Codi_Barri', 
        right_on='codi_barri_num', 
        how='inner'
    )
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    return combined_df[['barrio_id', 'anio', 'indice_intensidad_turistica', 'num_establecimientos_turisticos', 'etl_loaded_at']]
