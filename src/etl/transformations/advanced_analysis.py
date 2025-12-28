from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

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

def get_topographical_penalty(barrio_nombre: str, distrito_nombre: str) -> float:
    """
    Calculates a topographical penalty index (0 to 1) based on:
    - Steep slopes (Pendiente)
    - Accessibility constraints (e.g., extremely deep metro stations like in El Coll)
    - Urban fragmentation.
    """
    bn = str(barrio_nombre).lower()
    dn = str(distrito_nombre).lower()
    
    penalty = 0.0
    
    # 1. Base District-level penalty (general orography)
    if 'nou barris' in dn:
        penalty += 0.4
    elif 'horta-guinardó' in dn:
        penalty += 0.35
    elif 'sarrià-sant gervasi' in dn:
        penalty += 0.25
    elif 'gràcia' in dn:
        penalty += 0.15
    
    # 2. Neighborhood-specific boosts (The "El Coll" & surroundings factor)
    # El Coll: Extreme slopes + Deepest Metro station in BCN
    if 'coll' in bn:
        penalty += 0.35
    # Vallbona & Torre Baró: Isolation + Steep orography
    elif 'vallbona' in bn or 'torre baró' in bn:
        penalty += 0.4
    # Carmel & Teixonera: Complex terrain
    elif 'carmel' in bn or 'teixonera' in bn:
        penalty += 0.3
    # Roquetes & Trinitat Nova: High mountain neighborhoods in Nou Barris
    elif 'roquetes' in bn or 'trinitat nova' in bn:
        penalty += 0.25
        
    return min(penalty, 1.0)

def prepare_fact_catastro_avanzado(
    dfs: Dict[str, pd.DataFrame],
    dim_barrios: pd.DataFrame,
    reference_time: datetime
) -> pd.DataFrame:
    """
    Combina datasets de catastro en fact_catastro_avanzado.
    
    Datasets esperados:
    - cadastre_owner_type: Tipos de propietarios (física/jurídica)
    - cadastre_avg_surface: Superficie media
    - cadastre_year_const: Año de construcción
    - cadastre_owner_nationality: Nacionalidad de propietarios
    """
    combined_df = pd.DataFrame()
    
    for key, df in dfs.items():
        if df is None or df.empty:
            logger.info(f"  Saltando {key}: vacío")
            continue
        
        logger.info(f"  Procesando {key}: {len(df)} filas")
        df = df.copy()
        
        # 1. Normalización de columnas
        df.columns = [c.strip().lower() for c in df.columns]
        
        # 2. Renombrar columnas estándar (incluyendo Portaldades)
        rename_map = {
            "codi_barri": "Codi_Barri",
            "any": "Any",
            "dim-00:temps": "Any",
            "data_referencia": "Any"
        }
        for col_old, col_new in rename_map.items():
            if col_old in df.columns:
                df = df.rename(columns={col_old: col_new})
        
        # Especial para territori y temps en Portaldades
        if 'dim-01:territori (order)' in df.columns:
            df['Codi_Barri'] = df['dim-01:territori (order)']
        elif 'dim-01:territori' in df.columns and 'Codi_Barri' not in df.columns:
            df['Codi_Barri'] = df['dim-01:territori'].str.extract(r'^(\d+)').astype(float)
        
        # 3. Asegurar tipos numéricos
        if 'Any' in df.columns and df['Any'].dtype == 'object':
            # Intentar extraer año de fecha (ISO format como 2018-01-01T00:00:00Z)
            df['Any'] = pd.to_datetime(df['Any'], errors='coerce').dt.year
            
        df['Any'] = pd.to_numeric(df['Any'], errors='coerce')
        df['Codi_Barri'] = pd.to_numeric(df['Codi_Barri'], errors='coerce')
        
        # 4. Procesamiento específico por tipo de dataset
        if 'owner_type' in key or 'tipus-propietari' in key or 'carrecs' in key:
            # Tipos de propietarios (física vs jurídica)
            logger.info(f"    Tipo: Propietarios")
            
            # Buscar columna de tipo de propietario
            tipo_col = None
            for col in df.columns:
                if 'tipus_propietari' in col or 'desc_tipus' in col:
                    tipo_col = col
                    break
            
            if tipo_col:
                # Contar por tipo
                fisica = df[df[tipo_col].str.contains('fÃ\xadsic|física|fisica', case=False, na=False)]
                juridica = df[df[tipo_col].str.contains('jurídic|juridica', case=False, na=False)]
                
                p_fisica = fisica.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_fisica')
                p_juridica = juridica.groupby(['Any', 'Codi_Barri']).size().reset_index(name='num_propietarios_juridica')
                
                df = pd.merge(p_fisica, p_juridica, on=['Any', 'Codi_Barri'], how='outer').fillna(0)
                logger.info(f"    Resultado: {len(df)} filas")
            else:
                logger.warning(f"    No se encontró columna de tipo de propietario")
                continue
        
        elif 'avg_surface' in key or 'superficie' in key:
            # Superficie media
            logger.info(f"    Tipo: Superficie media")
            
            # Buscar columna de superficie
            sup_col = None
            for col in df.columns:
                if 'sup' in col and 'm2' in col:
                    sup_col = col
                    break
            
            if sup_col:
                # Convertir a numérico (puede tener separadores de miles)
                df[sup_col] = pd.to_numeric(df[sup_col], errors='coerce')
                df = df.groupby(['Any', 'Codi_Barri'])[sup_col].mean().reset_index()
                df = df.rename(columns={sup_col: 'superficie_media_m2'})
                logger.info(f"    Resultado: {len(df)} filas, media: {df['superficie_media_m2'].mean():.1f} m²")
            else:
                logger.warning(f"    No se encontró columna de superficie")
                continue
        
        elif 'year_const' in key or 'any-const' in key or 'any_construccio' in key:
            # Año de construcción -> antigüedad
            logger.info(f"    Tipo: Año de construcción")
            
            # Buscar columna de año de construcción
            year_col = None
            for col in df.columns:
                if 'any_construccio' in col or 'construccio' in col:
                    year_col = col
                    break
            
            if year_col:
                # Convertir rangos de años a valores numéricos
                def parse_year(val):
                    if pd.isna(val):
                        return np.nan
                    val_str = str(val)
                    if '<' in val_str:
                        return 1900  # Antes de 1901
                    elif '-' in val_str:
                        # Tomar el punto medio del rango
                        parts = val_str.split('-')
                        try:
                            return (int(parts[0]) + int(parts[1])) / 2
                        except:
                            return np.nan
                    else:
                        try:
                            return float(val)
                        except:
                            return np.nan
                
                df['year_numeric'] = df[year_col].apply(parse_year)
                current_year = 2024
                df['antiguedad'] = current_year - df['year_numeric']
                
                # Agregar por barrio (promedio ponderado por número de viviendas si existe)
                if 'nombre' in df.columns:
                    # Promedio ponderado
                    df['weighted'] = df['antiguedad'] * df['nombre']
                    grouped = df.groupby(['Any', 'Codi_Barri']).agg({
                        'weighted': 'sum',
                        'nombre': 'sum'
                    }).reset_index()
                    grouped['antiguedad_media_bloque'] = grouped['weighted'] / grouped['nombre']
                    df = grouped[['Any', 'Codi_Barri', 'antiguedad_media_bloque']]
                else:
                    df = df.groupby(['Any', 'Codi_Barri'])['antiguedad'].mean().reset_index()
                    df = df.rename(columns={'antiguedad': 'antiguedad_media_bloque'})
                
                logger.info(f"    Resultado: {len(df)} filas, antigüedad media: {df['antiguedad_media_bloque'].mean():.1f} años")
            else:
                logger.warning(f"    No se encontró columna de año de construcción")
                continue
        
        elif 'owner_nationality' in key or 'nacionalitat' in key or 'locals-prop' in key:
            # Nacionalidad de propietarios
            logger.info(f"    Tipo: Nacionalidad propietarios")
            
            # Buscar columna de tipo de propietario
            tipo_col = None
            for col in df.columns:
                if 'tipus_propietari' in col or 'desc_tipus' in col:
                    tipo_col = col
                    break
            
            if tipo_col:
                # Calcular % extranjeros
                total = df.groupby(['Any', 'Codi_Barri']).size().reset_index(name='total')
                extranjeros = df[df[tipo_col].str.contains('estrang|extranjera', case=False, na=False)]
                ext_count = extranjeros.groupby(['Any', 'Codi_Barri']).size().reset_index(name='extranjeros')
                
                df = pd.merge(total, ext_count, on=['Any', 'Codi_Barri'], how='left').fillna(0)
                df['pct_propietarios_extranjeros'] = (df['extranjeros'] / df['total']) * 100
                df = df[['Any', 'Codi_Barri', 'pct_propietarios_extranjeros']]
                logger.info(f"    Resultado: {len(df)} filas, % extranjeros: {df['pct_propietarios_extranjeros'].mean():.1f}%")
            else:
                logger.warning(f"    No se encontró columna de nacionalidad")
                continue
        
        elif 'built' in key or 'soil' in key or 'surface_total' in key or 'surface_soil' in key:
            # Superficie construida o de suelo (Portaldades proxy para plantas)
            logger.info(f"    Tipo: Proxy de Plantas (Superficie)")
            
            # Buscar columna de valor
            val_col = 'valor' if 'valor' in df.columns else (
                'value' if 'value' in df.columns else (
                'Valor' if 'Valor' in df.columns else None))
            
            if val_col:
                df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
                # Fix: Check for 'built' or 'constru' in key
                metric = 'built_surface' if 'built' in key or 'constru' in key else 'soil_surface'
                df = df.groupby(['Any', 'Codi_Barri'])[val_col].sum().reset_index()
                df = df.rename(columns={val_col: metric})
                logger.info(f"    Resultado {metric}: {len(df)} filas")
            else:
                logger.warning(f"    No se encontró columna de valor en {key}")
                continue
        
        elif 'floors' in key or 'plantes' in key:
            # Dataset oficial de plantas (o similar directo)
            logger.info(f"    Tipo: Plantas (Directo)")
            # Intentar encontrar una columna que represente el promedio o valor
            val_col = None
            for col in ['valor', 'value', 'nombre', 'count']:
                if col in df.columns:
                    val_col = col
                    break
            
            if val_col:
                # Agregación simple si es un dataset de conteo (aproximación)
                df = df.groupby(['Any', 'Codi_Barri'])[val_col].mean().reset_index()
                df = df.rename(columns={val_col: 'num_plantas_avg'})
                logger.info(f"    Resultado num_plantas_avg: {len(df)} filas")
            else:
                logger.warning(f"    No se pudo procesar dataset de plantas")
                continue
        
        else:
            logger.warning(f"    Tipo de dataset no reconocido: {key}")
            continue
        
        # 5. Mergear con combined_df
        if combined_df.empty:
            combined_df = df
            logger.info(f"    combined_df inicializado: {len(combined_df)} filas")
        else:
            logger.info(f"    Mergeando con combined_df ({len(combined_df)} filas)")
            combined_df['Any'] = pd.to_numeric(combined_df['Any'], errors='coerce')
            combined_df['Codi_Barri'] = pd.to_numeric(combined_df['Codi_Barri'], errors='coerce')
            combined_df = pd.merge(combined_df, df, on=['Any', 'Codi_Barri'], how='outer')
            logger.info(f"    Después del merge: {len(combined_df)} filas")
    
    if combined_df.empty:
        logger.warning("combined_df está vacío después de procesar todos los datasets")
        return pd.DataFrame()
    
    logger.info(f"Antes de mapear barrio_id: {len(combined_df)} filas")
    logger.info(f"Columnas disponibles: {list(combined_df.columns)}")
    
    # 6. Map barrio_id and calculate topographical penalty
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
    
    # Apply topographical penalty
    combined_df['indice_penalizacion_topografica'] = combined_df.apply(
        lambda x: get_topographical_penalty(x['barrio_nombre'], x['distrito_nombre']),
        axis=1
    )
    
    logger.info(f"Después de mapear barrio_id y calcular penalización topographical: {len(combined_df)} filas")
    
    # 7. Preparar columnas finales
    combined_df = combined_df.rename(columns={'Any': 'anio'})
    combined_df['etl_loaded_at'] = reference_time.isoformat()
    
    # Calculate num_plantas_avg proxy if built/soil columns are available
    if 'built_surface' in combined_df.columns and 'soil_surface' in combined_df.columns:
        # Avoid division by zero
        combined_df['num_plantas_avg_proxy'] = combined_df['built_surface'] / combined_df['soil_surface'].replace(0, np.nan)
        # If num_plantas_avg doesn't exist yet, use the proxy
        if 'num_plantas_avg' not in combined_df.columns:
            combined_df['num_plantas_avg'] = combined_df['num_plantas_avg_proxy']
        else:
            # Fill NaNs in official with proxy if available
            combined_df['num_plantas_avg'] = combined_df['num_plantas_avg'].fillna(combined_df['num_plantas_avg_proxy'])
        logger.info(f"Calculado num_plantas_avg (proxy/fusion): mean={combined_df['num_plantas_avg'].mean():.2f}")

    cols = ['barrio_id', 'anio', 'num_propietarios_fisica', 'num_propietarios_juridica',
            'pct_propietarios_extranjeros', 'superficie_media_m2', 'num_plantas_avg',
            'antiguedad_media_bloque', 'indice_penalizacion_topografica', 'etl_loaded_at']
    
    result = combined_df[[c for c in cols if c in combined_df.columns]]
    logger.info(f"Resultado final: {len(result)} filas, columnas: {list(result.columns)}")
    
    return result

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
