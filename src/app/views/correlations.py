"""
Correlations view - Statistical analysis and scatter plots.

Muestra matriz de correlación y relaciones entre variables.
"""

from __future__ import annotations

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.app.config import COLOR_SCALES
from src.app.data_loader import load_correlation_data


def render_correlation_matrix(year: int = 2022) -> None:
    """
    Renderiza matriz de correlación.
    
    Args:
        year: Año a analizar.
    """
    df = load_correlation_data(year)
    
    if df.empty:
        st.warning(f"No hay datos suficientes para calcular correlaciones en {year}.")
        return
    
    corr_cols = ["avg_precio_m2", "renta_euros", "densidad_hab_km2", "poblacion_total"]
    corr_matrix = df[corr_cols].corr()
    
    labels = ["Precio €/m²", "Renta anual", "Densidad hab/km²", "Población total"]
    
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=labels,
            y=labels,
            colorscale=COLOR_SCALES["correlation"],
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 14},
            hovertemplate="Correlación %{y} vs %{x}: %{z:.2f}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=f"Matriz de Correlación ({year})",
        height=450,
    )
    
    st.plotly_chart(fig, key="correlations_matrix")
    
    # Mostrar interpretación
    precio_renta = corr_matrix.loc["avg_precio_m2", "renta_euros"]
    precio_densidad = corr_matrix.loc["avg_precio_m2", "densidad_hab_km2"]
    
    st.info(
        f"**Correlaciones con Precio:**\n"
        f"- Renta anual: r = {precio_renta:.3f}\n"
        f"- Densidad: r = {precio_densidad:.3f}"
    )


def render_scatter_plots(year: int = 2022) -> None:
    """
    Renderiza scatter plots de precio vs otras variables.
    
    Args:
        year: Año a analizar.
    """
    df = load_correlation_data(year)
    
    if df.empty:
        st.warning(f"No hay datos suficientes para el año {year}.")
        return
    
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Precio vs Renta", "Precio vs Densidad"),
        horizontal_spacing=0.1,
    )
    
    # Precio vs Renta
    fig.add_trace(
        go.Scatter(
            x=df["renta_euros"],
            y=df["avg_precio_m2"],
            mode="markers",
            marker=dict(
                size=10,
                color=df["avg_precio_m2"],
                colorscale="Plasma",
                showscale=False,
            ),
            text=df["barrio_nombre"],
            hovertemplate="<b>%{text}</b><br>Renta: €%{x:,.0f}<br>Precio: €%{y:,.0f}/m²<extra></extra>",
            name="",
        ),
        row=1,
        col=1,
    )
    
    # Precio vs Densidad
    fig.add_trace(
        go.Scatter(
            x=df["densidad_hab_km2"],
            y=df["avg_precio_m2"],
            mode="markers",
            marker=dict(
                size=10,
                color=df["avg_precio_m2"],
                colorscale="Plasma",
                showscale=False,
            ),
            text=df["barrio_nombre"],
            hovertemplate="<b>%{text}</b><br>Densidad: %{x:,.0f} hab/km²<br>Precio: €%{y:,.0f}/m²<extra></extra>",
            name="",
        ),
        row=1,
        col=2,
    )
    
    fig.update_xaxes(title_text="Renta anual (€)", row=1, col=1)
    fig.update_xaxes(title_text="Densidad (hab/km²)", row=1, col=2)
    fig.update_yaxes(title_text="Precio (€/m²)", row=1, col=1)
    fig.update_yaxes(title_text="Precio (€/m²)", row=1, col=2)
    
    fig.update_layout(
        title=f"Relaciones entre Precio, Renta y Densidad ({year})",
        showlegend=False,
        height=450,
    )
    
    st.plotly_chart(fig, key="correlations_scatter_plots")


def render_top_barrios(year: int = 2022) -> None:
    """
    Muestra ranking de barrios por precio y esfuerzo.
    
    Args:
        year: Año a analizar.
    """
    from src.app.data_loader import load_affordability_data
    
    df = load_affordability_data(year)
    
    if df.empty:
        st.warning("No hay datos disponibles.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Más Caros")
        top_precio = df.nlargest(10, "avg_precio_m2")[
            ["barrio_nombre", "distrito_nombre", "avg_precio_m2", "effort_ratio"]
        ].reset_index(drop=True)
        top_precio.index += 1
        top_precio.columns = ["Barrio", "Distrito", "€/m²", "Esfuerzo"]
        st.dataframe(
            top_precio.style.format({"€/m²": "{:,.0f}", "Esfuerzo": "{:.1f}"}),
        )
    
    with col2:
        st.subheader("Más Asequibles")
        bottom_effort = df.nsmallest(10, "effort_ratio")[
            ["barrio_nombre", "distrito_nombre", "avg_precio_m2", "effort_ratio"]
        ].reset_index(drop=True)
        bottom_effort.index += 1
        bottom_effort.columns = ["Barrio", "Distrito", "€/m²", "Esfuerzo"]
        st.dataframe(
            bottom_effort.style.format({"€/m²": "{:,.0f}", "Esfuerzo": "{:.1f}"}),
        )


def render(year: int = 2022) -> None:
    """
    Renderiza la vista completa de Correlaciones.
    
    Args:
        year: Año seleccionado.
    """
    st.header("Análisis de Correlaciones")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_correlation_matrix(year)
    
    with col2:
        render_scatter_plots(year)
    
    st.divider()
    
    st.subheader("Rankings de Barrios")
    render_top_barrios(year)

