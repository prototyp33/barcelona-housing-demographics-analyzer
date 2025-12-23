"""
Vista de Análisis Avanzados - Visualizaciones avanzadas para insights.

Incluye:
- Evolución temporal multi-métrica
- Mapas de calor de correlaciones
- Radar charts para comparación de barrios
- Gráficos de burbujas (precio vs. calidad de vida)
- Treemaps de distribución de métricas
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.app.config import COLOR_SCALES
from src.app.components import render_empty_state
from src.analysis.descriptive import (
    calculate_trends,
    compare_barrios,
    calculate_correlations,
    generate_scorecard,
)

logger = logging.getLogger(__name__)


def render_temporal_evolution(
    barrio_id: int,
    metrics: List[str],
    years: Optional[List[int]] = None
) -> None:
    """
    Renderiza gráfico de evolución temporal multi-métrica.
    
    Args:
        barrio_id: ID del barrio a analizar.
        metrics: Lista de métricas a mostrar.
        years: Años opcionales a analizar.
    """
    st.subheader("📈 Evolución Temporal")
    
    # Obtener datos de tendencias para cada métrica
    trends_data = {}
    for metric in metrics:
        try:
            trend = calculate_trends(barrio_id, metric, years)
            if trend["values"]:
                trends_data[metric] = trend
        except Exception as e:
            logger.warning("Error calculando tendencia para %s: %s", metric, e)
    
    if not trends_data:
        render_empty_state(
            title="Sin datos de evolución",
            description="No se pudieron calcular tendencias para las métricas seleccionadas.",
            icon="📉"
        )
        return
    
    # Crear figura con subplots
    n_metrics = len(trends_data)
    fig = make_subplots(
        rows=n_metrics,
        cols=1,
        subplot_titles=[m.replace("_", " ").title() for m in trends_data.keys()],
        vertical_spacing=0.1,
    )
    
    colors = px.colors.qualitative.Set3
    
    for idx, (metric, trend) in enumerate(trends_data.items(), 1):
        fig.add_trace(
            go.Scatter(
                x=trend["years"],
                y=trend["values"],
                mode="lines+markers",
                name=metric.replace("_", " ").title(),
                line=dict(color=colors[idx % len(colors)], width=2),
                marker=dict(size=8),
                hovertemplate=f"<b>{metric.replace('_', ' ').title()}</b><br>"
                            f"Año: %{{x}}<br>"
                            f"Valor: %{{y:,.2f}}<extra></extra>",
            ),
            row=idx,
            col=1,
        )
        
        # Añadir línea de tendencia si hay suficientes puntos
        if len(trend["values"]) >= 2:
            z = np.polyfit(range(len(trend["values"])), trend["values"], 1)
            p = np.poly1d(z)
            fig.add_trace(
                go.Scatter(
                    x=trend["years"],
                    y=p(range(len(trend["values"]))),
                    mode="lines",
                    name=f"Tendencia {metric}",
                    line=dict(color=colors[idx % len(colors)], width=1, dash="dash"),
                    showlegend=False,
                ),
                row=idx,
                col=1,
            )
    
    fig.update_layout(
        height=300 * n_metrics,
        showlegend=False,
        title_text="Evolución Temporal Multi-Métrica",
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"temporal_evolution_{barrio_id}")
    
    # Mostrar información de tendencias
    for metric, trend in trends_data.items():
        if trend["trend_direction"] != "unknown":
            direction_emoji = "📈" if trend["trend_direction"] == "increasing" else "📉" if trend["trend_direction"] == "decreasing" else "➡️"
            st.caption(
                f"**{metric.replace('_', ' ').title()}**: {direction_emoji} "
                f"{trend['trend_direction']} ({trend['growth_rate']:.2f}% anual promedio)"
            )


def render_correlation_heatmap(
    metrics: List[str],
    year: Optional[int] = None
) -> None:
    """
    Renderiza mapa de calor de correlaciones entre métricas.
    
    Args:
        metrics: Lista de métricas a correlacionar.
        year: Año opcional para el análisis.
    """
    st.subheader("🔥 Mapa de Calor de Correlaciones")
    
    try:
        corr_matrix = calculate_correlations(metrics, year)
        
        if corr_matrix.empty:
            render_empty_state(
                title="Sin datos de correlación",
                description="No se pudieron calcular correlaciones para las métricas seleccionadas.",
                icon="📊"
            )
            return
        
        # Crear heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale=COLOR_SCALES["correlation"],
                zmin=-1,
                zmax=1,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
                textfont={"size": 12},
                hovertemplate="Correlación %{y} vs %{x}: %{z:.3f}<extra></extra>",
            )
        )
        
        fig.update_layout(
            title=f"Matriz de Correlaciones ({year if year else 'Último año disponible'})",
            height=600,
            xaxis_title="Métricas",
            yaxis_title="Métricas",
        )
        
        st.plotly_chart(fig, use_container_width=True, key="correlation_heatmap")
        
        # Mostrar correlaciones más fuertes
        st.caption("💡 **Tip**: Correlaciones cercanas a 1 o -1 indican relaciones fuertes entre variables.")
    
    except Exception as e:
        logger.error("Error renderizando mapa de correlaciones: %s", e)
        render_empty_state(
            title="Error al calcular correlaciones",
            description=str(e),
            icon="❌"
        )


def render_radar_chart(
    barrio_ids: List[int],
    metrics: List[str],
    year: Optional[int] = None
) -> None:
    """
    Renderiza radar chart para comparar múltiples barrios.
    
    Args:
        barrio_ids: Lista de IDs de barrios a comparar.
        metrics: Lista de métricas a comparar.
        year: Año opcional para la comparación.
    """
    st.subheader("🎯 Comparación Radar (Spider Chart)")
    
    try:
        df = compare_barrios(barrio_ids, metrics, year)
        
        if df.empty:
            render_empty_state(
                title="Sin datos para comparación",
                description="No se encontraron datos para los barrios seleccionados.",
                icon="📊"
            )
            return
        
        # Normalizar métricas (0-100) para el radar chart
        df_normalized = df.copy()
        barrio_names = df["barrio_nombre"].tolist()
        
        for metric in metrics:
            if metric in df.columns:
                col_data = df[metric].dropna()
                if len(col_data) > 0:
                    min_val = col_data.min()
                    max_val = col_data.max()
                    if max_val > min_val:
                        df_normalized[metric] = ((df[metric] - min_val) / (max_val - min_val)) * 100
                    else:
                        df_normalized[metric] = 50  # Valor medio si no hay variación
        
        # Crear radar chart
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        for idx, barrio_id in enumerate(barrio_ids):
            barrio_name = barrio_names[idx] if idx < len(barrio_names) else f"Barrio {barrio_id}"
            values = []
            for metric in metrics:
                if metric in df_normalized.columns:
                    val = df_normalized[df_normalized["barrio_id"] == barrio_id][metric].iloc[0] if len(df_normalized[df_normalized["barrio_id"] == barrio_id]) > 0 else 0
                    values.append(val)
                else:
                    values.append(0)
            
            # Cerrar el círculo (añadir primer valor al final)
            values.append(values[0])
            
            fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=[m.replace("_", " ").title() for m in metrics] + [metrics[0].replace("_", " ").title()],
                    fill="toself",
                    name=barrio_name,
                    line=dict(color=colors[idx % len(colors)]),
                )
            )
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                )
            ),
            showlegend=True,
            title="Comparación Multi-Métrica de Barrios",
            height=600,
        )
        
        st.plotly_chart(fig, use_container_width=True, key="radar_chart")
    
    except Exception as e:
        logger.error("Error renderizando radar chart: %s", e)
        render_empty_state(
            title="Error al crear comparación",
            description=str(e),
            icon="❌"
        )


def render_bubble_chart(
    year: Optional[int] = None,
    x_metric: str = "precio_m2_venta",
    y_metric: str = "tasa_criminalidad_1000hab",
    size_metric: str = "poblacion_total"
) -> None:
    """
    Renderiza gráfico de burbujas (precio vs. calidad de vida).
    
    Args:
        year: Año opcional para el análisis.
        x_metric: Métrica para eje X.
        y_metric: Métrica para eje Y.
        size_metric: Métrica para tamaño de burbujas.
    """
    st.subheader("💭 Gráfico de Burbujas: Precio vs. Calidad de Vida")
    
    try:
        from src.app.data_loader import get_connection
        
        conn = get_connection()
        
        query = """
            SELECT 
                barrio_id,
                barrio_nombre,
                precio_m2_venta,
                precio_mes_alquiler,
                poblacion_total,
                renta_mediana,
                tasa_criminalidad_1000hab,
                nivel_lden_medio,
                num_listings_airbnb
            FROM v_correlaciones_cruzadas
        """
        params = []
        
        if year:
            query += " WHERE anio = ?"
            params.append(year)
        else:
            query += " WHERE anio = (SELECT MAX(anio) FROM v_correlaciones_cruzadas)"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            render_empty_state(
                title="Sin datos para gráfico de burbujas",
                description="No se encontraron datos para el año seleccionado.",
                icon="📊"
            )
            return
        
        # Mapear métricas a columnas
        metric_map = {
            "precio_m2_venta": "precio_m2_venta",
            "precio_mes_alquiler": "precio_mes_alquiler",
            "poblacion_total": "poblacion_total",
            "renta_mediana": "renta_mediana",
            "tasa_criminalidad_1000hab": "tasa_criminalidad_1000hab",
            "nivel_lden_medio": "nivel_lden_medio",
            "num_listings_airbnb": "num_listings_airbnb",
        }
        
        x_col = metric_map.get(x_metric, x_metric)
        y_col = metric_map.get(y_metric, y_metric)
        size_col = metric_map.get(size_metric, size_metric)
        
        if x_col not in df.columns or y_col not in df.columns or size_col not in df.columns:
            render_empty_state(
                title="Métricas no disponibles",
                description=f"Algunas métricas seleccionadas no están disponibles en los datos.",
                icon="⚠️"
            )
            return
        
        # Filtrar valores nulos
        df_clean = df[[x_col, y_col, size_col, "barrio_nombre"]].dropna()
        
        if df_clean.empty:
            render_empty_state(
                title="Sin datos válidos",
                description="No hay datos completos para las métricas seleccionadas.",
                icon="📊"
            )
            return
        
        # Crear gráfico de burbujas
        fig = px.scatter(
            df_clean,
            x=x_col,
            y=y_col,
            size=size_col,
            hover_name="barrio_nombre",
            hover_data={x_col: ":,.0f", y_col: ":,.2f", size_col: ":,.0f"},
            title=f"{x_metric.replace('_', ' ').title()} vs {y_metric.replace('_', ' ').title()}",
            labels={
                x_col: x_metric.replace("_", " ").title(),
                y_col: y_metric.replace("_", " ").title(),
                size_col: size_metric.replace("_", " ").title(),
            },
        )
        
        fig.update_traces(
            marker=dict(
                opacity=0.6,
                line=dict(width=1, color="white"),
            )
        )
        
        fig.update_layout(
            height=600,
            xaxis_title=x_metric.replace("_", " ").title(),
            yaxis_title=y_metric.replace("_", " ").title(),
        )
        
        st.plotly_chart(fig, use_container_width=True, key="bubble_chart")
    
    except Exception as e:
        logger.error("Error renderizando gráfico de burbujas: %s", e)
        render_empty_state(
            title="Error al crear gráfico",
            description=str(e),
            icon="❌"
        )


def render_treemap(
    metric: str,
    year: Optional[int] = None
) -> None:
    """
    Renderiza treemap de distribución de una métrica por barrios.
    
    Args:
        metric: Métrica a visualizar.
        year: Año opcional para el análisis.
    """
    st.subheader("🌳 Treemap de Distribución")
    
    try:
        from src.app.data_loader import get_connection
        
        conn = get_connection()
        
        query = """
            SELECT 
                barrio_id,
                barrio_nombre,
                distrito_nombre,
                precio_m2_venta_promedio,
                poblacion_total_promedio,
                renta_mediana_promedio,
                tasa_criminalidad_1000hab_promedio,
                nivel_lden_medio_promedio,
                num_listings_airbnb_promedio
            FROM v_barrio_scorecard
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            render_empty_state(
                title="Sin datos para treemap",
                description="No se encontraron datos en el scorecard.",
                icon="📊"
            )
            return
        
        # Mapear métricas a columnas
        metric_map = {
            "precio_m2_venta": "precio_m2_venta_promedio",
            "poblacion_total": "poblacion_total_promedio",
            "renta_mediana": "renta_mediana_promedio",
            "tasa_criminalidad_1000hab": "tasa_criminalidad_1000hab_promedio",
            "nivel_lden_medio": "nivel_lden_medio_promedio",
            "num_listings_airbnb": "num_listings_airbnb_promedio",
        }
        
        value_col = metric_map.get(metric, metric + "_promedio")
        
        if value_col not in df.columns:
            render_empty_state(
                title="Métrica no disponible",
                description=f"La métrica '{metric}' no está disponible en el scorecard.",
                icon="⚠️"
            )
            return
        
        # Filtrar valores nulos
        df_clean = df[["barrio_nombre", "distrito_nombre", value_col]].dropna()
        
        if df_clean.empty:
            render_empty_state(
                title="Sin datos válidos",
                description="No hay datos completos para la métrica seleccionada.",
                icon="📊"
            )
            return
        
        # Crear treemap
        fig = px.treemap(
            df_clean,
            path=[px.Constant("Barcelona"), "distrito_nombre", "barrio_nombre"],
            values=value_col,
            title=f"Distribución de {metric.replace('_', ' ').title()} por Barrio",
            color=value_col,
            color_continuous_scale="Viridis",
            hover_data={value_col: ":,.2f"},
        )
        
        fig.update_layout(height=700)
        
        st.plotly_chart(fig, use_container_width=True, key=f"treemap_{metric}")
    
    except Exception as e:
        logger.error("Error renderizando treemap: %s", e)
        render_empty_state(
            title="Error al crear treemap",
            description=str(e),
            icon="❌"
        )


def render(year: int = 2022, barrio_id: Optional[int] = None) -> None:
    """
    Renderiza la vista completa de Análisis Avanzados.
    
    Args:
        year: Año seleccionado.
        barrio_id: ID opcional de barrio para análisis específico.
    """
    st.header("📊 Análisis Avanzados")
    
    # Selector de barrio si no se proporciona
    if barrio_id is None:
        from src.app.data_loader import load_barrios
        
        barrios_df = load_barrios()
        barrio_options = {f"{row['barrio_nombre']} ({row['barrio_id']})": row['barrio_id'] 
                         for _, row in barrios_df.iterrows()}
        
        selected_barrio_name = st.selectbox(
            "Seleccionar Barrio",
            options=list(barrio_options.keys()),
            key="advanced_analytics_barrio_selector"
        )
        barrio_id = barrio_options[selected_barrio_name]
    
    # Tabs para diferentes visualizaciones
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Evolución Temporal",
        "Correlaciones",
        "Comparación Radar",
        "Gráfico de Burbujas",
        "Treemap"
    ])
    
    with tab1:
        metrics_temporal = st.multiselect(
            "Métricas a analizar",
            options=["precio_m2_venta", "precio_mes_alquiler", "poblacion_total", 
                    "renta_mediana", "tasa_criminalidad_1000hab", "nivel_lden_medio"],
            default=["precio_m2_venta", "poblacion_total", "renta_mediana"],
            key="temporal_metrics"
        )
        
        if metrics_temporal:
            render_temporal_evolution(barrio_id, metrics_temporal, [year])
        else:
            st.info("Selecciona al menos una métrica para ver la evolución temporal.")
    
    with tab2:
        metrics_corr = st.multiselect(
            "Métricas a correlacionar",
            options=["precio_m2_venta", "precio_mes_alquiler", "poblacion_total",
                    "renta_mediana", "tasa_criminalidad_1000hab", "nivel_lden_medio",
                    "num_listings_airbnb", "densidad_hab_km2"],
            default=["precio_m2_venta", "renta_mediana", "tasa_criminalidad_1000hab", "nivel_lden_medio"],
            key="correlation_metrics"
        )
        
        if len(metrics_corr) >= 2:
            render_correlation_heatmap(metrics_corr, year)
        else:
            st.info("Selecciona al menos 2 métricas para calcular correlaciones.")
    
    with tab3:
        from src.app.data_loader import load_barrios
        
        barrios_df = load_barrios()
        barrio_options_compare = {f"{row['barrio_nombre']}": row['barrio_id'] 
                                 for _, row in barrios_df.iterrows()}
        
        selected_barrios_names = st.multiselect(
            "Barrios a comparar (máximo 5)",
            options=list(barrio_options_compare.keys()),
            default=list(barrio_options_compare.keys())[:3],
            max_selections=5,
            key="radar_barrios"
        )
        
        metrics_radar = st.multiselect(
            "Métricas para comparación",
            options=["precio_m2_venta", "poblacion_total", "renta_mediana",
                    "tasa_criminalidad_1000hab", "nivel_lden_medio"],
            default=["precio_m2_venta", "renta_mediana", "tasa_criminalidad_1000hab"],
            key="radar_metrics"
        )
        
        if selected_barrios_names and metrics_radar:
            barrio_ids_compare = [barrio_options_compare[name] for name in selected_barrios_names]
            render_radar_chart(barrio_ids_compare, metrics_radar, year)
        else:
            st.info("Selecciona barrios y métricas para la comparación radar.")
    
    with tab4:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_metric = st.selectbox(
                "Eje X",
                options=["precio_m2_venta", "precio_mes_alquiler", "renta_mediana"],
                index=0,
                key="bubble_x"
            )
        
        with col2:
            y_metric = st.selectbox(
                "Eje Y",
                options=["tasa_criminalidad_1000hab", "nivel_lden_medio", "num_listings_airbnb"],
                index=0,
                key="bubble_y"
            )
        
        with col3:
            size_metric = st.selectbox(
                "Tamaño de burbujas",
                options=["poblacion_total", "num_listings_airbnb", "renta_mediana"],
                index=0,
                key="bubble_size"
            )
        
        render_bubble_chart(year, x_metric, y_metric, size_metric)
    
    with tab5:
        treemap_metric = st.selectbox(
            "Métrica a visualizar",
            options=["precio_m2_venta", "poblacion_total", "renta_mediana",
                    "tasa_criminalidad_1000hab", "nivel_lden_medio", "num_listings_airbnb"],
            index=0,
            key="treemap_metric"
        )
        
        render_treemap(treemap_metric, year)

