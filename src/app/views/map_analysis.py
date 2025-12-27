"""
Map Analysis view - Choropleth maps for spatial analysis.

Muestra mapas de precios, esfuerzo de compra y variación temporal.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app.config import COLOR_SCALES, VIVIENDA_TIPO_M2
from src.app.utils import format_smart_currency, get_noise_level_color, PROFESSIONAL_COLORS
from src.app.data_loader import (
    build_geojson,
    load_affordability_data,
    load_precios,
    load_temporal_comparison,
    load_quality_of_life_data,
)
from src.app.components import render_empty_state


def render_price_map(
    year: int = 2022,
    distrito_filter: str | None = None,
    key: str | None = None,
) -> None:
    """
    Renderiza mapa de precios por barrio.
    
    Args:
        year: Año a mostrar.
        distrito_filter: Filtro opcional por distrito.
        key: Clave única para el componente plotly_chart (evita duplicados).
    """
    df = load_precios(year, distrito_filter)
    
    if df.empty:
        render_empty_state(
            title="Sin datos de precios",
            description=f"No hay datos de precios disponibles para el año {year}.",
            icon="🗺️"
        )
        return
    
    geojson = build_geojson(df)
    
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color="avg_precio_m2",
        color_continuous_scale=COLOR_SCALES["prices"],
        hover_data={
            "barrio_nombre": True,
            "distrito_nombre": True,
            "avg_precio_m2": ":.0f",
        },
        labels={"avg_precio_m2": "€/m²"},
        title=f"Precio de Vivienda por Barrio ({year})",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(r=0, t=60, l=0, b=0), height=500)
    
    st.plotly_chart(fig, key=key)


def render_snapshot(year: int = 2022, key: str | None = None) -> None:
    """
    Renderiza un mapa 'snapshot' simplificado para el Dashboard Principal.
    
    Args:
        year: Año a mostrar.
        key: Clave única para el componente plotly_chart.
    """
    df = load_precios(year)
    
    if df.empty:
        render_empty_state(
            title="Sin datos",
            description="No hay datos para mostrar el snapshot.",
            icon="🗺️"
        )
        return
    
    geojson = build_geojson(df)
    
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color="avg_precio_m2",
        color_continuous_scale=COLOR_SCALES["prices"],
    )
    
    fig.update_geos(
        fitbounds="locations",
        visible=False,
    )
    
    fig.update_layout(
        margin=dict(r=0, t=0, l=0, b=0),
        height=150,
        dragmode=False,
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    st.plotly_chart(fig, key=key, config={"displayModeBar": False})


def render_affordability_map(year: int = 2022, key: str | None = None) -> None:
    """
    Renderiza mapa de esfuerzo de compra.
    
    Args:
        year: Año para precios (renta siempre es 2022).
        key: Clave única para el componente plotly_chart.
    """
    df = load_affordability_data(year)
    
    if df.empty:
        render_empty_state(
            title="Datos insuficientes",
            description="No hay datos suficientes para calcular el esfuerzo de compra.",
            icon="💰"
        )
        return
    
    geojson = build_geojson(df)
    
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color="effort_ratio",
        color_continuous_scale=COLOR_SCALES["effort"],
        hover_data={
            "barrio_nombre": True,
            "distrito_nombre": True,
            "avg_precio_m2": ":.0f",
            "renta_euros": ":.0f",
            "effort_ratio": ":.1f",
        },
        labels={
            "effort_ratio": f"Rentas anuales ({VIVIENDA_TIPO_M2} m²)",
            "avg_precio_m2": "Precio €/m²",
            "renta_euros": "Renta anual €",
        },
        title=f"Esfuerzo de Compra ({year})<br><sup>Rentas anuales necesarias para comprar {VIVIENDA_TIPO_M2} m²</sup>",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(r=0, t=80, l=0, b=0), height=500)
    
    st.plotly_chart(fig, key=key)


def render_change_map(
    year_start: int = 2015,
    year_end: int = 2022,
    key: str | None = None,
) -> None:
    """
    Renderiza mapa de variación de precios.
    
    Args:
        year_start: Año inicial.
        year_end: Año final.
        key: Clave única para el componente plotly_chart.
    """
    df = load_temporal_comparison(year_start, year_end)
    
    if df.empty:
        render_empty_state(
            title="Comparación no disponible",
            description=f"No hay datos suficientes para comparar {year_start} vs {year_end}.",
            icon="📉"
        )
        return
    
    geojson = build_geojson(df)
    
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color="var_precio_pct",
        color_continuous_scale=COLOR_SCALES["change"],
        hover_data={
            "barrio_nombre": True,
            "distrito_nombre": True,
            "precio_start": ":.0f",
            "precio_end": ":.0f",
            "var_precio_pct": ":.1f",
            "effort_change": ":.1f",
        },
        labels={
            "var_precio_pct": "Δ Precio %",
            "precio_start": f"Precio {year_start} €/m²",
            "precio_end": f"Precio {year_end} €/m²",
            "effort_change": "Δ Esfuerzo",
        },
        title=f"Variación de Precios ({year_start} → {year_end})<br><sup>Rojo = mayor incremento | Verde = menor incremento</sup>",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(r=0, t=80, l=0, b=0), height=500)
    
    st.plotly_chart(fig, key=key)


def render_enhanced_explorer(year: int = 2022, distrito_filter: str | None = None, key_prefix: str = "enhanced") -> None:
    """
    Renderiza el explorador de mapa avanzado con capas semánticas.
    """
    st.subheader("📍 Explorador Geoespacial")
    
    # 1. Selector de Capa (Metric Switcher)
    map_metric = st.radio(
        "Capa de Visualización:",
        [
            "Mercado: Precio Venta (€/m²)", 
            "Bienestar: Nivel de Ruido (dB)", 
            "Bienestar: Zonas Verdes (m²)",
            "Transformación: Riesgo Gentrificación (0-100)"
        ],
        horizontal=True,
        key=f"{key_prefix}_metric_selector"
    )

    # 2. Cargar datos según la métrica
    if "Precio" in map_metric:
        df = load_precios(year, distrito_filter)
        if df.empty:
            render_empty_state(title="Sin datos", icon="📉")
            return
        
        color_col = "avg_precio_m2"
        color_scale = ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#0D47A1"] # Azules profesionales
        title = f"Mapa de Precios de Venta ({year})"
        legend_title = "€/m²"
        
        # Formatear tooltips
        df['tooltip_val'] = df[color_col].apply(lambda x: f"{format_smart_currency(x)}/m²")
        
    elif "Ruido" in map_metric:
        df = load_quality_of_life_data(year)
        if distrito_filter:
            df = df[df['distrito_nombre'] == distrito_filter]
            
        color_col = "nivel_ruido"
        # Semáforo Inverso (Verde es bajo ruido, Rojo es alto)
        color_scale = [
            (0.0, PROFESSIONAL_COLORS['success']),
            (0.55, PROFESSIONAL_COLORS['warning']),
            (1.0, PROFESSIONAL_COLORS['danger'])
        ]
        title = "Mapa de Contaminación Acústica (Lden)"
        legend_title = "dB"
        df['tooltip_val'] = df[color_col].apply(lambda x: f"{x:.1f} dB")
        
    elif "Zonas Verdes" in map_metric:
        df = load_quality_of_life_data(year)
        if distrito_filter:
            df = df[df['distrito_nombre'] == distrito_filter]
            
        color_col = "m2_zonas_verdes"
        color_scale = ["#E8F5E9", "#81C784", "#4CAF50", "#2E7D32", "#1B5E20"] # Verdes
        title = "Mapa de Zonas Verdes por Barrio"
        legend_title = "m²"
        df['tooltip_val'] = df[color_col].apply(lambda x: f"{x:,.0f} m²")

    else: # Gentrificación
        from src.app.data_loader import load_gentrification_risk_metrics
        df = load_gentrification_risk_metrics(year)
        # Recuperar nombres y geometrías
        df_b = load_precios(year) 
        df = df.merge(df_b[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'geometry_json']], on='barrio_id')
        
        if distrito_filter:
            df = df[df['distrito_nombre'] == distrito_filter]
            
        color_col = "score_gentrificacion"
        color_scale = "Purples" # Escala de transformación
        title = "Índice de Riesgo de Gentrificación"
        legend_title = "Score (0-100)"
        df['tooltip_val'] = df[color_col].apply(lambda x: f"Riesgo: {x:.1f}/100")

    # 3. Construir GeoJSON
    geojson = build_geojson(df)
    
    # 4. Crear Mapa
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color=color_col,
        color_continuous_scale=color_scale,
        hover_data={
            "barrio_id": False,
            "barrio_nombre": True,
            "distrito_nombre": True,
            "tooltip_val": True,
            color_col: False
        },
        labels={"tooltip_val": "Valor", "barrio_nombre": "Barrio", "distrito_nombre": "Distrito"},
        title=title,
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(r=0, t=60, l=0, b=0), 
        height=600,
        coloraxis_colorbar=dict(title=legend_title)
    )
    
    st.plotly_chart(fig, key=f"{key_prefix}_chart", use_container_width=True)


def render(
    year: int = 2022,
    distrito_filter: str | None = None,
    key_prefix: str = "tab_territorio",
) -> None:
    """
    Renderiza la vista completa de Mapas.
    """
    st.header("Análisis Espacial")
    
    tab_exp, tab1, tab2, tab3 = st.tabs([
        "✨ Explorador Avanzado", 
        "Precios", 
        "Esfuerzo de Compra", 
        "Variación Temporal"
    ])
    
    with tab_exp:
        render_enhanced_explorer(year, distrito_filter, key_prefix=f"{key_prefix}_enhanced")
    
    with tab1:
        render_price_map(year, distrito_filter, key=f"{key_prefix}_price_map")
    
    with tab2:
        render_affordability_map(year, key=f"{key_prefix}_affordability_map")
    
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            year_start = st.selectbox(
                "Año inicial",
                options=list(range(2015, 2023)),
                index=0,
                key=f"{key_prefix}_year_start",
            )
        with col2:
            year_end = st.selectbox(
                "Año final",
                options=list(range(2015, 2023)),
                index=7,
                key=f"{key_prefix}_year_end",
            )
        
        if year_start >= year_end:
            st.error("El año inicial debe ser menor que el año final.")
        else:
            render_change_map(year_start, year_end, key=f"{key_prefix}_change_map")

