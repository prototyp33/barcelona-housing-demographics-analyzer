"""
Script mejorado para generar reporte ejecutivo profesional para stakeholders.

Incluye visualizaciones interactivas con Plotly y diseño profesional.
"""

from __future__ import annotations

import base64
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
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
    'text': '#1F2937',     # Gris oscuro
    'bg': '#F9FAFB',       # Gris claro
}


def get_top_affordable_barrios(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """
    Obtiene barrios con mejor relación precio-calidad (más asequibles).
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de análisis.
        limit: Número de barrios a retornar.
    
    Returns:
        DataFrame con barrios más asequibles incluyendo ratio de asequibilidad.
    """
    query = """
    SELECT 
        db.barrio_nombre,
        db.distrito_nombre,
        fp.precio_m2_venta,
        fp.precio_mes_alquiler,
        dr.renta_euros,
        ROUND((fp.precio_mes_alquiler * 12) / dr.renta_euros * 100, 2) AS ratio_asequibilidad,
        ROUND(fp.precio_m2_venta / NULLIF(dr.renta_euros / 12, 0), 2) AS price_to_income_ratio,
        (COALESCE(fe.total_centros_educativos, 0) + 
         COALESCE(fs.total_servicios_sanitarios, 0) + 
         COALESCE(fc.total_establecimientos, 0)) AS total_servicios
    FROM dim_barrios db
    JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = ?
    JOIN fact_renta dr ON db.barrio_id = dr.barrio_id AND dr.anio = ?
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = ?
    LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = ?
    LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = ?
    WHERE fp.precio_m2_venta IS NOT NULL
        AND dr.renta_euros IS NOT NULL
        AND fp.precio_mes_alquiler IS NOT NULL
    ORDER BY 
        ratio_asequibilidad ASC,
        total_servicios DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio, anio, anio, anio, anio, limit))
    
    # Añadir ranking
    df.insert(0, 'rank', range(1, len(df) + 1))
    
    return df


def get_top_quality_of_life(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """
    Obtiene barrios con mejor calidad de vida con desglose completo.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de análisis.
        limit: Número de barrios a retornar.
    
    Returns:
        DataFrame con barrios con mejor calidad de vida.
    """
    query = """
    SELECT 
        db.barrio_nombre,
        db.distrito_nombre,
        COALESCE(fe.total_centros_educativos, 0) AS centros_educativos,
        COALESCE(fs.total_servicios_sanitarios, 0) AS servicios_salud,
        COALESCE(fc.total_establecimientos, 0) AS comercios,
        COALESCE(fm.m2_zonas_verdes_por_habitante, 0) AS m2_zonas_verdes,
        COALESCE(fm.nivel_lden_medio, 0) AS nivel_ruido,
        ROUND(
            (COALESCE(fe.total_centros_educativos, 0) * 0.3 +
             COALESCE(fs.total_servicios_sanitarios, 0) * 0.3 +
             COALESCE(fc.total_establecimientos, 0) * 0.2 +
             COALESCE(fm.m2_zonas_verdes_por_habitante, 0) * 10 * 0.2) -
            COALESCE(fm.nivel_lden_medio, 0) * 0.1, 2
        ) AS indice_calidad_vida
    FROM dim_barrios db
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = ?
    LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = ?
    LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = ?
    LEFT JOIN fact_medio_ambiente fm ON db.barrio_id = fm.barrio_id AND fm.anio = ?
    WHERE fe.total_centros_educativos IS NOT NULL
        OR fs.total_servicios_sanitarios IS NOT NULL
    ORDER BY indice_calidad_vida DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio, anio, anio, anio, limit))
    
    # Añadir ranking
    df.insert(0, 'rank', range(1, len(df) + 1))
    
    return df


def get_price_trend(conn: sqlite3.Connection, barrio_id: int, anio: int = 2023, years_back: int = 3) -> Optional[float]:
    """
    Calcula la tendencia de precio en los últimos años.
    
    Args:
        conn: Conexión a la base de datos.
        barrio_id: ID del barrio.
        anio: Año actual.
        years_back: Años hacia atrás para calcular tendencia.
    
    Returns:
        Porcentaje de cambio anualizado o None si no hay datos suficientes.
    """
    query = """
    SELECT anio, AVG(precio_m2_venta) as precio_promedio
    FROM fact_precios
    WHERE barrio_id = ? AND anio >= ? AND anio <= ? AND precio_m2_venta IS NOT NULL
    GROUP BY anio
    ORDER BY anio
    """
    
    df = pd.read_sql_query(query, conn, params=(barrio_id, anio - years_back, anio))
    
    if len(df) < 2:
        return None
    
    precio_inicial = df.iloc[0]['precio_promedio']
    precio_final = df.iloc[-1]['precio_promedio']
    
    if precio_inicial == 0:
        return None
    
    # Calcular crecimiento anualizado
    years = len(df) - 1
    if years > 0:
        growth_rate = ((precio_final / precio_inicial) ** (1 / years) - 1) * 100
        return round(growth_rate, 2)
    
    return None


def get_top_investment_potential(conn: sqlite3.Connection, anio: int = 2023, limit: int = 10) -> pd.DataFrame:
    """
    Obtiene barrios con mejor potencial de inversión.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de análisis.
        limit: Número de barrios a retornar.
    
    Returns:
        DataFrame con barrios con mejor potencial de inversión.
    """
    query = """
    SELECT 
        db.barrio_id,
        db.barrio_nombre,
        db.distrito_nombre,
        fp.precio_m2_venta,
        fp.precio_mes_alquiler,
        dr.renta_euros,
        fc.densidad_comercial_por_1000hab,
        (COALESCE(fe.total_centros_educativos, 0) + 
         COALESCE(fs.total_servicios_sanitarios, 0)) AS servicios_publicos,
        -- Yield bruto: (alquiler mensual * 12) / (precio_m2 * 70m² promedio) * 100
        ROUND(
            (fp.precio_mes_alquiler * 12) / NULLIF(fp.precio_m2_venta * 70, 0) * 100, 2
        ) AS yield_bruto_pct
    FROM dim_barrios db
    JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = ?
    JOIN fact_renta dr ON db.barrio_id = dr.barrio_id AND dr.anio = ?
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = ?
    LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = ?
    LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = ?
    WHERE fp.precio_m2_venta IS NOT NULL
        AND fp.precio_mes_alquiler IS NOT NULL
        AND dr.renta_euros IS NOT NULL
    ORDER BY yield_bruto_pct DESC
    LIMIT ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio, anio, anio, anio, anio, limit))
    
    # Calcular tendencia de precio para cada barrio
    tendencias = []
    for _, row in df.iterrows():
        trend = get_price_trend(conn, row['barrio_id'], anio, years_back=3)
        tendencias.append(trend if trend is not None else 0.0)
    
    df['tendencia_precio_pct'] = tendencias
    
    # Calcular score de liquidez (proxy usando oferta Idealista si disponible)
    liquidez_query = """
    SELECT barrio_id, COUNT(*) as num_anuncios
    FROM fact_oferta_idealista
    WHERE anio = ? AND operacion = 'venta'
    GROUP BY barrio_id
    """
    liquidez_df = pd.read_sql_query(liquidez_query, conn, params=(anio,))
    
    df = df.merge(liquidez_df, on='barrio_id', how='left')
    df['num_anuncios'] = df['num_anuncios'].fillna(0)
    df['score_liquidez'] = df['num_anuncios'].apply(lambda x: min(x / 10, 10))  # Normalizar a 0-10
    
    # Añadir ranking
    df.insert(0, 'rank', range(1, len(df) + 1))
    
    return df


def get_inequality_analysis(conn: sqlite3.Connection, anio: int = 2023) -> Tuple[pd.DataFrame, Dict]:
    """
    Analiza desigualdades entre barrios.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de análisis.
    
    Returns:
        Tuple con DataFrame de desigualdad y diccionario con métricas de disparidad.
    """
    query = """
    SELECT 
        db.barrio_id,
        db.barrio_nombre,
        db.distrito_nombre,
        dp.poblacion_total,
        dr.renta_euros,
        fp.precio_m2_venta,
        fe.total_centros_educativos,
        fs.total_servicios_sanitarios,
        fc.total_establecimientos,
        fm.m2_zonas_verdes_por_habitante,
        ROUND(
            CAST((COALESCE(fe.total_centros_educativos, 0) + 
             COALESCE(fs.total_servicios_sanitarios, 0) + 
             COALESCE(fc.total_establecimientos, 0)) AS REAL) / 
            NULLIF(dp.poblacion_total, 0) * 1000, 2
        ) AS servicios_por_1000hab,
        CASE 
            WHEN fm.m2_zonas_verdes_por_habitante < 2 THEN 'Crítico'
            WHEN fm.m2_zonas_verdes_por_habitante < 5 THEN 'Insuficiente'
            WHEN fm.m2_zonas_verdes_por_habitante < 9 THEN 'Aceptable'
            ELSE 'Óptimo'
        END AS estado_zonas_verdes
    FROM dim_barrios db
    JOIN fact_demografia dp ON db.barrio_id = dp.barrio_id AND dp.anio = ?
    LEFT JOIN fact_renta dr ON db.barrio_id = dr.barrio_id AND dr.anio = ?
    LEFT JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = ?
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = ?
    LEFT JOIN fact_servicios_salud fs ON db.barrio_id = fs.barrio_id AND fs.anio = ?
    LEFT JOIN fact_comercio fc ON db.barrio_id = fc.barrio_id AND fc.anio = ?
    LEFT JOIN fact_medio_ambiente fm ON db.barrio_id = fm.barrio_id AND fm.anio = ?
    WHERE dp.poblacion_total > 0
    ORDER BY servicios_por_1000hab ASC
    """
    
    df = pd.read_sql_query(query, conn, params=(anio, anio, anio, anio, anio, anio, anio))
    
    # Calcular métricas de disparidad
    mejor_barrio = df.loc[df['servicios_por_1000hab'].idxmax()]
    peor_barrio = df.loc[df['servicios_por_1000hab'].idxmin()]
    
    disparidad = {
        'mejor_barrio': mejor_barrio['barrio_nombre'],
        'peor_barrio': peor_barrio['barrio_nombre'],
        'ratio_servicios': mejor_barrio['servicios_por_1000hab'] / max(peor_barrio['servicios_por_1000hab'], 0.01),
        'gap_renta': mejor_barrio['renta_euros'] - peor_barrio['renta_euros'] if pd.notna(mejor_barrio['renta_euros']) and pd.notna(peor_barrio['renta_euros']) else None,
        'gap_precio': mejor_barrio['precio_m2_venta'] - peor_barrio['precio_m2_venta'] if pd.notna(mejor_barrio['precio_m2_venta']) and pd.notna(peor_barrio['precio_m2_venta']) else None,
    }
    
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
        COUNT(DISTINCT barrio_id) as barrios_con_datos,
        COUNT(*) as total_registros,
        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_precios) as completeness
    FROM fact_precios
    """
    precios = pd.read_sql_query(precios_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'fact_precios',
        'nombre': 'Precios de Vivienda',
        'min_year': int(precios['min_year']) if pd.notna(precios['min_year']) else None,
        'max_year': int(precios['max_year']) if pd.notna(precios['max_year']) else None,
        'barrios_cobertura': int(precios['barrios_con_datos']) if pd.notna(precios['barrios_con_datos']) else 0,
        'completeness_pct': round(precios['completeness'], 1) if pd.notna(precios['completeness']) else 0,
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
        'fuente': 'fact_demografia',
        'nombre': 'Demografía',
        'min_year': int(demo['min_year']) if pd.notna(demo['min_year']) else None,
        'max_year': int(demo['max_year']) if pd.notna(demo['max_year']) else None,
        'barrios_cobertura': int(demo['barrios_con_datos']) if pd.notna(demo['barrios_con_datos']) else 0,
        'completeness_pct': round((demo['barrios_con_datos'] / 73) * 100, 1) if pd.notna(demo['barrios_con_datos']) else 0,
    })
    
    # fact_educacion
    educ_query = """
    SELECT COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_educacion WHERE anio = 2023
    """
    educ = pd.read_sql_query(educ_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'fact_educacion',
        'nombre': 'Educación',
        'min_year': 2023,
        'max_year': 2023,
        'barrios_cobertura': int(educ['barrios_con_datos']) if pd.notna(educ['barrios_con_datos']) else 0,
        'completeness_pct': round((educ['barrios_con_datos'] / 73) * 100, 1) if pd.notna(educ['barrios_con_datos']) else 0,
    })
    
    # fact_servicios_salud
    salud_query = """
    SELECT COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_servicios_salud WHERE anio = 2023
    """
    salud = pd.read_sql_query(salud_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'fact_servicios_salud',
        'nombre': 'Servicios de Salud',
        'min_year': 2023,
        'max_year': 2023,
        'barrios_cobertura': int(salud['barrios_con_datos']) if pd.notna(salud['barrios_con_datos']) else 0,
        'completeness_pct': round((salud['barrios_con_datos'] / 73) * 100, 1) if pd.notna(salud['barrios_con_datos']) else 0,
    })
    
    # fact_comercio
    comercio_query = """
    SELECT COUNT(DISTINCT barrio_id) as barrios_con_datos
    FROM fact_comercio WHERE anio = 2023
    """
    comercio = pd.read_sql_query(comercio_query, conn).iloc[0]
    coverage_data.append({
        'fuente': 'fact_comercio',
        'nombre': 'Comercio',
        'min_year': 2023,
        'max_year': 2023,
        'barrios_cobertura': int(comercio['barrios_con_datos']) if pd.notna(comercio['barrios_con_datos']) else 0,
        'completeness_pct': round((comercio['barrios_con_datos'] / 73) * 100, 1) if pd.notna(comercio['barrios_con_datos']) else 0,
    })
    
    return pd.DataFrame(coverage_data)


def create_affordability_bar_chart(df: pd.DataFrame) -> str:
    """
    Crea gráfico de barras horizontal para ratio de asequibilidad.
    
    Args:
        df: DataFrame con datos de barrios asequibles.
    
    Returns:
        JSON string del gráfico Plotly.
    """
    fig = go.Figure()
    
    # Color coding
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
        hovertemplate='<b>%{{y}}</b><br>Ratio: %{{x:.1f}}%<extra></extra>'
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
    """
    Crea gráfico radar para comparar Top 3 barrios en calidad de vida.
    
    Args:
        df: DataFrame con datos de calidad de vida (top 3).
    
    Returns:
        JSON string del gráfico Plotly.
    """
    top3 = df.head(3)
    
    fig = go.Figure()
    
    categories = ['Educación', 'Salud', 'Comercio', 'Zonas Verdes', 'Ruido']
    
    for idx, row in top3.iterrows():
        # Normalizar valores para el radar (0-100)
        valores = [
            min(row['centros_educativos'] * 10, 100),
            min(row['servicios_salud'] * 10, 100),
            min(row['comercios'] / 10, 100),
            min(row['m2_zonas_verdes'] * 10, 100),
            max(100 - row['nivel_ruido'], 0)  # Invertir ruido (menos es mejor)
        ]
        
        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=categories,
            fill='toself',
            name=row['barrio_nombre'],
            line=dict(width=2)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title='Comparación Top 3 Barrios - Calidad de Vida',
        height=500
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def create_investment_scatter(df: pd.DataFrame) -> str:
    """
    Crea scatter plot para potencial de inversión con cuadrantes.
    
    Args:
        df: DataFrame con datos de inversión.
    
    Returns:
        JSON string del gráfico Plotly.
    """
    fig = go.Figure()
    
    # Calcular medianas para dividir cuadrantes
    median_yield = df['yield_bruto_pct'].median()
    median_price = df['precio_m2_venta'].median()
    
    # Clasificar barrios por cuadrante
    for idx, row in df.iterrows():
        x = row['precio_m2_venta']
        y = row['yield_bruto_pct']
        size = row.get('score_liquidez', 5) * 10
        
        if y >= median_yield and x <= median_price:
            color = COLORS['success']  # Sweet spot
            name = 'Sweet Spot'
        elif y >= median_yield and x > median_price:
            color = COLORS['accent']  # Premium rentable
            name = 'Premium Rentable'
        elif y < median_yield and x <= median_price:
            color = COLORS['warning']  # Value play
            name = 'Value Play'
        else:
            color = COLORS['danger']  # Evitar
            name = 'Evitar'
        
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
    
    # Añadir líneas de división
    fig.add_shape(
        type="line",
        x0=median_price, y0=df['yield_bruto_pct'].min(),
        x1=median_price, y1=df['yield_bruto_pct'].max(),
        line=dict(color="gray", width=1, dash="dash")
    )
    fig.add_shape(
        type="line",
        x0=df['precio_m2_venta'].min(), y0=median_yield,
        x1=df['precio_m2_venta'].max(), y1=median_yield,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    # Añadir etiquetas de cuadrantes
    fig.add_annotation(x=median_price * 0.7, y=median_yield * 1.3, text="Sweet Spot", 
                      showarrow=False, font=dict(color=COLORS['success'], size=12, bold=True))
    fig.add_annotation(x=median_price * 1.3, y=median_yield * 1.3, text="Premium Rentable", 
                      showarrow=False, font=dict(color=COLORS['accent'], size=12, bold=True))
    fig.add_annotation(x=median_price * 0.7, y=median_yield * 0.7, text="Value Play", 
                      showarrow=False, font=dict(color=COLORS['warning'], size=12, bold=True))
    fig.add_annotation(x=median_price * 1.3, y=median_yield * 0.7, text="Evitar", 
                      showarrow=False, font=dict(color=COLORS['danger'], size=12, bold=True))
    
    fig.update_layout(
        title='Potencial de Inversión: Yield vs Precio',
        xaxis_title='Precio por m² (€)',
        yaxis_title='Yield Bruto Anual (%)',
        height=600,
        plot_bgcolor='white',
        hovermode='closest'
    )
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)


def format_table_with_colors(df: pd.DataFrame, color_column: str, thresholds: Dict[str, float]) -> str:
    """
    Formatea tabla HTML con color coding.
    
    Args:
        df: DataFrame a formatear.
        color_column: Columna para aplicar color coding.
        thresholds: Diccionario con umbrales {'low': valor, 'high': valor}.
    
    Returns:
        HTML string de la tabla.
    """
    html = '<table class="data-table">\n<thead>\n<tr>'
    
    # Headers
    for col in df.columns:
        html += f'<th>{col.replace("_", " ").title()}</th>'
    html += '</tr>\n</thead>\n<tbody>\n'
    
    # Rows
    for idx, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            value = row[col]
            
            # Formatear según tipo
            if pd.isna(value):
                display_value = '-'
                cell_class = ''
            elif col == color_column:
                if value < thresholds.get('low', 30):
                    cell_class = 'cell-success'
                elif value < thresholds.get('high', 40):
                    cell_class = 'cell-warning'
                else:
                    cell_class = 'cell-danger'
                
                if isinstance(value, float):
                    display_value = f"{value:.2f}%"
                else:
                    display_value = str(value)
            elif isinstance(value, float):
                if 'precio' in col.lower() or 'renta' in col.lower():
                    display_value = f"€{value:,.0f}"
                else:
                    display_value = f"{value:.2f}"
            else:
                display_value = str(value)
            
            html += f'<td class="{cell_class}">{display_value}</td>'
        
        html += '</tr>\n'
    
    html += '</tbody>\n</table>'
    return html


def get_hero_metrics(conn: sqlite3.Connection, anio: int = 2023) -> Dict[str, float]:
    """Obtiene las métricas hero para la sección principal."""
    total_barrios_query = "SELECT COUNT(*) as total FROM dim_barrios"
    total_barrios = pd.read_sql_query(total_barrios_query, conn).iloc[0]['total'] or 73
    
    precio_query = """
    SELECT 
        AVG(precio_m2_venta) as precio_promedio_m2,
        AVG(precio_mes_alquiler) as precio_alquiler_mes
    FROM fact_precios 
    WHERE anio = ? AND precio_m2_venta IS NOT NULL AND precio_mes_alquiler IS NOT NULL
    """
    precio_result = pd.read_sql_query(precio_query, conn, params=(anio,))
    
    precio_promedio = float(precio_result.iloc[0]['precio_promedio_m2'] or 0) if not precio_result.empty else 0.0
    precio_alquiler = float(precio_result.iloc[0]['precio_alquiler_mes'] or 0) if not precio_result.empty else 0.0
    
    if precio_promedio > 0 and precio_alquiler > 0:
        precio_total_promedio = precio_promedio * 70
        yield_bruto = (precio_alquiler * 12) / precio_total_promedio * 100
    else:
        yield_bruto = 0.0
    
    datasets_query = """
    SELECT COUNT(DISTINCT source) as num FROM (
        SELECT source FROM fact_precios WHERE anio = ? AND source IS NOT NULL
        UNION
        SELECT source FROM fact_renta WHERE anio = ? AND source IS NOT NULL
        UNION
        SELECT source FROM fact_educacion WHERE anio = ? AND source IS NOT NULL
        UNION
        SELECT source FROM fact_servicios_salud WHERE anio = ? AND source IS NOT NULL
        UNION
        SELECT source FROM fact_comercio WHERE anio = ? AND source IS NOT NULL
    )
    """
    datasets_result = pd.read_sql_query(datasets_query, conn, params=(anio, anio, anio, anio, anio))
    num_datasets = int(datasets_result.iloc[0]['num'] or 10) if not datasets_result.empty else 10
    
    return {
        'total_barrios': int(total_barrios),
        'precio_promedio_m2': precio_promedio,
        'yield_bruto_pct': yield_bruto,
        'num_datasets': num_datasets
    }


# Continuará en la siguiente parte debido a límite de tamaño...

