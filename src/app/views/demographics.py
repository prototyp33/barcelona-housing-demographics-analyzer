"""
Demographics view - Radiografía Demográfica (V1.1)

Muestra análisis profundo de estructura demográfica por barrio:
- Índice de envejecimiento
- Correlación Precio vs. Edad
- Rankings de barrios por métricas demográficas
"""

from __future__ import annotations

from textwrap import dedent

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.app.config import COLOR_SCALES
from src.app.data_loader import load_demografia, load_precios
from src.app.styles import apply_plotly_theme, render_gradient_kpi, render_ranking_item


def render_demographic_kpis(year: int = 2022) -> None:
    """
    Renderiza KPIs principales de demografía con gradientes mesh.
    
    Args:
        year: Año a consultar
    """
    df_demo = load_demografia(year)
    
    if df_demo.empty:
        st.warning(f"No hay datos demográficos para {year}.")
        return
    
    # Calcular métricas agregadas
    avg_envejecimiento = df_demo["indice_envejecimiento"].mean()
    avg_juventud = df_demo["pct_menores_15"].mean()
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_gradient_kpi(
            title="Índice de Envejecimiento",
            value=avg_envejecimiento,
            gradient="warm",
            delta="Promedio de todos los barrios",
        )
        st.caption(
            "Un índice >100 indica más población ≥65 años que <15 años. "
            "Valores altos sugieren envejecimiento demográfico."
        )
    
    with col2:
        render_gradient_kpi(
            title="% Población Joven (<15 años)",
            value=avg_juventud,
            gradient="cool",
            delta="Promedio de todos los barrios",
        )
        st.caption(
            "Porcentaje de población menor de 15 años. "
            "Valores altos indican barrios con familias jóvenes."
        )


def render_price_vs_age_correlation(year: int = 2022) -> None:
    """
    Renderiza scatter plot de Precio vs. Edad (correlación).
    
    Args:
        year: Año a consultar
    """
    df_demo = load_demografia(year)
    df_precios = load_precios(year)
    
    if df_demo.empty or df_precios.empty:
        st.warning(f"No hay datos suficientes para {year}.")
        return
    
    # Merge de datos
    df_merged = df_precios.merge(
        df_demo[["barrio_id", "indice_envejecimiento", "pct_mayores_65", "pct_menores_15"]],
        on="barrio_id",
        how="inner",
    )
    
    if df_merged.empty:
        st.warning("No se pudieron combinar datos de precios y demografía.")
        return
    
    st.subheader("Correlación Precio vs. Estructura Demográfica")
    st.caption(
        "Análisis de la relación entre el precio de vivienda y la composición "
        "demográfica de cada barrio. ¿Los barrios más caros son más jóvenes o más envejecidos?"
    )
    
    # Crear subplots: Precio vs Envejecimiento y Precio vs Juventud
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Precio vs. Índice Envejecimiento", "Precio vs. % Población Joven"),
        horizontal_spacing=0.15,
    )
    
    # Scatter 1: Precio vs Envejecimiento
    fig.add_trace(
        go.Scatter(
            x=df_merged["indice_envejecimiento"],
            y=df_merged["avg_precio_m2"],
            mode="markers",
            marker=dict(
                size=10,
                color=df_merged["avg_precio_m2"],
                colorscale="Viridis",
                showscale=False,
                opacity=0.7,
                line=dict(width=1, color="white"),
            ),
            text=df_merged["barrio_nombre"],
            hovertemplate="<b>%{text}</b><br>"
            "Índice Envejecimiento: %{x:.1f}<br>"
            "Precio: €%{y:,.0f}/m²<extra></extra>",
            name="",
        ),
        row=1,
        col=1,
    )
    
    # Scatter 2: Precio vs Juventud
    fig.add_trace(
        go.Scatter(
            x=df_merged["pct_menores_15"],
            y=df_merged["avg_precio_m2"],
            mode="markers",
            marker=dict(
                size=10,
                color=df_merged["avg_precio_m2"],
                colorscale="Viridis",
                showscale=True,
                opacity=0.7,
                line=dict(width=1, color="white"),
            ),
            text=df_merged["barrio_nombre"],
            hovertemplate="<b>%{text}</b><br>"
            "% Población <15: %{x:.1f}%<br>"
            "Precio: €%{y:,.0f}/m²<extra></extra>",
            name="",
        ),
        row=1,
        col=2,
    )
    
    # Actualizar ejes
    fig.update_xaxes(title_text="Índice Envejecimiento", row=1, col=1)
    fig.update_xaxes(title_text="% Población <15 años", row=1, col=2)
    fig.update_yaxes(title_text="Precio (€/m²)", row=1, col=1)
    fig.update_yaxes(title_text="Precio (€/m²)", row=1, col=2)
    
    # Aplicar tema del Design System
    apply_plotly_theme(fig)
    fig.update_layout(
        height=450,
        showlegend=False,
        title_text=f"Relaciones Precio-Demografía ({year})",
        title_x=0.5,
    )
    
    st.plotly_chart(fig, key="demographics_correlation_scatter")
    
    # Calcular y mostrar correlaciones
    corr_envej = df_merged["avg_precio_m2"].corr(df_merged["indice_envejecimiento"])
    corr_joven = df_merged["avg_precio_m2"].corr(df_merged["pct_menores_15"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Correlación Precio-Envejecimiento",
            f"{corr_envej:.3f}",
            help="r > 0: Barrios más envejecidos = más caros. r < 0: Barrios más jóvenes = más caros.",
        )
    with col2:
        st.metric(
            "Correlación Precio-Juventud",
            f"{corr_joven:.3f}",
            help="r > 0: Barrios con más jóvenes = más caros. r < 0: Barrios con menos jóvenes = más caros.",
        )


def render_aging_map(year: int = 2022) -> None:
    """
    Renderiza mapa choropleth de índice de envejecimiento.
    
    Args:
        year: Año a consultar
    """
    from src.app.data_loader import build_geojson
    
    df_demo = load_demografia(year)
    df_precios = load_precios(year)
    
    if df_demo.empty or df_precios.empty:
        st.warning(f"No hay datos suficientes para {year}.")
        return
    
    # Merge con geometrías
    df_merged = df_precios.merge(
        df_demo[["barrio_id", "indice_envejecimiento", "pct_mayores_65"]],
        on="barrio_id",
        how="inner",
    )
    
    if df_merged.empty:
        return
    
    geojson = build_geojson(df_merged)
    
    st.subheader("Mapa de Envejecimiento Demográfico")
    st.caption(
        "Visualización espacial del índice de envejecimiento por barrio. "
        "Colores más oscuros indican mayor proporción de población mayor."
    )
    
    fig = px.choropleth(
        df_merged,
        geojson=geojson,
        locations="barrio_id",
        featureidkey="properties.barrio_id",
        color="indice_envejecimiento",
        color_continuous_scale="Reds",  # Rojo = más envejecido
        hover_data={
            "barrio_nombre": True,
            "distrito_nombre": True,
            "indice_envejecimiento": ":.1f",
            "pct_mayores_65": ":.1f",
        },
        labels={
            "indice_envejecimiento": "Índice Envejecimiento",
            "pct_mayores_65": "% ≥65 años",
        },
        title=f"Índice de Envejecimiento por Barrio ({year})",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    apply_plotly_theme(fig)
    fig.update_layout(margin=dict(r=0, t=60, l=0, b=0), height=500)
    
    st.plotly_chart(fig, key="demographics_aging_map")


def render_aging_ranking(year: int = 2022, top_n: int = 10) -> None:
    """
    Renderiza ranking de barrios por índice de envejecimiento.
    
    Args:
        year: Año a consultar
        top_n: Número de barrios a mostrar
    """
    df_demo = load_demografia(year)
    
    if df_demo.empty:
        st.warning(f"No hay datos demográficos para {year}.")
        return
    
    # Cargar nombres de barrios
    from src.app.data_loader import load_barrios
    
    df_barrios = load_barrios()
    df_merged = df_demo.merge(
        df_barrios[["barrio_id", "barrio_nombre", "distrito_nombre"]],
        on="barrio_id",
        how="left",
    )
    
    # Ordenar por índice de envejecimiento (mayor a menor)
    df_sorted = df_merged.sort_values("indice_envejecimiento", ascending=False)
    top_barrios = df_sorted.head(top_n)
    max_value = df_sorted["indice_envejecimiento"].max()
    
    st.subheader(f"Top {top_n} Barrios Más Envejecidos")
    st.caption(
        "Ranking de barrios con mayor índice de envejecimiento. "
        "Un índice alto indica una población significativamente más mayor que joven."
    )
    
    # Renderizar items con barra de progreso
    for _, row in top_barrios.iterrows():
        render_ranking_item(
            name=f"{row['barrio_nombre']} ({row['distrito_nombre']})",
            value=row["indice_envejecimiento"],
            max_value=max_value,
            show_percentage=False,
        )


def render(year: int = 2022) -> None:
    """
    Renderiza la vista completa de Demografía (V1.1).
    
    Args:
        year: Año seleccionado
    """
    st.header("Radiografía Demográfica")
    st.markdown(
        "Análisis profundo de la estructura demográfica de Barcelona por barrio. "
        "Explora cómo la edad de la población se relaciona con el precio de la vivienda."
    )
    
    # KPIs con gradientes
    render_demographic_kpis(year)
    
    st.divider()
    
    # Layout principal: 70% izquierda, 30% derecha
    col_main, col_sidebar = st.columns([0.7, 0.3])
    
    with col_main:
        # Row 1: Correlación Precio vs Edad
        render_price_vs_age_correlation(year)
        
        st.divider()
        
        # Row 2: Mapa de Envejecimiento
        render_aging_map(year)
    
    with col_sidebar:
        # Ranking de Envejecimiento
        render_aging_ranking(year, top_n=15)
        
        st.divider()
        
        info_html = dedent(
            """
            <details class="bh-expander">
              <summary>Sobre el Índice de Envejecimiento</summary>
              <div class="bh-expander-content">
                <p><strong>Fórmula:</strong> (Población ≥65 años / Población &lt;15 años) × 100</p>
                <h3>Interpretación</h3>
                <ul>
                  <li><strong>&lt; 100:</strong> Más jóvenes que mayores (población rejuvenecedora).</li>
                  <li><strong>= 100:</strong> Equilibrio demográfico.</li>
                  <li><strong>&gt; 100:</strong> Predominio de población mayor (envejecimiento).</li>
                  <li><strong>&gt; 200:</strong> Envejecimiento crítico.</li>
                </ul>
                <h3>Limitaciones</h3>
                <ul>
                  <li>Los datos de edad se propagan desde 2025 a años históricos.</li>
                  <li>El índice no captura migración reciente.</li>
                </ul>
              </div>
            </details>
            """
        )
        st.markdown(info_html, unsafe_allow_html=True)

