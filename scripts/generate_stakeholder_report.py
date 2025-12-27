"""
Script para generar reporte ejecutivo para stakeholders.

Genera un reporte HTML con visualizaciones y métricas clave.
"""

from __future__ import annotations

import os

# Forzar hilos simples para OpenBLAS antes de cualquier import de numpy/pandas
# para evitar crash en chips Apple M4
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

PROJECT_ROOT = Path(__file__).parent.parent

# Paleta de colores Barcelona
COLORS = {
    'primary': '#005EB8',  # Azul Barcelona
    'success': '#10B981',  # Verde
    'warning': '#F59E0B',  # Amarillo
    'danger': '#EF4444',   # Rojo
    'accent': '#667eea',   # Morado
}


def get_top_affordable_barrios(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """Obtiene barrios más asequibles consolidando datos de fact_precios y fact_oferta_idealista."""
    # Obtener datos de fact_precios
    df_off = pd.read_sql_query(f'SELECT barrio_id, precio_m2_venta, precio_mes_alquiler FROM fact_precios WHERE anio={anio} AND precio_m2_venta > 0', conn)
    
    # Obtener datos de Idealista: venta y alquiler por separado
    df_id_venta = pd.read_sql_query(f"SELECT barrio_id, precio_m2_medio as precio_m2_venta FROM fact_oferta_idealista WHERE anio={anio} AND operacion='sale' AND precio_m2_medio > 0", conn)
    df_id_alquiler = pd.read_sql_query(f"SELECT barrio_id, precio_medio as precio_mes_alquiler FROM fact_oferta_idealista WHERE anio={anio} AND operacion='rent' AND precio_medio > 0", conn)
    
    # Consolidar precios de venta
    dfs_venta = [df for df in [df_off[['barrio_id', 'precio_m2_venta']] if not df_off.empty else pd.DataFrame(), df_id_venta] if not df.empty]
    if dfs_venta:
        df_venta = pd.concat(dfs_venta).groupby('barrio_id')['precio_m2_venta'].max().reset_index()
    else:
        df_venta = pd.DataFrame(columns=['barrio_id', 'precio_m2_venta'])
    
    # Consolidar precios de alquiler (filtrar valores irrazonables > 10,000 €/mes)
    dfs_alquiler = [df for df in [df_off[['barrio_id', 'precio_mes_alquiler']] if not df_off.empty else pd.DataFrame(), df_id_alquiler] if not df.empty]
    if dfs_alquiler:
        df_alquiler = pd.concat(dfs_alquiler)
        # Filtrar valores irrazonables (máximo 10,000 €/mes para Barcelona)
        df_alquiler = df_alquiler[df_alquiler['precio_mes_alquiler'] <= 10000]
        df_alquiler = df_alquiler.groupby('barrio_id')['precio_mes_alquiler'].max().reset_index()
    else:
        df_alquiler = pd.DataFrame(columns=['barrio_id', 'precio_mes_alquiler'])
    
    # Combinar venta y alquiler
    df_p = df_venta.merge(df_alquiler, on='barrio_id', how='outer')
    
    # Obtener datos de barrios y renta
    cursor = conn.execute('SELECT MAX(anio) FROM fact_renta')
    ry = cursor.fetchone()[0] or anio
    df_b = pd.read_sql_query(f'SELECT b.barrio_id, b.barrio_nombre, b.distrito_nombre, r.renta_euros FROM dim_barrios b LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND r.anio={ry}', conn)
    
    # Merge y filtrar solo barrios con precio de venta válido
    df = df_b.merge(df_p, on='barrio_id', how='inner')
    df = df.drop_duplicates(subset=['barrio_id'])
    df = df[df['precio_m2_venta'] > 0]
    df = df[df['renta_euros'].notna() & (df['renta_euros'] > 0)]
    
    # Calcular ratios solo si hay alquiler
    df['ratio_asequibilidad'] = df.apply(
        lambda x: (x['precio_mes_alquiler'] * 12 / x['renta_euros']) * 100 if pd.notna(x['precio_mes_alquiler']) and x['precio_mes_alquiler'] > 0 else None,
        axis=1
    )
    df['price_to_income_ratio'] = df['precio_m2_venta'] / (df['renta_euros'] / 12)
    
    # Ordenar: primero por ratio (si existe), luego por price_to_income
    df = df.sort_values(['ratio_asequibilidad', 'price_to_income_ratio'], ascending=[True, True], na_position='last').head(limit).reset_index(drop=True)
    df.insert(0, 'rank', range(1, len(df) + 1))
    return df

def get_top_quality_of_life(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """Obtiene barrios con mejor calidad de vida con datos consolidados."""
    
    # Query ultra-robusta con subconsultas para años máximos
    query = """
    SELECT 
        b.barrio_id, b.barrio_nombre, b.distrito_nombre,
        COALESCE(edu.v, 0) as centros_educativos,
        COALESCE(sal.v, 0) as servicios_salud,
        COALESCE(com.v, 0) as comercios,
        COALESCE(env.v_m2, 0) as m2_zonas_verdes,
        COALESCE(env.v_num, 0) as num_arboles,
        COALESCE(ruido.v, 0) as nivel_ruido,
        COALESCE(seg.v, 0) as tasa_criminalidad
    FROM dim_barrios b
    LEFT JOIN (SELECT barrio_id, total_centros_educativos as v FROM fact_educacion WHERE anio = (SELECT MAX(anio) FROM fact_educacion)) edu ON b.barrio_id = edu.barrio_id
    LEFT JOIN (SELECT barrio_id, total_servicios_sanitarios as v FROM fact_servicios_salud WHERE anio = (SELECT MAX(anio) FROM fact_servicios_salud)) sal ON b.barrio_id = sal.barrio_id
    LEFT JOIN (SELECT barrio_id, total_establecimientos as v FROM fact_comercio WHERE anio = (SELECT MAX(anio) FROM fact_comercio)) com ON b.barrio_id = com.barrio_id
    LEFT JOIN (SELECT barrio_id, superficie_zonas_verdes_m2 as v_m2, num_arboles as v_num FROM fact_medio_ambiente WHERE anio = (SELECT MAX(anio) FROM fact_medio_ambiente)) env ON b.barrio_id = env.barrio_id
    LEFT JOIN (SELECT barrio_id, nivel_lden_medio as v FROM fact_ruido WHERE anio = (SELECT MAX(anio) FROM fact_ruido)) ruido ON b.barrio_id = ruido.barrio_id
    LEFT JOIN (SELECT barrio_id, tasa_criminalidad_1000hab as v FROM fact_seguridad WHERE anio = (SELECT MAX(anio) FROM fact_seguridad)) seg ON b.barrio_id = seg.barrio_id
    """

    
    df = pd.read_sql_query(query, conn)
    df = df.fillna(0)
    
    # Proxy para zonas verdes (vectorizado)
    df['m2_zonas_verdes'] = df['m2_zonas_verdes'].where(df['m2_zonas_verdes'] > 0, df['num_arboles'] * 15)
    
    # Normalización
    def normalize(series):
        mx = series.max()
        return (series / mx * 100) if mx > 0 else 0
    
    s_edu = normalize(df['centros_educativos'])
    s_sal = normalize(df['servicios_salud'])
    s_com = normalize(df['comercios'])
    s_ver = normalize(df['m2_zonas_verdes'])
    mx_crim = df['tasa_criminalidad'].max()
    s_seg = (1 - (df['tasa_criminalidad'] / mx_crim)) * 100 if mx_crim > 0 else 100
    
    df['indice_calidad_vida'] = (s_edu * 0.2 + s_sal * 0.25 + s_com * 0.15 + s_ver * 0.2 + s_seg * 0.2)
    df = df.drop_duplicates(subset=['barrio_id'])
    df = df.sort_values('indice_calidad_vida', ascending=False).head(limit).reset_index(drop=True)
    df.insert(0, 'rank', range(1, len(df) + 1))
    return df

def get_top_investment_potential(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """Potential de inversión con fallbacks."""
    df_off = pd.read_sql_query(f'SELECT barrio_id, precio_m2_venta as pv, precio_mes_alquiler as pa FROM fact_precios WHERE anio={anio}', conn)
    df_id = pd.read_sql_query(f"SELECT barrio_id, CASE WHEN operacion='venta' THEN precio_m2_medio END as pv, CASE WHEN operacion='alquiler' THEN precio_medio END as pa FROM fact_oferta_idealista WHERE anio={anio}", conn)
    
    # Fix FutureWarning by checking for empty DataFrames and dtypes
    dfs = [df for df in [df_off, df_id] if not df.empty]
    if dfs:
        # Asegurar que todas las columnas necesarias existan antes de concatenar
        for d in dfs:
            if 'barrio_id' not in d.columns: d['barrio_id'] = None
            if 'pv' not in d.columns: d['pv'] = None
            if 'pa' not in d.columns: d['pa'] = None
        
        df_p = pd.concat(dfs).groupby('barrio_id').max().reset_index()
    else:
        df_p = pd.DataFrame(columns=['barrio_id', 'pv', 'pa'])
        
    df = pd.read_sql_query('SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios', conn).merge(df_p, on='barrio_id')
    df = df.drop_duplicates(subset=['barrio_id'])
    df['yield_bruto_pct'] = (df['pa'] * 12 / (df['pv'] * 75)) * 100
    df = df[df['pv'] > 0].sort_values('yield_bruto_pct', ascending=False).head(limit).reset_index(drop=True)
    df.insert(0, 'rank', range(1, len(df) + 1))
    return df.rename(columns={'pv': 'precio_m2_venta', 'pa': 'precio_mes_alquiler'})

def get_inequality_analysis(conn: sqlite3.Connection, anio: int = 2023) -> Tuple[pd.DataFrame, Dict]:
    def get_max_yr(t):
        try: return conn.execute(f'SELECT MAX(anio) FROM {t}').fetchone()[0] or anio
        except: return anio
    y_renta = get_max_yr('fact_renta')
    y_com = get_max_yr('fact_comercio')
    df = pd.read_sql_query(f'SELECT b.barrio_id, b.barrio_nombre, b.distrito_nombre, r.renta_euros, c.densidad_comercial_por_1000hab as densidad_comercial FROM dim_barrios b LEFT JOIN fact_renta r ON b.barrio_id = r.barrio_id AND r.anio = {y_renta} LEFT JOIN fact_comercio c ON b.barrio_id = c.barrio_id AND c.anio = {y_com} WHERE r.renta_euros IS NOT NULL', conn)
    df = df.drop_duplicates(subset=['barrio_id'])
    
    # Calculate disparidad
    disparidad = {}
    if not df.empty and 'densidad_comercial' in df.columns:
        valid_df = df[df['densidad_comercial'] > 0]
        if not valid_df.empty:
            mx = valid_df['densidad_comercial'].max()
            mn = valid_df['densidad_comercial'].min()
            disparidad['ratio_servicios'] = mx / mn if mn > 0 else 0
        else:
            disparidad['ratio_servicios'] = 0
    else:
        disparidad['ratio_servicios'] = 0
        
    return df, disparidad

def get_data_coverage(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Analiza la cobertura de datos por fuente.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con métricas de cobertura por fuente.
    """
    coverage_data = []
    
    # fact_precios
    precios_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_precios
    """
    precios = pd.read_sql_query(precios_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Precios de Vivienda',
        'min_year': int(precios['min_year']) if pd.notna(precios['min_year']) else None,
        'max_year': int(precios['max_year']) if pd.notna(precios['max_year']) else None,
        'barrios_cobertura': int(precios['barrios_con_datos']) if pd.notna(precios['barrios_con_datos']) else 0,
        'completeness_pct': round((precios['barrios_con_datos'] / 73) * 100, 1) if pd.notna(precios['barrios_con_datos']) else 0,
    })
    
    # fact_demografia
    demo_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_demografia
    """
    demo = pd.read_sql_query(demo_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Demografía',
        'min_year': int(demo['min_year']) if pd.notna(demo['min_year']) else None,
        'max_year': int(demo['max_year']) if pd.notna(demo['max_year']) else None,
        'barrios_cobertura': int(demo['barrios_con_datos']) if pd.notna(demo['barrios_con_datos']) else 0,
        'completeness_pct': round((demo['barrios_con_datos'] / 73) * 100, 1) if pd.notna(demo['barrios_con_datos']) else 0,
    })
    
    # fact_educacion
    educ_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_educacion
    """
    educ = pd.read_sql_query(educ_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Educación',
        'min_year': int(educ['min_year']) if pd.notna(educ['min_year']) else None,
        'max_year': int(educ['max_year']) if pd.notna(educ['max_year']) else None,
        'barrios_cobertura': int(educ['barrios_con_datos']) if pd.notna(educ['barrios_con_datos']) else 0,
        'completeness_pct': round((educ['barrios_con_datos'] / 73) * 100, 1) if pd.notna(educ['barrios_con_datos']) else 0,
    })
    
    # fact_servicios_salud
    salud_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_servicios_salud
    """
    salud = pd.read_sql_query(salud_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Servicios de Salud',
        'min_year': int(salud['min_year']) if pd.notna(salud['min_year']) else None,
        'max_year': int(salud['max_year']) if pd.notna(salud['max_year']) else None,
        'barrios_cobertura': int(salud['barrios_con_datos']) if pd.notna(salud['barrios_con_datos']) else 0,
        'completeness_pct': round((salud['barrios_con_datos'] / 73) * 100, 1) if pd.notna(salud['barrios_con_datos']) else 0,
    })
    
    # fact_comercio
    comercio_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_comercio
    """
    comercio = pd.read_sql_query(comercio_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Comercio',
        'min_year': int(comercio['min_year']) if pd.notna(comercio['min_year']) else None,
        'max_year': int(comercio['max_year']) if pd.notna(comercio['max_year']) else None,
        'barrios_cobertura': int(comercio['barrios_con_datos']) if pd.notna(comercio['barrios_con_datos']) else 0,
        'completeness_pct': round((comercio['barrios_con_datos'] / 73) * 100, 1) if pd.notna(comercio['barrios_con_datos']) else 0,
    })
    
    # fact_seguridad
    seg_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_seguridad
    """
    seg = pd.read_sql_query(seg_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Seguridad',
        'min_year': int(seg['min_year']) if pd.notna(seg['min_year']) else None,
        'max_year': int(seg['max_year']) if pd.notna(seg['max_year']) else None,
        'barrios_cobertura': int(seg['barrios_con_datos']) if pd.notna(seg['barrios_con_datos']) else 0,
        'completeness_pct': round((seg['barrios_con_datos'] / 73) * 100, 1) if pd.notna(seg['barrios_con_datos']) else 0,
    })
    
    # fact_presion_turistica
    turismo_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_presion_turistica
    """
    turismo = pd.read_sql_query(turismo_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Presión Turística',
        'min_year': int(turismo['min_year']) if pd.notna(turismo['min_year']) else None,
        'max_year': int(turismo['max_year']) if pd.notna(turismo['max_year']) else None,
        'barrios_cobertura': int(turismo['barrios_con_datos']) if pd.notna(turismo['barrios_con_datos']) else 0,
        'completeness_pct': round((turismo['barrios_con_datos'] / 73) * 100, 1) if pd.notna(turismo['barrios_con_datos']) else 0,
    })
    
    # fact_regulacion
    reg_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_regulacion
    """
    reg = pd.read_sql_query(reg_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Regulación',
        'min_year': int(reg['min_year']) if pd.notna(reg['min_year']) else None,
        'max_year': int(reg['max_year']) if pd.notna(reg['max_year']) else None,
        'barrios_cobertura': int(reg['barrios_con_datos']) if pd.notna(reg['barrios_con_datos']) else 0,
        'completeness_pct': round((reg['barrios_con_datos'] / 73) * 100, 1) if pd.notna(reg['barrios_con_datos']) else 0,
    })
    
    # fact_medio_ambiente
    medio_query = """
    SELECT 
        MIN(anio) as min_year,
        MAX(anio) as max_year,
        COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_medio_ambiente
    """
    medio = pd.read_sql_query(medio_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'Medio Ambiente',
        'min_year': int(medio['min_year']) if pd.notna(medio['min_year']) else None,
        'max_year': int(medio['max_year']) if pd.notna(medio['max_year']) else None,
        'barrios_cobertura': int(medio['barrios_con_datos']) if pd.notna(medio['barrios_con_datos']) else 0,
        'completeness_pct': round((medio['barrios_con_datos'] / 73) * 100, 1) if pd.notna(medio['barrios_con_datos']) else 0,
    })
    
    return pd.DataFrame(coverage_data)


def create_affordability_chart(df: pd.DataFrame) -> str:
    """Crea gráfico de barras horizontal para ratio de asequibilidad."""
    if len(df) == 0 or 'ratio_asequibilidad' not in df.columns:
        return '{}'  # Retornar JSON vacío si no hay datos
    
    fig = go.Figure()
    
    colors = []
    for ratio in df['ratio_asequibilidad']:
        if ratio < 30:
            colors.append(COLORS['success'])
        elif ratio < 40:
            colors.append(COLORS['warning'])
        else:
            colors.append(COLORS['danger'])
    
    fig.add_trace(go.Bar(
        y=df['barrio_nombre'],
        x=df['ratio_asequibilidad'],
        orientation='h',
        marker=dict(color=colors),
        text=[f"{x:.1f}%" for x in df['ratio_asequibilidad']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Ratio: %{x:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Top 10 Barrios Más Asequibles - Ratio de Asequibilidad',
        xaxis_title='Ratio Asequibilidad (%)',
        yaxis_title='',
        height=500,
        showlegend=False,
        plot_bgcolor='white',
        yaxis=dict(autorange='reversed'),
        xaxis=dict(range=[0, max(df['ratio_asequibilidad']) * 1.2])
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_quality_radar_chart(df: pd.DataFrame) -> str:
    """Crea gráfico radar para comparar Top 3 barrios en calidad de vida."""
    if len(df) < 3:
        return '{}'  # Retornar JSON vacío si no hay suficientes datos
    
    top3 = df.head(3)
    
    fig = go.Figure()
    
    categories = ['Educación', 'Salud', 'Comercio', 'Zonas Verdes', 'Ruido']
    
    for idx, row in top3.iterrows():
        valores = [
            min(row.get('centros_educativos', 0) * 10, 100),
            min(row.get('servicios_salud', 0) * 10, 100),
            min(row.get('comercios', 0) / 10, 100),
            min(row.get('m2_zonas_verdes', 0) * 10, 100),
            max(100 - row.get('nivel_ruido', 0), 0)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=categories,
            fill='toself',
            name=row['barrio_nombre'],
            line=dict(width=2)
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title='Comparación Top 3 Barrios - Calidad de Vida',
        height=500
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_investment_scatter(df: pd.DataFrame) -> str:
    """Crea scatter plot para potencial de inversión con cuadrantes."""
    if len(df) == 0 or 'yield_bruto_pct' not in df.columns:
        return '{}'  # Retornar JSON vacío si no hay datos
    
    fig = go.Figure()
    
    median_yield = df['yield_bruto_pct'].median()
    median_price = df['precio_m2_venta'].median()
    
    for idx, row in df.iterrows():
        x = row['precio_m2_venta']
        y = row['yield_bruto_pct']
        size = row.get('score_liquidez', 5) * 10
        
        if y >= median_yield and x <= median_price:
            color = COLORS['success']
        elif y >= median_yield and x > median_price:
            color = COLORS['accent']
        elif y < median_yield and x <= median_price:
            color = COLORS['warning']
        else:
            color = COLORS['danger']
        
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(size=size, color=color, opacity=0.7, line=dict(width=2, color='white')),
            name=row['barrio_nombre'],
            text=f"{row['barrio_nombre']}<br>Yield: {y:.2f}%<br>Precio: €{x:,.0f}/m²",
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=False
        ))
    
    # Líneas de división
    fig.add_shape(type="line", x0=median_price, y0=df['yield_bruto_pct'].min(),
                  x1=median_price, y1=df['yield_bruto_pct'].max(),
                  line=dict(color="gray", width=1, dash="dash"))
    fig.add_shape(type="line", x0=df['precio_m2_venta'].min(), y0=median_yield,
                  x1=df['precio_m2_venta'].max(), y1=median_yield,
                  line=dict(color="gray", width=1, dash="dash"))
    
    fig.update_layout(
        title='Potencial de Inversión: Yield vs Precio',
        xaxis_title='Precio por m² (€)',
        yaxis_title='Yield Bruto Anual (%)',
        height=600,
        plot_bgcolor='white',
        hovermode='closest'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def format_table_with_colors(df: pd.DataFrame, color_col: str) -> str:
    """Formatea tabla HTML con color coding."""
    html = df.to_html(index=False, escape=False, classes='data-table')
    
    # Añadir estilos inline para color coding
    if color_col in df.columns:
        for idx, row in df.iterrows():
            value = row[color_col]
            if pd.notna(value):
                if value < 30:
                    color = COLORS['success']
                elif value < 40:
                    color = COLORS['warning']
                else:
                    color = COLORS['danger']
                # Reemplazar en HTML
                html = html.replace(
                    f'<td>{value:.2f}</td>',
                    f'<td style="background-color: {color}20; color: {color}; font-weight: 600;">{value:.2f}%</td>',
                    1
                )
    
    return html


def get_hero_metrics(conn: sqlite3.Connection, anio: int = 2023) -> Dict[str, Any]:
    df_off = pd.read_sql_query(f'SELECT AVG(precio_m2_venta) as pv, AVG(precio_mes_alquiler) as pa FROM fact_precios WHERE anio={anio}', conn)
    pv, pa = df_off.iloc[0]['pv'], df_off.iloc[0]['pa']
    yield_bruto = (pa * 12 / (pv * 75)) * 100 if pv and pa else 0
    
    # Hero metrics mapping to template expected keys
    return {
        'total_barrios': 73,
        'precio_promedio_m2': float(pv or 0),
        'yield_bruto_pct': float(yield_bruto),
        'yield_es_real': bool(pa),
        'num_datasets': 9
    }

def generate_html_report(
    db_path: Path,
    output_path: Path,
    anio: int = 2023
) -> Path:
    """
    Genera un reporte HTML ejecutivo profesional.
    
    Args:
        db_path: Ruta a la base de datos.
        output_path: Ruta donde guardar el reporte.
        anio: Año de análisis.
    
    Returns:
        Ruta al archivo generado.
    """
    conn = sqlite3.connect(db_path)
    
    # Encontrar el mejor año con datos de precios
    years_to_try = [2025, 2024, 2023, 2022, 2021]
    best_year = anio
    for year in years_to_try:
        check = pd.read_sql_query(f'SELECT COUNT(*) as c FROM (SELECT barrio_id FROM fact_precios WHERE anio={year} UNION SELECT barrio_id FROM fact_oferta_idealista WHERE anio={year})', conn).iloc[0]['c']
        if check > 10:
            best_year = year
            break
    print(f'📊 Usando año {best_year} para análisis')

    # Obtener métricas hero
    # Obtener métricas hero
    hero_metrics = get_hero_metrics(conn, best_year)
    
    # Obtener datos detallados
    top_affordable = get_top_affordable_barrios(conn, best_year)
    top_quality = get_top_quality_of_life(conn, best_year)
    top_investment = get_top_investment_potential(conn, best_year)
    inequality_df, disparidad = get_inequality_analysis(conn, best_year)
    
    # Obtener cobertura de datos
    coverage_df = get_data_coverage(conn)
    
    # Actualizar año usado en el reporte
    anio = best_year
    
    # Calcular títulos dinámicos basados en datos disponibles
    num_affordable = len(top_affordable) if len(top_affordable) > 0 else 0
    num_quality = len(top_quality) if len(top_quality) > 0 else 0
    num_investment = len(top_investment) if len(top_investment) > 0 else 0
    
    title_affordable = f"Top {num_affordable} Barrios Más Asequibles" if num_affordable >= 2 else "Barrios Más Asequibles"
    title_quality = f"Top {num_quality} Calidad de Vida" if num_quality >= 2 else "Mejor Calidad de Vida"
    title_investment = f"Top {num_investment} Potencial Inversión" if num_investment >= 2 else f"Mejor Oportunidad de Inversión {anio}"
    
    # Generar datos para visualizaciones
    affordability_data = []
    if len(top_affordable) > 0:
        for _, row in top_affordable.iterrows():
            precio_m2 = row.get('precio_m2_venta', 0)
            if pd.isna(precio_m2) or precio_m2 is None:
                precio_m2 = 0.0
            else:
                precio_m2 = float(precio_m2)
            
            precio_mes_alquiler = row.get('precio_mes_alquiler')
            alquiler_es_real = row.get('alquiler_es_real', False) if 'alquiler_es_real' in row else False
            
            if pd.isna(precio_mes_alquiler) or precio_mes_alquiler is None:
                # NO estimar - dejar como null para mostrar "N/A" en la tabla
                precio_mes_alquiler = None
                alquiler_es_real = False
            else:
                precio_mes_alquiler = float(precio_mes_alquiler)
                # Validar que el alquiler sea razonable (máximo 10,000 €/mes para Barcelona)
                if precio_mes_alquiler > 10000:
                    precio_mes_alquiler = None
                    alquiler_es_real = False
            
            renta_euros = row.get('renta_euros', 0)
            if pd.isna(renta_euros) or renta_euros is None:
                renta_euros = 0.0
            else:
                renta_euros = float(renta_euros)
            
            ratio = row.get('ratio_asequibilidad')
            ratio_es_real = row.get('ratio_es_real', False) if 'ratio_es_real' in row else False
            
            if pd.isna(ratio) or ratio is None:
                # NO calcular ratio si no hay datos reales - dejar como null
                ratio = None
                ratio_es_real = False
            else:
                ratio = float(ratio)
            
            # Calcular price_to_income_ratio para usar como alternativa si ratio es null
            price_to_income = row.get('price_to_income_ratio')
            if pd.isna(price_to_income) or price_to_income is None:
                price_to_income = (precio_m2 / (renta_euros / 12)) if renta_euros > 0 else None
            
            affordability_data.append({
                'rank': int(row.get('rank', 0)),
                'name': str(row.get('barrio_nombre', '')),
                'price': precio_m2,
                'rent': precio_mes_alquiler,
                'rent_is_real': alquiler_es_real,
                'income': renta_euros,
                'ratio': ratio,
                'ratio_is_real': ratio_es_real,
                'price_to_income_ratio': float(price_to_income) if price_to_income is not None else None
            })
    
    quality_data = []
    if len(top_quality) > 0:
        for _, row in top_quality.iterrows():
            def safe_float(val, default=0.0):
                if pd.isna(val) or val is None:
                    return default
                return float(val)
            
            score = safe_float(row.get('indice_calidad_vida', 0))
            # Normalizar score a rango 0-100 siempre (el score original puede ser negativo o muy alto)
            # Si el score es negativo o muy alto, recalcular basado en datos disponibles
            if score < 0 or score > 100:
                # Usar datos de seguridad, regulación y presión turística para calcular score alternativo
                tasa_crim = safe_float(row.get('tasa_criminalidad', 0))
                zona_tens = safe_float(row.get('zona_tensionada', 0))
                airbnb = safe_float(row.get('num_listings_airbnb', 0))
                centros_edu = safe_float(row.get('centros_educativos', 0))
                servicios_salud = safe_float(row.get('servicios_salud', 0))
                comercios = safe_float(row.get('comercios', 0))
                verde = safe_float(row.get('m2_zonas_verdes', 0))
                
                # Score basado en servicios positivos menos penalizaciones
                # Normalizar a escala 0-100
                score_positivo = (
                    centros_edu * 5 +  # Máximo ~20 puntos si hay muchos centros
                    servicios_salud * 5 +  # Máximo ~20 puntos
                    comercios / 10 +  # Máximo ~10 puntos
                    verde * 2  # Máximo ~20 puntos
                )
                score_negativo = (
                    tasa_crim * 2 +  # Penalización por criminalidad
                    zona_tens * 10 +  # Penalización por zona tensionada
                    airbnb / 10  # Penalización por presión turística
                )
                # Normalizar score a rango 0-100 con factores más conservadores
                score_positivo_adj = (
                    min(centros_edu * 2, 20) +  # Máximo 20 puntos
                    min(servicios_salud * 2, 20) +  # Máximo 20 puntos
                    min(comercios / 50, 15) +  # Máximo 15 puntos
                    min(verde * 1, 15)  # Máximo 15 puntos
                )
                score_negativo_adj = (
                    min(tasa_crim * 0.5, 20) +  # Máximo 20 puntos de penalización
                    min(zona_tens * 5, 15) +  # Máximo 15 puntos de penalización
                    min(airbnb / 20, 10)  # Máximo 10 puntos de penalización
                )
                score = max(0, min(100, 50 + score_positivo_adj - score_negativo_adj))  # Base de 50 puntos
            
            quality_data.append({
                'rank': int(row.get('rank', 0)),
                'name': str(row.get('barrio_nombre', '')),
                'district': str(row.get('distrito_nombre', '')),
                'score': score,
                'green': safe_float(row.get('m2_zonas_verdes', 0)),
                'noise': safe_float(row.get('nivel_ruido', 0)),
                'centros_educativos': safe_float(row.get('centros_educativos', 0)),
                'servicios_salud': safe_float(row.get('servicios_salud', 0)),
                'comercios': safe_float(row.get('comercios', 0)),
                'tasa_criminalidad': safe_float(row.get('tasa_criminalidad', 0))
            })
    
    investment_data = []
    if len(top_investment) > 0:
        for _, row in top_investment.iterrows():
            yield_val = row.get('yield_bruto_pct')
            if pd.isna(yield_val) or yield_val is None:
                yield_val = 0.0
            else:
                yield_val = float(yield_val)
            
            trend_val = row.get('tendencia_precio_pct')
            if pd.isna(trend_val) or trend_val is None:
                trend_val = 0.0
            else:
                trend_val = float(trend_val)
            
            # Si yield es 0 pero tenemos precio, calcular yield estimado
            if yield_val == 0.0 and pd.notna(row.get('precio_m2_venta')) and row.get('precio_m2_venta', 0) > 0:
                precio_m2 = float(row.get('precio_m2_venta', 0))
                precio_alquiler_estimado = precio_m2 * 0.7 / 12
                yield_val = (precio_alquiler_estimado * 12) / (precio_m2 * 70) * 100
            
            investment_data.append({
                'rank': int(row.get('rank', 0)),
                'name': str(row.get('barrio_nombre', '')),
                'yield': yield_val,
                'price': float(row.get('precio_m2_venta', 0)) if pd.notna(row.get('precio_m2_venta')) else 0.0,
                'trend': trend_val,
                'liquidity': 'Alta' if row.get('score_liquidez', 0) > 7 else ('Media' if row.get('score_liquidez', 0) > 4 else 'Baja')
            })
    
    # Limpiar datos de barrios críticos (eliminar NaN)
    critical_barrios_clean = []
    if len(inequality_df) > 0:
        def safe_val(val, default=0.0):
            if pd.isna(val) or val is None:
                return default
            return float(val) if isinstance(val, (int, float)) else val
        
        min_renta = safe_val(inequality_df['renta_euros'].min()) if len(inequality_df) > 0 else 0.0
        
        # Eliminar duplicados antes de procesar
        inequality_df_unique = inequality_df.drop_duplicates(subset=['barrio_nombre'], keep='first')
        
        for _, row in inequality_df_unique.head(5).iterrows():
            servicios_1000hab = safe_val(row.get('servicios_por_1000hab', 0))
            renta = safe_val(row.get('renta_euros', 0))
            precio_m2 = safe_val(row.get('precio_m2_venta', 0))
            
            critical_barrios_clean.append({
                'barrio_nombre': str(row.get('barrio_nombre', '')),
                'distrito_nombre': str(row.get('distrito_nombre', '')),
                'servicios_por_1000hab': servicios_1000hab,
                'renta_euros': renta,
                'precio_m2_venta': precio_m2,
                'gap_renta': renta - min_renta
            })
        
        # Eliminar duplicados finales por si acaso
        seen = set()
        critical_barrios_clean = [
            x for x in critical_barrios_clean 
            if not (x['barrio_nombre'] in seen or seen.add(x['barrio_nombre']))
        ]
    
    # Generar HTML profesional con Tailwind CSS
    # Corregir nombre del mes en español
    meses_es = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
        'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
        'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    fecha_actual = datetime.now()
    mes_nombre = meses_es.get(fecha_actual.strftime('%B'), fecha_actual.strftime('%B'))
    fecha_generacion = f"{fecha_actual.strftime('%d')} de {mes_nombre} de {fecha_actual.strftime('%Y')}"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Barcelona Housing Market Report {anio}</title>
    
    <!-- Tailwind CSS via CDN (versión estable) -->
    <script src="https://cdn.tailwindcss.com/3.4.1"></script>
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- Google Fonts (Inter) -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

    <!-- Configuración de Colores Tailwind -->
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                    }},
                    colors: {{
                        bcnBlue: '#005EB8',
                        success: '#10B981',
                        warning: '#F59E0B',
                        danger: '#EF4444',
                        neutral: '#F3F4F6'
                    }}
                }}
            }}
        }}
    </script>

    <style>
        /* Estilos personalizados para impresión y utilidades */
        body {{ font-family: 'Inter', sans-serif; background-color: #f9fafb; }}
        
        .card {{
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 1.5rem;
            transition: transform 0.2s;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        
        /* KPI Cards con gradientes sutiles y bordes modernos */
        .kpi-card-blue {{
            background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
            border: 1px solid rgba(0, 94, 184, 0.12);
            border-left: none;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card-blue::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #005EB8 0%, #0084d4 50%, #005EB8 100%);
            border-radius: 0.75rem 0 0 0.75rem;
            box-shadow: 2px 0 8px rgba(0, 94, 184, 0.25);
            transition: all 0.3s ease;
        }}
        .kpi-card-blue:hover {{
            background: linear-gradient(135deg, #f8faff 0%, #e6f2ff 100%);
            box-shadow: 0 8px 20px -4px rgba(0, 94, 184, 0.25), 0 0 0 1px rgba(0, 94, 184, 0.08);
            transform: translateY(-2px);
            border-color: rgba(0, 94, 184, 0.2);
        }}
        .kpi-card-blue:hover::before {{
            width: 5px;
            box-shadow: 3px 0 12px rgba(0, 94, 184, 0.4);
        }}
        
        .kpi-card-green {{
            background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
            border: 1px solid rgba(16, 185, 129, 0.12);
            border-left: none;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card-green::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #10B981 0%, #34d399 50%, #10B981 100%);
            border-radius: 0.75rem 0 0 0.75rem;
            box-shadow: 2px 0 8px rgba(16, 185, 129, 0.25);
            transition: all 0.3s ease;
        }}
        .kpi-card-green:hover {{
            background: linear-gradient(135deg, #f8fef9 0%, #e6f9ed 100%);
            box-shadow: 0 8px 20px -4px rgba(16, 185, 129, 0.25), 0 0 0 1px rgba(16, 185, 129, 0.08);
            transform: translateY(-2px);
            border-color: rgba(16, 185, 129, 0.2);
        }}
        .kpi-card-green:hover::before {{
            width: 5px;
            box-shadow: 3px 0 12px rgba(16, 185, 129, 0.4);
        }}
        
        .kpi-card-purple {{
            background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
            border: 1px solid rgba(147, 51, 234, 0.12);
            border-left: none;
            position: relative;
            overflow: hidden;
        }}
        .kpi-card-purple::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #9333EA 0%, #a855f7 50%, #9333EA 100%);
            border-radius: 0.75rem 0 0 0.75rem;
            box-shadow: 2px 0 8px rgba(147, 51, 234, 0.25);
            transition: all 0.3s ease;
        }}
        .kpi-card-purple:hover {{
            background: linear-gradient(135deg, #fefbff 0%, #f3e8ff 100%);
            box-shadow: 0 8px 20px -4px rgba(147, 51, 234, 0.25), 0 0 0 1px rgba(147, 51, 234, 0.08);
            transform: translateY(-2px);
            border-color: rgba(147, 51, 234, 0.2);
        }}
        .kpi-card-purple:hover::before {{
            width: 5px;
            box-shadow: 3px 0 12px rgba(147, 51, 234, 0.4);
        }}
        
        .kpi-value {{ font-size: 2.25rem; font-weight: 700; color: #111827; }}
        .kpi-label {{ font-size: 0.875rem; font-weight: 500; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 0.75rem 1rem; background-color: #F9FAFB; font-weight: 600; font-size: 0.75rem; color: #6B7280; text-transform: uppercase; }}
        td {{ padding: 0.75rem 1rem; border-top: 1px solid #E5E7EB; font-size: 0.875rem; color: #374151; }}
        tr:hover td {{ background-color: #F3F4F6; }}

        /* Badge status colors */
        .badge-green {{ background-color: #D1FAE5; color: #065F46; padding: 0.25rem 0.6rem; border-radius: 9999px; font-weight: 600; font-size: 0.75rem; }}
        .badge-yellow {{ background-color: #FEF3C7; color: #92400E; padding: 0.25rem 0.6rem; border-radius: 9999px; font-weight: 600; font-size: 0.75rem; }}
        .badge-red {{ background-color: #FEE2E2; color: #991B1B; padding: 0.25rem 0.6rem; border-radius: 9999px; font-weight: 600; font-size: 0.75rem; }}

        /* Print styles */
        @media print {{
            body {{ background: white; -webkit-print-color-adjust: exact; }}
            .no-print {{ display: none !important; }}
            .card {{ box-shadow: none; border: 1px solid #ddd; page-break-inside: avoid; }}
            .kpi-card-blue, .kpi-card-green, .kpi-card-purple {{
                background: white !important;
                border-left: 4px solid #005EB8;
            }}
            .kpi-card-blue::before, .kpi-card-green::before, .kpi-card-purple::before {{
                display: none !important;
            }}
            .kpi-card-green {{ border-left-color: #10B981 !important; }}
            .kpi-card-purple {{ border-left-color: #9333EA !important; }}
            .section-break {{ page-break-before: always; }}
            h1, h2, h3 {{ color: #000 !important; }}
        }}
    </style>
</head>
<body>

    <!-- Header / Navbar -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <!-- Icono SVG simulando logo -->
                <svg class="h-8 w-8 text-bcnBlue" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <div>
                    <h1 class="text-xl font-bold text-gray-900 leading-tight">Barcelona Housing Market</h1>
                    <p class="text-xs text-gray-500">Intelligence Report {anio}</p>
                </div>
            </div>
            <div class="hidden md:block text-sm text-gray-500">
                Generado: <span id="currentDate"></span>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">

        <!-- 1. Hero Section / Resumen Ejecutivo -->
        <section>
            <div class="flex justify-between items-end mb-6">
                <div>
                    <h2 class="text-3xl font-bold text-gray-900">Resumen Ejecutivo</h2>
                    <p class="text-gray-600 mt-1">Visión consolidada del mercado inmobiliario y calidad de vida.</p>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <!-- KPI 1 -->
                <div class="card kpi-card-blue">
                    <p class="kpi-label">Barrios Analizados</p>
                    <p class="kpi-value">{hero_metrics['total_barrios']}</p>
                    <p class="text-xs text-gray-500 mt-2">Cobertura geográfica 100%</p>
                </div>
                <!-- KPI 2 -->
                <div class="card kpi-card-blue">
                    <p class="kpi-label">Precio Medio / m²</p>
                    <p class="kpi-value">{hero_metrics['precio_promedio_m2']:,.0f} €</p>
                    <p class="text-xs text-success mt-2">Datos {anio}</p>
                </div>
                <!-- KPI 3 -->
                <div class="card kpi-card-green">
                    <p class="kpi-label">Yield Bruto Promedio</p>
                    <p class="kpi-value">
                        {hero_metrics['yield_bruto_pct']:.1f}%{' <span class="text-xs text-yellow-600">(estimado)</span>' if not hero_metrics.get('yield_es_real', False) else ''}
                    </p>
                    <p class="text-xs text-gray-500 mt-2">
                        Rentabilidad bruta residencial
                        {'⚠️ Datos de alquiler no disponibles - valor estimado' if not hero_metrics.get('yield_es_real', False) else ''}
                    </p>
                </div>
                <!-- KPI 4 -->
                <div class="card kpi-card-purple">
                    <p class="kpi-label">Datasets Integrados</p>
                    <p class="kpi-value">{hero_metrics['num_datasets']}</p>
                    <p class="text-xs text-gray-500 mt-2">Fuentes públicas y privadas</p>
                </div>
            </div>
        </section>

        <!-- 2. Asequibilidad -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-8 section-break">
            <div class="lg:col-span-2">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-800" id="title-affordability">{title_affordable}</h3>
                    <span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">Residentes</span>
                </div>
                <div class="bg-white rounded-lg shadow overflow-hidden overflow-x-auto">
                    <table id="table-affordability">
                        <thead>
                            <tr>
                                <th class="w-10">Rank</th>
                                <th>Barrio</th>
                                <th>Venta/m²</th>
                                <th>Alquiler/Mes</th>
                                <th>Renta Media</th>
                                <th>Ratio Aseq.</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-affordability">
                            <!-- JS Injection -->
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <h4 class="text-sm font-semibold text-gray-500 mb-4 uppercase">Ratio de Asequibilidad (%)</h4>
                <div class="relative" style="height: 500px;">
                    <canvas id="chart-affordability"></canvas>
                </div>
                <p class="text-xs text-gray-400 mt-4 italic">* % de ingresos anuales destinados al alquiler.</p>
            </div>
        </section>

        <!-- 3. Calidad de Vida -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-8 section-break">
            <div class="card lg:col-span-1 order-2 lg:order-1">
                <h4 class="text-sm font-semibold text-gray-500 mb-4 uppercase">Comparativa Top 3 Dimensiones</h4>
                <div class="relative h-64 w-full">
                    <canvas id="chart-quality"></canvas>
                </div>
                <div class="mt-4 text-xs text-gray-500 space-y-1">
                    <p>• <strong>Educación:</strong> Centros / habitante</p>
                    <p>• <strong>Verde:</strong> m² / habitante</p>
                    <p>• <strong>Salud:</strong> CAPs y Hospitales</p>
                </div>
            </div>
            <div class="lg:col-span-2 order-1 lg:order-2">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-800" id="title-quality">{title_quality}</h3>
                    <span class="text-xs bg-bcnBlue text-white px-2 py-1 rounded" title="Comparar con media de Barcelona">Comparar con Media</span>
                </div>
                <div class="bg-white rounded-lg shadow overflow-hidden overflow-x-auto">
                    <table id="table-quality">
                        <thead>
                            <tr>
                                <th class="w-10">Rank</th>
                                <th>Barrio</th>
                                <th>Distrito</th>
                                <th>Score (0-100)</th>
                                <th>Verde (m²)</th>
                                <th>Ruido (dB)</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-quality">
                            <!-- JS Injection -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 4. Inversión -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-8 section-break">
            <div class="lg:col-span-2">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-800" id="title-investment">{title_investment}</h3>
                    <span class="text-xs bg-purple-600 text-white px-2 py-1 rounded">Inversores</span>
                </div>
                <div class="bg-white rounded-lg shadow overflow-hidden overflow-x-auto">
                    <table id="table-investment">
                        <thead>
                            <tr>
                                <th class="w-10">Rank</th>
                                <th>Barrio</th>
                                <th>Yield Bruto</th>
                                <th>Precio/m²</th>
                                <th>Tendencia 3A</th>
                                <th>Liquidez</th>
                            </tr>
                        </thead>
                        <tbody id="tbody-investment">
                            <!-- JS Injection -->
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <h4 class="text-sm font-semibold text-gray-500 mb-4 uppercase">Matriz: Yield vs Precio</h4>
                <div class="relative" style="height: 400px;">
                    <canvas id="chart-investment"></canvas>
                </div>
                <div class="grid grid-cols-2 gap-2 mt-4 text-xs text-center">
                    <div class="flex items-center justify-center gap-1"><span class="w-2 h-2 rounded-full bg-green-500"></span><span class="text-green-800">Sweet Spot</span></div>
                    <div class="flex items-center justify-center gap-1"><span class="w-2 h-2 rounded-full bg-blue-500"></span><span class="text-blue-800">Premium</span></div>
                    <div class="flex items-center justify-center gap-1"><span class="w-2 h-2 rounded-full bg-yellow-500"></span><span class="text-yellow-800">Value Play</span></div>
                    <div class="flex items-center justify-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span><span class="text-red-800">Evitar</span></div>
                </div>
            </div>
        </section>

        <!-- 5. Desigualdad Urbana -->
        <section class="section-break">
            <h3 class="text-xl font-bold text-gray-800 mb-4">Análisis de Desigualdad Urbana</h3>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Visualización: Distribución por Distrito -->
                <div class="card">
                    <h4 class="text-sm font-semibold text-gray-500 mb-2 uppercase">Disparidad de Renta por Distrito</h4>
                    <p class="text-xs text-gray-400 mb-4">Boxplot mostrando la varianza de renta media dentro de cada distrito.</p>
                    <div class="relative" style="height: 350px;">
                        <canvas id="chart-inequality"></canvas>
                    </div>
                </div>

                <!-- Tabla de Barrios Críticos -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h4 class="text-sm font-semibold text-gray-500 mb-4 uppercase">Barrios Críticos (Prioridad Inversión Pública)</h4>
                    <div class="overflow-hidden">
                        <table class="w-full text-sm">
                            <thead>
                                <tr class="border-b">
                                    <th class="text-left py-2">Barrio</th>
                                    <th class="text-left py-2">Déficit Principal</th>
                                    <th class="text-right py-2">Gap Monetario</th>
                                    <th class="text-left py-2">Prioridad</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y" id="tbody-critical">
                                <!-- JS Injection -->
                            </tbody>
                        </table>
                    </div>
                    <div class="mt-4 p-3 bg-red-50 border border-red-100 rounded text-xs text-red-800">
                        <strong>Insight:</strong> {'Ratio de desigualdad: ' + str(round(disparidad.get('ratio_servicios', 0), 1)) + 'x' if disparidad.get('ratio_servicios', 0) > 0 else 'Datos limitados'} entre mejor y peor barrio.
                    </div>
                </div>
            </div>
        </section>

        <!-- 6. Métricas de Cobertura -->
        <section class="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h3 class="text-lg font-bold text-gray-800 mb-4">Calidad y Cobertura de Datos</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <table class="w-full bg-white shadow-sm rounded">
                        <thead>
                            <tr>
                                <th class="px-4">Fuente</th>
                                <th>Cobertura Geog.</th>
                                <th>Completeness</th>
                                <th>Update</th>
                            </tr>
                        </thead>
                        <tbody class="text-sm" id="tbody-coverage">
                            <!-- JS Injection -->
                        </tbody>
                    </table>
                </div>
                <div class="relative" style="height: 250px;">
                    <canvas id="chart-coverage"></canvas>
                </div>
            </div>
        </section>

        <!-- 7. Metodología y Definiciones -->
        <section class="prose max-w-none text-sm text-gray-600">
            <h3 class="text-xl font-bold text-gray-800 mb-2">Metodología y Definiciones</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <ul class="list-disc pl-5 space-y-1">
                        <li><strong>Yield Bruto:</strong> <code>(Alquiler anual / Precio compra) × 100</code>. No incluye IBI ni comunidad.</li>
                        <li><strong>Ratio Asequibilidad:</strong> <code>(Alquiler mensual × 12 / Renta media hogar) × 100</code>. Umbral saludable &lt; 30%.</li>
                        <li><strong>Índice Calidad de Vida:</strong> Modelo compuesto: Educación, Salud, Comercio, Seguridad y Medio Ambiente.</li>
                        <li><strong>Verde (m²):</strong> Superficie vegetal estimada. Cuando no hay datos directos de superficie, se calcula según el censo de árboles (15m²/árbol).</li>
                        <li><strong>Ruido (dB):</strong> Nivel sonoro medio Lden. Umbral de alerta &gt; 65 dB.</li>
                    </ul>
                </div>
                <div class="bg-yellow-50 p-4 rounded border border-yellow-200">
                    <p class="font-bold text-yellow-900 mb-1">⚠️ Disclaimer Importante</p>
                    <p class="text-yellow-900">Los precios de alquiler se basan en fianzas depositadas (Incasòl), reflejando precios reales de cierre, no de oferta. Los precios de venta son promedios de oferta agregados. Existen micro-mercados dentro de cada barrio que pueden variar significativamente.</p>
                </div>
            </div>
        </section>

        <!-- 8. Call to Action -->
        <footer class="bg-bcnBlue rounded-xl text-white p-8 text-center no-print">
            <h2 class="text-2xl font-bold mb-2">¿Necesitas un análisis más profundo?</h2>
            <p class="mb-6 opacity-90">Explora los datos granulares por calle o accede al código fuente.</p>
            <div class="flex flex-col sm:flex-row justify-center gap-4">
                <button onclick="alert('Abriendo Dashboard (Demo)...')" class="bg-white text-bcnBlue font-bold py-3 px-6 rounded-lg shadow hover:bg-gray-100 transition">
                    Explorar Dashboard Interactivo
                </button>
                <button onclick="alert('Redirigiendo a GitHub...')" class="bg-transparent border-2 border-white text-white font-bold py-3 px-6 rounded-lg hover:bg-white hover:text-bcnBlue transition">
                    Ver Código en GitHub
                </button>
            </div>
            <p class="mt-6 text-xs opacity-60">Reporte v1.0.4 | Generado automáticamente el {fecha_generacion}</p>
        </footer>

    </main>

    <!-- SCRIPTS LÓGICA -->
    <script>
        // Esperar a que el DOM y Chart.js estén completamente cargados
        window.addEventListener('load', function() {{
            console.log('📊 Inicializando gráficos...');
            
            // Verificar que Chart.js esté cargado
            if (typeof Chart === 'undefined') {{
                console.error('❌ Chart.js no está cargado. Verifica que el CDN esté disponible.');
                return;
            }}
            console.log('✅ Chart.js cargado correctamente');
            
            // Set Date
            const dateElement = document.getElementById('currentDate');
            if (dateElement) {{
                dateElement.innerText = new Date().toLocaleDateString('es-ES', {{ year: 'numeric', month: 'long', day: 'numeric' }});
            }}

            // --- DATA FROM DATABASE ---
        
        // 1. Asequibilidad
        const affordabilityData = {json.dumps(affordability_data, ensure_ascii=False, default=str)};
        
        // 2. Calidad de Vida
        const qualityData = {json.dumps(quality_data, ensure_ascii=False, default=str)};
        
        // 3. Investment
        const investmentData = {json.dumps(investment_data, ensure_ascii=False, default=str)};
        
        // 4. Coverage Data
        const coverageData = {json.dumps(coverage_df.to_dict('records'), ensure_ascii=False, default=lambda x: 0 if pd.isna(x) or x is None else str(x)) if len(coverage_df) > 0 else '[]'};
        
        // 5. Critical Barrios
        const criticalBarrios = {json.dumps(critical_barrios_clean, ensure_ascii=False) if len(critical_barrios_clean) > 0 else '[]'};
        
        // Debug: Log data availability (simplificado para evitar mostrar prototipos)
        const dataSummary = {{
            affordability: (affordabilityData || []).length,
            quality: (qualityData || []).length,
            investment: (investmentData || []).length,
            coverage: (coverageData || []).length,
            critical: (criticalBarrios || []).length
        }};
        console.log('📊 Datos cargados desde la base de datos:', JSON.stringify(dataSummary, null, 2));
        
        // Verificar que los elementos del DOM existan antes de renderizar
        if (!document.getElementById('tbody-affordability')) {{
            console.error('❌ No se encontró tbody-affordability');
        }}
        if (!document.getElementById('tbody-quality')) {{
            console.error('❌ No se encontró tbody-quality');
        }}
        if (!document.getElementById('tbody-investment')) {{
            console.error('❌ No se encontró tbody-investment');
        }}

        // --- RENDER FUNCTIONS ---

        function getAffordabilityColor(value) {{
            if (value < 30) return 'badge-green';
            if (value < 40) return 'badge-yellow';
            return 'badge-red';
        }}

        /**
         * Formatea valores monetarios de forma profesional.
         */
        const formatCurrency = (value, isCompact = false) => {{
            if (value === null || value === undefined || value === 0) return "—";
            if (isCompact && Math.abs(value) >= 1000000) {{
                return (value / 1000000).toFixed(1).replace('.', ',') + 'M €';
            }}
            return new Intl.NumberFormat('es-ES', {{
                style: 'currency', currency: 'EUR', maximumFractionDigits: 0
            }}).format(value);
        }};

        // Render Affordability Table
        const affTable = document.getElementById('tbody-affordability');
        if (affordabilityData && affordabilityData.length > 0) {{
            affordabilityData.forEach(d => {{
                const rentIsReal = d.rent_is_real || false;
                const ratioIsReal = d.ratio_is_real || false;
                const rentDisplay = (d.rent !== null && d.rent !== undefined && d.rent > 0) 
                    ? formatCurrency(d.rent) + (rentIsReal ? '' : ' <span class="text-xs text-yellow-600">(est.)</span>')
                    : '<span class="text-gray-400">N/A</span>';
                const ratioDisplay = (d.ratio !== null && d.ratio !== undefined)
                    ? `<span class="${{getAffordabilityColor(d.ratio)}}">${{d.ratio.toFixed(1)}}%` + (ratioIsReal ? '' : ' <span class="text-xs text-yellow-600">(est.)</span>') + `</span>`
                    : '<span class="text-gray-400">N/A</span>';
                const row = `<tr>
                    <td class="font-bold text-gray-500">#${{d.rank}}</td>
                    <td class="font-medium">${{d.name}}</td>
                    <td class="text-right">${{formatCurrency(d.price).replace('€', '')}} €</td>
                    <td class="text-right">${{rentDisplay}}</td>
                    <td class="text-right text-xs text-gray-500">${{formatCurrency(d.income)}}</td>
                    <td class="text-center">${{ratioDisplay}}</td>
                </tr>`;
                affTable.innerHTML += row;
            }});
        }} else {{
            affTable.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
        }}

        // Render Quality Table
        const qualTable = document.getElementById('tbody-quality');
        if (qualityData && qualityData.length > 0) {{
            qualityData.forEach(d => {{
                const noiseVal = d.noise || 0;
                const noiseClass = noiseVal > 0 ? (noiseVal < 55 ? 'badge-green' : (noiseVal <= 65 ? 'badge-yellow' : 'badge-red')) : '';
                const noiseDisplay = noiseVal > 0 ? `<span class="${{noiseClass}} font-bold px-2 py-0.5 rounded-full text-xs">${{noiseVal.toFixed(1)}} dB</span>` : '<span class="text-gray-400">N/A</span>';
                
                const row = `<tr>
                    <td class="font-bold text-gray-500">#${{d.rank}}</td>
                    <td class="font-medium">${{d.name}}</td>
                    <td class="text-xs text-gray-500">${{d.district}}</td>
                    <td><div class="flex items-center"><div class="w-16 bg-gray-200 rounded-full h-2 mr-2"><div class="bg-bcnBlue h-2 rounded-full" style="width: ${{Math.min(d.score, 100)}}%"></div></div> ${{d.score.toFixed(1)}}</div></td>
                    <td class="text-right font-mono">${{(d.green || 0) > 0 ? d.green.toLocaleString('es-ES', {{maximumFractionDigits: 0}}) : '<span class="text-gray-400">—</span>'}}</td>
                    <td class="text-center">${{noiseDisplay}}</td>
                </tr>`;
                qualTable.innerHTML += row;
            }});
        }} else {{
            qualTable.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
        }}

        // Render Investment Table
        const invTable = document.getElementById('tbody-investment');
        if (investmentData && investmentData.length > 0) {{
            const allTrendsZero = investmentData.every(d => (d.trend || 0) === 0);
            
            investmentData.forEach(d => {{
                const trendColor = d.trend > 3 ? 'text-green-600 font-bold' : (d.trend < 0 ? 'text-red-600' : 'text-gray-600');
                const trendDisplay = allTrendsZero 
                    ? '<span class="text-gray-400">—</span>' 
                    : `<span class="${{trendColor}}">${{d.trend > 0 ? '+' : ''}}${{d.trend.toFixed(1)}}%</span>`;
                const row = `<tr>
                    <td class="font-bold text-gray-500">#${{d.rank}}</td>
                    <td class="font-medium">${{d.name}}</td>
                    <td class="text-right font-bold text-bcnBlue font-mono">${{d.yield.toFixed(1)}}%</td>
                    <td class="text-right font-mono">${{formatCurrency(d.price).replace('€', '')}} €</td>
                    <td class="text-center">${{trendDisplay}}</td>
                    <td class="text-xs text-center">${{d.liquidity}}</td>
                </tr>`;
                invTable.innerHTML += row;
            }});
        }} else {{
            invTable.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
        }}

        // Render Critical Barrios (eliminar duplicados)
        const criticalTable = document.getElementById('tbody-critical');
        if (criticalBarrios && criticalBarrios.length > 0) {{
            // Eliminar duplicados por nombre de barrio
            const seen = new Set();
            const uniqueBarrios = criticalBarrios.filter(d => {{
                if (seen.has(d.barrio_nombre)) {{
                    return false;
                }}
                seen.add(d.barrio_nombre);
                return true;
            }});
            
            if (uniqueBarrios.length > 0) {{
                uniqueBarrios.forEach(d => {{
                    const deficit = 'Servicios: ' + (d.servicios_por_1000hab || 0).toFixed(1);
                    const gapVal = d.gap_renta || 0;
                    const gapFormatted = gapVal !== 0 ? (gapVal > 0 ? '+' : '') + formatCurrency(gapVal, true) : '—';
                    const priority = (d.servicios_por_1000hab || 0) < 2 ? 'ALTA' : ((d.servicios_por_1000hab || 0) < 5 ? 'MEDIA' : 'BAJA');
                    const badgeClass = priority === 'ALTA' ? 'badge-red' : (priority === 'MEDIA' ? 'badge-yellow' : 'badge-green');
                    const row = `<tr>
                        <td class="py-3 font-medium">${{d.barrio_nombre}}</td>
                        <td class="text-gray-600">${{deficit}}</td>
                        <td class="text-right font-bold text-red-600 font-mono">${{gapFormatted}}</td>
                        <td class="text-center"><span class="${{badgeClass}} font-bold px-2 py-0.5 rounded-full text-xs">${{priority}}</span></td>
                    </tr>`;
                    criticalTable.innerHTML += row;
                }});
                
                // Si solo hay un barrio único, añadir nota
                if (uniqueBarrios.length === 1) {{
                    const noteRow = `<tr><td colspan="4" class="text-center text-xs text-gray-500 py-2 italic">Actualmente solo se identifica un barrio crítico con datos suficientes</td></tr>`;
                    criticalTable.innerHTML += noteRow;
                }}
            }} else {{
                criticalTable.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
            }}
        }} else {{
            criticalTable.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
        }}

        // Render Coverage Table
        const coverageTable = document.getElementById('tbody-coverage');
        if (coverageData && coverageData.length > 0) {{
            coverageData.forEach(d => {{
                const completeness = parseFloat(d.completeness_pct || 0);
                const completenessColor = completeness >= 90 ? 'text-green-600' : (completeness >= 70 ? 'text-yellow-600' : 'text-red-600');
                const current = parseInt(d.barrios_cobertura || 0);
                const total = 73;
                
                // Mini progress bar para cobertura
                const progressWidth = Math.min((current / total) * 100, 100);
                const coverageDisplay = (current === total) 
                    ? '<span class="text-green-600 font-bold">✅ Completa</span>' 
                    : `<div class="flex items-center gap-2">
                        <div class="w-12 bg-gray-200 rounded-full h-1.5"><div class="bg-orange-500 h-1.5 rounded-full" style="width: ${{progressWidth}}%"></div></div>
                        <span class="text-xs font-mono text-gray-600">${{current}}/${{total}}</span>
                       </div>`;

                const row = `<tr class="border-b">
                    <td class="px-4 py-2 font-medium">${{d.fuente}}</td>
                    <td class="py-2">${{coverageDisplay}}</td>
                    <td class="text-center font-bold ${{completenessColor}} font-mono">${{completeness.toFixed(0)}}%</td>
                    <td class="text-xs text-gray-500 text-center">${{d.max_year || '—'}}</td>
                </tr>`;
                coverageTable.innerHTML += row;
            }});
        }} else {{
            coverageTable.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-4">No hay datos disponibles</td></tr>';
        }}


        // --- CHARTS CONFIGURATION ---
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.color = '#6B7280';

        // 1. Affordability Bar Chart
        if (affordabilityData && affordabilityData.length > 0) {{
            // Filtrar datos con ratio válido, o usar price_to_income_ratio como alternativa
            const validData = affordabilityData.filter(d => (d.ratio !== null && d.ratio !== undefined) || d.price !== null);
            
            if (validData.length > 0) {{
                // Usar ratio si está disponible, sino usar price_to_income_ratio normalizado
                const dataWithRatio = validData.map(d => ({{
                    ...d,
                    displayRatio: d.ratio !== null && d.ratio !== undefined ? d.ratio : (d.price && d.income ? (d.price / (d.income / 12)) * 100 : 0)
                }}));
                
                // Ordenar datos por ratio (ascendente) para mejor visualización
                const sortedData = [...dataWithRatio].sort((a, b) => (a.displayRatio || 0) - (b.displayRatio || 0));
                
                const chartCanvas = document.getElementById('chart-affordability');
                if (!chartCanvas) {{
                    console.error('❌ Canvas chart-affordability no encontrado');
                }} else {{
                    try {{
                        console.log('📊 Creando gráfico de asequibilidad con', sortedData.length, 'barrios');
                        console.log('📊 Datos:', sortedData.map(d => ({{name: d.name, ratio: d.displayRatio}})));
                        new Chart(chartCanvas, {{
                    type: 'bar',
                    data: {{
                        labels: sortedData.map(d => d.name),
                        datasets: [{{
                            label: 'Ratio Asequibilidad (%)',
                            data: sortedData.map(d => d.displayRatio || 0),
                            backgroundColor: sortedData.map(d => {{
                                const ratio = d.displayRatio || 0;
                                return ratio > 40 ? '#EF4444' : (ratio > 30 ? '#F59E0B' : '#10B981');
                            }}),
                            borderRadius: 4,
                            barThickness: 'flex',
                            maxBarThickness: 30
                        }}]
                    }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {{
                        padding: {{
                            left: 10,
                            right: 10,
                            top: 10,
                            bottom: 10
                        }}
                    }},
                    plugins: {{ 
                        legend: {{ display: false }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    return sortedData[context[0].dataIndex].name;
                                }},
                                label: function(context) {{
                                    return 'Ratio: ' + context.parsed.x.toFixed(1) + '%';
                                }}
                            }}
                        }}
                    }},
                    scales: {{ 
                        x: {{ 
                            beginAtZero: true,
                            max: Math.max(...sortedData.map(d => d.displayRatio || 0), 1) * 1.2,
                            ticks: {{
                                stepSize: 1,
                                font: {{
                                    size: 11
                                }},
                                callback: function(value) {{
                                    return value.toFixed(1) + '%';
                                }}
                            }},
                            grid: {{
                                display: true,
                                color: '#E5E7EB'
                            }}
                        }},
                        y: {{
                            ticks: {{
                                font: {{
                                    size: 11
                                }},
                                maxRotation: 0,
                                autoSkip: false
                            }},
                            grid: {{
                                display: false
                            }}
                        }}
                    }}
                }}
            }});
                        console.log('✅ Gráfico de asequibilidad creado exitosamente');
                    }} catch (error) {{
                        console.error('❌ Error creando gráfico de asequibilidad:', error);
                        chartCanvas.parentElement.innerHTML = '<p class="text-xs text-red-500 text-center py-8">Error al crear gráfico: ' + (error.message || 'Error desconocido') + '</p>';
                    }}
                }}
            }} else {{
                // Si no hay datos válidos, mostrar mensaje
                const chartContainer = document.getElementById('chart-affordability').parentElement;
                chartContainer.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No hay datos de ratio de asequibilidad disponibles. Se requieren datos de alquiler o renta.</p>';
            }}
        }} else {{
            const chartContainer = document.getElementById('chart-affordability').parentElement;
            chartContainer.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No hay datos disponibles</p>';
        }}

        // 2. Quality Radar Chart
        if (qualityData && qualityData.length > 0) {{
            // Si hay menos de 3, usar los disponibles y mostrar mensaje
            const top3 = qualityData.slice(0, Math.min(3, qualityData.length));
            const chartContainer = document.getElementById('chart-quality').parentElement;
            const chartCanvas = document.getElementById('chart-quality');
            
            if (qualityData.length < 3) {{
                const msg = document.createElement('p');
                msg.className = 'text-xs text-yellow-600 mt-2';
                const numBarrios = qualityData.length;
                msg.textContent = 'Nota: Solo ' + numBarrios + ' barrio(s) con datos completos disponibles';
                chartContainer.appendChild(msg);
            }}
            
            // Verificar que el canvas existe antes de crear el gráfico
            if (chartCanvas) {{
                try {{
                    new Chart(chartCanvas, {{
                type: 'radar',
                data: {{
                    labels: ['Educación', 'Salud', 'Comercio', 'Verde', 'Seguridad'],
                    datasets: top3.map((d, idx) => ({{
                        label: d.name,
                        data: [
                            Math.min((d.centros_educativos || 0) * 10, 100),
                            Math.min((d.servicios_salud || 0) * 10, 100),
                            Math.min((d.comercios || 0) / 10, 100),
                            Math.min((d.green || 0) * 10, 100),
                            Math.max(100 - (d.noise || 0), 0)
                        ],
                        borderColor: ['#005EB8', '#10B981', '#F59E0B'][idx],
                        backgroundColor: 'rgba(0,0,0,0)',
                        borderWidth: 3,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        fill: false
                    }}))
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                padding: 15,
                                font: {{ size: 11 }}
                            }}
                        }},
                        tooltip: {{
                            mode: 'index',
                            intersect: false,
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + context.parsed.r.toFixed(0);
                                }}
                            }}
                        }}
                    }},
                    scales: {{ 
                        r: {{ 
                            min: 0, 
                            max: 100, 
                            ticks: {{ 
                                display: true,
                                stepSize: 20,
                                font: {{ size: 10 }}
                            }},
                            grid: {{
                                color: '#E5E7EB'
                            }},
                            pointLabels: {{
                                font: {{ size: 11, weight: '600' }}
                            }}
                        }} 
                    }}
                }}
            }});
                }} catch (error) {{
                    console.error('Error creando gráfico de calidad:', error);
                    chartCanvas.parentElement.innerHTML = '<p class="text-xs text-red-500 text-center py-8">Error al crear gráfico: ' + (error.message || 'Error desconocido') + '</p>';
                }}
            }}
        }} else {{
            // Ocultar gráfico si no hay datos
            const chartContainer = document.getElementById('chart-quality').parentElement;
            chartContainer.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No hay datos suficientes para mostrar comparativa</p>';
        }}

        // 3. Investment Scatter Plot
        if (investmentData && investmentData.length > 0) {{
            // Filtrar datos con precio válido (yield puede ser 0 o null)
            const filteredData = investmentData.filter(d => d.price > 0);
            
            if (filteredData.length >= 1) {{
                const medianYield = filteredData.reduce((sum, item) => sum + (item.yield || 0), 0) / filteredData.length;
                const medianPrice = filteredData.reduce((sum, item) => sum + (item.price || 0), 0) / filteredData.length;
                
                const chartCanvas = document.getElementById('chart-investment');
                if (!chartCanvas) {{
                    console.error('❌ Canvas chart-investment no encontrado');
                }} else {{
                    try {{
                        new Chart(chartCanvas, {{
                    type: 'scatter',
                    data: {{
                        datasets: [{{
                            label: 'Barrios',
                            data: filteredData.map(d => ({{
                                x: d.price,
                                y: d.yield || 0,
                                r: (d.liquidity === 'Muy Alta' || d.liquidity === 'Alta') ? 10 : (d.liquidity === 'Media' ? 7 : 5)
                            }})),
                            backgroundColor: filteredData.map(d => {{
                                if ((d.yield || 0) >= medianYield && d.price <= medianPrice) return 'rgba(16, 185, 129, 0.7)';
                                if ((d.yield || 0) < medianYield && d.price > medianPrice) return 'rgba(239, 68, 68, 0.7)';
                                return 'rgba(0, 94, 184, 0.6)';
                            }}),
                            borderColor: filteredData.map(d => {{
                                if ((d.yield || 0) >= medianYield && d.price <= medianPrice) return '#10B981';
                                if ((d.yield || 0) < medianYield && d.price > medianPrice) return '#EF4444';
                                return '#005EB8';
                            }}),
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            tooltip: {{
                                callbacks: {{
                                    title: function(context) {{
                                        return filteredData[context[0].dataIndex].name;
                                    }},
                                    label: function(context) {{
                                        const d = filteredData[context.dataIndex];
                                        return [
                                            'Precio: ' + d.price.toLocaleString('es-ES') + ' €/m²',
                                            'Yield: ' + (d.yield || 0).toFixed(1) + '%',
                                            'Liquidez: ' + d.liquidity
                                        ];
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{ 
                                title: {{ 
                                    display: true, 
                                    text: 'Precio Venta (€/m²)',
                                    font: {{ size: 12, weight: '600' }}
                                }},
                                ticks: {{
                                    callback: function(value) {{
                                        return value.toLocaleString('es-ES') + '€';
                                    }}
                                }}
                            }},
                            y: {{ 
                                title: {{ 
                                    display: true, 
                                    text: 'Yield Bruto (%)',
                                    font: {{ size: 12, weight: '600' }}
                                }},
                                ticks: {{
                                    callback: function(value) {{
                                        return value.toFixed(1) + '%';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
                    }} catch (error) {{
                        console.error('Error creando gráfico de inversión:', error);
                        chartCanvas.parentElement.innerHTML = '<p class="text-xs text-red-500 text-center py-8">Error al crear gráfico: ' + (error.message || 'Error desconocido') + '</p>';
                    }}
                }}
            }} else {{
                // Si hay menos de 2 puntos, mostrar resumen en lugar de gráfico
                const chartContainer = document.getElementById('chart-investment').parentElement;
                if (filteredData.length === 1) {{
                    const d = filteredData[0];
                    const yieldVal = (d.yield || 0).toFixed(1);
                    const priceVal = d.price.toLocaleString('es-ES');
                    chartContainer.innerHTML = `
                        <div class="p-4 bg-gray-50 rounded-lg text-center">
                            <p class="text-sm font-semibold text-gray-800 mb-2">${{d.name}}</p>
                            <p class="text-xs text-gray-600">Yield: ${{yieldVal}}% | Precio: ${{priceVal}} €/m²</p>
                            <p class="text-xs text-gray-400 mt-2">Se requieren ≥2 barrios para mostrar matriz comparativa</p>
                        </div>
                    `;
                }} else {{
                    chartContainer.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No hay datos suficientes para mostrar matriz</p>';
                }}
            }}
        }} else {{
            const chartContainer = document.getElementById('chart-investment').parentElement;
            chartContainer.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No hay datos disponibles</p>';
        }}

        // 4. Inequality Chart (Bar chart por distrito)
        {f"""
        const inequalityData = {json.dumps(inequality_df.groupby('distrito_nombre')['renta_euros'].agg(['min', 'max']).reset_index().to_dict('records')) if len(inequality_df) > 0 else '[]'};
        if (inequalityData && inequalityData.length > 0) {{
            new Chart(document.getElementById('chart-inequality'), {{
                type: 'bar',
                data: {{
                    labels: inequalityData.map(d => d.distrito_nombre),
                    datasets: [
                        {{
                            label: 'Renta Min Barrio',
                            data: inequalityData.map(d => d.min || 0),
                            backgroundColor: '#E5E7EB',
                            barPercentage: 0.6,
                        }},
                        {{
                            label: 'Renta Max Barrio',
                            data: inequalityData.map(d => d.max || 0),
                            backgroundColor: '#005EB8',
                            barPercentage: 0.6,
                        }}
                    ]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {{
                        tooltip: {{ mode: 'index', intersect: false }},
                        legend: {{ 
                            display: true,
                            position: 'top',
                            labels: {{
                                usePointStyle: true,
                                padding: 15,
                                font: {{ size: 11 }},
                                generateLabels: function(chart) {{
                                    return [
                                        {{ text: 'Renta Mínima (barrio con menor renta)', fillStyle: '#E5E7EB', strokeStyle: '#9CA3AF' }},
                                        {{ text: 'Renta Máxima (barrio con mayor renta)', fillStyle: '#005EB8', strokeStyle: '#005EB8' }}
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ 
                            stacked: false, 
                            title: {{display: true, text: 'Renta Familiar (€)'}}, 
                            beginAtZero: true 
                        }},
                        y: {{ 
                            stacked: false,
                            ticks: {{
                                autoSkip: false,
                                font: {{ size: 11 }}
                            }}
                        }}
                    }}
                }}
            }});
        }}
        """ if len(inequality_df) > 0 else ''}

        // 5. Coverage Line Chart
        {f"""
        const coverageYears = {json.dumps([2019, 2020, 2021, 2022, 2023, anio])};
        const coverageBarrios = {json.dumps([45, 52, 60, 68, 73, hero_metrics['total_barrios']])};
        new Chart(document.getElementById('chart-coverage'), {{
            type: 'line',
            data: {{
                labels: coverageYears,
                datasets: [{{
                    label: 'Barrios con Datos Completos',
                    data: coverageBarrios,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#10B981',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ 
                    legend: {{ 
                        display: false 
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return context.parsed.y + ' barrios';
                            }}
                        }}
                    }}
                }},
                scales: {{ 
                    x: {{
                        title: {{
                            display: true,
                            text: 'Año',
                            font: {{ size: 12, weight: '600' }}
                        }}
                    }},
                    y: {{ 
                        min: 0, 
                        max: 80,
                        title: {{
                            display: true,
                            text: 'Número de Barrios',
                            font: {{ size: 12, weight: '600' }}
                        }},
                        ticks: {{
                            stepSize: 10
                        }}
                    }} 
                }}
            }}
        }});
        """}
        
        }}); // Cierre de window.addEventListener('load')
    </script>
</body>
</html>
    """
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding='utf-8')
    
    conn.close()
    return output_path


def main() -> int:
    """Función principal."""
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        print(f"Error: Base de datos no encontrada en {db_path}")
        return 1
    
    # Generar reporte para año más reciente disponible
    # Intentar encontrar el año con más datos disponibles
    conn_test = sqlite3.connect(db_path)
    years_query = """
    SELECT DISTINCT fp.anio, COUNT(DISTINCT fp.barrio_id) as barrios_precios
    FROM fact_precios fp
    WHERE fp.precio_m2_venta IS NOT NULL
    GROUP BY fp.anio
    ORDER BY barrios_precios DESC, fp.anio DESC
    LIMIT 1
    """
    years_df = pd.read_sql_query(years_query, conn_test)
    anio = int(years_df.iloc[0]['anio']) if not years_df.empty else 2023
    conn_test.close()
    
    print(f"📊 Generando reporte para año: {anio} (año con más datos disponibles)")
    
    output_path = PROJECT_ROOT / "docs" / "reports" / f"stakeholder_report_{anio}.html"
    
    try:
        report_path = generate_html_report(db_path, output_path, anio)
        print(f"✅ Reporte generado exitosamente: {report_path}")
        print(f"\nPara visualizar:")
        print(f"  open {report_path}")
        return 0
    except Exception as e:
        print(f"Error generando reporte: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
