"""
Overview view - KPIs and global trends.

Muestra métricas clave y evolución temporal de precios.
"""

from __future__ import annotations

from textwrap import dedent

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.app.config import COLORS, COLOR_SCALES
from src.app.data_loader import load_kpis, load_precios, load_available_years
from src.app.utils import format_smart_currency
from src.app.styles import render_responsive_kpi_grid, apply_plotly_theme, KPIMetric
from src.app.components import render_empty_state


def render_kpis() -> None:
    """Renderiza las tarjetas de KPIs principales con formato profesional."""
    kpis = load_kpis()
    
    metrics_data = [
        KPIMetric(
            title="Total Barrios",
            value=kpis["total_barrios"],
            style="white",
            delta=f"↑ {kpis['barrios_con_geometria']} con geometría",
            delta_color="green",
        ),
        KPIMetric(
            title="Registros de Precios",
            value=kpis['registros_precios'],
            style="warm",
            delta=f"{kpis['año_min']}-{kpis['año_max']}",
        ),
        KPIMetric(
            title="Precio Medio (Venta)",
            value=kpis.get('precio_medio_actual', 0.0),
            is_currency=True,
            unit="€/m²",
            style="cool",
            delta=f"vs {kpis.get('año_max', 2023)-1}: {((kpis.get('precio_medio_actual', 0)/kpis.get('precio_medio_anterior', 1))-1)*100:+.1f}%" if kpis.get('precio_medio_anterior') else None
        ),
        KPIMetric(
            title="Renta Media (Hogar)",
            value=kpis.get('renta_media_actual', 0.0),
            is_currency=True,
            style="white",
            delta="Dato más reciente (2022/23)"
        ),
    ]
    
    render_responsive_kpi_grid(metrics_data)


def render_price_evolution(
    distrito_filter: str | None = None,
    key: str | None = None,
) -> None:
    """
    Renderiza gráfico de evolución temporal de precios.
    
    Args:
        distrito_filter: Filtro opcional por distrito.
        key: Clave única para el componente plotly_chart.
    """
    years_info = load_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2022
    
    # Cargar datos para cada año
    data = []
    for year in range(min_year, max_year + 1):
        df = load_precios(year, distrito_filter)
        if not df.empty:
            avg_precio = df["avg_precio_m2"].mean()
            data.append({"año": year, "precio_medio": avg_precio})
    
    if not data:
        render_empty_state(
            title="Sin datos de precios",
            description="No hay datos históricos para el filtro seleccionado.",
            icon="📉"
        )
        return
    
    import pandas as pd
    df_evolution = pd.DataFrame(data)
    
    from src.app.styles import apply_plotly_theme
    
    fig = px.line(
        df_evolution,
        x="año",
        y="precio_medio",
        markers=True,
        title="Evolución del Precio Medio de Vivienda (€/m²)",
        labels={"año": "Año", "precio_medio": "Precio Medio (€/m²)"},
    )
    
    fig.update_traces(
        line=dict(color=COLORS["accent_blue"], width=3),
        marker=dict(size=10, color=COLORS["accent_blue"]),
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(dtick=1),
    )
    
    st.plotly_chart(fig, key=key)


def render_distrito_comparison(
    year: Optional[int] = None,
    distrito_filter: str | None = None,
    key: str | None = None,
) -> None:
    """
    Renderiza comparación inteligente: Por Distrito (Global) o Por Barrio (Local).
    
    Args:
        year: Año a mostrar. Si es None, usa el más reciente.
        distrito_filter: Si es None, muestra ranking de distritos. Si existe, ranking de barrios.
        key: Clave única para el componente plotly_chart.
    """
    if year is None:
        from src.app.data_loader import load_available_years
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    df = load_precios(year)
    
    if df.empty:
        render_empty_state(
            title="Datos no disponibles",
            description=f"No hay registros de precios para el año {year}.",
            icon="📉"
        )
        return
    
    from src.app.styles import apply_plotly_theme
    
    if distrito_filter:
        # MODO LOCAL: Ranking de Barrios dentro del Distrito
        df_filtered = df[df["distrito_nombre"] == distrito_filter]
        if df_filtered.empty:
            render_empty_state(
                title="Sin datos detallados",
                description=f"No hay información para {distrito_filter} en {year}.",
                icon="🏘️"
            )
            return
            
        ranking_data = (
            df_filtered.groupby("barrio_nombre")["avg_precio_m2"]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        
        title = f"Ranking de Barrios: {distrito_filter} ({year})"
        y_col = "barrio_nombre"
        label_y = "Barrio"
        height = max(350, len(ranking_data) * 30)  # Altura dinámica
        
    else:
        # MODO GLOBAL: Ranking de Distritos
        ranking_data = (
            df.groupby("distrito_nombre")["avg_precio_m2"]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        
        title = f"Precio Medio por Distrito ({year})"
        y_col = "distrito_nombre"
        label_y = "Distrito"
        height = 400

    fig = px.bar(
        ranking_data,
        x="avg_precio_m2",
        y=y_col,
        orientation="h",
        title=title,
        labels={"avg_precio_m2": "Precio (€/m²)", y_col: label_y},
        text="avg_precio_m2",
    )
    
    fig.update_traces(
        marker_color=COLORS["accent_blue"],
        marker_line_color=COLORS["accent_blue"],
        marker_line_width=1,
        texttemplate='%{text:,.0f}€',
        textposition='outside',
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(r=50) # Espacio para etiquetas
    )
    
    st.plotly_chart(fig, key=key)


def render(
    distrito_filter: str | None = None,
    year: Optional[int] = None,
    key_prefix: str = "overview",
) -> None:
    """
    Renderiza la vista completa de Overview.
    
    Args:
        distrito_filter: Filtro opcional por distrito.
        year: Año seleccionado. Si es None, usa el más reciente.
        key_prefix: Prefijo para claves únicas de componentes plotly.
    """
    if year is None:
        years_info = load_available_years()
        year = years_info.get("fact_precios", {}).get("max") or 2023

    st.header("Visión General")
    
    # Cargar metadatos para texto dinámico
    years_info = load_available_years()
    precios_max = years_info.get("fact_precios", {}).get("max") or 2023
    renta_max = years_info.get("fact_renta", {}).get("max") or 2022

    info_html = dedent(
        f"""
        <details class="bh-expander">
          <summary>Acerca de estos datos</summary>
          <div class="bh-expander-content">
            <h3>Fuentes de Datos</h3>
            <table>
              <tr><th>Fuente</th><th>Cobertura</th><th>Actualización</th></tr>
              <tr><td><strong>Open Data BCN</strong></td><td>2015-{precios_max}</td><td>Anual</td></tr>
              <tr><td><strong>Portal de Dades BCN</strong></td><td>2012-2025</td><td>Trimestral</td></tr>
              <tr><td><strong>IDESCAT</strong></td><td>Censal</td><td>Quinquenal</td></tr>
            </table>
            <h3>Metodología</h3>
            <ul>
              <li><strong>Precio medio (€/m²):</strong> Media aritmética de todos los indicadores de precio disponibles para cada barrio-año.</li>
              <li><strong>Esfuerzo de compra:</strong> Precio de vivienda tipo (70 m²) / Renta anual bruta.</li>
              <li><strong>Índice de envejecimiento:</strong> (Población ≥65) / (Población &lt;15) × 100.</li>
            </ul>
            <h3>Limitaciones</h3>
            <ul>
              <li>Los datos de renta solo están disponibles para <strong>{renta_max}</strong>.</li>
              <li>Las métricas de edad se propagan desde 2025 a años históricos.</li>
            </ul>
          </div>
        </details>
        """
    )
    st.markdown(info_html, unsafe_allow_html=True)
    
    render_kpis()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_price_evolution(distrito_filter, key=f"{key_prefix}_price_evolution")
    
    with col2:
        render_distrito_comparison(
            year=year,
            distrito_filter=distrito_filter,
            key=f"{key_prefix}_distrito_comparison"
        )

