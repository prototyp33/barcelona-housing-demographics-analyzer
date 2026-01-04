"""
Market Cockpit View - Dashboard principal según Wireframe 1.

Incluye:
- KPIs críticos (Precio vs Índice, Presión Turística, Crimen, Ruido)
- Mapa coroplético + Top 5 barrios vulnerables
- Métricas secundarias (Tendencia, Regulación, Asequibilidad)
- Acciones rápidas
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from src.app.components import card_standard, render_empty_state
from src.app.data_loader import (
    load_critical_kpis,
    load_top_vulnerable_barrios,
    load_regulation_summary,
    load_affordability_summary,
    load_price_trends,
    load_available_years,
)
from src.app.utils import format_smart_currency, get_noise_level_color, PROFESSIONAL_COLORS
from src.app.styles import render_responsive_kpi_grid

logger = logging.getLogger(__name__)


def _format_trend_icon(trend_value: Optional[float]) -> tuple[str, str]:
    """
    Formatea icono de tendencia basado en valor.
    
    Args:
        trend_value: Valor de cambio (positivo = aumento, negativo = disminución).
    
    Returns:
        Tupla con (icono, color).
    """
    if trend_value is None:
        return "→", "normal"
    elif trend_value > 2.0:
        return "↗↗", "normal"  # Crecimiento fuerte
    elif trend_value > 0:
        return "↗", "normal"  # Crecimiento
    elif trend_value < -2.0:
        return "↘↘", "inverse"  # Decrecimiento fuerte
    elif trend_value < 0:
        return "↘", "inverse"  # Decrecimiento
    else:
        return "→", "off"  # Estable


def render_critical_kpis(year: int = 2024) -> None:
    """
    Renderiza los 4 KPIs críticos del Market Cockpit alineados con el reporte profesional.
    """
    kpis = load_critical_kpis(year)
    
    # Precio vs Índice
    precio_data = kpis.get("precio_vs_indice", {})
    precio_value = precio_data.get("value")
    precio_trend = precio_data.get("trend")
    precio_icon, precio_color = _format_trend_icon(precio_trend)
    
    # Presión Turística
    turismo_data = kpis.get("presion_turistica", {})
    turismo_value = turismo_data.get("value")
    turismo_trend = turismo_data.get("trend")
    turismo_icon, turismo_color = _format_trend_icon(turismo_trend)
    
    # Criminalidad
    crimen_data = kpis.get("criminalidad", {})
    crimen_value = crimen_data.get("value")
    crimen_trend = crimen_data.get("trend")
    crimen_icon, crimen_color = _format_trend_icon(-crimen_trend if crimen_trend else None)
    
    # Ruido
    ruido_data = kpis.get("ruido", {})
    ruido_value = ruido_data.get("value")
    ruido_trend = ruido_data.get("trend")
    ruido_icon, ruido_color = _format_trend_icon(-ruido_trend if ruido_trend else None)
    
    kpi_data = [
        {
            "title": "📊 Precio vs Índice",
            "value": f"{precio_value:+.1f}%" if precio_value is not None else "N/A",
            "style": "white",
            "delta": f"{precio_icon} {precio_trend:+.1f}%" if precio_trend is not None else "Sin datos",
            "delta_color": precio_color,
        },
        {
            "title": "🏖️ Presión Turística",
            "value": f"{turismo_value:.1f}%" if turismo_value is not None else "N/A",
            "style": "warm",
            "delta": f"{turismo_icon} {turismo_trend:+.1f}%" if turismo_trend is not None else "Sin datos",
            "delta_color": turismo_color,
        },
        {
            "title": "🚨 Crimen",
            "value": f"{crimen_value:.1f}" if crimen_value is not None else "N/A",
            "style": "cool",
            "delta": f"{crimen_icon} {abs(crimen_trend):.1f}" if crimen_trend is not None else "Sin datos",
            "delta_color": crimen_color,
        },
        {
            "title": "🔊 Ruido Ambiente",
            "value": f"{ruido_value:.1f} dB" if ruido_value is not None else "N/A",
            "style": "white",
            "delta": f"{ruido_icon} {abs(ruido_trend):.1f} dB" if ruido_trend is not None else "Sin datos",
            "delta_color": get_noise_level_color(ruido_value) if ruido_value is not None else "normal",
        },
    ]
    
    render_responsive_kpi_grid(kpi_data)


def render_top_vulnerable_barrios_list(year: int = 2024, top_n: int = 5) -> None:
    """
    Renderiza lista de Top 5 barrios más vulnerables.
    
    Args:
        year: Año a mostrar.
        top_n: Número de barrios a mostrar.
    """
    df = load_top_vulnerable_barrios(year, top_n)
    
    if df.empty:
        render_empty_state(
            title="Sin datos de vulnerabilidad",
            description="No se encontraron datos de riesgo de gentrificación.",
            icon="📊"
        )
        return
    
    st.subheader(f"TOP {top_n} BARRIOS MÁS VULNERABLES")
    
    for idx, row in df.iterrows():
        score = row.get("score_riesgo_gentrificacion", 0)
        categoria = row.get("categoria_riesgo", "Desconocido")
        barrio_nombre = row.get("barrio_nombre", f"Barrio {row.get('barrio_id', 'N/A')}")
        
        # Determinar color según categoría
        if score >= 70:
            color_emoji = "🔴"
            color_bg = "rgba(220, 38, 38, 0.1)"
        elif score >= 40:
            color_emoji = "🟠"
            color_bg = "rgba(245, 158, 11, 0.1)"
        else:
            color_emoji = "🟡"
            color_bg = "rgba(234, 179, 8, 0.1)"
        
        st.markdown(
            f'<div style="display: flex; align-items: center; justify-content: space-between; '
            f'padding: 12px 16px; margin-bottom: 8px; background: {color_bg}; '
            f'border-radius: 12px; border-left: 4px solid '
            f'{"#DC2626" if score >= 70 else "#F59E0B" if score >= 40 else "#EAB308"};">'
            f'<div><span style="font-size: 18px; margin-right: 8px;">{color_emoji}</span>'
            f'<strong>{idx + 1}. {barrio_nombre}</strong></div>'
            f'<div style="text-align: right;">'
            f'<div style="font-size: 20px; font-weight: 700; color: #1A1A1A;">{score:.1f}</div>'
            f'<div style="font-size: 12px; color: #8E92BC;">{categoria}</div></div></div>',
            unsafe_allow_html=True,
        )
    
    if st.button("Ver ranking completo →", key="btn_ver_ranking_completo"):
        st.session_state["nav_to_recommendations"] = True


def render_secondary_metrics(year: int = 2024) -> None:
    """
    Renderiza métricas secundarias (Tendencia, Regulación, Asequibilidad).
    
    Args:
        year: Año a mostrar.
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Tendencia de precios
        with card_standard(title="📈 Tendencia", subtitle="Evolución Precios 2020-2025"):
            try:
                df_trends = load_price_trends()
                if not df_trends.empty:
                    # Agregar por año
                    df_agg = df_trends.groupby("anyo")["precio_venta_m2"].mean().reset_index()
                    df_agg = df_agg[df_agg["anyo"] >= 2020]
                    
                    if not df_agg.empty:
                        fig = px.line(
                            df_agg,
                            x="anyo",
                            y="precio_venta_m2",
                            markers=True,
                            title="",
                            labels={"anyo": "Año", "precio_venta_m2": "Precio (€/m²)"},
                        )
                        fig.update_layout(
                            height=200,
                            showlegend=False,
                            margin=dict(l=0, r=0, t=0, b=0),
                        )
                        st.plotly_chart(fig, width="stretch", key="trend_chart")
                    else:
                        st.caption("Sin datos de tendencia")
                else:
                    st.caption("Sin datos disponibles")
            except Exception as e:
                logger.error("Error cargando tendencia: %s", e)
                st.caption("Error al cargar datos")
    
    with col2:
        # Regulación
        with card_standard(title="🏘️ Regulación", subtitle="Zonas Tensionadas y VUT"):
            try:
                reg_data = load_regulation_summary(year)
                zonas = reg_data.get("zonas_tensionadas", 0)
                licencias = reg_data.get("total_licencias_vut", 0)
                
                st.markdown(
                    f'<div style="padding: 16px 0;">'
                    f'<div style="margin-bottom: 12px;">'
                    f'<div style="font-size: 12px; color: #8E92BC; margin-bottom: 4px;">Zonas Tensión:</div>'
                    f'<div style="font-size: 24px; font-weight: 700; color: #1A1A1A;">{zonas}/73 barrios</div></div>'
                    f'<div><div style="font-size: 12px; color: #8E92BC; margin-bottom: 4px;">Lic. VUT:</div>'
                    f'<div style="font-size: 24px; font-weight: 700; color: #1A1A1A;">{licencias:,}</div></div></div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                logger.error("Error cargando regulación: %s", e)
                st.caption("Error al cargar datos")
    
    with col3:
        # Asequibilidad
        with card_standard(title="💰 Asequibilidad", subtitle="Ratio Precio/Renta"):
            try:
                aff_data = load_affordability_summary(year)
                ratio_anios = aff_data.get("ratio_precio_renta_anios")
                
                if ratio_anios is not None:
                    st.markdown(
                        f'<div style="padding: 16px 0;">'
                        f'<div style="font-size: 12px; color: #8E92BC; margin-bottom: 4px;">Ratio precio/renta:</div>'
                        f'<div style="font-size: 32px; font-weight: 700; color: #1A1A1A;">{ratio_anios:.1f} años</div>'
                        f'<div style="font-size: 12px; color: #8E92BC; margin-top: 8px;">Para vivienda tipo (70m²)</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Sin datos disponibles")
            except Exception as e:
                logger.error("Error cargando asequibilidad: %s", e)
                st.caption("Error al cargar datos")


def render_quick_actions() -> None:
    """Renderiza acciones rápidas del Market Cockpit."""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Analizar barrio específico", width="stretch", key="btn_analizar_barrio"):
            st.session_state["nav_to_insights"] = True
        
        if st.button("💡 Obtener recomendaciones", width="stretch", key="btn_recomendaciones"):
            st.session_state["nav_to_recommendations"] = True
    
    with col2:
        # Contar alertas activas
        try:
            from src.alerts.detector import detect_all_changes
            # Contar alertas para todos los barrios (simplificado: solo algunos)
            num_alertas = 12  # Placeholder - se puede calcular realmente
            if st.button(f"🔔 Ver alertas activas ({num_alertas})", width="stretch", key="btn_alertas"):
                st.session_state["nav_to_alerts"] = True
        except Exception:
            if st.button("🔔 Ver alertas activas", width="stretch", key="btn_alertas"):
                st.session_state["nav_to_alerts"] = True
        
        if st.button("📄 Generar reporte ejecutivo", width="stretch", key="btn_reporte"):
            st.info("Ejecuta: `python scripts/generate_reports.py --type executive_summary`")


def render_hero_section() -> None:
    """Renderiza una sección Hero de alto impacto."""
    st.markdown(
        f"""
        <div style="position: relative; border-radius: 24px; overflow: hidden; margin-bottom: 30px; height: 300px;">
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                        background: linear-gradient(135deg, rgba(29, 53, 87, 0.85) 0%, rgba(47, 128, 237, 0.4) 100%); 
                        z-index: 1;"></div>
            <img src="https://images.unsplash.com/photo-1583997051651-8255c4236318?auto=format&fit=crop&q=80&w=2000" 
                 style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0;">
            <div style="position: absolute; bottom: 40px; left: 40px; z-index: 2; color: white;">
                <p style="text-transform: uppercase; letter-spacing: 2px; font-size: 12px; font-weight: 600; margin-bottom: 8px; color: rgba(255,255,255,0.8);">Barcelona Housing Demographics</p>
                <h1 style="color: white !important; font-size: 42px !important; margin: 0; font-weight: 800; text-shadow: 0 4px 12px rgba(0,0,0,0.3);">Market Intel Cockpit</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render(year: int = 2024, distrito_filter: Optional[str] = None) -> None:
    """
    Renderiza el Market Cockpit completo según Wireframe 1.
    
    Args:
        year: Año seleccionado.
        distrito_filter: Filtro opcional por distrito.
    """
    render_hero_section()
    st.header("🏘️ MARKET COCKPIT - DASHBOARD PRINCIPAL")
    
    # KPIs Críticos
    st.markdown("### KPIs CRÍTICOS")
    render_critical_kpis(year)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filtros y Controles
    with card_standard(title="FILTROS Y CONTROLES"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            from src.app.data_loader import load_barrios
            barrios_df = load_barrios()
            barrio_options = ["Todos"] + barrios_df["barrio_nombre"].tolist()
            selected_barrio = st.selectbox("📍 Barrio", options=barrio_options, key="cockpit_barrio_filter")
        
        with col2:
            years_info = load_available_years()
            max_year = years_info["fact_precios"]["max"] or 2024
            min_year = years_info["fact_precios"]["min"] or 2020
            year_range = list(range(min_year, max_year + 1))
            default_index = len(year_range) - 1 if year_range else 0
            selected_year_cockpit = st.selectbox("📅 Año", options=year_range, index=default_index, key="cockpit_year_filter")
        
        with col3:
            vista_mode = st.radio("📊 Vista", options=["Mapa", "Lista"], horizontal=True, key="cockpit_vista_mode")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Visualización Principal: Mapa + Top 5
    st.markdown("### VISUALIZACIÓN PRINCIPAL")
    col_map, col_top5 = st.columns([2, 1])
    
    with col_map:
        with card_standard(title="🗺️ MAPA BARCELONA", subtitle="Coroplético por métrica"):
            from src.app.views import map_analysis
            map_analysis.render_snapshot(year=selected_year_cockpit, key="cockpit_map")
    
    with col_top5:
        render_top_vulnerable_barrios_list(year=selected_year_cockpit, top_n=5)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Métricas Secundarias
    st.markdown("### MÉTRICAS SECUNDARIAS")
    render_secondary_metrics(year=selected_year_cockpit)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Acciones Rápidas
    st.markdown("### ACCIONES RÁPIDAS")
    render_quick_actions()

