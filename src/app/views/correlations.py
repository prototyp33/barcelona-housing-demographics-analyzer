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

from src.app.config import COLOR_SCALES, PROFESSIONAL_COLORS
from src.app.data_loader import load_full_correlation_data
from src.app.components import render_empty_state, card_standard
from src.app.styles import apply_plotly_theme


def render_correlation_matrix(year: int = 2023) -> None:
    """
    Renderiza matriz de correlación avanzada.
    """
    df = load_full_correlation_data(year)
    
    if df.empty:
        render_empty_state(title="Correlaciones no disponibles", icon="📉")
        return
    
    # Columnas para correlación
    corr_map = {
        "avg_precio_m2": "Precio €/m²",
        "renta_euros": "Renta Anual",
        "score_gentrificacion": "Índice Gentrif.",
        "pct_universitarios": "% Universitarios",
        "nivel_ruido": "Ruido (dB)",
        "densidad_hab_km2": "Densidad"
    }
    
    df_corr = df[list(corr_map.keys())].corr()
    labels = list(corr_map.values())
    
    fig = go.Figure(
        data=go.Heatmap(
            z=df_corr.values,
            x=labels,
            y=labels,
            colorscale="RdBu_r", # Divergente profesional
            zmin=-1,
            zmax=1,
            text=np.round(df_corr.values, 2),
            texttemplate="%{text}",
            textfont={"size": 12, "family": "Inter"},
            hovertemplate="Relación %{y} vs %{x}: %{z:.2f}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=dict(text=f"Mapa de Relaciones Estadísticas {year}", font=dict(size=16)),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    st.plotly_chart(fig, key="correlations_matrix", use_container_width=True)


def render_advanced_scatters(year: int = 2023) -> None:
    """
    Renderiza scatter plots cruzando Gentrificación, Precio y Ruido.
    """
    df = load_full_correlation_data(year)
    
    if df.empty:
        return

    st.subheader("📊 Análisis de Impacto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Scatter 1: Gentrificación vs Precio (El motor del cambio)
        fig1 = px.scatter(
            df,
            x="score_gentrificacion",
            y="avg_precio_m2",
            trendline="ols",
            color="distrito_nombre",
            hover_name="barrio_nombre",
            title="Gentrificación vs. Precio de Mercado",
            labels={
                "score_gentrificacion": "Índice Gentrificación (0-100)",
                "avg_precio_m2": "Precio Venta (€/m²)",
                "distrito_nombre": "Distrito"
            }
        )
        apply_plotly_theme(fig1)
        fig1.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True, key="scatter_gentrif_precio")
        st.caption("🔍 Muestra cómo la transformación demográfica empuja los precios al alza.")

    with col2:
        # Scatter 2: Ruido vs Gentrificación (Bienestar en transformación)
        fig2 = px.scatter(
            df,
            x="nivel_ruido",
            y="score_gentrificacion",
            size="avg_precio_m2",
            color="score_gentrificacion",
            color_continuous_scale="Purples",
            hover_name="barrio_nombre",
            title="Calidad Acústica vs. Gentrificación",
            labels={
                "nivel_ruido": "Nivel de Ruido (dB)",
                "score_gentrificacion": "Índice Gentrificación",
                "avg_precio_m2": "Precio (€/m²)"
            }
        )
        apply_plotly_theme(fig2)
        fig2.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True, key="scatter_ruido_gentrif")
        st.caption("🔊 Evalúa si las zonas en transformación están expuestas a mayor contaminación acústica.")


def render(year: int = 2023) -> None:
    """
    Renderiza la vista de Correlaciones mejorada.
    """
    st.header("📈 CORRELACIONES Y DINÁMICAS URBANAS")
    st.markdown("""
    Este módulo analiza estadísticamente cómo interactúan las variables económicas, 
    ambientales y demográficas en la ciudad.
    """)
    
    col_matrix, col_analysis = st.columns([1.2, 1.8])
    
    with col_matrix:
        with card_standard(title="🧩 Matriz de Interdependencia"):
            render_correlation_matrix(year)
    
    with col_analysis:
        render_advanced_scatters(year)
    
    st.divider()
    
    # Insights dinámicos basados en datos
    df = load_full_correlation_data(year)
    if not df.empty:
        corr_val = df['score_gentrificacion'].corr(df['avg_precio_m2'])
        st.info(f"💡 **Insight Estratégico:** Se detecta una correlación de **{corr_val:.2f}** entre la Gentrificación y el Precio. "
                "Esto confirma que la transformación demográfica es el principal predictor del valor inmobiliario en Barcelona.")

