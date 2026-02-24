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
from src.app.chart_config import CHART_HEIGHTS

def render_social_infrastructure(year: int, distrito: Optional[str] = None):
    """Renderiza gráficos de educación y vivienda pública."""
    st.subheader("🏫 Infraestructura Social")
    st.caption("Distribución de centros educativos y vivienda pública por barrio.")
    
    df = load_accessibility_metrics(year, distrito)
    
    if df.empty:
        render_empty_state("Datos de infraestructura no disponibles", "No hay registros para el periodo seleccionado.", "🏫")
        return

    col1, col2 = st.columns(2)
    
    with col1:
        # Check if we have breakdown data or just totals
        centros_cols = ['num_centros_infantil', 'num_centros_primaria', 'num_centros_secundaria', 'num_centros_universidad']
        
        if all(col in df.columns for col in centros_cols) and df[centros_cols].sum().sum() > 0:
            # We have breakdown data
            centros_sums = df[centros_cols].sum()
            centros_labels = ['Infantil', 'Primaria', 'Secundaria', 'Universidad']
            
            fig_pie = px.pie(
                values=centros_sums.values,
                names=centros_labels,
                title="Distribución por Tipo de Centro",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
        else:
            # Show total centers by neighborhood instead
            if 'total_centros_educativos' in df.columns and df['total_centros_educativos'].sum() > 0:
                df_top = df.nlargest(10, 'total_centros_educativos')
                fig_pie = px.bar(
                    df_top,
                    x='total_centros_educativos',
                    y='barrio_nombre',
                    orientation='h',
                    title="Top 10 Barrios: Centros Educativos",
                    color='total_centros_educativos',
                    color_continuous_scale='Blues'
                )
            else:
                st.info("📊 Datos de educación no disponibles para este año")
                return
                
        apply_plotly_theme(fig_pie)
        st.plotly_chart(fig_pie, width="stretch", key="esg_infrastructure_pie")

    with col2:
        # Bar chart de Vivienda Pública por barrio
        if 'viviendas_proteccion_oficial' in df.columns and df['viviendas_proteccion_oficial'].sum() > 0:
            df_vp = df.sort_values('viviendas_proteccion_oficial', ascending=False).head(10)
            fig_bar = px.bar(
                df_vp,
                x='viviendas_proteccion_oficial',
                y='barrio_nombre',
                orientation='h',
                title="Top 10 Barrios: Vivienda Pública",
                color='viviendas_proteccion_oficial',
                color_continuous_scale='GnBu'
            )
            apply_plotly_theme(fig_bar)
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, width="stretch", key="esg_vivienda_bar")
        else:
            st.info("🏘️ Datos de vivienda pública no disponibles para este año")

def render_safety_and_tourism(year: int, distrito: Optional[str] = None):
    """Renderiza métricas de seguridad y presión de Airbnb."""
    
    df = load_safety_metrics(year, distrito)
    
    if df.empty or df['tasa_criminalidad_1000hab'].isna().all():
        render_empty_state("Métricas de seguridad no disponibles", "No hay datos de Mossos/InsideAirbnb vinculados.", "🛡️")
        return

    # Fill NaN values for visualization
    df_plot = df.copy()
    df_plot['precio_noche_promedio'] = df_plot['precio_noche_promedio'].fillna(df_plot['precio_noche_promedio'].median())
    df_plot['num_listings_airbnb'] = df_plot['num_listings_airbnb'].fillna(0)
    df_plot['tasa_criminalidad_1000hab'] = df_plot['tasa_criminalidad_1000hab'].fillna(0)
    
    # Filter out rows where all key metrics are missing
    df_plot = df_plot.dropna(subset=['barrio_nombre'])

    # Scatter plot: Criminalidad vs Turismo - FULL WIDTH
    fig_scatter = px.scatter(
        df_plot,
        x="tasa_criminalidad_1000hab",
        y="num_listings_airbnb",
        size="precio_noche_promedio",
        color="distrito_nombre" if not distrito else "barrio_nombre",
        hover_name="barrio_nombre",
        hover_data={
            "tasa_criminalidad_1000hab": ":.1f",
            "num_listings_airbnb": True,
            "precio_noche_promedio": ":.0f€",
            "distrito_nombre": True
        },
        title="Relación entre Criminalidad y Presión Turística por Barrio",
        labels={
            "tasa_criminalidad_1000hab": "Tasa de Criminalidad (por 1000 hab.)",
            "num_listings_airbnb": "Número de Listings Airbnb",
            "precio_noche_promedio": "Precio Promedio/Noche"
        },
        height=CHART_HEIGHTS['standard']
    )
    
    fig_scatter.update_layout(
        xaxis_title="Tasa de Criminalidad (delitos por 1000 habitantes)",
        yaxis_title="Densidad de Alojamientos Turísticos (Airbnb)",
        legend_title="Distrito",
        font=dict(size=12)
    )
    
    apply_plotly_theme(fig_scatter)
    st.plotly_chart(fig_scatter, width="stretch", key="esg_safety_scatter")
    
    # Add summary metrics below the chart
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_crime = df_plot['tasa_criminalidad_1000hab'].mean()
        st.metric("Tasa Criminalidad Media", f"{avg_crime:.1f}", "por 1000 hab.")
    
    with col2:
        total_listings = df_plot['num_listings_airbnb'].sum()
        st.metric("Total Listings Airbnb", f"{int(total_listings):,}")
    
    with col3:
        avg_price = df_plot['precio_noche_promedio'].mean()
        st.metric("Precio Medio/Noche", f"{avg_price:.0f}€")

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
            width="stretch"
        )

def render(year: Optional[int] = None, distrito_filter: Optional[str] = None):
    """Punto de entrada principal para la vista ESG."""
    st.title("🌱 Social ESG & Equity Monitor")
    st.markdown(
        "Barcelona Housing Analytics se compromete con la **ética algorítmica** y la **transparencia social**. "
        "Esta vista permite auditar el impacto del mercado inmobiliario en la comunidad."
    )
    
    # Show data availability notice
    st.info(
        "📅 **Nota sobre disponibilidad de datos**: "
        "Esta vista muestra los datos más recientes disponibles para cada métrica. "
        "Educación (2025), Seguridad (2024), Vivienda Pública (2024), Turismo (2025)."
    )
    
    # Monitor de Equidad (Global) - Full Width
    render_model_fairness()
    
    st.divider()
    
    # === SECTION 1: SEGURIDAD Y TURISMO (Full Width) ===
    st.header("🛡️ Seguridad y Entorno Turístico")
    st.caption("📊 Datos de 2024 (Seguridad) y 2025 (Turismo)")
    render_safety_and_tourism(2024, distrito_filter)
    
    st.divider()
    
    # === SECTION 2: INFRAESTRUCTURA SOCIAL (Side by Side) ===
    st.header("🏫 Infraestructura Social")
    st.caption("📊 Datos de 2025 (Educación) y 2024 (Vivienda)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_education_chart(2025, distrito_filter)
    
    with col2:
        render_housing_chart(2025, distrito_filter)


def render_education_chart(year: int, distrito: Optional[str] = None):
    """Renderiza solo el gráfico de educación."""
    df = load_accessibility_metrics(year, distrito)
    
    if df.empty or 'total_centros_educativos' not in df.columns or df['total_centros_educativos'].sum() == 0:
        st.info("📊 Datos de educación no disponibles")
        return
    
    # Show top 15 for better visibility
    df_top = df.nlargest(15, 'total_centros_educativos')
    
    fig = px.bar(
        df_top,
        y='barrio_nombre',
        x='total_centros_educativos',
        orientation='h',
        title="Top 15 Barrios: Centros Educativos",
        color='total_centros_educativos',
        color_continuous_scale='Blues',
        height=CHART_HEIGHTS['standard']
    )
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Número de Centros",
        yaxis_title="",
        showlegend=False
    )
    
    apply_plotly_theme(fig)
    st.plotly_chart(fig, width="stretch", key="esg_education_bar")


def render_housing_chart(year: int, distrito: Optional[str] = None):
    """Renderiza solo el gráfico de vivienda pública."""
    df = load_accessibility_metrics(year, distrito)
    
    if df.empty or 'viviendas_proteccion_oficial' not in df.columns or df['viviendas_proteccion_oficial'].sum() == 0:
        st.info("🏘️ Datos de vivienda pública no disponibles")
        return
    
    # Show top 15 for better visibility
    df_top = df.nlargest(15, 'viviendas_proteccion_oficial')
    
    fig = px.bar(
        df_top,
        y='barrio_nombre',
        x='viviendas_proteccion_oficial',
        orientation='h',
        title="Top 15 Barrios: Vivienda Pública",
        color='viviendas_proteccion_oficial',
        color_continuous_scale='Greens',
        height=CHART_HEIGHTS['standard']
    )
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        xaxis_title="Unidades VPO",
        yaxis_title="",
        showlegend=False
    )
    
    apply_plotly_theme(fig)
    st.plotly_chart(fig, width="stretch", key="esg_housing_bar")
