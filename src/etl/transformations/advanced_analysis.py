from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

from .utils import cleaner, logger, _map_territorio_to_barrio_id

def prepare_fact_renta_avanzada(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Combina datasets de renta (Gini, P80/P20, Bruta) en fact_renta_avanzada.
    """
    combined_df = pd.DataFrame()
    
    for key, df in dfs.items():
        if df is None or df.empty:
            continue
            
        logger.info(f"Procesando componente de renta avanzada: {key}")
        df = df.copy()
        
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {
            "any": "Any", "data_referencia": "Any", "año": "Any", "anio": "Any",
            "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
            "valor": "Valor", "import_euros": "Valor",
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

        target_col = None
        if 'bruta' in key.lower() or 'gross' in key.lower():
            target_col = 'renta_bruta_llar'
        elif 'gini' in key.lower():
            target_col = 'indice_gini'
        elif 'p80' in key.lower():
            target_col = 'ratio_p80_p20'
            
        if not target_col or 'Valor' not in df.columns:
            continue

        df = df.rename(columns={'Valor': target_col})
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        df = df.groupby(['Any', 'Codi_Barri'])[target_col].mean().reset_index()
        
        if combined_df.empty:
            combined_df = df[['Any', 'Codi_Barri', target_col]].copy()
        else:
            df_to_merge = df[['Any', 'Codi_Barri', target_col]].copy()
            combined_df = pd.merge(combined_df, df_to_merge, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty:
        return pd.DataFrame()

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

def get_topographical_penalty(barrio_nombre: str, distrito_nombre: str) -> float:
    bn = str(barrio_nombre).lower()
    dn = str(distrito_nombre).lower()
    penalty = 0.0
    if 'nou barris' in dn: penalty += 0.4
    elif 'horta-guinardó' in dn: penalty += 0.35
    elif 'sarrià-sant gervasi' in dn: penalty += 0.25
    elif 'gràcia' in dn: penalty += 0.15
    if 'coll' in bn: penalty += 0.35
    elif 'vallbona' in bn or 'torre baró' in bn: penalty += 0.4
    elif 'carmel' in bn or 'teixonera' in bn: penalty += 0.3
    elif 'roquetes' in bn or 'trinitat nova' in bn: penalty += 0.25
    return min(penalty, 1.0)

def prepare_fact_catastro_avanzado(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    combined_df = pd.DataFrame()
    
    for key, df in dfs.items():
        if df is None or df.empty: continue
        logger.info(f"  Procesando {key}: {len(df)} filas")
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        
        rename_map = {
            "codi_barri": "Codi_Barri", "any": "Any", 
            "dim-00:temps": "Any", "data_referencia": "Any"
        }
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})
        
        if 'dim-01:territori (order)' in df.columns:
            df['Codi_Barri'] = df['dim-01:territori (order)']
        elif 'dim-01:territori' in df.columns and 'Codi_Barri' not in df.columns:
            df['Codi_Barri'] = df['dim-01:territori'].str.extract(r'^(\d+)').astype(float)
        
        if 'Any' in df.columns and df['Any'].dtype == 'object':
            df['Any'] = pd.to_datetime(df['Any'], errors='coerce').dt.year
            
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        # PROCESAMIENTO POR TIPO
        if 'owner_type' in key or 'tipus-propietari' in key:
            tipo_col = next((c for c in df.columns if 'tipus_propietari' in c or 'desc_tipus' in c), None)
            if tipo_col:
                fisica = df[df[tipo_col].str.contains('fÃ\xadsic|física|fisica', case=False, na=False)]
                juridica = df[df[tipo_col].str.contains('jurídic|juridica', case=False, na=False)]
                p_fisica = fisica.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_fisica')
                p_juridica = juridica.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_juridica')
                df = pd.merge(p_fisica, p_juridica, on=['Any', 'Codi_Barri'], how='outer').fillna(0)
            else: continue
            
        elif 'surface' in key or 'superficie' in key or 'locals-us-desti' in key:
            if 'concepte' in df.columns:
                df = df[df['concepte'].str.contains('superficie|superfície', case=False, na=False)].copy()
            sup_col = next((c for c in ['nombre', 'valor', 'value'] if c in df.columns), None)
            if sup_col:
                df[sup_col] = pd.to_numeric(df[sup_col], errors='coerce')
                df = df.groupby(['Any', 'Codi_Barri'])[sup_col].mean().reset_index()
                df = df.rename(columns={sup_col: 'superficie_media_m2'})
            else: continue
            
        elif 'year_const' in key or 'any-const' in key:
            year_col = next((c for c in df.columns if 'any_construccio' in c or 'construccio' in c), None)
            if year_col:
                def parse_year(val):
                    val_str = str(val)
                    if '<' in val_str: return 1900
                    if '-' in val_str:
                        parts = val_str.split('-')
                        try: return (int(parts[0]) + int(parts[1])) / 2
                        except: return np.nan
                    try: return float(val)
                    except: return np.nan
                df['year_numeric'] = df[year_col].apply(parse_year)
                df['antiguedad'] = 2024 - df['year_numeric']
                if 'nombre' in df.columns:
                    df['weighted'] = df['antiguedad'] * df['nombre']
                    grouped = df.groupby(['Any', 'Codi_Barri']).agg({'weighted': 'sum', 'nombre': 'sum'}).reset_index()
                    grouped['antiguedad_media_bloque'] = grouped['weighted'] / grouped['nombre']
                    df = grouped[['Any', 'Codi_Barri', 'antiguedad_media_bloque']].copy()
                else:
                    df = df.groupby(['Any', 'Codi_Barri'])['antiguedad'].mean().reset_index()
                    df = df.rename(columns={'antiguedad': 'antiguedad_media_bloque'})
            else: continue
            
        elif 'nationality' in key or 'nacionalitat' in key or 'locals-prop' in key:
            tipo_col = next((c for c in df.columns if 'nacionalitat' in c or 'tipus_propietari' in c or 'desc_tipus' in c), None)
            if tipo_col:
                total = df.groupby(['Any', 'Codi_Barri']).size().reset_index(name='total')
                ext = df[df[tipo_col].astype(str).str.contains('estrang|extranjera|extranjero', case=False, na=False)]
                ext_count = ext.groupby(['Any', 'Codi_Barri']).size().reset_index(name='extranjeros')
                df = pd.merge(total, ext_count, on=['Any', 'Codi_Barri'], how='left').fillna(0)
                df['pct_propietarios_extranjeros'] = (df['extranjeros'] / df['total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_propietarios_extranjeros']].copy()
            else: continue
        else: continue
        
        if combined_df.empty:
            combined_df = df.copy()
        else:
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')
    
    if combined_df.empty: return pd.DataFrame()
    
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id', 'barrio_nombre', 'distrito_nombre']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(
        combined_df,
        dim_barrios_clean[['codi_barri_num', 'barrio_id', 'barrio_nombre', 'distrito_nombre']],
        left_on='Codi_Barri',
        right_on='codi_barri_num',
        how='inner'
    )
    
    combined_df['indice_penalizacion_topografica'] = combined_df.apply(
        lambda x: get_topographical_penalty(x['barrio_nombre'], x['distrito_nombre']), axis=1
    )
    
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    cols = ['barrio_id', 'anio', 'num_propietarios_fisica', 'num_propietarios_juridica',
            'pct_propietarios_extranjeros', 'superficie_media_m2', 'num_plantas_avg',
            'antiguedad_media_bloque', 'indice_penalizacion_topografica', 'etl_loaded_at']
    return combined_df[[c for c in cols if c in combined_df.columns]].copy()

def prepare_fact_hogares_avanzado(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    combined_df = pd.DataFrame()
    for key, df in dfs.items():
        if df is None or df.empty: continue
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {"codi_barri": "Codi_Barri", "valor": "Valor"}
        if 'any' in df.columns: rename_map["any"] = "Any"
        elif 'data_referencia' in df.columns: rename_map["data_referencia"] = "Any"
        for col_old, col_new in rename_map.items():
            if col_old in df.columns: df = df.rename(columns={col_old: col_new})
        
        if 'Any' not in df.columns or 'Codi_Barri' not in df.columns: continue
        if df['Any'].dtype == 'object': df['Any'] = pd.to_datetime(df['Any'], errors='coerce').dt.year
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        if 'crowding' in key:
            if 'Valor' in df.columns:
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].mean().reset_index()
                df = df.rename(columns={'Valor': 'promedio_personas_por_hogar'})
            else: continue
        elif 'minors' in key:
            if 'Valor' in df.columns:
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].sum().reset_index()
                df = df.rename(columns={'Valor': 'num_hogares_con_menores'})
            else: continue
        elif 'women' in key:
            if 'Valor' in df.columns:
                df = df.groupby(['Any', 'Codi_Barri'])['Valor'].mean().reset_index()
                df = df.rename(columns={'Valor': 'pct_presencia_mujeres'})
            else: continue
        elif 'nationality' in key:
            nac_col = next((c for c in ['nacionalitat_domicili', 'nacionalitat'] if c in df.columns), None)
            if nac_col:
                ext = df[df[nac_col].astype(str).str.contains('Estrang', na=False, case=False)].groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_ext')
                total = df.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_total')
                df = pd.merge(ext, total, on=['Any', 'Codi_Barri'], how='right').fillna(0)
                df['pct_hogares_nacionalidad_extranjera'] = (df['num_ext'] / df['num_total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_hogares_nacionalidad_extranjera']].copy()
            else: continue
        else: continue
        
        if combined_df.empty: combined_df = df.copy()
        else: combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty: return pd.DataFrame()
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(combined_df, dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
                           left_on='Codi_Barri', right_on='codi_barri_num', how='inner')
    
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    cols = ['barrio_id', 'anio', 'promedio_personas_por_hogar', 'num_hogares_con_menores', 
            'pct_hogares_nacionalidad_extranjera', 'pct_presencia_mujeres', 'etl_loaded_at']
    return combined_df[[c for c in cols if c in combined_df.columns]].copy()

def prepare_fact_turismo_intensidad(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    combined_df = pd.DataFrame()
    for key, df in dfs.items():
        if df is None or df.empty: continue
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        rename_map = {"codi_barri": "Codi_Barri", "valor": "Valor"}
        if 'any' in df.columns: rename_map["any"] = "Any"
        elif 'data_referencia' in df.columns: rename_map["data_referencia"] = "Any"
        for col_old, col_new in rename_map.items():
            if col_old in df.columns: df = df.rename(columns={col_old: col_new})
        
        if 'Codi_Barri' not in df.columns:
            found_col = next((c for c in df.columns if ('codi' in c.lower() and 'barri' in c.lower()) or ('barrio' in c.lower() and 'id' in c.lower())), None)
            if found_col: df['Codi_Barri'] = df[found_col]
            else: continue

        if df['Codi_Barri'].dtype == 'object':
            df['Codi_Barri'] = df['Codi_Barri'].astype(str).str.strip().str.lstrip('0')
            df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        if 'Any' not in df.columns:
            if 'n_expedient' in df.columns: df['Any'] = df['n_expedient'].str.extract(r'(\d{4})', expand=False)
            else: df['Any'] = reference_time.year
        
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')

        target_col = None
        if 'intensity' in key:
            target_col = 'indice_intensidad_turistica'
            if 'Valor' in df.columns: df = df.rename(columns={'Valor': target_col})
            else:
                num_cols = [c for c in df.select_dtypes(include=['number']).columns if c not in ['Any', 'Codi_Barri']]
                if num_cols: df[target_col] = df[num_cols[0]]
                else: continue
        elif 'hut' in key:
            target_col = 'num_establecimientos_turisticos'
            df[target_col] = 1
        else: continue
        
        df = df[df['Any'].notna() & df['Codi_Barri'].notna()].copy()
        if df.empty: continue
        
        if 'indice' in target_col: df = df.groupby(['Any', 'Codi_Barri'])[target_col].mean().reset_index()
        else: df = df.groupby(['Any', 'Codi_Barri'])[target_col].sum().reset_index()
        
        if combined_df.empty: combined_df = df.copy()
        else: combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')

    if combined_df.empty: return pd.DataFrame()
    combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
    dim_barrios_clean = dim_barrios[['codi_barri', 'barrio_id']].copy()
    dim_barrios_clean['codi_barri_num'] = pd.to_numeric(dim_barrios_clean['codi_barri'], errors='coerce')
    
    combined_df = pd.merge(combined_df, dim_barrios_clean[['codi_barri_num', 'barrio_id']], 
                           left_on='Codi_Barri', right_on='codi_barri_num', how='inner')
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
def prepare_fact_presion_turistica(
    airbnb_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
    source: str = "insideairbnb"
) -> pd.DataFrame:
    """
    Procesa datos de InsideAirbnb para calcular presión turística.
    """
    if airbnb_df.empty:
        return pd.DataFrame()

    df = airbnb_df.copy()
    
    # InsideAirbnb suele traer coordenadas. Si no trae barrio, mapeamos por coordenadas or neighbourhood
    if 'neighbourhood_cleansed' in df.columns:
        df['barrio_id'] = df['neighbourhood_cleansed'].apply(
            lambda x: _map_territorio_to_barrio_id(str(x), "Barri", dim_barrios) if pd.notna(x) else None
        )
    
    df = df.dropna(subset=['barrio_id'])
    df['barrio_id'] = df['barrio_id'].astype(int)

    # Agregación
    df['is_entire_home'] = df['room_type'].str.contains('Entire', case=False, na=False)
    
    # Limpieza de precios (InsideAirbnb trae '$100.00')
    if 'price' in df.columns and df['price'].dtype == 'object':
        df['price'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)

    agg = df.groupby('barrio_id').agg(
        num_listings_airbnb=('id', 'count'),
        pct_entire_home=('is_entire_home', 'mean'),
        precio_noche_promedio=('price', 'mean') if 'price' in df.columns else ('id', lambda x: None),
        tasa_ocupacion=('availability_365', lambda x: 1 - (x.mean() / 365)) if 'availability_365' in df.columns else ('id', lambda x: None),
        num_reviews_mes=('reviews_per_month', 'sum') if 'reviews_per_month' in df.columns else ('id', 'count')
    ).reset_index()

    agg['anio'] = reference_time.year
    agg['mes'] = reference_time.month
    agg['etl_loaded_at'] = reference_time.isoformat()
    agg['pct_entire_home'] *= 100

    return agg

__all__ = [
    "prepare_fact_renta_avanzada",
    "prepare_fact_catastro_avanzado",
    "prepare_fact_hogares_avanzado",
    "prepare_fact_turismo_intensidad",
    "prepare_fact_presion_turistica"
]
