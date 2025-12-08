"""
Map Analysis view - Choropleth maps for spatial analysis.

Muestra mapas de precios, esfuerzo de compra y variación temporal.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.app.config import COLOR_SCALES, VIVIENDA_TIPO_M2
from src.app.data_loader import (
    build_geojson,
    load_affordability_data,
    load_precios,
    load_temporal_comparison,
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


def render(
    year: int = 2022,
    distrito_filter: str | None = None,
    key_prefix: str = "tab_territorio",
) -> None:
    """
    Renderiza la vista completa de Mapas.
    
    Args:
        year: Año seleccionado.
        distrito_filter: Filtro opcional por distrito.
        key_prefix: Prefijo para claves únicas de componentes plotly.
    """
    st.header("Análisis Espacial")
    
    tab1, tab2, tab3 = st.tabs(["Precios", "Esfuerzo de Compra", "Variación Temporal"])
    
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

