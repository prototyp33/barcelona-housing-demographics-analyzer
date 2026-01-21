"""
Social ESG View - Análisis de Impacto Social y Equidad (v1.0)

Esta vista consolida métricas de:
1. Infraestructura Social (Educación, Vivienda Pública)
2. Seguridad y Presión Turística
3. Equidad del Modelo (Fairness Metrics)
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
from src.app.data_loader import (
    load_accessibility_metrics,
    load_safety_metrics,
    load_equity_metrics
)
from src.app.styles import (
    apply_plotly_theme,
    render_responsive_kpi_grid,
    KPIMetric
)
from src.app.components import render_empty_state

def render_social_infrastructure(year: int, distrito: Optional[str] = None):
    """Renderiza gráficos de educación y vivienda pública."""
    st.subheader("🏫 Infraestructura Social")
    st.caption("Distribución de centros educativos y vivienda pública por barrio.")
    
    df = load_accessibility_metrics(year, distrito)
    
    if df.empty or df['total_centros_educativos'].isna().all():
        render_empty_state("Datos de infraestructura no disponibles", "No hay registros para el periodo seleccionado.", "🏫")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart de tipos de centros (BCN Global or Distrito)
        centros_cols = ['num_centros_infantil', 'num_centros_primaria', 'num_centros_secundaria', 'num_centros_universidad']
        centros_sums = df[centros_cols].sum()
        centros_labels = ['Infantil', 'Primaria', 'Secundaria', 'Universidad']
        
        fig_pie = px.pie(
            values=centros_sums.values,
            names=centros_labels,
            title="Distribución por Tipo de Centro",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        apply_plotly_theme(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True, key="esg_infrastructure_pie")

    with col2:
        # Bar chart de Vivienda Pública por barrio
        df_vp = df.sort_values('viviendas_publicas', ascending=False).head(10)
        fig_bar = px.bar(
            df_vp,
            x='viviendas_publicas',
            y='barrio_nombre',
            orientation='h',
            title="Top 10 Barrios: Vivienda Pública",
            color='viviendas_publicas',
            color_continuous_scale='GnBu'
        )
        apply_plotly_theme(fig_bar)
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True, key="esg_vivienda_bar")

def render_safety_and_tourism(year: int, distrito: Optional[str] = None):
    """Renderiza métricas de seguridad y presión de Airbnb."""
    st.subheader("🛡️ Seguridad y Entorno Turístico")
    st.caption("Relación entre la tasa de criminalidad y la densidad de alojamientos turísticos.")
    
    df = load_safety_metrics(year, distrito)
    
    if df.empty or df['tasa_criminalidad'].isna().all():
        render_empty_state("Métricas de seguridad no disponibles", "No hay datos de Mossos/InsideAirbnb vinculados.", "🛡️")
        return

    # Scatter plot: Criminalidad vs Precio Airbnb
    fig_scatter = px.scatter(
        df,
        x="tasa_criminalidad",
        y="num_listings",
        size="avg_price_night",
        color="distrito_nombre" if not distrito else "barrio_nombre",
        hover_name="barrio_nombre",
        title="Impacto Turístico vs. Seguridad",
        labels={
            "tasa_criminalidad": "Delitos (Tasa)",
            "num_listings": "Listings Airbnb",
            "avg_price_night": "Precio Noche Media"
        }
    )
    apply_plotly_theme(fig_scatter)
    st.plotly_chart(fig_scatter, use_container_width=True, key="esg_safety_scatter")

def render_model_fairness():
    """Muestra el monitor de equidad del modelo (v4 production)."""
    st.subheader("⚖️ Auditoría de Equidad (Fairness Monitor)")
    st.markdown(
        "Métricas de transparencia del algoritmo. Monitorizamos que el error de predicción "
        "sea equilibrado independientemente del nivel de renta del barrio."
    )
    
    df_equity = load_equity_metrics()
    
    if df_equity.empty:
        st.info("No se han registrado auditorías de equidad recientemente.")
        return
        
    latest = df_equity.iloc[0]
    
    # KPIs de Fairness
    fairness_kpis = [
        KPIMetric(
            title="Income Parity Ratio (IPR)",
            value=f"{latest['ipr']:.3f}",
            style="cool" if 0.8 <= latest['ipr'] <= 1.2 else "warn",
            delta="Target: 1.0",
        ),
        KPIMetric(
            title="Group Equity Score (GES)",
            value=f"{latest['ges']:.2f}",
            style="warm" if latest['ges'] > 0.5 else "warn",
            delta="Target: >0.6",
        ),
        KPIMetric(
            title="Error Medio (MAE)",
            value=f"{latest['mae']:.1f}€",
            style="cool",
            delta="V1 Baseline: 422€",
        )
    ]
    render_responsive_kpi_grid(fairness_kpis)
    
    # Tabla de histórico de auditorías
    with st.expander("Ver Histórico de Auditorías CI/CD"):
        st.dataframe(
            df_equity[['model_version', 'mae', 'r2', 'ges', 'ipr', 'etl_loaded_at']],
            use_container_width=True
        )

def render(year: Optional[int] = None, distrito_filter: Optional[str] = None):
    """Punto de entrada principal para la vista ESG."""
    st.title("🌱 Social ESG & Equity Monitor")
    st.markdown(
        "Barcelona Housing Analytics se compromete con la **ética algorítmica** y la **transparencia social**. "
        "Esta vista permite auditar el impacto del mercado inmobiliario en la comunidad."
    )
    
    if year is None:
        year = 2025 # Default to latest available integrated year
        
    # Monitor de Equidad (Global)
    render_model_fairness()
    
    st.divider()
    
    # Infraestructura y Seguridad (Filtrable)
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        render_social_infrastructure(year, distrito_filter)
        
    with col_right:
        render_safety_and_tourism(year, distrito_filter)
