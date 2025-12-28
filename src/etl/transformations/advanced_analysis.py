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
        
        # 1. Normalización agresiva
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {
            "any": "Any", "data_referencia": "Any", "año": "Any", "anio": "Any",
            "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
            "valor": "Valor", "import_euros": "Valor",
            # Mapeo específico para datasets de renta (múltiples encodings del símbolo €)
            "import_renda_bruta_€": "Valor",
            "import_renda_bruta_â¬": "Valor",
            "import_renda_bruta_â\x82¬": "Valor",
            "import_renda_bruta_eur": "Valor",
            "index_gini": "Valor",
            "distribucio_p80_20": "Valor"
        }
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})

        # 2. Identificar métricas
        target_col = None
        if 'bruta' in key.lower() or 'gross' in key.lower():
            target_col = 'renta_bruta_llar'
        elif 'gini' in key.lower():
            target_col = 'indice_gini'
        elif 'p80' in key.lower():
            target_col = 'ratio_p80_p20'
            
        if not target_col:
            continue
            
        # 3. Verificar que existe la columna Valor
        if 'Valor' not in df.columns:
            logger.warning(f"No se encontró columna 'Valor' en {key} después de normalización. Columnas: {list(df.columns)}")
            continue

        df = df.rename(columns={'Valor': target_col})
        
        # 4. Asegurar Any y Codi_Barri son numéricos
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        # AGREGAR: Los datos vienen por sección censal, necesitamos nivel barrio
        # Para renta, tomamos la media de las secciones (aproximación común si no hay pesos)
        df = df.groupby(['Any', 'Codi_Barri'])[target_col].mean().reset_index()
        
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
        
        # 1. Normalización agresiva
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {
            "any": "Any", "data_referencia": "Any", "año": "Any", "anio": "Any",
            "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
            "valor": "Valor"
        }
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})

        # 2. Asegurar Any y Codi_Barri son numéricos
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        # 3. Identificar métricas y agregar INMEDIATAMENTE
        if 'owner_type' in key:
            # Tipus_Propietari: 'Persona física', 'Persona jurídica'
            tp_col = 'tipus_propietari' if 'tipus_propietari' in df.columns else None
            if tp_col:
                p_fisica = df[df[tp_col] == 'Persona física'].groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_fisica')
                p_juridica = df[df[tp_col] == 'Persona jurídica'].groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_juridica')
                df = pd.merge(p_fisica, p_juridica, on=['Any', 'Codi_Barri'], how='outer').fillna(0)
            else:
                continue
                
        elif 'avg_surface' in key:
            # Agregar por barrio
            value_col = [c for c in df.columns if 'superficie' in c or 'valor' in c]
            if value_col:
                df = df.groupby(['Any', 'Codi_Barri'])[value_col[0]].mean().reset_index()
                df = df.rename(columns={value_col[0]: 'superficie_media_m2'})
            else:
                continue
                
        elif 'floors' in key:
            value_col = [c for c in df.columns if 'planta' in c or 'valor' in c]
            if value_col:
                df = df.groupby(['Any', 'Codi_Barri'])[value_col[0]].mean().reset_index()
                df = df.rename(columns={value_col[0]: 'num_plantas_avg'})
            else:
                continue
                
        elif 'year_const' in key:
            value_col = [c for c in df.columns if 'any' in c.lower() and c != 'Any']
            if not value_col:
                value_col = [c for c in df.columns if 'valor' in c]
            if value_col:
                # Calcular antigüedad (año actual - año construcción)
                current_year = 2024
                df['antiguedad'] = current_year - pd.to_numeric(df[value_col[0]], errors='coerce')
                df = df.groupby(['Any', 'Codi_Barri'])['antiguedad'].mean().reset_index()
                df = df.rename(columns={'antiguedad': 'antiguedad_media_bloque'})
            else:
                continue
                
        elif 'owner_nationality' in key:
            # Ejemplo: % extranjeros
            nac_col = 'nacionalitat' if 'nacionalitat' in df.columns else None
            if nac_col:
                extranjeros = df[df[nac_col].str.contains('Estrang', na=False, case=False)].groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_ext')
                total = df.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_total')
                df = pd.merge(extranjeros, total, on=['Any', 'Codi_Barri'], how='right').fillna(0)
                df['pct_propietarios_extranjeros'] = (df['num_ext'] / df['num_total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_propietarios_extranjeros']]
            else:
                continue
        else:
            continue
        
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
        if df is None or df.empty: 
            logger.info(f"Saltando {key}: vacío o None")
            continue
        
        logger.info(f"Procesando {key}: {len(df)} filas, columnas: {list(df.columns)[:5]}...")
        df = df.copy()
        
        # 1. Normalización agresiva
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Priorizar 'any' sobre 'data_referencia' si ambos existen
        rename_map = {
            "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
            "valor": "Valor"
        }
        # Renombrar columna de año (priorizar 'any')
        if 'any' in df.columns:
            rename_map["any"] = "Any"
        if 'data_referencia' in df.columns and 'Any' not in df.columns:
            rename_map["data_referencia"] = "Any"
        if 'año' in df.columns and 'Any' not in df.columns:
            rename_map["año"] = "Any"
        if 'anio' in df.columns and 'Any' not in df.columns:
            rename_map["anio"] = "Any"
            
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})
        
        # Eliminar columnas duplicadas si existen
        df = df.loc[:, ~df.columns.duplicated()]

        logger.info(f"  Después de normalización: {list(df.columns)[:8]}")
        
        # 2. Verificar que existen las columnas necesarias
        if 'Any' not in df.columns or 'Codi_Barri' not in df.columns:
            logger.warning(f"Columnas faltantes en {key}. Columnas: {list(df.columns)}")
            continue
            
        # 3. Asegurar Any y Codi_Barri son numéricos
        # Si Any contiene fechas (ej: '2024-01-01'), extraer el año
        if df['Any'].dtype == 'object':
            # Intentar extraer año de fecha
            df['Any'] = pd.to_datetime(df['Any'], errors='coerce').dt.year
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        # 4. Procesamiento específico y agregación INMEDIATA
        if 'crowding' in key:
            # Promedio de personas por hogar - usar columna Valor directamente
            if 'Valor' in df.columns:
                logger.info(f"  Antes de groupby: {len(df)} filas, NaN en Any: {df['Any'].isna().sum()}, NaN en Codi_Barri: {df['Codi_Barri'].isna().sum()}")
                # Agrupar por número de personas y calcular promedio ponderado
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].mean().reset_index()
                df = df.rename(columns={'Valor': 'promedio_personas_por_hogar'})
                logger.info(f"  Después de groupby: {len(df)} filas")
            else:
                logger.warning(f"No se encontró columna Valor en {key}")
                continue
                
        elif 'minors' in key:
            # Hogares con menores - sumar valores
            if 'Valor' in df.columns:
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                df = df.rename(columns={'Valor': 'num_hogares_con_menores'})
            else:
                logger.warning(f"No se encontró columna Valor en {key}")
                continue
                
        elif 'women' in key:
            # Presencia de mujeres - promedio
            if 'Valor' in df.columns:
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].mean().reset_index()
                df = df.rename(columns={'Valor': 'pct_presencia_mujeres'})
            else:
                logger.warning(f"No se encontró columna Valor en {key}")
                continue
                
        elif 'nationality' in key:
            nac_col = 'nacionalitat_domicili' if 'nacionalitat_domicili' in df.columns else ('nacionalitat' if 'nacionalitat' in df.columns else None)
            if nac_col:
                # Convertir a string para poder usar .str.contains
                df[nac_col] = df[nac_col].astype(str)
                extranjeros = df[df[nac_col].str.contains('Estrang', na=False, case=False)].groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_ext')
                total = df.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_total')
                df = pd.merge(extranjeros, total, on=['Any', 'Codi_Barri'], how='right').fillna(0)
                df['pct_hogares_nacionalidad_extranjera'] = (df['num_ext'] / df['num_total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_hogares_nacionalidad_extranjera']]
            else:
                logger.warning(f"No se encontró columna de nacionalidad en {key}")
                continue
        else:
            continue
        
        logger.info(f"  Después de procesar {key}: df tiene {len(df)} filas, columnas: {list(df.columns)}")
        
        if combined_df.empty: 
            combined_df = df
            logger.info(f"  combined_df inicializado con {len(combined_df)} filas de {key}")
        else: 
            logger.info(f"  Mergeando {key} ({len(df)} filas) con combined_df ({len(combined_df)} filas)")
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')
            logger.info(f"  Después del merge: combined_df tiene {len(combined_df)} filas")

    if combined_df.empty: 
        logger.warning("combined_df está vacío después de procesar todos los datasets")
        return pd.DataFrame()

    logger.info(f"combined_df antes de merge con dim_barrios: {len(combined_df)} filas, columnas: {list(combined_df.columns)}")
    logger.info(f"Primeras filas de combined_df:\n{combined_df.head()}")

    # Mapear barrio_id
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    logger.info(f"dim_barrios_clean: {len(dim_barrios_clean)} filas")
    logger.info(f"Valores únicos de Codi_Barri en combined_df: {sorted(combined_df['Codi_Barri'].dropna().unique())[:10]}")
    logger.info(f"Valores únicos de codi_barri_num en dim_barrios: {sorted(dim_barrios_clean['codi_barri_num'].dropna().unique())[:10]}")
    
    combined_df = pd.merge(
        combined_df, 
        dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
        left_on='Codi_Barri', 
        right_on='codi_barri_num', 
        how='inner'
    )
    
    logger.info(f"combined_df después de merge: {len(combined_df)} filas")
    
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
        
        # 1. Normalización agresiva
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {
            "any": "Any", "data_referencia": "Any", "año": "Any", "anio": "Any",
            "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
            "valor": "Valor"
        }
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})

        # 2. Asegurar Any y Codi_Barri son numéricos
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        # 3. Procesamiento específico
        target_col = None
        if 'intensity' in key:
            target_col = 'indice_intensidad_turistica'
            df = df.rename(columns={'Valor': target_col})
        elif 'hut' in key:
            target_col = 'num_establecimientos_turisticos'
            df = df.rename(columns={'Valor': target_col})
        else: continue
        
        # AGREGAR: Nivel barrio
        if 'indice' in target_col:
            df = df.groupby(['Any', 'Codi_Barri'])[target_col].mean().reset_index()
        else:
            df = df.groupby(['Any', 'Codi_Barri'])[target_col].sum().reset_index()
        
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
