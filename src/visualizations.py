"""
Visualizations Module - Chart Generation Functions

Consolidates all Plotly and Altair chart generation functions.
These functions return figure objects, keeping them independent of Streamlit's UI loop.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

from src.app.config import COLOR_SCALES, COLORS
from src.app.styles import apply_plotly_theme


def create_price_evolution_chart(
    df: pd.DataFrame,
    x_col: str = "año",
    y_col: str = "precio_medio",
    title: str = "Evolución del Precio Medio de Vivienda (€/m²)",
    color: Optional[str] = None,
) -> go.Figure:
    """
    Crea un gráfico de línea para evolución temporal de precios.
    
    Args:
        df: DataFrame con datos temporales.
        x_col: Nombre de la columna para el eje X.
        y_col: Nombre de la columna para el eje Y.
        title: Título del gráfico.
        color: Color de la línea (opcional).
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        markers=True,
        title=title,
        labels={x_col: "Año", y_col: "Precio Medio (€/m²)"},
    )
    
    if color:
        fig.update_traces(
            line=dict(color=color, width=3),
            marker=dict(size=10, color=color),
        )
    else:
        fig.update_traces(
            line=dict(color=COLORS["accent_blue"], width=3),
            marker=dict(size=10, color=COLORS["accent_blue"]),
        )
    
    apply_plotly_theme(fig)
    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(dtick=1),
    )
    
    return fig


def create_price_trends_chart(
    df: pd.DataFrame,
    x_col: str = "anyo",
    y_col: str = "precio_venta_m2",
    color_col: str = "barrio_nombre",
    title: str = "Evolución de Precios por Barrio",
) -> go.Figure:
    """
    Crea un gráfico de líneas múltiples para tendencias de precios por barrio.
    
    Args:
        df: DataFrame con datos temporales por barrio.
        x_col: Nombre de la columna para el eje X.
        y_col: Nombre de la columna para el eje Y.
        color_col: Columna para diferenciar líneas por color.
        title: Título del gráfico.
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        markers=True,
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_correlation_matrix(
    df: pd.DataFrame,
    corr_map: dict[str, str],
    year: int = 2023,
) -> go.Figure:
    """
    Crea una matriz de correlación como heatmap.
    
    Args:
        df: DataFrame con datos numéricos.
        corr_map: Diccionario mapeando nombres de columnas a etiquetas.
        year: Año para el título.
    
    Returns:
        Figura de Plotly con heatmap.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Calcular correlación
    df_corr = df[list(corr_map.keys())].corr()
    labels = list(corr_map.values())
    
    fig = go.Figure(
        data=go.Heatmap(
            z=df_corr.values,
            x=labels,
            y=labels,
            colorscale="RdBu_r",
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
    
    return fig


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    hover_name: Optional[str] = None,
    title: str = "Scatter Plot",
    trendline: Optional[str] = None,
    labels: Optional[dict[str, str]] = None,
) -> go.Figure:
    """
    Crea un gráfico de dispersión (scatter plot).
    
    Args:
        df: DataFrame con datos.
        x_col: Nombre de la columna para el eje X.
        y_col: Nombre de la columna para el eje Y.
        color_col: Columna para colorear puntos (opcional).
        size_col: Columna para tamaño de puntos (opcional).
        hover_name: Columna para mostrar en hover (opcional).
        title: Título del gráfico.
        trendline: Tipo de línea de tendencia ('ols', 'lowess', etc.).
        labels: Diccionario con etiquetas personalizadas.
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        hover_name=hover_name,
        title=title,
        trendline=trendline,
        labels=labels or {},
    )
    
    apply_plotly_theme(fig)
    
    return fig


def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "Bar Chart",
    orientation: str = "v",
    labels: Optional[dict[str, str]] = None,
) -> go.Figure:
    """
    Crea un gráfico de barras.
    
    Args:
        df: DataFrame con datos.
        x_col: Nombre de la columna para el eje X.
        y_col: Nombre de la columna para el eje Y.
        color_col: Columna para colorear barras (opcional).
        title: Título del gráfico.
        orientation: Orientación ('v' para vertical, 'h' para horizontal).
        labels: Diccionario con etiquetas personalizadas.
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        orientation=orientation,
        labels=labels or {},
    )
    
    apply_plotly_theme(fig)
    
    return fig


def create_distrito_comparison_chart(
    df: pd.DataFrame,
    group_col: str = "distrito_nombre",
    value_col: str = "avg_precio_m2",
    title: str = "Comparación por Distrito",
    top_n: int = 10,
) -> go.Figure:
    """
    Crea un gráfico de barras horizontal para comparación de distritos o barrios.
    
    Args:
        df: DataFrame con datos agrupados.
        group_col: Columna para agrupar (distrito o barrio).
        value_col: Columna con valores a comparar.
        title: Título del gráfico.
        top_n: Número de grupos a mostrar (top N).
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Agrupar y ordenar
    df_grouped = df.groupby(group_col)[value_col].mean().reset_index()
    df_grouped = df_grouped.sort_values(value_col, ascending=True).tail(top_n)
    
    fig = px.bar(
        df_grouped,
        x=value_col,
        y=group_col,
        orientation='h',
        title=title,
        labels={value_col: "Precio Medio (€/m²)", group_col: group_col.replace("_", " ").title()},
    )
    
    fig.update_traces(
        marker_color=COLORS["accent_blue"],
        marker_line_color='white',
        marker_line_width=1,
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(df_grouped) * 40),
    )
    
    return fig


def create_investment_scatter(
    df: pd.DataFrame,
    x_col: str = "avg_precio_m2",
    y_col: str = "yield_bruto_pct",
    color_col: str = "cuadrante",
    size_col: Optional[str] = "score_gentrificacion",
    hover_name: str = "barrio_nombre",
    title: str = "Matriz de Oportunidades Inmobiliarias",
    color_map: Optional[dict[str, str]] = None,
    median_x: Optional[float] = None,
    median_y: Optional[float] = None,
) -> go.Figure:
    """
    Crea un scatter plot para análisis de inversión con cuadrantes.
    
    Args:
        df: DataFrame con datos de inversión.
        x_col: Columna para eje X (precio).
        y_col: Columna para eje Y (yield).
        color_col: Columna para colorear por cuadrante.
        size_col: Columna para tamaño de puntos (opcional).
        hover_name: Columna para hover.
        title: Título del gráfico.
        color_map: Mapa de colores para cuadrantes.
        median_x: Mediana de X para línea de referencia.
        median_y: Mediana de Y para línea de referencia.
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        size=size_col,
        hover_name=hover_name,
        color_discrete_map=color_map,
        labels={
            x_col: "Precio Oferta (€/m²)",
            y_col: "Yield Bruto (%)",
            color_col: "Estrategia",
            size_col: "Índice Gentrificación" if size_col else None,
        },
        title=title,
    )
    
    # Añadir líneas de referencia si se proporcionan
    if median_y is not None:
        fig.add_hline(y=median_y, line_dash="dash", line_color="gray", opacity=0.5)
    if median_x is not None:
        fig.add_vline(x=median_x, line_dash="dash", line_color="gray", opacity=0.5)
    
    apply_plotly_theme(fig)
    fig.update_layout(
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_gentrification_scatter(
    df: pd.DataFrame,
    x_col: str = "score_gentrificacion",
    y_col: str = "avg_precio_m2",
    color_col: str = "distrito_nombre",
    title: str = "Gentrificación vs. Precio de Mercado",
) -> go.Figure:
    """
    Crea un scatter plot para análisis de gentrificación.
    
    Args:
        df: DataFrame con datos de gentrificación y precios.
        x_col: Columna para índice de gentrificación.
        y_col: Columna para precio.
        color_col: Columna para colorear por distrito.
        title: Título del gráfico.
    
    Returns:
        Figura de Plotly.
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        trendline="ols",
        color=color_col,
        hover_name="barrio_nombre",
        title=title,
        labels={
            x_col: "Índice Gentrificación (0-100)",
            y_col: "Precio Venta (€/m²)",
            color_col: "Distrito"
        }
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(height=400, showlegend=False)
    
    return fig
