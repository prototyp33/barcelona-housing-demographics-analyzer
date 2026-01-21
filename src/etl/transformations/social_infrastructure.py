"""Transformaciones para infraestructura social (Educación, Seguridad, Vivienda Pública)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from .utils import _map_territorio_to_barrio_id, logger, cleaner

def prepare_fact_educacion(
    education_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
    source: str = "opendata_bcn_educacion"
) -> pd.DataFrame:
    """
    Procesa centros educativos y los agrega por barrio.
    """
    if education_df.empty:
        return pd.DataFrame()

    df = education_df.copy()
    
    # Mapeo de barrios
    if 'addresses_neighborhood_id' in df.columns:
        df['barrio_id'] = pd.to_numeric(df['addresses_neighborhood_id'], errors='coerce')
    else:
        # Fallback a nombre
        df['barrio_id'] = df['addresses_neighborhood_name'].apply(
            lambda x: _map_territorio_to_barrio_id(str(x), "Barri", dim_barrios) if pd.notna(x) else None
        )

    df = df.dropna(subset=['barrio_id'])
    df['barrio_id'] = df['barrio_id'].astype(int)

    # Identificar tipos de centros (basado en 'secondary_filters_name')
    # Nota: El esquema real puede variar, usamos una clasificación simplificada
    def classify_center(name: str) -> str:
        name = str(name).lower()
        if 'infantil' in name or 'bressol' in name: return 'infantil'
        if 'primària' in name: return 'primaria'
        if 'secundària' in name or 'eso' in name: return 'secundaria'
        if 'professional' in name or 'fp' in name: return 'fp'
        if 'universitat' in name or 'facultat' in name: return 'universidad'
        return 'otro'

    df['tipo_centro'] = df['secondary_filters_name'].apply(classify_center)

    # Agregar por barrio
    # Como los equipamientos son estáticos para el año de extracción, usamos reference_time.year
    anio = reference_time.year
    
    aggregated = df.groupby('barrio_id').agg(
        num_centros_infantil=('tipo_centro', lambda x: (x == 'infantil').sum()),
        num_centros_primaria=('tipo_centro', lambda x: (x == 'primaria').sum()),
        num_centros_secundaria=('tipo_centro', lambda x: (x == 'secundaria').sum()),
        num_centros_fp=('tipo_centro', lambda x: (x == 'fp').sum()),
        num_centros_universidad=('tipo_centro', lambda x: (x == 'universidad').sum()),
        total_centros_educativos=('register_id', 'count')
    ).reset_index()

    aggregated['anio'] = anio
    aggregated['etl_loaded_at'] = reference_time.isoformat()
    aggregated['source'] = source

    return aggregated

def prepare_fact_seguridad(
    security_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
    source: str = "mossos_criminalidad"
) -> pd.DataFrame:
    """
    Procesa datos de criminalidad de los Mossos d'Esquadra.
    Mapea ABPs (Áreas Básicas Policiales) a Distritos.
    """
    if security_df.empty:
        return pd.DataFrame()

    df = security_df.copy()
    
    # Mapeo de ABP a Distrito (Simplificado para Barcelona Ciudad)
    # Las ABPs en BCN suelen coincidir con distritos
    abp_to_district = {
        'ABP Ciutat Vella': 'Ciutat Vella',
        'ABP Eixample': 'Eixample',
        'ABP Sants-Montjuïc': 'Sants-Montjuïc',
        'ABP Les Corts': 'Les Corts',
        'ABP Sarrià-Sant Gervasi': 'Sarrià-Sant Gervasi',
        'ABP Gràcia': 'Gràcia',
        'ABP Horta-Guinardó': 'Horta-Guinardó',
        'ABP Nou Barris': 'Nou Barris',
        'ABP Sant Andreu': 'Sant Andreu',
        'ABP Sant Martí': 'Sant Martí'
    }

    df['distrito_nombre'] = df['rea_b_sica_policial_abp'].map(abp_to_district)
    df = df.dropna(subset=['distrito_nombre'])

    # Clasificar delitos según esquema fact_seguridad
    def categorize_crime(titulo: str) -> str:
        t = str(titulo).lower()
        if 'patrimoni' in t or 'socioeconòmic' in t: return 'patrimonio'
        if 'persona' in t or 'llibertat' in t or 'integritat' in t: return 'personal'
        return 'otros'

    df['categoria'] = df['t_tol_codi_penal'].apply(categorize_crime)

    # Agregar por Distrito y Trimestre
    # Mossos dan mes, convertimos a trimestre
    df['trimestre'] = df['mes'].apply(lambda m: (int(m) - 1) // 3 + 1)
    
    agg = df.groupby(['distrito_nombre', 'any', 'trimestre']).agg(
        delitos_patrimonio=('coneguts', lambda x: x[df.loc[x.index, 'categoria'] == 'patrimonio'].sum()),
        delitos_seguridad_personal=('coneguts', lambda x: x[df.loc[x.index, 'categoria'] == 'personal'].sum())
    ).reset_index()

    # Distribuir datos de distrito a barrios (proporcional a población si es posible, 
    # o simplemente replicar con flag de granularidad)
    # Por simplicidad y consistencia con el resto del proyecto, replicamos a nivel barrio.
    results = []
    for _, row in agg.iterrows():
        barrios_in_district = dim_barrios[dim_barrios['distrito_nombre'] == row['distrito_nombre']]['barrio_id'].tolist()
        for b_id in barrios_in_district:
            results.append({
                'barrio_id': b_id,
                'anio': int(row['any']),
                'trimestre': int(row['trimestre']),
                'delitos_patrimonio': int(row['delitos_patrimonio']),
                'delitos_seguridad_personal': int(row['delitos_seguridad_personal']),
                'etl_loaded_at': reference_time.isoformat()
            })

    return pd.DataFrame(results)

def prepare_fact_vivienda_publica(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Consolida datos de vivienda pública y tutelada.
    """
    results = pd.DataFrame()
    
    # 1. Viviendas tuteladas (OpenDataBCN)
    if 'tutelats' in dfs and not dfs['tutelats'].empty:
        df_tut = dfs['tutelats'].copy()
        df_tut['barrio_id'] = pd.to_numeric(df_tut['addresses_neighborhood_id'], errors='coerce')
        df_tut = df_tut.dropna(subset=['barrio_id'])
        
        agg_tut = df_tut.groupby('barrio_id').size().reset_index(name='viviendas_proteccion_oficial')
        agg_tut['anio'] = reference_time.year
        results = agg_tut

    # 2. Idescat / INCASOL (más detallado)
    if 'idescat' in dfs and not dfs['idescat'].empty:
        df_id = dfs['idescat'].copy()
        # Mapeo y procesamiento específico de Idescat aquí...
        # Por ahora mantenemos el esquema base
        pass

    if results.empty:
        return pd.DataFrame()

    results['etl_loaded_at'] = reference_time.isoformat()
    results['source'] = 'consolidated_housing'
    
    return results
