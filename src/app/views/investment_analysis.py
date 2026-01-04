"""
Vista de Análisis de Inversión - Estrategia "Sweet Spot" (Rentabilidad vs Riesgo).
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

from src.app.data_loader import load_investment_data
from src.app.utils import format_smart_currency, PROFESSIONAL_COLORS
from src.app.components import card_standard, render_empty_state
from src.app.styles import apply_plotly_theme

def render_investment_scatter(df: pd.DataFrame, year: int) -> None:
    """
    Renderiza el scatter plot de inversión con cuadrantes estratégicos y dimensión de gentrificación.
    """
    if df.empty:
        render_empty_state(title="Sin datos de inversión", icon="💰")
        return

    # Selector de dimensión para el tamaño de burbuja
    bubble_size_metric = st.segmented_control(
        "Dimensión de Burbuja:",
        options=["Liquidez", "Riesgo Gentrificación"],
        default="Riesgo Gentrificación",
        key="invest_bubble_metric"
    )
    
    size_col = "score_liquidez" if bubble_size_metric == "Liquidez" else "score_gentrificacion"

    # Calcular medianas para los cuadrantes
    median_yield = df['yield_bruto_pct'].median()
    median_price = df['avg_precio_m2'].median()

    # Clasificar barrios por cuadrante
    def classify_quadrant(row):
        x, y = row['avg_precio_m2'], row['yield_bruto_pct']
        if y >= median_yield and x <= median_price:
            return "🎯 Sweet Spot (Alta Rent./Bajo Precio)"
        elif y >= median_yield and x > median_price:
            return "💎 Premium Profitable"
        elif y < median_yield and x <= median_price:
            return "📉 Value Play (Bajo Riesgo)"
        else:
            return "⚠️ Avoid (Baja Rent./Alto Precio)"

    df['cuadrante'] = df.apply(classify_quadrant, axis=1)
    
    # Preparar colores
    color_map = {
        "🎯 Sweet Spot (Alta Rent./Bajo Precio)": PROFESSIONAL_COLORS['success'],
        "💎 Premium Profitable": PROFESSIONAL_COLORS['primary'],
        "📉 Value Play (Bajo Riesgo)": PROFESSIONAL_COLORS['warning'],
        "⚠️ Avoid (Baja Rent./Alto Precio)": PROFESSIONAL_COLORS['danger']
    }

    # Crear Scatter Plot
    fig = px.scatter(
        df,
        x="avg_precio_m2",
        y="yield_bruto_pct",
        color="cuadrante",
        size=size_col,
        hover_name="barrio_nombre",
        color_discrete_map=color_map,
        labels={
            "avg_precio_m2": "Precio Oferta (€/m²)",
            "yield_bruto_pct": "Yield Bruto (Renta Contrato) (%)",
            "cuadrante": "Estrategia",
            "score_gentrificacion": "Índice Gentrificación"
        },
        title=f"Matriz de Oportunidades Inmobiliarias {year}"
    )

    # Añadir líneas de cuadrantes
    fig.add_hline(y=median_yield, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=median_price, line_dash="dash", line_color="gray", opacity=0.5)

    # Formatear tooltips enriquecidos
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>" +
                      "Precio: %{x:,.0f} €/m²<br>" +
                      "Yield: %{y:.2f}%<br>" +
                      "Índice Gentrificación: %{customdata[1]:.1f}<br>" +
                      "Estrategia: %{customdata[0]}<extra></extra>",
        customdata=df[['cuadrante', 'score_gentrificacion']].values
    )

    apply_plotly_theme(fig)
    fig.update_layout(
        height=600, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, width="stretch")

def render_investment_table(df: pd.DataFrame) -> None:
    """
    Muestra la tabla detallada de oportunidades incluyendo indicadores de gentrificación.
    """
    st.subheader("📋 Detalle de Oportunidades por Barrio")
    
    # Formatear columnas para visualización
    df_display = df.copy()
    df_display['Precio Venta'] = df_display['avg_precio_m2'].apply(lambda x: f"{x:,.0f} €/m²")
    df_display['Yield Bruto'] = df_display['yield_bruto_pct'].apply(lambda x: f"{x:.2f}%")
    df_display['Riesgo Gentrificación'] = df_display['score_gentrificacion'].apply(lambda x: f"{x:.1f}")
    
    # Ordenar por Yield
    df_display = df_display.sort_values('yield_bruto_pct', ascending=False)
    
    cols = ['barrio_nombre', 'distrito_nombre', 'Precio Venta', 'Yield Bruto', 'Riesgo Gentrificación', 'cuadrante']
    
    st.dataframe(
        df_display[cols],
        column_config={
            "barrio_nombre": "Barrio",
            "distrito_nombre": "Distrito",
            "Riesgo Gentrificación": st.column_config.ProgressColumn(
                "Riesgo Gentrificación",
                help="Score 0-100 basado en educación, momentum de precios e inmigración",
                min_value=0,
                max_value=100,
                format="%.1f"
            ),
            "cuadrante": st.column_config.TextColumn("Estrategia")
        },
        width="stretch",
        hide_index=True
    )

def render(year: int = 2023) -> None:
    """
    Punto de entrada para la vista de inversión.
    """
    st.header("💰 ANÁLISIS DE INVERSIÓN")
    st.markdown("""
    Este módulo identifica las mejores oportunidades de inversión basadas en la relación 
    entre el **Precio de Oferta** (Idealista/Portal) y el **Yield Bruto** calculado con **Rentas de Contrato** (Incasòl).
    """)

    # Cargar datos
    df = load_investment_data(year)
    
    if df.empty:
        render_empty_state(
            title="Datos insuficientes para inversión",
            description=f"No hay datos de alquiler y venta combinados para el año {year}.",
            icon="📉"
        )
        return

    # Layout de 2 columnas para KPIs de inversión
    col1, col2 = st.columns(2)
    with col1:
        avg_yield = df['yield_bruto_pct'].mean()
        st.metric("Yield Promedio BCN", f"{avg_yield:.2f}%", help="Media de rentabilidad bruta en los barrios analizados")
    with col2:
        top_barrio = df.loc[df['yield_bruto_pct'].idxmax(), 'barrio_nombre']
        st.metric("Máxima Rentabilidad", top_barrio, delta=f"{df['yield_bruto_pct'].max():.2f}%")

    # Renderizar Scatter Plot
    with card_standard(title="🎯 Matriz Rentabilidad vs. Precio"):
        render_investment_scatter(df, year)

    # Renderizar Tabla
    render_investment_table(df)

